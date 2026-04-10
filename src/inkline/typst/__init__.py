"""Typst output backend — slides (16:9 PDF) and documents (A4/Letter PDF).

This is Inkline's default output engine. It produces publication-quality
PDFs with embedded fonts via the Typst compiler.

Usage::

    from inkline.typst import export_typst_slides, export_typst_document

    # Slides from structured data
    export_typst_slides(
        slides=[
            {"slide_type": "title", "data": {"company": "Acme Corp", ...}},
            {"slide_type": "three_card", "data": {"section": "Problem", ...}},
        ],
        output_path="deck.pdf",
        brand="minimal",
        template="consulting",
    )

    # Document from Markdown
    export_typst_document(
        markdown="# Due Diligence Report\\n...",
        output_path="report.pdf",
        brand="minimal",
        title="DD Report",
    )
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

log = logging.getLogger(__name__)

_ASSETS_DIR = Path(__file__).parent.parent / "assets"
_FONTS_DIR = _ASSETS_DIR / "fonts"


def _verify_page_count(pdf_path: Path, expected: int) -> None:
    """Hard gate: verify rendered PDF has exactly the expected number of pages.

    If the page count doesn't match, content has overflowed onto extra pages.
    This logs a loud warning with details so the caller knows which slides
    overflowed. Does not raise — the PDF is still usable, but the caller
    should inspect and fix.
    """
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(str(pdf_path))
        actual = len(doc)
        doc.close()
    except ImportError:
        try:
            from pypdf import PdfReader
            actual = len(PdfReader(str(pdf_path)).pages)
        except ImportError:
            log.debug("No PDF reader available for page count verification")
            return

    if actual != expected:
        overflow = actual - expected
        import sys
        msg = (
            f"\n{'='*72}\n"
            f" INKLINE OVERFLOW GATE  |  {actual} pages rendered, {expected} expected\n"
            f" {overflow} slide(s) overflowed onto extra pages.\n"
            f" The PDF has been written but contains layout overflow.\n"
            f" Fix: reduce content, shorten titles, or split slides.\n"
            f"{'='*72}\n"
        )
        print(msg, file=sys.stderr)
        log.error("Page count mismatch: %d pages for %d slides", actual, expected)


def _auto_render_charts(
    slides: list[dict[str, Any]],
    brand: str,
    root: str,
) -> None:
    """Auto-render chart images requested via chart_request in slide data.

    When DesignAdvisor (LLM mode) picks a chart/chart_caption/dashboard slide,
    it embeds a ``chart_request`` dict with ``chart_type`` and ``chart_data``.
    This function renders those charts via matplotlib before Typst compilation,
    so the image files exist when the compiler needs them.
    """
    charts_to_render = []
    for slide in slides:
        data = slide.get("data", {})
        chart_req = data.get("chart_request")
        image_path = data.get("image_path")
        if chart_req and image_path:
            full_path = Path(root) / image_path
            if not full_path.exists():
                charts_to_render.append((slide, chart_req, full_path))

    if not charts_to_render:
        return

    try:
        from inkline.typst.chart_renderer import render_chart_for_brand
    except ImportError:
        log.warning("matplotlib not available — cannot auto-render %d chart(s)", len(charts_to_render))
        return

    # Determine chart dimensions based on slide type
    CHART_SIZES = {
        "chart_caption": (7.0, 3.0),
        "dashboard": (6.5, 3.4),
        "chart": (9.0, 4.5),
    }
    default_size = (7.0, 3.5)

    for slide, chart_req, full_path in charts_to_render:
        chart_type = chart_req.get("chart_type", "")
        chart_data = chart_req.get("chart_data", {})
        if not chart_type or not chart_data:
            log.warning("Skipping chart_request with missing type or data: %s", full_path.name)
            continue

        w, h = CHART_SIZES.get(slide["slide_type"], default_size)
        full_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            render_chart_for_brand(
                chart_type, chart_data, str(full_path),
                brand_name=brand, width=w, height=h,
            )
            log.info("Auto-rendered chart: %s (%s)", full_path.name, chart_type)
        except Exception as e:
            log.warning("Failed to auto-render chart %s: %s", full_path.name, e)
            # Remove the image_path so the slide doesn't reference a missing file
            slide["data"].pop("image_path", None)
            slide["data"].pop("chart_request", None)


def export_typst_slides(
    slides: list[dict[str, Any]],
    output_path: str | Path,
    *,
    brand: str = "minimal",
    template: str = "brand",
    title: str = "Untitled",
    date: str = "",
    subtitle: str = "",
    font_paths: Optional[list[str | Path]] = None,
    image_root: Optional[str | Path] = None,
    audit: bool = True,
    audit_visual: bool = True,
) -> Path:
    """Generate a slide deck PDF from structured slide specifications.

    Parameters
    ----------
    slides : list[dict]
        List of slide dicts, each with ``slide_type`` and ``data`` keys.
    output_path : Path
        Where to write the PDF.
    brand : str
        Brand name (e.g., "minimal" or any user-registered brand).
    template : str
        Slide template (e.g., "consulting", "executive", "newspaper", "brand").
    title : str
        Deck title.
    date : str
        Date string for footer.
    subtitle : str
        Optional subtitle.
    font_paths : list[Path], optional
        Additional font directories.

    Returns
    -------
    Path
        Path to the generated PDF.
    """
    from inkline.brands import get_brand
    from inkline.typst.compiler import compile_typst
    from inkline.typst.slide_renderer import DeckSpec, SlideSpec, TypstSlideRenderer
    from inkline.typst.theme_registry import brand_to_typst_theme

    # Pre-render content audit (catches static capacity issues)
    pre_warnings: list = []
    if audit:
        try:
            from inkline.intelligence.overflow_audit import audit_deck
            pre_warnings = audit_deck(slides)
        except Exception as e:
            log.debug("pre-render audit skipped: %s", e)

    brand_obj = get_brand(brand)
    theme = brand_to_typst_theme(brand_obj, template)

    output_path = Path(output_path)

    # Determine root for image resolution
    root = None
    if image_root:
        root = str(image_root)
    else:
        # Auto-detect: if any slide has image_path, use output dir as root
        for s in slides:
            if s.get("data", {}).get("image_path"):
                root = str(output_path.parent)
                break

    # Auto-render chart images requested by DesignAdvisor via chart_request
    _auto_render_charts(slides, brand, root or str(output_path.parent))

    deck_spec = DeckSpec(
        slides=[SlideSpec(slide_type=s["slide_type"], data=s.get("data", {})) for s in slides],
        title=title,
        date=date,
        subtitle=subtitle,
    )

    renderer = TypstSlideRenderer(theme)
    source = renderer.render_deck(deck_spec)

    # Collect font paths
    all_font_paths = [str(_FONTS_DIR)]
    if font_paths:
        all_font_paths.extend(str(p) for p in font_paths)

    compile_typst(source, output_path=output_path, root=root, font_paths=all_font_paths)

    # Hard gate: verify page count matches slide count (overflow detection)
    _verify_page_count(output_path, expected=len(slides))

    # Post-render audit — four layers (each catches what the others can't):
    #   1. Page count vs expected slides (catches layout overflow)
    #   2. Chart image edge clipping (deterministic PIL pixel scan)
    #   3. Static content capacity (counts items vs SLIDE_CAPACITY)
    #   4. LLM visual audit (Claude vision — the real designer's eye)
    #
    # Layer 4 is the most powerful: it catches everything the heuristics
    # miss (rainbow bars, label clipping inside slides, hierarchy issues,
    # alignment problems). Runs automatically when ANTHROPIC_API_KEY is set
    # OR when audit_visual=True is passed explicitly.
    if audit:
        try:
            from inkline.intelligence.overflow_audit import (
                audit_rendered_pdf,
                audit_chart_image,
                audit_deck_with_llm,
                emit_audit_report,
            )
            post_warnings = audit_rendered_pdf(output_path, expected_slides=len(slides))

            # Audit any embedded chart images for edge clipping
            seen_images = set()
            for s in slides:
                img = s.get("data", {}).get("image_path")
                if img and img not in seen_images:
                    seen_images.add(img)
                    if root:
                        img_path = Path(root) / img
                    else:
                        img_path = output_path.parent / img
                    if img_path.exists():
                        post_warnings.extend(audit_chart_image(img_path))

            # LLM visual audit — every page reviewed by Claude vision
            if audit_visual:
                log.info("Running LLM visual audit on %d slides...", len(slides))
                post_warnings.extend(audit_deck_with_llm(output_path, slides))

            all_warnings = pre_warnings + post_warnings
            if all_warnings:
                emit_audit_report(all_warnings)
        except Exception as e:
            log.debug("post-render audit skipped: %s", e)

    log.info("Typst slide deck written to %s", output_path)
    return output_path


def export_typst_document(
    markdown: str,
    output_path: str | Path,
    *,
    brand: str = "minimal",
    title: str = "",
    subtitle: str = "",
    date: Optional[str | datetime] = None,
    author: str = "",
    paper: str = "a4",
    sections: Optional[list[dict[str, Any]]] = None,
    font_paths: Optional[list[str | Path]] = None,
) -> Path:
    """Generate a branded document PDF from Markdown or structured sections.

    Parameters
    ----------
    markdown : str
        Markdown content. Ignored if ``sections`` is provided.
    output_path : Path
        Where to write the PDF.
    brand : str
        Brand name.
    title : str
        Document title.
    subtitle : str
        Document subtitle.
    date : str or datetime
        Document date.
    author : str
        Author name.
    paper : str
        Paper size ("a4" or "us-letter").
    sections : list[dict], optional
        Structured sections (overrides markdown).
    font_paths : list[Path], optional
        Additional font directories.

    Returns
    -------
    Path
        Path to the generated PDF.
    """
    from inkline.brands import get_brand
    from inkline.typst.compiler import compile_typst
    from inkline.typst.document_renderer import DocumentSpec, TypstDocumentRenderer
    from inkline.typst.theme_registry import brand_to_typst_theme

    brand_obj = get_brand(brand)
    theme = brand_to_typst_theme(brand_obj, "brand")

    if isinstance(date, datetime):
        date = date.strftime("%B %Y")
    elif not date:
        date = datetime.now().strftime("%B %Y")

    doc_spec = DocumentSpec(
        title=title,
        subtitle=subtitle,
        date=date,
        author=author,
        sections=sections or [],
        paper=paper,
    )

    renderer = TypstDocumentRenderer(theme)

    if sections:
        source = renderer.render_document(doc_spec)
    else:
        source = renderer.render_from_markdown(markdown, doc_spec)

    # Collect font paths
    all_font_paths = [str(_FONTS_DIR)]
    if font_paths:
        all_font_paths.extend(str(p) for p in font_paths)

    # Copy logo to temp location if needed (Typst needs file access)
    output_path = Path(output_path)
    logo_path = theme.get("logo_light_path", "")
    root_dir = None
    if logo_path:
        logo_file = _ASSETS_DIR / logo_path
        if logo_file.exists():
            # Copy logo next to output so Typst can find it
            target = output_path.parent / logo_path
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                import shutil
                shutil.copy2(logo_file, target)
            root_dir = str(output_path.parent)
        else:
            # Logo file doesn't exist — strip from source to avoid compile error
            log.warning("Logo file not found: %s — skipping", logo_file)
            source = source.replace(f'#image("{logo_path}", width: 5cm)', "")

    compile_typst(source, output_path=output_path, root=root_dir, font_paths=all_font_paths)

    log.info("Typst document written to %s", output_path)
    return output_path


# ---------------------------------------------------------------------------
# Convenience: list available templates and brands
# ---------------------------------------------------------------------------

def list_templates() -> list[str]:
    """Return names of all available slide templates."""
    from inkline.typst.theme_registry import SLIDE_TEMPLATES
    return list(SLIDE_TEMPLATES.keys())


def list_slide_types() -> list[str]:
    """Return all supported slide types."""
    return [
        "title", "content", "three_card", "four_card", "stat",
        "table", "split", "chart", "bar_chart", "kpi_strip",
        "timeline", "process_flow", "icon_stat", "progress_bars",
        "pyramid", "comparison", "closing",
    ]


# ---------------------------------------------------------------------------
# Capability manifest (for cross-project integration)
# ---------------------------------------------------------------------------

def get_capabilities() -> dict:
    """Return a dict describing Inkline's full capabilities.

    Used by client applications to discover available output
    formats, brands, templates, and chart types.
    """
    from inkline.brands import list_brands
    return {
        "version": "0.2.0",
        "output_formats": ["typst_slides", "typst_document", "html", "pdf", "pptx", "google_slides"],
        "default_format": "typst_document",
        "brands": list_brands(),
        "slide_templates": list_templates(),
        "slide_types": list_slide_types(),
        "document_paper_sizes": ["a4", "us-letter"],
        "chart_types": [
            "bar_chart", "horizontal_bar", "line_chart", "stacked_bar",
            "waterfall", "scatter", "donut", "kpi_strip", "hero_stat",
            "data_table", "rag_cards", "risk_heatmap", "two_by_two_matrix",
        ],
        "infographic_styles": [
            "timeline", "process_flow", "comparison", "pyramid",
            "icon_grid", "stat_strip", "progress_bars",
        ],
    }
