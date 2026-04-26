# Inkline — Claude Code Usage Guide

Inkline is a Python library for generating branded, publication-quality slide decks
and documents. You (Claude) drive it via Bash. This file is your complete reference.

For full architectural context, see [`plan_docs/execution-engine-and-knowledge-base-pivot-spec.md`](plan_docs/execution-engine-and-knowledge-base-pivot-spec.md).

---

## MODEL POLICY

- **Specs, architecture, design decisions**: Always use **Opus** (`claude-opus-4-6`)
- **Implementation / coding**: Use **Sonnet** (`claude-sonnet-4-6`) unless Opus is explicitly requested

## SPEC BEFORE CODE

All non-trivial changes to Inkline must start with a spec in `plan_docs/`.

| Spec | Status | Covers |
|---|---|---|
| `plan_docs/execution-engine-and-knowledge-base-pivot-spec.md` | Implemented | Execute-mode default, knowledge base as MCP resources, freeform + image strategy, post-render critique |
| `plan_docs/design-tokens-spec.md` | Proposed | Colour ramps (12-shade), named typography scale, spacing token system |
| `plan_docs/impeccable-design-intelligence-spec.md` | Approved — Draft Mode only | Anti-pattern library, quality scoring, auto-polish, design brief generation |
| `plan_docs/design-system-spec.md` | Approved — Draft Mode only | Decision framework, taste enforcer, self-learning, deck ingestion |
| `plan_docs/two-agent-design-loop-spec.md` | Implemented — Draft Mode only | Phase 1 planner + Phase 2 DesignAdvisor |
| `plan_docs/structural-fixes-v0.4-spec.md` | Implemented | v0.4 structural and overflow fixes |
| `plan_docs/inkline-standalone-app-spec.md` | Implemented | Bridge + MCP server + CLI |
| `plan_docs/ARCHON_AUDIT.md` | Implemented — Draft Mode only | Archon phase supervisor |

---

## PRIMARY PATH — Execute Mode (`inkline render`)

**Execute mode is the default path for Claude Code.** Write a structured markdown spec with explicit layout directives, then call `inkline render`. No LLM is invoked at render time — the renderer faithfully executes the spec.

### Quick start

```bash
# 1. Write a spec with explicit _layout directives (see Layout Catalogue below)
# 2. Render it:
inkline render deck.md --output pdf,pptx --brand minimal

# Or via the bridge:
curl -X POST http://localhost:8082/render \
  -H "Content-Type: application/json" \
  -d '{"spec_path": "/path/to/deck.md", "outputs": ["pdf", "pptx"], "brand": "minimal"}'
```

### Why execute mode

- **Deterministic.** Same spec → same output every time.
- **Faithful.** `_layout: split` with explicit content produces exactly a split layout. No reinterpretation.
- **Fast.** No LLM round-trip for layout decisions. Renders in seconds.
- **CC-friendly.** Claude Code reads the knowledge base (MCP resources / `inkline://` URIs), writes a spec with full context, hands it to the engine.

### Execute-mode spec format

```markdown
---
brand: minimal
template: consulting
title: My Deck
output: [pdf, pptx]
audit: post-render
---

## Three pain points
<!-- _layout: three_card -->
- Problem 1: Market is fragmented across 15+ vendors with no interoperability
- Problem 2: Manual workflows consume 40% of analyst time
- Problem 3: Point-in-time snapshots miss 80% of risk events

## Traction
<!-- _layout: kpi_strip -->
- value: "$1.2M"
  label: ARR
- value: "94%"
  label: Retention
- value: "3x"
  label: YoY growth

## Revenue trend
<!-- _layout: chart_caption
_image: {strategy: reuse, path: assets/revenue_chart.png, slot: right, width: 50%} -->
ARR compounding at 34% per quarter.
```

**Key directives:**
- `_layout: <slide_type>` — explicit layout; defaults `_mode` to `exact` (no LLM reinterpretation)
- `_mode: guided` — override to allow the renderer to make minor adjustments
- `audit: post-render` — no in-loop LLM; call `inkline critique` explicitly after render
- `_capacity_override: true` — suppress capacity warnings for this slide

