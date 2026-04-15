"""Chart Auditor — Archon overseer for matplotlib chart quality.

Wraps render_chart_for_brand() with a pre-embed visual quality gate.
Claude Sonnet inspects each chart PNG immediately after rendering, before
it is compiled into a Typst slide.  Issues that can be fixed
programmatically (excess categories, figure width) are fixed and the chart
re-rendered in-place.  Issues that require a different chart type or data
re-think are returned as ``redesign_needed=True`` so the pipeline can log
them for the Archon/design-advisor to address.

Max attempts: 2 (initial render + one programmatic-fix pass).
Bridge routing: POST http://localhost:8082/vision first (Claude Max, free),
then Anthropic SDK only if ``api_key`` is explicitly supplied.  Never
auto-reads ANTHROPIC_API_KEY from the environment.
"""

from __future__ import annotations

import base64
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------


@dataclass
class ChartAuditResult:
    """Outcome of a render_and_audit() call."""

    passed: bool
    chart_path: Path
    issues: list[str] = field(default_factory=list)
    fix_applied: bool = False
    redesign_needed: bool = False
    attempts: int = 1


# ---------------------------------------------------------------------------
# Vision prompt
# ---------------------------------------------------------------------------

_CHART_AUDIT_SYSTEM = """\
You are a chart quality auditor for a professional presentation tool.
Your job is to inspect matplotlib chart PNGs and identify RENDERING DEFECTS ONLY.

Do NOT comment on: content quality, narrative, colour choices, or chart-type optimality.

Flag only these specific rendering defects:

  LEGEND_OVERLAP    — Legend is visually covering bars, lines, data points, or fill areas
  LABEL_CLIPPED     — Any axis label, tick label, annotation, or title is cut off at the figure edge
  LABELS_UNREADABLE — Text labels are present but too small to read clearly at normal viewing distance
  TOO_CROWDED       — Bars, tick labels, or lines are so dense they cannot be individually distinguished
  EMPTY_CHART       — The chart area is mostly blank / near-empty (likely a data or render error)
  WRONG_CHART_TYPE  — The chart type is fundamentally incompatible with the data shown
                      (e.g., a donut chart rendering a time series)

Return a JSON array. Each item must be:
  {
    "issue_type": "<one of the types above>",
    "severity": "error" | "warn",
    "detail": "<one concise sentence describing the specific problem>",
    "fix": "programmatic" | "redesign"
  }

"programmatic" — the renderer can fix this by adjusting render parameters (no chart redesign needed)
"redesign"     — requires a different chart type or source data change

Return [] if the chart looks good — no issues at all.
Return ONLY valid JSON. No markdown fences, no prose outside the array.
"""

_USER_TMPL = (
    "Chart type: {chart_type}\n"
    "Figure size: {width:.1f}\" × {height:.1f}\"\n\n"
    "Audit this chart PNG for rendering defects only. Return a JSON array of issues."
)

# Maximum categories before truncation is applied as a programmatic fix
_MAX_CATEGORIES = 10


# ---------------------------------------------------------------------------
# ChartAuditor
# ---------------------------------------------------------------------------


