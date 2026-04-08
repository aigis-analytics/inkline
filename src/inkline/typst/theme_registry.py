"""Theme registry — maps Brand + template name to Typst theme dicts.

A Typst theme dict contains all color tokens needed to render slides or documents.
Themes are generated from BaseBrand instances, with template-specific overrides
for layout style (e.g., dark title slides, accent variations).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from inkline.brands import BaseBrand


# ---------------------------------------------------------------------------
# Slide template definitions (layout-style overrides)
# ---------------------------------------------------------------------------

SLIDE_TEMPLATES: dict[str, dict] = {
    "executive": {
        "desc": "Premium dark title, purple accent, yellow highlights",
        "title_bg_override": "#0D0D0D",
        "title_fg_override": "#FFFFFF",
        "accent_override": "#8D59E9",
        "accent2_override": "#EBE021",
        "bg_override": "#FAFAFA",
        "card_fill_override": "#FFFFFF",
        "surface_override": "#FFFFFF",
    },
    "minimalism": {
        "desc": "Sharp-edged, light gray, black text, no decoration",
        "title_bg_override": "#111111",
        "title_fg_override": "#FFFFFF",
        "bg_override": "#E9E9E9",
        "card_fill_override": "#F5F5F5",
        "surface_override": "#F5F5F5",
    },
    "newspaper": {
        "desc": "Modern editorial, white bg, yellow highlights",
        "title_bg_override": "#111111",
        "title_fg_override": "#FFFFFF",
        "accent2_override": "#FFCC00",
        "bg_override": "#FFFFFF",
        "card_fill_override": "#F5F5F5",
        "surface_override": "#F5F5F5",
    },
    "investor": {
        "desc": "Fundraising deck — clean, data-focused",
        "title_bg_override": "#1E293B",
        "title_fg_override": "#FFFFFF",
        "bg_override": "#FFFFFF",
        "card_fill_override": "#F8FAFC",
        "surface_override": "#F8FAFC",
    },
    "consulting": {
        "desc": "McKinsey-style — white bg, action titles",
        "title_bg_override": "#1A2332",
        "title_fg_override": "#FFFFFF",
        "bg_override": "#FFFFFF",
        "card_fill_override": "#F1F5F9",
        "surface_override": "#F1F5F9",
    },
    "brand": {
        "desc": "Uses brand colors directly — no template overrides",
    },
}


def brand_to_typst_theme(brand: BaseBrand, template: str = "brand") -> dict:
    """Generate a Typst theme dict from a BaseBrand instance.

    Parameters
    ----------
    brand : BaseBrand
        The brand identity to use.
    template : str
        Slide template name. ``"brand"`` uses brand colors directly;
        other templates apply layout-specific overrides.

    Returns
    -------
    dict
        Theme dict with all color tokens for Typst rendering.
    """
    # Base theme from brand palette
    theme = {
        "name": brand.display_name or brand.name.title(),
        "desc": f"{brand.display_name} — {brand.tagline}" if brand.tagline else brand.display_name,
        "bg": brand.background,
        "title_bg": brand.surface,
        "title_fg": "#FFFFFF",
        "text": brand.text,
        "muted": brand.muted,
        "accent": brand.primary,
        "accent2": brand.secondary,
        "border": brand.border,
        "surface": brand.light_bg,
        "card_fill": brand.light_bg,
        # Typography
        "heading_font": brand.heading_font,
        "body_font": brand.body_font,
        "heading_size": brand.heading_size,
        "body_size": brand.body_size,
        # Assets
        "logo_dark_path": brand.logo_dark_path,
        "logo_light_path": brand.logo_light_path,
        # Metadata
        "confidentiality": brand.confidentiality,
        "footer_text": brand.footer_text,
        # Chart colors
        "chart_colors": brand.chart_colors,
    }

    # Apply template overrides
    tpl = SLIDE_TEMPLATES.get(template, {})
    for key, value in tpl.items():
        if key.endswith("_override"):
            theme_key = key.replace("_override", "")
            theme[theme_key] = value
    if "desc" in tpl:
        theme["desc"] = tpl["desc"]

    return theme


def get_all_themes(brand: BaseBrand) -> dict[str, dict]:
    """Generate all slide template themes for a given brand.

    Returns
    -------
    dict[str, dict]
        Mapping of template name to Typst theme dict.
    """
    return {name: brand_to_typst_theme(brand, name) for name in SLIDE_TEMPLATES}


# ---------------------------------------------------------------------------
# Pre-built Aigis theme variants (warm beige advisor pitch aesthetic)
# ---------------------------------------------------------------------------

AIGIS_ADVISOR_PITCH = {
    "name": "Aigis Analytics",
    "desc": "Warm beige, Hubot Sans, advisor pitch aesthetic",
    "bg": "#e8e8e3",
    "title_bg": "#e8e8e3",
    "title_fg": "#0c0d0f",
    "text": "#0c0d0f",
    "muted": "#55575a",
    "accent": "#1a3a5c",
    "accent2": "#39d3bb",
    "border": "#c8cac1",
    "surface": "#e8e8e3",
    "card_fill": "#e8e8e3",
    "heading_font": "Hubot Sans",
    "body_font": "Roboto Condensed",
    "heading_size": 28,
    "body_size": 14,
    "logo_dark_path": "aigis_logo_dark.png",
    "logo_light_path": "aigis_logo_white.png",
    "confidentiality": "Private & Confidential",
    "footer_text": "Aigis Analytics Pty Ltd",
    "chart_colors": ["#3fb950", "#1A7FA0", "#f0883e", "#58a6ff", "#d2a8ff", "#e6c069"],
}

AIGIS_DARK = {
    "name": "Aigis Analytics",
    "desc": "Dark variant — for dashboards and title slides",
    "bg": "#0d1117",
    "title_bg": "#0d1117",
    "title_fg": "#e6edf3",
    "text": "#e6edf3",
    "muted": "#8b949e",
    "accent": "#39d3bb",
    "accent2": "#1A7FA0",
    "border": "#30363d",
    "surface": "#161b22",
    "card_fill": "#161b22",
    "heading_font": "Hubot Sans",
    "body_font": "Roboto Condensed",
    "heading_size": 28,
    "body_size": 14,
    "logo_dark_path": "aigis_logo_dark.png",
    "logo_light_path": "aigis_logo_white.png",
    "confidentiality": "Private & Confidential",
    "footer_text": "Aigis Analytics Pty Ltd",
    "chart_colors": ["#3fb950", "#58a6ff", "#f0883e", "#d2a8ff", "#e6c069", "#79c0ff"],
}
