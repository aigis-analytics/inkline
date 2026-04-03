"""Viral Infotainment template — inspired by sabrina.dev viral PowerPoint style.

Design principles:
- Clean off-white background, near-black text
- ONE strong accent color per slide (blue default)
- Roboto Mono / monospace typography feel
- No gradients, shadows, or rounded cards
- Every slide has one strong visual focus
- Max 8 words headline, max 15 words per bullet
"""

from __future__ import annotations

from typing import Any

from inkline.brands import BaseBrand
from inkline.slides import elements as el


_INFOTAINMENT = {
    "bg": "#FAFAF9",          # Off-white
    "text": "#171717",         # Near black
    "accent": "#2563EB",       # Strong blue
    "muted": "#A3A3A3",        # Neutral gray
    "surface": "#FFFFFF",
    "border": "#E5E5E5",
}


def template_infotainment(
    slide_id: str,
    brand: BaseBrand,
    slide_index: int,
    total_slides: int,
) -> list[dict]:
    """Apply viral infotainment template styling.

    Returns batchUpdate requests for base styling.
    """
    requests: list[dict] = []

    # Off-white background
    requests.append(el.set_slide_background(slide_id, _INFOTAINMENT["bg"]))

    if slide_index == 0:
        # Title slide: bold blue accent block (left edge)
        _, bar_reqs = el.create_shape(
            slide_id, "RECTANGLE",
            x=0, y=0, w=0.2, h=7.5,
            fill_color=_INFOTAINMENT["accent"],
        )
        requests.extend(bar_reqs)

        # Thin bottom rule
        _, rule_reqs = el.create_line(
            slide_id,
            x1=0.5, y1=7.0, x2=9.5, y2=7.0,
            color=_INFOTAINMENT["border"], weight_pt=1.0,
        )
        requests.extend(rule_reqs)

    elif slide_index == total_slides - 1:
        # Closing slide: blue bar at bottom
        _, bar_reqs = el.create_shape(
            slide_id, "RECTANGLE",
            x=0, y=7.0, w=10.0, h=0.5,
            fill_color=_INFOTAINMENT["accent"],
        )
        requests.extend(bar_reqs)

    else:
        # Content slides: accent dot + slide number
        _, dot_reqs = el.create_shape(
            slide_id, "ELLIPSE",
            x=0.5, y=0.3, w=0.2, h=0.2,
            fill_color=_INFOTAINMENT["accent"],
        )
        requests.extend(dot_reqs)

        # Slide number (monospace style, top-right)
        _, num_reqs = el.create_text_box(
            slide_id, f"{slide_index:02d}/{total_slides:02d}",
            x=8.5, y=0.3, w=1.2, h=0.3,
            font=brand.body_font, size_pt=9,
            color=_INFOTAINMENT["muted"],
            alignment="END",
        )
        requests.extend(num_reqs)

        # Bottom separator
        _, sep_reqs = el.create_line(
            slide_id,
            x1=0.5, y1=7.0, x2=9.5, y2=7.0,
            color=_INFOTAINMENT["border"], weight_pt=0.5,
        )
        requests.extend(sep_reqs)

    return requests
