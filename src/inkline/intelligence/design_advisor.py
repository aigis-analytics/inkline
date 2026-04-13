"""Design Advisor — the intelligent orchestrator for Inkline.

Takes structured content (WHAT to present) and decides HOW:
layout, chart type, visual hierarchy, and emphasis.

Two operating modes (orthogonal to the intelligence mode below):

  Mode A — "Data-in" (default for design_deck())
    Caller provides FACTS: raw metrics, claims, narratives, comparisons.
    Inkline (with LLM advisor) picks layouts and visualizations.
    HARD CONSTRAINT: the LLM may only restate/regroup facts that are
    in the input. It MUST NOT invent numbers, names, percentages, or
    statistics. When data is illustrative, the section MUST set
    `illustrative=True` and the renderer adds an "ILLUSTRATIVE" tag.

  Mode B — "Spec-in" (use export_typst_slides directly with raw slides)
    Caller provides full slide specs (slide_type + data).
    Inkline just renders. No LLM in the loop. No interpretation.

Three intelligence modes (only relevant for Mode A):
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
from pathlib import Path
from typing import Any, Callable, Optional

log = logging.getLogger(__name__)

# Type alias for the pluggable LLM caller. Any function that takes a system
# prompt + user prompt and returns the model's text response can be plugged in
# here — no Anthropic SDK dependency required. This is the integration point
# for Claude Code SDK, Claude Max sessions, custom LLM bridges, OpenAI, or any
# other LLM provider.
LLMCaller = Callable[[str, str], str]

# Available slide types that the Typst renderer supports
SLIDE_TYPES = [
    "title", "content", "three_card", "four_card", "stat",
    "table", "split", "chart", "bar_chart", "kpi_strip",
    "timeline", "process_flow", "icon_stat", "progress_bars",
    "pyramid", "comparison", "feature_grid", "dashboard",
    "chart_caption", "closing",
]

# Slide type descriptions for the LLM
SLIDE_TYPE_GUIDE = """
====================================================================
PRIME DIRECTIVE: PREFER VISUALS OVER TEXT, ALWAYS.
====================================================================

A great Inkline slide is SCANNABLE in 3 seconds, not READ in 30.
Your default reflex should be: "How can I show this visually instead of writing it?"

FORBIDDEN PATTERNS:
- Plain bullet lists ("content" type) when ANY of these alternatives fit:
  numbers → icon_stat/kpi_strip/stat
  comparisons → comparison/split/feature_grid
  steps → process_flow/timeline
  hierarchy → pyramid
  6 items → feature_grid
  trends → chart/chart_caption (request chart_type from caller)
- Tables wider than 6 columns or longer than 6 rows (they overflow the slide).
- Two consecutive text-heavy slides (content + content + content = boring).
- A slide that has only one element if a multi-exhibit layout would work better.

REQUIRED CADENCE:
- AT LEAST 60% of content slides must be visual layouts (icon_stat, kpi_strip,
  feature_grid, dashboard, chart_caption, timeline, process_flow, pyramid,
  progress_bars, comparison, three_card, four_card).
- AT MOST 1 plain "content" (bullet list) slide per deck.
- Every numerical value should be hero-formatted (icon_stat, stat, or kpi_strip).
- Every multi-step concept should be process_flow or timeline.

====================================================================
HARD CAPACITY LIMITS (overflow = broken slide — NEVER exceed these)
====================================================================
TITLES (HARD LIMIT — ENFORCED BY RENDERER):
- Slide titles: MAX 50 CHARS. Any title longer than 50 chars wraps to
  2 lines and pushes content off the page causing layout overflow.
  The fixer TRUNCATES titles at 50 chars — if your title is 60 chars,
  8-10 words will be silently cut off. Write tight, action titles.
  ALWAYS count: "Corsair delivers oil-weighted GoA cash flow" = 44 ✓
  BAD: "Corsair offers proven GoA cash flow with material 2P upside" = 59 ✗

ITEM COUNTS (anything beyond these limits is SILENTLY DROPPED):
- chart_caption bullets: MAX 4 short bullets (8-10 words each)
- dashboard bullets: MAX 3 short bullets (8-10 words each)
- dashboard stats: EXACTLY 3 stat callouts
- feature_grid features: EXACTLY 6 features (3x2 grid)
- table: MAX 6 rows x 6 columns. NEVER exceed 6 columns.
  Rows and columns beyond these limits are SILENTLY DROPPED by the renderer.
  If source data has more than 6 rows, pick the 6 most important ones.
  NEVER use a table when the data has >6 columns — use split or comparison instead.
- three_card cards: EXACTLY 3
- four_card cards: EXACTLY 4
- icon_stat stats: 3 or 4
- kpi_strip kpis: 3 to 5
- timeline milestones: MAX 6
- process_flow steps: MAX 4
- progress_bars: MAX 6 bars
- pyramid tiers: MAX 5
- comparison rows: MAX 6 per side
- content (bullets): MAX 6 bullets — and AVOID this slide type when possible

TEXT LENGTH:
- Card body text: MAX 2 short sentences (~60-80 chars total)
- Bullet items: MAX 10 words each. Telegraphic, not prose.
- Table cell text: MAX 50 chars per cell. Abbreviate if needed.
- Footnotes: MAX 80 chars. One short line only.

CHARTS (chart_caption / dashboard):
- Chart images are constrained to 6cm height on slide. Design accordingly.
- Keep chart titles short — they share vertical space with the image.
- MAX 4 bullets in the side panel (not 5 — accounts for caption text).

CONSISTENCY:
- three_card: ALL 3 cards render at the SAME HEIGHT regardless of text.
  Keep body text length similar across cards so content looks balanced.