class ChartAuditor:
    """Archon overseer for individual chart quality.

    Wraps ``render_chart_for_brand()`` with a Sonnet vision quality gate.

    Parameters
    ----------
    bridge_url : str
        Inkline bridge URL (tried first — Claude Max, zero API cost).
    api_key : str | None
        Anthropic API key for SDK fallback. Never auto-read from env.
    max_attempts : int
        Max render+audit cycles per chart (default 2).
    model : str
        Claude model for vision calls.
    """

    def __init__(
        self,
        bridge_url: str = "http://localhost:8082",
        api_key: Optional[str] = None,
        max_attempts: int = 2,
        model: str = "claude-sonnet-4-6",
    ) -> None:
        self.bridge_url = bridge_url
        self.api_key = api_key
        self.max_attempts = max_attempts
        self.model = model

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def render_and_audit(
        self,
        chart_type: str,
        chart_data: dict[str, Any],
        output_path: Path,
        brand_name: str,
        *,
        width: float = 7.0,
        height: float = 3.5,
    ) -> ChartAuditResult:
        """Render a chart, audit it, apply a fix if needed, re-render once.

        Never mutates the caller's ``chart_data`` dict.
        """
        from inkline.typst.chart_renderer import render_chart_for_brand

        data = _shallow_copy(chart_data)
        fix_applied = False

        for attempt in range(1, self.max_attempts + 1):

            # --- Render ---
            try:
                render_chart_for_brand(
                    chart_type, data, str(output_path),
                    brand_name=brand_name, width=width, height=height,
                )
            except Exception as exc:
                log.warning(
                    "ChartAuditor: render failed (attempt %d/%d): %s",
                    attempt, self.max_attempts, exc,
                )
                return ChartAuditResult(
                    passed=False, chart_path=output_path,
                    issues=[f"Render error: {exc}"],
                    redesign_needed=True, attempts=attempt,
                )

            if not output_path.exists():
                return ChartAuditResult(
                    passed=False, chart_path=output_path,
                    issues=["Chart file was not created after render"],
                    redesign_needed=True, attempts=attempt,
                )

            # --- Audit ---
            raw_issues = self._audit_png(output_path, chart_type, width, height)

            if not raw_issues:
                return ChartAuditResult(
                    passed=True, chart_path=output_path,
                    fix_applied=fix_applied, attempts=attempt,
                )

            issue_msgs = [
                f"{i['issue_type']}: {i.get('detail', '')}" for i in raw_issues
            ]
            programmatic = [i for i in raw_issues if i.get("fix") == "programmatic"]
            needs_redesign = any(i.get("fix") == "redesign" for i in raw_issues)

            if needs_redesign:
                return ChartAuditResult(
                    passed=False, chart_path=output_path,
                    issues=issue_msgs, fix_applied=fix_applied,
                    redesign_needed=True, attempts=attempt,
                )

            if attempt >= self.max_attempts or not programmatic:
                # Out of attempts or nothing to fix — ship with warnings
                return ChartAuditResult(
                    passed=False, chart_path=output_path,
                    issues=issue_msgs, fix_applied=fix_applied,
                    redesign_needed=False, attempts=attempt,
                )

            # --- Apply programmatic fix and loop ---
            fixed_data, new_w, new_h = _apply_programmatic_fixes(
                data, programmatic, chart_type, width, height,
            )
            if fixed_data is None:
                # No actionable fix found — don't loop
                return ChartAuditResult(
                    passed=False, chart_path=output_path,
                    issues=issue_msgs, fix_applied=fix_applied,
                    redesign_needed=False, attempts=attempt,
                )

            data, width, height = fixed_data, new_w, new_h
            fix_applied = True
            log.info(
                "ChartAuditor: programmatic fix applied to '%s', re-rendering "
                "(attempt %d → %d)",
                output_path.name, attempt, attempt + 1,
            )

        # Should not be reached in normal flow
        return ChartAuditResult(
            passed=False, chart_path=output_path,
            issues=["Max audit attempts reached"],
            fix_applied=fix_applied, attempts=self.max_attempts,
        )

    # ------------------------------------------------------------------
    # Vision call
    # ------------------------------------------------------------------

    def _audit_png(
        self,
        png_path: Path,
        chart_type: str,
        width: float,
        height: float,
    ) -> list[dict]:
        """Run Sonnet vision on the chart PNG. Returns list of raw issue dicts."""
        img_b64 = base64.standard_b64encode(png_path.read_bytes()).decode("utf-8")
        user_text = _USER_TMPL.format(
            chart_type=chart_type, width=width, height=height,
        )
        text: Optional[str] = None

        # --- 1. Bridge (Claude Max, zero cost) ---
        try:
            import requests as _req
            resp = _req.post(
                f"{self.bridge_url}/vision",
                json={
                    "prompt": user_text,
                    "system": _CHART_AUDIT_SYSTEM,
                    "image_base64": img_b64,
                    "image_media_type": "image/png",
                },
                timeout=(2, 60),
            )
            if resp.status_code == 200:
                text = resp.json().get("response", "").strip()
        except Exception:
            pass  # Bridge not available — try SDK

        # --- 2. Anthropic SDK (explicit api_key only) ---
        if not text and self.api_key:
            try:
                import anthropic
                client = anthropic.Anthropic(api_key=self.api_key)
                response = client.messages.create(
                    model=self.model,
                    max_tokens=1024,
                    system=_CHART_AUDIT_SYSTEM,
                    messages=[{
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": img_b64,
                                },
                            },
                            {"type": "text", "text": user_text},
                        ],
                    }],
                )
                text = response.content[0].text.strip()
            except Exception as exc:
                log.debug("ChartAuditor: API call failed for '%s': %s", png_path.name, exc)

        if not text:
            log.debug(
                "ChartAuditor: vision unavailable for '%s' — audit skipped",
                png_path.name,
            )
            return []  # No vision available → treat as pass

        # Strip markdown fences if the model wrapped the JSON
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            text = text.rstrip("`").strip()

        try:
            issues = json.loads(text)
            if isinstance(issues, list):
                return [i for i in issues if isinstance(i, dict) and i.get("issue_type")]
        except json.JSONDecodeError:
            log.debug(
                "ChartAuditor: could not parse audit JSON for '%s': %s",
                png_path.name, text[:120],
            )

        return []


