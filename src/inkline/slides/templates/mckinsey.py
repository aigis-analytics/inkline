"""McKinsey Consulting template — professional strategy presentation style.

Design principles:
- Clean white background, dark blue/black text
- Teal accent for key insights, orange for warnings
- One message per slide, action titles as sentences
- Source citations at bottom of data slides
- White space is mandatory, 2-3 colors max + grays
- Sans-serif (Arial/Helvetica/Calibri), left-aligned body
"""

from __future__ import annotations

from typing import Any

from inkline.brands import BaseBrand
from inkline.slides import elements as el


_MCKINSEY = {
    "bg": "#FFFFFF",
    "text": "#1A2332",         # Dark navy/charcoal
    "teal": "#0891B2",         # Teal accent
    "orange": "#EA580C",       # Warning/alert
    "muted": "#94A3B8",        # Slate gray
    "light": "#F1F5F9",        # Subtle section bg
    "border": "#CBD5E1",       # Light border
}


def template_mckinsey(
    slide_id: str,
    brand: BaseBrand,
    slide_index: int,
    total_slides: int,
) -> list[dict]:
    """Apply McKinsey consulting template styling.

    Returns batchUpdate requests for base styling.
    """
    requests: list[dict] = []

    # White background
    requests.append(el.set_slide_background(slide_id, _MCKINSEY["bg"]))

    if slide_index == 0:
        # Title slide: teal top bar (full-width, professional)
        _, bar_reqs = el.create_shape(
            slide_id, "RECTANGLE",
            x=0, y=0, w=10.0, h=0.12,
            fill_color=_MCKINSEY["teal"],
        )
        requests.extend(bar_reqs)

        # Thin dark rule below header area
        _, rule_reqs = el.create_line(
            slide_id,
            x1=0.8, y1=2.2, x2=9.2, y2=2.2,
            color=_MCKINSEY["border"], weight_pt=1.0,
        )
        requests.extend(rule_reqs)

        # Brand name (small, top-right, muted)
        _, brand_reqs = el.create_text_box(
            slide_id, brand.display_name,
            x=6.0, y=0.25, w=3.5, h=0.3,
            font=brand.body_font, size_pt=9,
            color=_MCKINSEY["muted"],
            alignment="END",
        )
        requests.extend(brand_reqs)

        # Teal bottom bar
        _, bottom_reqs = el.create_shape(
            slide_id, "RECTANGLE",
            x=0, y=7.38, w=10.0, h=0.12,
            fill_color=_MCKINSEY["teal"],
        )
        requests.extend(bottom_reqs)

    elif slide_index == total_slides - 1:
        # Closing slide: teal bars top + bottom
        _, top_reqs = el.create_shape(
            slide_id, "RECTANGLE",
            x=0, y=0, w=10.0, h=0.12,
            fill_color=_MCKINSEY["teal"],
        )
        requests.extend(top_reqs)

        _, bottom_reqs = el.create_shape(
            slide_id, "RECTANGLE",
            x=0, y=7.38, w=10.0, h=0.12,
            fill_color=_MCKINSEY["teal"],
        )
        requests.extend(bottom_reqs)

    else:
        # Content slides: action title area with rule
        _, rule_reqs = el.create_line(
            slide_id,
            x1=0.8, y1=1.1, x2=9.2, y2=1.1,
            color=_MCKINSEY["border"], weight_pt=0.75,
        )
        requests.extend(rule_reqs)

        # Teal accent dash (left of title area)
        _, dash_reqs = el.create_shape(
            slide_id, "RECTANGLE",
            x=0.8, y=0.4, w=0.15, h=0.5,
            fill_color=_MCKINSEY["teal"],
        )
        requests.extend(dash_reqs)

        # Source citation area (bottom)
        _, cite_reqs = el.create_line(
            slide_id,
            x1=0.8, y1=6.9, x2=9.2, y2=6.9,
            color=_MCKINSEY["border"], weight_pt=0.5,
        )
        requests.extend(cite_reqs)

        # Slide number (bottom-right, muted)
        _, num_reqs = el.create_text_box(
            slide_id, f"{slide_index}",
            x=9.0, y=7.0, w=0.5, h=0.3,
            font=brand.body_font, size_pt=8,
            color=_MCKINSEY["muted"],
            alignment="END",
        )
        requests.extend(num_reqs)

    return requests
