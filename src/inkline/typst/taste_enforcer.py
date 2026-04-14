"""Deterministic post-processing taste enforcement for Inkline.

Applied to all slide specs AFTER DesignAdvisor produces them and BEFORE
the Typst renderer runs. These rules are not suggestions — they are
enforced regardless of what the LLM requested.

Rules encode what a designer with good taste would always do:
- Bar charts in clean style (no axis chrome)
- Donut charts with direct radial labels when segments ≤ 6
- Scatter with named points always uses annotated labels
- accent_index auto-assigned if missing on bar charts
- Panel charts (inside multi_chart) suppress embedded titles

Usage::

    from inkline.typst.taste_enforcer import TasteEnforcer
    enforcer = TasteEnforcer()
    slides = enforcer.apply(slides)
"""

from __future__ import annotations

import logging
import re
from typing import Any

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Rule definitions
# ---------------------------------------------------------------------------

# Each rule is a dict with:
#   id         : short rule ID for logging
#   match_type : chart_type(s) this rule applies to (str or list, or "__all__")
#   match_context : "panel" | "full_width" | None (None = any)
#   condition  : callable(chart_data) → bool — True means "rule should fire"
#   enforce    : dict of key→value to set (or callable(chart_data) → dict)
#   reason     : short description for log output

_RULES: list[dict] = [

    # R-01: grouped_bar always uses clean style
    {
        "id": "R-01",
        "match_type": "grouped_bar",
        "match_context": None,
        "condition": lambda d: d.get("style") not in ("clean",),
        "enforce": {"style": "clean"},
        "reason": "axis chrome adds noise; clean style is always preferable for bar data",
    },

    # R-02: stacked_bar always uses clean style
    {
        "id": "R-02",
        "match_type": "stacked_bar",
        "match_context": None,
        "condition": lambda d: d.get("style") not in ("clean",),
        "enforce": {"style": "clean"},
        "reason": "axis chrome adds noise; same rule as grouped_bar",
    },

    # R-03: donut with ≤ 6 segments → direct radial labels, no legend
    {
        "id": "R-03",
        "match_type": ["donut", "pie"],
        "match_context": None,
        "condition": lambda d: (
            len(d.get("segments", [])) <= 6
            and d.get("label_style") not in ("direct",)
        ),
        "enforce": {"label_style": "direct"},
        "reason": "legend wastes space when segments are few enough to label directly (PT-14)",
    },

    # R-04: scatter with named points → annotated callout labels
    {
        "id": "R-04",
        "match_type": "scatter",
        "match_context": None,
        "condition": lambda d: (
            any(p.get("label") for p in d.get("points", []))
            and d.get("label_style") not in ("annotated",)
        ),
        "enforce": {"label_style": "annotated"},
        "reason": "named scatter points need callout boxes; plain dots lose the message (PT-4)",
    },

    # R-05: grouped_bar missing accent_index → infer from highest value
    {
        "id": "R-05",
        "match_type": "grouped_bar",
        "match_context": None,
        "condition": lambda d: "accent_index" not in d and d.get("categories"),
        "enforce": lambda d: {"accent_index": _infer_accent_index(d)},
        "reason": "accent as semantic signal; highest bar gets emphasis by default",
    },

    # R-06: panel chart inside multi_chart → clear embedded chart title
    #        (panel header already names the chart)
    {
        "id": "R-06",
        "match_type": "__all__",
        "match_context": "panel",
        "condition": lambda d: bool(d.get("chart_title")),
        "enforce": {"chart_title": None},
        "reason": "panel header already names the chart; embedded title duplicates (PT-6)",
    },

    # R-07: bar with > 12 categories → switch to horizontal orientation
    {
        "id": "R-07",
        "match_type": "grouped_bar",
        "match_context": None,
        "condition": lambda d: len(d.get("categories", [])) > 12,
        "enforce": {"orientation": "horizontal"},
        "reason": "vertical bars become unreadable past ~12 categories",
    },

    # R-08: line chart → always suppress right/top spines, no grid
    {
        "id": "R-08",
        "match_type": ["line_chart", "area_chart"],
        "match_context": None,
        "condition": lambda d: d.get("spine_style") not in ("minimal",),
        "enforce": {"spine_style": "minimal", "grid": False},
        "reason": "Pareto/Goldman standard: clean line on bottom/left axes only",
    },

    # R-09: dumbbell missing accent_direction → default to higher_is_better
    {
        "id": "R-09",
        "match_type": "dumbbell",
        "match_context": None,
        "condition": lambda d: "accent_direction" not in d,
        "enforce": {"accent_direction": "higher_is_better"},
        "reason": "default assumption: larger value = better (override with accent_direction in chart_data)",
    },

    # R-10: waterfall → clean style
    {
        "id": "R-10",
        "match_type": "waterfall",
        "match_context": None,
        "condition": lambda d: d.get("style") not in ("clean",),
        "enforce": {"style": "clean"},
        "reason": "waterfall charts benefit from same axis reduction as bar charts",
    },
]


