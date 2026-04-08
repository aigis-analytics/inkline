"""12-column grid system for slide layout.

Standard 16:9 slide (10" × 7.5") with:
- 0.4" left/right margins
- 0.3" top margin (below header)
- 0.4" bottom margin (above footer)
- 12 columns with 0.15" gutters
- Content area: 9.2" × 6.8"

Usage:
    from inkline.core.grid import SlideGrid
    grid = SlideGrid()
    x, w = grid.col_span(1, 6)   # left half
    x, w = grid.col_span(7, 12)  # right half
    x, w = grid.col_span(1, 12)  # full width
"""

from __future__ import annotations

from dataclasses import dataclass


# Slide dimensions (16:9 standard)
SLIDE_W = 10.0   # inches
SLIDE_H = 7.5    # inches

# Margins
MARGIN_LEFT = 0.4
MARGIN_RIGHT = 0.4
MARGIN_TOP = 0.3     # below any header/logo
MARGIN_BOTTOM = 0.4  # above footer

# Content area
CONTENT_LEFT = MARGIN_LEFT
CONTENT_TOP = MARGIN_TOP
CONTENT_W = SLIDE_W - MARGIN_LEFT - MARGIN_RIGHT  # 9.2"
CONTENT_H = SLIDE_H - MARGIN_TOP - MARGIN_BOTTOM  # 6.8"

# Grid
NUM_COLUMNS = 12
GUTTER = 0.15  # inches between columns
COL_W = (CONTENT_W - (NUM_COLUMNS - 1) * GUTTER) / NUM_COLUMNS  # ~0.634"

# Spacing unit (8pt grid, in inches: 8pt = 8/72 = 0.111")
SPACING_UNIT = 8 / 72  # 0.111"


@dataclass
class Zone:
    """A rectangular content zone on the grid."""
    x: float       # inches from left edge
    y: float       # inches from top edge
    w: float       # width in inches
    h: float       # height in inches
    name: str = ""

    @property
    def right(self) -> float:
        return self.x + self.w

    @property
    def bottom(self) -> float:
        return self.y + self.h


class SlideGrid:
    """12-column grid system for consistent slide layouts.

    Column numbering is 1-based (columns 1–12).
    """

    def __init__(
        self,
        slide_w: float = SLIDE_W,
        slide_h: float = SLIDE_H,
        margin_left: float = MARGIN_LEFT,
        margin_right: float = MARGIN_RIGHT,
        margin_top: float = MARGIN_TOP,
        margin_bottom: float = MARGIN_BOTTOM,
        num_columns: int = NUM_COLUMNS,
        gutter: float = GUTTER,
    ):
        self.slide_w = slide_w
        self.slide_h = slide_h
        self.margin_left = margin_left
        self.margin_right = margin_right
        self.margin_top = margin_top
        self.margin_bottom = margin_bottom
        self.num_columns = num_columns
        self.gutter = gutter

        self.content_w = slide_w - margin_left - margin_right
        self.content_h = slide_h - margin_top - margin_bottom
        self.col_w = (self.content_w - (num_columns - 1) * gutter) / num_columns

    def col_span(self, start_col: int, end_col: int) -> tuple[float, float]:
        """Get (x, width) for a column span.

        Args:
            start_col: 1-based start column (1–12)
            end_col: 1-based end column (1–12, inclusive)

        Returns:
            (x_inches, width_inches) tuple
        """
        start_col = max(1, min(start_col, self.num_columns))
        end_col = max(start_col, min(end_col, self.num_columns))

        x = self.margin_left + (start_col - 1) * (self.col_w + self.gutter)
        n_cols = end_col - start_col + 1
        w = n_cols * self.col_w + (n_cols - 1) * self.gutter
        return (x, w)

    def row_at(self, row_fraction: float) -> float:
        """Get y position as a fraction of content height (0.0 = top, 1.0 = bottom).

        Args:
            row_fraction: 0.0 to 1.0

        Returns:
            y position in inches
        """
        return self.margin_top + row_fraction * self.content_h

    def zone(
        self,
        col_start: int,
        col_end: int,
        row_start: float,
        row_end: float,
        name: str = "",
    ) -> Zone:
        """Create a content zone from column span and row fractions.

        Args:
            col_start: 1-based start column
            col_end: 1-based end column (inclusive)
            row_start: 0.0–1.0 fraction of content height
            row_end: 0.0–1.0 fraction of content height
            name: optional zone name

        Returns:
            Zone with absolute positioning
        """
        x, w = self.col_span(col_start, col_end)
        y_start = self.row_at(row_start)
        y_end = self.row_at(row_end)
        return Zone(x=x, y=y_start, w=w, h=y_end - y_start, name=name)

    # ── Common layout presets ──────────────────────────────────────────

    def full_width(self, row_start: float = 0.15, row_end: float = 0.95) -> Zone:
        """Full-width content zone (all 12 columns)."""
        return self.zone(1, 12, row_start, row_end, "full_width")

    def left_half(self, row_start: float = 0.15, row_end: float = 0.95) -> Zone:
        """Left half (columns 1–6)."""
        return self.zone(1, 6, row_start, row_end, "left_half")

    def right_half(self, row_start: float = 0.15, row_end: float = 0.95) -> Zone:
        """Right half (columns 7–12)."""
        return self.zone(7, 12, row_start, row_end, "right_half")

    def left_third(self, row_start: float = 0.15, row_end: float = 0.95) -> Zone:
        """Left third (columns 1–4)."""
        return self.zone(1, 4, row_start, row_end, "left_third")

    def center_third(self, row_start: float = 0.15, row_end: float = 0.95) -> Zone:
        """Center third (columns 5–8)."""
        return self.zone(5, 8, row_start, row_end, "center_third")

    def right_third(self, row_start: float = 0.15, row_end: float = 0.95) -> Zone:
        """Right third (columns 9–12)."""
        return self.zone(9, 12, row_start, row_end, "right_third")

    def title_zone(self) -> Zone:
        """Standard title zone (full width, top 12%)."""
        return self.zone(1, 12, 0.0, 0.12, "title")

    def body_zone(self) -> Zone:
        """Standard body zone (full width, below title)."""
        return self.zone(1, 12, 0.14, 0.95, "body")

    def stat_cards(self, n: int = 3) -> list[Zone]:
        """N equal-width stat card zones across the slide."""
        cols_per_card = 12 // n
        zones = []
        for i in range(n):
            start = 1 + i * cols_per_card
            end = min(start + cols_per_card - 1, 12)
            zones.append(self.zone(start, end, 0.15, 0.55, f"stat_{i}"))
        return zones
