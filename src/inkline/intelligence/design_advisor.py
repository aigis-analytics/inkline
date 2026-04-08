"""Design Advisor — the intelligent orchestrator for Inkline.

Takes structured content (WHAT to present) and decides HOW:
layout, chart type, visual hierarchy, and emphasis.

Three modes:
- "llm" — LLM makes design decisions using playbook context (default)
- "rules" — deterministic heuristics, no API calls (fallback)
- "advised" — rules decide, LLM reviews and suggests tweaks

The LLM mode feeds playbook knowledge as system context and asks
Claude to produce optimal slide specs for the given content.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Optional

log = logging.getLogger(__name__)

# Available slide types that the Typst renderer supports
SLIDE_TYPES = [
    "title", "content", "three_card", "four_card", "stat",
    "table", "split", "chart", "bar_chart", "kpi_strip", "closing",
]

# Slide type descriptions for the LLM
SLIDE_TYPE_GUIDE = """
Available slide types (use these exact names):

STANDARD LAYOUTS:
- title: Opening slide. data: {company, tagline, date, subtitle, left_footer}
- content: Bullet list. data: {section, title, items (list of strings), footnote}
- three_card: 3 equal cards. data: {section, title, cards [{title, body}], highlight_index (0-2), footnote}
- four_card: 2x2 card grid. data: {section, title, cards [{title, body}], footnote}
- stat: 2-4 hero statistics. data: {section, title, stats [{value, label, desc}]}
- table: Data table. data: {section, title, headers (list), rows (list of lists), footnote}
- split: Two-column layout. data: {section, title, left_title, left_items, right_title, right_items}
- bar_chart: Horizontal bars. data: {section, title, bars [{label, value, pct (0-100)}], footnote}
- kpi_strip: 3-5 metric cards. data: {section, title, kpis [{value, label, highlight (bool)}], footnote}
- closing: Final slide. data: {name, role, email, company, tagline}

INFOGRAPHIC LAYOUTS:
- timeline: Horizontal milestone flow. data: {section, title, milestones [{date, label, desc?}], footnote}
- process_flow: Numbered step sequence with arrows. data: {section, title, steps [{number, title, desc}], footnote}
- icon_stat: Big number + emoji/icon + label. data: {section, title, stats [{value, icon, label, desc?}], footnote}
- progress_bars: Labelled percentage bars. data: {section, title, bars [{label, pct (0-100), value?}], footnote}
- pyramid: 3-5 tier hierarchy (top=smallest). data: {section, title, tiers [{label, desc?}], footnote}
- comparison: Structured side-by-side with metrics. data: {section, title, left {name, items [{label, value}]}, right {name, items [{label, value}]}, footnote}

EMBEDDED CHARTS (for complex visualisations):
- chart: Embed a pre-rendered PNG/SVG image. data: {section, title, image_path, footnote}
  Use this for: line charts, scatter plots, area charts, waterfall, donut/pie, heatmaps,
  Sankey diagrams, radar charts — anything that requires precise data plotting.
  The caller generates the chart image (e.g. via matplotlib, Chart.js) and passes the path.

