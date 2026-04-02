"""Modern Newspaper template — inspired by NotebookLM newspaper style.

Design principles:
- White/light gray background, black text
- Electric yellow (#FFCC00) accent for highlights and section markers
- Impact/bold condensed headings with high size contrast (10:1 headline ratio)
- 1 slide = 1 message — clear, bold, editorial layout
- Thin horizontal rules as section dividers
- Minimal decoration, maximum readability
"""

from __future__ import annotations

from typing import Any

from inkline.brands import BaseBrand
from inkline.slides import elements as el


# Template-specific palette (overrides brand colors for styling elements)
_NEWSPAPER = {
    "bg": "#FFFFFF",
    "accent": "#FFCC00",        # Electric yellow
    "text": "#111111",
    "muted": "#666666",
    "rule": "#111111",
    "section_bg": "#F5F5F0",    # Warm off-white
}


def template_newspaper(
    slide_id: str,
    brand: BaseBrand,
    slide_index: int,
    total_slides: int,
) -> list[dict]:
    """Apply newspaper template styling to a slide.

    Returns batchUpdate requests for base styling.
    """
    requests: list[dict] = []

    # White background
    requests.append(el.set_slide_background(slide_id, _NEWSPAPER["bg"]))

    if slide_index == 0:
        # Title slide: yellow accent bar at top
        _, bar_reqs = el.create_shape(
            slide_id, "RECTANGLE",
            x=0, y=0, w=10.0, h=0.15,
            fill_color=_NEWSPAPER["accent"],
        )
        requests.extend(bar_reqs)

        # Thin rule below title area
        _, rule_reqs = el.create_line(
            slide_id,
            x1=0.5, y1=1.8, x2=9.5, y2=1.8,
            color=_NEWSPAPER["rule"], weight_pt=2.0,
        )
        requests.extend(rule_reqs)

        # Date/edition line placeholder (thin text)
        _, date_reqs = el.create_text_box(
            slide_id, brand.display_name.upper(),
            x=0.5, y=0.25, w=9.0, h=0.3,
            font=brand.body_font, size_pt=9,
            color=_NEWSPAPER["muted"],
        )
        requests.extend(date_reqs)
    else:
        # Content slides: thin top rule + section number
        _, rule_reqs = el.create_line(
            slide_id,
            x1=0.5, y1=0.25, x2=9.5, y2=0.25,
            color=_NEWSPAPER["rule"], weight_pt=1.5,
        )
        requests.extend(rule_reqs)

        # Yellow section marker dot
        _, dot_reqs = el.create_shape(
            slide_id, "ELLIPSE",
            x=0.3, y=0.35, w=0.15, h=0.15,
            fill_color=_NEWSPAPER["accent"],
        )
        requests.extend(dot_reqs)

        # Slide number
        _, num_reqs = el.create_text_box(
            slide_id, f"{slide_index:02d}",
            x=0.5, y=0.3, w=0.5, h=0.25,
            font=brand.body_font, size_pt=9,
            color=_NEWSPAPER["muted"],
        )
        requests.extend(num_reqs)

    # Bottom rule on all slides
    _, bottom_reqs = el.create_line(
        slide_id,
        x1=0.5, y1=7.0, x2=9.5, y2=7.0,
        color=_NEWSPAPER["muted"], weight_pt=0.5,
    )
    requests.extend(bottom_reqs)

    return requests
