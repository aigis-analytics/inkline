"""Inkline freeform layout — parse and validate positioned-shapes manifests.

A ``freeform`` slide accepts a ``_shapes_file:`` directive pointing to a JSON file
containing a list of positioned shapes. This covers bespoke hero exhibits that don't
fit any of the 22 typed layouts.

Schema::

    {
      "shapes": [
        {"type": "image",        "x": 0, "y": 0, "w": 100, "h": 100, "path": "assets/img.png", "units": "pct"},
        {"type": "rounded_rect", "x": 5, "y": 80, "w": 90, "h": 8, "fill": "#1A2B4A", "radius": 0.5, "units": "pct"},
        {"type": "rect",         "x": 5, "y": 5, "w": 30, "h": 20, "fill": "#FFFFFF", "units": "pct"},
        {"type": "text",         "x": 50, "y": 84, "w": 90, "h": 4, "text": "...", "font": "Calibri", "size": 14, "color": "#FFFFFF", "anchor": "mc", "units": "pct"},
        {"type": "line",         "x1": 10, "y1": 50, "x2": 90, "y2": 50, "color": "#AABBCC", "thickness": 1, "units": "pct"},
        {"type": "arrow",        "x1": 10, "y1": 50, "x2": 90, "y2": 50, "color": "#AABBCC", "thickness": 1, "units": "pct"},
        {"type": "circle",       "cx": 50, "cy": 50, "r": 10, "fill": "#FF0000", "units": "pct"},
        {"type": "polygon",      "points": [[10,10],[90,10],[50,90]], "fill": "#00FF00", "units": "pct"}
      ]
    }

All shapes use ``units: pct`` by default (0–100 percentage of slide width/height).
Absolute pixel units can be specified with ``units: px``.

Usage::

    from inkline.authoring.freeform import parse_shapes_manifest

    manifest = parse_shapes_manifest(path="/path/to/shapes.json", base_dir="/deck/dir")
    # Returns list[ShapeSpec]
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

VALID_SHAPE_TYPES = frozenset({
    "image", "rounded_rect", "rect", "text", "line", "arrow", "circle", "polygon"
})

# Slide dimensions for pct → px conversion
SLIDE_W_PX = 1280
SLIDE_H_PX = 720


class FreeformError(ValueError):
    """Raised when a freeform shapes manifest fails validation."""


@dataclass
class ShapeSpec:
    """A single positioned shape in a freeform slide."""
    type: str                             # one of VALID_SHAPE_TYPES
    units: str = "pct"                    # pct | px
    # Bounding box (for image, rect, rounded_rect, text, circle via bounding box)
    x: float = 0.0
    y: float = 0.0
    w: float = 0.0
    h: float = 0.0
    # Line/arrow endpoints
    x1: float | None = None
    y1: float | None = None
    x2: float | None = None
    y2: float | None = None
    # Polygon points
    points: list[list[float]] = field(default_factory=list)
    # Circle centre + radius
    cx: float | None = None
    cy: float | None = None
    r: float | None = None
    # Style
    fill: str = "#FFFFFF"
    color: str = "#000000"
    radius: float = 0.0           # corner radius for rounded_rect (0–1 scale)
    thickness: float = 1.0        # line thickness in pt
    # Text-specific
    text: str = ""
    font: str = "Inter"
    size: float = 14.0            # pt
    anchor: str = "ml"            # ml | mc | mr | tl | tc | tr | bl | bc | br
    # Image-specific
    path: str = ""                # resolved relative to base_dir
    fit: str = "cover"            # cover | contain | stretch
    # Opacity
    opacity: float = 1.0
    # Raw dict for passthrough fields
    raw: dict = field(default_factory=dict)


def parse_shapes_manifest(
    path: str | Path,
    base_dir: str | Path | None = None,
) -> list[ShapeSpec]:
    """Load and validate a shapes manifest JSON file.

    Parameters
    ----------
    path : str | Path
        Path to the shapes JSON file.
    base_dir : str | Path | None
        Directory for resolving relative image paths inside the manifest.

    Returns
    -------
    list[ShapeSpec]
        Validated list of shapes.

    Raises
    ------
    FreeformError
        If the file is missing, malformed, or contains invalid shape types.
    FileNotFoundError
        If the shapes file itself does not exist.
    """
    shapes_path = Path(path)
    if base_dir and not shapes_path.is_absolute():
        shapes_path = Path(base_dir) / shapes_path

    if not shapes_path.exists():
        raise FileNotFoundError(
            f"freeform _shapes_file not found: {shapes_path}"
        )

    try:
        raw = json.loads(shapes_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise FreeformError(
            f"freeform shapes file is not valid JSON: {shapes_path}\n  {exc}"
        ) from exc

    if not isinstance(raw, dict):
        raise FreeformError(
            f"freeform shapes file must be a JSON object with a 'shapes' key"
        )

    shapes_list = raw.get("shapes")
    if shapes_list is None:
        raise FreeformError(
            f"freeform shapes file missing 'shapes' array: {shapes_path}"
        )
    if not isinstance(shapes_list, list):
        raise FreeformError(
            f"freeform 'shapes' must be a list, got {type(shapes_list).__name__}"
        )

    base = Path(base_dir) if base_dir else shapes_path.parent
    result: list[ShapeSpec] = []
    for i, raw_shape in enumerate(shapes_list):
        try:
            shape = _validate_shape(raw_shape, index=i, base=base)
            result.append(shape)
        except (FreeformError, FileNotFoundError):
            raise
        except Exception as exc:
            raise FreeformError(
                f"freeform shape[{i}] validation error: {exc}"
            ) from exc

    return result


def _validate_shape(raw: dict, index: int, base: Path) -> ShapeSpec:
    """Validate a single shape dict and return a ShapeSpec."""
    if not isinstance(raw, dict):
        raise FreeformError(
            f"freeform shape[{index}] must be a dict, got {type(raw).__name__}"
        )

    shape_type = raw.get("type")
    if shape_type not in VALID_SHAPE_TYPES:
        raise FreeformError(
            f"freeform shape[{index}]: unknown type {shape_type!r}. "
            f"Valid types: {sorted(VALID_SHAPE_TYPES)}"
        )

    units = raw.get("units", "pct")
    if units not in ("pct", "px"):
        raise FreeformError(
            f"freeform shape[{index}]: units must be 'pct' or 'px', got {units!r}"
        )

    spec = ShapeSpec(
        type=shape_type,
        units=units,
        x=float(raw.get("x", 0)),
        y=float(raw.get("y", 0)),
        w=float(raw.get("w", 0)),
        h=float(raw.get("h", 0)),
        x1=float(raw["x1"]) if "x1" in raw else None,
        y1=float(raw["y1"]) if "y1" in raw else None,
        x2=float(raw["x2"]) if "x2" in raw else None,
        y2=float(raw["y2"]) if "y2" in raw else None,
        cx=float(raw["cx"]) if "cx" in raw else None,
        cy=float(raw["cy"]) if "cy" in raw else None,
        r=float(raw["r"]) if "r" in raw else None,
        points=raw.get("points", []),
        fill=raw.get("fill", "#FFFFFF"),
        color=raw.get("color", "#000000"),
        radius=float(raw.get("radius", 0.0)),
        thickness=float(raw.get("thickness", 1.0)),
        text=raw.get("text", ""),
        font=raw.get("font", "Inter"),
        size=float(raw.get("size", 14.0)),
        anchor=raw.get("anchor", "ml"),
        path=raw.get("path", ""),
        fit=raw.get("fit", "cover"),
        opacity=float(raw.get("opacity", 1.0)),
        raw=raw,
    )

    # Validate image path at parse time
    if shape_type == "image" and spec.path:
        img_path = Path(spec.path)
        if not img_path.is_absolute():
            img_path = base / img_path
        if not img_path.exists():
            raise FileNotFoundError(
                f"freeform shape[{index}] image path not found: {img_path}"
            )

    # Validate polygon points
    if shape_type == "polygon" and not spec.points:
        raise FreeformError(
            f"freeform shape[{index}] polygon must have 'points'"
        )

    return spec


def pct_to_px(value: float, dimension: str) -> float:
    """Convert a percentage value to pixels for the standard slide canvas.

    Parameters
    ----------
    value : float
        Percentage value (0–100).
    dimension : str
        'w' or 'x' for horizontal; 'h' or 'y' for vertical.

    Returns
    -------
    float
        Pixel value.
    """
    if dimension in ("w", "x", "x1", "x2", "cx"):
        return value / 100.0 * SLIDE_W_PX
    return value / 100.0 * SLIDE_H_PX


def shapes_to_px(shapes: list[ShapeSpec]) -> list[ShapeSpec]:
    """Return a copy of shapes with all pct units converted to px units.

    This is useful for renderers that work only in absolute pixel space.
    """
    result = []
    for s in shapes:
        if s.units == "px":
            result.append(s)
            continue

        # Convert bounding box
        new = ShapeSpec(
            type=s.type,
            units="px",
            x=pct_to_px(s.x, "x"),
            y=pct_to_px(s.y, "y"),
            w=pct_to_px(s.w, "w"),
            h=pct_to_px(s.h, "h"),
            x1=pct_to_px(s.x1, "x1") if s.x1 is not None else None,
            y1=pct_to_px(s.y1, "y1") if s.y1 is not None else None,
            x2=pct_to_px(s.x2, "x2") if s.x2 is not None else None,
            y2=pct_to_px(s.y2, "y2") if s.y2 is not None else None,
            cx=pct_to_px(s.cx, "cx") if s.cx is not None else None,
            cy=pct_to_px(s.cy, "cy") if s.cy is not None else None,
            r=pct_to_px(s.r, "w") if s.r is not None else None,
            points=[[pct_to_px(p[0], "x"), pct_to_px(p[1], "y")] for p in s.points],
            fill=s.fill,
            color=s.color,
            radius=s.radius,
            thickness=s.thickness,
            text=s.text,
            font=s.font,
            size=s.size,
            anchor=s.anchor,
            path=s.path,
            fit=s.fit,
            opacity=s.opacity,
            raw=s.raw,
        )
        result.append(new)
    return result