See [`examples/typed_layout_deck/spec.md`](examples/typed_layout_deck/spec.md) for a complete 8-slide investor pitch.

---

## Knowledge Base (MCP Resources)

The accumulated design knowledge is exposed as MCP resources. Pull the relevant resources into context before authoring a spec.

```
inkline://layouts                         — slide-type catalogue with capacity rules
inkline://layouts/<slide_type>            — single slide-type spec with examples
inkline://anti-patterns                   — anti-pattern library
inkline://archetypes                      — 771 archetype templates
inkline://brands                          — registered brand list
inkline://themes                          — theme registry
inkline://typography                      — type-scale + capacity rules
inkline://templates                       — template catalogue
inkline://playbooks/index                 — all playbooks with descriptions
inkline://playbooks/chart_selection       — chart selection playbook
inkline://playbooks/color_theory          — colour theory playbook
inkline://playbooks/document_design       — document design playbook
inkline://playbooks/infographic_styles    — infographic styles playbook
inkline://playbooks/professional_exhibit_design — institutional exhibit design
inkline://playbooks/slide_layouts         — slide layout playbook
inkline://playbooks/template_catalog      — template catalogue playbook
inkline://playbooks/typography            — typography playbook
inkline://playbooks/visual_libraries      — visual libraries playbook
```

**Via CLI:**
```bash
inkline knowledge list
inkline knowledge get inkline://layouts/three_card
inkline knowledge search "waterfall chart"
```

**Via HTTP proxy (bridge must be running):**
```bash
curl http://localhost:8082/knowledge/layouts
curl http://localhost:8082/knowledge/playbooks/chart_selection
```

**Workflow when authoring a spec:** Read `inkline://playbooks/index` first to identify relevant playbooks, then read the specific playbook and `inkline://layouts` before writing any `_layout:` directive.

---

## Freeform Slide Type

The `freeform` slide type renders an arbitrary positioned-shapes layout from a JSON manifest. Use it for architecture diagrams, competitive maps, and any layout that no typed slide fits.

```markdown
## System Architecture
<!-- _layout: freeform
_shapes_file: shapes/architecture_diagram.json -->
```

**Supported shape types:** `rounded_rect`, `rect`, `text`, `line`, `arrow`, `circle`, `polygon`, `image`

**Position/size units:** `%` (relative to slide canvas, 25.4cm × 14.29cm) or `px`

**Minimal shapes manifest (`shapes/architecture_diagram.json`):**
```json
[
  {"type": "rounded_rect", "x": "5%", "y": "15%", "w": "25%", "h": "20%",
   "fill": "#1F2937", "stroke": "#374151", "label": "Data Ingestion"},
  {"type": "arrow", "x1": "30%", "y1": "25%", "x2": "40%", "y2": "25%",
   "stroke": "#6B7280"},
  {"type": "rounded_rect", "x": "40%", "y": "15%", "w": "25%", "h": "20%",
   "fill": "#1E40AF", "stroke": "#2563EB", "label": "Feature Engineering"},
  {"type": "text", "x": "5%", "y": "42%", "w": "90%", "h": "8%",
   "text": "36-month account history → 200+ derived features", "size": 11,
   "color": "#6B7280", "align": "center"}
]
```

Backend support: `typst=True`, `pptx=True`, `google_slides=False`, `html=False`. Freeform is intentionally explicit — it does not silently downgrade if the backend is unsupported; the build fails visibly.

See [`examples/freeform_hero_deck/`](examples/freeform_hero_deck/) for a complete 4-slide deck, and [`examples/hybrid_deck/`](examples/hybrid_deck/) for a 5-slide deck mixing typed layouts with a freeform competitive map.

---

## Image Strategy Directives

The `_image:` directive controls how images are sourced for a slide. Three strategies:

```markdown
## Slide with existing asset
<!-- _layout: chart_caption
_image: {strategy: reuse, path: assets/revenue_chart.png, slot: right, width: 50%} -->

## Slide with AI-generated image
<!-- _layout: split
_image: {strategy: generate, prompt: "Abstract dark blue gradient, 16:9", slot: left} -->

## Slide with placeholder
<!-- _layout: dashboard
_image: {strategy: placeholder, slot: main, width: 60%, height: 80%} -->
```

