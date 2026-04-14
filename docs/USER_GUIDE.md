# Inkline User Guide

**Branded document and presentation toolkit — Typst, HTML, PDF, PPTX, Google Slides.**

---

## Table of contents

1. [How Inkline works](#how-inkline-works)
2. [Installation](#installation)
3. [Quick start — no API key required](#quick-start--no-api-key-required)
4. [Generating slides from a Markdown file](#generating-slides-from-a-markdown-file)
5. [LLM design advisor](#llm-design-advisor)
6. [Brands and themes](#brands-and-themes)
7. [Chart renderer](#chart-renderer)
8. [Overflow audit](#overflow-audit)
9. [Configuration reference](#configuration-reference)
10. [Troubleshooting](#troubleshooting)

---

## How Inkline works

Inkline has two distinct layers. You can use either layer independently.

### Layer 1 — Render layer (no API key needed)

You describe slide content as Python dicts, pass them to `export_typst_slides()`,
and get a publication-quality PDF. No LLM. No API key. Deterministic.

```
Python slide specs  →  Typst compiler (Rust)  →  PDF
```

### Layer 2 — Intelligence layer (optional)

You pass raw content sections (facts, metrics, narratives) to `DesignAdvisor`,
and it decides which layouts, chart types, and visual hierarchy to use.

```
Raw content sections  →  DesignAdvisor  →  slide specs  →  PDF
```

The intelligence layer has three modes:

| Mode | Description | Requires |
|------|-------------|---------|
| `rules` | Deterministic heuristics — no API calls | Nothing |
| `llm` | LLM picks layouts using design playbooks | API key or Claude Code |
| `advised` | Rules decide, LLM reviews and tweaks | API key or Claude Code |

**You can use Inkline end-to-end without any API key** by using the render layer
directly, or by using `DesignAdvisor(mode="rules")`.

---

## Installation

### Prerequisites

| Dependency | Required for | Install |
|-----------|--------------|---------|
| Python ≥ 3.11 | Everything | [python.org](https://python.org) |
| Typst | PDF output | Installed automatically with `inkline[typst]` |
| `claude` CLI | LLM mode via Claude subscription | [Claude Code](https://docs.claude.com/claude-code) |

### Install Inkline

```bash
# Minimal install (Markdown → HTML only)
pip install inkline

# PDF output via Typst (recommended)
pip install "inkline[typst]"

# Charts (matplotlib)
pip install "inkline[charts]"

# LLM design advisor (Anthropic SDK)
pip install "inkline[intelligence]"

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

## Quick start — no API key required

### Markdown → HTML (CLI)

The simplest entry point. Pass a `.md` file and get a styled, branded HTML report.

```bash
inkline-html report.md
inkline-html report.md --brand minimal --title "Q4 Review" --out q4_review.html
```

### Markdown → PDF (CLI)

```bash
inkline-pdf report.md
inkline-pdf report.md --brand minimal --title "Q4 Review" --out q4_review.pdf
```

Both CLI tools read a `.md` file directly from disk — no Python code required.

### Branded slides from Python (no LLM)

Describe your slide content as Python dicts and call `export_typst_slides()`.
This is the render layer — fully deterministic, no API key:

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
            {"title": "Fragmented data", "body": "Siloed dashboards, no single source of truth."},
            {"title": "Manual reporting", "body": "Analysts spend 80% of their week in PowerPoint."},
            {"title": "Stale insights",   "body": "Reports are outdated before they reach the board."},
        ],
    }},
    {"slide_type": "kpi_strip", "data": {
        "section": "Traction",
        "title": "2026 YTD",
        "kpis": [
            {"value": "34%",  "label": "Revenue growth", "highlight": True},
            {"value": "$4.2M","label": "ARR"},
            {"value": "87",   "label": "Customers"},
        ],
    }},
    {"slide_type": "closing", "data": {
        "name": "Jane Smith",
        "role": "CEO",
        "email": "jane@acme.com",
        "company": "Acme Corp",
        "tagline": "Let's build this together.",
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
    paper="a4",   # or "letter"
)
```

---

## Generating slides from a Markdown file

Inkline does not currently have a one-command CLI for `.md → slides`. The
workflow is a short Python script:

```python
from pathlib import Path
from inkline.typst import export_typst_slides
from inkline.intelligence import DesignAdvisor

# 1. Read your content
md = Path("my_report.md").read_text(encoding="utf-8")

# 2. Describe your sections (what you want on each slide)
sections = [
    {"type": "executive_summary", "narrative": md, "title": "Overview"},
    # add more sections as needed
]

# 3. Use DesignAdvisor in rules mode (no API key)
advisor = DesignAdvisor(brand="minimal", template="consulting", mode="rules")
slides = advisor.design_deck(
    title="My Report",
    sections=sections,
    audience="executive team",
)

# 4. Export to PDF
export_typst_slides(slides=slides, output_path="output.pdf", brand="minimal")
```

For `.docx` input, first convert to Markdown using
[`pandoc`](https://pandoc.org/): `pandoc input.docx -o input.md`, then use the
workflow above.

---

## LLM design advisor

The `DesignAdvisor` with `mode="llm"` delegates layout decisions to an LLM,
backed by 10 curated design playbooks (MBB-style chart selection, typography,
colour theory, professional exhibit design, and more).

### Option A — Anthropic API key

Set `ANTHROPIC_API_KEY` in your environment:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

Then use `DesignAdvisor` normally — it picks up the key automatically:

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

If you have Claude Code installed and authenticated (`claude /login`), Inkline
can route all LLM calls through the local `claude` CLI — zero Anthropic API
credits consumed:

```python
from inkline.intelligence import DesignAdvisor, build_claude_code_caller

# Build a caller that routes through the local claude CLI
caller = build_claude_code_caller(model="sonnet")

advisor = DesignAdvisor(
    brand="minimal",
    template="consulting",
    mode="llm",
    llm_caller=caller,   # plug in the Claude Code caller
)
slides = advisor.design_deck(...)
```

Check whether Claude Code is available before instantiating:

```python
from inkline.intelligence import claude_code_available

if claude_code_available():
    from inkline.intelligence import build_claude_code_caller
    caller = build_claude_code_caller()
else:
    caller = None   # falls back to Anthropic SDK if key is set
```

### Option C — Rules mode (no LLM, no API key)

Deterministic heuristics assign layouts based on content shape. Covers 90% of
common cases well. No API calls, instant:

```python
advisor = DesignAdvisor(brand="minimal", template="consulting", mode="rules")
```

### LLM caller is fully pluggable

`LLMCaller` is just `Callable[[system_prompt: str, user_prompt: str], str]`.
You can inject OpenAI, Gemini, a local Ollama instance, or any LLM:

```python
import openai

def openai_caller(system: str, user: str) -> str:
    resp = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": system},
                  {"role": "user",   "content": user}],
    )
    return resp.choices[0].message.content

advisor = DesignAdvisor(brand="minimal", mode="llm", llm_caller=openai_caller)
```

---

## Brands and themes

### Built-in brand

Inkline ships with a single public brand: `minimal`. It works out of the box.

### Custom brand (private, not committed to this repo)

Drop a `.py` file in any of these directories and it is auto-discovered:

1. Every path in `$INKLINE_BRANDS_DIR` (colon-separated)
2. `~/.config/inkline/brands/`
3. `./inkline_brands/` (relative to where you run Python)

```python
# ~/.config/inkline/brands/mycorp.py
from inkline.brands import BaseBrand

MyCorpBrand = BaseBrand(
    name="mycorp",
    display_name="My Corporation",
    primary="#0B5FFF",
    secondary="#00C2A8",
    background="#FFFFFF",
    surface="#0A2540",
    text="#111827",
    muted="#6B7280",
    border="#E5E7EB",
    light_bg="#F8FAFC",
    heading_font="Inter",
    body_font="Inter",
    logo_dark_path="mycorp_logo_white.png",   # resolved from asset dirs
    logo_light_path="mycorp_logo_dark.png",
    confidentiality="Private & Confidential",
    footer_text="My Corporation",
)
```

Asset files (logos, fonts) are looked up in parallel asset directories:
`$INKLINE_ASSETS_DIR`, `~/.config/inkline/assets/`, `./inkline_assets/`.

### Templates (37 built-in)

```python
export_typst_slides(slides=slides, brand="minimal", template="consulting")
export_typst_slides(slides=slides, brand="minimal", template="dmd_stripe")
export_typst_slides(slides=slides, brand="minimal", template="pitch")
```

**Built-in templates:** `executive`, `minimalism`, `newspaper`, `investor`,
`consulting`, `pitch`, `dark`, `editorial`, `boardroom`, `brand`

**Design-system styles:** `dmd_stripe`, `dmd_vercel`, `dmd_notion`, `dmd_apple`,
`dmd_spotify`, `dmd_tesla`, `dmd_airbnb`, `dmd_coinbase`, `dmd_shopify`,
`dmd_figma`, `dmd_framer`, `dmd_cursor`, `dmd_warp`, `dmd_supabase`, `dmd_uber`,
`dmd_ferrari`, `dmd_bmw`, `dmd_mongodb`, `dmd_intercom`, `dmd_webflow`,
`dmd_miro`, `dmd_posthog`, `dmd_raycast`, `dmd_revolut`, `dmd_superhuman`,
`dmd_zapier`, `dmd_claude`

### Themes (90 built-in)

```python
from inkline.typst.themes import list_themes, search_themes

list_themes(category="consulting")    # McKinsey, BCG, Bain, Deloitte, PwC, EY, KPMG
list_themes(category="dark")          # Nord, Dracula, Catppuccin, Carbon
search_themes("gold")                  # Aurum, Gold Leaf, ...
```

---

## Chart renderer

Inkline renders charts as PNGs via matplotlib and embeds them in slides.

### Standalone chart

```python
from inkline.typst.chart_renderer import render_chart_for_brand

render_chart_for_brand(
    chart_type="waterfall",
    data={
        "items": [
            {"label": "Revenue",   "value": 120, "total": True},
            {"label": "COGS",      "value": -40},
            {"label": "OpEx",      "value": -35},
            {"label": "EBITDA",    "value": 45,  "total": True},
        ],
    },
    output_path="waterfall.png",
    brand_name="minimal",
)
```

### Inline chart request (auto-rendered at export time)

Embed a chart request directly in a slide spec. Inkline renders the chart and
wires it into the layout automatically:

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
        "bullets": [
            "Q4 $3.1M, up from $1.2M in Q1",
            "Net revenue retention >120%",
            "Two enterprise deals signed in Q3",
        ],
    },
}
```

**Available chart types:**
`line_chart`, `area_chart`, `scatter`, `waterfall`, `donut`, `pie`,
`stacked_bar`, `grouped_bar`, `heatmap`, `radar`, `gauge`,
`marimekko`, `entity_flow`, `divergent_bar`, `horizontal_stacked_bar`

**Infographic archetypes (16):**
`iceberg`, `sidebar_profile`, `funnel_kpi_strip`, `persona_dashboard`,
`radial_pinwheel`, `hexagonal_honeycomb`, `semicircle_taxonomy`,
`process_curved_arrows`, `pyramid_detailed`, `ladder`, `petal_teardrop`,
`funnel_ribbon`, `dual_donut`, `waffle`, `metaphor_backdrop`, `chart_row`

---

## Overflow audit

Inkline checks every slide against hard capacity limits (title length, item
counts, cell widths) before compilation:

```python
from inkline.intelligence import audit_deck, format_report

warnings = audit_deck(slides)
print(format_report(warnings))
# OVERFLOW AUDIT: 0 errors, 1 warning, 0 info
# [WARN] slide 3 (content): field 'items' has 9 items but slide capacity is 6
```

`export_typst_slides()` runs the audit automatically. Pass `audit=False` to
disable it:

```python
export_typst_slides(slides=slides, output_path="out.pdf", audit=False)
```

---

## Configuration reference

### Environment variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `ANTHROPIC_API_KEY` | Anthropic SDK for LLM mode | `sk-ant-...` |
| `INKLINE_BRANDS_DIR` | Additional brand discovery paths | `/home/user/my_brands` |
| `INKLINE_THEMES_DIR` | Additional theme discovery paths | `/home/user/my_themes` |
| `INKLINE_TEMPLATES_DIR` | Additional template discovery paths | `/home/user/my_templates` |
| `INKLINE_ASSETS_DIR` | Additional asset search paths (logos, fonts) | `/home/user/brand_assets` |

### Personal config directory

`~/.config/inkline/` is the default location for private brands, themes,
templates, and assets. Subdirectory layout:

```
~/.config/inkline/
├── brands/       # .py files defining BaseBrand instances
├── themes/       # .py files defining theme dicts
├── templates/    # .py files defining template dicts
└── assets/       # logo PNGs, custom fonts, etc.
```

### What does NOT require Claude Code or an API key

Everything in this table works without any LLM:

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

---

## Troubleshooting

### `typst` compilation fails

Inkline uses the `typst` Python package which bundles the Typst binary.
If it fails, try:

```bash
pip install --upgrade typst
```

On some systems you may need to install `typst` separately:
[typst.app/docs/guides](https://typst.app/docs/guides)

### `ClaudeCodeNotInstalled` error

You passed `build_claude_code_caller()` but the `claude` CLI is not on
`$PATH`. Options:

1. Install Claude Code: `npm install -g @anthropic-ai/claude-code`
2. Authenticate: `claude /login`
3. Or switch to API key mode: `export ANTHROPIC_API_KEY=sk-ant-...`
4. Or switch to rules mode: `DesignAdvisor(mode="rules")`

### `ANTHROPIC_API_KEY not set` error

Set the key in your shell:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

Or store it in `~/.env` — Inkline checks there automatically:

```
ANTHROPIC_API_KEY=sk-ant-...
```

### PDF has missing fonts / boxes instead of text

Make sure the fonts referenced by your brand are installed on the system,
or place them in `~/.config/inkline/assets/`. The `minimal` brand uses
Inter and Source Sans 3, which are bundled with the package.

### Slide content overflows or gets cut off

Run the overflow audit before exporting to identify problematic slides:

```python
from inkline.intelligence import audit_deck, format_report
print(format_report(audit_deck(slides)))
```

Common causes: title > 50 characters, too many bullet items, table wider
than 6 columns. See the slide type limits in the [README](../README.md).

### `.docx` input is not supported

Convert to Markdown first:

```bash
pandoc input.docx -o input.md
inkline-pdf input.md
```

---

## Further reading

- [README](../README.md) — full API reference, slide type catalogue, theme list
- [Technical specification](TECHNICAL_SPEC.md) — architecture, data models, APIs
- [Archon audit workflow](ARCHON_AUDIT.md) — pipeline supervisor + two-agent audit loop
- [Closed-loop audit spec](CLOSED_LOOP_AUDIT_SPEC.md) — QA architecture
- [Commercial pitch](PITCH.md) — capabilities, competitive comparison
