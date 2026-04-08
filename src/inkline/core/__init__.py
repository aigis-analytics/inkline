"""Inkline Core — shared layout, typography, colour, and chart systems.

Backend-agnostic: used by both PptxBuilder (local) and SlideBuilder (Google Slides).
"""

from inkline.core.grid import SlideGrid, Zone
from inkline.core.typography import TypeScale, SCALE
from inkline.core.colors import ColorScheme

__all__ = ["SlideGrid", "Zone", "TypeScale", "SCALE", "ColorScheme"]