- four_card: ALL 4 cards render at the SAME HEIGHT. Same rule applies.
- feature_grid: ALL 6 cells are equal size. Keep descriptions uniform length.

====================================================================
SLIDE TYPE CATALOGUE
====================================================================

VISUAL HEROES (prefer these):
- icon_stat: Big number + emoji + label, in cards. data: {section, title, stats [{value, icon, label, desc?}], footnote}
  Use for: hero metrics with semantic meaning. Pick emoji that match the metric:
  $/£ for money, ⚡ for speed, 📈 for growth, 🎯 for accuracy, ✓ for done, ⏱ for time.
- kpi_strip: 3-5 metric cards in a strip. data: {section, title, kpis [{value, label, highlight}], footnote}
  Use for: dashboards where one metric is the hero (highlight=true).
- stat: 2-4 hero statistics, very large numbers. data: {section, title, stats [{value, label, desc}]}
- feature_grid: 6 features in a 3x2 grid with numbered icons. data: {section, title, features [{title, body, icon?}], footnote}
  Use for: capability showcases, feature catalogs, "what we offer" — better than 4-card when you have 5-6 items.
- dashboard: Chart image (left 60%) + 3 stat callouts + max 3 bullets (right 40%). data: {section, title, image_path, stats [{value, label}], bullets, footnote}
  Use this for the SHOWCASE slide of any deck — the most info-dense, brochure-style layout.
  HARD CAP: 3 stat callouts, 3 bullets max — anything more overflows.
- chart_caption: Chart image (left 65%) + key takeaways panel (right 35%). data: {section, title, image_path, caption, bullets, footnote}
  Use for: any chart that needs context. ALWAYS prefer this over bare 'chart'.
  HARD CAP: 5 short bullets max.
- chart: Bare embedded chart image (full width). data: {section, title, image_path, footnote}
  Use ONLY when the chart speaks entirely for itself. Prefer chart_caption.
- bar_chart: Native horizontal bars. data: {section, title, bars [{label, value, pct (0-100)}], footnote}
- progress_bars: Labelled percentage bars. data: {section, title, bars [{label, pct, value?}], footnote}

NARRATIVE LAYOUTS:
- timeline: Horizontal milestones with date nodes. data: {section, title, milestones [{date, label, desc?}], footnote}
  Use for: roadmaps, company history, project plans.
- process_flow: Numbered steps with arrows. data: {section, title, steps [{number, title, desc}], footnote}
  Use for: "how it works", workflows, methodologies (3-5 steps).
- pyramid: 3-5 tier hierarchy (top=smallest, bottom=largest). data: {section, title, tiers [{label, desc?}], footnote}
  Use for: strategic hierarchy, priority tiers, funnels, layered architecture.
- three_card: 3 equal cards with optional accent on one. data: {section, title, cards [{title, body}], highlight_index (0-2), footnote}
- four_card: 2x2 grid. data: {section, title, cards [{title, body}], footnote}
- split: Two-column layout (right side gets accent fill). data: {section, title, left_title, left_items, right_title, right_items}
  Use for: us-vs-them, before-vs-after, problem-vs-solution.
- comparison: Structured side-by-side with metrics. data: {section, title, left {name, items [{label, value}]}, right {name, items [{label, value}]}, footnote}

STRUCTURAL:
- title: Opening slide. data: {company, tagline, date, subtitle, left_footer}
- closing: Final slide. data: {name, role, email, company, tagline}
- table: Data table — MAX 6 ROWS x 6 COLUMNS. data: {section, title, headers, rows, footnote}
  AVOID unless absolutely necessary. Tables with more than 6 columns will overflow.
- content: Plain bullet list. data: {section, title, items, footnote}
  USE SPARINGLY. Only when nothing else fits.

====================================================================
WRITING RULES
====================================================================
- Action titles: state the CONCLUSION, not the topic.
  BAD: "Business Model" → GOOD: "98% gross margin at scale"
  BAD: "The Problem" → GOOD: "Analysts spend 80% of their week in PowerPoint"
- Card body text: 1-2 short sentences max. No paragraphs.
- Bullet items: 5-10 words each. Telegraphic, not prose.
- Footnotes: optional, one short line, source attribution or caveat.

====================================================================
CHART REQUESTS (auto-rendered by Inkline)
====================================================================
When a slide should embed a chart (chart, chart_caption, dashboard types),
you request the chart by adding a "chart_request" field to the slide data.
Inkline's chart_renderer (matplotlib) will auto-render it before compilation.

HOW TO REQUEST A CHART:
1. Set "image_path" to a simple filename (e.g. "market_growth.png")
2. Add a "chart_request" dict with:
   - "chart_type": one of: line_chart, area_chart, scatter, waterfall, donut,
     pie, stacked_bar, grouped_bar, heatmap, radar, gauge
   - "chart_data": the data dict for that chart type (see below)

Example — donut chart on a dashboard slide:
  {
    "slide_type": "dashboard",
    "data": {
      "title": "Revenue by segment",
      "image_path": "revenue_donut.png",
      "chart_request": {
        "chart_type": "donut",
        "chart_data": {
          "segments": [
            {"label": "Enterprise", "value": 60},
            {"label": "Mid-Market", "value": 30},
            {"label": "SMB", "value": 10}
          ],
          "center_label": "Revenue\nMix"
        }
      },
      "stats": [{"value": "$5.2M", "label": "Total ARR"}],
      "bullets": ["Enterprise drives 60% of revenue"]
    }
  }

