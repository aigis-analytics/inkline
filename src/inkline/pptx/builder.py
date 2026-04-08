"""PptxBuilder — local PPTX slide generation with grid, typography, and charts.

Replaces AigisDeck with a brand-aware, grid-based builder that produces
consulting-quality slides locally without Google Slides API.

Usage:
    from inkline.pptx import PptxBuilder

    deck = PptxBuilder(title="Aigis Analytics", brand="aigis")
    deck.add_title_slide("Aigis Analytics", "AI-Powered Due Diligence", "April 2026")
    deck.add_stat_slide("The Problem", [("$200K+", "Advisory fees", "Per transaction")])
    deck.add_chart_slide("Revenue Growth", chart_path="chart.png")
    deck.save("output.pptx")
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

from inkline.core.grid import SlideGrid, Zone
from inkline.core.typography import TypeScale, SCALE, WEIGHTS
from inkline.core.colors import ColorScheme, hex_to_rgb

log = logging.getLogger(__name__)

# Slide dimensions
SLIDE_WIDTH = Inches(10)
SLIDE_HEIGHT = Inches(7.5)


class PptxBuilder:
    """Grid-based PPTX slide builder with brand theming.

    Key improvements over AigisDeck:
    - 12-column grid layout system
    - Enforced typography scale
    - Chart image embedding
    - 60-30-10 colour application
    - Action title support
    """

    def __init__(
        self,
        title: str = "Untitled",
        brand: str = "aigis",
        subtitle: str = "",
    ):
        self.title = title
        self.brand_name = brand
        self.subtitle = subtitle

        # Initialize presentation
        self._prs = Presentation()
        self._prs.slide_width = SLIDE_WIDTH
        self._prs.slide_height = SLIDE_HEIGHT

        # Grid and colour scheme
        self.grid = SlideGrid()
        self.colors = self._resolve_colors(brand)

        # Logo path
        self._logo_path = self._find_logo(brand)

        # Slide count
        self._slide_count = 0

    def _resolve_colors(self, brand: str) -> ColorScheme:
        """Get colour scheme for brand."""
        if brand == "aigis":
            return ColorScheme.aigis_light()
        elif brand == "aigis_dark":
            return ColorScheme.aigis_dark()
        else:
            return ColorScheme.aigis_light()  # default

    def _find_logo(self, brand: str) -> Path | None:
        """Find logo file for brand."""
        candidates = [
            Path(__file__).resolve().parent.parent / "assets" / f"{brand}_logo_light.png",
            Path(__file__).resolve().parent.parent / "assets" / f"{brand}_logo_dark.png",
        ]
        for p in candidates:
            if p.exists():
                return p
        return None

    def _add_slide(self) -> Any:
        """Add a blank slide."""
        layout = self._prs.slide_layouts[6]  # blank layout
        slide = self._prs.slides.add_slide(layout)
        self._slide_count += 1
        return slide

    def _set_bg(self, slide: Any, color: str) -> None:
        """Set solid background colour."""
        bg = slide.background
        fill = bg.fill
        fill.solid()
        r, g, b = hex_to_rgb(color)
        fill.fore_color.rgb = RGBColor(r, g, b)

    def _add_text(
        self,
        slide: Any,
        text: str,
        zone: Zone,
        scale: TypeScale = TypeScale.BODY,
        color: str | None = None,
        alignment: int = PP_ALIGN.LEFT,
        bold: bool | None = None,
    ) -> Any:
        """Add a text box at the specified zone with typography scale."""
        txBox = slide.shapes.add_textbox(
            Inches(zone.x), Inches(zone.y), Inches(zone.w), Inches(zone.h)
        )
        tf = txBox.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = text
        p.font.size = Pt(SCALE[scale])
        p.font.bold = bold if bold is not None else WEIGHTS[scale]
        p.alignment = alignment

        r, g, b = hex_to_rgb(color or self.colors.text)
        p.font.color.rgb = RGBColor(r, g, b)

        return txBox

    def _add_shape(
        self,
        slide: Any,
        zone: Zone,
        fill_color: str,
    ) -> Any:
        """Add a filled rectangle shape."""
        from pptx.enum.shapes import MSO_SHAPE
        shape = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            Inches(zone.x), Inches(zone.y), Inches(zone.w), Inches(zone.h),
        )
        shape.fill.solid()
        r, g, b = hex_to_rgb(fill_color)
        shape.fill.fore_color.rgb = RGBColor(r, g, b)
        shape.line.fill.background()
        return shape

    def _add_logo(self, slide: Any, x: float = 0.4, y: float = 0.2, height: float = 0.4) -> None:
        """Add logo to slide if available."""
        if self._logo_path and self._logo_path.exists():
            slide.shapes.add_picture(
                str(self._logo_path),
                Inches(x), Inches(y),
                height=Inches(height),
            )

    def _add_divider(self, slide: Any, y: float, color: str | None = None) -> None:
        """Add a thin horizontal divider line."""
        from pptx.enum.shapes import MSO_SHAPE
        line = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            Inches(self.grid.margin_left), Inches(y),
            Inches(self.grid.content_w), Inches(0.02),
        )
        line.fill.solid()
        r, g, b = hex_to_rgb(color or self.colors.accent)
        line.fill.fore_color.rgb = RGBColor(r, g, b)
        line.line.fill.background()

    # ── Slide types ──────────────────────────────────────────────────

    def add_title_slide(self, title: str, subtitle: str, date: str = "") -> None:
        """Dark background title slide with accent stripe."""
        slide = self._add_slide()
        self._set_bg(slide, self.colors.secondary)

        # Accent stripe at top
        self._add_shape(slide, Zone(0, 0, 10, 0.08), self.colors.accent)

        # Logo (use dark bg version)
        self._add_logo(slide, x=0.4, y=0.5, height=0.6)

        # Title
        self._add_text(slide, title,
                       self.grid.zone(1, 12, 0.25, 0.50),
                       TypeScale.DISPLAY, self.colors.secondary_text, PP_ALIGN.LEFT)

        # Subtitle
        self._add_text(slide, subtitle,
                       self.grid.zone(1, 12, 0.50, 0.65),
                       TypeScale.SUBTITLE, self.colors.muted, PP_ALIGN.LEFT)

        # Date/stage
        if date:
            self._add_text(slide, date,
                           self.grid.zone(1, 12, 0.80, 0.90),
                           TypeScale.CAPTION, self.colors.muted, PP_ALIGN.LEFT)

    def add_section_header(self, title: str, subtitle: str = "") -> None:
        """Section divider slide (dark background)."""
        slide = self._add_slide()
        self._set_bg(slide, self.colors.secondary)

        self._add_text(slide, title,
                       self.grid.zone(1, 12, 0.30, 0.50),
                       TypeScale.DISPLAY, self.colors.secondary_text, PP_ALIGN.CENTER)
        if subtitle:
            self._add_text(slide, subtitle,
                           self.grid.zone(1, 12, 0.55, 0.65),
                           TypeScale.BODY, self.colors.muted, PP_ALIGN.CENTER)

    def add_content_slide(
        self,
        title: str,
        body_items: list[str],
        subtitle: str = "",
        accent_stat: str = "",
        accent_label: str = "",
    ) -> None:
        """Standard content slide with title, bullets, and optional accent stat."""
        slide = self._add_slide()
        self._set_bg(slide, self.colors.background)
        self._add_logo(slide, x=8.8, y=0.15, height=0.3)

        # Title (action title style)
        self._add_text(slide, title, self.grid.title_zone(),
                       TypeScale.TITLE, self.colors.text)

        self._add_divider(slide, 0.95)

        # Subtitle
        if subtitle:
            self._add_text(slide, subtitle,
                           self.grid.zone(1, 12, 0.14, 0.20),
                           TypeScale.CAPTION, self.colors.muted, bold=False)

        # Body bullets
        body_zone = self.grid.zone(1, 8 if accent_stat else 12, 0.22, 0.90)
        txBox = slide.shapes.add_textbox(
            Inches(body_zone.x), Inches(body_zone.y),
            Inches(body_zone.w), Inches(body_zone.h),
        )
        tf = txBox.text_frame
        tf.word_wrap = True

        for i, item in enumerate(body_items):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.text = f"• {item}"
            p.font.size = Pt(SCALE[TypeScale.BODY])
            p.font.color.rgb = RGBColor(*hex_to_rgb(self.colors.text))
            p.space_after = Pt(8)

        # Accent stat card (right side)
        if accent_stat:
            card_zone = self.grid.zone(9, 12, 0.25, 0.55)
            self._add_shape(slide, card_zone, self.colors.surface)
            self._add_text(slide, accent_stat,
                           Zone(card_zone.x + 0.2, card_zone.y + 0.3, card_zone.w - 0.4, 0.8),
                           TypeScale.DISPLAY, self.colors.accent, PP_ALIGN.CENTER)
            if accent_label:
                self._add_text(slide, accent_label,
                               Zone(card_zone.x + 0.2, card_zone.y + 1.2, card_zone.w - 0.4, 0.5),
                               TypeScale.CAPTION, self.colors.muted, PP_ALIGN.CENTER, bold=False)

    def add_stat_slide(self, title: str, stats: list[tuple[str, str, str]]) -> None:
        """Big stat cards slide (up to 4 stats)."""
        slide = self._add_slide()
        self._set_bg(slide, self.colors.background)
        self._add_logo(slide, x=8.8, y=0.15, height=0.3)

        self._add_text(slide, title, self.grid.title_zone(),
                       TypeScale.TITLE, self.colors.text)
        self._add_divider(slide, 0.95)

        card_zones = self.grid.stat_cards(len(stats))
        for i, (value, label, description) in enumerate(stats):
            z = card_zones[i] if i < len(card_zones) else card_zones[-1]

            # Card background
            self._add_shape(slide, z, self.colors.surface)

            # Big number
            self._add_text(slide, value,
                           Zone(z.x + 0.2, z.y + 0.3, z.w - 0.4, 0.8),
                           TypeScale.DISPLAY, self.colors.accent, PP_ALIGN.CENTER)

            # Label
            self._add_text(slide, label,
                           Zone(z.x + 0.2, z.y + 1.3, z.w - 0.4, 0.4),
                           TypeScale.HEADING, self.colors.text, PP_ALIGN.CENTER)

            # Description
            self._add_text(slide, description,
                           Zone(z.x + 0.2, z.y + 1.8, z.w - 0.4, 0.5),
                           TypeScale.SMALL, self.colors.muted, PP_ALIGN.CENTER, bold=False)

    def add_table_slide(
        self,
        title: str,
        headers: list[str],
        rows: list[list[str]],
        subtitle: str = "",
    ) -> None:
        """Table slide with branded header row."""
        slide = self._add_slide()
        self._set_bg(slide, self.colors.background)
        self._add_logo(slide, x=8.8, y=0.15, height=0.3)

        self._add_text(slide, title, self.grid.title_zone(),
                       TypeScale.TITLE, self.colors.text)
        self._add_divider(slide, 0.95)

        if subtitle:
            self._add_text(slide, subtitle,
                           self.grid.zone(1, 12, 0.14, 0.20),
                           TypeScale.CAPTION, self.colors.muted, bold=False)

        # Table
        table_zone = self.grid.zone(1, 12, 0.22 if subtitle else 0.16, 0.92)
        n_rows = len(rows) + 1  # +1 for header
        n_cols = len(headers)

        table_shape = slide.shapes.add_table(
            n_rows, n_cols,
            Inches(table_zone.x), Inches(table_zone.y),
            Inches(table_zone.w), Inches(table_zone.h),
        )
        table = table_shape.table

        # Header row
        for j, header in enumerate(headers):
            cell = table.cell(0, j)
            cell.text = header
            cell.fill.solid()
            r, g, b = hex_to_rgb(self.colors.secondary)
            cell.fill.fore_color.rgb = RGBColor(r, g, b)
            for paragraph in cell.text_frame.paragraphs:
                paragraph.font.size = Pt(SCALE[TypeScale.CAPTION])
                paragraph.font.bold = True
                paragraph.font.color.rgb = RGBColor(255, 255, 255)

        # Data rows
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                cell = table.cell(i + 1, j)
                cell.text = str(val)

                # Alternating row fill
                if i % 2 == 1:
                    cell.fill.solid()
                    r, g, b = hex_to_rgb(self.colors.surface)
                    cell.fill.fore_color.rgb = RGBColor(r, g, b)

                for paragraph in cell.text_frame.paragraphs:
                    paragraph.font.size = Pt(SCALE[TypeScale.BODY] - 2)
                    paragraph.font.color.rgb = RGBColor(*hex_to_rgb(self.colors.text))

    def add_chart_slide(
        self,
        title: str,
        chart_path: str | Path,
        subtitle: str = "",
        caption: str = "",
    ) -> None:
        """Slide with an embedded chart image."""
        slide = self._add_slide()
        self._set_bg(slide, self.colors.background)
        self._add_logo(slide, x=8.8, y=0.15, height=0.3)

        self._add_text(slide, title, self.grid.title_zone(),
                       TypeScale.TITLE, self.colors.text)
        self._add_divider(slide, 0.95)

        if subtitle:
            self._add_text(slide, subtitle,
                           self.grid.zone(1, 12, 0.14, 0.20),
                           TypeScale.CAPTION, self.colors.muted, bold=False)

        # Chart image
        chart_zone = self.grid.zone(1, 12, 0.22, 0.88)
        chart_path = Path(chart_path)
        if chart_path.exists():
            slide.shapes.add_picture(
                str(chart_path),
                Inches(chart_zone.x), Inches(chart_zone.y),
                width=Inches(chart_zone.w),
            )

        if caption:
            self._add_text(slide, caption,
                           self.grid.zone(1, 12, 0.92, 0.98),
                           TypeScale.TINY, self.colors.muted, bold=False)

    def add_two_column_slide(
        self,
        title: str,
        left_items: list[str],
        right_items: list[str],
        left_title: str = "",
        right_title: str = "",
    ) -> None:
        """Two-column comparison slide."""
        slide = self._add_slide()
        self._set_bg(slide, self.colors.background)
        self._add_logo(slide, x=8.8, y=0.15, height=0.3)

        self._add_text(slide, title, self.grid.title_zone(),
                       TypeScale.TITLE, self.colors.text)
        self._add_divider(slide, 0.95)

        # Left column
        left_zone = self.grid.left_half(0.16, 0.92)
        if left_title:
            self._add_text(slide, left_title,
                           Zone(left_zone.x, left_zone.y, left_zone.w, 0.4),
                           TypeScale.HEADING, self.colors.accent)

        txBox = slide.shapes.add_textbox(
            Inches(left_zone.x), Inches(left_zone.y + (0.5 if left_title else 0)),
            Inches(left_zone.w), Inches(left_zone.h - (0.5 if left_title else 0)),
        )
        tf = txBox.text_frame
        tf.word_wrap = True
        for i, item in enumerate(left_items):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.text = f"• {item}"
            p.font.size = Pt(SCALE[TypeScale.BODY])
            p.font.color.rgb = RGBColor(*hex_to_rgb(self.colors.text))
            p.space_after = Pt(6)

        # Right column
        right_zone = self.grid.right_half(0.16, 0.92)
        if right_title:
            self._add_text(slide, right_title,
                           Zone(right_zone.x, right_zone.y, right_zone.w, 0.4),
                           TypeScale.HEADING, self.colors.accent)

        txBox2 = slide.shapes.add_textbox(
            Inches(right_zone.x), Inches(right_zone.y + (0.5 if right_title else 0)),
            Inches(right_zone.w), Inches(right_zone.h - (0.5 if right_title else 0)),
        )
        tf2 = txBox2.text_frame
        tf2.word_wrap = True
        for i, item in enumerate(right_items):
            p = tf2.paragraphs[0] if i == 0 else tf2.add_paragraph()
            p.text = f"• {item}"
            p.font.size = Pt(SCALE[TypeScale.BODY])
            p.font.color.rgb = RGBColor(*hex_to_rgb(self.colors.text))
            p.space_after = Pt(6)

    def add_closing_slide(self, items: list[str], tagline: str = "") -> None:
        """Dark closing slide with contact info."""
        slide = self._add_slide()
        self._set_bg(slide, self.colors.secondary)

        # Accent stripe
        self._add_shape(slide, Zone(0, 7.42, 10, 0.08), self.colors.accent)

        # Logo
        self._add_logo(slide, x=3.5, y=0.8, height=0.8)

        # Contact items
        y_start = 0.35
        for i, item in enumerate(items):
            if item:
                self._add_text(slide, item,
                               self.grid.zone(1, 12, y_start + i * 0.06, y_start + (i + 1) * 0.06),
                               TypeScale.BODY if i < 2 else TypeScale.CAPTION,
                               self.colors.secondary_text, PP_ALIGN.CENTER,
                               bold=(i == 0))

        if tagline:
            self._add_text(slide, tagline,
                           self.grid.zone(1, 12, 0.82, 0.90),
                           TypeScale.SUBTITLE, self.colors.accent, PP_ALIGN.CENTER,
                           bold=False)

    # ── Save ─────────────────────────────────────────────────────────

    def save(self, path: str | Path) -> Path:
        """Save the presentation to a PPTX file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self._prs.save(str(path))
        log.info("PptxBuilder: saved %d slides to %s (%d KB)",
                 self._slide_count, path, path.stat().st_size // 1024)
        return path
