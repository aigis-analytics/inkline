"""Content analyzer — examines data shape and structure to classify content types.

Used by DesignAdvisor to determine what kind of exhibit/layout best
represents a given piece of content.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ContentType(Enum):
    """Classification of content for layout decisions."""
    NARRATIVE = "narrative"          # Long-form text, paragraphs
    METRICS = "metrics"             # Key numbers / KPIs
    TABLE = "table"                 # Structured tabular data
    TIME_SERIES = "time_series"     # Data over time
    COMPARISON = "comparison"       # Comparing items/categories
    PART_OF_WHOLE = "part_of_whole" # Percentage breakdowns
    RANKING = "ranking"             # Ordered list by value
    RISK = "risk"                   # RAG / severity assessment
    FLOW = "flow"                   # Process / waterfall / timeline
    POSITIONING = "positioning"     # 2x2 matrix / competitive map
    IMAGE = "image"                 # Chart image / photo
    MIXED = "mixed"                 # Multiple types combined


@dataclass
class ContentAnalysis:
    """Result of analyzing a content section."""
    content_type: ContentType
    data_points: int = 0          # Number of data values
    has_time_axis: bool = False
    has_categories: bool = False
    has_percentages: bool = False
    has_rag_status: bool = False
    narrative_length: int = 0     # Word count of text content
    num_columns: int = 0          # For tabular data
    num_rows: int = 0
    suggested_emphasis: str = ""  # What to make the hero element


def analyze_content(section: dict[str, Any]) -> ContentAnalysis:
    """Analyze a content section dict and classify it.

    Parameters
    ----------
    section : dict
        Section with keys like ``type``, ``metrics``, ``narrative``,
        ``table_data``, ``series``, ``items``, etc.

    Returns
    -------
    ContentAnalysis
        Classification and metadata about the content.
    """
    section_type = section.get("type", "")

    # Direct type hints from the caller
    type_map = {
        "executive_summary": ContentType.MIXED,
        "financial_overview": ContentType.TABLE,
        "production_analysis": ContentType.TIME_SERIES,
        "risk_assessment": ContentType.RISK,
        "competitive_positioning": ContentType.POSITIONING,
        "timeline": ContentType.FLOW,
        "kpi_dashboard": ContentType.METRICS,
    }

    if section_type in type_map:
        ct = type_map[section_type]
    else:
        ct = _infer_content_type(section)

    # Count data points
    metrics = section.get("metrics", {})
    table_data = section.get("table_data", {})
    series = section.get("series", [])
    items = section.get("items", [])
    narrative = section.get("narrative", "")

    data_points = len(metrics) + sum(len(r) for r in table_data.get("rows", [])) + len(series) + len(items)

    return ContentAnalysis(
        content_type=ct,
        data_points=data_points,
        has_time_axis="date" in str(table_data.get("headers", [])).lower() or bool(series),
        has_categories=bool(items) or bool(table_data.get("headers")),
        has_percentages=any("%" in str(v) for v in metrics.values()) if metrics else False,
        has_rag_status=any(k in section for k in ("rag", "risk", "severity", "status")),
        narrative_length=len(narrative.split()) if narrative else 0,
        num_columns=len(table_data.get("headers", [])),
        num_rows=len(table_data.get("rows", [])),
        suggested_emphasis=_pick_emphasis(metrics, narrative),
    )


def _infer_content_type(section: dict) -> ContentType:
    """Infer content type from available data fields."""
    if section.get("metrics") and not section.get("table_data"):
        return ContentType.METRICS
    if section.get("table_data"):
        headers = section["table_data"].get("headers", [])
        if any(h.lower() in ("date", "year", "month", "quarter") for h in headers):
            return ContentType.TIME_SERIES
        return ContentType.TABLE
    if section.get("series"):
        return ContentType.TIME_SERIES
    if section.get("items") and section.get("values"):
        return ContentType.COMPARISON
    if section.get("narrative") and len(section.get("narrative", "").split()) > 50:
        return ContentType.NARRATIVE
    if section.get("rag") or section.get("risk"):
        return ContentType.RISK
    return ContentType.NARRATIVE


def _pick_emphasis(metrics: dict, narrative: str) -> str:
    """Pick the most impactful metric for hero treatment."""
    if not metrics:
        return ""
    # Prefer monetary values, then percentages, then counts
    for key, val in metrics.items():
        val_str = str(val)
        if "$" in val_str or "USD" in val_str:
            return key
    for key, val in metrics.items():
        if "%" in str(val):
            return key
    # Return the first metric
    return next(iter(metrics), "")
