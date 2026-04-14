"""Inkline Claude Bridge — HTTP server that routes messages to the claude CLI.

Adapted from the Aria project (u3126117/aria). Exposes:
  POST /prompt       — send a message to Claude (agentic mode, full tool access)
  POST /vision       — visual audit: base64 PNG + prompt → Claude reads image and responds
  POST /upload       — save an uploaded file, returns its absolute path
  GET  /output/{f}   — serve generated PDFs and charts
  GET  /status       — current pipeline run state (JSON)
  GET  /progress     — SSE stream of pipeline progress events
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
import re
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
# Pipeline run state — served via /status and /progress
# ---------------------------------------------------------------------------
_PHASE_DEFS = [
    {"name": "parse_markdown",        "label": "Parse Document",  "weight": 0.03},
    {"name": "design_advisor_llm",    "label": "Design & Plan",   "weight": 0.72},
    {"name": "save_slide_spec",       "label": "Save Spec",       "weight": 0.02},
    {"name": "export_pdf_with_audit", "label": "Render & Audit",  "weight": 0.23},
]
_PHASE_START_RE  = re.compile(r"\[ARCHON\] Phase: (\S+)")
_PHASE_END_RE    = re.compile(r"\[ARCHON\] (\S+) → (OK|FAILED) in ([\d.]+)s")
_SLIDE_DESIGN_RE = re.compile(r"DesignAdvisor Phase 2: \[\s*(\d+)/(\d+)\]")

_run_state: dict = {
    "active": False, "phases": [], "slide_design_done": 0, "slide_design_total": 0,
    "vision_done": 0, "vision_total": 0, "complete": False, "error": None,
    "elapsed_s": 0, "pct": 0,
}
_sse_queues: set = set()
_run_started_at: float = 0.0


def _init_run_state() -> None:
    global _run_started_at
    _run_started_at = time.monotonic()
    _run_state.update({
        "active": True,
        "phases": [
            {"name": p["name"], "label": p["label"], "status": "pending", "elapsed_s": None}
            for p in _PHASE_DEFS
        ],
        "slide_design_done": 0, "slide_design_total": 0,
        "vision_done": 0, "vision_total": 0,
        "complete": False, "error": None, "elapsed_s": 0, "pct": 0,
    })
    _push_state()


def _push_state() -> None:
    _run_state["elapsed_s"] = int(time.monotonic() - _run_started_at) if _run_started_at else 0
    _run_state["pct"] = _compute_pct()
    snapshot = {**_run_state, "phases": [dict(p) for p in _run_state.get("phases", [])]}
    for q in list(_sse_queues):
        try:
            q.put_nowait(snapshot)
        except Exception:
            pass


def _compute_pct() -> int:
    pct = 0.0
    for pdef in _PHASE_DEFS:
        p_status = next(
            (p for p in _run_state.get("phases", []) if p["name"] == pdef["name"]), None
        )
        if not p_status:
            continue
        w = pdef["weight"]
        if p_status["status"] == "complete":
            pct += w
        elif p_status["status"] == "running":
            if pdef["name"] == "design_advisor_llm":
                done = _run_state.get("slide_design_done", 0)
                total = _run_state.get("slide_design_total", 0)
                frac = (0.10 + 0.85 * done / total) if total > 0 else 0.10
                pct += w * frac
            elif pdef["name"] == "export_pdf_with_audit":
                done = _run_state.get("vision_done", 0)
                total = _run_state.get("vision_total", 0)
                frac = (0.15 + 0.85 * done / total) if total > 0 else 0.10
                pct += w * frac
            else:
                pct += w * 0.5
    return min(99, int(pct * 100))


def _scan_output_text(text: str) -> None:
    """Parse ARCHON/DesignAdvisor output and update run state."""
    changed = False
    for m in _PHASE_START_RE.finditer(text):
        for p in _run_state.get("phases", []):
            if p["name"] == m.group(1) and p["status"] == "pending":
                p["status"] = "running"
                changed = True
    for m in _PHASE_END_RE.finditer(text):
        for p in _run_state.get("phases", []):
            if p["name"] == m.group(1) and p["status"] in ("running", "pending"):
                p["status"] = "complete" if m.group(2) == "OK" else "error"
                p["elapsed_s"] = float(m.group(3))
                changed = True
    for m in _SLIDE_DESIGN_RE.finditer(text):
        _run_state["slide_design_done"] = int(m.group(1))
        _run_state["slide_design_total"] = int(m.group(2))
        changed = True
    if changed:
        _push_state()


def _process_stream_line(line: str) -> None:
    """Extract progress signals from a single stream-json event line."""
    try:
        event = json.loads(line.strip())
    except json.JSONDecodeError:
        return
    etype = event.get("type", "")
    texts: list[str] = []
    # Tool result directly
    if etype == "tool_result":
        c = event.get("content", "")
        if isinstance(c, str):
            texts.append(c)
        elif isinstance(c, list):
            texts.extend(b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text")
    # Tool result inside user message (newer stream-json format)
    elif etype == "user":
        for item in event.get("message", {}).get("content", []):
            if isinstance(item, dict) and item.get("type") == "tool_result":
                inner = item.get("content", "")
                if isinstance(inner, str):
                    texts.append(inner)
                elif isinstance(inner, list):
                    texts.extend(b.get("text", "") for b in inner if isinstance(b, dict) and b.get("type") == "text")
    for t in texts:
        if t:
            _scan_output_text(t)


def _mark_complete() -> None:
    _run_state.update({"active": False, "complete": True, "pct": 100})
    _push_state()


def _mark_error(msg: str) -> None:
    _run_state.update({"active": False, "error": str(msg)[:200]})
    _push_state()


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
    """Accept a user message and route it through claude -p (agentic mode).

    Uses an inactivity-based watchdog instead of a wall-clock timeout:
    the session runs as long as the claude process is producing output.
    If no bytes arrive for INACTIVITY_LIMIT seconds the process is stuck
    and is killed.  An active 20-slide deck never times out; a genuinely
    hung process is reaped within 3 minutes of silence.
    """
    global _last_request_time

    INACTIVITY_LIMIT = 300   # seconds of silence before declaring stuck
    HARD_CAP = 3600          # absolute ceiling regardless of activity (1 hr)

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
        "--max-turns", "40",
        "--system-prompt", system,
    ]

    log.info("Agentic request: %d chars prompt, %d chars system", len(prompt), len(system))
    _init_run_state()

    proc = None
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

        # Write prompt to stdin then close it so the process can start
        proc.stdin.write(prompt.encode("utf-8"))
        await proc.stdin.drain()
        proc.stdin.close()

        # Stream stdout with inactivity watchdog.
        # Each stream-json event line resets the idle timer.
        stdout_chunks: list[bytes] = []
        line_buffer = b""
        start_time = time.monotonic()

        while True:
            # Hard cap: prevent runaway sessions regardless of activity
            elapsed = time.monotonic() - start_time
            if elapsed >= HARD_CAP:
                proc.kill()
                log.error("Agentic hard cap reached (%ds)", HARD_CAP)
                _mark_error(f"Hard cap {HARD_CAP}s reached")
                return web.json_response({"error": f"Hard cap {HARD_CAP}s reached"}, status=504)

            try:
                chunk = await asyncio.wait_for(
                    proc.stdout.read(65536),
                    timeout=INACTIVITY_LIMIT,
                )
            except asyncio.TimeoutError:
                proc.kill()
                elapsed_s = int(time.monotonic() - start_time)
                log.error("Agentic inactivity timeout (%ds idle, %ds elapsed)", INACTIVITY_LIMIT, elapsed_s)
                _mark_error(f"No output for {INACTIVITY_LIMIT}s")
                return web.json_response(
                    {"error": f"No output for {INACTIVITY_LIMIT}s (total {elapsed_s}s elapsed)"},
                    status=504,
                )

            if not chunk:
                break  # EOF — process has exited
            stdout_chunks.append(chunk)

            # Real-time progress tracking — parse stream-json lines as they arrive
            try:
                line_buffer += chunk
                while b"\n" in line_buffer:
                    ln, line_buffer = line_buffer.split(b"\n", 1)
                    _process_stream_line(ln.decode("utf-8", errors="replace"))
            except Exception:
                pass

        await proc.wait()
        stdout_raw = b"".join(stdout_chunks)
        stderr_raw = await proc.stderr.read()

        if proc.returncode == 0:
            session = _parse_stream_json(stdout_raw.decode("utf-8").strip())
            elapsed_s = int(time.monotonic() - start_time)
            log.info(
                "Response: %d chars, %d tool calls, %d turns, %.0fms (wall %ds)",
                len(session["text"]), len(session["tool_calls"]),
                session["num_turns"], session["duration_ms"], elapsed_s,
            )
            _mark_complete()
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
            err = stderr_raw.decode("utf-8").strip()
            log.error("CLI error (rc=%d): %s", proc.returncode, err[:200])
            _mark_error(f"CLI error rc={proc.returncode}")
            return web.json_response({"error": f"CLI error: {err[:200]}"}, status=502)

    except FileNotFoundError:
        log.error("claude CLI not found on PATH")
        _mark_error("Claude CLI not installed")
        return web.json_response({
            "error": "Claude CLI not installed. Run: npm install -g @anthropic-ai/claude-code && claude /login"
        }, status=503)
    except Exception as exc:
        if proc is not None:
            try:
                proc.kill()
            except Exception:
                pass
        log.exception("Unexpected error")
        _mark_error(str(exc))
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

    # Track vision progress
    try:
        _run_state["vision_total"] = _run_state.get("vision_total", 0) + 1
        _push_state()
    except Exception:
        pass

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
            try:
                _run_state["vision_done"] = _run_state.get("vision_done", 0) + 1
                _push_state()
            except Exception:
                pass
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


async def handle_status(request: web.Request) -> web.Response:
    """Return current pipeline run state as JSON (REST poll endpoint)."""
    snapshot = {**_run_state, "phases": [dict(p) for p in _run_state.get("phases", [])]}
    return web.json_response(snapshot)


async def handle_progress(request: web.Request) -> web.StreamResponse:
    """SSE stream of pipeline progress events.

    Emits ``data: <json>\\n\\n`` on every state change.
    Sends a heartbeat comment every 25 s to keep the connection alive.
    """
    resp = web.StreamResponse(headers={
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
    })
    await resp.prepare(request)

    q: asyncio.Queue = asyncio.Queue(maxsize=50)
    _sse_queues.add(q)
    try:
        # Send current state immediately so the client doesn't wait
        snapshot = {**_run_state, "phases": [dict(p) for p in _run_state.get("phases", [])]}
        await resp.write(f"data: {json.dumps(snapshot)}\n\n".encode())

        while True:
            try:
                state = await asyncio.wait_for(q.get(), timeout=25.0)
                await resp.write(f"data: {json.dumps(state)}\n\n".encode())
                if state.get("complete") or state.get("error"):
                    break
            except asyncio.TimeoutError:
                await resp.write(b": heartbeat\n\n")
    except Exception:
        pass
    finally:
        _sse_queues.discard(q)
    return resp


# ---------------------------------------------------------------------------
# App factory + main
# ---------------------------------------------------------------------------
def create_app() -> web.Application:
    app = web.Application(client_max_size=50 * 1024 * 1024)  # 50 MB upload limit
    app.router.add_post("/prompt", handle_prompt)
    app.router.add_post("/vision", handle_vision)
    app.router.add_post("/upload", handle_upload)
    app.router.add_get("/output/{filename}", handle_output_file)
    app.router.add_get("/status", handle_status)
    app.router.add_get("/progress", handle_progress)
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
