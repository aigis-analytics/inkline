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
    "feature_grid": ["features"],
    "dashboard": ["bullets"],   # the limiting field — chart + 3 stats are fixed
    "chart_caption": ["bullets"],
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


# ---------------------------------------------------------------------------
# POST-RENDER VISUAL AUDIT
# ---------------------------------------------------------------------------
# After the PDF is compiled, count actual pages and compare to expected
# slide count. If they differ, content has overflowed onto extra pages.
# This is the only audit that catches real layout overflow (vs the static
# capacity audit above which is content-count-based).

def audit_rendered_pdf(pdf_path: str | Path, expected_slides: int) -> list[AuditWarning]:
    """Audit a compiled PDF: every slide must occupy exactly one page.

    Counts actual pages in the PDF and compares to expected slide count.
    Returns errors if any slides overflowed onto extra pages.
    """
    warnings: list[AuditWarning] = []
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        return warnings

    actual_pages = _count_pdf_pages(pdf_path)
    if actual_pages is None:
        return warnings

    if actual_pages > expected_slides:
        overflow = actual_pages - expected_slides
        warnings.append(AuditWarning(
            slide_index=-1,
            slide_type="deck",
            severity="error",
            message=(
                f"VISUAL OVERFLOW: deck has {expected_slides} slides but rendered "
                f"{actual_pages} pages ({overflow} slides overflow onto extra pages). "
                f"Most likely cause: a chart/grid + 2-line title combination exceeds "
                f"the slide content area. Reduce chart height, shorten titles, or "
                f"split content across multiple slides. Inspect: {pdf_path}"
            ),
        ))
    elif actual_pages < expected_slides:
        warnings.append(AuditWarning(
            slide_index=-1,
            slide_type="deck",
            severity="warn",
            message=(
                f"deck has {expected_slides} slides but only {actual_pages} pages "
                f"rendered — some slides may have been merged or are empty."
            ),
        ))

    return warnings


def audit_chart_image(image_path: str | Path) -> list[AuditWarning]:
    """Detect content touching the edge of a chart PNG (bbox clipping).

    When matplotlib renders with `bbox_inches="tight"`, labels positioned
    outside the axes can be clipped. This audit checks if any content
    pixels are touching the outer 4px border of the image — that's a
    near-certain sign of clipping.

    Returns warning(s) if the chart appears to be clipped.
    """
    warnings: list[AuditWarning] = []
    try:
        from PIL import Image
        import numpy as np
    except ImportError:
        return warnings

    image_path = Path(image_path)
    if not image_path.exists():
        return warnings

    try:
        with Image.open(image_path) as im:
            im_rgba = im.convert("RGBA")
            arr = np.array(im_rgba)
    except Exception:
        return warnings

    if arr.size == 0 or arr.shape[0] < 20 or arr.shape[1] < 20:
        return warnings

    # Detect "content" pixels — anything that's not the chart background.
    # Background is whatever colour is in the corner pixels (most chart
    # backgrounds are uniform white/off-white). A content pixel differs
    # from background by more than 25/255 in any channel.
    bg_pixel = arr[2, 2, :3].astype(int)  # near-corner sample
    diff = np.abs(arr[:, :, :3].astype(int) - bg_pixel).max(axis=2)
    content_mask = diff > 25  # boolean

    # Check the outer 4px border for content
    border = 4
    h, w = content_mask.shape
    edges_with_content = []
    if content_mask[:border, :].any():
        edges_with_content.append("top")
    if content_mask[-border:, :].any():
        edges_with_content.append("bottom")
    if content_mask[:, :border].any():
        edges_with_content.append("left")
    if content_mask[:, -border:].any():
        edges_with_content.append("right")

    if edges_with_content:
        warnings.append(AuditWarning(
            slide_index=-1,
            slide_type="chart_image",
            severity="warn",
            message=(
                f"CHART CLIPPING: {image_path.name} has content touching the "
                f"{', '.join(edges_with_content)} edge — labels or data are "
                f"likely cut off. Increase figure size, move labels inside the "
                f"plot area, or use an external legend. Inspect: {image_path}"
            ),
        ))

    return warnings


def audit_all_chart_images(charts_dir: str | Path) -> list[AuditWarning]:
    """Audit every PNG in a charts directory for edge clipping."""
    charts_dir = Path(charts_dir)
    if not charts_dir.is_dir():
        return []
    warnings: list[AuditWarning] = []
    for png in sorted(charts_dir.glob("*.png")):
        warnings.extend(audit_chart_image(png))
    return warnings


# ---------------------------------------------------------------------------
# LLM-DRIVEN VISUAL AUDIT (Claude vision)
# ---------------------------------------------------------------------------
# A real designer looks at each slide and tells you what's wrong. Claude can
# do the same — vastly more accurate than pixel-scanning heuristics. This is
# the audit that catches:
#  - Donut chart label clipping
#  - Radar chart legend overlap
#  - Multi-coloured elements that should be single-colour (brand discipline)
#  - Misalignment, weak hierarchy, awkward spacing
#  - Style inconsistency across slides

