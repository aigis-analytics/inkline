"""Tests for the HTML exporter."""

import tempfile
from pathlib import Path

from inkline import export_html


def test_export_html_aigis():
    md = "# Test Report\n\nThis is a test paragraph.\n\n## Section One\n\nContent here."
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "test.html"
        result = export_html(md, output_path=out, brand="aigis", title="Test Report")
        assert result.exists()
        html = result.read_text()
        assert "Aigis Analytics" in html
        assert "#1A7FA0" in html  # brand primary color
        assert "Test Report" in html
        assert "Section One" in html


def test_export_html_tvf():
    md = "# TVF Quarterly Review\n\nContent."
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "tvf.html"
        result = export_html(md, output_path=out, brand="tvf")
        assert result.exists()
        html = result.read_text()
        assert "#3D5A3E" in html  # TVF olive color
        assert "Tamarind Village" in html


def test_export_html_minimal():
    md = "# Plain Report\n\nNo branding."
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "plain.html"
        result = export_html(md, output_path=out, brand="minimal")
        assert result.exists()
        html = result.read_text()
        assert "Plain Report" in html


def test_title_extraction():
    md = "# Auto Title\n\nBody text."
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "auto.html"
        result = export_html(md, output_path=out, brand="aigis")
        html = result.read_text()
        assert "<title>Auto Title</title>" in html


def test_no_toc():
    md = "# Heading\n\nShort doc."
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "notoc.html"
        result = export_html(md, output_path=out, brand="aigis", toc=False)
        html = result.read_text()
        assert "ink-toc" not in html or "onScroll" not in html
