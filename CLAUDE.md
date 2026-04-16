# Inkline — Claude Code Usage Guide

Inkline is a Python library for generating branded, publication-quality slide decks
and documents. You (Claude) drive it via Bash. This file is your complete reference.

---

## ⚠️ MODEL POLICY

- **Specs, architecture, design decisions**: Always use **Opus** (`claude-opus-4-6`)
- **Implementation / coding**: Use **Sonnet** (`claude-sonnet-4-6`) unless Opus is explicitly requested

## ⚠️ SPEC BEFORE CODE

All non-trivial changes to Inkline must start with a spec in `plan_docs/`.

| Spec | Status | Covers |
|---|---|---|
| `plan_docs/impeccable-design-intelligence-spec.md` | Approved for implementation | Anti-pattern library, quality scoring, auto-polish, design brief generation |
| `plan_docs/design-system-spec.md` | Approved for implementation | Decision framework, taste enforcer, self-learning, deck ingestion |
| `plan_docs/visual-auditor-self-learning-spec.md` | Superseded by design-system-spec | Per-brand pattern memory (partially implemented) |
| `plan_docs/two-agent-design-loop-spec.md` | Implemented | Phase 1 planner + Phase 2 DesignAdvisor |
| `plan_docs/structural-fixes-v0.4-spec.md` | Implemented | v0.4 structural and overflow fixes |
| `plan_docs/inkline-standalone-app-spec.md` | Implemented | Bridge + MCP server + CLI |
| `plan_docs/ARCHON_AUDIT.md` | Implemented | Archon phase supervisor |
| `plan_docs/CLOSED_LOOP_AUDIT_SPEC.md` | Implemented (partial) | Two-loop QA pipeline |

When adding a new significant feature, add a spec to `plan_docs/` before writing code.

---

## ⚠️ CORRECT WORKFLOW — READ FIRST

**Never run standalone Python scripts to generate decks or documents.**
**Never call `export_typst_slides()` or `export_typst_document()` directly outside an Archon phase.**

All Inkline output MUST flow through the structured Archon pipeline. This applies equally to
slide decks, PDF documents, and any other output type. Calling an export function directly
bypasses the visual audit and ships broken output without detection.

The correct workflow for all output types:

1. **Confirm the bridge is running** — `inkline serve` or `inkline bridge` must be active on port 8082.
   Check: `curl -s http://localhost:8082/ | head -1`

2. **Upload the source file** via the bridge:
   ```bash
   curl -X POST http://localhost:8082/upload -F "file=@/path/to/report.md"
   # Returns: {"path": "/home/.../.local/share/inkline/uploads/report.md", "filename": "report.md"}
   ```

3. **Send the generation prompt** to the bridge and let it run:
   ```bash
   # For slide decks (default):
   curl -X POST http://localhost:8082/prompt \
     -H "Content-Type: application/json" \
     -d '{"prompt": "I have uploaded a file at: <path>. Generate a deck ...", "mode": "slides"}'

   # For branded PDF documents / reports:
   curl -X POST http://localhost:8082/prompt \
     -H "Content-Type: application/json" \
     -d '{"prompt": "I have uploaded a file at: <path>. Generate a PDF report ...", "mode": "document"}'
   ```

4. **Monitor via logs** — do not intervene. The bridge runs Claude agentic mode which
   executes the 4-phase Archon pipeline (see Pipeline Reference below), then announces
   `PDF ready: <path>` when done.

**Why this matters:** Calling `export_typst_slides()` or `export_typst_document()` directly
bypasses the per-page visual audit (run via the `/vision` endpoint). The structural page-count
check passes even when slides are visually broken. The Archon pipeline is the only gate that
catches rendering failures, overflow, and brand violations.

**Enforcement:** The bridge detects bypass attempts. If a `PDF ready:` announcement appears
without any `[ARCHON] Phase:` markers in the output stream, the response includes
`"archon_bypassed": true` as a violation flag.

---

## Pipeline Reference — Archon-Wrapped Patterns

These are the ONLY correct ways to generate Inkline output. Both use the same 4-phase
Archon supervisor. Copy these patterns exactly.

### Slides pipeline (mode: "slides")