def _build_visual_audit_system() -> str:
    """Build the visual auditor system prompt with design playbooks.

    The auditor receives the SAME design knowledge as DesignAdvisor so it
    can evaluate slides against professional design principles, not just
    mechanical checks.
    """
    # Load design playbooks (same ones DesignAdvisor uses)
    playbook_context = ""
    try:
        from inkline.intelligence.playbooks import load_playbooks_for_task
        playbooks = load_playbooks_for_task("slide")
        parts = []
        for name, content in playbooks.items():
            parts.append(f"## {name.replace('_', ' ').title()}")
            # Truncate each playbook to keep prompt manageable
            lines = content.split("\n")[:60]
            parts.append("\n".join(lines))
        playbook_context = "\n\n".join(parts)
    except Exception:
        pass

    return f"""You are Inkline's Visual Auditor — an expert graphic designer reviewing \
rendered slide images before a deck ships to investors.

You evaluate slides against TWO standards:

A. MECHANICAL QUALITY (errors that break the slide)
B. DESIGN QUALITY (professional presentation design principles)

====================================================================
A. MECHANICAL QUALITY CHECKS
====================================================================

1. CLIPPING — text, chart labels, axis ticks, legends, or icons cut off \
at the edge of the slide or any container. Always ERROR.

2. OVERFLOW — content that has pushed onto a second page, leaving the slide \
visually incomplete. Always ERROR.

3. OVERLAP — legends on plots, text on text, icons on borders. ERROR.

4. MISSING CONTENT — slide title promises N items but fewer are shown \
(e.g., "8-agent mesh" but only 6 rows visible). ERROR.

====================================================================
B. DESIGN QUALITY CHECKS (consulting-grade standard)
====================================================================

5. WHITESPACE & PROPORTIONS — Is the slide using space efficiently? \
Flag: massive empty areas below compact content, charts that are too \
small for their container, narrow panels that waste vertical space. \
A chart_caption layout should have the chart filling 60-65%% of width \
and the full available height. Cards should fill their row height. WARN.

6. VISUAL HIERARCHY — Is the main message immediately clear? The title \
should state the insight (action title), not the topic. Hero numbers \
should dominate. The eye should be guided: title → exhibit → supporting \
text. Flag slides where nothing stands out. WARN.

7. CARD/BOX CONSISTENCY — In three_card, four_card, and feature_grid \
layouts: ALL cards/boxes MUST be the same height. Uneven card heights \
look unprofessional. The tallest card sets the standard. WARN if uneven.

8. BRAND DISCIPLINE — A branded deck uses a 2-3 colour system. Flag:
   - Numbered badges/icons using multiple colours (should be single accent)
   - Stats in a strip using different accent colours
   - Progress bars in different colours
   WARN. But do NOT flag: donut shades, 2-3 series comparisons, semantic colours.

9. DATA VISUALISATION QUALITY — For charts:
   - Is the key data point or company highlighted/differentiated? (e.g., in a \
     competitive landscape, the client's position should stand out via colour, \
     size, or annotation)
   - Are axis labels readable? Are they present?
   - Does the chart type match the data? (scatter for positioning, bar for \
     comparison, line for trends, donut for composition)
   WARN if the chart fails to communicate its message clearly.

10. INFOGRAPHIC > TABLE — Flag any slide that uses a plain table when an \
infographic layout would be more effective. Tables are for dense reference \
data. For 3-5 items with value/description, prefer icon_stat, process_flow, \
timeline, or bar_chart. WARN.

11. TYPOGRAPHY — Consistent font sizes, weights, families within a slide. \
Title should be bold and large. Body text should be readable (≥10pt). WARN.

12. POSITIVE — If the slide is well-designed, return []. Don't flag issues \
that aren't there.

====================================================================
DESIGN KNOWLEDGE (from playbooks — same as DesignAdvisor)
====================================================================

{playbook_context}

====================================================================
OUTPUT FORMAT
====================================================================

Return a JSON array of findings:
  {{"severity": "error|warn|info", "message": "<what's wrong, where, and how to fix>"}}

Output ONLY the JSON array. No prose, no markdown, no commentary.
Return [] for a well-designed slide."""


_VISUAL_AUDIT_SYSTEM = _build_visual_audit_system()


