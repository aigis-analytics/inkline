"""PptxBuilder -- Advisor-pitch-grade slide generation.

Matches the Aigis Analytics advisor pitch aesthetic:
- Warm beige background (#e8e8e3)
- HubotSans-Bold ALL-CAPS titles
- RobotoCondensed body text
- Cards with thin dark borders (not solid fills)
- Dark navy panels used sparingly for emphasis
- Section labels in bordered badges
- Grayscale text only (color comes from shapes, not text)
- 8-level type scale from PDF extraction
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn

from inkline.core.grid import SlideGrid, Zone
from inkline.core.colors import hex_to_rgb

log = logging.getLogger(__name__)

# -- Slide dimensions (16:9) --
SLIDE_W = Inches(10)
SLIDE_H = Inches(7.5)

# -- Exact colors extracted from advisor pitch PDF --
_BG = {
    "warm":    "#e8e8e3",   # Main slide background (warm beige)
    "card":    "#e8e8e3",   # Card fill (same as bg - transparent feel)
    "shadow":  "#c8cac1",   # Card border/accent color
    "footer":  "#dbdbd6",   # Footer bar (slightly darker)
    "navy":    "#1a3a5c",   # Dark featured panel (navy)
    "dark":    "#0c0d0f",   # Very dark (title slide, closing)
    "white":   "#ffffff",
}

_TC = {
    "title":   "#0c0d0f",   # Near-black -- slide titles (ALL CAPS)
    "label":   "#1e1e1a",   # Dark gray -- section label badges
    "body":    "#55575a",   # Medium gray -- body text, card titles
    "white":   "#ffffff",   # On dark panels only
    "black":   "#000000",   # Occasional emphasis
}

# -- Type scale (exact pt sizes from PDF extraction) --
_TS = {
    "display":    78,    # Company name (title slide)
    "hero":       44,    # Big impact stats
    "title":      35,    # Slide titles (ALL CAPS)
    "card_title": 17,    # Card headers (ALL CAPS)
    "body":       14,    # Body text
    "body_sm":    13,    # Smaller body
    "label":      11,    # Section label badges
    "table":      10,    # Table cells
    "footnote":    7,    # Source notes
}


class PptxBuilder:
    """Builds advisor-pitch-grade PPTX slides."""

    def __init__(
        self,
        title: str = "Untitled",
        brand: str = "aigis",
        heading_font: str = "Hubot Sans",
        body_font: str = "Roboto Condensed",
        template: str | None = None,
    ):
        self.title = title
        self.brand = brand
        self.heading_font = heading_font
        self.body_font = body_font

        self._prs = Presentation()
        self._prs.slide_width = SLIDE_W
        self._prs.slide_height = SLIDE_H

        self.grid = SlideGrid()
        self._slide_count = 0
        self._logos = self._find_logos(brand)

    # -- Logo discovery --

    def _find_logos(self, brand: str) -> dict:
        base = Path(__file__).resolve().parent.parent / "assets"
        logos = {}
        # Prefer shield-only versions (no text), fall back to full logos
        search = [
            (f"{brand}_shield_dark.png", "for_light_bg"),
            (f"{brand}_shield_light.png", "for_dark_bg"),
            (f"{brand}_logo_dark.png", "for_light_bg"),
            (f"{brand}_logo_light.png", "for_dark_bg"),
        ]
        for name, key in search:
            p = base / name
            if p.exists() and key not in logos:
                logos[key] = p
        return logos

    def _logo_for(self, bg: str) -> Path | None:
        r, g, b = hex_to_rgb(bg)
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        if brightness < 128:
            return self._logos.get("for_dark_bg") or self._logos.get("for_light_bg")
        return self._logos.get("for_light_bg") or self._logos.get("for_dark_bg")

    # -- Primitives --

    def _slide(self) -> Any:
        s = self._prs.slides.add_slide(self._prs.slide_layouts[6])
        self._slide_count += 1
        return s

    def _bg(self, slide: Any, color: str) -> None:
        fill = slide.background.fill
        fill.solid()
        fill.fore_color.rgb = RGBColor(*hex_to_rgb(color))

    def _rect(self, slide: Any, x: float, y: float, w: float, h: float,
              fill_color: str, border_color: str = "", border_width: float = 0) -> Any:
        from pptx.enum.shapes import MSO_SHAPE
        shape = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
        shape.fill.solid()
        shape.fill.fore_color.rgb = RGBColor(*hex_to_rgb(fill_color))
        if border_color and border_width > 0:
            shape.line.color.rgb = RGBColor(*hex_to_rgb(border_color))
            shape.line.width = Pt(border_width)
        else:
            shape.line.fill.background()
        return shape

    def _card(self, slide: Any, x: float, y: float, w: float, h: float,
              dark: bool = False) -> Any:
        """Content card -- bordered on light bg, solid fill on dark."""
        if dark:
            return self._rect(slide, x, y, w, h, _BG["navy"])
        else:
            return self._rect(slide, x, y, w, h, _BG["card"],
                            border_color=_BG["shadow"], border_width=1.0)

    def _card_with_left_accent(self, slide: Any, x: float, y: float, w: float, h: float,
                                dark: bool = False) -> None:
        """Card with a thick left border accent (like the advisor pitch cards)."""
        self._card(slide, x, y, w, h, dark=dark)
        # Left accent strip
        accent_color = _BG["shadow"] if not dark else _BG["warm"]
        self._rect(slide, x, y, 0.06, h, accent_color)

    def _text(self, slide: Any, text: str, x: float, y: float, w: float, h: float,
              size: int, color: str, font: str | None = None, bold: bool = False,
              align: int = PP_ALIGN.LEFT) -> Any:
        tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = text
        p.font.size = Pt(size)
        p.font.bold = bold
        p.font.name = font or self.body_font
        p.font.color.rgb = RGBColor(*hex_to_rgb(color))
        p.alignment = align
        return tb

    def _heading(self, slide: Any, text: str, x: float, y: float, w: float, h: float,
                 size: int = _TS["title"], color: str = _TC["title"]) -> Any:
        """ALL-CAPS title in heading font."""
        return self._text(slide, text.upper(), x, y, w, h, size, color,
                         self.heading_font, bold=True)

    def _card_heading(self, slide: Any, text: str, x: float, y: float, w: float,
                      color: str = _TC["body"]) -> Any:
        """ALL-CAPS card sub-title."""
        return self._text(slide, text.upper(), x, y, w, 0.4, _TS["card_title"],
                         color, self.heading_font, bold=True)

    def _body_text(self, slide: Any, text: str, x: float, y: float, w: float, h: float,
                   color: str = _TC["body"]) -> Any:
        return self._text(slide, text, x, y, w, h, _TS["body"], color, self.body_font)

    def _label_badge(self, slide: Any, text: str, x: float, y: float) -> None:
        """Section label in bordered badge (matching advisor pitch style)."""
        # Bordered rectangle badge
        badge_w = len(text) * 0.09 + 0.4
        self._rect(slide, x, y, badge_w, 0.28, _BG["warm"],
                   border_color=_TC["label"], border_width=0.75)
        self._text(slide, text.upper(), x + 0.1, y + 0.02, badge_w - 0.2, 0.24,
                   _TS["label"], _TC["label"], self.body_font, bold=False)

    def _bullets(self, slide: Any, items: list[str], x: float, y: float, w: float, h: float,
                 color: str = _TC["body"], size: int = _TS["body"],
                 bold_prefix: bool = False) -> Any:
        """Bulleted list with optional bold prefix (text before first dash)."""
        tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        tf = tb.text_frame
        tf.word_wrap = True

        for i, item in enumerate(items):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.space_after = Pt(6)

            if bold_prefix and " -- " in item:
                parts = item.split(" -- ", 1)
                run_bold = p.add_run()
                run_bold.text = parts[0].strip()
                run_bold.font.size = Pt(size)
                run_bold.font.bold = True
                run_bold.font.name = self.body_font
                run_bold.font.color.rgb = RGBColor(*hex_to_rgb(color))

                run_rest = p.add_run()
                run_rest.text = " -- " + parts[1].strip()
                run_rest.font.size = Pt(size)
                run_rest.font.bold = False
                run_rest.font.name = self.body_font
                run_rest.font.color.rgb = RGBColor(*hex_to_rgb(color))
            else:
                p.text = item
                p.font.size = Pt(size)
                p.font.name = self.body_font
                p.font.color.rgb = RGBColor(*hex_to_rgb(color))
        return tb

    def _rich_body(self, slide: Any, text: str, x: float, y: float, w: float, h: float,
                   color: str = _TC["body"]) -> Any:
        """Body text with **bold** spans rendered as actual bold runs."""
        import re
        tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.space_after = Pt(4)

        parts = re.split(r'(\*\*.*?\*\*)', text)
        for part in parts:
            if part.startswith('**') and part.endswith('**'):
                run = p.add_run()
                run.text = part[2:-2]
                run.font.size = Pt(_TS["body"])
                run.font.bold = True
                run.font.name = self.body_font
                run.font.color.rgb = RGBColor(*hex_to_rgb(color))
            elif part:
                run = p.add_run()
                run.text = part
                run.font.size = Pt(_TS["body"])
                run.font.bold = False
                run.font.name = self.body_font
                run.font.color.rgb = RGBColor(*hex_to_rgb(color))
        return tb

    def _logo(self, slide: Any, x: float, y: float, h: float, bg: str) -> None:
        logo = self._logo_for(bg)
        if logo and logo.exists():
            slide.shapes.add_picture(str(logo), Inches(x), Inches(y), height=Inches(h))

    def _footer_bar(self, slide: Any, text: str, y: float = 6.2) -> None:
        """Footer quote/note area with thin top border."""
        # Thin divider line
        self._rect(slide, 0.5, y, 9.0, 0.015, _BG["shadow"])
        # Footer text
        self._text(slide, text, 0.5, y + 0.1, 9.0, 0.5, _TS["footnote"],
                   _TC["body"], self.body_font)

    # -- Slide Types --

    def add_title_slide(self, company: str, tagline: str, date: str = "",
                        subtitle: str = "") -> None:
        """Light bg title slide matching advisor pitch: logo + display name + tagline."""
        s = self._slide()
        self._bg(s, _BG["warm"])

        # Small category label top-left
        if subtitle:
            self._text(s, subtitle.upper(), 0.6, 0.5, 5, 0.3, _TS["label"],
                       _TC["body"], self.body_font)

        # Logo (left side, shield icon)
        self._logo(s, 0.6, 1.0, 1.5, _BG["warm"])

        # Company name (display size, ALL CAPS, right of logo)
        self._text(s, company.upper(), 2.8, 0.8, 7, 2.5, _TS["display"], _TC["title"],
                   self.heading_font, bold=True)

        # Tagline (ALL CAPS, bold)
        self._text(s, tagline.upper(), 0.6, 3.8, 9, 1.5, _TS["title"], _TC["title"],
                   self.heading_font, bold=True)

        # Thin divider line
        self._rect(s, 0.6, 5.4, 9.0, 0.015, _BG["shadow"])

        # Date / subtitle below divider
        if date:
            self._text(s, date, 0.6, 5.5, 9, 0.5, _TS["body"], _TC["body"],
                       self.body_font, bold=True)

    def add_content_slide(self, section: str, title: str, items: list[str],
                          accent_stat: str = "", accent_label: str = "",
                          footnote: str = "") -> None:
        """Content slide: badge label + ALL-CAPS title + bordered cards with bullets."""
        s = self._slide()
        self._bg(s, _BG["warm"])

        # Section badge
        self._label_badge(s, section, 0.5, 0.35)

        # Title (ALL CAPS)
        self._heading(s, title, 0.5, 0.75, 8.5, 1.2)

        # Content area
        if accent_stat:
            # Split: bullets left, stat card right
            self._card(s, 0.5, 2.2, 6.5, 4.0)
            self._bullets(s, items, 0.8, 2.4, 5.9, 3.6, _TC["body"], _TS["body"])

            # Accent stat in dark card
            self._card(s, 7.2, 2.2, 2.3, 4.0, dark=True)
            self._text(s, accent_stat, 7.2, 2.8, 2.3, 1.0, _TS["hero"], _TC["white"],
                       self.heading_font, bold=True, align=PP_ALIGN.CENTER)
            if accent_label:
                self._text(s, accent_label.upper(), 7.2, 4.0, 2.3, 0.8,
                           _TS["card_title"], _TC["white"],
                           self.heading_font, bold=True, align=PP_ALIGN.CENTER)
        else:
            # Full-width bordered card with bullets
            self._card(s, 0.5, 2.2, 9.0, 4.0)
            self._bullets(s, items, 0.8, 2.4, 8.4, 3.6, _TC["body"], _TS["body"])

        if footnote:
            self._footer_bar(s, footnote, y=6.5)

    def add_three_card_slide(self, section: str, title: str,
                              cards: list[tuple[str, str, str]],
                              footnote: str = "") -> None:
        """3-column cards with icon + title + body (like Problem/Workstreams slides).

        cards: list of (icon, card_title, body_text)
        """
        s = self._slide()
        self._bg(s, _BG["warm"])

        self._label_badge(s, section, 0.5, 0.35)
        self._heading(s, title, 0.5, 0.75, 8.5, 1.0)

        card_w = 2.8
        gap = 0.3
        start_x = 0.5
        card_y = 2.2
        card_h = 3.2

        for i, (icon, ctitle, body) in enumerate(cards):
            cx = start_x + i * (card_w + gap)
            self._card_with_left_accent(s, cx, card_y, card_w, card_h)

            # Icon + card title
            header_text = f"{icon}  {ctitle}" if icon else ctitle
            self._card_heading(s, header_text, cx + 0.2, card_y + 0.15, card_w - 0.4)

            # Body
            self._rich_body(s, body, cx + 0.2, card_y + 0.65, card_w - 0.4, card_h - 0.8)

        if footnote:
            self._footer_bar(s, footnote, y=5.8)

    def add_stat_slide(self, section: str, title: str,
                       stats: list[tuple[str, str, str]]) -> None:
        """Hero stat cards: big number + label + description."""
        s = self._slide()
        self._bg(s, _BG["warm"])

        self._label_badge(s, section, 0.5, 0.35)
        self._heading(s, title, 0.5, 0.75, 8.5, 1.0)

        n = len(stats)
        card_w = (8.5 - (n - 1) * 0.3) / n
        start_x = 0.5

        for i, (value, label, desc) in enumerate(stats):
            cx = start_x + i * (card_w + 0.3)

            # Hero number
            self._text(s, value, cx, 2.5, card_w, 1.0, _TS["hero"], _TC["title"],
                       self.heading_font, bold=True, align=PP_ALIGN.CENTER)

            # Label (ALL CAPS, bold)
            self._text(s, label.upper(), cx, 3.7, card_w, 0.5, _TS["card_title"],
                       _TC["body"], self.heading_font, bold=True, align=PP_ALIGN.CENTER)

            # Description
            self._text(s, desc, cx, 4.3, card_w, 0.8, _TS["body"], _TC["body"],
                       self.body_font, align=PP_ALIGN.CENTER)

    def add_table_slide(self, section: str, title: str,
                        headers: list[str], rows: list[list[str]],
                        footnote: str = "") -> None:
        """Full-width table with clean styling."""
        s = self._slide()
        self._bg(s, _BG["warm"])

        self._label_badge(s, section, 0.5, 0.3)
        self._heading(s, title, 0.5, 0.65, 8.5, 0.8, size=_TS["title"] - 4)

        # Table
        n_rows = len(rows) + 1
        n_cols = len(headers)
        tbl_y = 1.6
        tbl_h = min(5.2, 0.35 * n_rows + 0.4)
        tbl_shape = s.shapes.add_table(
            n_rows, n_cols,
            Inches(0.5), Inches(tbl_y), Inches(9.0), Inches(tbl_h))
        tbl = tbl_shape.table

        # Style header row
        for j, h in enumerate(headers):
            cell = tbl.cell(0, j)
            cell.text = h
            # Dark background for header
            cell_fill = cell.fill
            cell_fill.solid()
            cell_fill.fore_color.rgb = RGBColor(*hex_to_rgb(_BG["dark"]))
            for p in cell.text_frame.paragraphs:
                p.font.size = Pt(_TS["table"])
                p.font.bold = True
                p.font.name = self.body_font
                p.font.color.rgb = RGBColor(*hex_to_rgb(_TC["white"]))

        # Data rows with alternating bg
        for i, row in enumerate(rows):
            bg = _BG["warm"] if i % 2 == 0 else _BG["white"]
            for j, val in enumerate(row):
                cell = tbl.cell(i + 1, j)
                cell.text = str(val)
                cell_fill = cell.fill
                cell_fill.solid()
                cell_fill.fore_color.rgb = RGBColor(*hex_to_rgb(bg))
                for p in cell.text_frame.paragraphs:
                    p.font.size = Pt(_TS["table"])
                    p.font.name = self.body_font
                    p.font.color.rgb = RGBColor(*hex_to_rgb(_TC["body"]))

        if footnote:
            self._footer_bar(s, footnote, y=tbl_y + tbl_h + 0.2)

    def add_split_slide(self, section: str, title: str,
                        left_title: str, left_items: list[str],
                        right_title: str, right_items: list[str],
                        left_dark: bool = True) -> None:
        """2-panel split: one dark navy, one bordered card."""
        s = self._slide()
        self._bg(s, _BG["warm"])

        self._label_badge(s, section, 0.5, 0.35)
        self._heading(s, title, 0.5, 0.75, 8.5, 1.0)

        # Left panel
        self._card(s, 0.5, 2.2, 4.3, 4.2, dark=left_dark)
        left_tc = _TC["white"] if left_dark else _TC["body"]
        self._card_heading(s, left_title, 0.7, 2.35, 3.9, left_tc)
        self._bullets(s, left_items, 0.7, 2.85, 3.9, 3.3, left_tc, _TS["body"] - 1)

        # Right panel
        self._card(s, 5.1, 2.2, 4.4, 4.2, dark=not left_dark)
        right_tc = _TC["white"] if not left_dark else _TC["body"]
        self._card_heading(s, right_title, 5.3, 2.35, 4.0, right_tc)
        self._bullets(s, right_items, 5.3, 2.85, 4.0, 3.3, right_tc, _TS["body"] - 1)

    def add_four_card_slide(self, section: str, title: str,
                            cards: list[tuple[str, str, str]],
                            footnote: str = "") -> None:
        """2x2 grid of bordered cards (like Differentiation/How It Works).

        cards: list of (icon, card_title, body_text) -- exactly 4
        """
        s = self._slide()
        self._bg(s, _BG["warm"])

        self._label_badge(s, section, 0.5, 0.35)
        self._heading(s, title, 0.5, 0.75, 8.5, 0.8)

        card_w = 4.3
        card_h = 2.2
        positions = [
            (0.5, 1.8), (5.1, 1.8),
            (0.5, 4.2), (5.1, 4.2),
        ]

        for i, (icon, ctitle, body) in enumerate(cards[:4]):
            cx, cy = positions[i]
            self._card(s, cx, cy, card_w, card_h)

            header = f"{icon}  {ctitle}" if icon else ctitle
            self._card_heading(s, header, cx + 0.2, cy + 0.15, card_w - 0.4)
            self._rich_body(s, body, cx + 0.2, cy + 0.6, card_w - 0.4, card_h - 0.8)

        if footnote:
            self._footer_bar(s, footnote, y=6.6)

    def add_chart_slide(self, section: str, title: str,
                        chart_path: str | Path, footnote: str = "") -> None:
        """Chart image on warm background."""
        s = self._slide()
        self._bg(s, _BG["warm"])

        self._label_badge(s, section, 0.5, 0.35)
        self._heading(s, title, 0.5, 0.75, 8.5, 1.0)

        path = Path(chart_path)
        if path.exists():
            s.shapes.add_picture(str(path), Inches(0.5), Inches(2.0), width=Inches(9.0))

        if footnote:
            self._footer_bar(s, footnote)

    def add_closing_slide(self, name: str, role: str, email: str,
                          company: str = "", tagline: str = "") -> None:
        """Clean closing slide with contact info."""
        s = self._slide()
        self._bg(s, _BG["warm"])

        # Logo centered
        self._logo(s, 4.0, 0.6, 1.5, _BG["warm"])

        # Thin divider
        self._rect(s, 3.0, 2.5, 4.0, 0.015, _BG["shadow"])

        # Contact info
        self._text(s, name, 0, 3.0, 10, 0.6, _TS["title"], _TC["title"],
                   self.heading_font, bold=True, align=PP_ALIGN.CENTER)
        self._text(s, role, 0, 3.7, 10, 0.4, _TS["card_title"], _TC["body"],
                   self.body_font, align=PP_ALIGN.CENTER)
        self._text(s, email, 0, 4.2, 10, 0.4, _TS["body"], _TC["body"],
                   self.body_font, align=PP_ALIGN.CENTER)

        if company:
            self._text(s, company, 0, 5.0, 10, 0.4, _TS["label"], _TC["body"],
                       self.body_font, align=PP_ALIGN.CENTER)

        if tagline:
            self._rect(s, 3.0, 5.8, 4.0, 0.015, _BG["shadow"])
            self._text(s, tagline, 0, 5.9, 10, 0.5, _TS["body"], _TC["body"],
                       self.body_font, bold=True, align=PP_ALIGN.CENTER)

    # -- Save --

    def save(self, path: str | Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self._prs.save(str(path))
        log.info("PptxBuilder: %d slides -> %s (%d KB)",
                 self._slide_count, path, path.stat().st_size // 1024)
        return path