```python
import subprocess, json, base64
import pymupdf
from pathlib import Path
from inkline.intelligence import DesignAdvisor
from inkline.typst import export_typst_slides

OUTPUT = Path("~/.local/share/inkline/output/deck.pdf").expanduser()
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

# ── Phase 1: parse_markdown ─────────────────────────────────────────────────
print("[ARCHON] Phase: parse_markdown")
# ... read and parse input file into sections list ...
print("[ARCHON] parse_markdown → OK in 0.5s")

# ── Phase 2: design_advisor_llm ─────────────────────────────────────────────
print("[ARCHON] Phase: design_advisor_llm")
advisor = DesignAdvisor(brand="minimal", template="consulting", mode="llm")
slides = advisor.design_deck(title="My Deck", sections=sections)
print("[ARCHON] design_advisor_llm → OK in 45.2s")

# ── Phase 3: save_slide_spec ─────────────────────────────────────────────────
print("[ARCHON] Phase: save_slide_spec")
import json
Path("~/.local/share/inkline/output/deck_spec.json").expanduser().write_text(
    json.dumps(slides, indent=2))
print("[ARCHON] save_slide_spec → OK in 0.1s")

# ── Phase 4: export_pdf_with_audit ──────────────────────────────────────────
print("[ARCHON] Phase: export_pdf_with_audit")
export_typst_slides(slides=slides, output_path=str(OUTPUT), brand="minimal", template="consulting")

# Per-slide visual audit via bridge /vision endpoint
doc = pymupdf.open(str(OUTPUT))
n = len(doc)
for i, page in enumerate(doc):
    pix = page.get_pixmap(dpi=120)
    img_b64 = base64.b64encode(pix.tobytes("png")).decode()
    r = subprocess.run(["curl", "-s", "-X", "POST", "http://localhost:8082/vision",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({
            "image_base64": img_b64,
            "prompt": f"Slide {i+1}/{n}: Are there any overflow, blank content areas, or rendering errors? Reply OK or FAIL with one-line reason."
        })], capture_output=True, text=True)
    result = json.loads(r.stdout).get("response", "")
    print(f"  Vision audit slide {i+1}/{n}: {result[:80]}")
    if "FAIL" in result.upper():
        print(f"  ⚠ Visual issue on slide {i+1} — fix before delivery")

print("[ARCHON] export_pdf_with_audit → OK in 12.3s")
print(f"PDF ready: {OUTPUT}")
```

### Document pipeline (mode: "document")

```python
import subprocess, json, base64
import pymupdf
from pathlib import Path
from inkline.typst import export_typst_document

OUTPUT = Path("~/.local/share/inkline/output/report.pdf").expanduser()
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

# ── Phase 1: parse_input ────────────────────────────────────────────────────
print("[ARCHON] Phase: parse_input")
# ... read and parse input file into md_text string ...
print("[ARCHON] parse_input → OK in 0.5s")

# ── Phase 2: build_doc_plan ──────────────────────────────────────────────────
print("[ARCHON] Phase: build_doc_plan")
# ... structure sections, headings, decide on brand/template/paper size ...
# For complex reports: build a doc_plan dict with section titles + content
print("[ARCHON] build_doc_plan → OK in 8.1s")

# ── Phase 3: render_document ─────────────────────────────────────────────────
print("[ARCHON] Phase: render_document")
export_typst_document(
    markdown=md_text,
    output_path=str(OUTPUT),
    brand="minimal",
    title="Q4 Report",
    subtitle="Board update",
    date="April 2026",
    paper="a4",
)
print("[ARCHON] render_document → OK in 4.2s")

# ── Phase 4: audit_document ──────────────────────────────────────────────────
print("[ARCHON] Phase: audit_document")
doc = pymupdf.open(str(OUTPUT))
n = len(doc)
for i, page in enumerate(doc):
    pix = page.get_pixmap(dpi=120)
    img_b64 = base64.b64encode(pix.tobytes("png")).decode()
    r = subprocess.run(["curl", "-s", "-X", "POST", "http://localhost:8082/vision",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({
            "image_base64": img_b64,
            "prompt": f"Page {i+1}/{n}: Are there any rendering errors, overflow, broken layout, or missing content? Reply OK or FAIL with one-line reason."
        })], capture_output=True, text=True)
    result = json.loads(r.stdout).get("response", "")
    print(f"  Vision audit page {i+1}/{n}: {result[:80]}")
    if "FAIL" in result.upper():
        print(f"  ⚠ Visual issue on page {i+1} — review output")

print("[ARCHON] audit_document → OK in 8.7s")
print(f"PDF ready: {OUTPUT}")
```