# ---------------------------------------------------------------------------
# Accent index inference
# ---------------------------------------------------------------------------

def _infer_accent_index(chart_data: dict) -> int:
    """Return the 0-based index of the bar that should get accent colour.

    Logic (in priority order):
    1. If chart_data has a ``narrative`` key, scan it for keywords like
       "highest", "leading", "top", "best" and try to match a category name.
    2. Otherwise, return the index of the largest value in the first series.
    3. Fall back to 0.
    """
    categories = chart_data.get("categories", [])
    series = chart_data.get("series", [])
    narrative = chart_data.get("narrative", "")

    # Try narrative matching
    if narrative and categories:
        narrative_lower = narrative.lower()
        positive_keywords = ["highest", "leading", "top", "best", "largest", "biggest", "most"]
        for kw in positive_keywords:
            if kw in narrative_lower:
                # Try to find a category that appears after the keyword
                for i, cat in enumerate(categories):
                    if cat.lower() in narrative_lower:
                        return i

    # Fall back to highest value in first series
    if series and categories:
        values = series[0].get("values", [])
        if values:
            try:
                return values.index(max(values))
            except (ValueError, TypeError):
                pass

    # Also check flat "values" format (single-series bar)
    flat_values = chart_data.get("values", [])
    if flat_values:
        try:
            return flat_values.index(max(flat_values))
        except (ValueError, TypeError):
            pass

    return 0


# ---------------------------------------------------------------------------
# Main enforcer class
# ---------------------------------------------------------------------------

class TasteEnforcer:
    """Apply deterministic taste rules to a list of slide specs."""

    def __init__(self, rules: list[dict] | None = None):
        self._rules = rules if rules is not None else _RULES

    def apply(self, slides: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Apply all taste rules to the slide list in-place.

        Returns the same list (mutated) for convenience.
        """
        for slide in slides:
            self._apply_to_slide(slide)
        return slides

    def _apply_to_slide(self, slide: dict) -> None:
        """Apply rules to a single slide, including nested chart_request data."""
        data = slide.get("data", {})

        # Check for a chart_request embedded in this slide
        chart_req = data.get("chart_request")
        if chart_req:
            chart_type = chart_req.get("chart_type", "")
            chart_data = chart_req.get("chart_data", {})
            context = "full_width"
            changes = self._apply_rules(chart_type, chart_data, context)
            if changes:
                chart_req["chart_data"] = {**chart_data, **changes}
                data["chart_request"] = chart_req

        # Check for multi_chart with multiple chart_requests
        charts = data.get("charts", [])
        for chart_item in charts:
            inner_req = chart_item.get("chart_request")
            if inner_req:
                chart_type = inner_req.get("chart_type", "")
                chart_data = inner_req.get("chart_data", {})
                changes = self._apply_rules(chart_type, chart_data, context="panel")
                if changes:
                    inner_req["chart_data"] = {**chart_data, **changes}
                    chart_item["chart_request"] = inner_req

    def _apply_rules(
        self,
        chart_type: str,
        chart_data: dict,
        context: str,
    ) -> dict:
        """Return a dict of changes to apply (may be empty)."""
        changes: dict = {}

        for rule in self._rules:
            # Match chart type
            match_type = rule["match_type"]
            if match_type != "__all__":
                if isinstance(match_type, list):
                    if chart_type not in match_type:
                        continue
                elif chart_type != match_type:
                    continue

            # Match context
            match_ctx = rule.get("match_context")
            if match_ctx is not None and match_ctx != context:
                continue

            # Evaluate condition on current chart_data + pending changes
            effective_data = {**chart_data, **changes}
            try:
                if not rule["condition"](effective_data):
                    continue
            except Exception:
                continue

            # Compute enforce dict
            enforce = rule["enforce"]
            if callable(enforce):
                try:
                    enforce = enforce(effective_data)
                except Exception:
                    continue

            changes.update(enforce)
            log.debug(
                "TasteEnforcer %s applied to %s: %s — %s",
                rule["id"], chart_type, enforce, rule["reason"],
            )

        return changes
