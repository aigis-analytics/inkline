"""Sculpture Pop / Vaporwave template — inspired by NotebookLM pop art style.

Design principles:
- High-saturation solid backgrounds that change per slide
- Classical art meets modern pop aesthetic
- Ultra-bold sans-serif headings with maximum contrast
- No muted colors — everything is bold and punchy
- Cycle through cyan, magenta, yellow, lime, purple backgrounds
- Strong contrast between bg and text (white or black)
"""

from __future__ import annotations

from typing import Any

from inkline.brands import BaseBrand
from inkline.slides import elements as el


# Rotating vivid backgrounds
_POP_COLORS = [
    "#00CED1",  # Cyan
    "#FF1493",  # Magenta
    "#FFD700",  # Yellow
    "#7FFF00",  # Lime
    "#8B5CF6",  # Purple
    "#FF6347",  # Tomato
]

_SCULPTURE_POP = {
    "text_light": "#FFFFFF",
    "text_dark": "#111111",
    "accent": "#FFD700",       # Gold accent
    "border": "#111111",
}

# Dark backgrounds need white text, light backgrounds need black text
_DARK_BGS = {"#00CED1", "#FF1493", "#8B5CF6", "#FF6347"}


def template_sculpture_pop(
    slide_id: str,
    brand: BaseBrand,
    slide_index: int,
    total_slides: int,
) -> list[dict]:
    """Apply sculpture pop / vaporwave template styling.

    Returns batchUpdate requests for base styling.
    """
    requests: list[dict] = []

    # Pick background color based on slide index
    bg_color = _POP_COLORS[slide_index % len(_POP_COLORS)]
    text_color = (
        _SCULPTURE_POP["text_light"]
        if bg_color in _DARK_BGS
        else _SCULPTURE_POP["text_dark"]
    )

    requests.append(el.set_slide_background(slide_id, bg_color))

    if slide_index == 0:
        # Title slide: large bold border frame
        _, frame_reqs = el.create_shape(
            slide_id, "RECTANGLE",
            x=0.4, y=0.4, w=9.2, h=6.7,
            border_color=text_color,
            border_weight_pt=4.0,
        )
        requests.extend(frame_reqs)

        # Inner accent rectangle
        _, inner_reqs = el.create_shape(
            slide_id, "RECTANGLE",
            x=0.6, y=0.6, w=8.8, h=6.3,
            border_color=text_color,
            border_weight_pt=1.0,
        )
        requests.extend(inner_reqs)

    elif slide_index == total_slides - 1:
        # Closing slide: centered accent circle
        _, circle_reqs = el.create_shape(
            slide_id, "ELLIPSE",
            x=3.5, y=2.0, w=3.0, h=3.0,
            border_color=text_color,
            border_weight_pt=3.0,
        )
        requests.extend(circle_reqs)

    else:
        # Content slides: bold number watermark (large, top-left)
        _, num_reqs = el.create_text_box(
            slide_id, f"{slide_index:02d}",
            x=0.3, y=0.1, w=2.0, h=1.2,
            font=brand.body_font, size_pt=48, bold=True,
            color=text_color,
        )
        requests.extend(num_reqs)

        # Thin bottom rule
        _, rule_reqs = el.create_line(
            slide_id,
            x1=0.5, y1=7.0, x2=9.5, y2=7.0,
            color=text_color, weight_pt=2.0,
        )
        requests.extend(rule_reqs)

    return requests