**Strategy behaviours:**
- `reuse` — validates path at parse time. Raises `FileNotFoundError` immediately if missing. Path resolved relative to the spec file, then `INKLINE_ASSETS_DIR`, then `~/.config/inkline/assets/`.
- `generate` — calls Gemini multimodal via n8n (see n8n section). Content-hash cached in `~/.local/share/inkline/image_cache/`. Raises `ImageStrategyError` on failure — no silent fallback to PIL placeholder.
- `placeholder` — grey box in the rendered output. Use for iterative authoring before assets are ready.

**Optional fields:** `reference_image_path` (multimodal anchor for `generate`), `region_width_px`, `region_height_px` (size hints for generation).

---

## Post-Render Critique

After rendering, run Vishwakarma's vision audit on the finished PDF:

```bash
inkline critique deck.pdf --rubric institutional
inkline critique deck.pdf --rubric tech_pitch
inkline critique deck.pdf --rubric internal_review
```

Returns per-slide verdicts (`PASS` / `WARN` / `FAIL`) with actionable fix hints. Overall score starts at 100; `-15` per FAIL, `-5` per WARN.

**Available rubrics:**
- `institutional` — investment bank standards (most strict)
- `tech_pitch` — startup/VC pitch standards
- `internal_review` — lightweight operational check

**Audit levels for the `audit:` front-matter directive:**

| Value | Behaviour |
|---|---|
| `off` | No audit at render time |
| `structural` | Overflow/capacity checks only; no vision model |
| `strict` | Structural + in-loop vision audit (Draft Mode) |
| `post-render` | Structural only at render time; use `inkline critique` after |

**Execute-mode default:** use `audit: post-render` in the spec front-matter. This runs structural checks at render time and leaves the vision audit as an explicit post-render step.

**Via bridge:** `POST /critique` with `{"pdf_path": "...", "rubric": "institutional"}`

**Via MCP:** `inkline_critique_pdf` tool

**Python API:**
```python
from inkline.intelligence.vishwakarma import critique_pdf

result = critique_pdf("deck.pdf", rubric="institutional", brand="minimal")
print(result.overall_score)        # e.g. 85
for sc in result.slide_critiques:
    print(f"Slide {sc.slide_index}: {sc.verdict} — {sc.comment}")
    if sc.fix_hint:
        print(f"  Fix: {sc.fix_hint}")
```

---

## OPT-IN: Draft Mode (`/prompt`)

Draft Mode is the **agentic path** — useful when you have raw source material and no spec yet, or when you want Inkline's internal DesignAdvisor to take design decisions. It requires the claude CLI.

**Use Draft Mode when:**
- You have raw source material and no spec yet (cold-start)
- You want Inkline's DesignAdvisor to propose layouts for you
- You want the full 4-phase Archon pipeline with in-loop Vishwakarma audit

**Note:** The 4-phase Archon pipeline, DesignAdvisor `mode="llm"`, and the self-learning loop are Draft Mode only. The modules are fully functional but are not invoked in the default execute-mode path.

---

## CORRECT WORKFLOW — Draft Mode

**Never run standalone Python scripts to generate decks or documents in Draft Mode.**
**Never call `export_typst_slides()` or `export_typst_document()` directly outside an Archon phase.**

All Draft Mode output MUST flow through the structured Archon pipeline. Calling an export function directly bypasses the visual audit and ships broken output without detection.

The correct workflow for Draft Mode:

1. **Confirm the bridge is running** — `inkline serve` or `inkline bridge` must be active on port 8082.
   Check: `curl -s http://localhost:8082/ | head -1`

2. **Upload the source file** via the bridge:
   ```bash
   curl -X POST http://localhost:8082/upload -F "file=@/path/to/report.md"
   # Returns: {"path": "/home/.../.local/share/inkline/uploads/report.md", "filename": "report.md"}
   ```

3. **Send the generation prompt** to the bridge:
   ```bash
   curl -X POST http://localhost:8082/prompt \
     -H "Content-Type: application/json" \
     -d '{"prompt": "I have uploaded a file at: <path>. Generate a deck ...", "mode": "slides"}'
   ```