---

## Output conventions (ALWAYS follow these)

- **Session PDF:** `~/.local/share/inkline/output/deck.pdf` — always write here, always overwrite
- **Charts:** `~/.local/share/inkline/output/charts/` — pre-rendered chart PNGs
- **Uploads:** `~/.local/share/inkline/uploads/` — files received from WebUI
- After every render, print exactly: `PDF ready: ~/.local/share/inkline/output/deck.pdf`
- This triggers the WebUI iframe to refresh automatically

---

## Input file handling

### .md or .txt — read directly
```bash
cat report.md   # or use Read tool
```

### .docx — convert via pandoc
```bash
pandoc input.docx -o /tmp/inkline_input.md --wrap=none
cat /tmp/inkline_input.md
```
If pandoc unavailable, use python-docx:
```python
from docx import Document
doc = Document('input.docx')
text = '\n'.join(p.text for p in doc.paragraphs if p.text.strip())
```

### .pdf — extract via pymupdf
```python
import pymupdf
doc = pymupdf.open('input.pdf')
text = '\n\n'.join(page.get_text() for page in doc)
```

### .pptx — extract outline
```python
from pptx import Presentation
prs = Presentation('input.pptx')
lines = []
for slide in prs.slides:
    for shape in slide.shapes:
        if shape.has_text_frame:
            lines.append(shape.text_frame.text)
text = '\n'.join(lines)
```

---

## Building sections[]

`sections` is the input to `DesignAdvisor.design_deck()`. Each section is a dict.
Build these from the parsed document text. Extract concrete metrics into `"metrics"` 
rather than leaving numbers in prose — this produces better slide layouts.

### Section type reference

```python
# Narrative / prose content
{"type": "executive_summary", "title": "...", "narrative": "...", "metrics": {"ARR": "$4.2M"}}

# KPI dashboard — key numbers
{"type": "kpi_dashboard", "title": "...", "metrics": {"Growth": "34%", "ARR": "$4.2M", "Customers": "87"}}

# Financial table
{"type": "financial_overview", "title": "...",
 "table_data": {"headers": ["Metric", "2025", "2026"], "rows": [["Revenue", "$3M", "$4.2M"]]}}

# Time-series data
{"type": "production_analysis", "title": "...",
 "series": [{"name": "Revenue", "values": [1.2, 1.8, 2.4], "dates": ["Q1", "Q2", "Q3"]}]}

# Risk / RAG assessment
{"type": "risk_assessment", "title": "...",
 "items": [{"risk": "Regulatory", "severity": "high", "mitigation": "..."}]}

# Competitive positioning (2x2, radar, comparison)
{"type": "competitive_positioning", "title": "...",
 "items": [{"name": "Inkline", "x": 90, "y": 85, "label": "Best overall"}]}

# Timeline / roadmap
{"type": "timeline", "title": "...",
 "milestones": [{"date": "Q1 2026", "label": "Launch", "desc": "..."}]}

# Process / how it works
{"type": "process_flow", "title": "...",
 "steps": [{"number": "1", "title": "Describe", "desc": "Pass structured data"}]}

# Card-style content (3 or 4 items)
{"type": "comparison", "title": "...",
 "cards": [{"title": "Problem 1", "body": "One or two short sentences."}]}

# Generic narrative (fallback)
{"type": "narrative", "title": "...", "narrative": "..."}
```

---

## Generating slides

### Option A — DesignAdvisor (recommended for natural language input)

DesignAdvisor reads the sections and picks the best slide type for each one.
Use this when you're working from a document or natural language description.

```python
from inkline.intelligence import DesignAdvisor
from inkline.typst import export_typst_slides
from pathlib import Path

OUTPUT = Path("~/.local/share/inkline/output/deck.pdf").expanduser()
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

advisor = DesignAdvisor(
    brand="minimal",       # or any registered brand
    template="consulting", # see template list below
    mode="llm",            # "llm" (best), "rules" (no API key needed), "advised"
)

slides = advisor.design_deck(
    title="Q4 Strategy Review",
    sections=sections,     # list of dicts built from document
    audience="investors",  # optional: shapes the tone and slide density
    goal="secure term sheet",  # optional: shapes the hero slide choices
    date="April 2026",
    subtitle="Board presentation",
    contact={              # optional: populates closing slide
        "name": "Jane Smith", "role": "CEO", "email": "jane@acme.com",
        "company": "Acme Corp", "tagline": "Let's build this together.",
    },
)

export_typst_slides(
    slides=slides,
    output_path=str(OUTPUT),
    brand="minimal",
    template="consulting",
    title="Q4 Strategy Review",
    date="April 2026",
)
print(f"PDF ready: {OUTPUT}")
```

