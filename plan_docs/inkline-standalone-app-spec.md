# Inkline Standalone App — Architecture Spec

**Status:** Draft for review  
**Date:** April 2026  
**Revision:** v2 — Claude Code wrapper pattern (replacing Chainlit/custom-agent approach)

---

## 1. The pattern: Claude Code as the agent

The right model here is identical to what we built for Aria and Aigis: a thin HTTP
bridge that hands messages to the `claude` CLI (`-p --dangerously-skip-permissions
--max-turns 25`). Claude Code IS the agent. It maintains conversation state, reads
files with its own tools, reasons about content structure, interprets amendment
instructions naturally, and calls Inkline via Bash.

**What this eliminates from the original spec:**
- ~~ContentAgent (custom Python)~~ → Claude reads the file and structures sections natively
- ~~AmendmentAgent (custom Python)~~ → Claude interprets "make slide 3 more visual" naturally
- ~~SessionManager~~ → Claude Code maintains conversation history in-session
- ~~Chainlit WebUI~~ → unnecessary, bridge + thin page is enough
- ~~FastAPI backend~~ → replaced by the bridge (< 400 lines, already written in Aria)
- ~~Custom streaming~~ → already handled by `--output-format stream-json` in the bridge

**What this keeps:**
- File parsers (small utilities for .docx/.pdf/.pptx → text)
- MCP server (for Claude.ai and Claude Desktop integration)
- A thin WebUI if we want browser access for non-technical users
- A good CLAUDE.md for Inkline

---

## 2. Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                       User Interfaces                            │
│                                                                  │
│  ┌───────────────┐   ┌────────────────┐   ┌─────────────────┐  │
│  │  Thin WebUI   │   │  Claude Code   │   │  Claude.ai /    │  │
│  │  (HTML/JS)    │   │  CLI directly  │   │  Claude Desktop │  │
│  │  localhost    │   │  (dev users)   │   │  via MCP        │  │
│  └───────┬───────┘   └───────┬────────┘   └────────┬────────┘  │
│          └──────POST /prompt─┘                      │ MCP tools │
│                    │                                │           │
│          ┌─────────▼─────────┐          ┌──────────▼──────────┐│
│          │  claude_bridge.py │          │  inkline_mcp.py     ││
│          │  port 8082        │          │  port 8083           ││
│          │  (aiohttp, ~350   │          │  (fastmcp, ~150      ││
│          │   lines — copy    │          │   lines)             ││
│          │   from Aria)      │          │                      ││
│          └─────────┬─────────┘          └──────────┬──────────┘│
│                    │                               │            │
│          ┌─────────▼───────────────────────────────▼──────────┐│
│          │            claude -p --dangerously-skip-permissions  ││
│          │            --max-turns 25 --output-format stream-json││
│          │                                                      ││
│          │  Claude Code uses its own tools:                     ││
│          │  • Read → reads .md/.txt files                       ││
│          │  • Bash → runs python -c "from inkline.typst import ..."││
│          │  • Bash → calls inkline-pdf/inkline-html CLI         ││
│          │  • Bash → runs pandoc for .docx input                ││
│          └─────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────┘
```

---

## 3. What actually needs to be built

### 3.1 CLAUDE.md for Inkline (`/mnt/d/inkline/CLAUDE.md`)

The core of the whole system. A well-written CLAUDE.md tells Claude exactly
how to use Inkline — API shapes, available slide types, chart types, templates,
brands, how to handle .docx input (call pandoc), how to call DesignAdvisor, how
to interpret amendment requests.

This is the most important piece of work and takes a day to do properly.

Contents:
- How to parse each file type (pandoc for docx, pymupdf CLI for PDF, direct read for .md)
- The sections[] format for DesignAdvisor
- Full slide type catalogue (copied/adapted from the current design_advisor.py guide)
- How to call `export_typst_slides()` via Bash
- How to handle amendments (update slide spec dict in memory, re-call export)
- Output conventions (where to write PDFs, how to open them for the user)
- Overflow rules and audit patterns

### 3.2 Bridge server (`inkline/app/claude_bridge.py`)

Direct copy of `aria/scripts/claude_bridge.py`. Zero changes needed except:
- Default port: `8082` (same, since Inkline bridge and Aria bridge won't run together)
- Log dir: `~/.local/share/inkline/logs/`
- Remove the `/vision` endpoint (not needed for now — can add if visual audit is wanted)

~350 lines, already written.

### 3.3 CLI entry point (`inkline/app/cli.py`)

```bash
inkline serve          # starts bridge on 8082 + opens thin WebUI at 8090
inkline serve --port-bridge 8082 --port-ui 8090
inkline bridge         # bridge only, no WebUI
inkline mcp            # MCP server only
```

`inkline serve` does two things: starts the bridge as a subprocess, then starts
the thin WebUI server to serve the HTML page.

### 3.4 Thin WebUI (`inkline/app/static/`)

Not Chainlit. A single `index.html` (~200 lines) with:
- File upload (drag and drop or browse)
- Text input for the intent ("turn this into an investor pitch")
- Chat message history
- PDF preview (iframe pointing at the last generated file)
- Download button

The page POSTs to `/prompt` on the bridge, streams the response, shows it in
the chat. That's it. No React, no build step, no framework. Vanilla JS.

The bridge response already has the text response; Claude will have written the
PDF to a temp path and told the user where it is. The WebUI can serve the PDF
at `/output/{filename}` from a simple file-serving route in the bridge.

### 3.5 MCP server (`inkline/app/mcp_server.py`)

For users who want to use Inkline from Claude.ai web or Claude Desktop. Built
with `fastmcp`. Four tools:

```python
@mcp.tool()
def generate_deck(content: str, intent: str, template: str = "consulting",
                  brand: str = "minimal", output_path: str = "") -> dict:
    """Generate a slide deck from content. Returns PDF path and slide count."""

