"""Tests for POST /critique endpoint."""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

pytest.importorskip("aiohttp")

import pytest_asyncio
from aiohttp.test_utils import TestClient
from inkline.app.claude_bridge import create_app


@pytest.fixture
def app():
    return create_app()


@pytest_asyncio.fixture
async def client(aiohttp_client, app):
    return await aiohttp_client(app)


class TestCritiqueEndpoint:
    @pytest.mark.asyncio
    async def test_critique_missing_pdf_path_returns_400(self, client):
        resp = await client.post("/critique", json={})
        assert resp.status == 400

    @pytest.mark.asyncio
    async def test_critique_invalid_json_returns_400(self, client):
        resp = await client.post(
            "/critique",
            data="not json",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status == 400

    @pytest.mark.asyncio
    async def test_critique_nonexistent_pdf_returns_error(self, client, tmp_path):
        resp = await client.post("/critique", json={
            "pdf_path": str(tmp_path / "nonexistent.pdf"),
            "rubric": "institutional",
            "brand": "minimal",
        })
        # Should return 200 with error in body (not 500 — file not found is expected)
        data = await resp.json()
        # CritiqueResult.to_dict() has error field when file is missing
        assert resp.status == 200
        assert data.get("overall_score") == 0 or data.get("error")

    @pytest.mark.asyncio
    async def test_critique_returns_expected_shape(self, client, tmp_path):
        """Even with a nonexistent file, the response shape should be correct."""
        resp = await client.post("/critique", json={
            "pdf_path": "/nonexistent/deck.pdf",
            "rubric": "tech_pitch",
            "brand": "",
        })
        assert resp.status == 200
        data = await resp.json()
        # Should have the CritiqueResult structure
        assert "overall_score" in data
        assert "slide_critiques" in data
