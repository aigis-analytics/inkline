"""Tests for the HTML exporter.

These tests use the public ``minimal`` brand only — no private/user brands.
"""

import tempfile
from pathlib import Path

from inkline import export_html
from inkline.brands import get_brand


def test_export_html_minimal():
    md = "# Test Report\n\nThis is a test paragraph.\n\n## Section One\n\nContent here."
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "test.html"
        result = export_html(md, output_path=out, brand="minimal", title="Test Report")
        assert result.exists()
        html = result.read_text()
        assert "Test Report" in html
        assert "Section One" in html


def test_export_html_minimal_palette_applied():
    md = "# Plain Report\n\nNo branding."
    brand = get_brand("minimal")
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "plain.html"
        result = export_html(md, output_path=out, brand="minimal")
        assert result.exists()
        html = result.read_text()
        assert "Plain Report" in html
        # brand primary colour should appear in the generated stylesheet
        assert brand.primary in html


def test_title_extraction():
    md = "# Auto Title\n\nBody text."
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "auto.html"
        result = export_html(md, output_path=out, brand="minimal")
        html = result.read_text()
        assert "<title>Auto Title</title>" in html


def test_no_toc():
    md = "# Heading\n\nShort doc."
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "notoc.html"
        result = export_html(md, output_path=out, brand="minimal", toc=False)
        html = result.read_text()
        assert "ink-toc" not in html or "onScroll" not in html