### Option B — Direct export (when you already know the exact slide specs)

Use this when amending an existing deck or when the user gives you exact requirements.
Keep `slides` as a Python variable in your context across turns.

```python
from inkline.typst import export_typst_slides
from pathlib import Path

slides = [
    {"slide_type": "title", "data": {
        "company": "Acme Corp", "tagline": "Series B", "date": "April 2026"}},
    {"slide_type": "three_card", "data": {
        "section": "Problem", "title": "Three pain points",
        "cards": [
            {"title": "Fragmented data", "body": "..."},
            {"title": "Manual reporting", "body": "..."},
            {"title": "Stale insights", "body": "..."},
        ]}},
    {"slide_type": "closing", "data": {
        "name": "Jane Smith", "role": "CEO", "email": "jane@acme.com",
        "company": "Acme Corp", "tagline": "Let's build this together."}},
]

OUTPUT = Path("~/.local/share/inkline/output/deck.pdf").expanduser()
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
export_typst_slides(slides=slides, output_path=str(OUTPUT), brand="minimal", template="consulting")
print(f"PDF ready: {OUTPUT}")
```

---

## Amending decks

When the user asks to change something, keep the current `slides` list in context
and modify it directly. Then re-export. Never start from scratch unless the user asks.

```python
# Example: user says "make slide 3 more visual"
# slides[2] is currently {"slide_type": "content", "data": {...}}
# Change to three_card:
slides[2] = {
    "slide_type": "three_card",
    "data": {
        "section": slides[2]["data"].get("section", ""),
        "title": slides[2]["data"]["title"],
        "cards": [
            {"title": item.split(":")[0] if ":" in item else item, "body": item.split(":", 1)[1].strip() if ":" in item else ""}
            for item in slides[2]["data"].get("items", [])[:3]
        ],
    }
}
# Then re-export
export_typst_slides(slides=slides, output_path=str(OUTPUT), brand="minimal", template="consulting")
print(f"PDF ready: {OUTPUT}")
```

After any amendment, always print the slide list so the user can orient:
```python
for i, s in enumerate(slides, 1):
    print(f"  {i:2d}. [{s['slide_type']:14s}] {s['data'].get('title', s['data'].get('company', ''))[:50]}")
```

---

## Slide type catalogue (all 21)

Capacity limits are hard — the renderer silently drops anything beyond them.

### Visual heroes (prefer these)

| Type | Data shape | Limits |
|------|-----------|--------|
| `icon_stat` | `{section, title, stats [{value, icon, label, desc?}], footnote?}` | 3–4 stats |
| `kpi_strip` | `{section, title, kpis [{value, label, highlight?}], footnote?}` | 3–5 KPIs |
| `stat` | `{section, title, stats [{value, label, desc}]}` | 2–4 stats |
| `feature_grid` | `{section, title, features [{title, body, icon?}], footnote?}` | EXACTLY 6 |
| `dashboard` | `{section, title, image_path, stats [{value, label}], bullets, footnote?}` | 3 stats, 3 bullets |
| `chart_caption` | `{section, title, image_path, caption, bullets, footnote?}` | 4 bullets max |
| `progress_bars` | `{section, title, bars [{label, pct, value?}], footnote?}` | 6 bars max |

### Narrative layouts

| Type | Data shape | Limits |
|------|-----------|--------|
| `three_card` | `{section, title, cards [{title, body}], highlight_index?, footnote?}` | EXACTLY 3 |
| `four_card` | `{section, title, cards [{title, body}], footnote?}` | EXACTLY 4 |
| `timeline` | `{section, title, milestones [{date, label, desc?}], footnote?}` | 6 max |
| `process_flow` | `{section, title, steps [{number, title, desc}], footnote?}` | 4 max |
| `pyramid` | `{section, title, tiers [{label, desc?}], footnote?}` | 3–5 tiers |
| `split` | `{section, title, left_title, left_items, right_title, right_items}` | 6 items/side |
| `comparison` | `{section, title, left {name, items [{label, value}]}, right {name, items [{label, value}]}, footnote?}` | 6 rows |
| `bar_chart` | `{section, title, bars [{label, value, pct}], footnote?}` | native Typst bars |

