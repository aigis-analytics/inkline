"""Layout selector — chooses slide layouts based on content density and hierarchy.

Implements the 60-30-10 visual hierarchy rule:
- 60% dominant (background, primary content area)
- 30% secondary (supporting cards, charts)
- 10% accent (hero stats, CTAs, highlights)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from inkline.intelligence.content_analyzer import ContentAnalysis, ContentType


@dataclass
class LayoutDecision:
    """Result of layout selection."""
    slide_type: str
    num_columns: int = 1
    has_hero: bool = False
    highlight_index: int = -1  # Which card to accent (-1 = none)
    rationale: str = ""


def select_layout(analysis: ContentAnalysis, context: dict[str, Any] | None = None) -> LayoutDecision:
    """Select the best slide layout for a given content analysis.

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

    # Metrics-heavy content
    if ct == ContentType.METRICS:
        if analysis.data_points <= 1:
            return LayoutDecision(
                slide_type="stat",
                num_columns=1,
                has_hero=True,
                rationale="Single metric gets hero treatment",
            )
        if analysis.data_points <= 3:
            return LayoutDecision(
                slide_type="stat",
                num_columns=3,
                has_hero=True,
                highlight_index=1,
                rationale="2-3 metrics in stat row with center highlighted",
            )
        if analysis.data_points <= 5:
            return LayoutDecision(
                slide_type="kpi_strip",
                num_columns=analysis.data_points,
                rationale="4-5 KPIs in a strip",
            )
        return LayoutDecision(
            slide_type="table",
            rationale="6+ metrics overflow to table format",
        )

    # Tabular data
    if ct == ContentType.TABLE:
        return LayoutDecision(
            slide_type="table",
            num_columns=analysis.num_columns,
            rationale="Structured tabular data → table slide",
        )

    # Time series
    if ct == ContentType.TIME_SERIES:
        return LayoutDecision(
            slide_type="chart",
            rationale="Time series → line chart slide",
        )

    # Comparison / ranking
    if ct in (ContentType.COMPARISON, ContentType.RANKING):
        if analysis.data_points <= 3:
            return LayoutDecision(
                slide_type="three_card",
                num_columns=3,
                highlight_index=1,
                rationale="2-3 comparison items → three card with highlight",
            )
        if analysis.data_points <= 4:
            return LayoutDecision(
                slide_type="four_card",
                num_columns=2,
                rationale="4 items → 2x2 grid",
            )
        return LayoutDecision(
            slide_type="bar_chart",
            rationale="5+ comparison items → bar chart",
        )

    # Risk / RAG
    if ct == ContentType.RISK:
        if analysis.has_rag_status:
            return LayoutDecision(
                slide_type="three_card",
                num_columns=3,
                rationale="RAG assessment → three cards (R/A/G)",
            )
        return LayoutDecision(
            slide_type="table",
            rationale="Risk data without RAG → risk table",
        )

    # Positioning
    if ct == ContentType.POSITIONING:
        return LayoutDecision(
            slide_type="four_card",
            num_columns=2,
            rationale="Competitive positioning → 2x2 matrix",
        )

    # Flow
    if ct == ContentType.FLOW:
        return LayoutDecision(
            slide_type="chart",
            rationale="Process flow → waterfall/timeline chart",
        )

    # Mixed content (e.g., executive summary)
    if ct == ContentType.MIXED:
        if analysis.narrative_length > 100 and analysis.data_points > 0:
            return LayoutDecision(
                slide_type="split",
                num_columns=2,
                rationale="Mixed narrative + data → split slide",
            )
        if analysis.data_points >= 3:
            return LayoutDecision(
                slide_type="three_card",
                num_columns=3,
                highlight_index=0,
                rationale="Mixed with 3+ data points → three card",
            )

    # Default: content slide with bullets
    return LayoutDecision(
        slide_type="content",
        rationale="Default: narrative content slide",
    )


def plan_deck_flow(analyses: list[ContentAnalysis]) -> list[LayoutDecision]:
    """Plan layouts for an entire deck, considering flow and variety.

    Avoids consecutive identical layouts and ensures visual rhythm.
    """
    decisions = []
    prev_type = ""

    for i, analysis in enumerate(analyses):
        decision = select_layout(analysis, context={"position": i, "total": len(analyses)})

        # Avoid 3+ consecutive same layouts — switch to alternative
        if len(decisions) >= 2 and decisions[-1].slide_type == prev_type == decision.slide_type:
            decision = _alternative_layout(decision)

        prev_type = decisions[-1].slide_type if decisions else ""
        decisions.append(decision)

    return decisions


def _alternative_layout(decision: LayoutDecision) -> LayoutDecision:
    """Provide an alternative layout to break visual monotony."""
    alternatives = {
        "content": "split",
        "three_card": "content",
        "table": "bar_chart",
        "stat": "kpi_strip",
        "chart": "split",
    }
    alt_type = alternatives.get(decision.slide_type, "content")
    return LayoutDecision(
        slide_type=alt_type,
        rationale=f"Alternative to avoid 3+ consecutive {decision.slide_type} slides",
    )
