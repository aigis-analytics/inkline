"""Inkline Intelligence Layer — smart document and presentation design.

Provides rules-based (and optionally LLM-advised) layout, chart type,
and visual hierarchy decisions. Any client (Aigis, Aria, etc.) gets
intelligent output without implementing their own presentation logic.

Usage::

    from inkline.intelligence import DesignAdvisor

    advisor = DesignAdvisor(brand="aigis", template="consulting")

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

__all__ = ["DesignAdvisor"]