Design principles:
- Use action titles (conclusion, not topic): "98% gross margin at scale" not "Business Model"
- Use three_card for triadic arguments (problem/solution/benefit)
- Use stat or icon_stat for 2-3 hero metrics that tell the story
- Use split or comparison for us-vs-them, before-vs-after
- Use timeline for milestones, roadmaps, company history
- Use process_flow for "how it works" (3-5 steps with arrows)
- Use progress_bars for completion status, ratings, coverage metrics
- Use pyramid for strategic hierarchy, priority tiers, funnels
- Use table only when precise data matters (financials, detailed breakdowns)
- Use chart (embedded image) for any complex data visualisation
- Vary layouts: never use the same slide type 3 times in a row
- The highlight_index on three_card accents one card (0=first, 1=middle, 2=last)
- For icon_stat, use Unicode emoji: document, chart, money, time, people, etc.
"""


class DesignAdvisor:
    """Intelligent presentation design engine.

    Parameters
    ----------
    brand : str
        Brand name (e.g., "aigis", "tvf", "aria", "sparkdcs").
    template : str
        Slide template style (e.g., "consulting", "executive", "brand").
    mode : str
        Intelligence mode: "llm" (default), "rules", or "advised".
    api_key : str, optional
        Anthropic API key. Falls back to ANTHROPIC_API_KEY env var.
    model : str
        Model to use for LLM calls.
    """

    def __init__(
        self,
        brand: str = "aigis",
        template: str = "brand",
        mode: str = "llm",
        api_key: str | None = None,
        model: str = "claude-sonnet-4-20250514",
    ):
        self.brand = brand
        self.template = template
        self.mode = mode
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.model = model

    def design_deck(
        self,
        title: str,
        sections: list[dict[str, Any]],
        *,
        date: str = "",
        subtitle: str = "",
        contact: Optional[dict] = None,
        audience: str = "",
        goal: str = "",
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
            Closing slide contact info.
        audience : str, optional
            Target audience (e.g., "PE fund CIOs", "board members").
        goal : str, optional
            Deck goal (e.g., "secure pre-seed investment", "inform board").

        Returns
        -------
        list[dict]
            List of slide specs ready for ``export_typst_slides()``.
        """
        if self.mode == "llm" and self.api_key:
            try:
                return self._design_deck_llm(
                    title, sections, date=date, subtitle=subtitle,
                    contact=contact, audience=audience, goal=goal,
                )
            except Exception as e:
                log.warning("LLM mode failed, falling back to rules: %s", e)

        # Fallback: rules-based
        return self._design_deck_rules(
            title, sections, date=date, subtitle=subtitle, contact=contact,
        )

    # ==================================================================
    # LLM-DRIVEN MODE
    # ==================================================================

    def _design_deck_llm(
        self,
        title: str,
        sections: list[dict[str, Any]],
        *,
        date: str = "",
        subtitle: str = "",
        contact: Optional[dict] = None,
        audience: str = "",
        goal: str = "",
    ) -> list[dict[str, Any]]:
        """Use Claude to design the optimal slide deck."""
        import anthropic

        client = anthropic.Anthropic(api_key=self.api_key)

        # Build system prompt with playbook context
        system_prompt = self._build_system_prompt()

        # Build user prompt with the content to design
        user_prompt = self._build_user_prompt(
            title, sections, date=date, subtitle=subtitle,
            contact=contact, audience=audience, goal=goal,
        )

        log.info("DesignAdvisor LLM: calling %s with %d chars system, %d chars user",
                 self.model, len(system_prompt), len(user_prompt))

        response = client.messages.create(
            model=self.model,
            max_tokens=8192,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )

        # Parse the response
        content = response.content[0].text
        slides = self._parse_llm_response(content, title, date, subtitle, contact)

        log.info("DesignAdvisor LLM: planned %d slides for '%s'", len(slides), title)
        return slides

    def _build_system_prompt(self) -> str:
        """Build the system prompt with playbook context."""
        from inkline.intelligence.playbooks import load_playbooks_for_task

        # Load slide-relevant playbooks
        playbooks = load_playbooks_for_task("slide")

        parts = [
            "You are Inkline's DesignAdvisor — an expert graphic designer and visual storyteller.",
            "You design compelling, professional slide decks that communicate information with maximum impact.",
            "",
            "Your job: given structured content sections, decide the BEST slide type and data layout",
            "for each section. You produce a JSON array of slide specs.",
            "",
            SLIDE_TYPE_GUIDE,
            "",
            "=" * 60,
            "DESIGN KNOWLEDGE",
            "=" * 60,
            "",
        ]

        for name, content in playbooks.items():
            # Include full playbook — these are specifically curated for this task
            parts.append(f"## {name.replace('_', ' ').title()}")
            parts.append(content)
            parts.append("")

        return "\n".join(parts)

    def _build_user_prompt(
        self,
        title: str,
        sections: list[dict[str, Any]],
        *,
        date: str = "",
        subtitle: str = "",
        contact: Optional[dict] = None,
        audience: str = "",
        goal: str = "",
    ) -> str:
        """Build the user prompt with content to design."""
        parts = [
            f"Design a slide deck for: **{title}**",
        ]
        if subtitle:
            parts.append(f"Subtitle: {subtitle}")
        if date:
            parts.append(f"Date: {date}")
        if audience:
            parts.append(f"Target audience: {audience}")
        if goal:
            parts.append(f"Goal: {goal}")

        parts.append(f"\nBrand: {self.brand}")
        parts.append(f"Template style: {self.template}")

        parts.append("\n## Content Sections\n")
        parts.append("Each section below is content that needs to become one (or occasionally two) slides.")
        parts.append("Decide the best slide_type for each, choose action titles, and structure the data.\n")

        for i, section in enumerate(sections):
            parts.append(f"### Section {i+1}: {section.get('section', section.get('type', 'Untitled'))}")
            parts.append(f"Original title: {section.get('title', '')}")
            parts.append(f"```json\n{json.dumps(section, indent=2, default=str)}\n```\n")

        if contact:
            parts.append(f"### Closing Contact\n```json\n{json.dumps(contact, indent=2)}\n```\n")

        parts.append("## Output Format")
        parts.append("")
        parts.append("Return ONLY a JSON array of slide specs. Each slide spec has:")
        parts.append('  {"slide_type": "...", "data": {...}}')
        parts.append("")
        parts.append("Start with a title slide and end with a closing slide.")
        parts.append("Use action titles throughout (state the conclusion, not the topic).")
        parts.append("Ensure visual variety — vary slide types across the deck.")
        parts.append("For three_card slides, set highlight_index to accent the most impactful card.")
        parts.append("For split slides, put the key message on the right (accent panel).")
        parts.append("")
        parts.append("Return the JSON array inside ```json ... ``` markers.")

        return "\n".join(parts)

    def _parse_llm_response(
        self,
        content: str,
        title: str,
        date: str,
        subtitle: str,
        contact: Optional[dict],
    ) -> list[dict[str, Any]]:
        """Parse the LLM's JSON response into slide specs."""
        # Extract JSON from markdown code block
        json_str = content
        if "```json" in content:
            start = content.index("```json") + 7
            end = content.index("```", start)
            json_str = content[start:end].strip()
        elif "```" in content:
            start = content.index("```") + 3
            end = content.index("```", start)
            json_str = content[start:end].strip()

        try:
            slides = json.loads(json_str)
        except json.JSONDecodeError as e:
            log.error("Failed to parse LLM response as JSON: %s", e)
            raise

        # Validate slide types
        validated = []
        for slide in slides:
            if not isinstance(slide, dict):
                continue
            stype = slide.get("slide_type", "")
            if stype not in SLIDE_TYPES:
                log.warning("Unknown slide type from LLM: %s, skipping", stype)
                continue
            if "data" not in slide:
                slide["data"] = {}
            validated.append(slide)

        if not validated:
            raise ValueError("LLM returned no valid slides")

        return validated

    # ==================================================================
    # RULES-BASED MODE (fallback)
    # ==================================================================

    def _design_deck_rules(
        self,
        title: str,
        sections: list[dict[str, Any]],
        *,
        date: str = "",
        subtitle: str = "",
        contact: Optional[dict] = None,
    ) -> list[dict[str, Any]]:
        """Rules-based deck design (no API calls)."""
        from inkline.intelligence.content_analyzer import analyze_content
        from inkline.intelligence.layout_selector import plan_deck_flow

        analyses = [analyze_content(s) for s in sections]
        layouts = plan_deck_flow(analyses)

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
            "DesignAdvisor rules: planned %d slides for '%s'",
            len(slides), title,
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
        """Design a document layout from markdown and optional exhibits."""
        return {
            "markdown": markdown,
            "title": title,
            "subtitle": subtitle,
            "date": date,
            "author": author,
            "brand": self.brand,
            "exhibits": exhibits or [],
        }

    # -- Rules-mode slide builders -----------------------------------------

    def _section_to_slide(self, section: dict, analysis: Any, layout: Any) -> dict | None:
        section_label = section.get("section", section.get("type", "").replace("_", " ").title())
        section_title = section.get("title", "")
        slide_type = layout.slide_type

        builders = {
            "content": self._build_content_slide,
            "three_card": lambda s, l, t: self._build_card_slide(s, l, t, 3, layout.highlight_index),
            "four_card": lambda s, l, t: self._build_card_slide(s, l, t, 4, layout.highlight_index),
            "stat": self._build_stat_slide,
            "kpi_strip": self._build_kpi_slide,
            "table": self._build_table_slide,
            "split": self._build_split_slide,
            "bar_chart": self._build_bar_chart_slide,
            "chart": self._build_chart_slide,
        }
        builder = builders.get(slide_type, self._build_content_slide)
        return builder(section, section_label, section_title)

    def _build_content_slide(self, section: dict, label: str, title: str) -> dict:
        items = section.get("items", [])
        if not items and section.get("cards"):
            items = [f"*{c.get('title', '')}* -- {c.get('body', '')}" for c in section["cards"]]
        if not items and section.get("left"):
            items = section["left"].get("items", [])
            items += section.get("right", {}).get("items", [])
        if not items and section.get("narrative"):
            sentences = [s.strip() for s in section["narrative"].replace("\n", " ").split(".") if s.strip()]
            items = [f"{s}." for s in sentences[:6]]
        return {"slide_type": "content", "data": {"section": label, "title": title or label, "items": items, "footnote": section.get("footnote", "")}}

    def _build_card_slide(self, section: dict, label: str, title: str, n: int, highlight: int) -> dict:
        cards = section.get("cards", [])
        if not cards and section.get("items"):
            cards = [{"title": item, "body": ""} for item in section["items"][:n]]
        if not cards and section.get("metrics"):
            cards = [{"title": k, "body": str(v)} for k, v in list(section["metrics"].items())[:n]]
        slide_type = "three_card" if n == 3 else "four_card"
        data: dict[str, Any] = {"section": label, "title": title or label, "cards": cards[:n], "footnote": section.get("footnote", "")}
        if highlight >= 0:
            data["highlight_index"] = highlight
        return {"slide_type": slide_type, "data": data}

    def _build_stat_slide(self, section: dict, label: str, title: str) -> dict:
        metrics = section.get("metrics", {})
        stats = [{"value": str(v), "label": k, "desc": ""} for k, v in list(metrics.items())[:4]]
        return {"slide_type": "stat", "data": {"section": label, "title": title or label, "stats": stats}}

    def _build_kpi_slide(self, section: dict, label: str, title: str) -> dict:
        metrics = section.get("metrics", {})
        kpis = [{"value": str(v), "label": k, "highlight": i == 0} for i, (k, v) in enumerate(list(metrics.items())[:5])]
        return {"slide_type": "kpi_strip", "data": {"section": label, "title": title or label, "kpis": kpis, "footnote": section.get("footnote", "")}}

    def _build_table_slide(self, section: dict, label: str, title: str) -> dict:
        table_data = section.get("table_data", {})
        return {"slide_type": "table", "data": {"section": label, "title": title or label, "headers": table_data.get("headers", []), "rows": table_data.get("rows", []), "footnote": section.get("footnote", "")}}

    def _build_split_slide(self, section: dict, label: str, title: str) -> dict:
        left = section.get("left", {})
        right = section.get("right", {})
        if not left and section.get("cards"):
            cards = section["cards"]
            mid = len(cards) // 2
            left = {"title": cards[0].get("title", ""), "items": [c.get("body", "") for c in cards[:mid]]}
            right = {"title": cards[mid].get("title", "") if mid < len(cards) else "", "items": [c.get("body", "") for c in cards[mid:]]}
        if not left and section.get("narrative"):
            words = section["narrative"].split()
            mid = len(words) // 2
            left = {"title": "Overview", "items": [" ".join(words[:mid])]}
            right = {"title": "Details", "items": [" ".join(words[mid:])]}
        return {"slide_type": "split", "data": {"section": label, "title": title or label, "left_title": left.get("title", ""), "left_items": left.get("items", []), "right_title": right.get("title", ""), "right_items": right.get("items", [])}}

    def _build_bar_chart_slide(self, section: dict, label: str, title: str) -> dict:
        items = section.get("items", [])
        values = section.get("values", [])
        if not items or not values:
            if section.get("table_data"):
                return self._build_table_slide(section, label, title)
            return self._build_content_slide(section, label, title)
        max_val = max(values) if values else 1
        bars = [{"label": item, "value": str(val), "pct": round(val / max_val * 100)} for item, val in zip(items, values)]
        return {"slide_type": "bar_chart", "data": {"section": label, "title": title or label, "bars": bars, "footnote": section.get("footnote", "")}}

    def _build_chart_slide(self, section: dict, label: str, title: str) -> dict:
        return {"slide_type": "chart", "data": {"section": label, "title": title or label, "image_path": section.get("image_path", ""), "footnote": section.get("footnote", "")}}
