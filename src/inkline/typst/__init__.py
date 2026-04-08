"""Typst output backend — slides (16:9 PDF) and documents (A4/Letter PDF).

This is Inkline's default output engine. It produces publication-quality
PDFs with embedded fonts via the Typst compiler.

Usage::

    from inkline.typst import export_typst_slides, export_typst_document

    # Slides from structured data
    export_typst_slides(
        slides=[
            {"slide_type": "title", "data": {"company": "Aigis Analytics", ...}},
            {"slide_type": "three_card", "data": {"section": "Problem", ...}},
        ],
        output_path="deck.pdf",
        brand="aigis",
        template="consulting",
    )

    # Document from Markdown
    export_typst_document(
        markdown="# Due Diligence Report\\n...",
        output_path="report.pdf",
        brand="aigis",
        title="Project Corsair DD Report",
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


def export_typst_slides(
    slides: list[dict[str, Any]],
    output_path: str | Path,
    *,
    brand: str = "aigis",
    template: str = "brand",
    title: str = "Untitled",
    date: str = "",
    subtitle: str = "",
    font_paths: Optional[list[str | Path]] = None,
) -> Path:
    """Generate a slide deck PDF from structured slide specifications.

    Parameters
    ----------
    slides : list[dict]
        List of slide dicts, each with ``slide_type`` and ``data`` keys.
    output_path : Path
        Where to write the PDF.
    brand : str
        Brand name (e.g., "aigis", "tvf", "aria").
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

    brand_obj = get_brand(brand)
    theme = brand_to_typst_theme(brand_obj, template)

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

    output_path = Path(output_path)
    compile_typst(source, output_path=output_path, font_paths=all_font_paths)

    log.info("Typst slide deck written to %s", output_path)
    return output_path


def export_typst_document(
    markdown: str,
    output_path: str | Path,
    *,
    brand: str = "aigis",
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
        "table", "split", "chart", "bar_chart", "kpi_strip", "closing",
    ]


# ---------------------------------------------------------------------------
# Capability manifest (for cross-project integration)
# ---------------------------------------------------------------------------

def get_capabilities() -> dict:
    """Return a dict describing Inkline's full capabilities.

    Used by Aigis, Aria, and other clients to discover available
    output formats, brands, templates, and chart types.
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
