"""Tests for selected MCP server tools."""

from __future__ import annotations

from unittest.mock import patch

import pytest

pytest.importorskip("fastmcp")

from inkline.app.mcp_server import inkline_render_document, inkline_render_spec


def test_inkline_render_document_emits_pdf_and_docx(tmp_path):
    with patch("inkline.pdf.export_pdf") as mock_pdf, \
         patch("inkline.docx.export_docx") as mock_docx:
        result = inkline_render_document(
            content="# Report\n\nBody text.",
            brand="minimal",
            title="Report",
            output_filename="report",
            outputs=["pdf", "docx"],
        )

    assert result["success"] is True
    assert result["outputs"] == ["pdf", "docx"]
    assert result["pdf_path"].endswith("report.pdf")
    assert result["docx_path"].endswith("report.docx")
    assert mock_pdf.called
    assert mock_docx.called


def test_inkline_render_spec_emits_docx(tmp_path):
    spec = tmp_path / "report.md"
    spec.write_text("# Report\n\nBody.", encoding="utf-8")

    with patch("inkline.authoring.preprocessor.preprocess") as mock_preprocess, \
         patch("inkline.intelligence.DesignAdvisor") as mock_advisor_cls, \
         patch("inkline.typst.export_typst_slides") as mock_pdf, \
         patch("inkline.docx.export_docx") as mock_docx:
        mock_preprocess.return_value = (
            {"brand": "minimal", "template": "consulting", "title": "Report", "mode": "rules"},
            [],
        )
        mock_advisor = mock_advisor_cls.return_value
        mock_advisor.design_deck.return_value = []

        result = inkline_render_spec(
            str(spec),
            outputs=["docx"],
            brand="minimal",
            template="consulting",
            output_filename="report_out",
        )

    assert result["success"] is True
    assert result["docx_path"].endswith("report_out.docx")
    assert not mock_pdf.called
    assert mock_docx.called
