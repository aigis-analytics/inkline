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


def _apply_programmatic_fixes(
    data: dict,
    issues: list[dict],
    chart_type: str,
    width: float,
    height: float,
) -> tuple[dict | None, float, float]:
    """Attempt to fix rendering issues by adjusting chart_data and dimensions.

    Returns ``(fixed_data, new_width, new_height)`` if at least one fix was
    applied, or ``(None, width, height)`` if nothing could be changed.
    """
    issue_types = {i["issue_type"] for i in issues}
    changed = False

    # TOO_CROWDED / LABELS_UNREADABLE → truncate categories to top N
    if issue_types & {"TOO_CROWDED", "LABELS_UNREADABLE"}:
        cats = data.get("categories", [])
        if len(cats) > _MAX_CATEGORIES:
            data["categories"] = cats[:_MAX_CATEGORIES]
            for s in data.get("series", []):
                vals = s.get("values", [])
                if len(vals) > _MAX_CATEGORIES:
                    s["values"] = vals[:_MAX_CATEGORIES]
            log.debug(
                "ChartAuditor fix: truncated %d categories → %d",
                len(cats), _MAX_CATEGORIES,
            )
            changed = True

        # Also cap scatter points if extremely dense
        pts = data.get("points", [])
        if len(pts) > _MAX_CATEGORIES * 4:
            data["points"] = pts[:_MAX_CATEGORIES * 4]
            changed = True

    # LABEL_CLIPPED → widen the figure to give labels more room
    if "LABEL_CLIPPED" in issue_types:
        new_w = min(width * 1.25, 12.0)
        if new_w > width + 0.1:
            width = new_w
            log.debug("ChartAuditor fix: width increased to %.2f\"", width)
            changed = True

    # LEGEND_OVERLAP — structural fix already in _legend_kw; try type-specific fallbacks
    if "LEGEND_OVERLAP" in issue_types:
        if chart_type == "donut" and data.get("label_style") != "direct":
            data["label_style"] = "direct"
            log.debug("ChartAuditor fix: donut label_style → direct")
            changed = True
        elif len(data.get("series", [])) <= 1:
            # Single-series chart — legend is redundant; drop series name to suppress it
            for s in data.get("series", []):
                if s.get("name"):
                    s["name"] = ""
                    changed = True

    if not changed:
        return None, width, height

    return data, width, height


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
