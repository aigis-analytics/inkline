"""Tests for selected MCP server tools."""

from __future__ import annotations

import importlib
import sys
import types
from unittest.mock import patch

import pytest


class _FakeFastMCP:
    def __init__(self, *args, **kwargs):
        self.tools = []
        self.resources = []

    def tool(self, func=None, **_kwargs):
        def decorator(fn):
            self.tools.append(fn)
            return fn

        if func is not None and callable(func):
            return decorator(func)
        return decorator

    def resource(self, uri=None, **kwargs):
        def decorator(fn):
            self.resources.append({"uri": uri, **kwargs, "fn": fn})
            return fn

        return decorator

    def run(self, **_kwargs):
        return None


try:
    import fastmcp as _fastmcp  # type: ignore # noqa: F401
except ImportError:
    fake_fastmcp = types.ModuleType("fastmcp")
    fake_fastmcp.FastMCP = _FakeFastMCP
    sys.modules.setdefault("fastmcp", fake_fastmcp)

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


def test_inkline_render_spec_yaml_forwards_execution_contract(tmp_path):
    spec = tmp_path / "deck.json"
    spec.write_text('{"title": "Deck", "slides": []}', encoding="utf-8")

    with patch("inkline.app.institutional.render_spec_file") as mock_render:
        mock_render.return_value = types.SimpleNamespace(
            pdf_path=tmp_path / "out" / "deck.pdf",
            pptx_path=tmp_path / "out" / "deck.pptx",
            export_metadata_path=tmp_path / "out" / "deck.export_metadata.json",
        )
        result = inkline_render_spec(
            str(spec),
            outputs=["pdf", "pptx"],
            execution_mode="explicit_spec",
            design_locked=True,
            use_design_advisor=False,
            authoring_mode="external_llm",
        )

    assert result["success"] is True
    _, kwargs = mock_render.call_args
    assert kwargs["execution_mode"] == "explicit_spec"
    assert kwargs["design_locked"] is True
    assert kwargs["use_design_advisor"] is False
    assert kwargs["authoring_mode"] == "external_llm"


def test_mcp_server_registers_knowledge_resources(monkeypatch):
    fake_fastmcp = types.ModuleType("fastmcp")
    fake_fastmcp.FastMCP = _FakeFastMCP
    monkeypatch.setitem(sys.modules, "fastmcp", fake_fastmcp)
    sys.modules.pop("inkline.app.mcp_server", None)

    module = importlib.import_module("inkline.app.mcp_server")
    resource_uris = {item["uri"] for item in module.mcp.resources}

    assert "inkline://layouts" in resource_uris
    assert "inkline://slide_roles" in resource_uris
    assert "inkline://archetypes/full_slide" in resource_uris
    assert "inkline://{resource_path}" in resource_uris
