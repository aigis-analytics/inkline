"""Inkline — Branded document generation toolkit.

Generates Typst (default), HTML, PDF, PPTX, and Google Slides with
consistent brand identity. Supports Aigis Analytics, TVF, Statler Energy,
Ex Machina, Aria, SparkDCS, and custom brands.

Usage::

    from inkline import export_html, export_pdf, get_brand
    from inkline.typst import export_typst_slides, export_typst_document

    # Typst (default — publication-quality PDF)
    export_typst_document("# My Report", output_path="report.pdf", brand="aigis")
    export_typst_slides(slides=[...], output_path="deck.pdf", brand="aigis")

    # Legacy backends
    export_html("# My Report", output_path="report.html", brand="aigis")
    export_pdf("# My Report", output_path="report.pdf", brand="tvf")
"""

from inkline.brands import get_brand, BaseBrand, list_brands
from inkline.html import export_html
from inkline.pdf import export_pdf
from inkline.slides import SlideBuilder

__version__ = "0.2.0"
__all__ = [
    "get_brand",
    "BaseBrand",
    "list_brands",
    "export_html",
    "export_pdf",
    "SlideBuilder",
]
