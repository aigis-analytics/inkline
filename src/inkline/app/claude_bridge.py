"""Inkline Claude Bridge — HTTP server that routes messages to the claude CLI.

Adapted from the Aria project (u3126117/aria). Exposes:
  POST /prompt       — send a message to Claude (agentic mode, full tool access)
  POST /vision       — visual audit: base64 PNG + prompt → Claude reads image and responds
  POST /upload       — save an uploaded file, returns its absolute path
  GET  /output/{f}   — serve generated PDFs and charts
  GET  /             — serve the Inkline WebUI (index.html)
  GET  /health       — liveness check

Claude Code must be installed and authenticated (``claude /login``).
Start with: ``inkline serve`` or ``python -m inkline.app.claude_bridge``
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import shutil
import subprocess
import tempfile
import time
import uuid
from pathlib import Path

try:
    from aiohttp import web
except ImportError:
    raise ImportError(
        "aiohttp is required for the Inkline bridge. "
        "Install it with: pip install \"inkline[app]\""
    )

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_BASE = Path("~/.local/share/inkline").expanduser()
OUTPUT_DIR = _BASE / "output"
CHARTS_DIR = OUTPUT_DIR / "charts"
UPLOAD_DIR = _BASE / "uploads"
LOG_DIR = _BASE / "logs"
for _d in (OUTPUT_DIR, CHARTS_DIR, UPLOAD_DIR, LOG_DIR):
    _d.mkdir(parents=True, exist_ok=True)

STATIC_DIR = Path(__file__).parent / "static"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [inkline-bridge] %(levelname)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(str(LOG_DIR / "bridge.log")),
    ],
)
log = logging.getLogger("inkline.bridge")

# ---------------------------------------------------------------------------
# System prompt — loaded from CLAUDE.md at repo root (dev install)
# or from the package's own CLAUDE.md equivalent
# ---------------------------------------------------------------------------
def _load_system_prompt() -> str:
    """Load the Inkline system prompt for Claude."""
    # Try installed package location first, then development path
    candidates = [
        Path(__file__).parent.parent.parent.parent / "CLAUDE.md",   # dev install: inkline/CLAUDE.md
        Path(__file__).parent / "SYSTEM_PROMPT.md",                  # packaged fallback
    ]
    for p in candidates:
        if p.exists():
            content = p.read_text(encoding="utf-8")
            log.info("System prompt loaded from %s (%d chars)", p, len(content))
            return content
    # Minimal fallback
    return (
        "You are an expert at using the Inkline Python library to generate "
        "branded slide decks and documents. Use Bash to call Inkline's Python API. "
        "Always write output PDFs to ~/.local/share/inkline/output/deck.pdf and "
        "announce 'PDF ready: ~/.local/share/inkline/output/deck.pdf' after rendering."
    )


SYSTEM_PROMPT = _load_system_prompt()

# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------
_last_request_time = 0.0
MIN_REQUEST_INTERVAL = 1.0


# ---------------------------------------------------------------------------
# Claude CLI helpers
# ---------------------------------------------------------------------------
def _parse_stream_json(raw: str) -> dict:
    """Extract result text, tool calls, and metadata from stream-json output."""
    result_text = ""
    tool_calls = []
    num_turns = 0
    duration_ms = 0
    cost_usd = 0.0
    session_id = ""

    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        etype = event.get("type", "")
        if etype == "result":
            result_text = event.get("result", "")
            num_turns = event.get("num_turns", 0)
            duration_ms = event.get("duration_ms", 0)
            cost_usd = event.get("cost_usd", 0.0)
            session_id = event.get("session_id", "")
        elif etype == "assistant":
            for block in event.get("message", {}).get("content", []):
                if block.get("type") == "tool_use":
                    inp = block.get("input", {})
                    tool_calls.append({
                        "tool": block.get("name", "unknown"),
                        "input": {k: (str(v)[:500] + "..." if len(str(v)) > 500 else str(v))
                                  for k, v in inp.items()},
                    })

    return {
        "text": result_text,
        "tool_calls": tool_calls,
        "num_turns": num_turns,
        "duration_ms": duration_ms,
        "cost_usd": cost_usd,
        "session_id": session_id,
    }


# ---------------------------------------------------------------------------
# Route handlers
# ---------------------------------------------------------------------------
async def handle_prompt(request: web.Request) -> web.Response:
    """Accept a user message and route it through claude -p (agentic mode)."""
    global _last_request_time

    try:
        data = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON"}, status=400)

    prompt = data.get("prompt", "").strip()
    extra_system = data.get("system", "")
    if not prompt:
        return web.json_response({"error": "No prompt provided"}, status=400)

    # Rate limiting
    now = time.time()
    wait = MIN_REQUEST_INTERVAL - (now - _last_request_time)
    if wait > 0:
        await asyncio.sleep(wait)
    _last_request_time = time.time()

    # Build full system prompt
    system = SYSTEM_PROMPT
    if extra_system:
        system = system + "\n\n" + extra_system

    cmd = [
        "claude", "-p",
        "--output-format", "stream-json",
        "--verbose",
        "--dangerously-skip-permissions",
        "--max-turns", "25",
        "--system-prompt", system,
    ]

    total_chars = len(prompt) + len(system)
    # Base 900s + 6s per 1k chars of context, capped at 1800s (30 min).
    # 20-slide decks with parallel visual audit observed at 13-15min runtime.
    timeout = min(1800, max(900, 900 + (total_chars // 1000) * 6))

    log.info("Agentic request: %d chars prompt, %d chars system", len(prompt), len(system))

    try:
        env = os.environ.copy()
        env.pop("CLAUDECODE", None)
        env.pop("CLAUDE_CODE_ENTRYPOINT", None)

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(input=prompt.encode("utf-8")),
            timeout=timeout,
        )

        if proc.returncode == 0:
            session = _parse_stream_json(stdout.decode("utf-8").strip())
            log.info(
                "Response: %d chars, %d tool calls, %d turns, %.0fms",
                len(session["text"]), len(session["tool_calls"]),
                session["num_turns"], session["duration_ms"],
            )
            return web.json_response({
                "response": session["text"],
                "source": "claude_max",
                "session": {
                    "tool_calls": session["tool_calls"],
                    "num_turns": session["num_turns"],
                    "duration_ms": session["duration_ms"],
                    "cost_usd": session["cost_usd"],
                },
            })
        else:
            err = stderr.decode("utf-8").strip()
            log.error("CLI error (rc=%d): %s", proc.returncode, err[:200])
            return web.json_response({"error": f"CLI error: {err[:200]}"}, status=502)

    except asyncio.TimeoutError:
        proc.kill()
        log.error("CLI timeout (%ds)", timeout)
        return web.json_response({"error": f"Timed out after {timeout}s"}, status=504)
    except FileNotFoundError:
        log.error("claude CLI not found on PATH")
        return web.json_response({
            "error": "Claude CLI not installed. Run: npm install -g @anthropic-ai/claude-code && claude /login"
        }, status=503)
    except Exception as exc:
        log.exception("Unexpected error")
        return web.json_response({"error": str(exc)}, status=500)


async def handle_vision(request: web.Request) -> web.Response:
    """Accept a base64 PNG slide image + audit prompt, route through Claude for visual review.

    Request JSON:
        image_base64    : base64-encoded PNG bytes
        image_media_type: "image/png" (ignored; only PNG supported)
        prompt          : user audit question
        system          : optional system prompt override

    Response JSON:
        {"response": "<Claude's audit text>"}

    Implementation: saves the image to a temp file, then calls ``claude -p``
    with a prompt asking Claude to Read the file.  Claude Code's Read tool
    supports images natively, so no API key is required — Claude Max covers it.
    """
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON"}, status=400)

    img_b64 = data.get("image_base64", "")
    prompt = data.get("prompt", "").strip()
    extra_system = data.get("system", "")

    if not img_b64 or not prompt:
        return web.json_response({"error": "image_base64 and prompt are required"}, status=400)

    # Decode image and write to a temp file that claude can Read
    try:
        img_bytes = base64.b64decode(img_b64)
    except Exception as exc:
        return web.json_response({"error": f"Invalid base64: {exc}"}, status=400)

    tmp_path = None
    try:
        fd, tmp_path = tempfile.mkstemp(suffix=".png", prefix="inkline_vision_")
        os.close(fd)
        Path(tmp_path).write_bytes(img_bytes)

        # Build the full prompt: ask Claude to read the image file then audit it
        full_prompt = (
            f"Please use the Read tool to read this image file:\n{tmp_path}\n\n"
            f"Then answer the following:\n{prompt}"
        )

        system = SYSTEM_PROMPT
        if extra_system:
            system = extra_system  # vision calls use the caller's system prompt, not deck-building one

        cmd = [
            "claude", "-p",
            "--output-format", "stream-json",
            "--verbose",
            "--dangerously-skip-permissions",
            "--max-turns", "5",
            "--system-prompt", system,
        ]

        timeout = 90  # vision calls are single-slide: 90s is ample

        log.info("Vision audit: %d bytes image, %d chars prompt", len(img_bytes), len(prompt))

        env = os.environ.copy()
        env.pop("CLAUDECODE", None)
        env.pop("CLAUDE_CODE_ENTRYPOINT", None)

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(input=full_prompt.encode("utf-8")),
            timeout=timeout,
        )

        if proc.returncode == 0:
            session = _parse_stream_json(stdout.decode("utf-8").strip())
            log.info("Vision audit complete: %d chars response", len(session["text"]))
            return web.json_response({"response": session["text"]})
        else:
            err = stderr.decode("utf-8").strip()
            log.error("Vision CLI error (rc=%d): %s", proc.returncode, err[:200])
            return web.json_response({"error": f"CLI error: {err[:200]}"}, status=502)

    except asyncio.TimeoutError:
        proc.kill()
        log.error("Vision timeout (90s)")
        return web.json_response({"error": "Vision audit timed out after 90s"}, status=504)
    except Exception as exc:
        log.exception("Vision audit error")
        return web.json_response({"error": str(exc)}, status=500)
    finally:
        if tmp_path and Path(tmp_path).exists():
            Path(tmp_path).unlink(missing_ok=True)


async def handle_upload(request: web.Request) -> web.Response:
    """Save an uploaded file to the uploads directory. Returns the absolute path."""
    try:
        reader = await request.multipart()
        field = await reader.next()
        if field is None:
            return web.json_response({"error": "No file in request"}, status=400)

        filename = field.filename or f"upload_{uuid.uuid4().hex[:8]}"
        dest = UPLOAD_DIR / filename
        # Avoid overwrites
        if dest.exists():
            stem, suffix = Path(filename).stem, Path(filename).suffix
            dest = UPLOAD_DIR / f"{stem}_{uuid.uuid4().hex[:6]}{suffix}"

        with dest.open("wb") as f:
            while True:
                chunk = await field.read_chunk(65536)
                if not chunk:
                    break
                f.write(chunk)

        log.info("Uploaded: %s (%d bytes)", dest.name, dest.stat().st_size)
        return web.json_response({"path": str(dest), "filename": dest.name})

    except Exception as exc:
        log.exception("Upload error")
        return web.json_response({"error": str(exc)}, status=500)


async def handle_output_file(request: web.Request) -> web.Response:
    """Serve a generated PDF or chart PNG from the output directory."""
    filename = request.match_info["filename"]
    # Prevent path traversal
    filepath = (OUTPUT_DIR / filename).resolve()
    if not str(filepath).startswith(str(OUTPUT_DIR.resolve())):
        return web.Response(status=403)
    if not filepath.exists():
        return web.Response(status=404)

    content_type = "application/pdf" if filename.endswith(".pdf") else "image/png"
    return web.FileResponse(filepath, headers={"Content-Type": content_type})


async def handle_index(request: web.Request) -> web.Response:
    """Serve the WebUI index.html."""
    index = STATIC_DIR / "index.html"
    if not index.exists():
        return web.Response(text="WebUI not found. Run: pip install \"inkline[app]\"", status=404)
    return web.FileResponse(index)


async def handle_health(request: web.Request) -> web.Response:
    """Liveness check — also verifies claude CLI is accessible."""
    try:
        proc = subprocess.run(
            ["claude", "--version"], capture_output=True, text=True, timeout=5,
        )
        cli_ok = proc.returncode == 0
        version = proc.stdout.strip() if cli_ok else "unavailable"
    except Exception:
        cli_ok = False
        version = "unavailable"

    return web.json_response({
        "status": "ok" if cli_ok else "degraded",
        "cli_available": cli_ok,
        "cli_version": version,
        "output_dir": str(OUTPUT_DIR),
    })


# ---------------------------------------------------------------------------
# App factory + main
# ---------------------------------------------------------------------------
def create_app() -> web.Application:
    app = web.Application(client_max_size=50 * 1024 * 1024)  # 50 MB upload limit
    app.router.add_post("/prompt", handle_prompt)
    app.router.add_post("/vision", handle_vision)
    app.router.add_post("/upload", handle_upload)
    app.router.add_get("/output/{filename}", handle_output_file)
    app.router.add_get("/health", handle_health)
    app.router.add_get("/", handle_index)
    # Serve static assets (JS/CSS if we add them later)
    if STATIC_DIR.exists():
        app.router.add_static("/static", STATIC_DIR, show_index=False)
    return app


def main(port: int = 8082) -> None:
    if not shutil.which("claude"):
        log.warning(
            "WARNING: 'claude' CLI not found on PATH. "
            "Install Claude Code: npm install -g @anthropic-ai/claude-code && claude /login"
        )
    log.info("Inkline Bridge starting on http://localhost:%d", port)
    log.info("Output directory: %s", OUTPUT_DIR)
    log.info("WebUI: http://localhost:%d/", port)
    web.run_app(create_app(), host="0.0.0.0", port=port, print=lambda s: None)


if __name__ == "__main__":
    main()
