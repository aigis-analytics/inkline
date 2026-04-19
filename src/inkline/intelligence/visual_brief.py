"""Visual Brief — structured visual direction for presentation decks.

The Visual Brief captures global visual decisions (palette, template, image treatment,
chart style, layout pacing) that constrain all per-slide design decisions.

Replaces prose 'visual_strategy' from DesignBrief with a typed schema that the
renderer and per-slide designer can consume directly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class VisualBrief:
    """Structured visual direction for a presentation deck.

    Generated once per deck by VisualDirectionAgent, then injected into:
    - DesignAdvisor system prompt (VISUAL DIRECTION section)
    - Per-slide design prompts (accent color, background slot, chart style)
    - Renderer (background images, color overrides, chart formatting)
    """

    # Deck register — determines the visual register (authority level, density, etc.)
    register: str  # "investor_pitch" | "executive_report" | "brand_editorial" | "consulting_proposal" | "technical_doc"
    tone: str  # "authoritative" | "visionary" | "approachable" | "data_first"

    # Template selection — VDA chooses this, replaces caller's preference
    template: str  # one of 38 Inkline templates (consulting, pitch, editorial, dmd_stripe, etc.)

    # Colour palette (typed, not prose descriptions)
    dominant_bg: str  # hex — background for 60% of slides
    secondary_bg: str  # hex — structural elements, cards, title blocks
    accent: str  # hex — single accent element per slide only
    text_primary: str  # hex — primary body text
    text_secondary: str  # hex — secondary text, captions
    divider_bg: str  # hex — full-bleed section divider slides

    # Image treatment strategy
    image_style: str  # "abstract_geometric" | "organic_ink" | "editorial_photo" | "icon_only" | "none"
    image_color_grade: str  # "cool" | "warm" | "monochrome" | "native"
    overlay_opacity: float  # 0.0–0.6 for text-over-image readability

    # Layout pacing (how to distribute visual density through the deck)
    interstitial_frequency: int  # every N content slides, insert a divider
    cover_treatment: str  # "full_bleed_dark" | "full_bleed_brand" | "light_editorial"
    avg_density: str  # "low" | "medium" | "high" — average content density

    # Chart and exhibit style
    chart_gridlines: bool  # show gridlines in charts
    chart_borders: bool  # show chart borders
    chart_accent_protocol: str  # "one_per_slide" (only ONE element highlighted) | "series_color"
    chart_data_labels: bool  # show values on chart elements
    chart_legend_position: str  # "top" | "bottom" | "right" | "off"

    # Background image generation requests (for n8n orchestration)
    background_requests: list[dict] = field(default_factory=list)
    # [{
    #     "slot": "cover" | "divider" | "hero" | "dark_callout",
    #     "prompt": "...",  # full Gemini prompt for image generation
    #     "style": "..."    # image treatment style hint
    # }]

    # Generated background image paths (filled by n8n after generation)
    background_paths: dict[str, str] = field(default_factory=dict)
    # {
    #     "cover": "/path/to/generated_cover.png",
    #     "divider": "/path/to/generated_divider.png",
    #     ...
    # }

    def to_json_for_prompt(self) -> str:
        """Export as JSON for injection into LLM prompts (VISUAL DIRECTION section)."""
        import json
        return json.dumps({
            "register": self.register,
            "template": self.template,
            "palette": {
                "dominant_bg": self.dominant_bg,
                "secondary_bg": self.secondary_bg,
                "accent": self.accent,
                "text_primary": self.text_primary,
                "text_secondary": self.text_secondary,
                "divider_bg": self.divider_bg,
            },
            "image_style": self.image_style,
            "image_color_grade": self.image_color_grade,
            "overlay_opacity": self.overlay_opacity,
            "interstitial_frequency": self.interstitial_frequency,
            "chart_style": {
                "gridlines": self.chart_gridlines,
                "borders": self.chart_borders,
                "accent_protocol": self.chart_accent_protocol,
                "data_labels": self.chart_data_labels,
                "legend_position": self.chart_legend_position,
            },
            "pacing": {
                "avg_density": self.avg_density,
                "cover_treatment": self.cover_treatment,
                "interstitial_frequency": self.interstitial_frequency,
            },
        }, indent=2)