@mcp.tool()
def render_slides(slides_json: str, template: str = "consulting",
                  brand: str = "minimal", output_path: str = "") -> dict:
    """Render a JSON slide spec to PDF. Use when you have the slide specs already."""

@mcp.tool()
def list_templates() -> list[str]:
    """List available Inkline templates."""

@mcp.tool()
def list_themes(category: str = "") -> list[str]:
    """List available Inkline themes, optionally filtered by category."""
```

The MCP tools call Inkline's Python API directly (no bridge needed). The
conversation and amendment loop is handled by the Claude.ai/Desktop interface
natively.

### 3.6 File conversion utilities (optional, minimal)

Rather than building Python parsers:
- `.docx` → `pandoc input.docx -o input.md` via Bash (Claude can call this itself)
- `.pdf` → `python -c "import pymupdf; ..."` one-liner via Bash
- `.pptx` → `python -c "from pptx import Presentation; ..."` one-liner via Bash

Claude Code can call all of these with its Bash tool. We only need Python
utilities if we want the MCP server to accept binary files — in which case, a
single `parse_file(path: str) -> str` function that dispatches by extension,
~50 lines.

---

## 4. The amendment loop — no custom code needed

This is where the Claude Code wrapper pattern shines. The amendment loop is just
Claude's native conversation capability:

```
User: [uploads report.docx] "Make it a 10-slide investor pitch"
Claude: [calls pandoc via Bash, reads .md output, structures sections,
         calls export_typst_slides, writes /tmp/deck.pdf]
         "Done — 10 slides rendered. [PDF preview] Want me to change anything?"

User: "Slide 3 is too text-heavy"
Claude: [remembers current slide specs in its context window, identifies slide 3,
         changes layout from 'content' to 'three_card', re-calls export_typst_slides]
         "Updated slide 3 to a three-card layout. [new preview]"

User: "Add a revenue waterfall chart after slide 5"
Claude: [adds chart_request to a new chart_caption slide at index 5,
         re-renders]
         "Added a waterfall chart slide. [new preview]"
