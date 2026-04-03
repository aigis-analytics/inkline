"""Neo-Retro Dev Deck template — inspired by NotebookLM pixel-infographic style.

Design principles:
- Light cream grid-paper background (engineering notebook feel)
- Hot pink, bright yellow, cyan color blocks with thick black borders
- Bold, heavy sans-serif headings
- Stacked modular blocks, collage-like assembly
- Pixel-art / retro-futuristic developer aesthetic
"""

from __future__ import annotations

from typing import Any

from inkline.brands import BaseBrand
from inkline.slides import elements as el


_NEO_RETRO = {
    "bg": "#FFFDF5",           # Cream / off-white
    "pink": "#FF2D78",         # Hot pink
    "yellow": "#FFD600",       # Bright yellow
    "cyan": "#00D4FF",         # Cyan / light blue
    "text": "#111111",
    "border": "#111111",       # Black borders
    "muted": "#666666",
    "grid": "#E8E4DC",         # Subtle grid lines
}


def template_neo_retro(
    slide_id: str,
    brand: BaseBrand,
    slide_index: int,
    total_slides: int,
) -> list[dict]:
    """Apply neo-retro dev deck template styling.

    Returns batchUpdate requests for base styling.
    """
    requests: list[dict] = []

    # Cream background
    requests.append(el.set_slide_background(slide_id, _NEO_RETRO["bg"]))

    # Subtle grid lines (horizontal + vertical)
    for gy in range(0, 8):
        _, line_reqs = el.create_line(
            slide_id,
            x1=0, y1=float(gy), x2=10.0, y2=float(gy),
            color=_NEO_RETRO["grid"], weight_pt=0.25,
        )
        requests.extend(line_reqs)
    for gx in range(0, 11):
        _, line_reqs = el.create_line(
            slide_id,
            x1=float(gx), y1=0, x2=float(gx), y2=7.5,
            color=_NEO_RETRO["grid"], weight_pt=0.25,
        )
        requests.extend(line_reqs)

    if slide_index == 0:
        # Title slide: large pink header block
        _, block_reqs = el.create_shape(
            slide_id, "RECTANGLE",
            x=0.5, y=1.0, w=9.0, h=2.5,
            fill_color=_NEO_RETRO["pink"],
            border_color=_NEO_RETRO["border"],
            border_weight_pt=3.0,
        )
        requests.extend(block_reqs)

        # Yellow accent block (bottom-left)
        _, accent_reqs = el.create_shape(
            slide_id, "RECTANGLE",
            x=0.5, y=4.0, w=4.0, h=1.2,
            fill_color=_NEO_RETRO["yellow"],
            border_color=_NEO_RETRO["border"],
            border_weight_pt=3.0,
        )
        requests.extend(accent_reqs)

        # Cyan accent block (bottom-right)
        _, cyan_reqs = el.create_shape(
            slide_id, "RECTANGLE",
            x=5.0, y=4.0, w=4.5, h=1.2,
            fill_color=_NEO_RETRO["cyan"],
            border_color=_NEO_RETRO["border"],
            border_weight_pt=3.0,
        )
        requests.extend(cyan_reqs)

    elif slide_index == total_slides - 1:
        # Closing slide: yellow manifesto block
        _, block_reqs = el.create_shape(
            slide_id, "RECTANGLE",
            x=1.0, y=1.5, w=8.0, h=4.5,
            fill_color=_NEO_RETRO["yellow"],
            border_color=_NEO_RETRO["border"],
            border_weight_pt=4.0,
        )
        requests.extend(block_reqs)

    else:
        # Content slides: section header bar (cycles pink/yellow/cyan)
        colors = [_NEO_RETRO["pink"], _NEO_RETRO["yellow"], _NEO_RETRO["cyan"]]
        bar_color = colors[(slide_index - 1) % 3]

        _, bar_reqs = el.create_shape(
            slide_id, "RECTANGLE",
            x=0, y=0, w=10.0, h=0.6,
            fill_color=bar_color,
            border_color=_NEO_RETRO["border"],
            border_weight_pt=2.0,
        )
        requests.extend(bar_reqs)

        # Slide number in heavy type
        _, num_reqs = el.create_text_box(
            slide_id, f"{slide_index:02d}",
            x=9.0, y=0.05, w=0.7, h=0.5,
            font=brand.body_font, size_pt=14, bold=True,
            color=_NEO_RETRO["text"],
            alignment="END",
        )
        requests.extend(num_reqs)

    # Bottom thick rule on all slides
    _, bottom_reqs = el.create_line(
        slide_id,
        x1=0, y1=7.3, x2=10.0, y2=7.3,
        color=_NEO_RETRO["border"], weight_pt=3.0,
    )
    requests.extend(bottom_reqs)

    return requests
