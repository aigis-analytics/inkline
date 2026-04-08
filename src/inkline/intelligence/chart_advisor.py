"""Chart advisor — recommends the best chart type for a given data shape.

Rules-based first (deterministic, no API calls), with optional LLM
override for edge cases.
"""

from __future__ import annotations

from typing import Any

from inkline.intelligence.content_analyzer import ContentAnalysis, ContentType


# ---------------------------------------------------------------------------
# Chart type recommendations
# ---------------------------------------------------------------------------

# Priority-ordered rules: first match wins
CHART_RULES: list[tuple[str, dict, str]] = [
    # (chart_type, conditions, rationale)
    ("line_chart", {"content_type": ContentType.TIME_SERIES}, "Time series data is best shown as a line chart"),
    ("horizontal_bar", {"content_type": ContentType.COMPARISON, "data_points_max": 10}, "Category comparisons with <=10 items work well as horizontal bars"),
    ("stacked_bar", {"content_type": ContentType.COMPARISON, "has_percentages": True}, "Percentage breakdowns across categories map to stacked bars"),
    ("donut", {"content_type": ContentType.PART_OF_WHOLE, "data_points_max": 6}, "Part-of-whole with <=6 segments is clear as a donut chart"),
    ("waterfall", {"content_type": ContentType.FLOW}, "Flow/change data is best shown as a waterfall"),
    ("two_by_two_matrix", {"content_type": ContentType.POSITIONING}, "Competitive positioning maps to a 2x2 matrix"),
    ("rag_cards", {"content_type": ContentType.RISK, "has_rag_status": True}, "Risk data with RAG statuses maps to RAG cards"),
    ("risk_heatmap", {"content_type": ContentType.RISK}, "Risk data without explicit RAG maps to a heatmap"),
    ("data_table", {"content_type": ContentType.TABLE, "num_rows_min": 5}, "Dense tabular data (5+ rows) is best as a formatted table"),
    ("kpi_strip", {"content_type": ContentType.METRICS, "data_points_max": 5}, "3-5 KPI metrics work well as a stat strip"),
    ("hero_stat", {"content_type": ContentType.METRICS, "data_points_max": 1}, "Single standout metric gets hero treatment"),
    ("stat_cards", {"content_type": ContentType.METRICS}, "Multiple metrics default to stat cards"),
    ("scatter", {"content_type": ContentType.COMPARISON, "has_time_axis": True}, "Correlation with time axis suggests a scatter plot"),
]


def recommend_chart(analysis: ContentAnalysis) -> str:
    """Recommend the best chart type for the given content analysis.

    Parameters
    ----------
    analysis : ContentAnalysis
        Result from ``analyze_content()``.

    Returns
    -------
    str
        Recommended chart type name.
    """
    for chart_type, conditions, _rationale in CHART_RULES:
        if _matches(analysis, conditions):
            return chart_type

    # Fallback
    if analysis.num_rows > 0:
        return "data_table"
    if analysis.data_points > 0:
        return "horizontal_bar"
    return "narrative"


def recommend_chart_with_rationale(analysis: ContentAnalysis) -> tuple[str, str]:
    """Like recommend_chart, but also returns the reasoning."""
    for chart_type, conditions, rationale in CHART_RULES:
        if _matches(analysis, conditions):
            return chart_type, rationale
    return "data_table", "Default: tabular display for structured data"


def _matches(analysis: ContentAnalysis, conditions: dict) -> bool:
    """Check if an analysis matches all conditions in a rule."""
    for key, expected in conditions.items():
        if key == "content_type":
            if analysis.content_type != expected:
                return False
        elif key == "data_points_max":
            if analysis.data_points > expected:
                return False
        elif key == "data_points_min":
            if analysis.data_points < expected:
                return False
        elif key == "num_rows_min":
            if analysis.num_rows < expected:
                return False
        elif key == "num_rows_max":
            if analysis.num_rows > expected:
                return False
        elif key == "has_percentages":
            if analysis.has_percentages != expected:
                return False
        elif key == "has_rag_status":
            if analysis.has_rag_status != expected:
                return False
        elif key == "has_time_axis":
            if analysis.has_time_axis != expected:
                return False
    return True


# ---------------------------------------------------------------------------
# Slide layout recommendations
# ---------------------------------------------------------------------------

LAYOUT_RULES = {
    "hero_stat": "stat",           # Single big number → stat slide
    "kpi_strip": "kpi_strip",     # 3-5 KPIs → KPI strip slide
    "stat_cards": "stat",          # Multiple stats → stat slide
    "data_table": "table",         # Table → table slide
    "horizontal_bar": "bar_chart", # Bar chart → bar chart slide
    "line_chart": "chart",         # Line chart → image chart slide
    "donut": "chart",              # Donut → image chart slide
    "waterfall": "chart",          # Waterfall → image chart slide
    "scatter": "chart",            # Scatter → image chart slide
    "stacked_bar": "chart",        # Stacked → image chart slide
    "two_by_two_matrix": "four_card",  # 2x2 → four card slide
    "rag_cards": "three_card",     # RAG → three card slide
    "risk_heatmap": "table",       # Heatmap → table slide
    "narrative": "content",        # Text → content slide
}


def recommend_slide_type(chart_type: str) -> str:
    """Map a chart type recommendation to a Typst slide type."""
    return LAYOUT_RULES.get(chart_type, "content")
