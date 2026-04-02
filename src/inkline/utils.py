"""Shared utilities — base64 encoding, color helpers, unit conversion."""

from __future__ import annotations

import base64
from pathlib import Path

# EMU (English Metric Units) — used by Google Slides API
EMU_PER_INCH = 914400
EMU_PER_PT = 12700


def inches_to_emu(inches: float) -> int:
    return int(inches * EMU_PER_INCH)


def pt_to_emu(pt: float) -> int:
    return int(pt * EMU_PER_PT)


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert '#1B283B' to (27, 40, 59)."""
    h = hex_color.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def hex_to_rgba_str(hex_color: str, alpha: float = 0.85) -> str:
    """Convert hex to 'rgba(r, g, b, a)' for Chart.js."""
    r, g, b = hex_to_rgb(hex_color)
    return f"rgba({r}, {g}, {b}, {alpha})"


def b64_encode_file(path: Path) -> str:
    """Return base64-encoded file contents, or empty string if not found."""
    if not path or not path.is_file():
        return ""
    return base64.b64encode(path.read_bytes()).decode()


def b64_data_uri(path: Path, mime: str = "image/png") -> str:
    """Return a data:URI for embedding, or empty string if not found."""
    encoded = b64_encode_file(path)
    if not encoded:
        return ""
    return f"data:{mime};base64,{encoded}"


def luminance(hex_color: str) -> float:
    """Relative luminance (0-1) for choosing light/dark logo variant."""
    r, g, b = hex_to_rgb(hex_color)
    # sRGB relative luminance
    def c(v: int) -> float:
        s = v / 255.0
        return s / 12.92 if s <= 0.03928 else ((s + 0.055) / 1.055) ** 2.4
    return 0.2126 * c(r) + 0.7152 * c(g) + 0.0722 * c(b)
