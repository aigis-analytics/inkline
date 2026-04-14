"""Automated design pattern extractor from PDF reference decks.

Analyses slide layouts, chart types, colour usage and typography patterns
from a PDF file and produces:
  1. A structured ``DeckAnalysis`` object
  2. A human-readable Markdown summary (same format as design_inspiration_analysis.md)
  3. Candidate decision-matrix rules that can be reviewed and promoted

Requires: pymupdf (fitz) — ``pip install pymupdf``

Usage::

    from inkline.intelligence.deck_analyser import DeckAnalyser
    analyser = DeckAnalyser()
    analysis = analyser.analyse("/path/to/deck.pdf", deck_name="my_deck")
    print(analysis.summary_markdown())
    analysis.save("~/.config/inkline/reference_decks/my_deck/")
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

_CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "inkline"

# ---------------------------------------------------------------------------
# Chart type detection heuristics (from drawing path analysis)
# Each entry: (detector_fn, chart_type_label)
# Detectors receive (drawings, blocks, page_width, page_height) and return bool
# ---------------------------------------------------------------------------

def _has_vertical_bars(drawings, blocks, w, h):
    """Multiple filled rectangles at similar y-origin, varying widths."""
    rects = [d for d in drawings if d.get("type") == "f" and d.get("rect")]
    if len(rects) < 3:
        return False
    # Look for rect clusters with similar bottom-y coords
    bottoms = []
    for r in rects:
        rect = r["rect"]
        if len(rect) == 4:
            bottoms.append(rect[3])  # y1 (bottom)
    if not bottoms:
        return False
    mean_bottom = sum(bottoms) / len(bottoms)
    close = sum(1 for b in bottoms if abs(b - mean_bottom) < h * 0.05)
    return close >= 3


def _has_horizontal_bars(drawings, blocks, w, h):
    """Multiple filled rectangles anchored at similar x-origin."""
    rects = [d for d in drawings if d.get("type") == "f" and d.get("rect")]
    if len(rects) < 3:
        return False
    lefts = []
    for r in rects:
        rect = r["rect"]
        if len(rect) == 4:
            lefts.append(rect[0])
    if not lefts:
        return False
    mean_left = sum(lefts) / len(lefts)
    close = sum(1 for l in lefts if abs(l - mean_left) < w * 0.04)
    return close >= 3


def _has_donut(drawings, blocks, w, h):
    """Large circle path + smaller inner circle (donut) pattern."""
    curves = [d for d in drawings if d.get("type") in ("c", "curve")]
    return len(curves) >= 2


def _has_line_chart(drawings, blocks, w, h):
    """Connected line segments with many points (polyline signature)."""
    lines = [d for d in drawings if d.get("type") == "l"]
    return len(lines) >= 8


def _has_scatter(drawings, blocks, w, h):
    """Multiple small circles scattered across the chart area."""
    small_curves = [
        d for d in drawings
        if d.get("type") in ("c", "curve")
        and d.get("rect")
        and (d["rect"][2] - d["rect"][0]) < w * 0.05
    ]
    return len(small_curves) >= 4


def _has_heatmap(drawings, blocks, w, h):
    """Grid of filled rectangles with varying colours (heatmap signature)."""
    rects = [d for d in drawings if d.get("type") == "f" and d.get("rect")]
    if len(rects) < 6:
        return False
    # Check if rects form a regular grid
    xs = set(round(r["rect"][0] / 5) * 5 for r in rects if len(r.get("rect", [])) == 4)
    ys = set(round(r["rect"][1] / 5) * 5 for r in rects if len(r.get("rect", [])) == 4)
    return len(xs) >= 2 and len(ys) >= 2 and len(xs) * len(ys) >= 6


def _has_gantt(drawings, blocks, w, h):
    """Multiple wide horizontal bars stacked vertically."""
    rects = [d for d in drawings if d.get("type") == "f" and d.get("rect")]
    wide_horizontal = [
        r for r in rects
        if len(r.get("rect", [])) == 4
        and (r["rect"][2] - r["rect"][0]) > w * 0.2   # width > 20% of page
        and (r["rect"][3] - r["rect"][1]) < h * 0.08  # height < 8% of page
    ]
    return len(wide_horizontal) >= 2


def _has_dumbbell(drawings, blocks, w, h):
    """Two small circles connected by a line — repeated pattern."""
    small_circles = [
        d for d in drawings
        if d.get("type") in ("c", "curve")
        and d.get("rect")
        and (d["rect"][2] - d["rect"][0]) < w * 0.04
    ]
    lines = [d for d in drawings if d.get("type") == "l"]
    return len(small_circles) >= 4 and len(lines) >= 2


CHART_DETECTORS = [
    (_has_heatmap,       "heatmap"),
    (_has_gantt,         "gantt"),
    (_has_dumbbell,      "dumbbell"),
    (_has_donut,         "donut"),
    (_has_line_chart,    "line_chart"),
    (_has_scatter,       "scatter"),
    (_has_horizontal_bars, "horizontal_bar"),
    (_has_vertical_bars, "grouped_bar"),
]

# Chart type → data_structure mapping
CHART_TO_DATA_STRUCTURE = {
    "grouped_bar":     "n_categories_one_value",
    "horizontal_bar":  "n_categories_one_value",
    "stacked_bar":     "n_categories_composition",
    "line_chart":      "n_categories_time_series",
    "area_chart":      "n_categories_time_series",
    "donut":           "part_of_whole",
    "pie":             "part_of_whole",
    "waterfall":       "n_categories_composition",
    "scatter":         "two_continuous_variables",
    "heatmap":         "matrix_rows_cols",
    "gantt":           "steps_over_time",
    "dumbbell":        "two_values_comparison",
    "scoring_matrix":  "matrix_rows_cols",
    "multi_timeline":  "steps_over_time",
    "entity_flow":     "network_relationships",
}

# Chart type → likely message_type
CHART_TO_MESSAGE_TYPE = {
    "grouped_bar":     "ranking_or_comparison",
    "horizontal_bar":  "ranking_or_comparison",
    "stacked_bar":     "part_of_whole_breakdown",
    "line_chart":      "change_over_time",
    "area_chart":      "change_over_time",
    "donut":           "part_of_whole_breakdown",
    "pie":             "part_of_whole_breakdown",
    "waterfall":       "waterfall_bridge",
    "scatter":         "concentration_or_outlier",
    "heatmap":         "density_or_intensity",
    "gantt":           "parallel_workstreams",
    "dumbbell":        "change_over_time",
    "scoring_matrix":  "capability_comparison",
    "multi_timeline":  "process_or_sequence",
    "entity_flow":     "hierarchical_structure",
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class SlideAnalysis:
    page: int
    width: float
    height: float
    layout_class: str      # "chart_slide" | "text_heavy" | "kpi_strip" | etc.
    chart_types: list[str]
    colour_palette: list[str]
    text_structure: list[str]   # ordered list of text blocks (largest font first)
    whitespace_ratio: float     # 0.0–1.0
    label_strategy: str         # "legend" | "direct" | "none"


@dataclass
class DeckAnalysis:
    deck_name: str
    pdf_path: str
    slide_count: int
    slides: list[SlideAnalysis]
    global_palette: list[str]
    dominant_layouts: dict[str, int]   # layout_class → count
    chart_vocabulary: dict[str, int]   # chart_type → count
    dm_candidates: list[dict] = field(default_factory=list)

    def summary_markdown(self) -> str:
        """Generate a human-readable pattern summary in design_inspiration_analysis.md format."""
        lines = [
            f"# Design Pattern Analysis: {self.deck_name}",
            "",
            f"**Source:** {self.pdf_path}",
            f"**Slides analysed:** {self.slide_count}",
            "",
            "---",
            "",
            "## Layout Distribution",
            "",
        ]
        for layout, count in sorted(self.dominant_layouts.items(), key=lambda x: -x[1]):
            lines.append(f"- **{layout}**: {count} slides ({100*count//self.slide_count}%)")
        lines += [
            "",
            "---",
            "",
            "## Chart Vocabulary",
            "",
        ]
        for ctype, count in sorted(self.chart_vocabulary.items(), key=lambda x: -x[1]):
            dm_struct = CHART_TO_DATA_STRUCTURE.get(ctype, "—")
            dm_msg = CHART_TO_MESSAGE_TYPE.get(ctype, "—")
            lines.append(f"- **{ctype}** × {count}: data=`{dm_struct}`, message=`{dm_msg}`")
        lines += [
            "",
            "---",
            "",
            "## Colour Palette",
            "",
            ", ".join(f"`{c}`" for c in self.global_palette[:8]),
            "",
            "---",
            "",
            "## Decision Matrix Candidates",
            "",
            "| data_structure | message_type | chart_type | confidence |",
            "|---|---|---|---|",
        ]
        for cand in self.dm_candidates:
            lines.append(
                f"| {cand['data_structure']} | {cand['message_type']} "
                f"| {cand['chart_type']} | {cand['confidence']:.2f} |"
            )
        lines.append("")
        return "\n".join(lines)

    def save(self, output_dir: str | Path) -> Path:
        """Save analysis.yaml + patterns.md to output_dir."""
        out = Path(output_dir).expanduser()
        out.mkdir(parents=True, exist_ok=True)

        # Save YAML analysis
        yaml_path = out / "analysis.json"
        with open(yaml_path, "w", encoding="utf-8") as f:
            json.dump({
                "deck_name": self.deck_name,
                "pdf_path": self.pdf_path,
                "slide_count": self.slide_count,
                "dominant_layouts": self.dominant_layouts,
                "chart_vocabulary": self.chart_vocabulary,
                "global_palette": self.global_palette,
                "dm_candidates": self.dm_candidates,
            }, f, indent=2, ensure_ascii=False)

        # Save human-readable markdown
        md_path = out / "patterns.md"
        md_path.write_text(self.summary_markdown(), encoding="utf-8")

        log.info("Deck analysis saved to %s", out)
        return out


# ---------------------------------------------------------------------------
# Main analyser
# ---------------------------------------------------------------------------

class DeckAnalyser:
    """Automated design pattern extractor from PDF reference decks."""

    def analyse(self, pdf_path: str | Path, deck_name: str = "") -> DeckAnalysis:
        """Analyse a PDF deck and return a DeckAnalysis object."""
        try:
            import fitz  # pymupdf
        except ImportError:
            raise ImportError(
                "pymupdf is required for deck analysis. "
                "Install it with: pip install pymupdf"
            )

        pdf_path = Path(pdf_path)
        if not deck_name:
            deck_name = pdf_path.stem

        doc = fitz.open(str(pdf_path))
        slides: list[SlideAnalysis] = []

        for page_num, page in enumerate(doc):
            try:
                slide = self._analyse_page(page, page_num + 1)
                slides.append(slide)
            except Exception as e:
                log.warning("Page %d analysis failed: %s", page_num + 1, e)

        doc.close()

        # Aggregate across slides
        layout_counts: dict[str, int] = {}
        chart_counts: dict[str, int] = {}
        all_colours: list[str] = []

        for s in slides:
            layout_counts[s.layout_class] = layout_counts.get(s.layout_class, 0) + 1
            for ct in s.chart_types:
                chart_counts[ct] = chart_counts.get(ct, 0) + 1
            all_colours.extend(s.colour_palette)

        global_palette = self._top_colours(all_colours, n=8)
        dm_candidates = self._extract_dm_candidates(slides, deck_name)

        return DeckAnalysis(
            deck_name=deck_name,
            pdf_path=str(pdf_path),
            slide_count=len(slides),
            slides=slides,
            global_palette=global_palette,
            dominant_layouts=layout_counts,
            chart_vocabulary=chart_counts,
            dm_candidates=dm_candidates,
        )

    def _analyse_page(self, page: Any, page_num: int) -> SlideAnalysis:
        """Analyse one page and return a SlideAnalysis."""
        w = page.rect.width
        h = page.rect.height
        blocks = page.get_text("dict")["blocks"]
        drawings = page.get_drawings()

        chart_types = self._detect_chart_types(drawings, blocks, w, h)
        layout_class = self._classify_layout(blocks, drawings, chart_types, w, h)
        palette = self._extract_palette(drawings)
        text_structure = self._extract_text_structure(blocks)
        whitespace = self._calc_whitespace(blocks, drawings, w, h)
        label_strategy = self._detect_label_strategy(drawings, blocks, w, h)

        return SlideAnalysis(
            page=page_num,
            width=w,
            height=h,
            layout_class=layout_class,
            chart_types=chart_types,
            colour_palette=palette,
            text_structure=text_structure,
            whitespace_ratio=whitespace,
            label_strategy=label_strategy,
        )

    def _detect_chart_types(self, drawings, blocks, w, h) -> list[str]:
        """Run all chart detectors and return matches."""
        found = []
        for detector_fn, label in CHART_DETECTORS:
            try:
                if detector_fn(drawings, blocks, w, h):
                    found.append(label)
            except Exception:
                pass
        return found

    def _classify_layout(self, blocks, drawings, chart_types, w, h) -> str:
        """Classify the overall slide layout."""
        has_images = any(b.get("type") == 1 for b in blocks)
        text_blocks = [b for b in blocks if b.get("type") == 0]
        total_text_area = sum(
            (b["bbox"][2] - b["bbox"][0]) * (b["bbox"][3] - b["bbox"][1])
            for b in text_blocks if "bbox" in b
        )
        page_area = w * h

        if chart_types:
            return "chart_slide"
        if has_images and total_text_area < page_area * 0.2:
            return "visual_anchor"
        if total_text_area > page_area * 0.4:
            return "text_heavy"
        if len(text_blocks) >= 6:
            block_heights = [
                b["bbox"][3] - b["bbox"][1]
                for b in text_blocks if "bbox" in b
            ]
            avg_h = sum(block_heights) / len(block_heights) if block_heights else 0
            if avg_h < h * 0.05:
                return "kpi_strip"
        return "mixed"

    def _extract_palette(self, drawings) -> list[str]:
        """Extract dominant hex colours from drawing fills."""
        colour_counts: dict[str, int] = {}
        for d in drawings:
            fill = d.get("fill")
            if fill and isinstance(fill, (list, tuple)) and len(fill) >= 3:
                r, g, b = fill[:3]
                hex_col = f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
                # Skip near-white and near-black (background/text noise)
                brightness = (r + g + b) / 3
                if 0.05 < brightness < 0.95:
                    colour_counts[hex_col] = colour_counts.get(hex_col, 0) + 1
        return [c for c, _ in sorted(colour_counts.items(), key=lambda x: -x[1])[:5]]

    def _extract_text_structure(self, blocks) -> list[str]:
        """Return text content ordered by font size (largest first)."""
        text_items = []
        for b in blocks:
            if b.get("type") != 0:
                continue
            for line in b.get("lines", []):
                for span in line.get("spans", []):
                    text = span.get("text", "").strip()
                    size = span.get("size", 0)
                    if text:
                        text_items.append((size, text))
        text_items.sort(reverse=True)
        return [t for _, t in text_items[:10]]

    def _calc_whitespace(self, blocks, drawings, w, h) -> float:
        """Estimate fraction of page that is empty space."""
        page_area = w * h
        used_area = 0.0
        for b in blocks:
            bbox = b.get("bbox", [])
            if len(bbox) == 4:
                used_area += (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
        for d in drawings:
            rect = d.get("rect", [])
            if len(rect) == 4:
                used_area += (rect[2] - rect[0]) * (rect[3] - rect[1])
        whitespace = max(0.0, 1.0 - min(1.0, used_area / page_area))
        return round(whitespace, 2)

    def _detect_label_strategy(self, drawings, blocks, w, h) -> str:
        """Detect whether chart labels use direct labelling or legend."""
        text_blocks = [b for b in blocks if b.get("type") == 0]
        # If there are text blocks near the chart perimeter → direct labels
        if len(text_blocks) > 6:
            return "direct"
        if drawings:
            return "legend"
        return "none"

    def _top_colours(self, all_colours: list[str], n: int = 8) -> list[str]:
        """Return the most common n colours across the whole deck."""
        counts: dict[str, int] = {}
        for c in all_colours:
            counts[c] = counts.get(c, 0) + 1
        return [c for c, _ in sorted(counts.items(), key=lambda x: -x[1])[:n]]

    def _extract_dm_candidates(self, slides: list[SlideAnalysis], deck_name: str) -> list[dict]:
        """Convert detected chart types into candidate DM rules."""
        candidates = []
        for slide in slides:
            for chart_type in slide.chart_types:
                data_structure = CHART_TO_DATA_STRUCTURE.get(chart_type, "unknown")
                message_type = CHART_TO_MESSAGE_TYPE.get(chart_type, "unknown")
                if data_structure == "unknown" or message_type == "unknown":
                    continue
                # Check for duplicate candidate
                existing = next(
                    (c for c in candidates
                     if c["data_structure"] == data_structure
                     and c["message_type"] == message_type
                     and c["chart_type"] == chart_type),
                    None,
                )
                if existing:
                    existing["observations"] = existing.get("observations", 1) + 1
                else:
                    candidates.append({
                        "data_structure": data_structure,
                        "message_type": message_type,
                        "chart_type": chart_type,
                        "enforce": self._infer_enforce(slide, chart_type),
                        "source_deck": deck_name,
                        "source_page": slide.page,
                        "confidence": 0.50,
                        "observations": 1,
                        "status": "candidate",
                    })
        return candidates

    def _infer_enforce(self, slide: SlideAnalysis, chart_type: str) -> dict:
        """Infer mandatory parameters from observed slide characteristics."""
        enforce: dict = {}
        if chart_type in ("grouped_bar", "stacked_bar"):
            enforce["style"] = "clean"
        if chart_type in ("donut", "pie") and slide.label_strategy == "direct":
            enforce["label_style"] = "direct"
        if chart_type == "scatter" and slide.label_strategy == "direct":
            enforce["label_style"] = "annotated"
        return enforce
