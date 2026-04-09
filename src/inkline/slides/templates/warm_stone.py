"""Warm Stone template — off-white / warm-stone advisor-pitch aesthetic.

Design principles:
- Off-white / warm stone (#E7E7E3) background — NOT pure white
- Near-black (#0C0D0E) text with bold condensed headings
- Dark charcoal (#1D1D1A) for card backgrounds and emphasis
- Warm gray (#C7CAC1) for secondary card fills
- Muted gray (#545759) for captions and secondary text
- Deep navy (#1A3A5C) used sparingly as accent (CTA slides, highlights)
- White (#FFFFFF) card surfaces on the warm background
- Simple, clean, no decoration — authority through typography weight
- Bold uppercase section headers
"""

from __future__ import annotations

from inkline.brands import BaseBrand
from inkline.slides import elements as el


_PALETTE = {
    "bg": "#E7E7E3",           # Off-white / warm stone (primary background)
    "surface": "#FFFFFF",       # White cards
    "card_dark": "#0C0D0E",    # Near-black (dark card backgrounds)
    "card_warm": "#D7D8D1",    # Warm light gray (section cards)
    "card_muted": "#C7CAC1",   # Muted warm gray (secondary cards)
    "text": "#0C0D0E",         # Near-black body text
    "text_dark": "#1D1D1A",    # Charcoal emphasis
    "text_light": "#FFFFFF",   # Text on dark backgrounds
    "muted": "#545759",        # Captions, secondary
    "accent": "#1A3A5C",       # Deep navy (CTA, highlights)
    "line": "#1D1D1A",         # Rules and borders
    "subtle_bg": "#F5F5F5",    # Lightest fill
}


def template_warm_stone(
    slide_id: str,
    brand: BaseBrand,
    slide_index: int,
    total_slides: int,
) -> list[dict]:
    """Apply Warm Stone template styling.

    Returns batchUpdate requests for base styling.
    """
    requests: list[dict] = []

    if slide_index == 0:
        # ── Title slide: warm stone bg, dark accent blocks ──
        requests.append(el.set_slide_background(slide_id, _PALETTE["bg"]))

        # Dark header strip (top)
        _, strip_reqs = el.create_shape(
            slide_id, "RECTANGLE",
            x=0, y=0, w=10.0, h=0.08,
            fill_color=_PALETTE["card_dark"],
        )
        requests.extend(strip_reqs)

        # Small muted gray accent block (bottom-left)
        _, accent_reqs = el.create_shape(
            slide_id, "RECTANGLE",
            x=0.5, y=6.5, w=2.0, h=0.06,
            fill_color=_PALETTE["muted"],
        )
        requests.extend(accent_reqs)

    elif slide_index == total_slides - 1:
        # ── Closing / CTA slide: dark background ──
        requests.append(el.set_slide_background(slide_id, _PALETTE["card_dark"]))

        # Navy accent bar (bottom)
        _, bar_reqs = el.create_shape(
            slide_id, "RECTANGLE",
            x=0, y=7.3, w=10.0, h=0.2,
            fill_color=_PALETTE["accent"],
        )
        requests.extend(bar_reqs)

    else:
        # ── Content slides: warm stone bg, clean layout ──
        requests.append(el.set_slide_background(slide_id, _PALETTE["bg"]))

        # Section label accent bar (thin, top-left)
        _, accent_reqs = el.create_shape(
            slide_id, "RECTANGLE",
            x=0.5, y=0.35, w=1.5, h=0.06,
            fill_color=_PALETTE["card_dark"],
        )
        requests.extend(accent_reqs)

        # Bottom rule (charcoal, thin)
        _, rule_reqs = el.create_line(
            slide_id,
            x1=0.5, y1=7.0, x2=9.5, y2=7.0,
            color=_PALETTE["line"], weight_pt=0.75,
        )
        requests.extend(rule_reqs)

        # Slide number (bottom-right, muted)
        _, num_reqs = el.create_text_box(
            slide_id, f"{slide_index}",
            x=9.0, y=7.05, w=0.5, h=0.25,
            font=brand.body_font, size_pt=8,
            color=_PALETTE["muted"],
            alignment="END",
        )
        requests.extend(num_reqs)

    return requests
