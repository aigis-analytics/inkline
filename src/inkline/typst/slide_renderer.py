"""Typst slide renderer — generates 16:9 presentation markup from structured data.

Produces a complete ``.typ`` source string that compiles to a multi-page PDF
where each page is one slide.

Slide types: title, content, three_card, four_card, stat, table, split,
chart, closing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from inkline.typst.components import (
    _esc_content,
    _rgb,
    accent_bar,
    bar_row,
    card,
    card_title,
    data_table,
    footer_bar,
    hero_stat,
    section_badge,
    slide_title,
)


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class SlideSpec:
    """Specification for a single slide."""
    slide_type: str  # title, content, three_card, four_card, stat, table, split, chart, closing
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class DeckSpec:
    """Specification for a full slide deck."""
    slides: list[SlideSpec] = field(default_factory=list)
    title: str = "Untitled"
    date: str = ""
    subtitle: str = ""


# ---------------------------------------------------------------------------
# Multi-chart layout slot sizes
# ---------------------------------------------------------------------------
# Exact cell dimensions (width_cm, height_cm) for each chart image slot in
# multi_chart layouts. Derived from actual page geometry:
#   page: 25.4cm × 14.29cm, margins: left/right=1.4cm, top=1.4cm, bottom=1.2cm
#   content_width = 22.6cm, content_height = 11.69cm
#   multi_chart header overhead ≈ 1.62cm → body ≈ 10.07cm
#   _body_block height = 9.0cm, footer_bar inside = 0.69cm → chart content ≤ 8.31cm
#   _MC_BH = 8.2cm (8.31 - 0.11 safety) so images + footer fit without clipping
#   chart cell title overhead (8pt text + v(3pt)) ≈ 0.4cm
#
# These dimensions are imported by _auto_render_charts in __init__.py to size
# matplotlib figures exactly, so chart images fill their slots with no
# letterboxing or empty space — the PowerPoint-placeholder model.
#
# For top_bottom: dict key includes chart index (0=top, 1+=bottom).
# bottom_n is the number of bottom charts (1, 2, or 3); used for column width.
_MC_W = 22.6   # content width
_MC_BH = 8.2   # chart content height inside _body_block:
               # BODY_H_CM(9.0) - FOOTER_H_CM(0.69) = 8.31cm; use 8.2cm for safety margin.
_MC_G10 = 10 * 2.54 / 72   # 10pt gutter in cm
_MC_G12 = 12 * 2.54 / 72   # 12pt gutter
_MC_G8 = 8 * 2.54 / 72     # 8pt stack spacing
_MC_TOH = 0.4              # chart title overhead (8pt + 3pt)

MULTI_CHART_SLOT_SIZES: dict[str, list[tuple[float, float]]] = {
    # quad: 2×2 grid, gutter 10pt. Each cell = half width, half height.
    "quad": [
        ((_MC_W - _MC_G10) / 2, (_MC_BH - _MC_G10) / 2 - _MC_TOH),  # row0 col0
        ((_MC_W - _MC_G10) / 2, (_MC_BH - _MC_G10) / 2 - _MC_TOH),  # row0 col1
        ((_MC_W - _MC_G10) / 2, (_MC_BH - _MC_G10) / 2 - _MC_TOH),  # row1 col0
        ((_MC_W - _MC_G10) / 2, (_MC_BH - _MC_G10) / 2 - _MC_TOH),  # row1 col1
    ],
    # equal_2: 2 columns, gutter 12pt. Full body height.
    "equal_2": [
        ((_MC_W - _MC_G12) / 2, _MC_BH - _MC_TOH),
        ((_MC_W - _MC_G12) / 2, _MC_BH - _MC_TOH),
    ],
    # equal_3: 3 columns, 2×gutter 12pt.
    "equal_3": [
        ((_MC_W - 2 * _MC_G12) / 3, _MC_BH - _MC_TOH),
        ((_MC_W - 2 * _MC_G12) / 3, _MC_BH - _MC_TOH),
        ((_MC_W - 2 * _MC_G12) / 3, _MC_BH - _MC_TOH),
    ],
    # equal_4: 4 columns, 3×gutter 12pt.
    "equal_4": [
        ((_MC_W - 3 * _MC_G12) / 4, _MC_BH - _MC_TOH),
        ((_MC_W - 3 * _MC_G12) / 4, _MC_BH - _MC_TOH),
        ((_MC_W - 3 * _MC_G12) / 4, _MC_BH - _MC_TOH),
        ((_MC_W - 3 * _MC_G12) / 4, _MC_BH - _MC_TOH),
    ],
    # hero_left: 2fr (hero) + 1fr (small), gutter 12pt.
    "hero_left": [
        ((_MC_W - _MC_G12) * 2 / 3, _MC_BH - _MC_TOH),   # hero
        ((_MC_W - _MC_G12) * 1 / 3, _MC_BH - _MC_TOH),   # small
    ],
    # hero_left_3: 2fr hero + 1fr + 1fr, 2×gutter 12pt.
    "hero_left_3": [
        ((_MC_W - 2 * _MC_G12) * 2 / 4, _MC_BH - _MC_TOH),  # hero
        ((_MC_W - 2 * _MC_G12) * 1 / 4, _MC_BH - _MC_TOH),  # small
        ((_MC_W - 2 * _MC_G12) * 1 / 4, _MC_BH - _MC_TOH),  # small
    ],
    # hero_right_3: 1fr + 1fr + 2fr hero, 2×gutter 12pt.
    "hero_right_3": [
        ((_MC_W - 2 * _MC_G12) * 1 / 4, _MC_BH - _MC_TOH),  # small
        ((_MC_W - 2 * _MC_G12) * 1 / 4, _MC_BH - _MC_TOH),  # small
        ((_MC_W - 2 * _MC_G12) * 2 / 4, _MC_BH - _MC_TOH),  # hero
    ],
    # top_bottom: stack(8pt). Top 55%, bottom 45% of body height.
    # Index 0 = top (full width). Indices 1-3 = bottom (width depends on n_bottom).
    # Bottom widths assume 2 bottom charts; caller adjusts for 1 or 3.
    "top_bottom": [
        (_MC_W, (_MC_BH - _MC_G8) * 0.55 - _MC_TOH),                  # [0] top
        ((_MC_W - _MC_G10) / 2, (_MC_BH - _MC_G8) * 0.45 - _MC_TOH),  # [1] bot (2-col default)
        ((_MC_W - _MC_G10) / 2, (_MC_BH - _MC_G8) * 0.45 - _MC_TOH),  # [2] bot
        ((_MC_W - 2 * _MC_G10) / 3, (_MC_BH - _MC_G8) * 0.45 - _MC_TOH),  # [3] bot (3-col)
    ],
    # three_top_wide: 3 equal charts top (45%) + 1 full-width chart bottom (55%).
    # Inverse of top_bottom. Index 0-2 = top row; index 3 = bottom wide.
    "three_top_wide": [
        ((_MC_W - 2 * _MC_G10) / 3, (_MC_BH - _MC_G8) * 0.45 - _MC_TOH),  # [0] top-left
        ((_MC_W - 2 * _MC_G10) / 3, (_MC_BH - _MC_G8) * 0.45 - _MC_TOH),  # [1] top-center
        ((_MC_W - 2 * _MC_G10) / 3, (_MC_BH - _MC_G8) * 0.45 - _MC_TOH),  # [2] top-right
        (_MC_W, (_MC_BH - _MC_G8) * 0.55 - _MC_TOH),                       # [3] bottom wide
    ],
    # left_stack: wide chart left (3fr) + 2 stacked charts right (2fr).
    # Right stack gutter = 10pt. Index 0 = left; 1 = right-top; 2 = right-bottom.
    "left_stack": [
        ((_MC_W - _MC_G12) * 3 / 5, _MC_BH - _MC_TOH),                  # [0] left hero
        ((_MC_W - _MC_G12) * 2 / 5, (_MC_BH - _MC_G10) / 2 - _MC_TOH),  # [1] right top
        ((_MC_W - _MC_G12) * 2 / 5, (_MC_BH - _MC_G10) / 2 - _MC_TOH),  # [2] right bottom
    ],
    # right_stack: 2 stacked charts left (2fr) + wide chart right (3fr).
    # Index 0 = left-top; 1 = left-bottom; 2 = right hero.
    "right_stack": [
        ((_MC_W - _MC_G12) * 2 / 5, (_MC_BH - _MC_G10) / 2 - _MC_TOH),  # [0] left top
        ((_MC_W - _MC_G12) * 2 / 5, (_MC_BH - _MC_G10) / 2 - _MC_TOH),  # [1] left bottom
        ((_MC_W - _MC_G12) * 3 / 5, _MC_BH - _MC_TOH),                   # [2] right hero
    ],
    # mosaic_5: row of 2 charts (top 50%) + row of 3 charts (bottom 50%).
    # Index 0-1 = top row; index 2-4 = bottom row.
    "mosaic_5": [
        ((_MC_W - _MC_G10) / 2, (_MC_BH - _MC_G8) * 0.50 - _MC_TOH),         # [0] top-left
        ((_MC_W - _MC_G10) / 2, (_MC_BH - _MC_G8) * 0.50 - _MC_TOH),         # [1] top-right
        ((_MC_W - 2 * _MC_G10) / 3, (_MC_BH - _MC_G8) * 0.50 - _MC_TOH),     # [2] bot-left
        ((_MC_W - 2 * _MC_G10) / 3, (_MC_BH - _MC_G8) * 0.50 - _MC_TOH),     # [3] bot-center
        ((_MC_W - 2 * _MC_G10) / 3, (_MC_BH - _MC_G8) * 0.50 - _MC_TOH),     # [4] bot-right
    ],
    # six_grid: 3 columns × 2 rows = 6 equal charts. gutter 10pt.
    "six_grid": [
        ((_MC_W - 2 * _MC_G10) / 3, (_MC_BH - _MC_G10) / 2 - _MC_TOH),  # row0 col0
        ((_MC_W - 2 * _MC_G10) / 3, (_MC_BH - _MC_G10) / 2 - _MC_TOH),  # row0 col1
        ((_MC_W - 2 * _MC_G10) / 3, (_MC_BH - _MC_G10) / 2 - _MC_TOH),  # row0 col2
        ((_MC_W - 2 * _MC_G10) / 3, (_MC_BH - _MC_G10) / 2 - _MC_TOH),  # row1 col0
        ((_MC_W - 2 * _MC_G10) / 3, (_MC_BH - _MC_G10) / 2 - _MC_TOH),  # row1 col1
        ((_MC_W - 2 * _MC_G10) / 3, (_MC_BH - _MC_G10) / 2 - _MC_TOH),  # row1 col2
    ],
}

# Convenience accessor for _auto_render_charts
def get_multi_chart_slot(layout: str, chart_index: int, n_charts: int) -> tuple[float, float]:
    """Return (width_cm, height_cm) for a chart slot.

    For top_bottom, adjusts bottom-chart widths based on actual n_bottom charts.
    """
    slots = MULTI_CHART_SLOT_SIZES.get(layout)
    if not slots:
        return (5.5, 3.0)  # safe fallback

    if layout == "top_bottom" and chart_index > 0:
        # Bottom charts: recalculate width based on actual number of bottom charts
        n_bottom = n_charts - 1
        if n_bottom == 1:
            w = _MC_W
        elif n_bottom == 3:
            w = (_MC_W - 2 * _MC_G10) / 3
        else:
            w = (_MC_W - _MC_G10) / 2  # default: 2 bottom charts
        h = (_MC_BH - _MC_G8) * 0.45 - _MC_TOH
        return (w, h)

    # All other layouts: use slot table, clamped to list length
    idx = min(chart_index, len(slots) - 1)
    return slots[idx]


# ---------------------------------------------------------------------------
# Content limits — derived from page geometry + Source Sans 3 font metrics
# ---------------------------------------------------------------------------
# Page: 25.4 × 14.29cm, margins: top 1.4cm, bottom 1.2cm, left/right 1.4cm
# Content width W = 22.6cm.  Body block = 9.0cm (clip: true), footer_bar = 0.69cm
# Available body content = 8.31cm.
#
# Source Sans 3 average character widths (fraction of em, empirically measured):
#   Regular text ~0.54em  |  Bold text ~0.60em
# At 22pt bold: 22 × 0.03528 × 0.60 = 0.466cm/char → W/char = 48 → use 45 (safety)
# At 18pt bold: 0.381cm/char → half-col (10.6cm): 27 chars
# At 14pt reg:  0.267cm/char → full: 84, half: 39, third: 26
# At 13pt bold: 0.275cm/char → half: 38, third: 25
# At 12pt reg:  0.229cm/char → half: 46, third: 31, quarter (5.1cm): 22
# At 10pt reg:  0.191cm/char → quarter: 26
# At 40pt bold: 0.847cm/char → 4-col (5.1cm): 6 → use 8 empirical limit
#
# Grid gutter = 20pt = 0.706cm
# 4-col width = (22.6 - 3×0.706)/4 = 5.12cm  |  3-col = 7.06cm  |  2-col = 10.95cm
# Card inset = 14pt = 0.494cm each side:  inner 2-col = 9.96cm  |  inner 3-col = 6.07cm

def _clamp(text: str | None, n: int) -> str:
    """Truncate text to at most n characters, appending '…' if cut."""
    if not text:
        return text or ""
    s = str(text)
    return s if len(s) <= n else s[:n - 1] + "…"


def _clamp_list(items: list, n: int) -> list:
    """Clamp every string element in a list to n chars."""
    return [_clamp(item, n) if isinstance(item, str) else item for item in items]


# Per-field character limits for every slide type.
# Key format:  "field"               → simple top-level string field
#              "list_field.subfield"  → subfield inside each dict of a list field
#              "list_field"           → direct-string items of a list
FIELD_LIMITS: dict[str, dict[str, int]] = {
    "title": {},  # title/closing/section_divider intentionally unbounded
    "closing": {},
    "section_divider": {},
    "content": {
        "title": 45,      # 22pt bold full-width → 48 chars max; 45 with margin
        "items": 80,      # 14pt at full 22.6cm → 84 chars; 80 with margin
        "footnote": 90,
    },
    "split": {
        "title": 45,
        "left.heading": 26,   # 18pt bold half-col
        "right.heading": 26,
        "left.items": 65,     # 14pt half-col — revalidated ceiling
        "right.items": 65,
        "footnote": 90,
    },
    "three_card": {
        "title": 45,
        "cards.title": 24,    # 13pt bold inner 3-col (6.07cm)
        "cards.body": 95,     # 12pt inner 3-col — revalidated ceiling
        "footnote": 90,
    },
    "four_card": {
        "title": 45,
        "cards.title": 42,    # 13pt bold inner 2-col (9.96cm) — revalidated ceiling
        "cards.body": 145,    # 12pt inner 2-col = 43 chars/line × ~3.4 lines
        "footnote": 90,
    },
    "stat": {
        "title": 45,
        # value at 40pt bold: 4-col→8 chars, 3-col→12, 2-col→16
        # enforced dynamically in _apply_field_limits
        "stats.value": 8,     # worst-case (4 stats); overridden per n_stats below
        "stats.label": 20,    # 12pt bold upper at 5.1cm
        "stats.desc": 26,     # 10pt at 5.1cm
    },
    "table": {
        "title": 45,
        # cell width depends on n_cols; use 20 (safe for 5-col tables)
        "headers": 20,
        "rows": 20,           # applied per cell in each row
        "footnote": 90,
    },
    "bar_chart": {
        "title": 45,
        "bars.label": 25,     # 12pt at ~6cm label column
        "bars.value": 12,     # numeric
        "footnote": 90,
    },
    "kpi_strip": {
        "title": 45,
        "kpis.value": 10,     # 18pt bold at ~4.5cm (5-kpi layout)
        "kpis.label": 20,     # 12pt at ~4.5cm
        "footnote": 90,
    },
    "chart": {
        "title": 45,
        "footnote": 90,
    },
    "chart_caption": {
        "title": 45,
        "caption": 90,
        "bullets": 80,        # sidebar 35% = 7.9cm, 14pt → 29 chars/line × ~2.8 lines
        "footnote": 90,
    },
    "dashboard": {
        "title": 45,
        "stats.value": 10,    # 18pt bold at ~7.5cm (40% col ÷ 3 stats)
        "stats.label": 22,
        "bullets": 70,        # 14pt at 40% col = 8.6cm → 32 chars/line × ~2.2 lines
        "footnote": 90,
    },
    "timeline": {
        "title": 45,
        "milestones.date": 12,   # "Pre-Mar 2029" = 12 ✓
        "milestones.title": 18,  # 12pt bold at 3-col width = 7cm → 30 chars; 18 for safety
        "milestones.body": 70,   # 10pt at 3-col width → 36 chars/line × ~2 lines
        "footnote": 90,
    },
    "comparison": {
        "title": 45,
        "left_title": 26,     # 18pt bold half-col
        "right_title": 26,
        "rows.metric": 22,    # 12pt muted at ~5cm left margin
        "rows.left": 30,      # 12pt half-col value
        "rows.right": 30,
        "footnote": 90,
    },
    "feature_grid": {
        "title": 45,
        "features.title": 22,  # 13pt bold inner 3-col (6.07cm)
        "features.body": 130,  # 12pt inner 3-col: ~22 chars/line × 6 lines validated
        "footnote": 90,
    },
    "process_flow": {
        "title": 45,
        "steps.title": 22,
        "steps.body": 130,    # 4-step layout: ~130 chars fit without overflow
        "footnote": 90,
    },
    "icon_stat": {
        "title": 45,
        "stats.value": 14,
        "stats.icon": 4,
        "stats.label": 22,
        "stats.desc": 50,
        "footnote": 90,
    },
    "progress_bars": {
        "title": 45,
        "bars.label": 32,
        "footnote": 90,
    },
    "pyramid": {
        "title": 45,
        "tiers.label": 30,
        "tiers.value": 15,
        "footnote": 90,
    },
    "multi_chart": {
        "title": 45,
        "charts.title": 30,
        "footnote": 90,
    },
    "team_grid": {
        "title": 45,
        "members.name": 30,    # Bold 14pt in third-col ~7cm → 26 chars; 30 with safety
        "members.role": 35,    # 10pt italic in third-col → 36 chars
        "members.bio": 120,    # 9pt 3-line bio at ~7cm → ~120 chars
        "footnote": 90,
    },
}


# ---------------------------------------------------------------------------
# Renderer
# ---------------------------------------------------------------------------

class TypstSlideRenderer:
    """Renders SlideSpec objects into Typst markup."""

    # Slide geometry (16:9 at 25.4cm × 14.29cm with 1.2cm x-margin, 0.8cm y-margin)
    SLIDE_WIDTH_CM = 23.0   # usable content width (25.4 - 2×1.2)
    SLIDE_HEIGHT_CM = 12.69  # usable content height (14.29 - 2×0.8)
    # After section badge + title + spacing: ~2.5cm header, ~1.5cm footer
    BODY_HEIGHT_CM = 9.0    # usable body area for content
    # Fixed zone heights (must sum to ≤ SLIDE_HEIGHT_CM)
    HEADER_H_CM = 2.0    # badge + v(6pt) + title + v(14pt)
    FOOTER_H_CM = 0.69   # line + v(4pt) + 7pt text
    BODY_H_CM = 9.0      # clipped content area (11.69 - 2.0 - 0.69)
    # Content limits per slide type
    MAX_BULLETS = 8
    MAX_TABLE_ROWS = 12
    MAX_BARS = 8
    MAX_TIMELINE_NODES = 8
    MAX_PROCESS_STEPS = 5
    MAX_PROGRESS_BARS = 6
    MAX_PYRAMID_TIERS = 6
    MAX_COMPARISON_ROWS = 8

    def __init__(self, theme: dict, image_root: str | None = None):
        self.t = theme
        self._image_root = image_root

    @staticmethod
    def _apply_field_limits(slide_type: str, d: dict) -> dict:
        """Truncate every text field in slide data to its geometric character limit.

        This is a hard pre-render pass — Typst never sees text that would overflow
        its allocated box.  Limits are defined in FIELD_LIMITS, derived from:
          page width 22.6cm, font metrics (Source Sans 3), and box geometry.

        The stat slide has a special case: hero-value limits tighten as n_stats grows
        because each column gets narrower (4-col → 8 chars, 3-col → 12, 2-col → 16).
        """
        import copy
        limits = FIELD_LIMITS.get(slide_type, {})
        if not limits:
            return d
        d = copy.deepcopy(d)

        for spec, n in limits.items():
            if "." not in spec:
                # Top-level field
                val = d.get(spec)
                if isinstance(val, str):
                    d[spec] = _clamp(val, n)
                elif isinstance(val, list):
                    d[spec] = _clamp_list(val, n)
            else:
                list_key, subkey = spec.split(".", 1)
                items = d.get(list_key)
                if not isinstance(items, list):
                    continue
                for item in items:
                    if isinstance(item, dict):
                        v = item.get(subkey)
                        if isinstance(v, str):
                            # stat.stats.value: tighten based on n_stats
                            limit = n
                            if slide_type == "stat" and subkey == "value":
                                ns = len(d.get("stats", []))
                                if ns <= 2:
                                    limit = 16
                                elif ns == 3:
                                    limit = 12
                                # else keep 8 (4 stats)
                            item[subkey] = _clamp(v, limit)

        return d

    def _body_block(self, inner: str, footnote: str) -> str:
        """Wrap body content + footer in a fixed-height clipped block.

        This prevents any native Typst content from overflowing to the next page.
        The block is 9.0cm tall (hard-clipped). The footer sits at the bottom
        via v(1fr), which works correctly within a finite-height block.
        """
        t = self.t
        return (
            f"block(height: {self.BODY_H_CM}cm, clip: true, width: 100%)[#{{\n"
            f"  {inner}\n\n"
            f"  {footer_bar(footnote, t['border'], t['muted'])}\n"
            f"}}]"
        )

    def _image_markup(self, image_path: str, **kwargs) -> str:
        """Return Typst image markup, or a placeholder if the file is missing.

        Path resolution order when image_root is set:
          1. image_root / image_path  (exact relative path)
          2. image_root / "charts" / image_path  (charts sub-directory)
          3. image_path as absolute path
        The resolved Typst-relative path is used in the image() call so Typst
        can locate the file from its root directory.
        """
        from pathlib import Path
        exists = False
        typst_path = image_path  # path used in generated Typst source
        if image_path:
            if self._image_root:
                root = Path(self._image_root)
                candidate = root / image_path
                if candidate.exists():
                    exists = True
                else:
                    # Fallback: check charts/ subdirectory
                    charts_candidate = root / "charts" / image_path
                    if charts_candidate.exists():
                        exists = True
                        typst_path = "charts/" + image_path
            else:
                exists = Path(image_path).exists()
            if not exists:
                import logging
                logging.getLogger(__name__).warning(
                    "Image not found, using placeholder: %s", image_path
                )

        if exists:
            args = ", ".join(f'{k.replace("_", "-")}: {v}' for k, v in kwargs.items())
            return f'image("{typst_path}", {args})' if args else f'image("{typst_path}")'

        # Typst-native placeholder: colored rect with text.
        # Use caller-supplied height/width kwargs so placeholder takes the same
        # space as the real image would — otherwise height: 100% fills the page.
        t = self.t
        label = image_path or "Chart not available"
        ph_height = kwargs.get("height", "5cm")
        ph_width = kwargs.get("width", "100%")
        return (
            f'block(fill: {_rgb(t["card_fill"])}, stroke: 1pt + {_rgb(t["border"])}, '
            f'width: {ph_width}, height: {ph_height}, radius: 4pt)['
            f'#align(center + horizon, text(size: 9pt, fill: {_rgb(t["muted"])}, style: "italic")['
            f'"Chart not available\\n{label}"'
            f'])]'
        )

    # Slide types that use #page(...)[content] (function form) which
    # starts its own page — no #pagebreak() needed before them.
    _SELF_PAGED_TYPES = {"title", "closing"}

    def render_deck(self, spec: DeckSpec) -> str:
        """Render a full deck to Typst source."""
        parts = [self._preamble()]
        for i, slide in enumerate(spec.slides):
            # #pagebreak() between slides — but skip when the next slide
            # uses #page(...) which starts its own page. Otherwise we get
            # an empty page between them.
            if i > 0 and slide.slide_type not in self._SELF_PAGED_TYPES:
                parts.append("#pagebreak()")
            parts.append(self._render_slide(slide))
        return "\n\n".join(parts)

    # -- Preamble ----------------------------------------------------------

    def _preamble(self) -> str:
        t = self.t
        heading_font = t.get("heading_font", "Inter")
        body_font = t.get("body_font", "Inter")
        body_size = t.get("body_size", 11)
        accent = t.get("accent", "#6366F1")
        muted = t.get("muted", "#64748B")
        bg = t.get("bg", "#FFFFFF")
        brand_name = t.get("name", "")
        # Footer tagline — prefer brand footer_text, fall back to brand tagline,
        # NEVER use template desc (that's metadata for humans, not slide chrome)
        footer_tagline = t.get("footer_text") or t.get("tagline") or ""
        return f"""// Generated by Inkline - Typst Slide Engine
