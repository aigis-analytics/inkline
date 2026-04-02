"""Inkline Slides — Google Slides generation with brand support.

Scaffold for Phase 3 implementation. The SlideBuilder fluent API
will be implemented here.

Usage (planned)::

    from inkline.slides import SlideBuilder

    deck = (
        SlideBuilder(title="Project Report", brand="aigis")
        .slide()
            .title("Executive Summary")
            .bullet_list(["Point 1", "Point 2"])
        .slide()
            .title("Financial Overview")
            .table(headers=["Metric", "Value"], rows=[["NPV", "$32M"]])
        .build()
    )
    print(deck.url)
"""

from __future__ import annotations


class SlideBuilder:
    """Fluent API for constructing Google Slides presentations.

    Phase 3 implementation — currently a stub that documents the planned API.
    """

    def __init__(self, title: str = "Untitled", brand: str = "aigis"):
        self._title = title
        self._brand_name = brand
        self._slides: list[dict] = []
        raise NotImplementedError(
            "SlideBuilder is planned for Phase 3. "
            "Use inkline.export_html() or inkline.export_pdf() for now."
        )
