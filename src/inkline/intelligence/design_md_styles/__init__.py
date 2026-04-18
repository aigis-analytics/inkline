"""design.md style catalog — 27 design systems from getdesign.md.

Parses curated DESIGN.md files (brand design system specs inspired by companies
like Stripe, Vercel, Notion, Apple, etc.) into structured style definitions
usable by the DesignAdvisor, OverflowAuditor, and theme_registry.

Each style provides:
- Color palette (primary, background, text, accent, surface, chart colors)
- Typography hints (heading + body font families)
- Tags for style matching (dark, minimal, gradient, fintech, etc.)
- Description for LLM context
- Slide template overrides compatible with theme_registry.SLIDE_TEMPLATES

Usage
-----
    from inkline.intelligence.design_md_styles import (
        DESIGN_MD_STYLES,       # dict[str, DesignMdStyle]
        DESIGN_MD_TEMPLATES,    # dict[str, dict] — SLIDE_TEMPLATES format
        get_style,              # lookup by name
        find_styles_by_tag,     # filter by tag
        get_playbook_text,      # markdown for design advisor context
    )

Source: https://getdesign.md — 66 open-source design system specs (27 curated).
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

log = logging.getLogger(__name__)

_STYLES_DIR = Path(__file__).parent


@dataclass
class DesignMdStyle:
    """Structured design system extracted from a DESIGN.md file."""
    name: str
    display_name: str
    description: str
    tags: list[str]

    # Palette
    primary: str
    secondary: str
    background: str
    text: str
    accent: str
    surface: str
    border: str
    muted: str
    chart_colors: list[str]

    # Typography
    heading_font: str
    body_font: str
    mono_font: str

    # Template overrides (for theme_registry)
    title_bg: str
    title_fg: str

    # Source
    source_file: str = ""


def _extract_hex(text: str) -> list[str]:
    return list(dict.fromkeys(re.findall(r'#[0-9a-fA-F]{6}\b', text)))


def _extract_named_colors(text: str) -> dict[str, str]:
    colors: dict[str, str] = {}
    for m in re.finditer(r'\*\*([^*]+)\*\*.*?[(`]+(#[0-9a-fA-F]{6})', text):
        colors[m.group(1).strip()] = m.group(2)
    for m in re.finditer(r'\|\s*([^|]+?)\s*\|\s*.*?(#[0-9a-fA-F]{6})', text):
        name = m.group(1).strip().strip('`*')
        if name and 2 < len(name) < 40:
            colors[name] = m.group(2)
    return colors


def _find_color(named: dict[str, str], keywords: list[str], fallback: str) -> str:
    for name, hex_val in named.items():
        name_lower = name.lower()
        if any(k in name_lower for k in keywords):
            return hex_val
    return fallback


def _extract_fonts(text: str) -> list[str]:
    fonts: list[str] = []
    for m in re.finditer(
        r'`([A-Z][a-zA-Z\s\-]+?'
        r'(?:Sans|Serif|Mono|Pro|Var|Grotesk|Display|Neue|Rounded|Text|Code|Gothic|Move|Cereal|Inter|Plex|Aeonik|Geist|Mona|Roobert|Messina|Matter|Circular|Walsheim)'
        r'[a-zA-Z\s\-]*)`', text
    ):
        fonts.append(m.group(1).strip())
    return list(dict.fromkeys(fonts))


def _classify(text: str) -> list[str]:
    tl = text.lower()
    tags = []
    checks = [
        ('dark', ['dark mode', 'dark background', 'dark bg', 'dark theme', '#0d1117', '#000000', '#111111', '#0a0a0a']),
        ('minimal', ['minimal', 'clean', 'whitespace', 'simplicity', 'precision']),
        ('gradient', ['gradient', 'mesh gradient', 'linear-gradient']),
        ('premium', ['premium', 'luxury', 'elegant', 'sophisticated']),
        ('vibrant', ['playful', 'fun', 'bold color', 'vibrant', 'saturated']),
        ('editorial', ['editorial', 'magazine', 'serif heading', 'publishing']),
        ('developer', ['developer', 'engineering', 'code', 'terminal', 'monospace']),
        ('fintech', ['fintech', 'financial', 'banking', 'payment', 'crypto']),
        ('saas', ['saas', 'dashboard', 'analytics', 'productivity']),
        ('automotive', ['automotive', 'vehicle', 'car', 'driving']),
        ('consumer', ['consumer', 'marketplace', 'social', 'travel']),
        ('warm', ['warm', 'serif', 'organic', 'friendly', 'human']),
        ('monochrome', ['monochrome', 'black and white', 'grayscale']),
    ]
    for tag, kws in checks:
        if any(k in tl for k in kws):
            tags.append(tag)
    return tags


def _is_dark_bg(hex_color: str) -> bool:
    hex_color = hex_color.lstrip('#')
    if len(hex_color) != 6:
        return False
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return (r * 0.299 + g * 0.587 + b * 0.114) < 128


def _ensure_readable(fg: str, bg: str, *, dark_fallback: str = "#111111", light_fallback: str = "#FFFFFF") -> str:
    """Return fg if it has adequate contrast against bg, else return a readable fallback."""
    if _is_dark_bg(bg) and _is_dark_bg(fg):
        return light_fallback   # dark-on-dark → use white
    if not _is_dark_bg(bg) and not _is_dark_bg(fg):
        return dark_fallback    # light-on-light → use near-black
    return fg


def _lighten_dark_bg(hex_color: str, amount: int = 30) -> str:
    """Lighten a dark hex color by a fixed RGB amount (for card surfaces on dark themes)."""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) != 6:
        return hex_color
    r = min(255, int(hex_color[0:2], 16) + amount)
    g = min(255, int(hex_color[2:4], 16) + amount)
    b = min(255, int(hex_color[4:6], 16) + amount)
    return f"#{r:02X}{g:02X}{b:02X}"


def parse_design_md(filepath: Path) -> DesignMdStyle | None:
    """Parse a single DESIGN.md file into a DesignMdStyle."""
    try:
        text = filepath.read_text(encoding="utf-8")
    except Exception:
        return None

    name = filepath.stem
    named = _extract_named_colors(text)
    all_hex = _extract_hex(text)
    fonts = _extract_fonts(text)
    tags = _classify(text)

    # Extract description: first non-heading paragraph after the title
    desc = ""
    # Find first paragraph that isn't a heading (doesn't start with #)
    for para in re.split(r'\n\n+', text):
        para = para.strip()
        if para and not para.startswith('#') and len(para) > 50:
            # Clean markdown formatting
            clean = re.sub(r'[`*_]', '', para)
            desc = clean[:200]
            break
    if not desc:
        desc = f"Design system inspired by {name.title()}"

    # Resolve role-based colors
    primary = _find_color(named, ['primary', 'brand color', 'brand blue', 'brand green'], '')
    if not primary:
        primary = _find_color(named, ['cta', 'link', 'action'], all_hex[0] if all_hex else '#333333')

    bg = _find_color(named, ['background', 'page bg', 'canvas', 'page background'], '#FFFFFF')
    text_raw = _find_color(named, ['heading', 'text primary', 'foreground'], '')
    text_color = _ensure_readable(text_raw or ('#FFFFFF' if _is_dark_bg(bg) else '#111111'), bg)
    accent = _find_color(named, ['accent', 'secondary', 'highlight'], primary)
    surface = _find_color(named, ['surface', 'card bg', 'card background', 'container'], '')
    if not surface:
        surface = '#F8F9FA' if not _is_dark_bg(bg) else _lighten_dark_bg(bg, 28)
    border = _find_color(named, ['border', 'divider', 'separator'], '#E5E7EB' if not _is_dark_bg(bg) else '#444444')
    muted_raw = _find_color(named, ['muted', 'caption', 'secondary text', 'subtle'], '')
    if not muted_raw:
        muted = '#6B7280' if not _is_dark_bg(bg) else '#A0A0B0'
    else:
        muted = _ensure_readable(muted_raw, bg, dark_fallback='#6B7280', light_fallback='#A0A0B0')

    # Build chart color palette from available colors
    chart_candidates = [v for v in named.values() if v not in (bg, text_color, '#FFFFFF', '#000000')]
    chart_colors = chart_candidates[:6] if len(chart_candidates) >= 3 else [
        primary, accent, '#3fb950', '#58a6ff', '#f0883e', '#d2a8ff'
    ]

    # Title slide: typically dark bg + white text
    is_dark = _is_dark_bg(bg)
    title_bg = bg if is_dark else (text_color if _is_dark_bg(text_color) else '#111111')
    title_fg = _ensure_readable(text_color, title_bg)

    # Typography
    heading_font = fonts[0] if fonts else 'Inter'
    body_font = fonts[1] if len(fonts) > 1 else heading_font
    mono_font = next((f for f in fonts if any(k in f.lower() for k in ['mono', 'code'])), 'Roboto Mono')

    display_name = name.replace('-', ' ').replace('_', ' ').title()

    return DesignMdStyle(
        name=name,
        display_name=display_name,
        description=desc,
        tags=tags,
        primary=primary,
        secondary=accent,
        background=bg,
        text=text_color,
        accent=accent,
        surface=surface,
        border=border,
        muted=muted,
        chart_colors=chart_colors[:6],
        heading_font=heading_font,
        body_font=body_font,
        mono_font=mono_font,
        title_bg=title_bg,
        title_fg=title_fg,
        source_file=filepath.name,
    )


def _load_all() -> dict[str, DesignMdStyle]:
    styles: dict[str, DesignMdStyle] = {}
    for md_file in sorted(_STYLES_DIR.glob("*.md")):
        style = parse_design_md(md_file)
        if style:
            styles[style.name] = style
    return styles


# ─── Public API ──────────────────────────────────────────────────────────────

DESIGN_MD_STYLES: dict[str, DesignMdStyle] = _load_all()


def get_style(name: str) -> DesignMdStyle | None:
    """Get a design.md style by name."""
    return DESIGN_MD_STYLES.get(name)


def find_styles_by_tag(*tags: str) -> list[DesignMdStyle]:
    """Find styles matching any of the given tags."""
    tag_set = set(tags)
    return [s for s in DESIGN_MD_STYLES.values() if tag_set & set(s.tags)]


def list_style_names() -> list[str]:
    """List all available design.md style names."""
    return list(DESIGN_MD_STYLES.keys())


def to_slide_template(style: DesignMdStyle) -> dict:
    """Convert a DesignMdStyle into a SLIDE_TEMPLATES-compatible dict."""
    tpl: dict = {
        "desc": f"{style.display_name} style — {style.description[:80]}",
        "title_bg_override": style.title_bg,
        "title_fg_override": style.title_fg,
        "accent_override": style.primary,
    }
    if style.secondary != style.primary:
        tpl["accent2_override"] = style.secondary
    if not _is_dark_bg(style.background):
        tpl["bg_override"] = style.background
        tpl["card_fill_override"] = style.surface
        tpl["surface_override"] = style.surface
    else:
        bg = style.background
        # Guarantee readable text on the slide background
        text = _ensure_readable(style.text, bg)
        muted = _ensure_readable(style.muted, bg, dark_fallback='#6B7280', light_fallback='#A0A0B0')
        # Card surface must stay in the same luminance band as the bg so the
        # slide-level text color (now forced white) remains readable on the card.
        # If the extracted surface is light (common when the spec has a "card" color
        # from the light-mode variant), darken it to stay readable.
        card = style.surface if _is_dark_bg(style.surface) else _lighten_dark_bg(bg, 28)
        border = style.border if not _is_dark_bg(style.border) else '#555555'
        tpl["bg_override"] = bg
        tpl["text_override"] = text
        tpl["muted_override"] = muted
        tpl["border_override"] = border
        tpl["card_fill_override"] = card
        tpl["surface_override"] = card
    # Ensure title_fg is always readable against title_bg
    tpl["title_fg_override"] = _ensure_readable(
        tpl.get("title_fg_override", "#FFFFFF"),
        tpl.get("title_bg_override", "#111111"),
    )
    return tpl


# Pre-built template dict for theme_registry integration
DESIGN_MD_TEMPLATES: dict[str, dict] = {
    f"dmd_{style.name}": to_slide_template(style)
    for style in DESIGN_MD_STYLES.values()
}


def get_playbook_text() -> str:
    """Generate a markdown playbook section describing all design.md styles.

    This is injected into the DesignAdvisor's system prompt when the user
    requests a specific design.md style or when style recommendations are needed.
    """
    lines = [
        "## Design.md Style Catalog (27 curated design systems)",
        "",
        "These are production-grade design systems extracted from world-class",
        "companies. Use them as style references when the user requests a specific",
        "aesthetic or when recommending a visual direction.",
        "",
        "To apply a style, use the template name `dmd_<name>` (e.g., `dmd_stripe`,",
        "`dmd_vercel`, `dmd_notion`). Each style provides full color overrides",
        "compatible with Inkline's theme system.",
        "",
        "| Style | Tags | Primary | BG | Fonts | Best For |",
        "|-------|------|---------|-----|-------|----------|",
    ]
    for s in DESIGN_MD_STYLES.values():
        tags = ", ".join(s.tags[:3])
        fonts = s.heading_font[:20]
        best_for = s.description[:50]
        lines.append(
            f"| `dmd_{s.name}` | {tags} | `{s.primary}` | `{s.background}` | {fonts} | {best_for} |"
        )

    lines.extend([
        "",
        "### Style Groups",
        "",
        "**Fintech/Premium:** dmd_stripe, dmd_coinbase, dmd_revolut — purple/blue accents, weight-300 headlines, blue-tinted shadows",
        "**Developer/Dark:** dmd_vercel, dmd_cursor, dmd_warp, dmd_supabase, dmd_raycast — monochrome/emerald, Geist/mono fonts, dark surfaces",
        "**Consumer/Warm:** dmd_airbnb, dmd_notion, dmd_spotify — friendly palettes, rounded elements, warm typography",
        "**Editorial/Minimal:** dmd_apple, dmd_tesla, dmd_framer — extreme whitespace, SF Pro/custom sans, photographic hero sections",
        "**SaaS/Product:** dmd_shopify, dmd_figma, dmd_intercom, dmd_miro — accessible palettes, system fonts, card-heavy layouts",
        "**Automotive/Luxury:** dmd_bmw, dmd_ferrari, dmd_tesla — dark immersive, custom display fonts, cinematic imagery",
        "",
        "### Applying a Style",
        "",
        "When the user says 'make it look like Stripe' or 'Vercel aesthetic',",
        "select the matching `dmd_*` template. The template provides color",
        "overrides that layer on top of the active brand palette. Typography",
        "hints from the style should inform your font and weight choices.",
    ])
    return "\n".join(lines)


log.debug("Loaded %d design.md styles", len(DESIGN_MD_STYLES))
