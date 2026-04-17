"""Layout selector — chooses slide layouts based on content density and hierarchy.

Implements the Visual-First Exhaustion Protocol (VFEP): text-heavy layouts are
residual, only used after quantitative, sequence, comparison, and categorical
visual options have been genuinely attempted and found inapplicable.

Tier ordering (lowest number = highest visual priority):
  T1 — Quantitative (chart_caption, dashboard, kpi_strip, stat, bar_chart, multi_chart)
  T2 — Sequence / Journey (process_flow, timeline)
  T3 — Comparison / Contrast (comparison, three_card used as before/after)
  T4 — Grouped Categories / Infographic (feature_grid, icon_stat, three_card, four_card)
  T5 — Structured Text — LAST RESORT (split, content, table)
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from enum import IntEnum
from typing import Any

from inkline.intelligence.content_analyzer import ContentAnalysis, ContentType


class VisualTier(IntEnum):
    """VFEP tier assignment — lower = more visual."""
    QUANTITATIVE = 1
    SEQUENCE     = 2
    CONTRAST     = 3
    CATEGORICAL  = 4
    TEXT         = 5


@dataclass
class LayoutDecision:
    """Result of layout selection."""
    slide_type: str
    num_columns: int = 1
    has_hero: bool = False
    highlight_index: int = -1  # Which card to accent (-1 = none)
    max_items: int = 0         # Max content items that fit (0 = no limit)
    rationale: str = ""


# Content capacity per slide type (matches TypstSlideRenderer constants)
SLIDE_CAPACITY: dict[str, int] = {
    "content": 6,        # bullet points
    "table": 10,         # data rows (renderer auto-shrinks font for 7-12 rows)
    "bar_chart": 8,      # bars
    "three_card": 3,     # cards
    "four_card": 4,      # cards
    "stat": 4,           # hero stats
    "kpi_strip": 5,      # KPI cards
    "split": 6,          # bullets per side
    "timeline": 6,       # milestone nodes
    "process_flow": 4,   # steps
    "progress_bars": 6,  # bars (audit-validated; 7 overflows)
    "pyramid": 5,        # tiers
    "comparison": 6,     # rows per side
    "feature_grid": 6,   # features (3×2 grid)
    "dashboard": 3,      # bullets in right column (caps the limiting field)
    "chart_caption": 5,  # bullets in takeaways panel
}


# VFEP tier assignment for every slide type.
LAYOUT_TIER: dict[str, VisualTier] = {
    "chart_caption": VisualTier.QUANTITATIVE,
    "bar_chart":     VisualTier.QUANTITATIVE,
    "kpi_strip":     VisualTier.QUANTITATIVE,
    "stat":          VisualTier.QUANTITATIVE,
    "dashboard":     VisualTier.QUANTITATIVE,
    "multi_chart":   VisualTier.QUANTITATIVE,
    "chart":         VisualTier.QUANTITATIVE,
    "process_flow":  VisualTier.SEQUENCE,
    "timeline":      VisualTier.SEQUENCE,
    "comparison":    VisualTier.CONTRAST,
    "feature_grid":  VisualTier.CATEGORICAL,
    "icon_stat":     VisualTier.CATEGORICAL,
    "three_card":    VisualTier.CATEGORICAL,
    "four_card":     VisualTier.CATEGORICAL,
    "pyramid":       VisualTier.CATEGORICAL,
    "progress_bars": VisualTier.CATEGORICAL,
    "split":         VisualTier.TEXT,
    "content":       VisualTier.TEXT,
    "table":         VisualTier.TEXT,
}


# Rotation alternatives for each slide type.
# When _alternative_layout is called, it cycles through this list —
# selecting the first option not already in the recent history.
# Crucially, text layouts (split/content) rotate through visual alternatives,
# not between themselves.
ALTERNATIVES: dict[str, list[str]] = {
    "split":         ["comparison", "feature_grid", "process_flow", "three_card"],
    "content":       ["bar_chart", "feature_grid", "icon_stat", "comparison"],
    "four_card":     ["feature_grid", "icon_stat", "three_card", "bar_chart"],
    "three_card":    ["feature_grid", "comparison", "icon_stat", "process_flow"],
    "table":         ["bar_chart", "kpi_strip", "stat", "dashboard"],
    "stat":          ["kpi_strip", "icon_stat", "dashboard", "bar_chart"],
    "chart":         ["multi_chart", "dashboard", "kpi_strip", "comparison"],
    "kpi_strip":     ["stat", "dashboard", "bar_chart", "feature_grid"],
    "bar_chart":     ["kpi_strip", "stat", "comparison", "feature_grid"],
    "comparison":    ["feature_grid", "split", "three_card", "bar_chart"],
    "feature_grid":  ["three_card", "icon_stat", "comparison", "split"],
    "process_flow":  ["timeline", "comparison", "feature_grid", "split"],
    "timeline":      ["process_flow", "comparison", "feature_grid", "split"],
}


def _with_capacity(decision: LayoutDecision) -> LayoutDecision:
    """Attach max_items capacity from SLIDE_CAPACITY to a decision."""
    decision.max_items = SLIDE_CAPACITY.get(decision.slide_type, 0)
    return decision


def select_layout(analysis: ContentAnalysis, context: dict[str, Any] | None = None) -> LayoutDecision:
    """Select the best slide layout for a given content analysis.

    Applies VFEP: quantitative > sequence > contrast > categorical > text.

    Parameters
    ----------
    analysis : ContentAnalysis
        Content classification from the analyzer.
    context : dict, optional
        Additional context (e.g., position in deck, adjacent slides).

    Returns
    -------
    LayoutDecision
        Layout specification.
    """
    ct = analysis.content_type

    # Metrics-heavy content (T1)
    if ct == ContentType.METRICS:
        if analysis.data_points <= 1:
            return _with_capacity(LayoutDecision(
                slide_type="stat", num_columns=1, has_hero=True,
                rationale="Single metric gets hero treatment",
            ))
        if analysis.data_points <= 3:
            return _with_capacity(LayoutDecision(
                slide_type="stat", num_columns=3, has_hero=True, highlight_index=1,
                rationale="2-3 metrics in stat row with center highlighted",
            ))
        if analysis.data_points <= 5:
            return _with_capacity(LayoutDecision(
                slide_type="kpi_strip", num_columns=analysis.data_points,
                rationale="4-5 KPIs in a strip",
            ))
        return _with_capacity(LayoutDecision(
            slide_type="table", rationale="6+ metrics overflow to table format",
        ))

    # Tabular data (T1/T5 depending on whether it has quantitative context)
    if ct == ContentType.TABLE:
        return _with_capacity(LayoutDecision(
            slide_type="table", num_columns=analysis.num_columns,
            rationale="Structured tabular data → table slide",
        ))

    # Time series (T1)
    if ct == ContentType.TIME_SERIES:
        return _with_capacity(LayoutDecision(
            slide_type="chart", rationale="Time series → line chart slide",
        ))

    # Comparison / ranking — T3 or T4 depending on item count
    if ct == ContentType.COMPARISON:
        if analysis.data_points <= 3:
            return _with_capacity(LayoutDecision(
                slide_type="three_card", num_columns=3, highlight_index=1,
                rationale="2-3 comparison/card items → three card with highlight",
            ))
        if analysis.data_points == 4:
            return _with_capacity(LayoutDecision(
                slide_type="four_card", num_columns=2,
                rationale="4 card items → 2x2 grid",
            ))
        if analysis.data_points <= 6:
            return _with_capacity(LayoutDecision(
                slide_type="feature_grid", num_columns=3,
                rationale="5-6 card items → feature grid (3×2)",
            ))
        return _with_capacity(LayoutDecision(
            slide_type="bar_chart", rationale="7+ comparison items → bar chart",
        ))

    if ct == ContentType.RANKING:
        if analysis.data_points <= 3:
            return _with_capacity(LayoutDecision(
                slide_type="three_card", num_columns=3, highlight_index=1,
                rationale="2-3 ranking items → three card",
            ))
        if analysis.data_points <= 4:
            return _with_capacity(LayoutDecision(
                slide_type="four_card", num_columns=2,
                rationale="4 ranking items → 2x2 grid",
            ))
        return _with_capacity(LayoutDecision(
            slide_type="bar_chart", rationale="5+ ranking items → bar chart",
        ))

    # Risk / RAG — VFEP T3: try comparison before falling back to split
    if ct == ContentType.RISK:
        if analysis.has_rag_status:
            return _with_capacity(LayoutDecision(
                slide_type="three_card", num_columns=3,
                rationale="RAG assessment → three cards (R/A/G)",
            ))
        if analysis.data_points <= 3:
            return _with_capacity(LayoutDecision(
                slide_type="three_card", num_columns=3,
                rationale="Risk dict items → three card layout",
            ))
        # T3 before T5: risk content often has a before/after contrast
        return _with_capacity(LayoutDecision(
            slide_type="comparison",
            rationale="Risk data without RAG — comparison layout (T3 before T5)",
        ))

    # Positioning (T4)
    if ct == ContentType.POSITIONING:
        return _with_capacity(LayoutDecision(
            slide_type="four_card", num_columns=2,
            rationale="Competitive positioning → 2x2 matrix",
        ))

    # Flow — T2 (sequence)
    if ct == ContentType.FLOW:
        if analysis.data_points > 0:
            return _with_capacity(LayoutDecision(
                slide_type="timeline", rationale="Timeline/flow dict items → timeline slide",
            ))
        return _with_capacity(LayoutDecision(
            slide_type="process_flow", rationale="Process flow → process_flow slide",
        ))

    # Mixed content — VFEP: probe T1→T4 before defaulting to split
    if ct == ContentType.MIXED:
        # T1: if it has data points, prefer a visual grouping
        if analysis.data_points >= 3:
            return _with_capacity(LayoutDecision(
                slide_type="three_card", num_columns=3, highlight_index=0,
                rationale="Mixed with 3+ data points → three card (T4)",
            ))
        # T3: narrative + some data suggests a comparison or split is appropriate,
        # but prefer comparison first (T3) over split (T5)
        if analysis.narrative_length > 100 and analysis.data_points > 0:
            return _with_capacity(LayoutDecision(
                slide_type="comparison", num_columns=2,
                rationale="Mixed narrative + data → comparison layout (T3 before split)",
            ))

    # T5 — Last resort text layout
    return _with_capacity(LayoutDecision(
        slide_type="content", rationale="T1-T4 exhausted: narrative content slide (T5)",
    ))


def plan_deck_flow(analyses: list[ContentAnalysis]) -> list[LayoutDecision]:
    """Plan layouts for an entire deck, considering flow and variety.

    Maintains a sliding window of the last 5 slide types. When a layout
    would create 3+ consecutive identical types, _step_up_tier() is called
    to force a visually higher-tier alternative.
    """
    decisions: list[LayoutDecision] = []
    history: deque[str] = deque(maxlen=5)

    for i, analysis in enumerate(analyses):
        decision = select_layout(analysis, context={"position": i, "total": len(analyses)})

        # Avoid 3+ consecutive identical layouts
        if len(decisions) >= 2 and (
            decisions[-1].slide_type == decisions[-2].slide_type == decision.slide_type
        ):
            upgraded = _step_up_tier(decision, list(history))
            if upgraded is not None:
                decision = upgraded

        decisions.append(decision)
        history.append(decision.slide_type)

    return decisions


def _alternative_layout(current_type: str, history: list[str]) -> str:
    """Return an alternative layout that breaks visual monotony.

    Cycles through ALTERNATIVES[current_type], selecting the first option
    not already present in the recent history. Falls back to the first
    option if all alternatives have been used recently.
    """
    options = ALTERNATIVES.get(current_type, ["comparison", "feature_grid", "bar_chart"])
    recent = set(history[-3:]) if history else set()
    for option in options:
        if option not in recent:
            return option
    return options[0]


def _step_up_tier(decision: LayoutDecision, history: list[str]) -> LayoutDecision | None:
    """Force a higher-tier layout to break consecutive same-type repetition.

    Walks up the VFEP tier stack from the current slide's tier, attempting
    to find a viable alternative at a lower (more visual) tier number.
    Returns None if no viable step-up exists (very rare — only pure
    narrative content that genuinely cannot be visualised).
    """
    current_tier = LAYOUT_TIER.get(decision.slide_type, VisualTier.TEXT)
    alt_type = _alternative_layout(decision.slide_type, history)
    alt_tier = LAYOUT_TIER.get(alt_type, VisualTier.TEXT)

    if alt_tier <= current_tier:
        # Good: the alternative is at the same or higher visual tier
        return _with_capacity(LayoutDecision(
            slide_type=alt_type,
            rationale=f"Step-up from {decision.slide_type} (T{current_tier}) → {alt_type} (T{alt_tier})",
        ))

    # Fallback: just use the alternative even if same tier — at least it's different
    return _with_capacity(LayoutDecision(
        slide_type=alt_type,
        rationale=f"Variety break: {decision.slide_type} → {alt_type}",
    ))