def audit_slide_with_llm(
    image_path: str | Path,
    *,
    slide_index: int = -1,
    slide_type: str = "",
    api_key: str | None = None,
    model: str = "claude-sonnet-4-20250514",
) -> list[AuditWarning]:
    """Send a rendered slide PNG to Claude and ask for a visual audit.

    Returns AuditWarning objects with Claude's findings. If no API key
    is available, returns empty silently.
    """
    api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return []

    image_path = Path(image_path)
    if not image_path.exists():
        return []

    try:
        import anthropic
        import base64
        import json
    except ImportError:
        return []

    img_b64 = base64.standard_b64encode(image_path.read_bytes()).decode("utf-8")

    client = anthropic.Anthropic(api_key=api_key)

    user_text = (
        f"Audit this rendered slide image (slide_index={slide_index}, "
        f"slide_type='{slide_type}'). Return JSON array of findings only."
    )

    try:
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            system=_VISUAL_AUDIT_SYSTEM,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": img_b64,
                        },
                    },
                    {"type": "text", "text": user_text},
                ],
            }],
        )
    except Exception as e:
        return [AuditWarning(
            slide_index=slide_index, slide_type=slide_type,
            severity="info",
            message=f"LLM visual audit skipped: {str(e)[:80]}",
        )]

    text = response.content[0].text.strip()
    # Strip markdown fences if present
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

    try:
        findings = json.loads(text)
    except json.JSONDecodeError:
        return []

    if not isinstance(findings, list):
        return []

    warnings: list[AuditWarning] = []
    for f in findings:
        if not isinstance(f, dict):
            continue
        sev = f.get("severity", "info")
        msg = f.get("message", "")
        if sev not in ("error", "warn", "info"):
            sev = "warn"
        if msg:
            warnings.append(AuditWarning(
                slide_index=slide_index,
                slide_type=slide_type,
                severity=sev,
                message=msg,
            ))
    return warnings


def audit_deck_with_llm(
    pdf_path: str | Path,
    slides: list[dict],
    *,
    api_key: str | None = None,
    model: str = "claude-sonnet-4-20250514",
    page_dir: str | Path | None = None,
) -> list[AuditWarning]:
    """Render each PDF page to PNG and run LLM visual audit on each.

    Uses pymupdf if available (fast), else falls back to recompiling the
    Typst source via typst.compile(format='png').
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        return []

    api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return []

    # Render PDF pages to PNGs in a temp/output dir
    if page_dir is None:
        page_dir = pdf_path.parent / f"_audit_{pdf_path.stem}"
    page_dir = Path(page_dir)
    page_dir.mkdir(parents=True, exist_ok=True)

    page_pngs = _render_pdf_pages(pdf_path, page_dir)
    if not page_pngs:
        return []

    warnings: list[AuditWarning] = []
    for i, png in enumerate(page_pngs):
        slide_type = slides[i].get("slide_type", "?") if i < len(slides) else "?"
        page_warnings = audit_slide_with_llm(
            png,
            slide_index=i + 1,
            slide_type=slide_type,
            api_key=api_key,
            model=model,
        )
        warnings.extend(page_warnings)

    return warnings


def _render_pdf_pages(pdf_path: Path, out_dir: Path) -> list[Path]:
    """Render PDF pages to PNGs. Tries pymupdf, then falls back to nothing."""
    # Try pymupdf (fitz)
    try:
        import fitz  # pymupdf
        doc = fitz.open(str(pdf_path))
        pages = []
        for i, page in enumerate(doc):
            pix = page.get_pixmap(dpi=120)
            png_path = out_dir / f"page_{i+1:02d}.png"
            pix.save(str(png_path))
            pages.append(png_path)
        doc.close()
        return pages
    except ImportError:
        pass
    except Exception:
        return []

    # No PDF→PNG library available
    return []


def extract_page_texts(pdf_path: Path) -> list[str]:
    """Extract text content from each page of a PDF.

    Returns list of strings, one per page. Empty list if no PDF reader.
    """
    try:
        import fitz
        doc = fitz.open(str(pdf_path))
        texts = [page.get_text() for page in doc]
        doc.close()
        return texts
    except ImportError:
        pass
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(pdf_path))
        return [page.extract_text() or "" for page in reader.pages]
    except ImportError:
        pass
    return []


def _count_pdf_pages(pdf_path: Path) -> int | None:
    """Count pages in a PDF. Returns None if no PDF library available."""
    # Try pypdf first
    try:
        from pypdf import PdfReader
        return len(PdfReader(str(pdf_path)).pages)
    except ImportError:
        pass
    # Try pdfplumber
    try:
        import pdfplumber
        with pdfplumber.open(str(pdf_path)) as pdf:
            return len(pdf.pages)
    except ImportError:
        pass
    # Try PyPDF2
    try:
        from PyPDF2 import PdfReader
        return len(PdfReader(str(pdf_path)).pages)
    except ImportError:
        pass
    return None


def emit_audit_report(warnings: list[AuditWarning]) -> None:
    """Print audit report directly to stderr — visible without logging config.

    This is the user-facing audit. Logging warnings get swallowed by default;
    stderr prints are always visible.
    """
    if not warnings:
        return

    import sys
    errors = [w for w in warnings if w.severity == "error"]
    warns = [w for w in warnings if w.severity == "warn"]
    infos = [w for w in warnings if w.severity == "info"]

    bar = "=" * 76
    print("", file=sys.stderr)
    print(bar, file=sys.stderr)
    print(
        f" INKLINE AUDIT  ·  {len(errors)} errors  ·  {len(warns)} warnings  ·  {len(infos)} info",
        file=sys.stderr,
    )
    print(bar, file=sys.stderr)
    for w in errors + warns + infos:
        print(f"  {w}", file=sys.stderr)
    print(bar, file=sys.stderr)
    print("", file=sys.stderr)
