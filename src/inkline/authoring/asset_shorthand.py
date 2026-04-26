"""Inkline asset shorthand parser — ``![bg left:40%](image.png)`` syntax.

Parses the alt-text of markdown images that begin with ``bg`` and returns
a structured dict describing the layout intent.

Recognised tokens (whitespace-separated in the alt-text after ``bg``):

    bg              — switches alt-text into background-layout mode
    left[:N%]       — left side, optional width percent (default 50%)
    right[:N%]      — right side, optional width percent (default 50%)
    cover           — fill-mode: cover
    contain         — fill-mode: contain
    fit             — fill-mode: fit (alias for contain)
    w:Npx           — explicit pixel width hint
    h:Npx           — explicit pixel height hint
    blur:Npx        — blur radius in px
    brightness:N    — brightness multiplier
    vertical        — stack images vertically (for multi-bg)
"""

from __future__ import annotations

import re
from typing import NamedTuple


class AssetShorthand(NamedTuple):
    """Parsed result from a single ``![bg ...]`` image node."""
    image_path: str
    side: str           # "left", "right", "full", or ""
    width_pct: int      # 0 means not specified
    fill_mode: str      # "cover", "contain", "fit", or ""
    width_px: int       # 0 means not specified
    height_px: int      # 0 means not specified
    blur_px: int        # 0 means not specified
    brightness: float   # 0.0 means not specified
    vertical: bool


_SIDE_RE = re.compile(r"^(left|right)(?::(\d+)%)?$", re.IGNORECASE)
_DIM_RE  = re.compile(r"^([wh]):(\d+)px$", re.IGNORECASE)
_BLUR_RE = re.compile(r"^blur:(\d+)px$", re.IGNORECASE)
_BRIGHT_RE = re.compile(r"^brightness:([0-9.]+)$", re.IGNORECASE)


def parse_asset_shorthand(alt_text: str, image_path: str) -> AssetShorthand | None:
    """Parse an image alt-text for the ``bg`` shorthand.

    Returns ``None`` if the alt-text does not start with ``bg``.
    Returns an ``AssetShorthand`` otherwise.
    """
    tokens = alt_text.strip().split()
    if not tokens or tokens[0].lower() != "bg":
        return None

    side = ""
    width_pct = 0
    fill_mode = ""
    width_px = 0
    height_px = 0
    blur_px = 0
    brightness = 0.0
    vertical = False

    for token in tokens[1:]:
        tok = token.lower()

        side_m = _SIDE_RE.match(token)
        if side_m:
            side = side_m.group(1).lower()
            if side_m.group(2):
                width_pct = int(side_m.group(2))
            continue

        if tok in ("cover", "contain", "fit"):
            fill_mode = tok
            continue

        if tok == "vertical":
            vertical = True
            continue

        dim_m = _DIM_RE.match(token)
        if dim_m:
            dim, val = dim_m.group(1).lower(), int(dim_m.group(2))
            if dim == "w":
                width_px = val
            else:
                height_px = val
            continue

        blur_m = _BLUR_RE.match(token)
        if blur_m:
            blur_px = int(blur_m.group(1))
            continue

        bright_m = _BRIGHT_RE.match(token)
        if bright_m:
            brightness = float(bright_m.group(1))
            continue

    return AssetShorthand(
        image_path=image_path,
        side=side or "full",
        width_pct=width_pct,
        fill_mode=fill_mode or "cover",
        width_px=width_px,
        height_px=height_px,
        blur_px=blur_px,
        brightness=brightness,
        vertical=vertical,
    )


def infer_layout_from_assets(assets: list[AssetShorthand]) -> dict:
    """Infer a slide layout from one or more parsed ``![bg ...]`` images.

    Returns a partial section dict with ``slide_type`` and any inferred data fields.
    """
    if not assets:
        return {}

    if len(assets) == 1:
        a = assets[0]
        if a.side in ("left", "right"):
            return {
                "slide_type": "chart_caption",
                "_bg_side":   a.side,
                "_bg_width":  a.width_pct or 50,
                "image_path": a.image_path,
                "_bg_fill":   a.fill_mode,
            }
        # Full background — add as bg directive, no layout change
        return {
            "_bg": a.image_path,
        }

    # Multiple images → multi_chart
    count = len(assets)
    if count == 2:
        layout = "equal_2"
    elif count == 3:
        layout = "equal_3"
    else:
        layout = "equal_4"

    return {
        "slide_type": "multi_chart",
        "multi_layout": layout,
        "image_paths": [a.image_path for a in assets],
    }
