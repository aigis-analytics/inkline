"""Tests for POST /render — non-agentic synchronous render endpoint."""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

# Skip entire module if aiohttp not available
pytest.importorskip("aiohttp")

import pytest_asyncio
from aiohttp.test_utils import TestClient
from inkline.app.claude_bridge import create_app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SIMPLE_MD = """\
---
brand: minimal
template: consulting
title: Test Deck
---

## Slide one
Some narrative content.
"""


@pytest_asyncio.fixture
async def client(aiohttp_client):
    """Create a test client for the Inkline bridge."""
    app = create_app()
    return await aiohttp_client(app)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_render_missing_body(client):
    """POST /render with no markdown or path should return 400."""
    resp = await client.post("/render", json={})
    assert resp.status == 400
    data = await resp.json()
    assert "error" in data


@pytest.mark.asyncio
async def test_render_invalid_json(client):
    """POST /render with invalid JSON should return 400."""
    resp = await client.post(
        "/render",
        data="not json",
        headers={"Content-Type": "application/json"},
    )
    assert resp.status == 400


@pytest.mark.asyncio
async def test_render_simple_markdown(client):
    """POST /render with valid markdown should return 200 with output paths."""
    with patch("inkline.authoring.preprocessor.preprocess") as mock_preprocess, \
         patch("inkline.intelligence.DesignAdvisor") as mock_advisor_cls, \
         patch("inkline.typst.export_typst_slides") as mock_export, \
         patch("inkline.authoring.notes_writer.write_notes") as mock_notes, \
         patch("inkline.intelligence.audit_deck") as mock_audit:

        mock_preprocess.return_value = (
            {"brand": "minimal", "template": "consulting", "title": "Test", "mode": "rules",
             "audit": "structural", "audience": "", "goal": "", "subtitle": "", "date": ""},
            [{"type": "narrative", "title": "Slide one", "narrative": "Content"}],
        )
        mock_advisor = MagicMock()
        mock_advisor.design_deck.return_value = [
            {"slide_type": "title", "data": {"company": "Test", "tagline": "", "date": ""}},
        ]
        mock_advisor_cls.return_value = mock_advisor
        mock_export.return_value = None
        mock_notes.return_value = None
        mock_audit.return_value = []

        resp = await client.post("/render", json={"markdown": SIMPLE_MD, "skip_audit": True})

    assert resp.status == 200
    data = await resp.json()
    assert "outputs" in data
    assert "pdf" in data["outputs"]
    assert "audit" in data
    assert "warnings" in data


@pytest.mark.asyncio
async def test_render_nonexistent_path(client):
    """POST /render with nonexistent path should return 404."""
    resp = await client.post("/render", json={"path": "/nonexistent/file.md"})
    assert resp.status == 404


@pytest.mark.asyncio
async def test_render_multi_output_shape(client):
    """POST /render response has correct multi-output shape."""
    with patch("inkline.authoring.preprocessor.preprocess") as mock_preprocess, \
         patch("inkline.intelligence.DesignAdvisor") as mock_advisor_cls, \
         patch("inkline.typst.export_typst_slides") as mock_export, \
         patch("inkline.authoring.notes_writer.write_notes") as mock_notes, \
         patch("inkline.intelligence.audit_deck") as mock_audit:

        mock_preprocess.return_value = (
            {"brand": "minimal", "template": "consulting", "title": "Test", "mode": "rules",
             "audit": "off", "audience": "", "goal": "", "subtitle": "", "date": ""},
            [],
        )
        mock_advisor = MagicMock()
        mock_advisor.design_deck.return_value = []
        mock_advisor_cls.return_value = mock_advisor
        mock_export.return_value = None
        mock_notes.return_value = None
        mock_audit.return_value = []

        resp = await client.post("/render", json={
            "markdown": "## Slide\nContent.",
            "skip_audit": True,
        })

    assert resp.status == 200
    data = await resp.json()
    assert isinstance(data["outputs"], dict)
    assert isinstance(data["warnings"], list)
    assert isinstance(data["audit"], dict)
    assert "pass" in data["audit"]
    assert "fail" in data["audit"]
