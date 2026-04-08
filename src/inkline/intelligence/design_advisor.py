"""Design Advisor — the intelligent orchestrator for Inkline.

Takes structured content (WHAT to present) and decides HOW:
layout, chart type, visual hierarchy, and emphasis.

Three modes:
- "rules" — deterministic heuristics, no API calls (default)
- "advised" — rules decide, LLM reviews and suggests tweaks
- "driven" — LLM makes all design decisions from structured prompt
"""

from __future__ import annotations

import logging
from typing import Any, Optional

log = logging.getLogger(__name__)


class DesignAdvisor:
    """Intelligent presentation design engine.

    Parameters
    ----------
    brand : str
        Brand name (e.g., "aigis", "tvf", "aria", "sparkdcs").
    template : str
        Slide template style (e.g., "consulting", "executive", "brand").
    mode : str
        Intelligence mode: "rules" (default), "advised", or "driven".
    """

    def __init__(
        self,
        brand: str = "aigis",
        template: str = "brand",
        mode: str = "rules",
    ):
        self.brand = brand
        self.template = template
        self.mode = mode

    def design_deck(
        self,
        title: str,
        sections: list[dict[str, Any]],
        *,
        date: str = "",
        subtitle: str = "",
        contact: Optional[dict] = None,
    ) -> list[dict[str, Any]]:
        """Design a slide deck from structured content sections.

        Parameters
        ----------
        title : str
            Deck title.
        sections : list[dict]
            Content sections, each with ``type`` and data fields.
        date : str
            Date string.
        subtitle : str
            Subtitle / tagline.
        contact : dict, optional
            Closing slide contact info: ``name``, ``role``, ``email``.

        Returns
        -------
        list[dict]
            List of slide specs ready for ``export_typst_slides()``.
        """
        from inkline.intelligence.chart_advisor import recommend_chart, recommend_slide_type
        from inkline.intelligence.content_analyzer import analyze_content
        from inkline.intelligence.layout_selector import plan_deck_flow

        # 1. Analyze all sections
        analyses = [analyze_content(s) for s in sections]

        # 2. Plan layouts with flow variety
        layouts = plan_deck_flow(analyses)

        # 3. Build slide specs
        slides = []

        # Title slide
        slides.append({
            "slide_type": "title",
            "data": {
                "company": title,
                "tagline": subtitle,
                "date": date,
                "left_footer": "",
            },
        })

        # Content slides
        for section, analysis, layout in zip(sections, analyses, layouts):
            slide = self._section_to_slide(section, analysis, layout)
            if slide:
                slides.append(slide)

        # Closing slide
        if contact:
            slides.append({
                "slide_type": "closing",
                "data": contact,
            })

        log.info(
            "DesignAdvisor: planned %d slides for '%s' (mode=%s, brand=%s, template=%s)",
            len(slides), title, self.mode, self.brand, self.template,
        )

        return slides

    def design_document(
        self,
        markdown: str = "",
        *,
        title: str = "",
        subtitle: str = "",
        date: str = "",
        author: str = "",
        exhibits: Optional[list[dict]] = None,
    ) -> dict:
        """Design a document layout from markdown and optional exhibits.

        Returns a dict ready for ``export_typst_document()``.
        """
        return {
            "markdown": markdown,
            "title": title,
            "subtitle": subtitle,
            "date": date,
            "author": author,
            "brand": self.brand,
            "exhibits": exhibits or [],
        }

    # -- Internal helpers --------------------------------------------------

    def _section_to_slide(
        self,
        section: dict,
        analysis: Any,
        layout: Any,
    ) -> dict | None:
        """Convert a content section + layout decision into a slide spec."""
        section_label = section.get("section", section.get("type", "").replace("_", " ").title())
        section_title = section.get("title", "")

        slide_type = layout.slide_type

        if slide_type == "content":
            return self._build_content_slide(section, section_label, section_title)
        if slide_type == "three_card":
            return self._build_card_slide(section, section_label, section_title, 3, layout.highlight_index)
        if slide_type == "four_card":
            return self._build_card_slide(section, section_label, section_title, 4, layout.highlight_index)
        if slide_type == "stat":
            return self._build_stat_slide(section, section_label, section_title)
        if slide_type == "kpi_strip":
            return self._build_kpi_slide(section, section_label, section_title)
        if slide_type == "table":
            return self._build_table_slide(section, section_label, section_title)
        if slide_type == "split":
            return self._build_split_slide(section, section_label, section_title)
        if slide_type == "bar_chart":
            return self._build_bar_chart_slide(section, section_label, section_title)
        if slide_type == "chart":
            return self._build_chart_slide(section, section_label, section_title)

        # Fallback
        return self._build_content_slide(section, section_label, section_title)

    def _build_content_slide(self, section: dict, label: str, title: str) -> dict:
        items = section.get("items", [])
        if not items and section.get("narrative"):
            # Split narrative into bullet points
            narrative = section["narrative"]
            sentences = [s.strip() for s in narrative.replace("\n", " ").split(".") if s.strip()]
            items = [f"{s}." for s in sentences[:6]]
        return {
            "slide_type": "content",
            "data": {
                "section": label,
                "title": title or label,
                "items": items,
                "footnote": section.get("footnote", ""),
            },
        }

    def _build_card_slide(self, section: dict, label: str, title: str, n: int, highlight: int) -> dict:
        cards = section.get("cards", [])
        if not cards and section.get("items"):
            cards = [{"title": item, "body": ""} for item in section["items"][:n]]
        if not cards and section.get("metrics"):
            cards = [
                {"title": k, "body": str(v)}
                for k, v in list(section["metrics"].items())[:n]
            ]
        slide_type = "three_card" if n == 3 else "four_card"
        data: dict[str, Any] = {
            "section": label,
            "title": title or label,
            "cards": cards[:n],
            "footnote": section.get("footnote", ""),
        }
        if highlight >= 0:
            data["highlight_index"] = highlight
        return {"slide_type": slide_type, "data": data}

    def _build_stat_slide(self, section: dict, label: str, title: str) -> dict:
        metrics = section.get("metrics", {})
        stats = [
            {"value": str(v), "label": k, "desc": ""}
            for k, v in list(metrics.items())[:4]
        ]
        return {
            "slide_type": "stat",
            "data": {
                "section": label,
                "title": title or label,
                "stats": stats,
            },
        }

    def _build_kpi_slide(self, section: dict, label: str, title: str) -> dict:
        metrics = section.get("metrics", {})
        kpis = [
            {"value": str(v), "label": k, "highlight": i == 0}
            for i, (k, v) in enumerate(list(metrics.items())[:5])
        ]
        return {
            "slide_type": "kpi_strip",
            "data": {
                "section": label,
                "title": title or label,
                "kpis": kpis,
                "footnote": section.get("footnote", ""),
            },
        }

    def _build_table_slide(self, section: dict, label: str, title: str) -> dict:
        table_data = section.get("table_data", {})
        return {
            "slide_type": "table",
            "data": {
                "section": label,
                "title": title or label,
                "headers": table_data.get("headers", []),
                "rows": table_data.get("rows", []),
                "footnote": section.get("footnote", ""),
            },
        }

    def _build_split_slide(self, section: dict, label: str, title: str) -> dict:
        # Split narrative into two halves, or use left/right data
        left = section.get("left", {})
        right = section.get("right", {})
        if not left and section.get("narrative"):
            words = section["narrative"].split()
            mid = len(words) // 2
            left = {"title": "Overview", "items": [" ".join(words[:mid])]}
            right = {"title": "Details", "items": [" ".join(words[mid:])]}
        return {
            "slide_type": "split",
            "data": {
                "section": label,
                "title": title or label,
                "left_title": left.get("title", ""),
                "left_items": left.get("items", []),
                "right_title": right.get("title", ""),
                "right_items": right.get("items", []),
            },
        }

    def _build_bar_chart_slide(self, section: dict, label: str, title: str) -> dict:
        items = section.get("items", [])
        values = section.get("values", [])
        max_val = max(values) if values else 1
        bars = [
            {"label": item, "value": str(val), "pct": round(val / max_val * 100)}
            for item, val in zip(items, values)
        ]
        return {
            "slide_type": "bar_chart",
            "data": {
                "section": label,
                "title": title or label,
                "bars": bars,
                "footnote": section.get("footnote", ""),
            },
        }

    def _build_chart_slide(self, section: dict, label: str, title: str) -> dict:
        return {
            "slide_type": "chart",
            "data": {
                "section": label,
                "title": title or label,
                "image_path": section.get("image_path", ""),
                "footnote": section.get("footnote", ""),
            },
        }