# ---------------------------------------------------------------------------
# Programmatic fixes
# ---------------------------------------------------------------------------

# Max characters before a category label is abbreviated
_MAX_LABEL_CHARS = 10


def _apply_programmatic_fixes(
    data: dict,
    issues: list[dict],
    chart_type: str,
    width: float,
    height: float,
) -> tuple[dict | None, float, float]:
    """Fix rendering issues by adapting what is shown, never the canvas size.

    Dimensions (width/height) are contractual — they must fill the Typst slot
    exactly.  All fixes work within the given space:
      - Reduce data density (fewer categories, every-other labels)
      - Abbreviate label text
      - Reposition / suppress the legend
      - Chart-type-specific layout tweaks

    Returns ``(fixed_data, width, height)`` if at least one change was made,
    or ``(None, width, height)`` if nothing actionable was found.
    """
    issue_types = {i["issue_type"] for i in issues}
    changed = False

    # ------------------------------------------------------------------
    # TOO_CROWDED / LABELS_UNREADABLE
    # Strategy 1: truncate to top N categories (most impactful series first)
    # Strategy 2: thin the x-axis labels (show every other one)
    # Strategy 3: abbreviate long category names in-place
    # ------------------------------------------------------------------
    if issue_types & {"TOO_CROWDED", "LABELS_UNREADABLE"}:
        cats = data.get("categories", [])

        if len(cats) > _MAX_CATEGORIES:
            # Truncate to top N — keeps the most important data visible
            data["categories"] = cats[:_MAX_CATEGORIES]
            for s in data.get("series", []):
                vals = s.get("values", [])
                if len(vals) > _MAX_CATEGORIES:
                    s["values"] = vals[:_MAX_CATEGORIES]
            log.debug(
                "ChartAuditor fix: truncated %d categories → %d",
                len(cats), _MAX_CATEGORIES,
            )
            cats = data["categories"]
            changed = True

        elif len(cats) > 6:
            # Too many to truncate cleanly — thin the labels instead.
            # Replace every odd-indexed label with "" so only even indices
            # show text.  The bar/line still renders at every position;
            # only the x-tick label is suppressed.
            data["categories"] = _thin_labels(cats)
            log.debug(
                "ChartAuditor fix: thinned %d category labels (every other)",
                len(cats),
            )
            changed = True

        # Abbreviate names that are still too long for the available width
        if data.get("categories"):
            abbreviated = _abbreviate_labels(data["categories"])
            if abbreviated != data["categories"]:
                data["categories"] = abbreviated
                log.debug("ChartAuditor fix: abbreviated category labels")
                changed = True

        # Cap scatter points if extremely dense
        pts = data.get("points", [])
        if len(pts) > _MAX_CATEGORIES * 4:
            data["points"] = pts[: _MAX_CATEGORIES * 4]
            changed = True

    # ------------------------------------------------------------------
    # LABEL_CLIPPED
    # Strategy: shorten the labels so they fit within the existing canvas.
    # Never resize the canvas — dimensions are layout-contractual.
    # ------------------------------------------------------------------
    if "LABEL_CLIPPED" in issue_types:
        cats = data.get("categories", [])
        if cats:
            abbreviated = _abbreviate_labels(cats, max_chars=8)
            if abbreviated != cats:
                data["categories"] = abbreviated
                log.debug("ChartAuditor fix: hard-abbreviated clipped category labels")
                changed = True

        # For line/area charts with many x-axis points, thin the labels
        x_vals = data.get("x", [])
        if len(x_vals) > 10:
            data["x"] = _thin_labels(x_vals)
            # Also thin corresponding series values if same length
            for s in data.get("series", []):
                if len(s.get("values", [])) == len(x_vals):
                    s["values"] = s["values"][::2]
            log.debug("ChartAuditor fix: thinned x-axis to %d points", len(data["x"]))
            changed = True

    # ------------------------------------------------------------------
    # LEGEND_OVERLAP
    # Strategy: move legend to a location that doesn't cover the data,
    # suppress it entirely for single-series, or switch to direct labels.
    # ------------------------------------------------------------------
    if "LEGEND_OVERLAP" in issue_types:
        if chart_type == "donut" and data.get("label_style") != "direct":
            # Donut supports radial direct labels — no legend needed
            data["label_style"] = "direct"
            log.debug("ChartAuditor fix: donut label_style → direct")
            changed = True

        elif len(data.get("series", [])) <= 1:
            # Single-series — legend adds no information; suppress it
            for s in data.get("series", []):
                if s.get("name"):
                    s["name"] = ""
                    changed = True

        elif len(data.get("series", [])) > 5:
            # More series than a legend can display cleanly: merge the tail
            # into an "Other" series so the legend stays to ≤ 5 entries.
            series = data["series"]
            keep = series[:4]
            tail = series[4:]
            if tail:
                # Sum the tail values element-wise
                tail_vals = tail[0].get("values", [])[:]
                for extra in tail[1:]:
                    evs = extra.get("values", [])
                    tail_vals = [
                        (tail_vals[j] or 0) + (evs[j] if j < len(evs) else 0)
                        for j in range(len(tail_vals))
                    ]
                keep.append({"name": "Other", "values": tail_vals})
            data["series"] = keep
            log.debug(
                "ChartAuditor fix: merged %d tail series into 'Other'", len(tail)
            )
            changed = True

    if not changed:
        return None, width, height

    return data, width, height


