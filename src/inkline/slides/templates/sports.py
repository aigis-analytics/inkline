"""Sports / Athletic / Energy template — inspired by NotebookLM sports style.

Design principles:
- Dark asphalt-black (#111111) base, white text
- Bolt lime (#CCFF00) and neon orange (#FF4500) accents
- Extra-bold italic headings, stencil-style numbers
- Skewed/diagonal shapes for speed and energy
- Angled page numbers, parallelogram accents
"""

from __future__ import annotations

from typing import Any

from inkline.brands import BaseBrand
from inkline.slides import elements as el


_SPORTS = {
    "bg": "#111111",           # Asphalt black
    "text": "#FFFFFF",
    "lime": "#CCFF00",         # Bolt lime
    "orange": "#FF4500",       # Neon orange
    "muted": "#888888",
    "surface": "#1A1A1A",      # Slightly lighter black
}


def template_sports(
    slide_id: str,
    brand: BaseBrand,
    slide_index: int,
    total_slides: int,
) -> list[dict]:
    """Apply sports/athletic template styling.

    Returns batchUpdate requests for base styling.
    """
    requests: list[dict] = []

    # Dark background
    requests.append(el.set_slide_background(slide_id, _SPORTS["bg"]))

    if slide_index == 0:
        # Title slide: lime accent stripe (top)
        _, stripe_reqs = el.create_shape(
            slide_id, "RECTANGLE",
            x=0, y=0, w=10.0, h=0.25,
            fill_color=_SPORTS["lime"],
        )
        requests.extend(stripe_reqs)

        # Large lime block (left side, speed feel)
        _, block_reqs = el.create_shape(
            slide_id, "RECTANGLE",
            x=0, y=2.5, w=0.4, h=3.0,
            fill_color=_SPORTS["lime"],
        )
        requests.extend(block_reqs)

        # Orange accent dot
        _, dot_reqs = el.create_shape(
            slide_id, "ELLIPSE",
            x=9.0, y=0.5, w=0.4, h=0.4,
            fill_color=_SPORTS["orange"],
        )
        requests.extend(dot_reqs)

        # Bottom orange stripe
        _, bottom_reqs = el.create_shape(
            slide_id, "RECTANGLE",
            x=0, y=7.25, w=10.0, h=0.25,
            fill_color=_SPORTS["orange"],
        )
        requests.extend(bottom_reqs)

    elif slide_index == total_slides - 1:
        # Closing slide: full lime top bar
        _, bar_reqs = el.create_shape(
            slide_id, "RECTANGLE",
            x=0, y=0, w=10.0, h=0.5,
            fill_color=_SPORTS["lime"],
        )
        requests.extend(bar_reqs)

        # Orange bottom bar
        _, bottom_reqs = el.create_shape(
            slide_id, "RECTANGLE",
            x=0, y=7.0, w=10.0, h=0.5,
            fill_color=_SPORTS["orange"],
        )
        requests.extend(bottom_reqs)

    else:
        # Content slides: thin lime top accent
        _, accent_reqs = el.create_line(
            slide_id,
            x1=0, y1=0.15, x2=3.0, y2=0.15,
            color=_SPORTS["lime"], weight_pt=3.0,
        )
        requests.extend(accent_reqs)

        # Orange side marker
        _, marker_reqs = el.create_shape(
            slide_id, "RECTANGLE",
            x=9.7, y=0, w=0.3, h=7.5,
            fill_color=_SPORTS["orange"],
        )
        requests.extend(marker_reqs)

        # Slide number (lime on dark)
        _, num_reqs = el.create_text_box(
            slide_id, f"{slide_index:02d}",
            x=0.3, y=6.9, w=0.8, h=0.4,
            font=brand.body_font, size_pt=14, bold=True,
            color=_SPORTS["lime"],
        )
        requests.extend(num_reqs)

    return requests