### Data exhibits

| Type | Data shape | Limits |
|------|-----------|--------|
| `table` | `{section, title, headers, rows, footnote?}` | 6 rows × 6 cols MAX |
| `multi_chart` | `{section, title, layout, charts [{image_path, title?}], footnote?}` | see layouts below |
| `chart` | `{section, title, image_path, footnote?}` | bare full-width chart |

`multi_chart` layouts: `equal_2` (2 charts), `equal_3`, `equal_4`, `hero_left` (2),
`hero_left_3` (3), `hero_right_3` (3), `quad` (4), `top_bottom` (4).

### Structural

| Type | Data shape |
|------|-----------|
| `title` | `{company, tagline, date, subtitle?, left_footer?}` |
| `closing` | `{name, role, email, company, tagline}` |
| `content` | `{section, title, items, footnote?}` — USE SPARINGLY, max 6 bullets |
| `section_divider` | `{section, title}` |

### Title length hard limit
**Slide titles MUST be ≤ 50 characters.** Titles longer than 50 chars wrap and push
content off the slide. Count before writing. Write action titles (state the conclusion):
- BAD: "Business Model Overview" → GOOD: "98% gross margin at scale"
- BAD: "The Problem" → GOOD: "Analysts spend 80% of their week formatting"

---

## Chart request format

Embed a `chart_request` in any `chart`, `chart_caption`, `dashboard`, or `multi_chart`
slide. Inkline auto-renders the chart PNG before Typst compilation.

```python
{
    "slide_type": "chart_caption",
    "data": {
        "section": "Financials",
        "title": "Revenue growing 34% YoY",
        "image_path": "revenue.png",         # just the filename — written to charts/ dir
        "chart_request": {
            "chart_type": "area_chart",       # see chart types below
            "chart_data": {
                "x": ["Q1", "Q2", "Q3", "Q4"],
                "series": [{"name": "Revenue ($M)", "values": [1.2, 1.8, 2.4, 3.1]}],
                "y_label": "$M",
            },
        },
        "caption": "ARR compounding at 34% per quarter",
        "bullets": ["Q4 $3.1M, up from $1.2M in Q1", "Net revenue retention >120%"],
    }
}
```

**Chart types:** `line_chart`, `area_chart`, `scatter`, `waterfall`, `donut`, `pie`,
`stacked_bar`, `grouped_bar`, `heatmap`, `radar`, `gauge`,
`marimekko`, `entity_flow`, `divergent_bar`, `horizontal_stacked_bar`

**Infographic archetypes (use via `chart_row` type):**
`iceberg`, `sidebar_profile`, `funnel_kpi_strip`, `persona_dashboard`,
`radial_pinwheel`, `hexagonal_honeycomb`, `waffle`, `ladder`, `dual_donut`, + more

---

## Available templates (37)

**Built-in (10):** `consulting`, `executive`, `minimalism`, `newspaper`, `investor`,
`pitch`, `dark`, `editorial`, `boardroom`, `brand`

**Design-system styles (27):** `dmd_stripe`, `dmd_vercel`, `dmd_notion`, `dmd_apple`,
`dmd_spotify`, `dmd_tesla`, `dmd_airbnb`, `dmd_coinbase`, `dmd_shopify`, `dmd_figma`,
`dmd_framer`, `dmd_cursor`, `dmd_warp`, `dmd_supabase`, `dmd_uber`, `dmd_ferrari`,
`dmd_bmw`, `dmd_mongodb`, `dmd_intercom`, `dmd_webflow`, `dmd_miro`, `dmd_posthog`,
`dmd_raycast`, `dmd_revolut`, `dmd_superhuman`, `dmd_zapier`, `dmd_claude`

Use `consulting` or `executive` for business decks. `pitch` for startup pitches.
`dmd_stripe` / `dmd_vercel` / `dmd_notion` for modern tech product decks.

---

## Available brands

