"""Unit tests for the Claude bridge server (claude_bridge.py).

Tests cover:
- _parse_stream_json: event parsing for result, tool_use, edge cases
- handle_vision: missing fields → 400, bad base64 → 400, successful mock
- handle_prompt: missing prompt → 400
- handle_health: always 200
- create_app: routes are registered
- Route existence: /vision, /prompt, /upload, /health, /output/{filename}
"""
from __future__ import annotations

import base64
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

pytest_asyncio = pytest.importorskip("pytest_asyncio", reason="pytest-asyncio required")

from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from inkline.app.claude_bridge import (
    _parse_stream_json,
    create_app,
    handle_health,
    handle_prompt,
    handle_vision,
)


# ---------------------------------------------------------------------------
# _parse_stream_json
# ---------------------------------------------------------------------------

class TestParseStreamJson:
    def test_extracts_result_text(self):
        event = json.dumps({"type": "result", "result": "Hello world", "num_turns": 2,
                            "duration_ms": 500, "cost_usd": 0.01, "session_id": "abc"})
        out = _parse_stream_json(event)
        assert out["text"] == "Hello world"
        assert out["num_turns"] == 2
        assert out["duration_ms"] == 500
        assert out["cost_usd"] == 0.01
        assert out["session_id"] == "abc"

    def test_empty_result_text(self):
        event = json.dumps({"type": "result", "result": ""})
        out = _parse_stream_json(event)
        assert out["text"] == ""

    def test_extracts_tool_calls(self):
        tool_event = json.dumps({
            "type": "assistant",
            "message": {
                "content": [{
                    "type": "tool_use",
                    "name": "Read",
                    "input": {"file_path": "/tmp/foo.png"},
                }]
            },
        })
        result_event = json.dumps({"type": "result", "result": "done"})
        raw = tool_event + "\n" + result_event
        out = _parse_stream_json(raw)
        assert len(out["tool_calls"]) == 1
        assert out["tool_calls"][0]["tool"] == "Read"
        assert out["tool_calls"][0]["input"]["file_path"] == "/tmp/foo.png"

    def test_tool_input_truncated_at_500_chars(self):
        long_val = "x" * 600
        tool_event = json.dumps({
            "type": "assistant",
            "message": {
                "content": [{
                    "type": "tool_use",
                    "name": "Bash",
                    "input": {"command": long_val},
                }]
            },
        })
        out = _parse_stream_json(tool_event)
        assert len(out["tool_calls"][0]["input"]["command"]) == 503  # 500 + "..."

    def test_ignores_malformed_json_lines(self):
        raw = "not-json\n" + json.dumps({"type": "result", "result": "ok"}) + "\nalso-bad"
        out = _parse_stream_json(raw)
        assert out["text"] == "ok"

    def test_empty_input(self):
        out = _parse_stream_json("")
        assert out["text"] == ""
        assert out["tool_calls"] == []
        assert out["num_turns"] == 0

    def test_multiple_result_events_uses_last(self):
        # In practice stream-json emits exactly one result, but be defensive
        e1 = json.dumps({"type": "result", "result": "first"})
        e2 = json.dumps({"type": "result", "result": "last"})
        out = _parse_stream_json(e1 + "\n" + e2)
        assert out["text"] == "last"

    def test_unknown_event_types_ignored(self):
        events = "\n".join([
            json.dumps({"type": "system", "data": "startup"}),
            json.dumps({"type": "tool_result", "content": "some result"}),
            json.dumps({"type": "result", "result": "answer"}),
        ])
        out = _parse_stream_json(events)
        assert out["text"] == "answer"
        assert out["tool_calls"] == []


# ---------------------------------------------------------------------------
# HTTP route tests (using aiohttp TestClient)
# ---------------------------------------------------------------------------

@pytest.fixture
def app():
    return create_app()


@pytest.mark.asyncio
async def test_health_returns_200(app):
    async with TestClient(TestServer(app)) as client:
        resp = await client.get("/health")
        assert resp.status == 200
        data = await resp.json()
        assert data.get("status") == "ok"


