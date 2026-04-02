"""Inkline PDF exporter — Markdown to branded PDF documents.

Backend selection (automatic, in priority order):
1. WeasyPrint — excellent quality, repeating headers/footers
2. Playwright / Chromium — highest visual fidelity
3. Edge / Chrome headless — last resort system browser fallback

Usage::

    from inkline import export_pdf

    path = export_pdf(
        "# My Report\\n\\nContent...",
        output_path="report.pdf",
        brand="aigis",
        title="My Report",
    )
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from inkline.brands import BaseBrand, get_brand
from inkline.html.renderer import md_to_html
from inkline.pdf.renderer import render_pdf
from inkline.utils import b64_data_uri


def export_pdf(
    markdown: str,
    output_path: str | Path,
    *,
    brand: str | BaseBrand = "aigis",
    title: str = "",
    confidentiality: str | None = None,
    date: Optional[datetime] = None,
) -> Path:
    """Convert Markdown to a branded PDF document.

    Parameters
    ----------
    markdown : str
        Full Markdown source (UTF-8).
    output_path : str | Path
        Destination .pdf path.
    brand : str | BaseBrand
        Brand name or BaseBrand instance.
    title : str
        Document title. If blank, extracted from first # heading.
    confidentiality : str | None
        Footer label. Defaults to brand setting.
    date : datetime | None
        Report date for footer. Defaults to today.

    Returns
    -------
    Path
        Absolute path of the generated PDF file.
    """
    brand_obj = get_brand(brand)

    if date is None:
        date = datetime.now()

    if confidentiality is None:
        confidentiality = brand_obj.confidentiality

    if not title:
        for line in markdown.split("\n"):
            if line.startswith("# "):
                title = line.lstrip("# ").strip()
                break

    footer_date = date.strftime("%B %Y")
    body_html = md_to_html(markdown)
    logo_uri = b64_data_uri(brand_obj.logo_for_bg(brand_obj.surface))

    footer_parts = [p for p in [brand_obj.display_name, confidentiality, footer_date] if p]
    footer_text = "\u2002\u00b7\u2002".join(footer_parts)

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    render_pdf(
        body_html=body_html,
        output_path=out,
        brand=brand_obj,
        logo_uri=logo_uri,
        doc_title=title,
        footer_text=footer_text,
    )

    return out.resolve()


def _cli() -> None:
    """Entry-point for ``inkline-pdf``."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="inkline-pdf",
        description="Convert a Markdown file to a branded PDF.",
    )
    parser.add_argument("input", help="Path to the Markdown (.md) file")
    parser.add_argument("--out", "-o", default=None, help="Output PDF path")
    parser.add_argument("--brand", "-b", default="aigis", help="Brand name (default: aigis)")
    parser.add_argument("--title", "-t", default="", help="Document title")
    args = parser.parse_args()

    src = Path(args.input)
    if not src.exists():
        parser.error(f"File not found: {src}")

    out = Path(args.out) if args.out else src.with_suffix(".pdf")
    md = src.read_text(encoding="utf-8")

    pdf_path = export_pdf(
        markdown=md,
        output_path=out,
        brand=args.brand,
        title=args.title,
    )
    print(f"  Brand  : {args.brand}")
    print(f"  Output : {pdf_path}")


if __name__ == "__main__":
    _cli()
