"""Inkline Claude Bridge — HTTP server that routes messages to the claude CLI.

Exposes:
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
    from aiohttp import WSMsgType as _WSMsgType
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
_PHASE_DEFS_SLIDES = [
    {"name": "parse_markdown",        "label": "Parse Document",  "weight": 0.03},
    {"name": "design_advisor_llm",    "label": "Design & Plan",   "weight": 0.72},
    {"name": "save_slide_spec",       "label": "Save Spec",       "weight": 0.02},
    {"name": "export_pdf_with_audit", "label": "Render & Audit",  "weight": 0.23},
]
_PHASE_DEFS_DOCUMENT = [
    {"name": "parse_input",      "label": "Parse Input",     "weight": 0.05},
    {"name": "build_doc_plan",   "label": "Plan Document",   "weight": 0.35},
    {"name": "render_document",  "label": "Render Document", "weight": 0.30},
    {"name": "audit_document",   "label": "Audit Pages",     "weight": 0.30},
]
# Active phase defs — reassigned per request by _init_run_state()
_PHASE_DEFS = _PHASE_DEFS_SLIDES

_PHASE_START_RE  = re.compile(r"\[ARCHON\] Phase: (\S+)")
_PHASE_END_RE    = re.compile(r"\[ARCHON\] (\S+) → (OK|FAILED) in ([\d.]+)s")
_SLIDE_DESIGN_RE = re.compile(r"DesignAdvisor Phase 2: \[\s*(\d+)/(\d+)\]")
# Bypass detection regexes
_ARCHON_PHASE_SEEN_RE = re.compile(r"\[ARCHON\] Phase: \S+")
_PDF_READY_RE         = re.compile(r"PDF[_ ]ready:", re.IGNORECASE)

_run_state: dict = {
    "active": False, "phases": [], "slide_design_done": 0, "slide_design_total": 0,
    "vision_done": 0, "vision_total": 0, "complete": False, "error": None,
    "elapsed_s": 0, "pct": 0, "mode": "slides", "archon_bypassed": False,
}
_sse_queues: set = set()
_run_started_at: float = 0.0


def _init_run_state(mode: str = "slides") -> None:
    global _run_started_at, _PHASE_DEFS
    _run_started_at = time.monotonic()
    _PHASE_DEFS = _PHASE_DEFS_DOCUMENT if mode == "document" else _PHASE_DEFS_SLIDES
    _run_state.update({
        "active": True,
        "mode": mode,
        "archon_bypassed": False,
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
            # Phases that sub-track per-slide / per-section design progress
            if pdef["name"] in ("design_advisor_llm", "build_doc_plan"):
                done = _run_state.get("slide_design_done", 0)
                total = _run_state.get("slide_design_total", 0)
                frac = (0.10 + 0.85 * done / total) if total > 0 else 0.10
                pct += w * frac
            # Phases that sub-track per-page / per-slide vision audit calls
            elif pdef["name"] in ("export_pdf_with_audit", "audit_document"):
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


def _check_archon_bypass(stdout_text: str, result_text: str) -> None:
    """Detect and flag Archon bypass: 'PDF ready:' announced without Archon phase markers.

    Archon emits ``[ARCHON] Phase: <name>`` to stdout (inside tool result blocks).
    If a PDF is announced but no such markers appeared, Claude called the export
    function directly outside of any pipeline phase — a violation of the mandatory
    pipeline rule.
    """
    combined = stdout_text + "\n" + result_text
    pdf_announced = bool(_PDF_READY_RE.search(combined))
    archon_seen   = bool(_ARCHON_PHASE_SEEN_RE.search(stdout_text))
    if pdf_announced and not archon_seen:
        _run_state["archon_bypassed"] = True
        log.warning(
            "ARCHON BYPASS DETECTED: 'PDF ready:' was announced but no [ARCHON] Phase: "
            "markers were seen in the output stream. Claude called export_typst_slides() "
            "or export_typst_document() directly, bypassing the Archon pipeline supervisor. "
            "All output MUST go through the 4-phase Archon pipeline — see CLAUDE.md."
        )


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
# Implicit feedback detection
# ---------------------------------------------------------------------------

_IMPLICIT_PATTERNS = [
    # Chart type changes: "change the bar chart to a dumbbell"
    (re.compile(r"change (?:the |that )?(?:[\w_]+\s)?(?:chart\s)?to (?:a |an )?([\w_]+)", re.I), "chart_type_change"),
    # Orientation: "make it horizontal" / "make the chart vertical"
    (re.compile(r"make (?:it |the chart )?(horizontal|vertical)", re.I), "orientation_change"),
    # Legend/axis/label removal: "remove the legend"
    (re.compile(r"(remove|hide|add|show) (?:the )?(legend|axis|labels?|title|gridlines?)", re.I), "param_change"),
    # Accent: "highlight the 2025 bar" / "accent the enterprise column"
    (re.compile(r"(?:highlight|accent|emphasise?|emphasize) (?:the )?([\w\s]+?)(?:\s+bar|column|segment|series)?$", re.I), "accent_change"),
    # Density feedback: "too many labels" / "too much data"
    (re.compile(r"too (?:many|much) (labels?|bars?|categories|data points?|text)", re.I), "density_feedback"),
    # Direct chart type request: "use a dumbbell chart instead"
    (re.compile(r"use (?:a |an )?([\w_]+) chart", re.I), "chart_type_change"),
    # P6.3: Design quality signals
    (re.compile(r"make (?:it |this |the )?more visual", re.I), "too_textual"),
    (re.compile(r"(?:reduce|less) (?:the )?text", re.I), "too_verbose"),
    (re.compile(r"too many slides", re.I), "too_many_slides"),
    (re.compile(r"change (?:the )?template", re.I), "template_change"),
    (re.compile(r"(?:the title is wrong|fix (?:the )?title)", re.I), "bad_title"),
    # Title rewrite detection (new — self-learning signals)
    (re.compile(r"(?:change|rename|update|rewrite|fix)\s+(?:the\s+)?title\s+(?:of\s+slide\s+\d+\s+)?(?:to|as)\s+[\"']?(.+?)[\"']?$", re.I), "title_rewrite"),
    (re.compile(r"title\s+should\s+(?:be|say|read)\s+[\"']?(.+?)[\"']?$", re.I), "title_rewrite"),
    # Slide type change (implicit regen signal)
    (re.compile(r"change\s+(?:slide\s+\d+\s+)?to\s+(?:a\s+)?(\w+(?:_\w+)*)\s+(?:slide|layout)", re.I), "slide_type_change"),
    (re.compile(r"use\s+(?:a\s+)?(\w+(?:_\w+)*)\s+(?:slide|layout)\s+(?:instead|for\s+(?:this|that))", re.I), "slide_type_change"),
]

_CHART_TYPE_ALIASES = {
    "dumbbell": "dumbbell",
    "gantt": "gantt",
    "heatmap": "heatmap",
    "donut": "donut",
    "pie": "pie",
    "scatter": "scatter",
    "waterfall": "waterfall",
    "line": "line_chart",
    "bar": "grouped_bar",
    "stacked": "stacked_bar",
    "horizontal": "horizontal_stacked_bar",
    "scoring": "scoring_matrix",
    "matrix": "scoring_matrix",
    "timeline": "multi_timeline",
    "multi_timeline": "multi_timeline",
    "transition": "transition_grid",
}


def _record_implicit_feedback(prompt: str, deck_id: str, slide_index: int) -> None:
    """Scan a user message for chart correction patterns and file feedback events.

    Also detects title rewrites and slide type changes for the self-learning store.
    """
    if not prompt:
        return
    try:
        import datetime, uuid
        from inkline.intelligence.aggregator import append_feedback_event

        for pattern, feedback_type in _IMPLICIT_PATTERNS:
            m = pattern.search(prompt)
            if not m:
                continue

            event: dict = {
                "event_id": str(uuid.uuid4())[:8],
                "ts": datetime.datetime.utcnow().isoformat() + "Z",
                "deck_id": deck_id or "unknown",
                "slide_index": slide_index,
                "action": "modified",
                "source": "implicit_conversation",
                "feedback_type": feedback_type,
            }

            if feedback_type == "chart_type_change":
                raw_type = m.group(1).lower().strip()
                resolved = _CHART_TYPE_ALIASES.get(raw_type, raw_type)
                event["modified_to"] = resolved
                event["comment"] = f"User requested: {m.group(0)}"
            elif feedback_type == "orientation_change":
                event["enforce_overrides"] = {"orientation": m.group(1).lower()}
                event["comment"] = f"Orientation override: {m.group(0)}"
            elif feedback_type == "param_change":
                action_word = m.group(1).lower()
                param = m.group(2).lower()
                event["enforce_overrides"] = {f"{action_word}_{param}": True}
                event["comment"] = f"Param change: {m.group(0)}"
            elif feedback_type == "accent_change":
                event["enforce_overrides"] = {"accent_target": m.group(1).strip()}
                event["comment"] = f"Accent request: {m.group(0)}"
            elif feedback_type == "title_rewrite":
                new_title = m.group(1).strip().strip('"\'') if m.lastindex and m.lastindex >= 1 else ""
                event["comment"] = f"Title rewrite: {m.group(0)}"
                # Record to learning store
                _record_title_rewrite_to_store(
                    session_id="", position=slide_index,
                    original="", rewritten=new_title,
                    brand=deck_id or "",
                )
            elif feedback_type == "slide_type_change":
                new_type = m.group(1).lower().strip() if m.lastindex and m.lastindex >= 1 else ""
                event["comment"] = f"Slide type change: {m.group(0)}"
                # Record implicit regen to learning store
                _record_regen_to_store(
                    session_id="", position=slide_index,
                    section_type="", brand=deck_id or "",
                )
            else:
                event["comment"] = f"Density feedback: {m.group(0)}"

            append_feedback_event(event)
            log.info("Implicit feedback recorded: %s (%s)", feedback_type, event.get("comment", ""))
            break  # One event per message — take the first match

    except Exception as e:
        log.debug("Implicit feedback detection skipped: %s", e)


def _record_title_rewrite_to_store(
    session_id: str,
    position: int,
    original: str,
    rewritten: str,
    brand: str = "",
    section_type: str = "",
) -> None:
    """Record a title rewrite event to the learning store. Fail-safe."""
    if not rewritten:
        return
    try:
        from inkline.learning import record_title_rewrite
        record_title_rewrite(
            session_id=session_id,
            position=position,
            original=original,
            rewritten=rewritten,
            section_type=section_type,
            brand=brand,
        )
    except Exception as exc:
        log.debug("_record_title_rewrite_to_store: %s", exc)


def _record_regen_to_store(
    session_id: str,
    position: int,
    section_type: str,
    brand: str = "",
) -> None:
    """Record an implicit slide regen event to the learning store. Fail-safe."""
    try:
        from inkline.learning import record_regen
        record_regen(
            session_id=session_id,
            position=position,
            section_type=section_type,
            brand=brand,
        )
    except Exception as exc:
        log.debug("_record_regen_to_store: %s", exc)


# ---------------------------------------------------------------------------
# Route handlers
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Phase 2: POST /render — non-agentic synchronous render
# ---------------------------------------------------------------------------

async def handle_render(request: web.Request) -> web.Response:
    """Non-agentic render endpoint — preprocessor → DesignAdvisor → exporter.

    POST /render
    {
      "markdown": "<full md text>",      # OR
      "path": "/uploads/foo.md",         # absolute path to already-uploaded file
      "deck_meta_overrides": {...},      # optional CLI-equivalent overrides
      "skip_audit": false                # optional
    }

    Response:
    {
      "outputs": {"pdf": "/output/deck.pdf"},
      "warnings": [...],
      "audit": {"pass": N, "fail": N, "details": [...]}
    }
    """
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON"}, status=400)

    markdown_text = data.get("markdown", "")
    md_path_str   = data.get("path", "")
    overrides     = data.get("deck_meta_overrides", {}) or {}
    skip_audit    = bool(data.get("skip_audit", False))

    if not markdown_text and not md_path_str:
        return web.json_response({"error": "Provide 'markdown' or 'path'"}, status=400)

    if md_path_str and not markdown_text:
        md_file = Path(md_path_str)
        if not md_file.exists():
            return web.json_response({"error": f"File not found: {md_path_str}"}, status=404)
        markdown_text = md_file.read_text(encoding="utf-8")
        source_path = md_path_str
    else:
        source_path = None

    try:
        from inkline.authoring.preprocessor import preprocess
        from inkline.intelligence import DesignAdvisor, audit_deck
        from inkline.typst import export_typst_slides
        from inkline.authoring.notes_writer import write_notes
    except ImportError as exc:
        return web.json_response({"error": f"Missing dependency: {exc}"}, status=500)

    try:
        deck_meta, sections = preprocess(
            markdown_text,
            source_path=source_path,
        )
    except Exception as exc:
        log.exception("Preprocessor error")
        return web.json_response({"error": f"Preprocessor failed: {exc}"}, status=500)

    # Apply overrides (CLI flags / API params take precedence over front-matter)
    deck_meta.update({k: v for k, v in overrides.items() if v})

    brand    = deck_meta.get("brand", "minimal")
    template = deck_meta.get("template", "consulting")
    mode     = deck_meta.get("mode", "rules")   # default rules for non-agentic

    try:
        advisor = DesignAdvisor(brand=brand, template=template, mode=mode)
        slides = advisor.design_deck(
            title=deck_meta.get("title", "Untitled"),
            subtitle=deck_meta.get("subtitle", ""),
            date=deck_meta.get("date", ""),
            sections=sections,
            audience=deck_meta.get("audience", ""),
            goal=deck_meta.get("goal", ""),
        )
    except Exception as exc:
        log.exception("DesignAdvisor error")
        return web.json_response({"error": f"DesignAdvisor failed: {exc}"}, status=500)

    # Determine output file
    stem = Path(source_path).stem if source_path else "render"
    pdf_path = OUTPUT_DIR / f"{stem}.pdf"

    try:
        export_typst_slides(
            slides=slides,
            output_path=str(pdf_path),
            brand=brand,
            template=template,
        )
    except Exception as exc:
        log.exception("Export error")
        return web.json_response({"error": f"Export failed: {exc}"}, status=500)

    # Write notes file
    notes_path = None
    try:
        notes_path = write_notes(pdf_path, slides, sections)
    except Exception as exc:
        log.warning("Notes writer failed: %s", exc)

    # Audit
    audit_result: dict = {"pass": 0, "fail": 0, "details": []}
    warnings_list: list = []
    if not skip_audit:
        try:
            from inkline.intelligence import format_report
            audit_warnings = audit_deck(slides)
            for w in audit_warnings:
                warnings_list.append(str(w))
                if "FAIL" in str(w).upper():
                    audit_result["fail"] += 1
                else:
                    audit_result["pass"] += 1
            audit_result["details"] = [str(w) for w in audit_warnings]
        except Exception as exc:
            log.warning("Audit failed: %s", exc)

    outputs: dict = {"pdf": str(pdf_path)}
    if notes_path:
        outputs["notes"] = str(notes_path)

    return web.json_response({
        "outputs": outputs,
        "spec_path": str(pdf_path.with_suffix("") / "_spec.json") if False else None,
        "warnings": warnings_list,
        "audit": audit_result,
    })


# ---------------------------------------------------------------------------
# Phase 2: WebSocket /watch?file=<path> — file-change push
# ---------------------------------------------------------------------------

# Track active watchers to allow cleanup
_active_watchers: dict = {}  # ws_id → observer


async def handle_watch(request: web.Request) -> web.WebSocketResponse:
    """WebSocket endpoint — watch a file and push render events on change.

    Connect: ws://localhost:8082/watch?file=/path/to/deck.md
    Events pushed to client:
      {"event": "render_start"}
      {"event": "render_done", "outputs": {...}, "audit": {...}}
      {"event": "render_error", "message": "..."}
      {"event": "bridge_shutdown"}
    """
    file_param = request.rel_url.query.get("file", "")
    if not file_param:
        return web.Response(text="?file= param required", status=400)

    md_path = Path(file_param)
    if not md_path.exists():
        return web.Response(text=f"File not found: {file_param}", status=404)

    ws = web.WebSocketResponse()
    await ws.prepare(request)

    ws_id = uuid.uuid4().hex

    # Import watchdog
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
    except ImportError:
        await ws.send_json({"event": "render_error", "message": "watchdog not installed"})
        await ws.close()
        return ws

    loop = asyncio.get_event_loop()
    _DEBOUNCE = 0.25
    _last_render: list[float] = [0.0]

    async def _do_render():
        """Run the non-agentic render and push result to the WebSocket."""
        await ws.send_json({"event": "render_start"})
        try:
            from inkline.authoring.preprocessor import preprocess
            from inkline.intelligence import DesignAdvisor, audit_deck
            from inkline.typst import export_typst_slides
            from inkline.authoring.notes_writer import write_notes

            md_text = md_path.read_text(encoding="utf-8")
            deck_meta, sections = preprocess(md_text, source_path=str(md_path))

            brand    = deck_meta.get("brand", "minimal")
            template = deck_meta.get("template", "consulting")
            mode     = deck_meta.get("mode", "rules")

            advisor = DesignAdvisor(brand=brand, template=template, mode=mode)
            slides = advisor.design_deck(
                title=deck_meta.get("title", md_path.stem),
                subtitle=deck_meta.get("subtitle", ""),
                date=deck_meta.get("date", ""),
                sections=sections,
                audience=deck_meta.get("audience", ""),
                goal=deck_meta.get("goal", ""),
            )

            stem = md_path.stem
            pdf_path = OUTPUT_DIR / f"{stem}.pdf"
            export_typst_slides(
                slides=slides,
                output_path=str(pdf_path),
                brand=brand,
                template=template,
            )

            notes_path = None
            try:
                notes_path = write_notes(pdf_path, slides, sections)
            except Exception:
                pass

            from inkline.intelligence import audit_deck as _audit
            audit_result: dict = {"pass": 0, "fail": 0, "details": []}
            audit_level = deck_meta.get("audit", "structural")
            if audit_level != "off":
                try:
                    aws = _audit(slides)
                    for w in aws:
                        if "FAIL" in str(w).upper():
                            audit_result["fail"] += 1
                        else:
                            audit_result["pass"] += 1
                    audit_result["details"] = [str(w) for w in aws]
                except Exception:
                    pass

            outputs: dict = {"pdf": str(pdf_path)}
            if notes_path:
                outputs["notes"] = str(notes_path)

            await ws.send_json({
                "event": "render_done",
                "outputs": outputs,
                "audit": audit_result,
            })
        except Exception as exc:
            log.exception("Watch render error")
            try:
                await ws.send_json({"event": "render_error", "message": str(exc)})
            except Exception:
                pass

    class _Handler(FileSystemEventHandler):
        def on_modified(self, event):
            import time as _time
            if event.src_path != str(md_path.resolve()):
                return
            now = _time.time()
            if now - _last_render[0] < _DEBOUNCE:
                return
            _last_render[0] = now
            asyncio.run_coroutine_threadsafe(_do_render(), loop)

        def on_created(self, event):
            self.on_modified(event)

    observer = Observer()
    observer.schedule(_Handler(), str(md_path.parent), recursive=False)
    observer.start()
    _active_watchers[ws_id] = observer

    log.info("Watch started: %s (id=%s)", md_path, ws_id)

    try:
        # Run initial render immediately
        await _do_render()

        # Keep alive while the WebSocket is open
        async for msg in ws:
            if msg.type in (_WSMsgType.ERROR, _WSMsgType.CLOSE):
                break
    except Exception:
        pass
    finally:
        observer.stop()
        observer.join(timeout=2.0)
        _active_watchers.pop(ws_id, None)
        log.info("Watch stopped: %s", md_path)

    return ws


# ---------------------------------------------------------------------------
# Phase 2: POST /redesign_slide — single-slide LLM redesign (D3)
# ---------------------------------------------------------------------------

async def handle_redesign_slide(request: web.Request) -> web.Response:
    """Single-slide redesign using DesignAdvisor.redesign_one().

    POST /redesign_slide
    {
      "slide_index": 7,
      "audit_findings": [{"category": "...", "message": "...", "fix": "..."}],
      "current_spec": {...},
      "source_section": {...}
    }

    Response:
    {
      "new_spec": {...},
      "suggested_markdown": "## ... rewritten section ...",
      "rationale": "..."
    }
    """
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON"}, status=400)

    slide_index    = int(data.get("slide_index", 0))
    audit_findings = data.get("audit_findings", [])
    current_spec   = data.get("current_spec", {})
    source_section = data.get("source_section", {})

    try:
        from inkline.intelligence import DesignAdvisor
        advisor = DesignAdvisor(brand="minimal", template="consulting", mode="llm")
        result = advisor.redesign_one(
            slide_index=slide_index,
            current_spec=current_spec,
            audit_findings=audit_findings,
            source_section=source_section,
        )
        return web.json_response(result)
    except AttributeError:
        # redesign_one not yet implemented — return stub
        log.warning("DesignAdvisor.redesign_one() not available — returning stub response")
        return web.json_response({
            "new_spec": current_spec,
            "suggested_markdown": f"## {current_spec.get('data', {}).get('title', 'Untitled')}\n<!-- redesign requested -->\n",
            "rationale": "redesign_one() not yet implemented on this DesignAdvisor build",
        })
    except Exception as exc:
        log.exception("Redesign error")
        return web.json_response({"error": str(exc)}, status=500)


# ---------------------------------------------------------------------------
# Phase 2: GET /authoring/directives — list all registered directives
# ---------------------------------------------------------------------------

async def handle_authoring_directives(request: web.Request) -> web.Response:
    """Return all registered directive names for editor auto-completion."""
    try:
        from inkline.authoring.directives import list_directives
        return web.json_response(list_directives())
    except Exception as exc:
        return web.json_response({"error": str(exc)}, status=500)


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

    # Implicit feedback detection — scan for chart correction patterns before routing
    _record_implicit_feedback(prompt, data.get("deck_id", ""), data.get("slide_index", -1))

    # Output mode — "slides" (default) or "document"
    mode = data.get("mode", "slides")
    if mode not in ("slides", "document"):
        # pptx and other future output types are not yet pipeline-supported;
        # fall back to slides to avoid silent no-op behaviour.
        log.warning("Unknown mode '%s' requested — falling back to 'slides'", mode)
        mode = "slides"

    # Rate limiting
    now = time.time()
    wait = MIN_REQUEST_INTERVAL - (now - _last_request_time)
    if wait > 0:
        await asyncio.sleep(wait)
    _last_request_time = time.time()

    # /prompt extensions (Phase 2) — brand, template, deck_meta overrides
    # These are injected into the system prompt so Claude picks them up automatically.
    brand_hint    = data.get("brand", "")
    template_hint = data.get("template", "")
    deck_meta_ext = data.get("deck_meta", {})
    brand_injects: list[str] = []
    if brand_hint:
        brand_injects.append(f"Brand: {brand_hint}")
    if template_hint:
        brand_injects.append(f"Template: {template_hint}")
    if deck_meta_ext and isinstance(deck_meta_ext, dict):
        brand_injects.append(f"Deck meta overrides: {json.dumps(deck_meta_ext)}")

    # Build full system prompt — base + optional caller override + mandatory mode hint
    system = SYSTEM_PROMPT
    if extra_system:
        system = system + "\n\n" + extra_system
    if brand_injects:
        system = system + "\n\n## DECK CONFIGURATION (from API caller)\n" + "\n".join(brand_injects)
    # Mode hint appended last so it always takes effect regardless of extra_system
    if mode == "document":
        system = system + (
            "\n\n## ACTIVE MODE: document\n"
            "You MUST run the DOCUMENT pipeline with Archon wrapping.\n"
            "Required phases (in order): parse_input → build_doc_plan → render_document → audit_document.\n"
            "Call export_typst_document() ONLY inside the render_document Archon phase.\n"
            "After rendering, run per-page visual audit via POST http://localhost:8082/vision "
            "(one call per page, pymupdf renders each page to PNG) inside the audit_document phase.\n"
            "NEVER call export_typst_document() directly without an Archon phase wrapper.\n"
            "Announce output as: PDF ready: <path>"
        )
    else:
        system = system + (
            "\n\n## ACTIVE MODE: slides\n"
            "You MUST run the SLIDES pipeline with Archon wrapping.\n"
            "Required phases (in order): parse_markdown → design_advisor_llm → save_slide_spec → export_pdf_with_audit.\n"
            "Call export_typst_slides() ONLY inside the export_pdf_with_audit Archon phase.\n"
            "NEVER call export_typst_slides() directly without an Archon phase wrapper.\n"
            "Announce output as: PDF ready: <path>"
        )

    cmd = [
        "claude", "-p",
        "--output-format", "stream-json",
        "--verbose",
        "--dangerously-skip-permissions",
        "--max-turns", "40",
        "--system-prompt", system,
    ]

    log.info("Agentic request: %d chars prompt, %d chars system", len(prompt), len(system))
    _init_run_state(mode=mode)

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
            stdout_text = stdout_raw.decode("utf-8").strip()
            session = _parse_stream_json(stdout_text)
            elapsed_s = int(time.monotonic() - start_time)
            log.info(
                "Response: %d chars, %d tool calls, %d turns, %.0fms (wall %ds)",
                len(session["text"]), len(session["tool_calls"]),
                session["num_turns"], session["duration_ms"], elapsed_s,
            )
            _check_archon_bypass(stdout_text, session["text"])
            _mark_complete()
            return web.json_response({
                "response": session["text"],
                "source": "claude_max",
                "archon_bypassed": _run_state.get("archon_bypassed", False),
                "session": {
                    "tool_calls": session["tool_calls"],
                    "num_turns": session["num_turns"],
                    "duration_ms": session["duration_ms"],
                    "cost_usd": session["cost_usd"],
                },
            })
        else:
            err = stderr_raw.decode("utf-8").strip()
            stdout_text_fail = stdout_raw.decode("utf-8", errors="replace")
            elapsed_fail = time.monotonic() - start_time
            log.error("CLI error (rc=%d): %s", proc.returncode, err[:200])
            _mark_error(f"CLI error rc={proc.returncode}")

            # Write verbose failure dump so the user can diagnose what happened
            dump_path: str | None = None
            try:
                _failures_dir = _BASE / "output" / "cli_failures"
                _failures_dir.mkdir(parents=True, exist_ok=True)
                ts = time.strftime("%Y%m%dT%H%M%S")
                dump_file = _failures_dir / f"{ts}_rc{proc.returncode}.log"
                deck_id = data.get("deck_id", "") if isinstance(data, dict) else ""
                dump_lines = [
                    f"timestamp: {ts}",
                    f"exit_code: {proc.returncode}",
                    f"mode: {mode}",
                    f"deck_id: {deck_id}",
                    f"elapsed_s: {elapsed_fail:.1f}",
                    f"system_prompt_len: {len(system)}",
                    f"prompt:\n{prompt}",
                    f"--- stdout ---\n{stdout_text_fail}",
                    f"--- stderr ---\n{err}",
                ]
                dump_file.write_text("\n\n".join(dump_lines), encoding="utf-8")
                dump_path = str(dump_file)
                log.info("Verbose failure log: %s", dump_path)
            except Exception as _dump_exc:
                log.error("Failed to write CLI failure dump: %s", _dump_exc)

            resp_body: dict = {"error": f"CLI error: {err[:200]}"}
            if dump_path:
                resp_body["dump_path"] = dump_path
            return web.json_response(resp_body, status=502)

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
    """Liveness check — also verifies claude CLI is accessible.

    Returns a ``modes`` object reporting which engine paths are available:
    - ``execute``: always true — the deterministic render engine requires no CLI.
    - ``draft``: true when the claude CLI is available (agentic /prompt path).
    - ``critique``: true when the claude CLI is available (post-render vision audit).
    """
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
        "modes": {
            "execute": True,          # always available — no CLI required
            "draft": cli_ok,          # requires claude CLI (agentic /prompt path)
            "critique": cli_ok,       # requires claude CLI (post-render vision audit)
        },
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
    # Phase 2: non-agentic render + watch + redesign
    app.router.add_post("/render", handle_render)
    app.router.add_get("/watch", handle_watch)
    app.router.add_post("/redesign_slide", handle_redesign_slide)
    app.router.add_get("/authoring/directives", handle_authoring_directives)
    # Output files + status
    app.router.add_get("/output/{filename}", handle_output_file)
    app.router.add_get("/status", handle_status)
    app.router.add_get("/progress", handle_progress)
    app.router.add_get("/health", handle_health)
    app.router.add_get("/", handle_index)
    # Serve static assets (JS/CSS if we add them later)
    if STATIC_DIR.exists():
        app.router.add_static("/static", STATIC_DIR, show_index=False)
    return app


def _cleanup_old_failure_dumps(max_age_days: int = 7) -> None:
    """Delete CLI failure dump files older than *max_age_days* days.

    Called once at bridge startup.  Failures directory:
    ``~/.local/share/inkline/output/cli_failures/``

    Each file is named ``<timestamp>_rc<code>.log``.  Files older than
    *max_age_days* are silently removed.  Any error during cleanup is
    logged but does not prevent startup.
    """
    failures_dir = _BASE / "output" / "cli_failures"
    if not failures_dir.exists():
        return
    cutoff = time.time() - max_age_days * 86400
    removed = 0
    try:
        for p in failures_dir.iterdir():
            if p.is_file() and p.stat().st_mtime < cutoff:
                try:
                    p.unlink()
                    removed += 1
                except Exception as e:
                    log.warning("Could not remove old failure dump %s: %s", p, e)
        if removed:
            log.info("Cleaned up %d CLI failure dump(s) older than %d days", removed, max_age_days)
    except Exception as e:
        log.warning("Failure dump cleanup error: %s", e)


def main(port: int = 8082) -> None:
    if not shutil.which("claude"):
        log.warning(
            "WARNING: 'claude' CLI not found on PATH. "
            "Install Claude Code: npm install -g @anthropic-ai/claude-code && claude /login"
        )
    _cleanup_old_failure_dumps()
    log.info("Inkline Bridge starting on http://localhost:%d", port)
    log.info("Output directory: %s", OUTPUT_DIR)
    log.info("WebUI: http://localhost:%d/", port)
    web.run_app(create_app(), host="0.0.0.0", port=port, print=lambda s: None)


if __name__ == "__main__":
    main()
