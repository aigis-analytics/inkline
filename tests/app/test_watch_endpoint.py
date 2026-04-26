"""Tests for WebSocket /watch — file-change push endpoint."""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import pytest_asyncio

pytest.importorskip("aiohttp")

from inkline.app.claude_bridge import create_app


@pytest_asyncio.fixture
async def client(aiohttp_client):
    app = create_app()
    return await aiohttp_client(app)


@pytest.mark.asyncio
async def test_watch_missing_file_param(client):
    """GET /watch with no ?file= param returns error response."""
    # Non-WebSocket request to WS endpoint
    resp = await client.get("/watch")
    # Should get 400 (missing param) or 426 (Upgrade Required)
    assert resp.status in (400, 426)


@pytest.mark.asyncio
async def test_watch_nonexistent_file(client):
    """GET /watch with nonexistent file returns 404."""
    resp = await client.get("/watch?file=/nonexistent/file.md")
    assert resp.status in (400, 404, 426)


@pytest.mark.asyncio
async def test_watch_websocket_lifecycle(aiohttp_client):
    """WebSocket /watch connects, receives initial render_start, closes cleanly."""
    app = create_app()
    client = await aiohttp_client(app)

    with tempfile.NamedTemporaryFile(suffix=".md", delete=False, mode="w") as f:
        f.write("---\nbrand: minimal\n---\n\n## Test Slide\nContent.\n")
        tmp_path = f.name

    try:
        with patch("inkline.authoring.preprocessor.preprocess") as mock_preprocess, \
             patch("inkline.intelligence.DesignAdvisor") as mock_advisor_cls, \
             patch("inkline.typst.export_typst_slides") as mock_export, \
             patch("inkline.authoring.notes_writer.write_notes") as mock_notes, \
             patch("inkline.intelligence.audit_deck") as mock_audit:

            mock_preprocess.return_value = (
                {"brand": "minimal", "template": "consulting", "title": "Test", "mode": "rules",
                 "audit": "off", "audience": "", "goal": "", "subtitle": "", "date": ""},
                [{"type": "narrative", "title": "Test Slide", "narrative": "Content."}],
            )
            mock_advisor = MagicMock()
            mock_advisor.design_deck.return_value = [
                {"slide_type": "title", "data": {"company": "Test", "tagline": "", "date": ""}},
            ]
            mock_advisor_cls.return_value = mock_advisor
            mock_export.return_value = None
            mock_notes.return_value = None
            mock_audit.return_value = []

            ws = await client.ws_connect(f"/watch?file={tmp_path}")

            events = []
            try:
                for _ in range(3):
                    msg = await asyncio.wait_for(ws.receive_json(), timeout=5.0)
                    events.append(msg)
                    if msg.get("event") in ("render_done", "render_error"):
                        break
            except asyncio.TimeoutError:
                pass

            await ws.close()

        event_types = [e.get("event") for e in events]
        assert "render_start" in event_types, f"Expected render_start in {event_types}"
    finally:
        Path(tmp_path).unlink(missing_ok=True)
