"""Inkline PPTX Backend — local PowerPoint generation.

Primary offline slide builder using python-pptx.
Uses the shared core layer (grid, typography, colors, charts).
"""

from inkline.pptx.builder import PptxBuilder

__all__ = ["PptxBuilder"]
