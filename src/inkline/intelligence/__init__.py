"""Inkline Intelligence Layer — smart document and presentation design.

Provides rules-based (and optionally LLM-advised) layout, chart type,
and visual hierarchy decisions. Any client application gets intelligent
output without implementing its own presentation logic.

Usage::

    from inkline.intelligence import DesignAdvisor

    advisor = DesignAdvisor(brand="minimal", template="consulting")

    # Smart slides from structured data
    slides = advisor.design_deck(
        title="Project Corsair DD Summary",
        sections=[
            {"type": "executive_summary", "metrics": {...}, "narrative": "..."},
            {"type": "financial_overview", "table_data": {...}},
        ],
    )

    # Smart document from markdown
    doc_source = advisor.design_document(
        markdown="# Due Diligence Report\\n...",
        exhibits=[{"type": "table", "data": {...}}],
    )
"""

from inkline.intelligence.design_advisor import DesignAdvisor
from inkline.intelligence.overflow_audit import (
    audit_deck,
    audit_image,
    audit_slide,
    format_report,
    AuditWarning,
)

__all__ = [
    "DesignAdvisor",
    "audit_deck",
    "audit_image",
    "audit_slide",
    "format_report",
    "AuditWarning",
]