Example — bar chart on a chart_caption slide:
  {
    "slide_type": "chart_caption",
    "data": {
      "title": "Market sizing",
      "image_path": "market_bars.png",
      "chart_request": {
        "chart_type": "grouped_bar",
        "chart_data": {
          "categories": ["2024", "2025", "2026"],
          "series": [
            {"name": "TAM", "values": [8.5, 10, 12]},
            {"name": "SAM", "values": [1.5, 2, 2.5]}
          ],
          "y_label": "$ Billion"
        }
      },
      "caption": "DD market growing at 7.8% CAGR",
      "bullets": ["Energy DD is $1-2B of the $10B+ total"]
    }
  }

CHART DATA FORMATS (by chart_type):
- line_chart / area_chart: {x: [...], series: [{name, values}], x_label?, y_label?}
- waterfall: {items: [{label, value, total?}]}
- donut / pie: {segments: [{label, value}], center_label?}
- stacked_bar / grouped_bar: {categories: [...], series: [{name, values}], y_label?}
- radar: {axes: [...], series: [{name, values}]}
- gauge: {value: 0-100, label?}
- scatter: {points: [{x, y, label?, size?}], x_label?, y_label?}
- heatmap: {x_labels: [...], y_labels: [...], values: [[...]]}

RULES:
- ONLY use chart_request with data that is EXPLICITLY in the input sections.
  DO NOT invent data points.
- If input data contains "illustrative": true, add it to chart_data — the
  renderer will add a watermark automatically.
- Use charts when they genuinely add visual value. Don't force a chart when
  a table or icon_stat would be clearer.
- Prefer donut/waterfall/radar for small datasets, line/area for trends.

