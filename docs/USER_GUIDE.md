# Inkline User Guide

**Branded document and presentation toolkit — Typst, HTML, PDF, PPTX, Google Slides.**

---

## Table of contents

1. [How Inkline works](#how-inkline-works)
2. [Installation](#installation)
3. [Standalone app — conversational WebUI](#standalone-app--conversational-webui)
4. [MCP integration — Claude Desktop and Claude.ai](#mcp-integration--claude-desktop-and-claudeai)
5. [Quick start — Python API, no LLM required](#quick-start--python-api-no-llm-required)
6. [LLM design advisor](#llm-design-advisor)
7. [Brands and themes](#brands-and-themes)
8. [Chart renderer](#chart-renderer)
9. [Overflow audit](#overflow-audit)
10. [Configuration reference](#configuration-reference)
11. [Troubleshooting](#troubleshooting)

---

## How Inkline works

Inkline has three layers. Each one can be used independently.

### Layer 1 — Render layer (no API key, no LLM)

You describe slides as Python dicts, call `export_typst_slides()`, and get a
publication-quality PDF. Fully deterministic.

```
Python slide specs  →  Typst compiler (Rust)  →  PDF
```

### Layer 2 — Intelligence layer (optional LLM)

You pass raw content sections (facts, metrics, narratives) to `DesignAdvisor`, and
it decides layouts, chart types, and visual hierarchy.

```
Raw content sections  →  DesignAdvisor  →  slide specs  →  PDF
```

Three modes:

| Mode | Description | Requires |
|------|-------------|---------|
| `rules` | Deterministic heuristics | Nothing |
| `llm` | LLM picks layouts using 10 design playbooks | `ANTHROPIC_API_KEY` or Claude Code |
| `advised` | Rules first, LLM reviews | `ANTHROPIC_API_KEY` or Claude Code |

### Layer 3 — Standalone app (conversational, no Python required)

A Claude Code-powered bridge that lets you describe what you want in plain English.
Upload a file, say what to do with it, and get a PDF in the browser — then keep
talking to refine it.

```
Natural language + file  →  Claude Code (agentic)  →  Inkline Python API  →  PDF
```

**You can use Inkline end-to-end without any API key** using the render layer
directly or `DesignAdvisor(mode="rules")`.

---

## Installation

### Prerequisites

| Dependency | Required for | Install |
|-----------|--------------|---------|
| Python ≥ 3.11 | Everything | [python.org](https://python.org) |
| Typst | PDF output | Bundled with `inkline[typst]` |
| Claude Code CLI | Standalone app + LLM via subscription | [docs.claude.com/claude-code](https://docs.claude.com/claude-code) |
| pandoc | `.docx` input in the standalone app | `brew install pandoc` / `apt install pandoc` |

### Install Inkline

```bash
# Minimal (Markdown → HTML only)
pip install inkline

# PDF output (Typst — recommended)
pip install "inkline[typst]"

# Charts
pip install "inkline[charts]"

# LLM design advisor (Anthropic SDK)
pip install "inkline[intelligence]"

# Standalone WebUI + Claude bridge
pip install "inkline[app]"

# MCP server for Claude Desktop / Claude.ai
pip install "inkline[mcp]"

# Everything
pip install "inkline[all]"
```

### Install from source

```bash
git clone https://github.com/u3126117/inkline.git
cd inkline
pip install -e ".[all]"
```

---

## Standalone app — conversational WebUI

The standalone app is the best starting point for non-technical users, or anyone
who wants to go from a file to a slide deck without writing code.

### Requirements

1. Install Claude Code and authenticate:
   ```bash
   npm install -g @anthropic-ai/claude-code
   claude /login
   ```
2. Optionally install `pandoc` for `.docx` input:
   ```bash
   brew install pandoc      # macOS
   apt install pandoc       # Linux
   ```

### Starting the app

```bash
pip install "inkline[all]"
inkline serve
```

The browser opens automatically at `http://localhost:8082`.

```bash
inkline serve --port 9000      # custom port
inkline serve --no-browser     # start without opening browser
inkline bridge                 # bridge only — no browser, for headless use
```

### The workflow

**Step 1 — Upload a file (optional)**

Drag and drop a `.md`, `.docx`, `.pdf`, or `.pptx` file onto the upload area.
The file is saved locally and its path is automatically attached to your next message.
No file is uploaded to any external service.

**Step 2 — Describe what you want**

```
"Turn this into a 10-slide investor pitch for a technical audience."
"Make a board update deck from these quarterly results."
"Create a 6-slide product overview using the Stripe theme."
```

Claude parses the file, structures the content into Inkline sections, calls
`DesignAdvisor`, and renders the PDF. Progress is shown in the chat. The PDF
appears in the right-hand preview panel when ready.

**Step 3 — Refine in conversation**

Keep talking to amend the deck:

```
"Slide 3 is too text-heavy — make it more visual."
"Add a waterfall chart for the cost breakdown after slide 5."
"Change the theme to something darker."
"Remove slide 7 and reorder 4 and 6."
"Make all titles shorter — they feel long."
```

Claude edits the slide specs in its context and re-renders. Only changed slides
are re-compiled where possible.

**Step 4 — Download**

Click the **Download PDF** button in the top-right of the preview panel.

### Output location

All generated files are written to `~/.local/share/inkline/output/`:

| File | Description |
|------|-------------|
| `deck.pdf` | Current session PDF (always overwritten on re-render) |
| `charts/` | Pre-rendered chart PNGs |

Uploaded files are saved to `~/.local/share/inkline/uploads/`.

### Using Claude Code directly (no browser)

If you prefer the terminal, open Claude Code in the Inkline project directory.
The `CLAUDE.md` at the repo root is automatically loaded as Claude's context —
it contains the full API reference, slide type catalogue, and output conventions.

```bash
cd /path/to/inkline
claude
```

Then just describe what you want. Slash commands are available:

- `/generate-deck <file or description>` — generate a deck
- `/amend <instruction>` — amend the current deck

---

## MCP integration — Claude Desktop and Claude.ai

The MCP server exposes Inkline as tools inside Claude Desktop and Claude.ai,
so you can generate decks as part of any Claude conversation.

### Setup

```bash
pip install "inkline[mcp]"
```

**Claude Desktop** — add to `~/Library/Application Support/Claude/claude_desktop_config.json`
(macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "inkline": {
      "command": "inkline",
      "args": ["mcp"]
    }
  }
}
```

Restart Claude Desktop. You will see Inkline tools available in the tool selector.

**Claude.ai** — use the MCP server configuration in Claude.ai settings (requires
a supported plan).

### Available tools

| Tool | Description |
|------|-------------|
| `inkline_generate_deck` | Content text + intent → rendered PDF |
| `inkline_render_slides` | JSON slide spec array → rendered PDF |
| `inkline_list_templates` | List all available templates |
| `inkline_list_themes` | List themes, optionally filtered by category |

### Example usage in Claude

```
"Use inkline to turn this text into a consulting deck:
 [paste your document text]
 Make it 8 slides, consulting template, minimal brand."
```

Claude will call `inkline_generate_deck` and return the PDF path.

---

## Quick start — Python API, no LLM required

### Markdown → HTML (CLI)

```bash
inkline-html report.md
inkline-html report.md --brand minimal --title "Q4 Review" --out q4_review.html
```

### Markdown → PDF (CLI)

```bash
inkline-pdf report.md
inkline-pdf report.md --brand minimal --title "Q4 Review" --out q4_review.pdf
```

### Branded slides from Python (no LLM)

```python
from inkline.typst import export_typst_slides

slides = [
    {"slide_type": "title", "data": {
        "company": "Acme Corp",
        "tagline": "Series B Pitch",
        "date": "April 2026",
    }},
    {"slide_type": "three_card", "data": {
        "section": "Problem",
        "title": "Three pain points we solve",
        "cards": [
            {"title": "Fragmented data",  "body": "Siloed dashboards, no single source of truth."},
            {"title": "Manual reporting", "body": "Analysts spend 80% of their week in PowerPoint."},
            {"title": "Stale insights",   "body": "Reports are outdated before they reach the board."},
        ],
    }},
    {"slide_type": "kpi_strip", "data": {
        "section": "Traction",
        "title": "2026 YTD",
        "kpis": [
            {"value": "34%",   "label": "Revenue growth", "highlight": True},
            {"value": "$4.2M", "label": "ARR"},
            {"value": "87",    "label": "Customers"},
        ],
    }},
    {"slide_type": "closing", "data": {
        "name": "Jane Smith", "role": "CEO", "email": "jane@acme.com",
        "company": "Acme Corp", "tagline": "Let's build this together.",
    }},
]

export_typst_slides(
    slides=slides,
    output_path="acme_pitch.pdf",
    brand="minimal",
    template="consulting",
)
```

### Branded document from Python (no LLM)

```python
from inkline.typst import export_typst_document

export_typst_document(
    markdown="# Q4 2026 Review\n\nRevenue grew 34%...",
    output_path="q4_report.pdf",
    brand="minimal",
    title="Q4 2026 Review",
    subtitle="Board update",
    date="April 2026",
    author="Finance team",
    paper="a4",
)
```

### Generating slides from a document (Python)

For `.md` or `.txt`, read directly. For `.docx`, convert with pandoc first:

```bash
pandoc input.docx -o input.md --wrap=none
```

Then use `DesignAdvisor` in `rules` mode (no API key):

```python
from pathlib import Path
from inkline.intelligence import DesignAdvisor
from inkline.typst import export_typst_slides

md = Path("input.md").read_text(encoding="utf-8")

sections = [{"type": "narrative", "title": "Overview", "narrative": md}]

advisor = DesignAdvisor(brand="minimal", template="consulting", mode="rules")
slides = advisor.design_deck(title="My Report", sections=sections, audience="executive team")
export_typst_slides(slides=slides, output_path="output.pdf", brand="minimal")
```

---

## LLM design advisor

`DesignAdvisor` with `mode="llm"` delegates layout decisions to an LLM backed by
10 curated design playbooks (MBB-style chart selection, typography, colour theory,
professional exhibit design, and more).

### Option A — Anthropic API key

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

```python
from inkline.intelligence import DesignAdvisor

advisor = DesignAdvisor(brand="minimal", template="consulting", mode="llm")
slides = advisor.design_deck(
    title="Q4 Strategy Review",
    sections=[
        {"type": "executive_summary", "metrics": {"ARR": "$4.2M", "Growth": "34%"}, "narrative": "..."},
        {"type": "financial_overview", "table_data": {"headers": [...], "rows": [...]}},
        {"type": "risks", "rag": {...}},
    ],
    audience="investors",
    goal="secure term sheet",
)
```

### Option B — Claude Code (no API key, uses your subscription)

```python
from inkline.intelligence import DesignAdvisor, build_claude_code_caller

caller = build_claude_code_caller(model="sonnet")

advisor = DesignAdvisor(
    brand="minimal",
    template="consulting",
    mode="llm",
    llm_caller=caller,
)
slides = advisor.design_deck(...)
```

### Option C — Rules mode (no LLM, no API key)

```python
advisor = DesignAdvisor(brand="minimal", template="consulting", mode="rules")
```

### LLM caller is fully pluggable

`LLMCaller` is `Callable[[system_prompt: str, user_prompt: str], str]`. Plug in
any provider:

```python
import openai

def openai_caller(system: str, user: str) -> str:
    resp = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": user}],
    )
    return resp.choices[0].message.content

advisor = DesignAdvisor(brand="minimal", mode="llm", llm_caller=openai_caller)
```

---

## Brands and themes

### Built-in brand

Inkline ships one public brand: `minimal`. It works out of the box.

### Custom brand

Drop a `.py` file in any of these directories — auto-discovered at import time:

1. Every path in `$INKLINE_BRANDS_DIR`
2. `~/.config/inkline/brands/`
3. `./inkline_brands/`

```python
# ~/.config/inkline/brands/mycorp.py
from inkline.brands import BaseBrand

MyCorpBrand = BaseBrand(
    name="mycorp",
    display_name="My Corporation",
    primary="#0B5FFF", secondary="#00C2A8",
    background="#FFFFFF", surface="#0A2540", text="#111827",
    muted="#6B7280", border="#E5E7EB", light_bg="#F8FAFC",
    heading_font="Inter", body_font="Inter",
    logo_dark_path="mycorp_logo_white.png",
    logo_light_path="mycorp_logo_dark.png",
    confidentiality="Private & Confidential",
    footer_text="My Corporation",
)
```

Asset files are resolved from `$INKLINE_ASSETS_DIR`, `~/.config/inkline/assets/`,
or `./inkline_assets/`.

### Templates (37 built-in)

**Built-in:** `consulting`, `executive`, `minimalism`, `newspaper`, `investor`,
`pitch`, `dark`, `editorial`, `boardroom`, `brand`

**Design-system styles:** `dmd_stripe`, `dmd_vercel`, `dmd_notion`, `dmd_apple`,
`dmd_spotify`, `dmd_tesla`, `dmd_airbnb`, `dmd_coinbase`, `dmd_shopify`,
`dmd_figma`, `dmd_framer`, `dmd_cursor`, `dmd_warp`, `dmd_supabase`, `dmd_uber`,
`dmd_ferrari`, `dmd_bmw`, `dmd_mongodb`, `dmd_intercom`, `dmd_webflow`,
`dmd_miro`, `dmd_posthog`, `dmd_raycast`, `dmd_revolut`, `dmd_superhuman`,
`dmd_zapier`, `dmd_claude`

### Themes (90 built-in)

```python
from inkline.typst.themes import list_themes, search_themes

list_themes(category="consulting")    # Strategy Blue, Strategy Green, Strategy Red, Professional Services, Advisory Orange, Advisory Yellow, Corporate Blue
list_themes(category="dark")          # Nord, Dracula, Catppuccin, Carbon
search_themes("gold")                 # Aurum, Gold Leaf, ...
```

---

## Chart renderer

### Standalone chart

```python
from inkline.typst.chart_renderer import render_chart_for_brand

render_chart_for_brand(
    chart_type="waterfall",
    data={
        "items": [
            {"label": "Revenue", "value": 120, "total": True},
            {"label": "COGS",    "value": -40},
            {"label": "OpEx",    "value": -35},
            {"label": "EBITDA",  "value": 45,  "total": True},
        ],
    },
    output_path="waterfall.png",
    brand_name="minimal",
)
```

### Inline chart request (auto-rendered at export time)

```python
{
    "slide_type": "chart_caption",
    "data": {
        "section": "Financials",
        "title": "Revenue growing 34% YoY",
        "image_path": "revenue.png",
        "chart_request": {
            "chart_type": "area_chart",
            "chart_data": {
                "x": ["Q1", "Q2", "Q3", "Q4"],
                "series": [{"name": "Revenue", "values": [1.2, 1.8, 2.4, 3.1]}],
                "y_label": "$M",
            },
        },
        "caption": "ARR compounding at 34% per quarter",
        "bullets": ["Q4 $3.1M, up from $1.2M in Q1", "Net revenue retention >120%"],
    },
}
```

**Standard charts (11):** `line_chart`, `area_chart`, `scatter`, `waterfall`,
`donut`, `pie`, `stacked_bar`, `grouped_bar`, `heatmap`, `radar`, `gauge`

**Institutional exhibits (4):** `marimekko`, `entity_flow`, `divergent_bar`,
`horizontal_stacked_bar`

**Infographic archetypes (16):** `iceberg`, `sidebar_profile`, `funnel_kpi_strip`,
`persona_dashboard`, `radial_pinwheel`, `hexagonal_honeycomb`, `semicircle_taxonomy`,
`process_curved_arrows`, `pyramid_detailed`, `ladder`, `petal_teardrop`,
`funnel_ribbon`, `dual_donut`, `waffle`, `metaphor_backdrop`, `chart_row`

---

## Overflow audit

```python
from inkline.intelligence import audit_deck, format_report

warnings = audit_deck(slides)
print(format_report(warnings))
# OVERFLOW AUDIT: 0 errors, 1 warning, 0 info
# [WARN] slide 3 (content): field 'items' has 9 items but slide capacity is 6
```

`export_typst_slides()` runs the audit automatically. Pass `audit=False` to skip.

---

## Configuration reference

### Environment variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `ANTHROPIC_API_KEY` | Anthropic SDK for LLM mode | `sk-ant-...` |
| `INKLINE_BRANDS_DIR` | Additional brand paths | `/home/user/my_brands` |
| `INKLINE_THEMES_DIR` | Additional theme paths | `/home/user/my_themes` |
| `INKLINE_TEMPLATES_DIR` | Additional template paths | `/home/user/my_templates` |
| `INKLINE_ASSETS_DIR` | Additional asset paths (logos, fonts) | `/home/user/assets` |

### Config and output directories

| Directory | Purpose |
|-----------|---------|
| `~/.config/inkline/brands/` | Private brand `.py` files |
| `~/.config/inkline/themes/` | Custom theme `.py` files |
| `~/.config/inkline/templates/` | Custom template `.py` files |
| `~/.config/inkline/assets/` | Logo PNGs, custom fonts |
| `~/.local/share/inkline/output/` | Generated PDFs and charts (standalone app) |
| `~/.local/share/inkline/uploads/` | Uploaded files (standalone app) |
| `~/.local/share/inkline/logs/` | Bridge server logs |

### What works without any API key or Claude Code

| Feature | Works offline |
|---------|--------------|
| `inkline-html` CLI | Yes |
| `inkline-pdf` CLI | Yes |
| `export_typst_slides()` with hand-crafted specs | Yes |
| `export_typst_document()` | Yes |
| `render_chart_for_brand()` | Yes |
| `DesignAdvisor(mode="rules")` | Yes |
| Overflow audit | Yes |
| All 90 themes, 37 templates | Yes |
| `inkline serve` / standalone app | No — requires Claude Code |
| `DesignAdvisor(mode="llm")` | No — requires API key or Claude Code |

---

## Troubleshooting

### `typst` compilation fails

```bash
pip install --upgrade typst
```

### `ClaudeCodeNotInstalled` error

```bash
npm install -g @anthropic-ai/claude-code
claude /login
```

Or switch to `ANTHROPIC_API_KEY` mode, or use `DesignAdvisor(mode="rules")`.

### `inkline serve` shows "bridge degraded"

The `claude` CLI is not found on `$PATH`. Verify with `which claude`. If missing,
install Claude Code and run `claude /login`.

### `ANTHROPIC_API_KEY not set`

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

Or store in `~/.env` — Inkline checks there automatically:

```
ANTHROPIC_API_KEY=sk-ant-...
```

### PDF has missing fonts

Place font files in `~/.config/inkline/assets/`. The `minimal` brand uses Inter
and Source Sans 3, which are bundled with the package.

### Slide content overflows or gets cut off

```python
from inkline.intelligence import audit_deck, format_report
print(format_report(audit_deck(slides)))
```

Common causes: title > 50 characters, too many items per slide type, table
wider than 6 columns.

### `.docx` input in the standalone app fails

Install pandoc — the bridge uses it for `.docx` conversion:

```bash
brew install pandoc      # macOS
apt install pandoc       # Linux
winget install pandoc    # Windows
```

### WebUI PDF preview is blank

The PDF iframe is loaded from `/output/deck.pdf` on the bridge. If blank:
1. Check the chat for a `PDF ready:` message — this is what triggers the preview.
2. Verify `~/.local/share/inkline/output/deck.pdf` exists.
3. Try navigating directly to `http://localhost:8082/output/deck.pdf`.

---

## Further reading

- [README](../README.md) — full API reference, slide type catalogue, theme list
- [CLAUDE.md](../CLAUDE.md) — Claude Code usage guide (slide types, amendment patterns, code snippets)
- [Technical specification](TECHNICAL_SPEC.md) — architecture, data models, APIs
- [Archon audit workflow](ARCHON_AUDIT.md) — pipeline supervisor + two-agent audit loop
- [Standalone app spec](../plan_docs/inkline-standalone-app-spec.md) — architecture decisions