4. **Monitor via logs** — do not intervene. The bridge runs Claude agentic mode which executes the 4-phase Archon pipeline, then announces `PDF ready: <path>` when done.

**Enforcement:** The bridge detects bypass attempts. If a `PDF ready:` announcement appears without any `[ARCHON] Phase:` markers in the output stream, the response includes `"archon_bypassed": true` as a violation flag.

---

## n8n / Gemini Image-Generation Prerequisite

Image generation (Gemini multimodal — used by `_image: {strategy: generate, ...}` and generative-asset slides) routes through **n8n on port 5678**. n8n is **NOT** installed on the main Windows PC. It runs **only on K1Mini** (`k1mini@192.168.1.116`).

**When running Inkline from the main PC, tunnel K1Mini's n8n port to localhost BEFORE any image-generating pipeline.** Without the tunnel, `strategy: generate` directives raise `ImageStrategyError` immediately (they do not silently fall back).

### Open the tunnel (run once per session)

```bash
ssh -N -f -L 5678:localhost:5678 \
  -o StrictHostKeyChecking=no \
  -i ~/.ssh/id_ed25519 \
  k1mini@192.168.1.116
```

### Verify the tunnel is up

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:5678/
# Expect: 200 (or any non-000 code)
```

### Active n8n workflows

| Workflow | Endpoint | Input | Use case |
|---|---|---|---|
| `inkblot-icon` | `POST /webhook/inkblot-icon` | `{"prompt": "..."}` | Text-only background / icon generation |
| `gemini-multimodal-icon` | `POST /webhook/gemini-multimodal-icon` | `{"prompt": "...", "reference_image_b64": "<base64>", "mime_type": "image/png"}` | Style-anchored generation with reference image |

Both use model `gemini-2.5-flash-image`. Always read `imageBase64` from the multimodal response — the `image_path` field is a container-local path and cannot be used.

### Python usage

```python
from inkline.generative_assets import generate_background_image

path = generate_background_image(
    n8n_endpoint="http://localhost:5678/webhook/inkblot-icon",
    prompt="Abstract geometric blue background, 16:9",
)
```

---

## Diagnostics — CLI failure dumps

When a `POST /prompt` request fails, the bridge writes a dump file:

```
~/.local/share/inkline/output/cli_failures/<YYYYMMDDTHHMMSS>_rc<code>.log
```

The `dump_path` is also returned in the 502 JSON response. Files older than 7 days are auto-deleted on bridge startup.

---

## Pipeline Reference — Archon-Wrapped Patterns (Draft Mode Only)

These patterns are **Draft Mode only**. The 4-phase Archon supervisor is invoked when the bridge runs `claude -p` in agentic mode. In execute mode, use `inkline render` instead.

### Slides pipeline (mode: "slides")

```python
# ── Phase 1: parse_markdown ─────────────────────────────────────────────────
print("[ARCHON] Phase: parse_markdown")
# ... read and parse input file into sections list ...
print("[ARCHON] parse_markdown → OK in 0.5s")

# ── Phase 2: design_advisor_llm ─────────────────────────────────────────────
print("[ARCHON] Phase: design_advisor_llm")
from inkline.intelligence import DesignAdvisor
advisor = DesignAdvisor(brand="minimal", template="consulting", mode="llm")
slides = advisor.design_deck(title="My Deck", sections=sections)
print("[ARCHON] design_advisor_llm → OK in 45.2s")

# ── Phase 3: save_slide_spec ─────────────────────────────────────────────────
print("[ARCHON] Phase: save_slide_spec")
import json
from pathlib import Path
Path("~/.local/share/inkline/output/deck_spec.json").expanduser().write_text(
    json.dumps(slides, indent=2))
print("[ARCHON] save_slide_spec → OK in 0.1s")

# ── Phase 4: export_pdf_with_audit ──────────────────────────────────────────
print("[ARCHON] Phase: export_pdf_with_audit")
from inkline.typst import export_typst_slides
import base64, subprocess, pymupdf
OUTPUT = Path("~/.local/share/inkline/output/deck.pdf").expanduser()
export_typst_slides(slides=slides, output_path=str(OUTPUT), brand="minimal",
                    template="consulting", image_root=str(OUTPUT.parent))