====================================================================
"""


class DesignAdvisor:
    """Intelligent presentation design engine.

    Parameters
    ----------
    brand : str
        Brand name (e.g., "minimal" or any user-registered brand).
    template : str
        Slide template style (e.g., "consulting", "executive", "brand").
    mode : str
        Intelligence mode: "llm" (default), "rules", or "advised".
    api_key : str, optional
        Anthropic API key. Falls back to ANTHROPIC_API_KEY env var.
    model : str
        Model to use for LLM calls.
    """

    #: Default LLM bridge URL. Override via env var ``INKLINE_BRIDGE_URL``
    #: (e.g. ``http://host.docker.internal:8082`` from inside Docker).
    DEFAULT_BRIDGE_URL = "http://localhost:8082"

    def __init__(
        self,
        brand: str = "minimal",
        template: str = "brand",
        mode: str = "llm",
        api_key: str | None = None,
        model: str = "claude-sonnet-4-6",
        llm_caller: Optional["LLMCaller"] = None,
        bridge_url: str | None = None,
    ):
        self.brand = brand
        self.template = template
        self.mode = mode
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.model = model
        self.llm_caller = llm_caller
        # Bridge URL: kwarg > env var > class default
        self.bridge_url = (
            bridge_url
            or os.environ.get("INKLINE_BRIDGE_URL", "")
            or self.DEFAULT_BRIDGE_URL
        )

    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Route an LLM call: injected caller → bridge → Anthropic SDK.

        Priority:
        1. ``self.llm_caller`` — injected custom caller (e.g. test mocks)
        2. LLM bridge at ``self.bridge_url`` — uses Claude Max subscription
        3. Anthropic SDK with ``self.api_key`` / ``ANTHROPIC_API_KEY``
        """
        if self.llm_caller is not None:
            log.info(
                "DesignAdvisor LLM (injected caller): %d sys / %d user chars",
                len(system_prompt), len(user_prompt),
            )
            return self.llm_caller(system_prompt, user_prompt)

        # Ensure bridge is running before attempting to connect — auto-starts from
        # ~/.config/inkline/claude_bridge.py if present.  Zero-cost (1s timeout
        # health check), never blocks if bridge is already up.
        try:
            from inkline.intelligence.claude_code import ensure_bridge_running
            ensure_bridge_running(self.bridge_url)
        except Exception:
            pass  # Non-fatal — proceed to bridge attempt regardless

        # Try bridge — narrative truncation in _build_user_prompt() keeps prompts
        # under ~80K total (47K system + 33K user), within bridge processing limits.
        # Read timeout matches bridge's dynamic timeout (180s + 3s/KB, max 600s).
        try:
            import requests as _req
            total_chars = len(system_prompt) + len(user_prompt)
            bridge_read_timeout = min(600, max(200, 180 + (total_chars // 1000) * 3)) + 15  # +15s buffer
            log.info(
                "DesignAdvisor LLM bridge %s (%d sys / %d user chars, timeout=%ds)...",
                self.bridge_url, len(system_prompt), len(user_prompt), bridge_read_timeout,
            )
            resp = _req.post(
                f"{self.bridge_url}/prompt",
                json={"prompt": user_prompt, "system": system_prompt, "max_tokens": 16000},
                timeout=(1, bridge_read_timeout),  # 1s connect (fast-fail if bridge down)
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("response"):
                log.info(
                    "DesignAdvisor LLM bridge OK — %d chars (source=%s)",
                    len(data["response"]), data.get("source", "?"),
                )
                return data["response"]
        except Exception as e:
            log.info("DesignAdvisor LLM bridge unavailable (%s) — falling back to Anthropic API", e)

        # Anthropic SDK fallback
        try:
            import anthropic
        except ImportError as exc:
            raise RuntimeError(
                "Inkline intelligence requires the 'anthropic' package. "
                "Install it with: pip install inkline[intelligence]"
            ) from exc

        if not self.api_key:
            raise RuntimeError(
                "No LLM available: bridge unreachable and ANTHROPIC_API_KEY not set. "
                "Set ANTHROPIC_API_KEY or start the LLM bridge, or use mode='rules'."
            )

        client = anthropic.Anthropic(api_key=self.api_key)
        log.info(
            "DesignAdvisor Anthropic API (%s): %d sys / %d user chars",
            self.model, len(system_prompt), len(user_prompt),
        )
        response = client.messages.create(
            model=self.model,
            max_tokens=8192,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return response.content[0].text

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
        additional_guidance: str = "",
        reference_archetypes: Optional[list[str]] = None,
    ) -> list[dict[str, Any]]:
        """Design a slide deck from structured content sections.

        Parameters
        ----------
        title : str
            Deck title.
        sections : list[dict]
            Content sections, each with ``type`` and data fields.

            Each section can include a ``"slide_mode"`` field to control how
            much creative freedom the LLM has:

            - ``"exact"`` — Section is a complete slide spec. The LLM does not
              touch it. Must include ``"slide_type"`` and ``"data"`` keys.
              Use this when you know exactly what the slide should look like.
            - ``"guided"`` — Section specifies constraints (e.g., ``slide_type``,
              some ``data`` fields). The LLM fills missing fields but MUST
              preserve everything the user provided. Use this when you want
              the LLM to polish presentation but not change substance.
            - ``"auto"`` (default) — Full LLM control. The LLM picks the best
              slide type and structures all data from the section content.

            If ``slide_mode`` is omitted, defaults to ``"auto"``.

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
        additional_guidance : str, optional
            Free-form guidance the user wants the LLM to follow on top of the
            playbook rules.
        reference_archetypes : list[str], optional
            Archetype names from ``inkline.intelligence.template_catalog.ARCHETYPES``
            that the LLM should consider for this deck.

        Returns
        -------
        list[dict]
            List of slide specs ready for ``export_typst_slides()``.
        """
        # Partition sections by slide_mode
        exact_slides = []   # (original_index, slide_spec)
        llm_sections = []   # (original_index, section) — for auto + guided

        for i, section in enumerate(sections):
            mode = section.get("slide_mode", "auto")
            if mode == "exact":
                # Exact mode: section IS the slide spec — pass through directly
                stype = section.get("slide_type", "")
                data = section.get("data", {})
                if stype and stype in SLIDE_TYPES:
                    exact_slides.append((i, {"slide_type": stype, "data": data, "slide_mode": "exact"}))
                else:
                    log.warning(
                        "Section %d has slide_mode='exact' but invalid/missing "
                        "slide_type '%s' — falling back to auto", i, stype,
                    )
                    llm_sections.append((i, section))
            else:
                llm_sections.append((i, section))

        # If ALL sections are exact, no LLM call needed
        if not llm_sections:
            slides = [spec for _, spec in sorted(exact_slides)]
            # Add title + closing if not already present
            if not slides or slides[0]["slide_type"] != "title":
                slides.insert(0, {"slide_type": "title", "data": {
                    "company": title, "tagline": subtitle, "date": date,
                }})
            if contact and (not slides or slides[-1]["slide_type"] != "closing"):
                slides.append({"slide_type": "closing", "data": contact})
            return slides

        # LLM mode: send auto + guided sections to LLM
        if self.mode == "llm" and (self.llm_caller is not None or self.api_key):
            try:
                llm_only = [s for _, s in llm_sections]
                llm_slides = self._design_deck_llm(
                    title, llm_only, date=date, subtitle=subtitle,
                    contact=contact, audience=audience, goal=goal,
                    additional_guidance=additional_guidance,
                    reference_archetypes=reference_archetypes,
                )

                # Merge: replace LLM-designed slides with exact ones at
                # their original positions. LLM output is sequential for
                # the auto/guided sections; exact slides are spliced in.
                if exact_slides:
                    llm_slides = self._merge_exact_slides(
                        llm_slides, exact_slides, llm_sections,
                    )

                # Post-process: enforce guided mode constraints
                llm_slides = self._enforce_guided_constraints(
                    llm_slides, sections,
                )

                return llm_slides
            except Exception as e:
                log.warning("LLM mode failed, falling back to rules: %s", e)

        # Fallback: rules-based (exact slides still honored)
        rules_sections = [s for _, s in llm_sections]
        rules_slides = self._design_deck_rules(
            title, rules_sections, date=date, subtitle=subtitle, contact=contact,
        )
        if exact_slides:
            rules_slides = self._merge_exact_slides(
                rules_slides, exact_slides, llm_sections,
            )
        return rules_slides

    @staticmethod
    def _merge_exact_slides(
        llm_slides: list[dict],
        exact_slides: list[tuple[int, dict]],
        llm_sections: list[tuple[int, dict]],
    ) -> list[dict]:
        """Splice exact slides into LLM output at their original positions.

        The LLM only saw auto/guided sections, so its output indices don't
        account for exact slides. We insert exact slides at the correct
        positions relative to the original section ordering.
        """
        # Build a mapping: original_index → slide_spec
        result_by_idx: dict[int, dict] = {}
        for orig_idx, spec in exact_slides:
            result_by_idx[orig_idx] = spec

        # LLM slides map to llm_sections in order (skip title/closing)
        llm_content = [s for s in llm_slides if s["slide_type"] not in ("title", "closing")]
        title_slide = next((s for s in llm_slides if s["slide_type"] == "title"), None)
        closing_slide = next((s for s in llm_slides if s["slide_type"] == "closing"), None)

        for i, (orig_idx, _) in enumerate(llm_sections):
            if i < len(llm_content):
                result_by_idx[orig_idx] = llm_content[i]

        # Reassemble in original order
        merged = []
        if title_slide:
            merged.append(title_slide)
        for idx in sorted(result_by_idx):
            merged.append(result_by_idx[idx])
        if closing_slide:
            merged.append(closing_slide)

        return merged

    @staticmethod
    def _enforce_guided_constraints(
        slides: list[dict],
        original_sections: list[dict],
    ) -> list[dict]:
        """For guided-mode sections, ensure user-specified fields are preserved.

        The LLM may have changed fields the user explicitly set. This method
        restores them from the original section.
        """
        # Map section titles to original sections for matching
        guided = {
            s.get("section", s.get("title", "")): s
            for s in original_sections
            if s.get("slide_mode") == "guided"
        }
        if not guided:
            return slides

        for slide in slides:
            data = slide.get("data", {})
            section_key = data.get("section", data.get("title", ""))

            orig = guided.get(section_key)
            if not orig:
                continue

            # Mark as guided so the visual auditor stores suggestions for HITL
            slide["slide_mode"] = "guided"

            # Restore user-specified slide_type if provided
            if "slide_type" in orig and orig["slide_type"] in SLIDE_TYPES:
                slide["slide_type"] = orig["slide_type"]

            # Restore user-specified data fields
            user_data = orig.get("data", {})
            for key, value in user_data.items():
                data[key] = value

        return slides

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
        additional_guidance: str = "",
        reference_archetypes: Optional[list[str]] = None,
    ) -> list[dict[str, Any]]:
        """Use an LLM to design the optimal slide deck.

        Routing order (handled by ``_call_llm``):
          1. ``self.llm_caller`` — injected custom caller (test mocks, custom providers)
          2. LLM bridge at ``self.bridge_url`` (default ``INKLINE_BRIDGE_URL`` env var
             or ``localhost:8082``) — Claude Max subscription, no API spend
          3. Anthropic SDK using ``self.api_key`` / ``ANTHROPIC_API_KEY`` env var
        """
        # Build prompts
        system_prompt = self._build_system_prompt(reference_archetypes=reference_archetypes)
        user_prompt = self._build_user_prompt(
            title, sections, date=date, subtitle=subtitle,
            contact=contact, audience=audience, goal=goal,
            additional_guidance=additional_guidance,
        )

        content = self._call_llm(system_prompt, user_prompt)
        slides = self._parse_llm_response(content, title, date, subtitle, contact)
        log.info("DesignAdvisor LLM: planned %d slides for '%s'", len(slides), title)
        return slides

    def _build_system_prompt(
        self,
        reference_archetypes: Optional[list[str]] = None,
    ) -> str:
        """Build the system prompt with playbook context.

        Uses tiered loading to keep the system prompt under ~30K chars:
        - slide_layouts: full text (layout rules are essential)
        - SLIDE_TYPE_GUIDE: full text (critical for JSON output format)
        - template_catalog, typography, color_theory: condensed summaries
        """
        from inkline.intelligence.playbooks import load_playbook, load_playbook_summary

        # Tiered playbook loading — full for core, summary for bulk reference
        CORE_PLAYBOOKS = ["slide_layouts"]
        SUMMARY_PLAYBOOKS = ["template_catalog", "typography", "color_theory"]

        from inkline.intelligence.vishwakarma import VISHWAKARMA_SYSTEM_PREAMBLE

        parts = [
            "You are Inkline's DesignAdvisor — an expert graphic designer and visual storyteller.",
            "You design compelling, professional slide decks that communicate information with maximum impact.",
            "",
            VISHWAKARMA_SYSTEM_PREAMBLE,
            "",
            "=" * 60,
            "PRIME DIRECTIVE: NEVER INVENT FACTS",
            "=" * 60,
            "",
            "You are NOT a copywriter. You are a designer.",
            "",
            "STRICT RULES:",
            "- USE ONLY the data, claims, numbers, names, percentages, and",
            "  narratives that are EXPLICITLY in the input sections.",
            "- DO NOT invent statistics. DO NOT make up customer counts, growth",
            "  rates, GitHub stars, contributor counts, ARR figures, or any other",
            "  quantitative claim that isn't in the input.",
            "- DO NOT add hypothetical examples ('teams like Acme...') unless they",
            "  are explicitly in the input.",
            "- If a section has an `illustrative=True` flag, the data is for",
            "  visual demonstration only — your slide MUST mark it as ILLUSTRATIVE",
            "  in the footnote/caption (e.g., 'Illustrative example — not real data').",
            "- If you need a chart and the input provides a chart_path, use that",
            "  path. Do NOT invent additional chart paths or describe charts that",
            "  weren't provided.",
            "",
            "Your job is to PICK LAYOUTS and STRUCTURE the provided facts —",
            "not to fill in plausible-sounding details. If a section is sparse,",
            "design a sparse-but-impactful slide. If you cannot honestly support",
            "a claim with the input data, OMIT it.",
            "",
            "Action titles are great. Hallucinated metrics are not.",
            "",
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

        # Core playbooks: include full text
        for name in CORE_PLAYBOOKS:
            try:
                content = load_playbook(name)
                parts.append(f"## {name.replace('_', ' ').title()}")
                parts.append(content)
                parts.append("")
            except Exception as e:
                log.warning("Failed to load core playbook '%s': %s", name, e)

        # Summary playbooks: condensed to reduce token count
        for name in SUMMARY_PLAYBOOKS:
            try:
                content = load_playbook_summary(name, max_chars=4000)
                parts.append(f"## {name.replace('_', ' ').title()} (summary)")
                parts.append(content)
                parts.append("")
            except Exception as e:
                log.warning("Failed to load summary playbook '%s': %s", name, e)

        # Include design.md style catalog (27 curated design systems)
        try:
            from inkline.intelligence.design_md_styles import get_playbook_text
            parts.append(get_playbook_text())
            parts.append("")
        except Exception:
            pass  # Non-blocking: design_md_styles is optional

        # Optional: inline structured archetype recipes the caller pinned
        if reference_archetypes:
            from inkline.intelligence.template_catalog import get_archetype_recipe
            parts.append("=" * 60)
            parts.append("PINNED ARCHETYPES")
            parts.append("=" * 60)
            parts.append("")
            parts.append(
                "The caller has pinned these archetype recipes — bias your slide "
                "selection toward these patterns where the data fits:"
            )
            parts.append("")
            for arch_name in reference_archetypes:
                try:
                    recipe = get_archetype_recipe(arch_name)
                except ValueError:
                    log.warning("Unknown pinned archetype '%s', skipping", arch_name)
                    continue
                parts.append(f"### {arch_name}: {recipe['name']}")
                parts.append(f"  best_for: {', '.join(recipe['best_for'])}")
                parts.append(f"  layout: {recipe['layout']}")
                parts.append(f"  palette_rule: {recipe['palette_rule']}")
                parts.append(f"  inkline_slide_type: {recipe['inkline_slide_type']}")
                parts.append(f"  n_items: {recipe['n_items']}")
                parts.append("")

        # Inject learned patterns for this brand
        try:
            from inkline.intelligence.pattern_memory import format_patterns_for_prompt
            pattern_text = format_patterns_for_prompt(self.brand)
            if pattern_text:
                parts.append("")
                parts.append(pattern_text)
        except Exception:
            pass

        return "\n".join(parts)

    # Maximum chars for a section's narrative field in the user prompt.
    # Bridge handles ~80K total (47K system + 33K user) within its 300s timeout.
    # With ~16 sections × 1200 chars avg + 8K overhead ≈ 27K user + 47K sys = 74K.
    MAX_NARRATIVE_CHARS = 1200

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
        additional_guidance: str = "",
    ) -> str:
        """Build the user prompt with content to design.

        Narratives are truncated at sentence boundaries to keep the total
        prompt size within the LLM bridge limit (~80K chars total).
        """
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
        if additional_guidance:
            parts.append("")
            parts.append("## Additional guidance from the caller")
            parts.append("Apply this on top of the playbook rules:")
            parts.append(additional_guidance.strip())

        parts.append(f"\nBrand: {self.brand}")
        parts.append(f"Template style: {self.template}")

        parts.append("\n## Content Sections\n")
        parts.append("Each section below is content that needs to become one (or occasionally two) slides.")
        parts.append("Decide the best slide_type for each, choose action titles, and structure the data.\n")
        parts.append("SECTION MODES:")
        parts.append("- `auto` (default): You have full creative control over slide_type and data.")
        parts.append("- `guided`: The user has specified certain fields (e.g., slide_type, some data")
        parts.append("  fields like rows, cards, title). You MUST PRESERVE those fields exactly as")
        parts.append("  provided. Fill in any MISSING fields (e.g., footnote, highlight_index) and")
        parts.append("  polish the presentation, but DO NOT change user-specified content.")
        parts.append("  If the user specifies `slide_type: table` with 8 rows, output a table with 8 rows.\n")

        for i, section in enumerate(sections):
            slide_mode = section.get("slide_mode", "auto")
            mode_tag = f" [MODE: {slide_mode.upper()}]" if slide_mode != "auto" else ""
            parts.append(f"### Section {i+1}: {section.get('section', section.get('type', section.get('title', 'Untitled')))}{mode_tag}")
            parts.append(f"Original title: {section.get('title', '')}")

            # Truncate long narratives to keep user prompt within bridge limits.
            # Guided sections are never truncated — user-specified content must be preserved.
            sec_for_prompt = dict(section)
            if slide_mode == "auto":
                narrative = sec_for_prompt.get("narrative", "")
                if len(narrative) > self.MAX_NARRATIVE_CHARS:
                    # Cut at sentence boundary nearest to the limit
                    trunc = narrative[:self.MAX_NARRATIVE_CHARS]
                    # Find last sentence-ending character
                    for end_char in ("\n\n", ".\n", ". ", ".\t"):
                        idx = trunc.rfind(end_char)
                        if idx > int(self.MAX_NARRATIVE_CHARS * 0.6):
                            trunc = trunc[:idx + len(end_char)].rstrip()
                            break
                    omitted_pct = int((len(narrative) - len(trunc)) / len(narrative) * 100)
                    sec_for_prompt["narrative"] = trunc + f"\n[...{omitted_pct}% omitted — key data above is sufficient for slide design]"

            parts.append(f"```json\n{json.dumps(sec_for_prompt, indent=2, default=str)}\n```\n")

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
    # TWO-AGENT DESIGN DIALOGUE — Revision from Auditor feedback
    # ==================================================================

    def revise_slides_from_review(
        self,
        slides: list[dict[str, Any]],
        review_findings: list,
        original_sections: Optional[list[dict[str, Any]]] = None,
    ) -> list[dict[str, Any]]:
        """Receive Visual Auditor's review and revise slides accordingly.

        For each finding:
        - If Auditor proposes a redesign: evaluate it, accept or modify
        - If Auditor flags a mechanical issue: apply the fix
        - If Auditor makes a subjective suggestion: use LLM to decide

        Parameters
        ----------
        slides : list[dict]
            Current slide specs.
        review_findings : list
            Auditor findings (AuditWarning objects or dicts with
            severity, category, message, proposed_redesign).
        original_sections : list[dict], optional
            Original section data for context.

        Returns
        -------
        list[dict]
            Revised slide specs.
        """
        # Separate findings with proposed redesigns from text-only findings
        redesign_proposals = []
        other_findings = []

        for finding in review_findings:
            if hasattr(finding, "severity"):
                severity = finding.severity
                msg = finding.message
                proposed = getattr(finding, "proposed_redesign", None)
                slide_idx = getattr(finding, "slide_index", -1)
            elif isinstance(finding, dict):
                severity = finding.get("severity", "info")
                msg = finding.get("message", "")
                proposed = finding.get("proposed_redesign")
                slide_idx = finding.get("slide_index", -1)
            else:
                continue

            if severity not in ("error", "warn"):
                continue

            if proposed and isinstance(proposed, dict) and proposed.get("slide_type"):
                redesign_proposals.append({
                    "slide_index": slide_idx,
                    "proposed": proposed,
                    "reason": msg,
                })
            else:
                other_findings.append({
                    "slide_index": slide_idx,
                    "message": msg,
                    "severity": severity,
                })

        if not redesign_proposals and not other_findings:
            return slides

        # Authority model based on slide_mode:
        #
        # ERRORS (clipping, overflow, missing content, truncation):
        #   → Always fix, even on exact/guided slides.
        #     These are mechanical failures that break the user's intent.
        #
        # DESIGN SUGGESTIONS (layout_change, infographic, whitespace):
        #   → Auto-apply on auto slides
        #   → Store for HITL on exact/guided slides
        #
        modified = list(slides)
        accepted_count = 0
        protected_indices = {
            i for i, s in enumerate(slides)
            if s.get("slide_mode") in ("exact", "guided")
        }
        hitl_suggestions: list[dict] = []

        for proposal in redesign_proposals:
            idx = proposal["slide_index"] - 1  # Convert 1-based to 0-based
            if idx in protected_indices:
                # Design redesigns on protected slides → HITL only
                hitl_suggestions.append({
                    "slide_index": idx + 1,
                    "current_type": modified[idx].get("slide_type", ""),
                    "proposed_type": proposal["proposed"].get("slide_type", ""),
                    "reason": proposal["reason"],
                    "proposed_redesign": proposal["proposed"],
                    "status": "pending_review",
                })
                log.info("Suggestion stored for HITL: slide %d (%s → %s)",
                         idx + 1, modified[idx].get("slide_type", ""),
                         proposal["proposed"].get("slide_type", ""))
                continue  # Don't auto-apply
            if 0 <= idx < len(modified):
                proposed = proposal["proposed"]
                old_type = modified[idx].get("slide_type", "")
                new_type = proposed.get("slide_type", "")

                if new_type in SLIDE_TYPES:
                    modified[idx] = {
                        "slide_type": new_type,
                        "data": proposed.get("data", modified[idx].get("data", {})),
                    }
                    accepted_count += 1
                    log.info(
                        "Design revision: slide %d %s → %s (%s)",
                        idx + 1, old_type, new_type, proposal["reason"][:50],
                    )

                    # Record in pattern memory
                    try:
                        from inkline.intelligence.pattern_memory import record_accepted_redesign
                        record_accepted_redesign(
                            self.brand, old_type, new_type, proposal["reason"][:100],
                        )
                    except Exception:
                        pass

        # Split non-redesign findings by severity:
        # - ERRORS on protected slides → still fix (mechanical failures)
        # - WARNINGS on protected slides → store for HITL
        # - Everything on auto slides → fix
        fixable_findings = []
        for f in other_findings:
            idx = f["slide_index"] - 1
            is_protected = idx in protected_indices
            is_error = f["severity"] == "error"

            if not is_protected:
                # Auto slides: fix everything
                fixable_findings.append(f)
            elif is_error:
                # Protected slide with error: still fix (broken = not respecting intent)
                fixable_findings.append(f)
                log.info("Fixing error on protected slide %d: %s", f["slide_index"], f["message"][:60])
            else:
                # Protected slide with warning: HITL suggestion
                hitl_suggestions.append({
                    "slide_index": f["slide_index"],
                    "message": f["message"],
                    "severity": f["severity"],
                    "status": "pending_review",
                })

        if fixable_findings and (self.llm_caller is not None or self.api_key):
            try:
                modified = self._revise_via_llm(modified, fixable_findings, original_sections)
            except Exception as e:
                log.warning("LLM revision failed: %s", e)

        # Save HITL suggestions to file
        if hitl_suggestions:
            self._save_suggestions(hitl_suggestions)

        if accepted_count:
            log.info("Design dialogue: accepted %d proposals, %d stored for HITL",
                     accepted_count, len(hitl_suggestions))

        return modified

    def _save_suggestions(self, suggestions: list[dict]) -> None:
        """Save HITL suggestions to suggestions.json alongside the output."""
        import os
        suggestions_path = Path(os.environ.get(
            "INKLINE_SUGGESTIONS_PATH",
            Path.home() / ".config" / "inkline" / "suggestions.json",
        ))
        # Append to existing suggestions
        existing = []
        if suggestions_path.exists():
            try:
                existing = json.loads(suggestions_path.read_text(encoding="utf-8"))
            except Exception:
                existing = []

        existing.extend(suggestions)
        suggestions_path.write_text(
            json.dumps(existing, indent=2, default=str, ensure_ascii=False),
            encoding="utf-8",
        )
        log.info("Saved %d HITL suggestions to %s", len(suggestions), suggestions_path)

    def _revise_via_llm(
        self,
        slides: list[dict[str, Any]],
        findings: list[dict],
        original_sections: Optional[list[dict[str, Any]]] = None,
    ) -> list[dict[str, Any]]:
        """Revise ONLY the specific slides flagged by the auditor.

        Sends only affected slides to the LLM, then splices results
        back into the original list. Unflagged slides are never touched.
        """
        # Identify which slides are flagged (0-based indices)
        flagged_indices = set()
        for f in findings:
            idx = f["slide_index"] - 1  # Convert 1-based to 0-based
            if 0 <= idx < len(slides):
                flagged_indices.add(idx)

        if not flagged_indices:
            return slides

        # Extract only the flagged slides
        flagged_slides = [(i, slides[i]) for i in sorted(flagged_indices)]

        system_prompt = self._build_system_prompt()

        # Check if any findings are overflow-related — require stricter constraints
        has_overflow = any("overflow" in f.get("message", "").lower() for f in findings)

        parts = [
            "Fix ONLY the specific issues listed below. Return the revised slides as JSON.",
            "DO NOT change company names, numbers, or factual data.",
            "DO NOT add new image_path references.",
            "Only adjust layout, text formatting, or slide_type if needed.",
        ]
        if has_overflow:
            parts += [
                "",
                "CRITICAL OVERFLOW CONSTRAINT:",
                "- Each slide MUST fit on exactly ONE page. Overflow onto a second page is a hard failure.",
                "- To fix overflow: reduce items, shorten text, or switch to a SIMPLER slide type.",
                "- SAFE types that reliably fit: content, split, three_card, stat, icon_stat.",
                "- AVOID or DOWNGRADE: feature_grid, dashboard, comparison, four_card, table with many rows.",
                "- Do NOT switch to a denser slide type. If unsure, use 'content' with bullet points.",
            ]
        parts += [
            "",
            "Issues to fix:\n",
        ]

        for f in findings:
            idx = f["slide_index"] - 1
            if idx in flagged_indices:
                parts.append(f"- Slide {f['slide_index']} [{f['severity']}]: {f['message']}")

        parts.append(f"\nSlides to revise ({len(flagged_slides)} of {len(slides)}):")
        for i, s in flagged_slides:
            parts.append(f"\n// Slide {i+1}:")
            parts.append(json.dumps(s, indent=2, default=str)[:1500])

        parts.append("\nReturn ONLY the revised slides as a JSON array (same count as above).")
        parts.append("Return inside ```json ... ``` markers.")

        user_prompt = "\n".join(parts)

        try:
            content = self._call_llm(system_prompt, user_prompt)
            revised = self._parse_llm_response(content, "", "", "", None)

            # Splice revised slides back into the original list
            if len(revised) == len(flagged_slides):
                result = list(slides)
                for (orig_idx, _), new_slide in zip(flagged_slides, revised):
                    result[orig_idx] = new_slide
                return result
        except Exception as e:
            log.warning("LLM slide revision failed: %s", e)

        return slides

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
            "feature_grid": lambda s, l, t: self._build_card_slide(s, l, t, 6, -1),
            "stat": self._build_stat_slide,
            "kpi_strip": self._build_kpi_slide,
            "table": self._build_table_slide,
            "split": self._build_split_slide,
            "bar_chart": self._build_bar_chart_slide,
            "chart": self._build_chart_slide,
            "timeline": self._build_timeline_slide,
        }
        builder = builders.get(slide_type, self._build_content_slide)
        return builder(section, section_label, section_title)

    def _build_content_slide(self, section: dict, label: str, title: str) -> dict:
        items = section.get("items", [])
        # Normalize dict items to strings
        if items and isinstance(items[0], dict):
            items = self._dict_items_to_strings(items)
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
            raw = section["items"]
            if raw and isinstance(raw[0], dict):
                # Dict items — extract title/body from known key patterns
                cards = self._dict_items_to_cards(raw[:n])
            else:
                cards = [{"title": item, "body": ""} for item in raw[:n]]
        if not cards and section.get("metrics"):
            cards = [{"title": k, "body": str(v)} for k, v in list(section["metrics"].items())[:n]]
        # Map n to slide type
        if n <= 3:
            slide_type = "three_card"
        elif n == 4:
            slide_type = "four_card"
        else:
            slide_type = "feature_grid"
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

    def _build_timeline_slide(self, section: dict, label: str, title: str) -> dict:
        """Build a timeline slide from dict items with date/label keys."""
        items = section.get("items", [])
        milestones = []
        for item in items:
            if isinstance(item, dict):
                date = item.get("date") or item.get("timing") or item.get("year") or ""
                lbl = item.get("label") or item.get("name") or item.get("title") or ""
                desc = item.get("description") or item.get("body") or item.get("detail") or ""
                milestones.append({"date": str(date), "label": str(lbl), "description": str(desc)})
            else:
                milestones.append({"date": "", "label": str(item), "description": ""})
        return {"slide_type": "timeline", "data": {"section": label, "title": title or label, "milestones": milestones, "footnote": section.get("footnote", "")}}

    @staticmethod
    def _dict_items_to_cards(items: list) -> list:
        """Convert a list of dict items to card dicts with title/body keys."""
        cards = []
        for item in items:
            if not isinstance(item, dict):
                cards.append({"title": str(item), "body": ""})
                continue
            card_title = item.get("title") or item.get("name") or item.get("well") or item.get("action") or item.get("risk") or ""
            card_body = item.get("body") or item.get("detail") or item.get("value") or item.get("status") or ""
            severity = item.get("severity") or item.get("priority") or ""
            if severity and not card_body:
                card_body = f"Severity: {severity}"
            cards.append({"title": str(card_title), "body": str(card_body)})
        return cards

    @staticmethod
    def _dict_items_to_strings(items: list) -> list:
        """Convert a list of dict items to display strings."""
        result = []
        for item in items:
            if isinstance(item, str):
                result.append(item)
            elif isinstance(item, dict):
                name = item.get("title") or item.get("name") or item.get("well") or item.get("action") or item.get("risk") or ""
                detail = item.get("body") or item.get("detail") or item.get("value") or item.get("status") or ""
                severity = item.get("severity") or item.get("priority") or ""
                if name and detail:
                    result.append(f"{name} — {detail}")
                elif name and severity:
                    result.append(f"{name} [{severity}]")
                elif name:
                    result.append(name)
                else:
                    result.append("; ".join(f"{k}: {v}" for k, v in item.items()))
            else:
                result.append(str(item))
        return result