**Public (ships with Inkline):** `minimal`

**Private (loaded from `~/.config/inkline/brands/` if cloned):**
Run `python3 -c "from inkline.brands import list_brands; print(list_brands())"` to see
what's available on the current machine.

---

## Themes (90 total)

```python
from inkline.typst.themes import list_themes, search_themes
list_themes(category="consulting")  # McKinsey, BCG, Bain, Deloitte, PwC, EY, KPMG
list_themes(category="dark")        # Nord, Dracula, Catppuccin, Carbon
search_themes("gold")               # Aurum, Gold Leaf, Mercury, ...
```

Theme is applied automatically by the template — usually you just pick a template.

---

## Overflow audit

Run before exporting to catch problems early:

```python
from inkline.intelligence import audit_deck, format_report
warnings = audit_deck(slides)
if warnings:
    print(format_report(warnings))
```

`export_typst_slides()` runs audit automatically. Pass `audit=False` to skip.

---

## Common patterns

### Quick deck from a .docx file
```python
import subprocess, json
from pathlib import Path
from inkline.intelligence import DesignAdvisor
from inkline.typst import export_typst_slides

# 1. Convert
result = subprocess.run(["pandoc", "input.docx", "-o", "/tmp/input.md", "--wrap=none"], check=True)
md = Path("/tmp/input.md").read_text()

# 2. Build sections from the document structure
# Parse headings and content into sections list
sections = []
current = {}
for line in md.split("\n"):
    if line.startswith("## "):
        if current: sections.append(current)
        current = {"type": "narrative", "title": line.lstrip("# ").strip(), "narrative": ""}
    elif line.startswith("# "):
        pass  # document title — skip, use for deck title
    elif current:
        current["narrative"] = (current.get("narrative", "") + "\n" + line).strip()
if current: sections.append(current)

# 3. Generate
OUTPUT = Path("~/.local/share/inkline/output/deck.pdf").expanduser()
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
advisor = DesignAdvisor(brand="minimal", template="consulting", mode="llm")
slides = advisor.design_deck(title="Report", sections=sections)
export_typst_slides(slides=slides, output_path=str(OUTPUT), brand="minimal")
print(f"PDF ready: {OUTPUT}")
```

### Add a chart slide to an existing deck
```python
# Insert after index 3 (0-based)
new_slide = {
    "slide_type": "chart_caption",
    "data": {
        "section": "Financials",
        "title": "Revenue trend 2025–2026",
        "image_path": "revenue.png",
        "chart_request": {
            "chart_type": "line_chart",
            "chart_data": {
                "x": ["Jan", "Feb", "Mar", "Apr"],
                "series": [{"name": "Revenue", "values": [1.0, 1.3, 1.8, 2.2]}],
            },
        },
        "caption": "Consistent month-on-month growth",
        "bullets": ["MoM growth averaging 25%", "Q1 total $4.1M"],
    },
}
slides.insert(4, new_slide)
export_typst_slides(slides=slides, output_path=str(OUTPUT), brand="minimal")
print(f"PDF ready: {OUTPUT}")
```

### Change template
```python
# Just re-export with a different template
export_typst_slides(slides=slides, output_path=str(OUTPUT), brand="minimal", template="dmd_stripe")
print(f"PDF ready: {OUTPUT}")
```

### Generate a document (not slides)

Always use the full Archon-wrapped document pipeline — see **Pipeline Reference** above.
Never call `export_typst_document()` directly. The 4-phase pattern is:
`parse_input → build_doc_plan → render_document → audit_document`

Send via bridge with `"mode": "document"`:
```bash
curl -X POST http://localhost:8082/prompt \
  -H "Content-Type: application/json" \
  -d '{"prompt": "I have uploaded a report at: <path>. Generate a branded PDF report.", "mode": "document"}'
```

---

## Troubleshooting

- **`typst` compile error:** Run `pip install --upgrade typst`
- **Brand not found:** Run `python3 -c "from inkline.brands import list_brands; print(list_brands())"` to see available brands
- **`pandoc` not found:** `brew install pandoc` (macOS) or `apt install pandoc` (Linux)
- **Overflow warnings:** Check title lengths (≤50 chars) and item counts per slide type
- **LLM mode fails:** Set `ANTHROPIC_API_KEY` or use `mode="rules"` for deterministic output
