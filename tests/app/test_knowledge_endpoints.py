"""Tests for GET /knowledge/* HTTP proxy endpoints."""

from __future__ import annotations

import pytest

pytest.importorskip("aiohttp")

import pytest_asyncio
from aiohttp.test_utils import TestClient
from inkline.app.claude_bridge import create_app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def app():
    return create_app()


@pytest_asyncio.fixture
async def client(aiohttp_client, app):
    return await aiohttp_client(app)


# ---------------------------------------------------------------------------
# GET /knowledge/* tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_knowledge_layouts_returns_markdown(client):
    resp = await client.get("/knowledge/layouts")
    assert resp.status == 200
    text = await resp.text()
    assert "three_card" in text


@pytest.mark.asyncio
async def test_knowledge_playbooks_index_returns_content(client):
    resp = await client.get("/knowledge/playbooks/index")
    assert resp.status == 200
    text = await resp.text()
    assert "inkline://playbooks/" in text


@pytest.mark.asyncio
async def test_knowledge_typography_returns_content(client):
    resp = await client.get("/knowledge/typography")
    assert resp.status == 200
    text = await resp.text()
    assert len(text) > 50


@pytest.mark.asyncio
async def test_knowledge_specific_layout_returns_content(client):
    resp = await client.get("/knowledge/layouts/three_card")
    assert resp.status == 200
    text = await resp.text()
    assert "three_card" in text


@pytest.mark.asyncio
async def test_knowledge_unknown_resource_returns_404(client):
    resp = await client.get("/knowledge/totally_fake_xyz/resource")
    assert resp.status == 404


@pytest.mark.asyncio
async def test_knowledge_anti_patterns_returns_content(client):
    resp = await client.get("/knowledge/anti-patterns")
    assert resp.status == 200