# Per-slide visual audit via bridge /vision endpoint
doc = pymupdf.open(str(OUTPUT))
for i, page in enumerate(doc):
    pix = page.get_pixmap(dpi=120)
    img_b64 = base64.b64encode(pix.tobytes("png")).decode()
    r = subprocess.run(["curl", "-s", "-X", "POST", "http://localhost:8082/vision",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({"image_base64": img_b64, "prompt": f"Slide {i+1}/{len(doc)}: PASS or FAIL with reason."})],
        capture_output=True, text=True)
    result = json.loads(r.stdout).get("response", "")
    print(f"  Vision audit slide {i+1}: {result[:120]}")

print("[ARCHON] export_pdf_with_audit → OK")
print(f"PDF ready: {OUTPUT}")
```

### Document pipeline (mode: "document")

```python
# ── Phase 1: parse_input ────────────────────────────────────────────────────
print("[ARCHON] Phase: parse_input")
# ... read and parse input file into md_text string ...

# ── Phase 2: build_doc_plan ──────────────────────────────────────────────────
print("[ARCHON] Phase: build_doc_plan")
# ... structure sections, headings, decide on brand/template/paper size ...

# ── Phase 3: render_document ─────────────────────────────────────────────────
print("[ARCHON] Phase: render_document")
from inkline.typst import export_typst_document
from pathlib import Path
OUTPUT = Path("~/.local/share/inkline/output/report.pdf").expanduser()
export_typst_document(markdown=md_text, output_path=str(OUTPUT), brand="minimal",
                      title="Report", date="April 2026", paper="a4")
print("[ARCHON] render_document → OK")

# ── Phase 4: audit_document ──────────────────────────────────────────────────
print("[ARCHON] Phase: audit_document")
# ... per-page vision audit same as slides pattern ...
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
```
If pandoc unavailable:
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
lines = [shape.text_frame.text for slide in prs.slides
         for shape in slide.shapes if shape.has_text_frame]
```

---

## Building sections[]

`sections` is the input to `DesignAdvisor.design_deck()`. Each section is a dict.
Build these from the parsed document text. Extract concrete metrics into `"metrics"` rather than leaving numbers in prose.

```python
# Key section types:
{"type": "executive_summary", "title": "...", "narrative": "...", "metrics": {"ARR": "$4.2M"}}
{"type": "kpi_dashboard",     "title": "...", "metrics": {"Growth": "34%", "ARR": "$4.2M"}}
{"type": "financial_overview","title": "...", "table_data": {"headers": [...], "rows": [...]}}
{"type": "production_analysis","title": "...", "series": [{"name": "Revenue", "values": [...]}]}
{"type": "risk_assessment",   "title": "...", "items": [{"risk": "...", "severity": "high"}]}
{"type": "competitive_positioning", "title": "...", "items": [{"name": "...", "x": 90, "y": 85}]}
{"type": "timeline",          "title": "...", "milestones": [{"date": "Q1 2026", "label": "..."}]}
{"type": "process_flow",      "title": "...", "steps": [{"number": "1", "title": "..."}]}
{"type": "comparison",        "title": "...", "cards": [{"title": "...", "body": "..."}]}
{"type": "narrative",         "title": "...", "narrative": "..."}
```

---

## Generating slides

### Option A — DesignAdvisor (Draft Mode — natural language input)

```python
from inkline.intelligence import DesignAdvisor
from inkline.typst import export_typst_slides
from pathlib import Path

OUTPUT = Path("~/.local/share/inkline/output/deck.pdf").expanduser()
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

advisor = DesignAdvisor(brand="minimal", template="consulting", mode="llm")
slides = advisor.design_deck(
    title="Q4 Strategy Review",
    sections=sections,
    audience="investors",
    goal="secure term sheet",
    date="April 2026",
)
export_typst_slides(slides=slides, output_path=str(OUTPUT), brand="minimal", template="consulting")
print(f"PDF ready: {OUTPUT}")
```

### Option B — Direct export (execute mode — exact spec)

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

When the user asks to change something, keep the current `slides` list in context and modify it directly. Then re-export. Never start from scratch unless the user asks.

