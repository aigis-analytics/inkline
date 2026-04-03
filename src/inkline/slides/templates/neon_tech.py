"""Tech / Art / Neon Constructivism template — inspired by NotebookLM avant-garde style.

Design principles:
- Warm gray/beige (#E0E0D0) matte background (paper-like)
- Neon yellow (#DFFF00) geometric accents
- Charcoal text (#333333), not pure black
- Ultra-thin architectural draft lines (0.5pt)
- Mix of serif (Didot/Bodoni) and sans-serif typography
- Monochrome imagery with neon overlays
- Blueprint / technical drawing aesthetic
"""

from __future__ import annotations

from typing import Any

from inkline.brands import BaseBrand
from inkline.slides import elements as el


_NEON_TECH = {
    "bg": "#E0E0D0",          # Warm gray / beige
    "text": "#333333",         # Charcoal (not pure black)
    "neon": "#DFFF00",         # Neon yellow
    "draft": "#C0BFB0",       # Architectural draft lines
    "muted": "#888878",
    "dark": "#1A1A1A",
}


def template_neon_tech(
    slide_id: str,
    brand: BaseBrand,
    slide_index: int,
    total_slides: int,
) -> list[dict]:
    """Apply tech/art/neon constructivism template styling.

    Returns batchUpdate requests for base styling.
    """
    requests: list[dict] = []

    # Warm gray background
    requests.append(el.set_slide_background(slide_id, _NEON_TECH["bg"]))

    # Architectural draft lines (cross pattern, all slides)
    _, h_rule = el.create_line(
        slide_id,
        x1=0.3, y1=0.4, x2=9.7, y2=0.4,
        color=_NEON_TECH["draft"], weight_pt=0.5,
    )
    requests.extend(h_rule)
    _, h_rule2 = el.create_line(
        slide_id,
        x1=0.3, y1=7.1, x2=9.7, y2=7.1,
        color=_NEON_TECH["draft"], weight_pt=0.5,
    )
    requests.extend(h_rule2)
    _, v_rule = el.create_line(
        slide_id,
        x1=0.3, y1=0.4, x2=0.3, y2=7.1,
        color=_NEON_TECH["draft"], weight_pt=0.5,
    )
    requests.extend(v_rule)
    _, v_rule2 = el.create_line(
        slide_id,
        x1=9.7, y1=0.4, x2=9.7, y2=7.1,
        color=_NEON_TECH["draft"], weight_pt=0.5,
    )
    requests.extend(v_rule2)

    if slide_index == 0:
        # Title slide: large neon yellow circle (top-right, geometric)
        _, circle_reqs = el.create_shape(
            slide_id, "ELLIPSE",
            x=6.5, y=0.5, w=3.0, h=3.0,
            fill_color=_NEON_TECH["neon"],
        )
        requests.extend(circle_reqs)

        # Small neon square (bottom-left)
        _, sq_reqs = el.create_shape(
            slide_id, "RECTANGLE",
            x=0.5, y=5.5, w=1.0, h=1.0,
            fill_color=_NEON_TECH["neon"],
        )
        requests.extend(sq_reqs)

        # Figure label (blueprint style)
        _, fig_reqs = el.create_text_box(
            slide_id, "Fig. 01",
            x=0.5, y=7.15, w=1.0, h=0.25,
            font=brand.body_font, size_pt=7,
            color=_NEON_TECH["muted"],
        )
        requests.extend(fig_reqs)

    elif slide_index == total_slides - 1:
        # Closing: neon yellow bar
        _, bar_reqs = el.create_shape(
            slide_id, "RECTANGLE",
            x=0.3, y=6.5, w=9.4, h=0.5,
            fill_color=_NEON_TECH["neon"],
        )
        requests.extend(bar_reqs)

    else:
        # Content slides: small neon accent square
        _, sq_reqs = el.create_shape(
            slide_id, "RECTANGLE",
            x=0.5, y=0.55, w=0.25, h=0.25,
            fill_color=_NEON_TECH["neon"],
        )
        requests.extend(sq_reqs)

        # Figure label
        _, fig_reqs = el.create_text_box(
            slide_id, f"Fig. {slide_index:02d}",
            x=0.5, y=7.15, w=1.0, h=0.25,
            font=brand.body_font, size_pt=7,
            color=_NEON_TECH["muted"],
        )
        requests.extend(fig_reqs)

        # Concentric target circle (top-right, decorative)
        _, ring_reqs = el.create_shape(
            slide_id, "ELLIPSE",
            x=8.5, y=0.5, w=0.8, h=0.8,
            border_color=_NEON_TECH["draft"],
            border_weight_pt=0.5,
        )
        requests.extend(ring_reqs)
        _, ring2_reqs = el.create_shape(
            slide_id, "ELLIPSE",
            x=8.65, y=0.65, w=0.5, h=0.5,
            border_color=_NEON_TECH["draft"],
            border_weight_pt=0.5,
        )
        requests.extend(ring2_reqs)

    return requests