#set page(
  width: 25.4cm,
  height: 14.29cm,
  margin: (top: 1.4cm, bottom: 1.2cm, left: 1.4cm, right: 1.4cm),
  fill: {_rgb(bg)},
  header: context {{
    if counter(page).get().first() > 1 {{
      grid(
        columns: (auto, 1fr, auto),
        align: horizon,
        block(width: 2.4cm, height: 3pt, fill: {_rgb(accent)}),
        h(1fr),
        text(size: 8pt, weight: "bold", tracking: 1pt, fill: {_rgb(muted)})[{_esc(brand_name).upper()}],
      )
    }}
  }},
  footer: context {{
    if counter(page).get().first() > 1 {{
      grid(
        columns: (auto, 1fr, auto),
        align: horizon,
        text(size: 8pt, fill: {_rgb(muted)})[{_esc(footer_tagline)}],
        h(1fr),
        text(size: 8pt, weight: "bold", fill: {_rgb(accent)})[#counter(page).display() / #context counter(page).final().first()],
      )
    }}
  }},
)
#set text(font: "{body_font}", size: {body_size}pt, fill: {_rgb(t.get('text', '#0F172A'))})
#set par(leading: 0.7em)"""

    # -- Slide dispatch ----------------------------------------------------

    def _render_slide(self, slide: SlideSpec) -> str:
        renderer = {
            "title": self._title_slide,
            "content": self._content_slide,
            "three_card": self._three_card_slide,
            "four_card": self._four_card_slide,
            "stat": self._stat_slide,
            "table": self._table_slide,
            "split": self._split_slide,
            "chart": self._chart_slide,
            "closing": self._closing_slide,
            "bar_chart": self._bar_chart_slide,
            "kpi_strip": self._kpi_strip_slide,
            "timeline": self._timeline_slide,
            "process_flow": self._process_flow_slide,
            "icon_stat": self._icon_stat_slide,
            "progress_bars": self._progress_bars_slide,
            "pyramid": self._pyramid_slide,
            "comparison": self._comparison_slide,
            "feature_grid": self._feature_grid_slide,
            "dashboard": self._dashboard_slide,
            "chart_caption": self._chart_caption_slide,
            "multi_chart": self._multi_chart_slide,
            "section_divider": self._section_divider_slide,
            # New slide types (P4)
            "credentials": self._credentials_slide,
            "testimonial": self._testimonial_slide,
            "before_after": self._before_after_slide,
            # New slide types (P5)
            "team_grid": self._team_grid_slide,
        }.get(slide.slide_type)
        if not renderer:
            return f'// Unknown slide type: {slide.slide_type}'
        # Hard-truncate every text field to its geometric capacity before rendering.
        # This guarantees Typst never receives content that would overflow its box.
        data = self._apply_field_limits(slide.slide_type, slide.data)
        return renderer(data)

    # -- Title slide -------------------------------------------------------

    def _title_slide(self, d: dict) -> str:
        t = self.t
        company = d.get("company", t.get("name", ""))
        tagline = d.get("tagline", "")
        date = d.get("date", "")
        subtitle = d.get("subtitle", "")
        left_footer = d.get("left_footer", "")
        secondary_headline = d.get("secondary_headline", "")
        heading_font = t.get("heading_font", "Inter")

        # Resolve title bg/fg — if brand bg is light, use it for title too
        title_bg = t.get("title_bg", t.get("bg", "#1B283B"))
        title_fg = t.get("title_fg", "#FFFFFF")
        logo_path = t.get("logo_light_path", "")

        # Adaptive vertical spacing: when secondary_headline or both subtitle +
        # left_footer are present, compress the upper spacer so the lower half
        # is visually filled rather than blank.
        has_lower_content = bool(secondary_headline or subtitle or left_footer)
        upper_frac = "0.6fr" if has_lower_content else "1fr"

        lower_block = ""
        if secondary_headline:
            lower_block += f'#v(20pt)\n  #text(size: 14pt, fill: {_rgb(t["muted"])})[{_esc(secondary_headline)}]\n  '
        if subtitle:
            lower_block += f'#text(size: 11pt, fill: {_rgb(t["muted"])})[{_esc(subtitle)}]#v(4pt)\n  '
        if left_footer:
            lower_block += f'#text(weight: "bold", size: 11pt, fill: {_rgb(title_fg)})[{_esc(left_footer)}]#v(4pt)\n  '

        return f"""#page(
  fill: {_rgb(title_bg)},
  margin: (top: 1.4cm, bottom: 1.2cm, left: 1.6cm, right: 1.6cm),
  header: none,
  footer: none,
)[
  #set text(fill: {_rgb(title_fg)})

  #v({upper_frac})

  // Shield + company name
  #grid(
    columns: (4.5cm, 1fr),
    gutter: 16pt,
    align: horizon,
    {f'image("{logo_path}", height: 4.2cm),' if logo_path else 'none,'}
    text(weight: "bold", size: 60pt, font: "{heading_font}", tracking: -1pt)[#upper[{_esc(company)}]]
  )

  #v(0.6cm)

  // Tagline — large bold uppercase, full width
  #text(weight: "bold", size: 20pt, font: "{heading_font}", fill: {_rgb(title_fg)})[#upper[{_esc(tagline)}]]

  #v(0.5cm)
  #line(length: 100%, stroke: 0.5pt + {_rgb(t['muted'])})
  #v(0.4cm)
  {lower_block}
  #v(1fr)

  // Footer — date + confidentiality
  #grid(
    columns: (1fr, auto),
    align: bottom,
    text(size: 9pt, fill: {_rgb(t['muted'])})[{_esc(date)}],
    text(size: 8pt, weight: "bold", tracking: 1pt, fill: {_rgb(t['muted'])})[{_esc(t.get('confidentiality', ''))}],
  )
]"""

    # -- Content slide -----------------------------------------------------

    def _content_slide(self, d: dict) -> str:
        t = self.t
        section = d.get("section", "")
        title = d.get("title", "")
        items = _ensure_string_items(d.get("items", []))[:self.MAX_BULLETS]
        footnote = d.get("footnote", "")

        # Auto-shrink: more bullets → smaller font so everything fits in 9cm body
        n_items = len(items)
        if n_items <= 5:
            item_font = 12
        elif n_items <= 7:
            item_font = 11
        else:
            item_font = 10

        bullets = "\n    ".join(f"- {_esc_rich(item, t['accent'])}" for item in items)

        body = f"""text(size: {item_font}pt, fill: {_rgb(t['text'])})[
    {bullets}
  ]"""

        return f"""#{{
  set page(fill: {_rgb(t['bg'])})
  set text(fill: {_rgb(t['text'])})
  set block(spacing: 0pt)
  set par(spacing: 0em)

  {section_badge(section, t['muted'])}
  v(6pt)
  {slide_title(title, t['text'])}
  v(14pt)

  {self._body_block(body, footnote)}
}}"""

    # -- Three card slide --------------------------------------------------

    def _three_card_slide(self, d: dict) -> str:
        t = self.t
        section = d.get("section", "")
        title = d.get("title", "")
        cards = d.get("cards", [])
        footnote = d.get("footnote", "")
        highlight_idx = d.get("highlight_index", 1)  # Which card gets accent fill

        if not cards:
            return self._content_slide(d)

        card_markups = []
        for i, c in enumerate(cards[:3]):
            if i == highlight_idx:
                # Accent card
                cm = card(
                    f'{card_title(c.get("title", ""), t["title_fg"])}\n      #v(6pt)\n      #text(size: 10pt, fill: {_rgb(t["title_fg"])})[{_esc(c.get("body", ""))}]',
                    fill=t["accent"],
                    text_color=t["title_fg"],
                )
            else:
                cm = card(
                    f'{card_title(c.get("title", ""), t["text"])}\n      #v(6pt)\n      #text(size: 10pt, fill: {_rgb(t["muted"])})[{_esc(c.get("body", ""))}]',
                    fill=t["card_fill"],
                    border=t["border"],
                    text_color=t["text"],
                )
            card_markups.append(cm)

        cards_str = ",\n    ".join(card_markups)

        body = f"""v(1fr)

  grid(
    columns: (1fr, 1fr, 1fr),
    gutter: 14pt,
    {cards_str}
  )

  v(1fr)"""

        return f"""#{{
  set page(fill: {_rgb(t['bg'])})
  set text(fill: {_rgb(t['text'])})
  set block(spacing: 0pt)
  set par(spacing: 0em)

  {section_badge(section, t['muted'])}
  v(6pt)
  {slide_title(title, t['text'])}

  {self._body_block(body, footnote)}
}}"""

    # -- Four card slide ---------------------------------------------------

    def _four_card_slide(self, d: dict) -> str:
        t = self.t
        section = d.get("section", "")
        title = d.get("title", "")
        cards = d.get("cards", [])
        footnote = d.get("footnote", "")

        if not cards:
            return self._content_slide(d)

        card_markups = []
        for c in cards[:4]:
            cm = card(
                f'{card_title(c.get("title", ""), t["text"])}\n      #v(6pt)\n      #text(size: 10.5pt, fill: {_rgb(t["muted"])})[{_esc(c.get("body", ""))}]',
                fill=t["card_fill"],
                border=t["border"],
                text_color=t["text"],
            )
            card_markups.append(cm)

        cards_str = ",\n    ".join(card_markups)

        body = f"""v(1fr)

  grid(
    columns: (1fr, 1fr),
    gutter: 14pt,
    {cards_str}
  )

  v(1fr)"""

        return f"""#{{
  set page(fill: {_rgb(t['bg'])})
  set text(fill: {_rgb(t['text'])})
  set block(spacing: 0pt)
  set par(spacing: 0em)

  {section_badge(section, t['muted'])}
  v(6pt)
  {slide_title(title, t['text'])}

  {self._body_block(body, footnote)}
}}"""

    # -- Stat slide --------------------------------------------------------

    def _stat_slide(self, d: dict) -> str:
        t = self.t
        section = d.get("section", "")
        title = d.get("title", "")
        stats = d.get("stats", [])

        stat_markups = []
        for i, s in enumerate(stats[:4]):
            accent = t["accent"] if i == 1 else None  # Highlight second stat
            stat_markups.append(hero_stat(
                s.get("value", ""),
                s.get("label", ""),
                s.get("desc", ""),
                t["text"],
                t["muted"],
                accent=accent,
            ))

        stats_str = ",\n    ".join(stat_markups)
        n_cols = len(stat_markups)

        return f"""#{{
  set page(fill: {_rgb(t['bg'])})
  set text(fill: {_rgb(t['text'])})
  set block(spacing: 0pt)
  set par(spacing: 0em)

  {section_badge(section, t['muted'])}
  v(6pt)
  {slide_title(title, t['text'])}
  v(28pt)

  grid(
    columns: ({', '.join(['1fr'] * n_cols)}),
    gutter: 20pt,
    {stats_str}
  )

  v(1fr)
  {accent_bar(t['accent'], 'bottom')}
}}"""

    # -- Table slide -------------------------------------------------------

    def _table_slide(self, d: dict) -> str:
        t = self.t
        section = d.get("section", "")
        title = d.get("title", "")
        headers = d.get("headers", [])
        rows = d.get("rows", [])[:self.MAX_TABLE_ROWS]
        footnote = d.get("footnote", "")

        table_markup = data_table(
            headers,
            rows,
            header_fill=t.get("accent", t.get("surface", "#1a3a5c")),
            header_text="#FFFFFF",
            bg=t["bg"],
            alt_bg=t.get("card_fill", t.get("surface", "#F5F5F5")),
            border=t["border"],
        )

        body = f"""{table_markup}"""

        return f"""#{{
  set page(fill: {_rgb(t['bg'])})
  set text(fill: {_rgb(t['text'])})
  set block(spacing: 0pt)
  set par(spacing: 0em)

  {section_badge(section, t['muted'])}
  v(6pt)
  text(weight: "bold", size: 18pt, fill: {_rgb(t['text'])})[{_esc_content(title)}]
  v(10pt)

  {self._body_block(body, footnote)}
}}"""

    # -- Split slide -------------------------------------------------------

    def _split_slide(self, d: dict) -> str:
        t = self.t
        section = d.get("section", "")
        title = d.get("title", "")
        left_title = d.get("left_title", "")
        left_items = _ensure_string_items(d.get("left_items", []))
        right_title = d.get("right_title", "")
        right_items = _ensure_string_items(d.get("right_items", []))

        left_bullets = "\n      ".join(f"- {_esc_rich(item, t['accent'])}" for item in left_items[:self.MAX_BULLETS])
        right_bullets = "\n      ".join(f"- {_esc_rich(item, t['accent'])}" for item in right_items[:self.MAX_BULLETS])

        body = f"""grid(
    columns: (1fr, 1fr),
    gutter: 20pt,
    block(
      fill: {_rgb(t['card_fill'])},
      stroke: 0.75pt + {_rgb(t['border'])},
      radius: 3pt,
      inset: 14pt,
      width: 100%,
    )[
      #text(weight: "bold", size: 14pt, fill: {_rgb(t['text'])})[#upper[{_esc(left_title)}]]
      #v(8pt)
      #text(size: 11pt, fill: {_rgb(t['muted'])})[
        {left_bullets}
      ]
    ],
    block(
      fill: {_rgb(t['accent'])},
      radius: 3pt,
      inset: 14pt,
      width: 100%,
    )[
      #text(weight: "bold", size: 14pt, fill: {_rgb(t['title_fg'])})[#upper[{_esc(right_title)}]]
      #v(8pt)
      #text(size: 11pt, fill: {_rgb(t['title_fg'])})[
        {right_bullets}
      ]
    ],
  )"""

        return f"""#{{
  set page(fill: {_rgb(t['bg'])})
  set text(fill: {_rgb(t['text'])})
  set block(spacing: 0pt)
  set par(spacing: 0em)

  {section_badge(section, t['muted'])}
  v(6pt)
  {slide_title(title, t['text'])}
  v(14pt)

  {self._body_block(body, '')}
}}"""

    # -- Chart slide (image embed) -----------------------------------------

    def _chart_slide(self, d: dict) -> str:
        t = self.t
        section = d.get("section", "")
        title = d.get("title", "")
        image_path = d.get("image_path", "")
        footnote = d.get("footnote", "")

        # 8.2cm: BODY_H_CM(9.0) - FOOTER_H_CM(0.69) = 8.31cm available for content;
        # use 8.2cm to leave ~0.1cm breathing room before the footer bar.
        body = f"""align(center, {self._image_markup(image_path, width="90%", height="8.2cm")})"""

        return f"""#{{
  set page(fill: {_rgb(t['bg'])})
  set text(fill: {_rgb(t['text'])})
  set block(spacing: 0pt)
  set par(spacing: 0em)

  {section_badge(section, t['muted'])}
  v(6pt)
  {slide_title(title, t['text'])}
  v(14pt)

  {self._body_block(body, footnote)}
}}"""

    # -- Bar chart slide (native Typst) ------------------------------------

    def _bar_chart_slide(self, d: dict) -> str:
        t = self.t
        section = d.get("section", "")
        title = d.get("title", "")
        bars = d.get("bars", [])[:self.MAX_BARS]
        footnote = d.get("footnote", "")

        accent = t.get("accent", "#6366F1")
        bar_markups = []
        for i, b in enumerate(bars):
            bar_markups.append(bar_row(b["label"], b["value"], b["pct"], accent, t["muted"]))

        bars_str = "\n  ".join(bar_markups)

        body = f"""{bars_str}"""

        return f"""#{{
  set page(fill: {_rgb(t['bg'])})
  set text(fill: {_rgb(t['text'])})
  set block(spacing: 0pt)
  set par(spacing: 0em)

  {section_badge(section, t['muted'])}
  v(6pt)
  {slide_title(title, t['text'])}
  v(14pt)

  {self._body_block(body, footnote)}
}}"""

    # -- KPI strip slide ---------------------------------------------------

    def _kpi_strip_slide(self, d: dict) -> str:
        t = self.t
        section = d.get("section", "")
        title = d.get("title", "")
        kpis = d.get("kpis", [])  # [{"value": ..., "label": ..., "highlight": bool}, ...]
        footnote = d.get("footnote", "")

        from inkline.typst.components import kpi_card
        kpi_markups = []
        for k in kpis:
            fill = t["accent"] if k.get("highlight") else t["card_fill"]
            text_color = t["title_fg"] if k.get("highlight") else t["text"]
            kpi_markups.append(kpi_card(k["value"], k["label"], fill, text_color))

        kpis_str = ",\n    ".join(kpi_markups)
        n_cols = len(kpi_markups)
        vertical = d.get("vertical", False)

        if vertical:
            body = f"""v(1fr)
  stack(
    spacing: 8pt,
    {kpis_str}
  )"""
        else:
            body = f"""v(1fr)
  grid(
    columns: ({', '.join(['1fr'] * n_cols)}),
    gutter: 8pt,
    {kpis_str}
  )"""

        return f"""#{{
  set page(fill: {_rgb(t['bg'])})
  set text(fill: {_rgb(t['text'])})
  set block(spacing: 0pt)
  set par(spacing: 0em)

  {section_badge(section, t['muted'])}
  v(6pt)
  {slide_title(title, t['text'])}
  v(20pt)

  {self._body_block(body, footnote)}
}}"""

    # -- Closing slide -----------------------------------------------------

    def _closing_slide(self, d: dict) -> str:
        t = self.t
        name = d.get("name", "")
        role = d.get("role", "")
        email = d.get("email", "")
        company = d.get("company", t.get("name", ""))
        tagline = d.get("tagline", "")
        cta = d.get("cta", "")
        website = d.get("website", "")
        heading_font = t.get("heading_font", "Inter")
        logo_path = t.get("logo_light_path", "")

        has_contact = any([name, role, email])

        if has_contact:
            # Full closing: company + tagline + optional CTA + contact block
            cta_block = (
                f'#v(0.5cm)\n    '
                f'#text(weight: "bold", size: 16pt, fill: {_rgb(t["accent"])})[{_esc(cta)}]\n    '
                if cta else ""
            )
            name_block = (
                f'#v(0.6cm)\n    '
                f'#block(fill: {_rgb(t["accent"])}, inset: (x: 14pt, y: 6pt), radius: 4pt)['
                f'#text(weight: "bold", size: 14pt, fill: white)[{_esc(name)}]]\n    '
                if name else ""
            )
            role_block = (
                f'#v(0.3cm)\n    #text(size: 10pt, fill: {_rgb(t["muted"])})[{_esc(role)}]\n    '
                if role else ""
            )
            email_block = (
                f'#v(2pt)\n    #text(size: 10pt, weight: "bold", fill: {_rgb(t["accent2"])})[{_esc(email)}]\n    '
                if email else ""
            )
            website_block = (
                f'#v(6pt)\n    #text(size: 10pt, fill: {_rgb(t["muted"])})[{_esc(website)}]\n    '
                if website else ""
            )
            contact_section = f"{cta_block}{name_block}{role_block}{email_block}{website_block}"
        else:
            # Minimal closing: no contact — just brand + tagline + decorative accent line
            cta_text = cta or tagline
            contact_section = (
                f'#v(0.8cm)\n    '
                f'#line(length: 6cm, stroke: 2pt + {_rgb(t["accent"])})\n    '
                f'#v(0.4cm)\n    '
                f'#text(size: 14pt, fill: {_rgb(t["muted"])})[{_esc(cta_text)}]\n    '
                if cta_text else
                f'#v(0.8cm)\n    #line(length: 6cm, stroke: 2pt + {_rgb(t["accent"])})\n    '
            )

        return f"""#page(
  fill: {_rgb(t['title_bg'])},
  margin: (top: 1.4cm, bottom: 1.2cm, left: 1.6cm, right: 1.6cm),
  header: none,
  footer: none,
)[
  #set text(fill: {_rgb(t['title_fg'])})

  #v(1fr)
  #align(center)[
    {f'#image("{logo_path}", width: 1.5cm)#v(0.2cm)' if logo_path else ''}
    #text(weight: "bold", size: 36pt, font: "{heading_font}", tracking: -1pt)[#upper[{_esc(company)}]]
    #v(0.3cm)
    #text(size: 16pt, fill: {_rgb(t['muted'])})[{_esc(tagline)}]
    {contact_section}
  ]

  #v(1fr)

  // Bottom — confidentiality
  #align(center)[
    #text(size: 8pt, weight: "bold", tracking: 1pt, fill: {_rgb(t['muted'])})[{_esc(t.get('confidentiality', ''))}]
  ]
]"""


    # -- Section divider ---------------------------------------------------

    def _section_divider_slide(self, d: dict) -> str:
        """Full-bleed accent page used to separate major deck sections.

        data: title (required), subtitle? (optional tagline)
        """
        t = self.t
        title = d.get("title", "")
        subtitle = d.get("subtitle", "")
        heading_font = t.get("heading_font", "Inter")

        return f"""#page(
  fill: {_rgb(t['accent'])},
  margin: (top: 1.4cm, bottom: 1.2cm, left: 1.6cm, right: 1.6cm),
  header: none,
  footer: none,
)[
  #set text(fill: white)
  #v(1fr)
  #align(horizon)[
    #text(weight: "bold", size: 40pt, font: "{heading_font}", tracking: -0.5pt)[{_esc(title)}]
    {f'#v(0.5cm)#text(size: 14pt, fill: white.transparentize(25%))[{_esc(subtitle)}]' if subtitle else ''}
  ]
  #v(1fr)
]"""

    # ==================================================================
    # INFOGRAPHIC SLIDE TYPES
    # ==================================================================

    # -- Timeline slide ----------------------------------------------------

    def _timeline_slide(self, d: dict) -> str:
        """Horizontal timeline with milestones.

        data: section, title, milestones [{date, label, desc?}], footnote
        """
        t = self.t
        section = d.get("section", "")
        title = d.get("title", "")
        milestones = d.get("milestones", [])[:self.MAX_TIMELINE_NODES]
        footnote = d.get("footnote", "")

        n = len(milestones)
        if n == 0:
            return self._content_slide(d)

        # Build milestone nodes — bubbles bottom-aligned on timeline
        # Structure: date label above, bubble centred on line, text below
        max_bubble = max((m.get("size", 14) for m in milestones), default=14)

        above_nodes = []  # date + bubble (above the line)
        below_nodes = []  # label + desc (below the line)

        for i, m in enumerate(milestones):
            date = _esc(m.get("date", ""))
            label = _esc(m.get("label", ""))
            desc = _esc(m.get("desc", ""))
            bubble_size = m.get("size", 14)
            bubble_pt = f"{bubble_size}pt"
            opacity = 0.4 + (0.6 * i / max(n - 1, 1))

            # Above: date + spacer + bubble (bubble bottom-aligned)
            above_nodes.append(f"""align(center)[
        #v(1fr)
        #text(size: 8pt, weight: "bold", fill: {_rgb(t['accent'])})[{date}]
        #v(4pt)
        #block(
          fill: {_rgb(t['accent'])}.transparentize({int((1-opacity)*100)}%),
          radius: 50%,
          width: {bubble_pt},
          height: {bubble_pt},
        )[]
      ]""")

            # Below: label + desc (top-aligned)
            below_nodes.append(f"""align(center)[
        #text(size: 9pt, weight: "bold", fill: {_rgb(t['text'])})[{label}]
        {f'#v(1pt)#text(size: 8pt, fill: {_rgb(t["muted"])})[{desc}]' if desc else ''}
      ]""")

        cols = ", ".join(["1fr"] * n)
        above_str = ",\n    ".join(above_nodes)
        below_str = ",\n    ".join(below_nodes)

        body = f"""v(1fr)

  // Above timeline: dates + bubbles (bottom-aligned to line)
  block(height: {max_bubble + 30}pt, width: 100%)[
    #grid(
      columns: ({cols}),
      rows: (100%,),
      gutter: 4pt,
      {above_str}
    )
  ]

  // Timeline line
  line(length: 100%, stroke: 2pt + {_rgb(t['border'])})

  // Below timeline: labels + descriptions (top-aligned)
  v(6pt)
  grid(
    columns: ({cols}),
    gutter: 4pt,
    {below_str}
  )

  v(1fr)"""

        return f"""#{{
  set page(fill: {_rgb(t['bg'])})
  set text(fill: {_rgb(t['text'])})
  set block(spacing: 0pt)
  set par(spacing: 0em)

  {section_badge(section, t['muted'])}
  v(6pt)
  {slide_title(title, t['text'])}

  {self._body_block(body, footnote)}
}}"""

    # -- Process flow slide ------------------------------------------------

    def _process_flow_slide(self, d: dict) -> str:
        """Numbered step sequence with arrows.

        data: section, title, steps [{number, title, desc}], footnote
        """
        t = self.t
        section = d.get("section", "")
        title = d.get("title", "")
        steps = d.get("steps", [])[:self.MAX_PROCESS_STEPS]
        footnote = d.get("footnote", "")

        if not steps:
            return self._content_slide(d)

        # Build step blocks with arrows between them
        step_blocks = []
        for i, step in enumerate(steps):
            num = step.get("number", str(i + 1))
            step_title = _esc(step.get("title", ""))
            desc = _esc(step.get("desc", ""))

            block_str = f"""block(
        fill: {_rgb(t['card_fill'])},
        stroke: 0.75pt + {_rgb(t['border'])},
        radius: 4pt,
        inset: 10pt,
        width: 100%,
      )[
        #align(center)[
          #block(
            fill: {_rgb(t['accent'])},
            radius: 50%,
            width: 28pt,
            height: 28pt,
            inset: 4pt,
          )[#align(center + horizon, text(weight: "bold", size: 14pt, fill: {_rgb(t['title_fg'])})[{_esc(num)}])]
          #v(6pt)
          #text(weight: "bold", size: 11pt, fill: {_rgb(t['text'])})[#upper[{step_title}]]
          #v(3pt)
          #text(size: 9pt, fill: {_rgb(t['muted'])})[{desc}]
        ]
      ]"""
            step_blocks.append(block_str)

            # Add arrow between steps (not after last)
            if i < len(steps) - 1:
                step_blocks.append(
                    f'align(center + horizon, text(size: 20pt, fill: {_rgb(t["accent"])})[\\u{{2192}}])'
                )

        n_cols = len(steps) * 2 - 1  # steps + arrows
        cols = []
        for i in range(n_cols):
            cols.append("0.5fr" if i % 2 == 1 else "1fr")  # arrows get less space
        cols_str = ", ".join(cols)
        blocks_str = ",\n    ".join(step_blocks)

        body = f"""v(1fr)

  grid(
    columns: ({cols_str}),
    gutter: 6pt,
    {blocks_str}
  )

  v(1fr)"""

        return f"""#{{
  set page(fill: {_rgb(t['bg'])})
  set text(fill: {_rgb(t['text'])})
  set block(spacing: 0pt)
  set par(spacing: 0em)

  {section_badge(section, t['muted'])}
  v(6pt)
  {slide_title(title, t['text'])}

  {self._body_block(body, footnote)}
}}"""

    # -- Icon stat slide ---------------------------------------------------

    # Mapping of LLM-friendly text names → Unicode emoji.
    # LLMs often produce names like "chart-bar" instead of emoji characters;
    # this table ensures they render as actual glyphs in Typst.
    _ICON_NAME_TO_EMOJI: dict[str, str] = {
        # Finance / business
        "money": "💰", "dollar": "💵", "chart": "📊", "chart-bar": "📊",
        "chart-line": "📈", "trending-up": "📈", "trending-down": "📉",
        "briefcase": "💼", "bank": "🏦", "handshake": "🤝",
        # Oil & gas / energy
        "oil": "🛢", "oil-drum": "🛢", "oil-barrel": "🛢", "barrel": "🛢",
        "flame": "🔥", "fire": "🔥", "gas": "⛽", "drill": "⛏",
        "pipeline": "🔧", "platform": "🏗", "offshore": "⚓",
        # Status
        "warning": "⚠️", "alert": "⚠️", "error": "❌", "critical": "🔴",
        "check": "✅", "tick": "✅", "success": "✅", "ok": "✅",
        "info": "ℹ️", "question": "❓",
        # Awards / metrics
        "trophy": "🏆", "award": "🏆", "star": "⭐", "medal": "🥇",
        "target": "🎯", "bullseye": "🎯",
        # General
        "clock": "⏱", "calendar": "📅", "pin": "📌", "map": "🗺",
        "gear": "⚙️", "settings": "⚙️", "rocket": "🚀", "flag": "🚩",
        "lock": "🔒", "key": "🔑", "shield": "🛡", "eye": "👁",
        "people": "👥", "person": "👤", "team": "👥",
        "building": "🏢", "home": "🏠", "location": "📍",
        "document": "📄", "file": "📁", "search": "🔍",
        "phone": "📞", "email": "📧", "globe": "🌍",
    }

    def _icon_stat_slide(self, d: dict) -> str:
        """Big number + emoji/icon + label — statistical infographic style.

        data: section, title, stats [{value, icon, label, desc?}], footnote
        """
        t = self.t
        section = d.get("section", "")
        title = d.get("title", "")
        stats = d.get("stats", [])
        footnote = d.get("footnote", "")

        if not stats:
            return self._content_slide(d)

        # Brand discipline: ALL stat values use the SINGLE brand accent.
        # Variation is by ICON, not by colour. A multi-coloured row of stats
        # is the visual equivalent of mixed fonts.
        stat_blocks = []
        for i, s in enumerate(stats):
            value = _esc(s.get("value", ""))
            raw_icon = s.get("icon", "")
            # Resolve text icon names (e.g. "chart-bar") to emoji glyphs.
            icon = self._ICON_NAME_TO_EMOJI.get(
                raw_icon.lower().strip(), raw_icon
            ) if isinstance(raw_icon, str) and raw_icon else raw_icon
            label = _esc(s.get("label", ""))
            desc = _esc(s.get("desc", ""))

            # Auto-scale value font: shorter values get larger text
            val_len = len(value.replace("\\#", "#").replace("\\$", "$"))
            if val_len <= 4:
                val_size = 36
            elif val_len <= 7:
                val_size = 28
            else:
                val_size = 22

            stat_blocks.append(f"""block(
        fill: {_rgb(t['card_fill'])},
        stroke: 0.75pt + {_rgb(t['border'])},
        radius: 4pt,
        inset: 12pt,
        width: 100%,
      )[
        #align(center)[
          {f'#text(size: 24pt)[{_esc_content(icon)}]#v(4pt)' if icon else ''}
          #text(weight: "bold", size: {val_size}pt, fill: {_rgb(t['accent'])})[{value}]
          #v(4pt)
          #text(weight: "bold", size: 9pt, fill: {_rgb(t['muted'])})[#upper[{label}]]
          {f'#v(2pt)#text(size: 8pt, fill: {_rgb(t["muted"])})[{desc}]' if desc else ''}
        ]
      ]""")

        n = len(stat_blocks)
        cols_str = ", ".join(["1fr"] * n)
        blocks_str = ",\n    ".join(stat_blocks)

        body = f"""v(1fr)

  grid(
    columns: ({cols_str}),
    gutter: 14pt,
    {blocks_str}
  )

  v(1fr)"""

        return f"""#{{
  set page(fill: {_rgb(t['bg'])})
  set text(fill: {_rgb(t['text'])})
  set block(spacing: 0pt)
  set par(spacing: 0em)

  {section_badge(section, t['muted'])}
  v(6pt)
  {slide_title(title, t['text'])}

  {self._body_block(body, footnote)}
}}"""

    # -- Progress bars slide -----------------------------------------------

    def _progress_bars_slide(self, d: dict) -> str:
        """Labelled percentage bars — skill bars, completion, ratings.

        data: section, title, bars [{label, pct, value?}], footnote
        """
        t = self.t
        section = d.get("section", "")
        title = d.get("title", "")
        bars = d.get("bars", [])[:self.MAX_PROGRESS_BARS]
        footnote = d.get("footnote", "")

        if not bars:
            return self._content_slide(d)

        # Brand discipline: ALL progress bars use the SINGLE brand accent
        # colour. Variation is by FILL PERCENTAGE, not hue. A roadmap is
        # one programme, not six unrelated initiatives in different colours.
        bar_rows = []
        for i, b in enumerate(bars):
            label = _esc(b.get("label", ""))
            pct = b.get("pct", 0)
            value = _esc(b.get("value", f"{pct}%"))

            bar_rows.append(f"""  grid(
    columns: (4cm, 1fr, 1.5cm),
    gutter: 8pt,
    align(right + horizon, text(size: 10pt, weight: "bold", fill: {_rgb(t['text'])})[{label}]),
    block(width: 100%, height: 16pt, fill: {_rgb(t['card_fill'])}, stroke: 0.5pt + {_rgb(t['border'])}, radius: 3pt)[
      #block(width: {pct}%, height: 100%, fill: {_rgb(t['accent'])}, radius: 3pt)[]
    ],
    align(left + horizon, text(size: 10pt, weight: "bold", fill: {_rgb(t['accent'])})[{value}]),
  )""")

        bars_str = "\n  v(4pt)\n  ".join(bar_rows)

        return f"""#{{
  set page(fill: {_rgb(t['bg'])})
  set text(fill: {_rgb(t['text'])})
  set block(spacing: 0pt)
  set par(spacing: 0em)

  {section_badge(section, t['muted'])}
  v(6pt)
  {slide_title(title, t['text'])}
  v(8pt)

  {self._body_block(bars_str, footnote)}
}}"""

    # -- Pyramid slide -----------------------------------------------------

    def _pyramid_slide(self, d: dict) -> str:
        """3-5 tier hierarchy pyramid.

        data: section, title, tiers [{label, desc?}] (top to bottom), footnote
        """
        t = self.t
        section = d.get("section", "")
        title = d.get("title", "")
        tiers = d.get("tiers", [])[:self.MAX_PYRAMID_TIERS]
        footnote = d.get("footnote", "")

        if not tiers:
            return self._content_slide(d)

        colors = t.get("chart_colors", [t["accent"]])
        n = len(tiers)
        tier_blocks = []
        for i, tier in enumerate(tiers):
            label = _esc(tier.get("label", ""))
            desc = _esc(tier.get("desc", ""))
            color = colors[i % len(colors)]
            # Each tier gets wider — top is narrowest
            width_pct = 30 + (i * (70 // n))

            tier_blocks.append(f"""  align(center, block(
    fill: {_rgb(color)},
    radius: 3pt,
    inset: (x: 12pt, y: 6pt),
    width: {width_pct}%,
  )[
    #align(center)[
      #text(weight: "bold", size: 11pt, fill: white)[#upper[{label}]]
      {f'#v(2pt)#text(size: 9pt, fill: white.transparentize(30%))[{desc}]' if desc else ''}
    ]
  ])""")

        tiers_str = "\n  v(4pt)\n".join(tier_blocks)

        body = f"""v(1fr)

{tiers_str}

  v(1fr)"""

        return f"""#{{
  set page(fill: {_rgb(t['bg'])})
  set text(fill: {_rgb(t['text'])})
  set block(spacing: 0pt)
  set par(spacing: 0em)

  {section_badge(section, t['muted'])}
  v(6pt)
  {slide_title(title, t['text'])}

  {self._body_block(body, footnote)}
}}"""

    # -- Comparison slide --------------------------------------------------

    def _comparison_slide(self, d: dict) -> str:
        """Structured side-by-side comparison with metrics.

        data: section, title, left {name, items [{label, value}]},
              right {name, items [{label, value}]}, footnote
        """
        t = self.t
        section = d.get("section", "")
        title = d.get("title", "")
        left = d.get("left", {})
        right = d.get("right", {})
        footnote = d.get("footnote", "")

        left_name = _esc(left.get("name", "Option A"))
        right_name = _esc(right.get("name", "Option B"))
        left_items = left.get("items", [])
        right_items = right.get("items", [])

        # Build comparison rows (cap to fit on slide)
        left_items = left_items[:self.MAX_COMPARISON_ROWS]
        right_items = right_items[:self.MAX_COMPARISON_ROWS]
        rows = []
        max_rows = max(len(left_items), len(right_items))

        # Auto-shrink: more rows → smaller font + tighter inset + less spacing
        if max_rows <= 4:
            row_font, row_inset, row_gap = 10, 8, "4pt"
        elif max_rows <= 6:
            row_font, row_inset, row_gap = 9, 6, "3pt"
        else:
            row_font, row_inset, row_gap = 8, 5, "2pt"

        for i in range(max_rows):
            l_item = left_items[i] if i < len(left_items) else {}
            r_item = right_items[i] if i < len(right_items) else {}
            l_label = _esc(l_item.get("label", "") if isinstance(l_item, dict) else str(l_item))
            l_value = _esc(l_item.get("value", "") if isinstance(l_item, dict) else "")
            r_label = _esc(r_item.get("label", "") if isinstance(r_item, dict) else str(r_item))
            r_value = _esc(r_item.get("value", "") if isinstance(r_item, dict) else "")

            fill = _rgb(t['card_fill']) if i % 2 == 0 else _rgb(t['bg'])
            rows.append(f"""    grid(
      columns: (1fr, 1fr),
      gutter: 14pt,
      block(fill: {fill}, inset: {row_inset}pt, width: 100%, radius: 2pt)[
        #text(size: {row_font}pt, fill: {_rgb(t['muted'])})[{l_label}]
        {f'#h(1fr)#text(size: {row_font}pt, weight: "bold", fill: {_rgb(t["text"])})[{l_value}]' if l_value else ''}
      ],
      block(fill: {fill}, inset: {row_inset}pt, width: 100%, radius: 2pt)[
        #text(size: {row_font}pt, fill: {_rgb(t['muted'])})[{r_label}]
        {f'#h(1fr)#text(size: {row_font}pt, weight: "bold", fill: {_rgb(t["text"])})[{r_value}]' if r_value else ''}
      ],
    )""")

        rows_str = f"\n    v({row_gap})\n".join(rows)

        body = f"""// Column headers
  grid(
    columns: (1fr, 1fr),
    gutter: 14pt,
    block(fill: {_rgb(t['card_fill'])}, stroke: (bottom: 2pt + {_rgb(t['accent'])}), inset: 10pt, width: 100%)[
      #align(center, text(weight: "bold", size: 14pt, fill: {_rgb(t['accent'])})[#upper[{left_name}]])
    ],
    block(fill: {_rgb(t['accent'])}, inset: 10pt, width: 100%, radius: (top: 3pt))[
      #align(center, text(weight: "bold", size: 14pt, fill: {_rgb(t['title_fg'])})[#upper[{right_name}]])
    ],
  )
  v(6pt)

  // Comparison rows
  {rows_str}"""

        return f"""#{{
  set page(fill: {_rgb(t['bg'])})
  set text(fill: {_rgb(t['text'])})
  set block(spacing: 0pt)
  set par(spacing: 0em)

  {section_badge(section, t['muted'])}
  v(6pt)
  {slide_title(title, t['text'])}
  v(14pt)

  {self._body_block(body, footnote)}
}}"""

    # ==================================================================
    # MULTI-EXHIBIT SLIDE TYPES (info-dense, brochure-style)
    # ==================================================================

    # -- Feature grid (3x2 = 6 features) -----------------------------------

    def _feature_grid_slide(self, d: dict) -> str:
        """3x2 grid of feature cards with icon + title + body.

        data: section, title, features [{icon, title, body}], footnote
        Use this for: capability showcases, "what we offer", feature catalogs.
        Better than four_card when you have 5-6 items.
        """
        t = self.t
        section = d.get("section", "")
        title = d.get("title", "")
        features = d.get("features", [])[:6]
        footnote = d.get("footnote", "")

        if not features:
            return self._content_slide(d)

        # Brand discipline: ALL number badges use the single brand accent
        # colour, NOT a rainbow. Best practice: 2-3 colour brand system.
        cells = []
        for i, f in enumerate(features):
            icon = f.get("icon", "")
            f_title = _esc(f.get("title", ""))
            f_body = _esc(f.get("body", ""))

            cells.append(f"""block(
        fill: {_rgb(t['card_fill'])},
        stroke: 0.75pt + {_rgb(t['border'])},
        radius: 4pt,
        inset: 12pt,
        width: 100%,
      )[
        #grid(
          columns: (auto, 1fr),
          gutter: 8pt,
          block(fill: {_rgb(t['accent'])}, radius: 50%, width: 24pt, height: 24pt, inset: 4pt)[
            #align(center + horizon, text(weight: "bold", size: 11pt, fill: white)[{i+1}])
          ],
          text(weight: "bold", size: 11pt, fill: {_rgb(t['text'])})[#upper[{f_title}]],
        )
        #v(4pt)
        #text(size: 9pt, fill: {_rgb(t['muted'])})[{f_body}]
      ]""")

        # Pad to 6 cells with empty blocks for clean grid
        while len(cells) < 6:
            cells.append('block(width: 100%)[]')

        cells_str = ",\n    ".join(cells)

        body = f"""v(1fr)

  grid(
    columns: (1fr, 1fr, 1fr),
    gutter: 10pt,
    {cells_str}
  )

  v(1fr)"""

        return f"""#{{
  set page(fill: {_rgb(t['bg'])})
  set text(fill: {_rgb(t['text'])})
  set block(spacing: 0pt)
  set par(spacing: 0em)

  {section_badge(section, t['muted'])}
  v(6pt)
  {slide_title(title, t['text'])}
  v(10pt)

  {self._body_block(body, footnote)}
}}"""

    # -- Dashboard slide (chart + stats + bullets) -------------------------

    def _dashboard_slide(self, d: dict) -> str:
        """Multi-exhibit slide: chart image (left 60%) + stats stack (right 40%).

        data: section, title, image_path, stats [{value, label}], bullets [str], footnote
        The brochure-style "everything on one page" layout.
        """
        t = self.t
        section = d.get("section", "")
        title = d.get("title", "")
        image_path = d.get("image_path", "")
        stats = d.get("stats", [])[:3]
        bullets = d.get("bullets", [])[:4]
        footnote = d.get("footnote", "")

        # Build stat blocks for the right column (compact for dashboard layout)
        stat_blocks = []
        for s in stats:
            stat_blocks.append(f"""block(
        fill: {_rgb(t['card_fill'])},
        stroke: (left: 3pt + {_rgb(t['accent'])}),
        inset: 8pt,
        width: 100%,
      )[
        #text(weight: "bold", size: 18pt, fill: {_rgb(t['accent'])})[{_esc(s.get('value', ''))}]
        #h(8pt)
        #text(size: 8pt, fill: {_rgb(t['muted'])})[#upper[{_esc(s.get('label', ''))}]]
      ]""")

        # Limit bullets to 3 to ensure right column fits
        bullets = bullets[:3]
        bullets_str = "\n        ".join(f"- {_esc(b)}" for b in bullets)
        stats_str = ",\n      ".join(stat_blocks) if stat_blocks else 'block()[]'

        body = f"""grid(
    columns: (1.55fr, 1fr),
    gutter: 14pt,
    block(width: 100%)[
      #align(center + horizon, {self._image_markup(image_path, width="100%", height="6.2cm")})
    ],
    block(width: 100%)[
      #stack(
        spacing: 4pt,
        {stats_str}
      )
      {f'#v(6pt)#text(size: 8pt, fill: {_rgb(t["text"])})[{chr(10)}        {bullets_str}{chr(10)}      ]' if bullets else ''}
    ],
  )"""

        return f"""#{{
  set page(fill: {_rgb(t['bg'])})
  set text(fill: {_rgb(t['text'])})
  set block(spacing: 0pt)
  set par(spacing: 0em)

  {section_badge(section, t['muted'])}
  v(6pt)
  {slide_title(title, t['text'])}
  v(8pt)

  {self._body_block(body, footnote)}
}}"""

    # -- Multi-chart slide — 2-4 exhibits in configurable grid ------------

    def _multi_chart_slide(self, d: dict) -> str:
        """Multiple chart images arranged in a configurable grid layout.

        Supports asymmetric proportions and 2-row arrangements, modelled on
        institutional bank presentation patterns (Pareto, Goldman Sachs, McKinsey).

        data:
          section: str
          title: str
          layout: one of:
            "equal_2"        — two equal columns (50/50)
            "equal_3"        — three equal columns (33/33/33)
            "equal_4"        — four equal columns (25/25/25/25)
            "hero_left"      — two columns 65/35
            "hero_left_3"    — three columns 50/25/25 (hero + 2 small)
            "hero_right_3"   — three columns 25/25/50 (2 small + hero)
            "quad"           — 2×2 grid (4 charts, equal)
            "top_bottom"     — 1 wide chart top + up to 3 charts below
            "three_top_wide" — 3 equal charts top (45%) + 1 wide chart bottom (55%)
            "left_stack"     — 1 wide hero left (3fr) + 2 stacked charts right (2fr)
            "right_stack"    — 2 stacked charts left (2fr) + 1 wide hero right (3fr)
            "mosaic_5"       — 2 charts top row (50%) + 3 charts bottom row (50%)
            "six_grid"       — 3×2 grid of 6 equal charts
          charts: list of {image_path, title?}   (2–6 charts depending on layout)
          footnote: str
        """
        t = self.t
        section = d.get("section", "")
        title = d.get("title", "")
        layout = d.get("layout", "equal_2")
        charts = d.get("charts", [])
        footnote = d.get("footnote", "")

        def _chart_cell(c: dict, height: str | None = None) -> str:
            """Render a single chart cell.

            height: Typst dimension string (e.g. "4.3cm") for the image slot.
            When None, the image fills width=100% at its natural aspect ratio
            (correct when the matplotlib figure was pre-sized to match the slot).
            """
            img = c.get("image_path", "")
            ctitle = _esc(c.get("title", ""))
            # Use width: 100% + natural height when pre-sized; otherwise constrain.
            if height is not None:
                img_block = self._image_markup(img, height=height, width="100%", fit='"contain"')
            else:
                img_block = self._image_markup(img, width="100%")
            if ctitle:
                return f"""block(width: 100%)[
      #text(weight: "bold", size: 9pt, fill: {_rgb(t['text'])})[{ctitle}]
      #v(4pt)
      #align(center, {img_block})
    ]"""
            return f'block(width: 100%)[#align(center + horizon, {img_block})]'

        # Retrieve pre-computed slot heights from module-level constants.
        # These match the matplotlib figsize sent by _auto_render_charts so images
        # fill their slots exactly — no letterboxing, no empty space.
        _slots = MULTI_CHART_SLOT_SIZES.get(layout, [])
        def _slot_h(idx: int) -> str:
            """Return Typst height string for chart slot at index."""
            if idx < len(_slots):
                return f"{_slots[idx][1]:.2f}cm"
            return "9.0cm"  # fallback

        # Layout → Typst grid column specification
        LAYOUTS = {
            "equal_2":      ("(1fr, 1fr)", 2),
            "equal_3":      ("(1fr, 1fr, 1fr)", 3),
            "equal_4":      ("(1fr, 1fr, 1fr, 1fr)", 4),
            "hero_left":    ("(2fr, 1fr)", 2),
            "hero_left_3":  ("(2fr, 1fr, 1fr)", 3),
            "hero_right_3": ("(1fr, 1fr, 2fr)", 3),
        }

        if layout == "quad":
            # 2×2 grid — 4 charts in two rows of two
            charts = charts[:4]
            while len(charts) < 4:
                charts.append({})
            # All quad slots have the same height
            quad_h = _slot_h(0)
            cells = ",\n    ".join(_chart_cell(c, height=quad_h) for c in charts)
            grid_body = f"""grid(
    columns: (1fr, 1fr),
    rows: (auto, auto),
    gutter: 10pt,
    {cells},
  )"""

        elif layout == "top_bottom":
            # Top: single wide chart; Bottom: up to 3 equal charts
            top = charts[:1]
            bottom = charts[1:4]
            n_bot = max(len(bottom), 1)
            bot_cols = "(" + ", ".join(["1fr"] * n_bot) + ",)"
            # Slot heights from table (index 0 = top, index 1+ = bottom)
            top_h = _slot_h(0)
            bot_h = _slot_h(min(1, len(_slots) - 1))  # all bottom cells same height
            top_cell = _chart_cell(top[0], height=top_h) if top else "block(width: 100%)[]"
            bot_cells = ",\n      ".join(_chart_cell(c, height=bot_h) for c in bottom)
            bot_grid = f"""grid(
      columns: {bot_cols},
      gutter: 10pt,
      {bot_cells},
    )""" if bottom else ""
            grid_body = f"""stack(
    spacing: 8pt,
    {top_cell},
    {bot_grid}
  )"""

        elif layout == "three_top_wide":
            # 3 equal charts on top (45% height) + 1 full-width chart on bottom (55%)
            charts = charts[:4]
            while len(charts) < 4:
                charts.append({})
            top_h = _slot_h(0)   # same for indices 0-2
            bot_h = _slot_h(3)
            top_cells = ",\n      ".join(_chart_cell(c, height=top_h) for c in charts[:3])
            bot_cell = _chart_cell(charts[3], height=bot_h) if charts[3] else "block(width:100%)[]"
            grid_body = f"""stack(
    spacing: 8pt,
    grid(
      columns: (1fr, 1fr, 1fr),
      gutter: 10pt,
      {top_cells},
    ),
    {bot_cell}
  )"""

        elif layout == "left_stack":
            # Wide left chart (3fr) + 2 stacked right charts (2fr)
            charts = charts[:3]
            while len(charts) < 3:
                charts.append({})
            left_h = _slot_h(0)
            right_h = _slot_h(1)  # both right cells same height
            left_cell = _chart_cell(charts[0], height=left_h)
            right_top = _chart_cell(charts[1], height=right_h)
            right_bot = _chart_cell(charts[2], height=right_h)
            grid_body = f"""grid(
    columns: (3fr, 2fr),
    gutter: 12pt,
    {left_cell},
    stack(
      spacing: 10pt,
      {right_top},
      {right_bot},
    ),
  )"""

        elif layout == "right_stack":
            # 2 stacked left charts (2fr) + wide right chart (3fr)
            charts = charts[:3]
            while len(charts) < 3:
                charts.append({})
            left_h = _slot_h(0)   # both left cells same height
            right_h = _slot_h(2)
            left_top = _chart_cell(charts[0], height=left_h)
            left_bot = _chart_cell(charts[1], height=left_h)
            right_cell = _chart_cell(charts[2], height=right_h)
            grid_body = f"""grid(
    columns: (2fr, 3fr),
    gutter: 12pt,
    stack(
      spacing: 10pt,
      {left_top},
      {left_bot},
    ),
    {right_cell},
  )"""

        elif layout == "mosaic_5":
            # Row of 2 charts (top 50%) + row of 3 charts (bottom 50%)
            charts = charts[:5]
            while len(charts) < 5:
                charts.append({})
            top_h = _slot_h(0)   # indices 0-1
            bot_h = _slot_h(2)   # indices 2-4
            top_cells = ",\n      ".join(_chart_cell(c, height=top_h) for c in charts[:2])
            bot_cells = ",\n      ".join(_chart_cell(c, height=bot_h) for c in charts[2:5])
            grid_body = f"""stack(
    spacing: 8pt,
    grid(
      columns: (1fr, 1fr),
      gutter: 10pt,
      {top_cells},
    ),
    grid(
      columns: (1fr, 1fr, 1fr),
      gutter: 10pt,
      {bot_cells},
    ),
  )"""

        elif layout == "six_grid":
            # 3×2 grid: 6 equal charts
            charts = charts[:6]
            while len(charts) < 6:
                charts.append({})
            cell_h = _slot_h(0)  # all cells equal
            cells = ",\n    ".join(_chart_cell(c, height=cell_h) for c in charts)
            grid_body = f"""grid(
    columns: (1fr, 1fr, 1fr),
    rows: (auto, auto),
    gutter: 10pt,
    {cells},
  )"""

        else:
            col_spec, n_expected = LAYOUTS.get(layout, ("(1fr, 1fr)", 2))
            charts = charts[:n_expected]
            # Each chart in a single-row layout gets the same height
            cells = ",\n    ".join(
                _chart_cell(c, height=_slot_h(i)) for i, c in enumerate(charts)
            )
            grid_body = f"""grid(
    columns: {col_spec},
    gutter: 12pt,
    {cells},
  )"""

        return f"""#{{
  set page(fill: {_rgb(t['bg'])})
  set text(fill: {_rgb(t['text'])})
  set block(spacing: 0pt)
  set par(spacing: 0em)

  {section_badge(section, t['muted'])}
  v(6pt)
  text(weight: "bold", size: 18pt, fill: {_rgb(t['text'])})[{_esc_content(title)}]
  v(8pt)

  {self._body_block(grid_body, footnote)}
}}"""

    # -- Chart slide with side caption -------------------------------------

    def _chart_caption_slide(self, d: dict) -> str:
        """Embedded chart image (left 65%) + supporting bullets (right 35%).

        data: section, title, image_path, caption, bullets [str], footnote
        Use this when a chart needs context — better than bare chart slide.
        """
        t = self.t
        section = d.get("section", "")
        title = d.get("title", "")
        image_path = d.get("image_path", "")
        caption = _esc(d.get("caption", ""))
        bullets = d.get("bullets", [])[:5]
        footnote = d.get("footnote", "")

        bullets_str = "\n        ".join(f"- {_esc(b)}" for b in bullets)

        body = f"""grid(
    columns: (2.2fr, 1fr),
    rows: (7.5cm,),
    gutter: 12pt,
    block(width: 100%, height: 100%)[
      #align(center + horizon, {self._image_markup(image_path, height="95%", width="95%", fit='"contain"')})
    ],
    block(
      fill: {_rgb(t['card_fill'])},
      stroke: (left: 4pt + {_rgb(t['accent'])}),
      inset: 10pt,
      width: 100%,
      height: 100%,
    )[
      #text(weight: "bold", size: 9pt, tracking: 1pt, fill: {_rgb(t['accent'])})[#upper[Key takeaways]]
      #v(6pt)
      #text(size: 8.5pt, fill: {_rgb(t['text'])})[
        {bullets_str}
      ]
      {f'#v(4pt)#text(size: 7pt, style: "italic", fill: {_rgb(t["muted"])})[{caption}]' if caption else ''}
    ],
  )"""

        return f"""#{{
  set page(fill: {_rgb(t['bg'])})
  set text(fill: {_rgb(t['text'])})
  set block(spacing: 0pt)
  set par(spacing: 0em)

  {section_badge(section, t['muted'])}
  v(6pt)
  {slide_title(title, t['text'])}
  v(10pt)

  {self._body_block(body, footnote)}
}}"""

    # -- Credentials (tombstone grid) slide --------------------------------

    def _credentials_slide(self, d: dict) -> str:
        """Grid of 4-8 tombstone cells (track record / deal history).

        data: section, title, tombstones [{name, detail}], footnote
        """
        t = self.t
        section = d.get("section", "")
        title = d.get("title", "")
        tombstones = d.get("tombstones", [])[:8]
        footnote = d.get("footnote", "")

        if not tombstones:
            return self._content_slide(d)

        n = len(tombstones)
        # Determine grid columns: 3 cols for ≤6 items, 4 cols for 7-8 items
        n_cols = 3 if n <= 6 else 4
        col_spec = "(" + ", ".join(["1fr"] * n_cols) + ",)"

        cells = []
        for tb in tombstones:
            name = _esc(tb.get("name", ""))
            detail = _esc(tb.get("detail", ""))
            cell = (
                f"block("
                f"  fill: {_rgb(t['card_fill'])},"
                f"  stroke: (top: 3pt + {_rgb(t['accent'])}),"
                f"  inset: 10pt,"
                f"  width: 100%,"
                f"  height: 100%,"
                f")[\n"
                f"  #text(weight: \"bold\", size: 11pt, fill: {_rgb(t['text'])})[{name}]\n"
                f"  #v(4pt)\n"
                f"  #text(size: 9pt, fill: {_rgb(t['muted'])})[{detail}]\n"
                f"]"
            )
            cells.append(cell)

        cells_str = ",\n    ".join(cells)
        grid_body = f"""grid(
  columns: {col_spec},
  rows: (auto,),
  gutter: 8pt,
  {cells_str},
)"""

        return f"""#{{
  set page(fill: {_rgb(t['bg'])})
  set text(fill: {_rgb(t['text'])})
  set block(spacing: 0pt)
  set par(spacing: 0em)

  {section_badge(section, t['muted'])}
  v(6pt)
  {slide_title(title, t['text'])}
  v(8pt)

  {self._body_block(grid_body, footnote)}
}}"""

    # -- Testimonial (pull-quote) slide ------------------------------------

    # -- Team grid (management team bios) slide ---------------------------

    def _team_grid_slide(self, d: dict) -> str:
        """Management team / advisory board bio grid.

        2-3 members → single row.  4 members → 2×2 grid.

        data: section, title, members [{name, role, bio, image_path?, logos?}], footnote?

        image_path resolution (same as chart slides):
          - absolute path  → used as-is
          - relative path  → resolved under self._image_root (charts/ dir)
          - None / missing → initials placeholder circle
        Logo path uses identical resolution; missing logos are silently skipped.
        """
        from pathlib import Path

        t = self.t
        section = d.get("section", "")
        title = d.get("title", "")
        footnote = d.get("footnote", "")
        members = d.get("members", [])[:4]
        n = len(members)
        if n == 0:
            return self._content_slide(d)

        # Headshot and logo sizes depend on member count
        if n == 4:
            photo_pt = 100
        elif n == 2:
            photo_pt = 130
        else:
            photo_pt = 120  # 3 members (most common)

        def _resolve_img(path: str | None) -> str | None:
            """Return resolved absolute path string, or None if not found / not provided."""
            if not path:
                return None
            p = Path(path)
            if p.is_absolute():
                return str(p) if p.exists() else None
            if self._image_root:
                candidate = Path(self._image_root) / path
                if candidate.exists():
                    return str(candidate)
            return None

        def _initials(name: str) -> str:
            """Extract up to 2 initials from a name."""
            parts = name.strip().split()
            if len(parts) >= 2:
                return (parts[0][0] + parts[-1][0]).upper()
            return name[:2].upper() if name else "?"

        def _member_card(m: dict, compact: bool) -> str:
            """Render one member card as Typst markup."""
            name = _esc(m.get("name", ""))
            role = _esc(m.get("role", ""))
            bio = _esc(m.get("bio", ""))
            image_path = m.get("image_path")
            logos = m.get("logos", []) or []

            p_pt = photo_pt - 20 if compact else photo_pt
            p_cm_str = f"{p_pt / 28.35:.2f}cm"  # convert pt → cm for Typst

            resolved_img = _resolve_img(image_path)

            if resolved_img:
                photo_markup = (
                    f'box(width: {p_cm_str}, height: {p_cm_str}, clip: true, radius: 4pt)[\n'
                    f'  #image("{resolved_img}", width: {p_cm_str}, height: {p_cm_str}, fit: "cover")\n'
                    f']'
                )
            else:
                # Initials circle placeholder
                initials = _initials(m.get("name", ""))
                photo_markup = (
                    f'circle(radius: {p_pt / 2}pt, fill: {_rgb(t["accent"])})[#align(center + horizon)['
                    f'#text(weight: "bold", size: {max(12, p_pt // 5)}pt, fill: white)[{initials}]]]'
                )

            # Logo strip — only render logos that resolve to an existing file
            logo_items = []
            for logo_path in logos[:4]:
                resolved_logo = _resolve_img(logo_path)
                if resolved_logo:
                    logo_items.append(
                        f'image("{resolved_logo}", height: 16pt, fit: "contain")'
                    )

            logo_strip = ""
            if logo_items:
                logos_str = ", ".join(logo_items)
                logo_strip = (
                    f'\n  #v(4pt)\n'
                    f'  #line(length: 100%, stroke: 0.5pt + {_rgb(t["border"])})\n'
                    f'  #v(4pt)\n'
                    f'  #grid(columns: ({", ".join(["auto"] * len(logo_items))}), gutter: 8pt, {logos_str})\n'
                )

            return (
                f'block(width: 100%, inset: 8pt)[\n'
                f'  #align(center)[#{{' + photo_markup + f'}}]\n'
                f'  #v(6pt)\n'
                f'  #align(center)[#text(weight: "bold", size: 14pt, fill: {_rgb(t["text"])})[{name}]]\n'
                f'  #v(2pt)\n'
                f'  #align(center)[#text(size: 10pt, fill: {_rgb(t["accent"])}, style: "italic")[{role}]]\n'
                f'  #v(4pt)\n'
                f'  #text(size: 9pt, fill: {_rgb(t["muted"])})[{bio}]'
                + logo_strip +
                f'\n]'
            )

        if n == 4:
            # 2×2 grid
            cells = [_member_card(m, compact=True) for m in members]
            grid_body = (
                f'grid(\n'
                f'  columns: (1fr, 1fr),\n'
                f'  gutter: 10pt,\n'
                f'  {cells[0]},\n'
                f'  {cells[1]},\n'
                f'  {cells[2]},\n'
                f'  {cells[3]},\n'
                f')'
            )
        else:
            # Single row: 2 or 3 members
            cols = ", ".join(["1fr"] * n)
            cards_str = ",\n    ".join(_member_card(m, compact=False) for m in members)
            grid_body = (
                f'grid(\n'
                f'  columns: ({cols}),\n'
                f'  gutter: 14pt,\n'
                f'  {cards_str},\n'
                f')'
            )

        body = f"v(1fr)\n\n  {grid_body}\n\n  v(1fr)"

        return f"""#{{
  set page(fill: {_rgb(t['bg'])})
  set text(fill: {_rgb(t['text'])})
  set block(spacing: 0pt)
  set par(spacing: 0em)

  {section_badge(section, t['muted'])}
  v(6pt)
  {slide_title(title, t['text'])}

  {self._body_block(body, footnote)}
}}"""

    def _testimonial_slide(self, d: dict) -> str:
        """Large pull-quote with attribution.

        data: section, quote, attribution, image_path?, footnote?
        """
        t = self.t
        section = d.get("section", "")
        quote = _esc(d.get("quote", ""))
        attribution = _esc(d.get("attribution", ""))
        footnote = d.get("footnote", "")
        heading_font = t.get("heading_font", "Inter")

        body = f"""align(center + horizon)[
  text(size: 11pt, fill: {_rgb(t['muted'])})[{section_badge(section, t['muted'])}]
  v(1fr)
  text(size: 10pt, fill: {_rgb(t['accent'])}, tracking: 2pt)[\u201c]
  v(4pt)
  block(width: 85%)[
    #align(center)[
      #text(weight: "bold", size: 22pt, font: "{heading_font}", fill: {_rgb(t['text'])}, style: "italic")[{quote}]
    ]
  ]
  v(4pt)
  text(size: 10pt, fill: {_rgb(t['accent'])}, tracking: 2pt)[\u201d]
  v(12pt)
  align(center)[
    #text(size: 11pt, fill: {_rgb(t['muted'])})[{attribution}]
  ]
  v(1fr)
  {footer_bar(footnote, t['border'], t['muted'])}
]"""

        return f"""#{{
  set page(fill: {_rgb(t['bg'])})
  set text(fill: {_rgb(t['text'])})
  set block(spacing: 0pt)
  set par(spacing: 0em)
  {body}
}}"""

    # -- Before/After (two-panel transformation) slide --------------------

    def _before_after_slide(self, d: dict) -> str:
        """Two equal panels: Before (left) and After (right).

        data: section, title, left {label, items, colour?}, right {label, items, colour?}, footnote?
        """
        t = self.t
        section = d.get("section", "")
        title = d.get("title", "")
        footnote = d.get("footnote", "")

        def _resolve_colour(key: str) -> str:
            colour_map = {
                "accent": t.get("accent", "#3B82F6"),
                "warning": "#F59E0B",
                "muted": t.get("muted", "#64748B"),
                "error": "#EF4444",
                "success": "#10B981",
            }
            return colour_map.get(key, t.get("accent", "#3B82F6"))

        def _panel(side_data: dict, is_right: bool) -> str:
            label = _esc(side_data.get("label", "Before" if not is_right else "After"))
            items = side_data.get("items", [])[:5]
            colour_key = side_data.get("colour", "accent" if is_right else "muted")
            colour = _resolve_colour(colour_key)
            items_str = "\n    ".join(f"- {_esc(str(item))}" for item in items)
            bg_fill = t.get("card_fill", "#F8FAFC")
            stroke_side = "right" if not is_right else "left"
            return (
                f"block("
                f"  fill: {_rgb(bg_fill)},"
                f"  stroke: ({stroke_side}: 4pt + {_rgb(colour)}),"
                f"  inset: (top: 10pt, bottom: 10pt, left: 12pt, right: 12pt),"
                f"  width: 100%,"
                f"  height: 100%,"
                f")[\n"
                f"  #text(weight: \"bold\", size: 13pt, fill: {_rgb(colour)})[{label}]\n"
                f"  #v(8pt)\n"
                f"  #list(indent: 6pt, {', '.join(repr(_esc(str(it))) for it in items)})\n"
                f"]"
            )

        left_panel = _panel(d.get("left", {}), is_right=False)
        right_panel = _panel(d.get("right", {}), is_right=True)

        body = f"""grid(
  columns: (1fr, 1fr),
  rows: (auto,),
  gutter: 16pt,
  {left_panel},
  {right_panel},
)"""

        return f"""#{{
  set page(fill: {_rgb(t['bg'])})
  set text(fill: {_rgb(t['text'])})
  set block(spacing: 0pt)
  set par(spacing: 0em)

  {section_badge(section, t['muted'])}
  v(6pt)
  {slide_title(title, t['text'])}
  v(10pt)

  {self._body_block(body, footnote)}
}}"""


def _esc(text) -> str:
    """Escape special Typst characters.

    Handles non-string types gracefully (dicts, lists, numbers)
    by converting to string first.
    """
    if not text:
        return ""
    if isinstance(text, dict):
        # Use semicolons (not commas) to avoid breaking Typst grid arguments
        name = text.get("title") or text.get("name") or text.get("well") or text.get("action") or text.get("risk") or ""
        detail = text.get("body") or text.get("detail") or text.get("value") or text.get("status") or ""
        if name and detail:
            text = f"{name} — {detail}"
        elif name:
            text = name
        else:
            text = "; ".join(f"{k}: {v}" for k, v in text.items())
    elif not isinstance(text, str):
        text = str(text)
    # Strip LLM-style \$ escaping before our Typst escaping runs.
    text = text.replace("\\$", "$")
    return (
        text
        .replace("\\", "\\\\")
        .replace("#", "\\#")
        .replace("$", "\\$")
        .replace("@", "\\@")
        .replace("<", "\\<")
        .replace(">", "\\>")
        .replace("[", "\\[")
        .replace("]", "\\]")
    )


def _esc_rich(text: str, accent_color: str = "#1A7FA0") -> str:
    """Escape for Typst AND parse **bold** markdown into Typst bold markup.

    **text** → #text(weight: "bold", fill: rgb("#accent"))[text]
    """
    import re
    parts = re.split(r'\*\*(.+?)\*\*', str(text))
    out = []
    for j, part in enumerate(parts):
        if j % 2 == 0:
            out.append(_esc(part))
        else:
            out.append(
                f'#text(weight: "bold", fill: rgb("{accent_color}")[{_esc(part)}]'
            )
    return "".join(out)


def _ensure_string_items(items: list) -> list:
    """Normalize a list of mixed str/dict items into plain strings.

    Extracts meaningful display strings from dict items using common
    key patterns (title/body, name/detail, risk/severity, etc.).
    """
    result = []
    for item in items:
        if isinstance(item, str):
            result.append(item)
        elif isinstance(item, dict):
            name = item.get("title") or item.get("name") or item.get("well") or item.get("action") or item.get("risk") or ""
            detail = item.get("body") or item.get("detail") or item.get("value") or item.get("status") or ""
            severity = item.get("severity") or item.get("priority") or ""
            if name and detail:
                result.append(f"{name} — {detail}")
            elif name and severity:
                result.append(f"{name} [{severity}]")
            elif name:
                result.append(name)
            else:
                result.append("; ".join(f"{k}: {v}" for k, v in item.items()))
        else:
            result.append(str(item))
    return result