@pytest.mark.asyncio
async def test_vision_missing_image_returns_400(app):
    async with TestClient(TestServer(app)) as client:
        resp = await client.post("/vision", json={"prompt": "audit this"})
        assert resp.status == 400
        data = await resp.json()
        assert "error" in data


@pytest.mark.asyncio
async def test_vision_missing_prompt_returns_400(app):
    async with TestClient(TestServer(app)) as client:
        img_b64 = base64.b64encode(b"\x89PNG\r\n" + b"\x00" * 10).decode()
        resp = await client.post("/vision", json={"image_base64": img_b64})
        assert resp.status == 400
        data = await resp.json()
        assert "error" in data


@pytest.mark.asyncio
async def test_vision_bad_base64_returns_400(app):
    async with TestClient(TestServer(app)) as client:
        resp = await client.post(
            "/vision",
            json={"image_base64": "!!!not-valid-base64!!!", "prompt": "audit"},
        )
        assert resp.status == 400
        data = await resp.json()
        assert "error" in data


@pytest.mark.asyncio
async def test_vision_invalid_json_returns_400(app):
    async with TestClient(TestServer(app)) as client:
        resp = await client.post(
            "/vision",
            data=b"not json",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status == 400


@pytest.mark.asyncio
async def test_prompt_missing_prompt_returns_400(app):
    async with TestClient(TestServer(app)) as client:
        resp = await client.post("/prompt", json={"system": "override"})
        assert resp.status == 400
        data = await resp.json()
        assert "error" in data


@pytest.mark.asyncio
async def test_prompt_invalid_json_returns_400(app):
    async with TestClient(TestServer(app)) as client:
        resp = await client.post(
            "/prompt",
            data=b"broken",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status == 400


@pytest.mark.asyncio
async def test_vision_cli_success_returns_response(app, tmp_path):
    """Mock the claude subprocess to verify the success path returns {"response": ...}."""
    # Create a minimal valid PNG (1×1 white pixel)
    png_1x1 = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00"
        b"\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    img_b64 = base64.b64encode(png_1x1).decode()

    # Simulate a successful claude -p stream-json response
    fake_stream = json.dumps({
        "type": "result",
        "result": '[{"severity":"warn","message":"legend overlaps axis"}]',
        "num_turns": 1,
        "duration_ms": 100,
        "cost_usd": 0.0,
        "session_id": "test-session",
    }) + "\n"

    mock_proc = AsyncMock()
    mock_proc.returncode = 0
    mock_proc.communicate = AsyncMock(
        return_value=(fake_stream.encode(), b"")
    )

    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        async with TestClient(TestServer(app)) as client:
            resp = await client.post(
                "/vision",
                json={
                    "image_base64": img_b64,
                    "image_media_type": "image/png",
                    "prompt": "Check for visual issues",
                    "system": "You are an auditor.",
                },
            )
            assert resp.status == 200
            data = await resp.json()
            assert "response" in data
            assert "legend" in data["response"]


@pytest.mark.asyncio
async def test_vision_cli_failure_returns_502(app):
    """Mock claude returning rc=1 → bridge should return 502."""
    png_1x1 = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00"
        b"\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    img_b64 = base64.b64encode(png_1x1).decode()

    mock_proc = AsyncMock()
    mock_proc.returncode = 1
    mock_proc.communicate = AsyncMock(return_value=(b"", b"Claude exited with error"))

    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        async with TestClient(TestServer(app)) as client:
            resp = await client.post(
                "/vision",
                json={"image_base64": img_b64, "prompt": "audit"},
            )
            assert resp.status == 502
            data = await resp.json()
            assert "error" in data


@pytest.mark.asyncio
async def test_create_app_registers_all_routes(app):
    """Verify all expected routes exist in the application."""
    router = app.router
    named = {r.resource.canonical for r in router.routes()}
    assert "/health" in named
    assert "/vision" in named
    assert "/prompt" in named
    assert "/upload" in named
