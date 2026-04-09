"""Declarative template system — backend-agnostic slide styling.

Templates define WHAT goes WHERE. Backends (PPTX or Google Slides)
handle HOW to render it.

Usage:
    from inkline.core.templates import get_template
    template = get_template("consulting")
    # template provides colour overrides, decoration shapes, layout preferences
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Decoration:
    """A decorative shape element on a slide."""
    shape: str = "RECTANGLE"  # RECTANGLE, ELLIPSE, LINE
    x: float = 0.0           # inches from left
    y: float = 0.0           # inches from top
    w: float = 10.0          # width in inches
    h: float = 0.08          # height in inches
    fill_color: str = ""     # hex colour
    opacity: float = 1.0     # 0.0–1.0


@dataclass
class SlideStyle:
    """Styling for a specific slide type within a template."""
    background: str = "#FFFFFF"
    title_color: str = "#1A1A1A"
    body_color: str = "#1A1A1A"
    muted_color: str = "#6B7280"
    accent_color: str = "#1A7FA0"
    decorations: list[Decoration] = field(default_factory=list)


@dataclass
class DeckTemplate:
    """Complete template definition for a presentation deck.

    Defines colour palette, decorations, and per-slide-type styling.
    Backend-agnostic — works with both PptxBuilder and SlideBuilder.
    """
    name: str
    description: str = ""

    # Global palette
    primary: str = "#1A7FA0"
    secondary: str = "#1B283B"
    accent: str = "#39D3BB"
    background: str = "#FFFFFF"
    surface: str = "#F4F6F8"
    text: str = "#1A1A1A"
    muted: str = "#6B7280"
    border: str = "#D1D5DB"

    # Per-slide-type styles
    title_slide: SlideStyle = field(default_factory=lambda: SlideStyle(
        background="#1B283B",
        title_color="#FFFFFF",
        body_color="#c9d1d9",
        accent_color="#1A7FA0",
    ))
    section_slide: SlideStyle = field(default_factory=lambda: SlideStyle(
        background="#1B283B",
        title_color="#FFFFFF",
    ))
    content_slide: SlideStyle = field(default_factory=lambda: SlideStyle(
        background="#FFFFFF",
        title_color="#1A1A1A",
        accent_color="#1A7FA0",
    ))
    closing_slide: SlideStyle = field(default_factory=lambda: SlideStyle(
        background="#1B283B",
        title_color="#FFFFFF",
    ))

    # Font preferences (override brand defaults if set)
    heading_font: str = ""
    body_font: str = ""


# ── Template Registry ────────────────────────────────────────────────────────

_TEMPLATES: dict[str, DeckTemplate] = {}


def register_template(name: str, template: DeckTemplate) -> None:
    """Register a template."""
    _TEMPLATES[name] = template


def get_template(name: str) -> DeckTemplate | None:
    """Get a registered template by name."""
    return _TEMPLATES.get(name)


def list_templates() -> list[str]:
    """List all registered template names."""
    return list(_TEMPLATES.keys())


# ── Built-in Templates ───────────────────────────────────────────────────────

# Consulting (McKinsey-inspired)
register_template("consulting", DeckTemplate(
    name="consulting",
    description="McKinsey-style — white bg, action titles, teal accent, source notes",
    primary="#0891B2",
    secondary="#1A2332",
    accent="#EA580C",
    background="#FFFFFF",
    surface="#F1F5F9",
    text="#1A2332",
    muted="#94A3B8",
    border="#CBD5E1",
    title_slide=SlideStyle(
        background="#1A2332",
        title_color="#FFFFFF",
        accent_color="#0891B2",
        decorations=[Decoration(shape="RECTANGLE", x=0, y=0, w=10, h=0.12, fill_color="#0891B2")],
    ),
    content_slide=SlideStyle(
        background="#FFFFFF",
        title_color="#1A2332",
        accent_color="#0891B2",
        decorations=[Decoration(shape="RECTANGLE", x=0.4, y=0.9, w=9.2, h=0.015, fill_color="#CBD5E1")],
    ),
))

# Executive (NotebookLM-inspired)
register_template("executive", DeckTemplate(
    name="executive",
    description="Premium executive — dark title, purple accent, yellow highlights",
    primary="#8D59E9",
    secondary="#0D0D0D",
    accent="#EBE021",
    background="#FAFAFA",
    surface="#FFFFFF",
    text="#111111",
    muted="#999999",
    border="#E0E0E0",
    title_slide=SlideStyle(
        background="#0D0D0D",
        title_color="#FFFFFF",
        accent_color="#8D59E9",
        decorations=[
            Decoration(shape="RECTANGLE", x=0, y=0, w=0.08, h=7.5, fill_color="#8D59E9"),
        ],
    ),
    content_slide=SlideStyle(
        background="#FAFAFA",
        title_color="#111111",
        accent_color="#8D59E9",
    ),
))

# Minimalism (NotebookLM-inspired)
register_template("minimalism", DeckTemplate(
    name="minimalism",
    description="Sharp-edged minimalist — light gray, black text, no decoration",
    primary="#111111",
    secondary="#333333",
    accent="#111111",
    background="#E9E9E9",
    surface="#F5F5F5",
    text="#111111",
    muted="#666666",
    border="#CCCCCC",
    title_slide=SlideStyle(background="#111111", title_color="#FFFFFF"),
    content_slide=SlideStyle(background="#E9E9E9", title_color="#111111"),
))

# Newspaper (NotebookLM-inspired)
register_template("newspaper", DeckTemplate(
    name="newspaper",
    description="Modern editorial — white bg, yellow highlights, bold headlines",
    primary="#111111",
    secondary="#111111",
    accent="#FFCC00",
    background="#FFFFFF",
    surface="#F5F5F5",
    text="#111111",
    muted="#666666",
    title_slide=SlideStyle(
        background="#111111",
        title_color="#FFFFFF",
        accent_color="#FFCC00",
    ),
    content_slide=SlideStyle(
        background="#FFFFFF",
        title_color="#111111",
        accent_color="#FFCC00",
    ),
))

# Investor (optimised for fundraising decks)
register_template("investor", DeckTemplate(
    name="investor",
    description="Investor pitch — clean, data-focused, blue accent, stat-heavy",
    primary="#2563EB",
    secondary="#1E293B",
    accent="#10B981",
    background="#FFFFFF",
    surface="#F8FAFC",
    text="#0F172A",
    muted="#64748B",
    border="#E2E8F0",
    title_slide=SlideStyle(
        background="#1E293B",
        title_color="#FFFFFF",
        accent_color="#2563EB",
        decorations=[Decoration(shape="RECTANGLE", x=0, y=7.42, w=10, h=0.08, fill_color="#2563EB")],
    ),
    content_slide=SlideStyle(
        background="#FFFFFF",
        title_color="#0F172A",
        accent_color="#2563EB",
        decorations=[Decoration(shape="RECTANGLE", x=0.4, y=0.92, w=9.2, h=0.015, fill_color="#E2E8F0")],
    ),
))