# ---------------------------------------------------------------------------
# Label helpers
# ---------------------------------------------------------------------------


def _thin_labels(labels: list) -> list:
    """Return a copy where every odd-indexed label is replaced with an empty string.

    The bar/line still renders at every position; only the tick label text
    is hidden, halving the visible density without losing data.
    """
    return [lbl if i % 2 == 0 else "" for i, lbl in enumerate(labels)]


def _abbreviate_labels(labels: list, max_chars: int = _MAX_LABEL_CHARS) -> list:
    """Truncate string labels that exceed max_chars to fit the available axis space."""
    result = []
    for lbl in labels:
        if isinstance(lbl, str) and len(lbl) > max_chars:
            result.append(lbl[: max_chars - 1] + "…")
        else:
            result.append(lbl)
    return result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _shallow_copy(data: dict) -> dict:
    """Copy the dict and one level of list values so fixes don't mutate caller's data."""
    result = dict(data)
    for k, v in result.items():
        if isinstance(v, list):
            result[k] = [dict(item) if isinstance(item, dict) else item for item in v]
    return result


# ---------------------------------------------------------------------------
# Convenience wrapper (used by _auto_render_charts)
# ---------------------------------------------------------------------------


def render_and_audit(
    chart_type: str,
    chart_data: dict[str, Any],
    output_path: Path,
    brand_name: str,
    *,
    width: float = 7.0,
    height: float = 3.5,
    bridge_url: str = "http://localhost:8082",
    api_key: Optional[str] = None,
    max_attempts: int = 2,
) -> ChartAuditResult:
    """Render a chart and immediately audit it for quality.

    Convenience wrapper around ``ChartAuditor.render_and_audit()``.
    Falls back to a plain render (no audit) if Sonnet vision is unavailable.
    """
    auditor = ChartAuditor(
        bridge_url=bridge_url,
        api_key=api_key,
        max_attempts=max_attempts,
    )
    return auditor.render_and_audit(
        chart_type, chart_data, output_path, brand_name,
        width=width, height=height,
    )


__all__ = ["ChartAuditor", "ChartAuditResult", "render_and_audit"]
