"""Inkline — Branded document generation toolkit.

Generates HTML, PDF, and Google Slides with consistent brand identity.
Supports Aigis Analytics, TVF, Statler Energy, and custom brands.

Usage::

    from inkline import export_html, export_pdf, get_brand

    export_html("# My Report", output_path="report.html", brand="aigis")
    export_pdf("# My Report", output_path="report.pdf", brand="tvf")
"""

from inkline.brands import get_brand, BaseBrand
from inkline.html import export_html
from inkline.pdf import export_pdf
from inkline.slides import SlideBuilder

__version__ = "0.1.0"
__all__ = ["get_brand", "BaseBrand", "export_html", "export_pdf", "SlideBuilder"]