After any amendment, print the slide list so the user can orient:
```python
for i, s in enumerate(slides, 1):
    print(f"  {i:2d}. [{s['slide_type']:14s}] {s['data'].get('title', s['data'].get('company', ''))[:50]}")
```

---

## Slide type catalogue (all 22)

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

`multi_chart` layouts: `equal_2`, `equal_3`, `equal_4`, `hero_left`, `hero_left_3`, `hero_right_3`, `quad`, `top_bottom`, `three_top_wide`, `left_stack`, `right_stack`, `mosaic_5`, `six_grid`.

### Freeform

| Type | Data shape | Notes |
|------|-----------|-------|
| `freeform` | `{section?, title?, shapes_file}` | JSON manifest, see Freeform section above |

### Structural

| Type | Data shape | Limits |
|------|-----------|--------|
| `title` | `{company, tagline, date, subtitle?, left_footer?}` | |
| `closing` | `{name, role, email, company, tagline}` | |
| `content` | `{section, title, items, footnote?}` — USE SPARINGLY, max 6 bullets | 6 bullets |
| `section_divider` | `{section, title}` | |
| `credentials` | `{section, title, tombstones [{name, detail}], footnote?}` | 4–8 tombstones |
| `testimonial` | `{section, quote, attribution, footnote?}` | quote ≤200 chars |
| `before_after` | `{section, title, left {label, items, colour?}, right {label, items, colour?}, footnote?}` | 3–5 items/side |
| `team_grid` | `{section, title, members [{name, role, bio, image_path?, logos?}], footnote?}` | 2–4 members |

### Title length hard limit
**Slide titles MUST be ≤ 50 characters.** Titles longer than 50 chars wrap and push content off the slide. Write action titles (state the conclusion):
- BAD: "Business Model Overview" → GOOD: "98% gross margin at scale"
- BAD: "The Problem" → GOOD: "Analysts spend 80% of their week formatting"

---

## Chart request format

Embed a `chart_request` in any `chart`, `chart_caption`, `dashboard`, or `multi_chart` slide:

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
`marimekko`, `entity_flow`, `divergent_bar`, `horizontal_stacked_bar`,
`dumbbell`, `transition_grid`, `scoring_matrix`, `gantt`, `multi_timeline`

**Infographic archetypes (use via `chart_row` type):**
`iceberg`, `sidebar_profile`, `funnel_kpi_strip`, `persona_dashboard`,
`radial_pinwheel`, `hexagonal_honeycomb`, `waffle`, `ladder`, `dual_donut` + more

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
```bash
python3 -c "from inkline.brands import list_brands; print(list_brands())"
```

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

## Markdown authoring + live preview

### Directive grammar

**Front-matter (deck-wide):**
```markdown
---
brand: minimal
template: consulting
title: Q4 Strategy Review
audience: investors
audit: post-render
output: [pdf, pptx]
---
```

**HTML-comment (per-slide):**
```markdown
## Market opportunity
<!-- _layout: kpi_strip -->
TAM is $40B, growing 32% YoY.
```

### Directive scopes

| Scope | Prefix | Effect |
|---|---|---|
| Global | none | Front-matter or comment before first heading — whole-deck setting |
| Local | none | Comment after a heading — cascades forward to subsequent slides |
| Spot | `_` prefix | Comment in a section body — applies to this slide only |

### Built-in directives

**Global:** `brand`, `template`, `mode` (llm/rules/advised/exact), `title`, `subtitle`,
`date`, `audience`, `goal`, `paper` (a4/letter/16:9/4:3), `audit` (off/structural/strict/post-render),
`headingDivider` (1–6, default 2), `output` ([pdf,pptx,html,google_slides,png_thumbs])

**Local/spot:** `_layout` (slide type), `_shapes_file` (freeform manifest path),
`_image` (image strategy dict), `_class`, `_mode`, `_paginate`, `_header`, `_footer`,
`_accent`, `_bg`, `_notes`, `_layout_pptx`, `_capacity_override`

### Asset shorthand

```markdown
## Revenue trend
![bg left:40%](charts/revenue.png)
ARR compounding at 34% per quarter.
```

Tokens: `bg`, `left[:N%]`, `right[:N%]`, `cover`/`contain`/`fit`, `w:Npx`, `h:Npx`, `blur:Npx`

