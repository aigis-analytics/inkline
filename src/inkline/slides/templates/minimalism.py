"""Sharp-Edged Minimalism template — inspired by NotebookLM minimalist style.

Design principles:
- Light gray (#E9E9E9) background, black text
- No rounded corners — sharp edges everywhere
- Helvetica/Inter typography, minimal font sizes
- Grid-based layout with generous whitespace
- Section navigation: subtle numbered markers
- 17 layout sub-types in the original — we implement the core patterns
"""

from __future__ import annotations

from typing import Any

from inkline.brands import BaseBrand
from inkline.slides import elements as el


_MINIMAL = {
    "bg": "#E9E9E9",
    "surface": "#FFFFFF",
    "text": "#111111",
    "muted": "#888888",
    "accent": "#333333",
    "border": "#CCCCCC",
}


def template_minimalism(
    slide_id: str,
    brand: BaseBrand,
    slide_index: int,
    total_slides: int,
) -> list[dict]:
    """Apply sharp-edged minimalism template styling.

    Returns batchUpdate requests for base styling.
    """
    requests: list[dict] = []

    # Light gray background
    requests.append(el.set_slide_background(slide_id, _MINIMAL["bg"]))

    if slide_index == 0:
        # Title slide: white content card
        _, card_reqs = el.create_shape(
            slide_id, "RECTANGLE",
            x=0.5, y=0.5, w=9.0, h=6.5,
            fill_color=_MINIMAL["surface"],
            border_color=_MINIMAL["border"],
            border_weight_pt=0.5,
        )
        requests.extend(card_reqs)

        # Navigation dots at bottom
        for i in range(min(total_slides, 10)):
            dot_color = _MINIMAL["accent"] if i == 0 else _MINIMAL["border"]
            _, dot_reqs = el.create_shape(
                slide_id, "ELLIPSE",
                x=4.0 + i * 0.25, y=6.7, w=0.1, h=0.1,
                fill_color=dot_color,
            )
            requests.extend(dot_reqs)
    else:
        # Content slides: white content area with thin border
        _, card_reqs = el.create_shape(
            slide_id, "RECTANGLE",
            x=0.5, y=0.8, w=9.0, h=6.0,
            fill_color=_MINIMAL["surface"],
            border_color=_MINIMAL["border"],
            border_weight_pt=0.5,
        )
        requests.extend(card_reqs)

        # Section number (top-left, small)
        _, num_reqs = el.create_text_box(
            slide_id, f"{slide_index:02d} / {total_slides:02d}",
            x=0.6, y=0.35, w=1.5, h=0.3,
            font=brand.body_font, size_pt=8,
            color=_MINIMAL["muted"],
        )
        requests.extend(num_reqs)

        # Navigation dots
        for i in range(min(total_slides, 10)):
            dot_color = _MINIMAL["accent"] if i == slide_index else _MINIMAL["border"]
            _, dot_reqs = el.create_shape(
                slide_id, "ELLIPSE",
                x=4.0 + i * 0.25, y=7.1, w=0.08, h=0.08,
                fill_color=dot_color,
            )
            requests.extend(dot_reqs)

    return requests