```

No AmendmentAgent class. No diff-spec protocol. Claude Code just keeps the slide
specs in its context window across turns and edits them. This is what Claude Code
is built for.

**One thing to put in CLAUDE.md:** Instruct Claude to always print the current
slide list after any amendment so the user can orient themselves, and to write
the PDF to a consistent path (`/tmp/inkline_session/deck.pdf`) so the WebUI
iframe can always point to the same URL.

---

## 5. WebUI question

**Is a browser-based UI worth building?** Yes, for one specific reason: non-technical
users who want to see a PDF preview without finding a file in `/tmp` and opening
it manually.

**Which approach:**

| Option | Effort | UX | For whom |
|--------|--------|-----|---------|
| Claude Code CLI directly | 0 (already works) | Terminal | Technical users |
| Thin HTML/JS page → bridge | ~1 day | Chat + PDF preview in browser | Semi-technical users |
| MCP + Claude.ai web app | ~1 day (MCP only) | Full Claude.ai chat | Non-technical users |
| Chainlit | 1–2 weeks | Chat + file upload | Nobody, unnecessary |

The thin HTML page is worth 1 day to build — it gives you file drag-and-drop, a
PDF iframe preview, and a download button without any framework overhead. The PDF
is the hardest part of the UX; once you have an iframe showing the live render,
the tool feels finished.

The MCP route (Claude.ai) is the best for truly non-technical users who already
use Claude.ai, because they get Claude's full interface for free.

**Recommendation:** Build both the thin WebUI (1 day) and the MCP server (1 day).
Skip Chainlit entirely.

---

## 6. Phased build plan

### Phase 1 — Works from Claude Code CLI (2–3 days)
1. **CLAUDE.md** — comprehensive Inkline usage guide for Claude
2. **Slash commands** — `/generate-deck`, `/amend-slide` as Claude Code custom commands
3. **Test**: open Claude Code in the inkline directory, upload a .docx, ask for a pitch deck

At the end: `claude` in the Inkline directory → full conversational slide generation works.
No new Python code, just a great CLAUDE.md.

### Phase 2 — Browser access (1 day)
1. **Bridge server** — copy from Aria, adjust log paths and port
2. **Thin WebUI** — single `index.html`, PDF iframe, file upload, chat
3. **`inkline serve` CLI command** — starts bridge + serves static HTML
4. **`inkline bridge` CLI command** — bridge only (for headless server use)

At the end: `inkline serve` → browser opens → full UX for non-technical users.

### Phase 3 — MCP integration (1 day)
1. **`inkline_mcp.py`** — fastmcp, four tools, ~150 lines
2. **`inkline mcp` CLI command**
3. **Test in Claude Desktop** — add to MCP config, verify all four tools

At the end: Inkline is accessible from Claude.ai and Claude Desktop as a tool.

### Phase 4 — Polish (ongoing)
- `parse_file()` utility for MCP binary file handling
- Docker container for self-hosted deploy (`inkline serve` in Docker)
- README update with the three usage paths

---

## 7. Total new code

| File | Lines | Notes |
|------|-------|-------|
| `CLAUDE.md` (Inkline root) | ~200 | Markdown, no Python |
| `inkline/app/claude_bridge.py` | ~350 | Copy from Aria, minimal changes |
| `inkline/app/static/index.html` | ~200 | Vanilla HTML/JS |
| `inkline/app/mcp_server.py` | ~150 | fastmcp, 4 tools |
| `inkline/app/cli.py` | ~80 | Click/argparse entry points |
| `inkline/app/parsers.py` | ~60 | Optional: parse_file() for MCP |
| **Total** | **~1040** | |

Compare to original spec: ~2000 lines with ContentAgent, AmendmentAgent,
SessionManager, FastAPI, Chainlit. The Claude Code wrapper is half the code
with better behaviour.

---

## 8. New dependencies (minimal)

```toml
[project.optional-dependencies]
app = ["aiohttp>=3.9"]           # bridge server
mcp = ["fastmcp>=0.5"]           # MCP server
```

`pandoc` is a system dependency for .docx → .md conversion. Document in
README that users should `apt install pandoc` or `brew install pandoc`. Claude
will call it via Bash, not Python.

---

## 9. What stays as-is

Everything in `inkline/typst/`, `inkline/intelligence/`, `inkline/html/`, etc.
is unchanged. The `app/` layer is purely additive. External API users keep
calling `export_typst_slides()` etc. directly as documented in the README.
