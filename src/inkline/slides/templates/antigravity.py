"""Anti-Gravity / Living Artifact template — inspired by NotebookLM calm premium style.

Design principles:
- Pure white background, maximum negative space
- Calm blue accent used sparingly
- Clean modern sans-serif, medium-bold, calm authority
- Wide margins, airy layout, no visual noise
- Apple-level clarity, DeepMind research aesthetic
- No textures, grids, or hard shapes
"""

from __future__ import annotations

from typing import Any

from inkline.brands import BaseBrand
from inkline.slides import elements as el


_ANTIGRAVITY = {
    "bg": "#FFFFFF",
    "text": "#1A1A1A",         # Near-black
    "accent": "#3B82F6",       # Calm blue
    "accent_light": "#DBEAFE", # Pale blue
    "muted": "#9CA3AF",
    "border": "#E5E7EB",       # Barely visible
}


def template_antigravity(
    slide_id: str,
    brand: BaseBrand,
    slide_index: int,
    total_slides: int,
) -> list[dict]:
    """Apply anti-gravity / living artifact template styling.

    Returns batchUpdate requests for base styling.
    """
    requests: list[dict] = []

    # Pure white background
    requests.append(el.set_slide_background(slide_id, _ANTIGRAVITY["bg"]))

    if slide_index == 0:
        # Title slide: subtle blue accent line (short, left-aligned)
        _, accent_reqs = el.create_line(
            slide_id,
            x1=0.8, y1=2.0, x2=2.5, y2=2.0,
            color=_ANTIGRAVITY["accent"], weight_pt=2.5,
        )
        requests.extend(accent_reqs)

        # Pale blue circle (decorative, top-right corner — subtle gradient feel)
        _, circle_reqs = el.create_shape(
            slide_id, "ELLIPSE",
            x=7.5, y=-0.5, w=3.5, h=3.5,
            fill_color=_ANTIGRAVITY["accent_light"],
        )
        requests.extend(circle_reqs)

    elif slide_index == total_slides - 1:
        # Closing slide: centered blue accent dot
        _, dot_reqs = el.create_shape(
            slide_id, "ELLIPSE",
            x=4.75, y=6.5, w=0.5, h=0.5,
            fill_color=_ANTIGRAVITY["accent"],
        )
        requests.extend(dot_reqs)

    else:
        # Content slides: very subtle top separator
        _, sep_reqs = el.create_line(
            slide_id,
            x1=0.8, y1=0.5, x2=1.8, y2=0.5,
            color=_ANTIGRAVITY["accent"], weight_pt=1.5,
        )
        requests.extend(sep_reqs)

        # Slide number (ultra-light, bottom-right)
        _, num_reqs = el.create_text_box(
            slide_id, f"{slide_index}",
            x=9.0, y=7.0, w=0.5, h=0.3,
            font=brand.body_font, size_pt=8,
            color=_ANTIGRAVITY["muted"],
            alignment="END",
        )
        requests.extend(num_reqs)

    return requests
