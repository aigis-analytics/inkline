"""Colour system — 60-30-10 rule application for professional slides.

60% = background (dominant)
30% = secondary (headings, card fills, table headers)
10% = accent (CTAs, highlights, key stats)

Usage:
    from inkline.core.colors import ColorScheme
    scheme = ColorScheme.from_brand(brand)
    bg = scheme.background       # 60% — slide background
    secondary = scheme.secondary  # 30% — headers, cards
    accent = scheme.accent        # 10% — highlights
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ColorScheme:
    """Application of the 60-30-10 colour rule to a brand palette."""

    # 60% — Background (dominant)
    background: str        # slide background
    surface: str           # card/container fill (slightly different from bg)

    # 30% — Secondary (structure)
    secondary: str         # headings, table headers, dark accents
    secondary_text: str    # text on secondary background

    # 10% — Accent (attention)
    accent: str            # CTAs, key stats, highlights
    accent_text: str       # text on accent background

    # Functional
    text: str              # primary body text
    muted: str             # captions, footnotes
    border: str            # dividers, table borders
    positive: str          # positive values, growth
    negative: str          # negative values, decline

    @classmethod
    def from_brand(cls, brand: "BaseBrand") -> ColorScheme:
        """Derive a 60-30-10 scheme from a brand definition."""
        return cls(
            background=brand.background,
            surface=brand.light_bg if hasattr(brand, "light_bg") else brand.background,
            secondary=brand.surface,
            secondary_text="#FFFFFF",
            accent=brand.primary,
            accent_text="#FFFFFF",
            text=brand.text,
            muted=brand.muted,
            border=brand.border if hasattr(brand, "border") else "#D1D5DB",
            positive="#16a34a",
            negative="#dc2626",
        )

    @classmethod
    def aigis_light(cls) -> ColorScheme:
        """Aigis Analytics light theme (white background)."""
        return cls(
            background="#FFFFFF",
            surface="#F4F6F8",
            secondary="#1B283B",
            secondary_text="#FFFFFF",
            accent="#1A7FA0",
            accent_text="#FFFFFF",
            text="#1A1A1A",
            muted="#6B7280",
            border="#D1D5DB",
            positive="#16a34a",
            negative="#dc2626",
        )

    @classmethod
    def aigis_dark(cls) -> ColorScheme:
        """Aigis Analytics dark theme (navy background)."""
        return cls(
            background="#0d1117",
            surface="#161b22",
            secondary="#1B283B",
            secondary_text="#c9d1d9",
            accent="#39D3BB",
            accent_text="#000000",
            text="#c9d1d9",
            muted="#8b949e",
            border="#30363d",
            positive="#3fb950",
            negative="#f85149",
        )


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert '#RRGGBB' to (R, G, B) tuple."""
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
