"""Tests for verbose CLI failure dump on rc != 0 in handle_prompt.

Verifies:
- A dump file is created under cli_failures/ on subprocess rc != 0
- The dump file contains: exit code, prompt text, stdout chunk text
- The 502 response JSON includes a dump_path field
- The 502 status code is preserved

Uses aiohttp test client + mocked asyncio.create_subprocess_exec.
"""
from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

pytest.importorskip("aiohttp")

import pytest_asyncio
from aiohttp.test_utils import TestClient
from inkline.app.claude_bridge import create_app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def client(aiohttp_client):
    app = create_app()
    return await aiohttp_client(app)


def _make_fake_proc(rc: int, stdout_data: bytes, stderr_data: bytes):
    """Build a mock asyncio subprocess object that exits with *rc*."""
    proc = MagicMock()
    proc.returncode = rc

    # stdin
    proc.stdin = MagicMock()
    proc.stdin.write = MagicMock()
    proc.stdin.drain = AsyncMock()
    proc.stdin.close = MagicMock()

    # stdout — read() returns data once then b""
    stdout_calls = [stdout_data, b""]
    async def _stdout_read(n):
        return stdout_calls.pop(0) if stdout_calls else b""
    proc.stdout = MagicMock()
    proc.stdout.read = _stdout_read

    # stderr
    proc.stderr = MagicMock()
    proc.stderr.read = AsyncMock(return_value=stderr_data)

    # wait
    proc.wait = AsyncMock()
    proc.kill = MagicMock()

    return proc


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestCliFailureDump:
    @pytest.mark.asyncio
    async def test_dump_file_created_on_nonzero_rc(self, client, tmp_path):
        """A .log dump file must be created under cli_failures/ when rc != 0."""
        fake_proc = _make_fake_proc(
            rc=143,
            stdout_data=b'{"type":"text","text":"partial output before SIGTERM"}\n',
            stderr_data=b"",
        )

        failures_dir = Path("~/.local/share/inkline/output/cli_failures").expanduser()
        failures_dir.mkdir(parents=True, exist_ok=True)

        # Capture files before
        before = set(failures_dir.iterdir())

        with patch("asyncio.create_subprocess_exec", return_value=fake_proc):
            resp = await client.post(
                "/prompt",
                json={"prompt": "Generate a test deck", "mode": "slides"},
            )

        assert resp.status == 502

        # A new .log file should have appeared
        after = set(failures_dir.iterdir())
        new_files = after - before
        assert len(new_files) == 1, f"Expected 1 new dump file, got: {new_files}"
        dump_file = new_files.pop()
        assert dump_file.suffix == ".log"

        # Clean up
        dump_file.unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_dump_contains_rc_prompt_and_stdout(self, client):
        """Dump file must contain the exit code, full prompt, and stdout chunk text."""
        test_prompt = "Generate a RadarSeq branded deck please"
        stdout_chunk = b'{"type":"text","text":"I started generating"}\n'

        fake_proc = _make_fake_proc(
            rc=143,
            stdout_data=stdout_chunk,
            stderr_data=b"some stderr text",
        )

        failures_dir = Path("~/.local/share/inkline/output/cli_failures").expanduser()
        failures_dir.mkdir(parents=True, exist_ok=True)
        before = set(failures_dir.iterdir())

        with patch("asyncio.create_subprocess_exec", return_value=fake_proc):
            resp = await client.post(
                "/prompt",
                json={"prompt": test_prompt, "mode": "slides"},
            )

        assert resp.status == 502
        after = set(failures_dir.iterdir())
        new_files = after - before
        assert len(new_files) == 1

        dump_file = new_files.pop()
        content = dump_file.read_text(encoding="utf-8")

        assert "143" in content, "exit_code 143 should appear in dump"
        assert test_prompt in content, "Full prompt should appear in dump"
        assert "I started generating" in content, "stdout chunk text should appear in dump"

        dump_file.unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_response_json_includes_dump_path(self, client):
        """The 502 response body must include a dump_path field."""
        fake_proc = _make_fake_proc(
            rc=1,
            stdout_data=b"",
            stderr_data=b"claude exited with rc 1",
        )

        failures_dir = Path("~/.local/share/inkline/output/cli_failures").expanduser()
        failures_dir.mkdir(parents=True, exist_ok=True)
        before = set(failures_dir.iterdir())

        with patch("asyncio.create_subprocess_exec", return_value=fake_proc):
            resp = await client.post(
                "/prompt",
                json={"prompt": "test prompt", "mode": "slides"},
            )

        assert resp.status == 502
        body = await resp.json()
        assert "dump_path" in body, f"dump_path missing from response: {body}"
        assert body["dump_path"].endswith(".log")
        assert "cli_failures" in body["dump_path"]

        # Clean up
        after = set(failures_dir.iterdir())
        for f in after - before:
            f.unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_502_status_preserved(self, client):
        """Ensure 502 status code is unchanged by dump logic."""
        fake_proc = _make_fake_proc(
            rc=143,
            stdout_data=b"",
            stderr_data=b"",
        )

        failures_dir = Path("~/.local/share/inkline/output/cli_failures").expanduser()
        failures_dir.mkdir(parents=True, exist_ok=True)
        before = set(failures_dir.iterdir())

        with patch("asyncio.create_subprocess_exec", return_value=fake_proc):
            resp = await client.post(
                "/prompt",
                json={"prompt": "any prompt", "mode": "slides"},
            )

        assert resp.status == 502, f"Expected 502 but got {resp.status}"

        # Clean up
        after = set(failures_dir.iterdir())
        for f in after - before:
            f.unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_dump_path_points_at_existing_file(self, client):
        """The dump_path in the response must point to a file that actually exists."""
        fake_proc = _make_fake_proc(
            rc=2,
            stdout_data=b"hello",
            stderr_data=b"",
        )

        failures_dir = Path("~/.local/share/inkline/output/cli_failures").expanduser()
        failures_dir.mkdir(parents=True, exist_ok=True)
        before = set(failures_dir.iterdir())

        with patch("asyncio.create_subprocess_exec", return_value=fake_proc):
            resp = await client.post(
                "/prompt",
                json={"prompt": "verify path", "mode": "slides"},
            )

        body = await resp.json()
        dump_path = body.get("dump_path")
        assert dump_path is not None
        assert Path(dump_path).exists(), f"dump_path {dump_path} does not exist on disk"

        # Clean up
        after = set(failures_dir.iterdir())
        for f in after - before:
            f.unlink(missing_ok=True)
