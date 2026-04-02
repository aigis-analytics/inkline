"""Executive / Premium template — inspired by NotebookLM executive style.

Design principles:
- White/light gray/black backgrounds with clear hierarchy
- Purple (#8D59E9) primary accent + acid yellow (#EBE021) secondary
- Clean Apple-device-mockup aesthetic
- Generous spacing, premium feel
- Title slide: dark surface with accent, content slides: white
"""

from __future__ import annotations

from typing import Any

from inkline.brands import BaseBrand
from inkline.slides import elements as el


_EXEC = {
    "title_bg": "#0D0D0D",
    "content_bg": "#FAFAFA",
    "surface": "#FFFFFF",
    "accent_primary": "#8D59E9",    # Purple
    "accent_secondary": "#EBE021",  # Acid yellow
    "text_dark": "#111111",
    "text_light": "#FFFFFF",
    "muted": "#999999",
    "border": "#E0E0E0",
}


def template_executive(
    slide_id: str,
    brand: BaseBrand,
    slide_index: int,
    total_slides: int,
) -> list[dict]:
    """Apply executive/premium template styling.

    Returns batchUpdate requests for base styling.
    """
    requests: list[dict] = []

    if slide_index == 0:
        # Title slide: dark background
        requests.append(el.set_slide_background(slide_id, _EXEC["title_bg"]))

        # Accent gradient bar (left edge)
        _, bar_reqs = el.create_shape(
            slide_id, "RECTANGLE",
            x=0, y=0, w=0.08, h=7.5,
            fill_color=_EXEC["accent_primary"],
        )
        requests.extend(bar_reqs)

        # Small accent badge (yellow dot)
        _, badge_reqs = el.create_shape(
            slide_id, "ELLIPSE",
            x=0.5, y=0.5, w=0.2, h=0.2,
            fill_color=_EXEC["accent_secondary"],
        )
        requests.extend(badge_reqs)

        # Bottom bar
        _, bottom_reqs = el.create_shape(
            slide_id, "RECTANGLE",
            x=0, y=7.2, w=10.0, h=0.3,
            fill_color=_EXEC["accent_primary"],
        )
        requests.extend(bottom_reqs)

    elif slide_index == total_slides - 1:
        # Closing slide: dark like title
        requests.append(el.set_slide_background(slide_id, _EXEC["title_bg"]))

        # Purple accent bar
        _, bar_reqs = el.create_shape(
            slide_id, "RECTANGLE",
            x=0, y=7.2, w=10.0, h=0.3,
            fill_color=_EXEC["accent_primary"],
        )
        requests.extend(bar_reqs)

    else:
        # Content slides: light background
        requests.append(el.set_slide_background(slide_id, _EXEC["content_bg"]))

        # Top accent line (thin purple)
        _, line_reqs = el.create_line(
            slide_id,
            x1=0.5, y1=0.3, x2=2.0, y2=0.3,
            color=_EXEC["accent_primary"], weight_pt=2.5,
        )
        requests.extend(line_reqs)

        # Slide number (bottom right)
        _, num_reqs = el.create_text_box(
            slide_id, f"{slide_index}",
            x=9.0, y=7.0, w=0.5, h=0.3,
            font=brand.body_font, size_pt=9,
            color=_EXEC["muted"],
            alignment="END",
        )
        requests.extend(num_reqs)

        # Subtle bottom border
        _, border_reqs = el.create_line(
            slide_id,
            x1=0.5, y1=7.1, x2=9.5, y2=7.1,
            color=_EXEC["border"], weight_pt=0.5,
        )
        requests.extend(border_reqs)

    return requests
