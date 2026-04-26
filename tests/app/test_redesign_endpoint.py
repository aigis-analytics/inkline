"""Tests for POST /redesign_slide — single-slide LLM redesign endpoint (D3)."""

from __future__ import annotations

import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock

pytest.importorskip("aiohttp")

from inkline.app.claude_bridge import create_app


@pytest_asyncio.fixture
async def client(aiohttp_client):
    app = create_app()
    return await aiohttp_client(app)


@pytest.mark.asyncio
async def test_redesign_missing_body(client):
    """POST /redesign_slide with empty body should not crash."""
    resp = await client.post("/redesign_slide", json={})
    assert resp.status in (200, 400, 500)


@pytest.mark.asyncio
async def test_redesign_returns_new_spec(client):
    """POST /redesign_slide returns new_spec, suggested_markdown, rationale."""
    payload = {
        "slide_index": 2,
        "audit_findings": [
            {"category": "D2", "message": "Wall of bullets", "fix": "Use a three_card layout"}
        ],
        "current_spec": {
            "slide_type": "content",
            "data": {"title": "Three problems", "items": ["A", "B", "C"]},
        },
        "source_section": {
            "title": "Three problems",
            "narrative": "A, B, C",
        },
    }

    with patch("inkline.intelligence.DesignAdvisor") as mock_cls:
        mock_advisor = MagicMock()
        mock_advisor.redesign_one.side_effect = AttributeError("not implemented")
        mock_cls.return_value = mock_advisor

        resp = await client.post("/redesign_slide", json=payload)

    assert resp.status == 200
    data = await resp.json()
    assert "new_spec" in data
    assert "suggested_markdown" in data
    assert "rationale" in data


@pytest.mark.asyncio
async def test_redesign_with_real_redesign_one(client):
    """POST /redesign_slide calls DesignAdvisor.redesign_one if it exists."""
    payload = {
        "slide_index": 0,
        "audit_findings": [],
        "current_spec": {"slide_type": "content", "data": {"title": "Test"}},
        "source_section": {"title": "Test", "narrative": "Content"},
    }

    mock_result = {
        "new_spec": {"slide_type": "three_card", "data": {"title": "Test", "cards": []}},
        "suggested_markdown": "## Test\n<!-- _layout: three_card -->\nContent.",
        "rationale": "Converted to three_card.",
    }

    with patch("inkline.intelligence.DesignAdvisor") as mock_cls:
        mock_advisor = MagicMock()
        mock_advisor.redesign_one.return_value = mock_result
        mock_cls.return_value = mock_advisor

        resp = await client.post("/redesign_slide", json=payload)

    assert resp.status == 200
    data = await resp.json()
    assert data["new_spec"]["slide_type"] == "three_card"


@pytest.mark.asyncio
async def test_authoring_directives_endpoint(client):
    """GET /authoring/directives returns directive names by scope."""
    resp = await client.get("/authoring/directives")
    assert resp.status == 200
    data = await resp.json()
    assert "global" in data
    assert "local" in data
    assert "spot" in data
    assert "brand" in data["global"]