### Class system

```python
from inkline.authoring.classes import register

register("lead", r"""
  #show heading.where(level: 2): set text(size: 48pt, weight: 900)
  #show heading.where(level: 2): set align(center)
""")
```

Use in markdown: `<!-- _class: lead -->`

### Plugin API

Register custom directives in a brand package:

```python
from inkline.authoring.directives import register, DirectiveError

@register(scope="global", name="classification")
def classification(value, ctx):
    valid = ("PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED")
    if value.upper() not in valid:
        raise DirectiveError(f"classification must be one of {valid}")
    return {"header_overrides": {"text": value}}
```

### CLI commands

```bash
inkline render deck.md                        # non-agentic render to PDF
inkline render deck.md --watch                # watch + re-render on save
inkline render deck.md --brand minimal --template dmd_stripe
inkline render deck.md --strict-directives    # treat unknown directives as errors
inkline critique deck.pdf --rubric institutional
inkline knowledge list
inkline knowledge get inkline://layouts/three_card
inkline backend-coverage                      # print slide-type × backend matrix
```

### Backend coverage matrix

Run `inkline backend-coverage` to see which slide types are supported by each output backend.

Example downgrades for PPTX:
- `kpi_strip` → `stat`
- `pyramid` → `three_card`
- `multi_chart` → `chart`
- `feature_grid` → `four_card` → `content`
- `freeform` → no downgrade (fails visibly)

### PPTX notes and layout overrides

```markdown
## Revenue trend
<!--
_layout: chart_caption
_layout_pptx: table
_notes: Emphasise the net retention number here.
-->
```

---

## Common patterns

### Quick deck from a .docx file (execute mode)
```bash
pandoc input.docx -o /tmp/input.md --wrap=none
# Then author a spec using /tmp/input.md as source material
inkline render deck.md --brand minimal
```

### Quick deck from a .docx file (Draft Mode via DesignAdvisor)
```python
import subprocess
from pathlib import Path
from inkline.intelligence import DesignAdvisor
from inkline.typst import export_typst_slides

subprocess.run(["pandoc", "input.docx", "-o", "/tmp/input.md", "--wrap=none"], check=True)
md = Path("/tmp/input.md").read_text()

sections = []
current = {}
for line in md.split("\n"):
    if line.startswith("## "):
        if current: sections.append(current)
        current = {"type": "narrative", "title": line.lstrip("# ").strip(), "narrative": ""}
    elif current:
        current["narrative"] = (current.get("narrative", "") + "\n" + line).strip()
if current: sections.append(current)

OUTPUT = Path("~/.local/share/inkline/output/deck.pdf").expanduser()
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
advisor = DesignAdvisor(brand="minimal", template="consulting", mode="llm")
slides = advisor.design_deck(title="Report", sections=sections)
export_typst_slides(slides=slides, output_path=str(OUTPUT), brand="minimal")
print(f"PDF ready: {OUTPUT}")
```

### Add a chart slide to an existing deck
```python
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
export_typst_slides(slides=slides, output_path=str(OUTPUT), brand="minimal", template="dmd_stripe")
print(f"PDF ready: {OUTPUT}")
```

### Generate a document (not slides)
```bash
curl -X POST http://localhost:8082/prompt \
  -H "Content-Type: application/json" \
  -d '{"prompt": "I have uploaded a report at: <path>. Generate a branded PDF report.", "mode": "document"}'
```

---

## Troubleshooting

- **`typst` compile error:** Run `pip install --upgrade typst`
- **Brand not found:** Run `python3 -c "from inkline.brands import list_brands; print(list_brands())"`
- **`pandoc` not found:** `brew install pandoc` (macOS) or `apt install pandoc` (Linux)
- **Overflow warnings:** Check title lengths (≤50 chars) and item counts per slide type
- **LLM mode fails:** Set `ANTHROPIC_API_KEY` or use `mode="rules"` for deterministic output
- **`ImageStrategyError` on generate:** Check the n8n tunnel is up (see n8n section)
- **`FileNotFoundError` on reuse:** Path in `_image:` directive does not exist; check relative path from spec file
