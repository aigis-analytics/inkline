"""Typography scale — enforced size hierarchy for professional slides.

Based on top-tier consulting and investment banking presentation standards:
- Clear hierarchy from display (44pt) down to source note (11pt)
- Consistent ratio between levels (~1.25× modular scale)
- Font weight differentiation: bold for headings, regular for body

Usage:
    from inkline.core.typography import SCALE, TypeScale
    title_size = SCALE[TypeScale.TITLE]  # 32
"""

from __future__ import annotations

from enum import Enum


class TypeScale(Enum):
    """Named type scale levels for slide elements."""
    DISPLAY = "display"      # Hero numbers, big stats (44pt)
    TITLE = "title"          # Slide title / action title (32pt)
    SUBTITLE = "subtitle"    # Slide subtitle (22pt)
    HEADING = "heading"      # Section heading within slide (18pt)
    BODY = "body"            # Body text, bullets (16pt)
    CAPTION = "caption"      # Table headers, labels (14pt)
    SMALL = "small"          # Footnotes, disclaimers (11pt)
    TINY = "tiny"            # Source notes, legal (9pt)


# Size in points for each level
SCALE: dict[TypeScale, int] = {
    TypeScale.DISPLAY:  44,
    TypeScale.TITLE:    32,
    TypeScale.SUBTITLE: 22,
    TypeScale.HEADING:  18,
    TypeScale.BODY:     16,
    TypeScale.CAPTION:  14,
    TypeScale.SMALL:    11,
    TypeScale.TINY:     9,
}

# Font weight mapping
WEIGHTS: dict[TypeScale, bool] = {
    TypeScale.DISPLAY:  True,   # bold
    TypeScale.TITLE:    True,   # bold
    TypeScale.SUBTITLE: False,  # regular
    TypeScale.HEADING:  True,   # bold
    TypeScale.BODY:     False,  # regular
    TypeScale.CAPTION:  True,   # bold (for labels)
    TypeScale.SMALL:    False,  # regular
    TypeScale.TINY:     False,  # regular
}

# Line height multiplier (relative to font size)
LINE_HEIGHTS: dict[TypeScale, float] = {
    TypeScale.DISPLAY:  1.1,
    TypeScale.TITLE:    1.2,
    TypeScale.SUBTITLE: 1.3,
    TypeScale.HEADING:  1.3,
    TypeScale.BODY:     1.5,
    TypeScale.CAPTION:  1.4,
    TypeScale.SMALL:    1.4,
    TypeScale.TINY:     1.3,
}
