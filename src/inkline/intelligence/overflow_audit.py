"""Overflow audit — validates slide/exhibit sizing before and after rendering.

Used by the Archon review process to detect content that won't fit on a slide
or images that exceed the safe embed area. Returns actionable warnings so the
design advisor can re-plan slides with too much content.

Usage
-----
    from inkline.intelligence.overflow_audit import audit_deck, audit_image

    warnings = audit_deck(slides)  # list[SlideSpec]-like dicts
    for w in warnings:
        print(w)

    img_ok = audit_image("chart.png", max_width_cm=20.7, max_height_cm=8.5)
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from inkline.intelligence.layout_selector import SLIDE_CAPACITY

# Slide geometry (must stay in sync with TypstSlideRenderer constants)
SLIDE_CONTENT_WIDTH_CM = 23.0
SLIDE_BODY_HEIGHT_CM = 8.5
MAX_IMAGE_WIDTH_CM = 20.7  # 90% of content width
MAX_IMAGE_HEIGHT_CM = 8.5
IMAGE_DPI_TARGET = 200


@dataclass
class AuditWarning:
    slide_index: int
    slide_type: str
    severity: str  # "info" | "warn" | "error"
    message: str

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] slide {self.slide_index} ({self.slide_type}): {self.message}"


# Field names that carry content arrays, keyed by slide_type
_CONTENT_FIELDS: dict[str, list[str]] = {
    "content": ["items"],
    "table": ["rows"],
    "bar_chart": ["bars"],
    "three_card": ["cards"],
    "four_card": ["cards"],
    "stat": ["stats"],
    "kpi_strip": ["kpis"],
    "split": ["left_items", "right_items"],
    "timeline": ["milestones"],
    "process_flow": ["steps"],
    "icon_stat": ["stats"],
    "progress_bars": ["bars"],
    "pyramid": ["tiers"],
    "comparison": ["left.items", "right.items"],
}


def _get_nested(d: dict, dotted: str) -> Any:
    cur: Any = d
    for part in dotted.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def audit_slide(slide_index: int, slide_type: str, data: dict) -> list[AuditWarning]:
    """Audit one slide's content volume against its layout capacity."""
    warnings: list[AuditWarning] = []
    capacity = SLIDE_CAPACITY.get(slide_type, 0)

    for field in _CONTENT_FIELDS.get(slide_type, []):
        items = _get_nested(data, field)
        if not isinstance(items, list):
            continue
        if capacity and len(items) > capacity:
            warnings.append(AuditWarning(
                slide_index, slide_type, "warn",
                f"field '{field}' has {len(items)} items but slide capacity is {capacity}. "
                f"Excess items will be truncated by the renderer. Consider splitting into multiple slides.",
            ))

    # Long bullet/label strings tend to wrap and push content off slide
    for field in _CONTENT_FIELDS.get(slide_type, []):
        items = _get_nested(data, field)
        if isinstance(items, list):
            for i, item in enumerate(items):
                text = item if isinstance(item, str) else (
                    item.get("label") or item.get("title") or item.get("body") or ""
                    if isinstance(item, dict) else ""
                )
                if text and len(text) > 220:
                    warnings.append(AuditWarning(
                        slide_index, slide_type, "warn",
                        f"{field}[{i}] text is {len(text)} chars — risks wrapping beyond slide height.",
                    ))

    # Chart slides must reference an existing image
    if slide_type == "chart":
        path = data.get("image_path")
        if path and os.path.exists(path):
            warnings.extend(audit_image(path, slide_index=slide_index))
        elif path:
            warnings.append(AuditWarning(
                slide_index, "chart", "error",
                f"image_path '{path}' does not exist.",
            ))

    return warnings


def audit_image(
    path: str | Path,
    *,
    slide_index: int = -1,
    max_width_cm: float = MAX_IMAGE_WIDTH_CM,
    max_height_cm: float = MAX_IMAGE_HEIGHT_CM,
    dpi: int = IMAGE_DPI_TARGET,
) -> list[AuditWarning]:
    """Audit a PNG exhibit for size suitability as a slide embed.

    Returns warnings if the image's aspect ratio would force it to exceed the
    safe body height when scaled to slide width, or if the file is too small/large.
    """
    warnings: list[AuditWarning] = []
    try:
        from PIL import Image  # lazy import
    except ImportError:
        return warnings  # can't audit without PIL — skip silently

    try:
        with Image.open(path) as im:
            w_px, h_px = im.size
    except Exception as e:
        warnings.append(AuditWarning(
            slide_index, "chart", "error",
            f"failed to open image '{path}': {e}",
        ))
        return warnings

    # Convert px → cm at target DPI
    w_cm = w_px / dpi * 2.54
    h_cm = h_px / dpi * 2.54

    # If scaled to max_width, would it exceed max_height?
    if w_cm > 0:
        scale = max_width_cm / w_cm
        scaled_h = h_cm * scale
        if scaled_h > max_height_cm + 0.3:  # 3mm tolerance
            warnings.append(AuditWarning(
                slide_index, "chart", "warn",
                f"image {Path(path).name} is {w_px}×{h_px}px ({w_cm:.1f}×{h_cm:.1f}cm @ {dpi}dpi); "
                f"when fit to slide width it would be {scaled_h:.1f}cm tall (max {max_height_cm}cm). "
                f"Re-render with smaller matplotlib figsize (e.g. 8×4 inches) or use height constraint.",
            ))

    # Flag extreme aspect ratios that typically look bad on slides
    if h_px > 0:
        aspect = w_px / h_px
        if aspect < 1.2:
            warnings.append(AuditWarning(
                slide_index, "chart", "info",
                f"image aspect ratio {aspect:.2f} is nearly square/tall — wide-format (≥1.6) reads better on 16:9 slides.",
            ))

    return warnings


def audit_deck(slides: list[dict]) -> list[AuditWarning]:
    """Audit a full deck (list of {slide_type, data} dicts or SlideSpec-likes).

    Returns all warnings flattened across all slides.
    """
    warnings: list[AuditWarning] = []
    for i, slide in enumerate(slides):
        if hasattr(slide, "slide_type"):  # SlideSpec dataclass
            stype = slide.slide_type
            data = slide.data
        else:
            stype = slide.get("slide_type", "")
            data = slide.get("data", {})
        warnings.extend(audit_slide(i, stype, data))
    return warnings


def format_report(warnings: list[AuditWarning]) -> str:
    """Render an audit report as a printable string."""
    if not warnings:
        return "OK: no overflow issues detected."
    by_sev = {"error": 0, "warn": 0, "info": 0}
    for w in warnings:
        by_sev[w.severity] = by_sev.get(w.severity, 0) + 1
    header = (
        f"OVERFLOW AUDIT: {by_sev['error']} errors, "
        f"{by_sev['warn']} warnings, {by_sev['info']} info"
    )
    lines = [header, "-" * len(header)]
    lines.extend(str(w) for w in warnings)
    return "\n".join(lines)
