"""Inkline HTML exporter — Markdown to branded HTML reports.

Usage::

    from inkline import export_html

    path = export_html(
        "# My Report\\n\\nContent...",
        output_path="report.html",
        brand="aigis",
        title="My Report",
    )
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from inkline.brands import BaseBrand, get_brand
from inkline.html.renderer import md_to_html, normalise_mermaid
from inkline.html.styles import build_css
from inkline.html.template import build_html_page


def export_html(
    markdown: str,
    output_path: str | Path,
    *,
    brand: str | BaseBrand = "aigis",
    title: str = "",
    confidentiality: str | None = None,
    date: Optional[datetime] = None,
    force_python_md: bool = False,
    toc: bool = True,
    mermaid: bool = True,
    charts: bool = True,
) -> Path:
    """Convert Markdown to a self-contained branded HTML report.

    Parameters
    ----------
    markdown : str
        Full Markdown source (UTF-8).
    output_path : str | Path
        Destination .html path. Parent directories created automatically.
    brand : str | BaseBrand
        Brand name or BaseBrand instance.
    title : str
        Document title for browser tab and header. If blank, extracted
        from first ``# Heading`` in the markdown.
    confidentiality : str | None
        Footer label. Defaults to brand's confidentiality setting.
    date : datetime | None
        Report date for footer. Defaults to today.
    force_python_md : bool
        Skip pandoc and use python-markdown.
    toc : bool
        Auto-generate floating table of contents sidebar.
    mermaid : bool
        Enable mermaid.js diagram rendering.
    charts : bool
        Include Chart.js CDN for chart rendering.

    Returns
    -------
    Path
        Absolute path of the generated HTML file.
    """
    brand_obj = get_brand(brand)

    if date is None:
        date = datetime.now()

    if confidentiality is None:
        confidentiality = brand_obj.confidentiality

    # Extract title from markdown if not provided
    if not title:
        for line in markdown.split("\n"):
            if line.startswith("# "):
                title = line.lstrip("# ").strip()
                break

    footer_date = date.strftime("%B %Y")

    # 1. Markdown → HTML body
    body_html = md_to_html(markdown, force_python=force_python_md)

    # 2. Normalise mermaid blocks
    body_html = normalise_mermaid(body_html)

    # 3. Generate CSS from brand
    css = build_css(brand_obj)

    # 4. Assemble full page
    full_html = build_html_page(
        body_html=body_html,
        css=css,
        brand=brand_obj,
        doc_title=title,
        confidentiality=confidentiality,
        footer_date=footer_date,
        enable_mermaid=mermaid,
        enable_chartjs=charts,
        enable_toc=toc,
    )

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(full_html, encoding="utf-8")

    return out.resolve()


def _cli() -> None:
    """Entry-point for ``inkline-html``."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="inkline-html",
        description="Convert a Markdown file to a branded HTML report.",
    )
    parser.add_argument("input", help="Path to the Markdown (.md) file")
    parser.add_argument("--out", "-o", default=None, help="Output HTML path")
    parser.add_argument("--brand", "-b", default="aigis", help="Brand name (default: aigis)")
    parser.add_argument("--title", "-t", default="", help="Document title")
    parser.add_argument("--no-pandoc", action="store_true", help="Force python-markdown")
    args = parser.parse_args()

    src = Path(args.input)
    if not src.exists():
        parser.error(f"File not found: {src}")

    out = Path(args.out) if args.out else src.with_suffix(".html")
    md = src.read_text(encoding="utf-8")

    html_path = export_html(
        markdown=md,
        output_path=out,
        brand=args.brand,
        title=args.title,
        force_python_md=args.no_pandoc,
    )
    print(f"  Brand  : {args.brand}")
    print(f"  Output : {html_path}")


if __name__ == "__main__":
    _cli()
