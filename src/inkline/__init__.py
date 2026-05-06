"""Inkline — Branded document generation toolkit.

Generates Typst (default), HTML, PDF, DOCX, PPTX, and Google Slides with
consistent brand identity. Ships with the ``minimal`` brand out of the
box; additional brands can be loaded from ``~/.config/inkline/brands/``
(see :mod:`inkline.brands` for the plugin discovery mechanism).

Usage::

    from inkline import export_html, export_pdf, export_docx, get_brand
    from inkline.typst import export_typst_slides, export_typst_document

    # Typst (default — publication-quality PDF)
    export_typst_document("# My Report", output_path="report.pdf", brand="minimal")
    export_typst_slides(slides=[...], output_path="deck.pdf", brand="minimal")

    # Legacy backends
    export_html("# My Report", output_path="report.html", brand="minimal")
    export_pdf("# My Report", output_path="report.pdf", brand="minimal")
    export_docx("# My Report", output_path="report.docx", brand="minimal")
"""

from inkline.brands import get_brand, BaseBrand, list_brands
from inkline.docx import export_docx
from inkline.html import export_html
from inkline.pdf import export_pdf
from inkline.slides import SlideBuilder
from inkline.exhibit import render_exhibit

__version__ = "0.2.0"
__all__ = [
    "get_brand",
    "BaseBrand",
    "list_brands",
    "export_docx",
    "export_html",
    "export_pdf",
    "SlideBuilder",
    "render_exhibit",
]
