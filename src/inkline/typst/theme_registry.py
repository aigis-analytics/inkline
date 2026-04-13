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
    "pitch": {
        "desc": "Startup pitch — bold hero stats, clean white",
        "title_bg_override": "#111111",
        "title_fg_override": "#FFFFFF",
        "bg_override": "#FFFFFF",
        "card_fill_override": "#F8F9FA",
        "surface_override": "#F8F9FA",
    },
    "dark": {
        "desc": "Full dark mode — dark bg, light text",
        "title_bg_override": "#0D1117",
        "title_fg_override": "#E6EDF3",
        "bg_override": "#0D1117",
        "text_override": "#E6EDF3",
        "muted_override": "#8B949E",
        "border_override": "#30363D",
        "card_fill_override": "#161B22",
        "surface_override": "#161B22",
    },
    "editorial": {
        "desc": "Magazine editorial — warm surface, black headers",
        "title_bg_override": "#1A1A18",
        "title_fg_override": "#FAFAF8",
        "bg_override": "#FAFAF8",
        "card_fill_override": "#F0EDE6",
        "surface_override": "#F0EDE6",
    },
    "boardroom": {
        "desc": "Executive board — charcoal header, gold accent",
        "title_bg_override": "#1F2937",
        "title_fg_override": "#FFFFFF",
        "accent2_override": "#D97706",
        "bg_override": "#FFFFFF",
        "card_fill_override": "#F9FAFB",
        "surface_override": "#F9FAFB",
    },
    "brand": {
        "desc": "Uses brand colors directly — no template overrides",
    },
}

# Merge built-in curated design system styles into SLIDE_TEMPLATES
try:
    from inkline.intelligence.design_md_styles import DESIGN_MD_TEMPLATES
    SLIDE_TEMPLATES.update(DESIGN_MD_TEMPLATES)
except Exception:
    pass  # Non-blocking: curated styles are optional


def _load_user_templates() -> None:
    """Scan user-controlled directories for additional slide templates.

    Each ``.py`` file found is imported; any top-level ``dict`` with a
    ``"desc"`` key is registered into ``SLIDE_TEMPLATES``.  Errors never raise.

    Search order (first-win per template name):
    1. Every path in ``$INKLINE_TEMPLATES_DIR`` (colon-separated)
    2. ``~/.config/inkline/templates/``
    3. ``./inkline_templates/`` (current working directory)

    Example template file (``~/.config/inkline/templates/mycorp_templates.py``)::

        my_bd_template = {
            "desc": "In-house board deck — charcoal header, gold accent",
            "title_bg_override": "#1A1A1A",
            "title_fg_override": "#FFFFFF",
            "accent2_override": "#C9A84C",
        }
    """
    import importlib.util
    import logging
    import os
    from pathlib import Path

    _log = logging.getLogger("inkline.typst")

    search_dirs: list[Path] = []
    if env := os.environ.get("INKLINE_TEMPLATES_DIR"):
        search_dirs.extend(Path(p) for p in env.split(os.pathsep) if p)
    xdg = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    search_dirs.append(xdg / "inkline" / "templates")
    search_dirs.append(Path.cwd() / "inkline_templates")

    for search_dir in search_dirs:
        if not search_dir.is_dir():
            continue
        for py_file in sorted(search_dir.glob("*.py")):
            if py_file.stem.startswith("_"):
                continue
            try:
                spec = importlib.util.spec_from_file_location(
                    f"inkline._user_templates.{py_file.stem}", py_file
                )
                if spec is None or spec.loader is None:
                    continue
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)  # type: ignore[arg-type]
                registered = 0
                for attr_name in dir(mod):
                    obj = getattr(mod, attr_name)
                    if isinstance(obj, dict) and "desc" in obj and not attr_name.startswith("_"):
                        key = attr_name.lower()
                        if key not in SLIDE_TEMPLATES:
                            SLIDE_TEMPLATES[key] = obj
                            registered += 1
                if registered:
                    _log.debug("Loaded %d user templates from %s", registered, py_file)
            except Exception as exc:  # noqa: BLE001
                _log.warning("Failed to load user templates from %s: %s", py_file, exc)


_load_user_templates()


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

    # If the brand has a non-white background (e.g., cream/off-white), use it
    # as the title slide background too — the brand's own color scheme takes
    # priority over the template's dark title default.
    if brand.background.upper() not in ("#FFFFFF", "#FFF"):
        theme["title_bg"] = brand.background
        theme["title_fg"] = brand.text  # dark text on light bg
        theme["bg"] = brand.background  # content slides match

    return theme


def get_all_themes(brand: BaseBrand) -> dict[str, dict]:
    """Generate all slide template themes for a given brand.

    Returns
    -------
    dict[str, dict]
        Mapping of template name to Typst theme dict.
    """
    return {name: brand_to_typst_theme(brand, name) for name in SLIDE_TEMPLATES}


