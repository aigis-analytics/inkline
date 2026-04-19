# Inkline

**Branded document & presentation toolkit — Typst, HTML, PDF, PPTX, Google Slides.**

Inkline turns structured data or Markdown into publication-quality, brand-consistent
output with **encoded taste** — the outputs it produces are always within the range
that a designer with good judgement would approve, without user handholding.

Ships with: 90 built-in themes, 37 slide templates, 22 slide layouts, 31 chart/exhibit
types (11 standard + 5 institutional + 5 derived-from-pitchbook + 16 infographic
archetypes), a 1-brand public registry (extensible via plugins), an LLM-driven design
advisor driven by a structured **decision framework** (not an option menu), 10 design
playbooks, a 771-template archetype catalog, a two-layer audit (structural + Claude
vision), and a **self-learning feedback loop** that improves chart selection quality
over time as users accept, reject, or modify slides.

---

## Why Inkline

Inkline is the only code-first slide toolkit with built-in design intelligence, visual auditing, and self-learning — running entirely on your infrastructure.

| Feature | Inkline | Gamma | Beautiful.ai | Canva | python-pptx |
|---|:---:|:---:|:---:|:---:|:---:|
| Programmatic (code-first) | ✓ | ✗ | ✗ | ✗ | ✓ |
| LLM design intelligence | ✓ | ✓ | ✗ | ✗ | ✗ |
| Per-slide visual audit | ✓ | ✗ | ✗ | ✗ | ✗ |
| Brand system / tokens | ✓ | limited | limited | limited | ✗ |
| Self-learning from feedback | ✓ | ✗ | ✗ | ✗ | ✗ |
| Typst PDF output (not PPTX) | ✓ | ✗ | ✗ | ✗ | ✗ |
| 22+ slide type library | ✓ | ✗ | limited | ✓ | ✗ |
| 37 templates | ✓ | limited | limited | ✓ | ✗ |
| 90 themes | ✓ | ✗ | ✗ | limited | ✗ |
| Chart auto-rendering | ✓ | ✓ | limited | ✓ | ✗ |
| Open source | ✓ | ✗ | ✗ | ✗ | ✓ |
| Local / self-hosted | ✓ | ✗ | ✗ | ✗ | ✓ |

---

## Capabilities at a glance

- **Code-first, LLM-amplified** — describe a deck in Python or natural language; a structured design advisor picks layouts, charts, and hierarchy for you
- **Per-slide visual audit** — every exported slide is inspected by a vision model against 11 design-quality and gate checks before delivery
- **Self-learning loop** — user feedback (explicit approvals/rejections + implicit conversation signals) updates rule confidence in a local decision matrix; ingests reference PDFs to extract new patterns
- **Brand system** — token-based brand registry (colours, fonts, logos, confidentiality strings); drop a `.py` file in `~/.config/inkline/brands/` and your brand auto-registers
- **90 themes × 37 templates × 22 slide types × 31 chart types** — covers institutional finance, consulting, tech, editorial, and creative registers
- **Typst backend** — fast, deterministic PDF compilation with no browser dependency; no PPTX export required
- **MCP server** — native integration with Claude Desktop and Claude.ai for conversational deck generation
- **Fully local** — no SaaS dependency; routes LLM calls through a local Claude bridge (zero incremental API cost when Claude Max is running)

---

```bash
pip install inkline                # core: Markdown → HTML
pip install inkline[typst]         # + Typst PDF (default backend)
pip install inkline[pdf]           # + WeasyPrint PDF
pip install inkline[charts]        # + matplotlib chart renderer
pip install inkline[slides]        # + Google Slides API
pip install inkline[intelligence]  # + LLM design advisor (Anthropic)
pip install inkline[app]           # + standalone WebUI + Claude bridge
pip install inkline[mcp]           # + MCP server for Claude Desktop / Claude.ai
pip install inkline[all]           # everything (excludes mcp)
```

## Standalone app — conversational WebUI

The fastest way to use Inkline for non-technical users, or anyone who wants a
natural-language interface instead of writing Python.

**Requirements:** [Claude Code](https://docs.claude.com/claude-code) installed and
authenticated (`claude /login`). Optionally `pandoc` for `.docx` input.

```bash
pip install "inkline[all]"
inkline serve                      # opens http://localhost:8082
```

Upload any file (`.md`, `.docx`, `.pdf`, `.pptx`), type what you want — *"turn this
into a 10-slide investor pitch"* — and a branded PDF appears in the browser. Continue
the conversation to refine: *"make slide 3 more visual"*, *"add a revenue chart after
slide 5"*, *"switch to the Stripe theme"*.

Claude Code handles the entire pipeline: file parsing, content structuring, layout
selection, rendering, and iterative amendments.

```bash
inkline serve --port 9000          # custom port
inkline bridge                     # bridge only, headless
```

**Claude Desktop / Claude.ai integration (MCP):**

```bash
pip install "inkline[mcp]"
inkline mcp                        # start MCP server (stdio)
```

Add to Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "inkline": { "command": "inkline", "args": ["mcp"] }
  }
}
```

---

## Quick start

### Branded report (Typst — default)
```python
from inkline.typst import export_typst_document

export_typst_document(
    markdown="# Q4 Review\n\nRevenue up 34%...",
    output_path="q4_report.pdf",
    brand="minimal",
    title="Q4 2026 Review",
)
```

### Structured slide deck
```python
from inkline.typst import export_typst_slides

slides = [
    {"slide_type": "title", "data": {
        "company": "Acme Corp",
        "tagline": "Series B Pitch",
        "date": "2026-04-09",
    }},
    {"slide_type": "three_card", "data": {
        "section": "Problem", "title": "Three pain points",
        "cards": [
            {"title": "Fragmented data", "body": "..."},
            {"title": "Manual reporting", "body": "..."},
            {"title": "Stale insights",   "body": "..."},
        ],
    }},
    {"slide_type": "kpi_strip", "data": {
        "section": "Traction", "title": "2026 YTD",
        "kpis": [
            {"value": "34%",  "label": "Rev growth", "highlight": True},
            {"value": "$4.2M","label": "ARR"},
            {"value": "87",   "label": "Customers"},
        ],
    }},
]

export_typst_slides(
    slides=slides,
    output_path="acme_pitch.pdf",
    brand="minimal",
    template="consulting",
)
```

### LLM-driven design advisor
```python
from inkline.intelligence import DesignAdvisor

advisor = DesignAdvisor(brand="minimal", template="consulting", mode="llm")
slides = advisor.design_deck(
    title="Q4 Strategy Review",
    sections=[
        {"type": "executive_summary", "metrics": {...}, "narrative": "..."},
        {"type": "financials", "table_data": {...}},
        {"type": "risks", "rag": {...}},
    ],
    audience="investors",
    goal="secure term sheet",
)
# `slides` is ready for export_typst_slides()
```

### Chart renderer (matplotlib)
```python
from inkline.typst.chart_renderer import render_chart_for_brand

render_chart_for_brand(
    chart_type="waterfall",
    data={"labels": [...], "values": [...]},
    output_path="exhibit_1.png",
    brand_name="minimal",
)
```

## Themes (90 total)

Themes live in `inkline.typst.themes` across 13 categories:

| Category     | Examples                                          |
|--------------|---------------------------------------------------|
| consulting   | Strategy Blue, Strategy Green, Strategy Red, Professional Services, Advisory Orange, Advisory Yellow, Corporate Blue |
| corporate    | Pitchbook, Private Banking, MS, BlackRock         |
| tech         | Stripe, Linear, Vercel, Notion, GitHub            |
| dark         | Nord, Dracula, Catppuccin Mocha, Carbon           |
| warm         | Cigar, Creme, Linen, Terracotta, Clementa         |
| cool         | Borealis, Marine, Serene, Zephyr                  |
| nature       | Sage, Sprout, Moss, Lux                           |
| creative     | Gamma, Electric, Aurora, Nebulae                  |
| editorial    | Piano, Chimney, Editoria                          |
| pastel       | Lavender, Seafoam, Twilight                       |
| luxury       | Aurum, Gold Leaf, Mercury, Mystique               |
| minimal      | Pearl, Onyx, Coal, Howlite                        |
| industry     | Healthcare, Energy, Real Estate, Legal, Education |

```python
from inkline.typst.themes import get_theme, list_themes, search_themes

theme = get_theme("stripe")
warm_themes = list_themes(category="warm")
matches = search_themes("gold")
```

**Private / custom themes** — drop a `.py` file in one of these directories
and any `dict` with a `"name"` key is auto-registered:

1. Every path in `$INKLINE_THEMES_DIR`
2. `~/.config/inkline/themes/`
3. `./inkline_themes/` in the current working directory

## Brands

Inkline ships with a single public brand — `minimal` — and an open
plugin system for loading additional brands from a user-controlled
directory. Drop a `.py` file in one of these locations and any
`BaseBrand` instance it defines will be auto-registered at import time:

1. Every path in the `INKLINE_BRANDS_DIR` environment variable
2. `$XDG_CONFIG_HOME/inkline/brands/` (default: `~/.config/inkline/brands/`)
3. `./inkline_brands/` in the current working directory

Asset files (logos, fonts) are looked up in a parallel list of
directories (`INKLINE_ASSETS_DIR`, `~/.config/inkline/assets/`,
`./inkline_assets/`, then the package's bundled assets).

This means personal / proprietary brands — with their own logos,
palettes, and confidentiality strings — live **outside** this repository
and are never committed.

Example brand file (`~/.config/inkline/brands/mycorp.py`):

```python
from inkline.brands import BaseBrand

MyCorpBrand = BaseBrand(
    name="mycorp",
    display_name="My Corporation",
    primary="#0B5FFF", secondary="#00C2A8",
    background="#FFFFFF", surface="#0A2540", text="#111827",
    muted="#6B7280", border="#E5E7EB", light_bg="#F8FAFC",
    heading_font="Inter", body_font="Inter",
    logo_dark_path="mycorp_logo_white.png",   # resolved from asset dirs
    logo_light_path="mycorp_logo_dark.png",
    confidentiality="Private & Confidential",
    footer_text="My Corporation",
)
```

## Design system — encoded taste (v0.5)

Inkline encodes aesthetic quality as three layers that always fire:

**Layer 1 — Decision framework:** The LLM advisor answers three questions
(data shape → message type → exhibit type), then looks up the answer in a
decision matrix. No option menu, no entropy. 27 rules seeded from top-tier
investment bank and consulting firm chart grammar. Confidence scores update
with every feedback event.

**Layer 3 — TasteEnforcer:** Ten deterministic rules run before rendering
regardless of LLM output:
- Bar charts always get `style: "clean"` (no axes, direct value labels)
- Donuts with ≤ 6 segments always get `label_style: "direct"` (radial labels, no legend)
- Scatter with named points always gets `label_style: "annotated"` (callout boxes)
- `accent_index` auto-inferred on bar charts if not set (highlights highest value)
- Panel charts inside multi_chart have embedded titles cleared automatically

**Self-learning loop:** User feedback (explicit + implicit from conversation) updates
rule confidence. Users can also ingest reference PDFs to extract new design patterns.

```bash
inkline learn                          # process feedback log, update DM confidence
inkline ingest /path/to/pitchbook.pdf  # extract patterns from a reference deck
```

---

## Slide types (21)

**Standard:** `title`, `content`, `three_card`, `four_card`, `stat`, `table`,
`split`, `bar_chart`, `kpi_strip`, `closing`
**Infographic:** `timeline`, `process_flow`, `icon_stat`, `progress_bars`,
`pyramid`, `comparison`, `feature_grid`
**Data exhibit:** `dashboard`, `chart_caption`, `multi_chart`
**Embedded:** `chart` (matplotlib PNG/SVG)

### `multi_chart` — multi-exhibit grid layout

Arrange 2–4 pre-rendered chart images in configurable asymmetric grids,
modelled on institutional bank presentation patterns:

```python
{
    "slide_type": "multi_chart",
    "data": {
        "section": "Market Overview",
        "title": "Four-panel market dashboard",
        "layout": "hero_left_3",   # 50/25/25 — hero chart + two supporting
        "charts": [
            {"image_path": "revenue_trend.png", "title": "Revenue trend"},
            {"image_path": "asset_mix.png",     "title": "Asset mix"},
            {"image_path": "ebitda.png",         "title": "EBITDA margin"},
        ],
        "footnote": "Source: management accounts",
    }
}
```

Supported layouts:

| Layout | Columns | Use case |
|--------|---------|----------|
| `equal_2` | 50 / 50 | Side-by-side comparison |
| `equal_3` | 33 / 33 / 33 | Three-metric overview |
| `equal_4` | 25 / 25 / 25 / 25 | Four-panel dashboard |
| `hero_left` | 65 / 35 | Main chart + supporting callout |
| `hero_left_3` | 50 / 25 / 25 | Hero + two supporting panels |
| `hero_right_3` | 25 / 25 / 50 | Two context panels + hero |
| `quad` | 2×2 grid | Full four-panel data page |
| `top_bottom` | Wide top + row below | Summary chart + detail exhibits |
| `three_top_wide` | 3 small top + 1 wide bottom | Overview trio + main exhibit |
| `left_stack` | 1 hero left + 2 stacked right | Feature + two supporting |
| `right_stack` | 2 stacked left + 1 hero right | Two context + hero right |
| `mosaic_5` | 2 top + 3 bottom | Rich mosaic analysis page |
| `six_grid` | 3×2 equal grid | Comprehensive 6-exhibit summary |

## Chart types (31+)

### Standard charts (11)
`line_chart`, `area_chart`, `scatter`, `waterfall`, `donut`, `pie`,
`stacked_bar`, `grouped_bar`, `heatmap`, `radar`, `gauge`

**Enhanced in v0.5:** `style: "clean"` on bars removes axes and adds direct
value labels. `accent_index`/`accent_series` marks one element in accent colour.
`label_style: "direct"` on donuts removes the legend. `label_style: "annotated"`
on scatter adds callout boxes per point.

### Institutional exhibit types (4)
| Type | Description |
|------|-------------|
| `marimekko` | Proportional mosaic — column width and cell height both encode data; no axes |
| `entity_flow` | Legal/org structure diagram with tiered grey palette (dark=focal, mid=intermediary, light=peripheral) |
| `divergent_bar` | Vertical bars above/below zero baseline; floating value labels; no y-axis |
| `horizontal_stacked_bar` | 100% stacked horizontal bars showing composition shift over time |

### Pitchbook-derived chart types (5, new in v0.5)

Derived from top-tier investment bank reference decks. All registered in
the decision matrix with proven (data_structure, message_type) mappings.

| Type | Best for |
|------|----------|
| `dumbbell` | Before/after pairs, spread migration, analyst estimate vs actual |
| `transition_grid` | Business model transitions, revenue mix shifts over time |
| `scoring_matrix` | Capability comparison matrices (scores 0–3 render as ○◔◕●) |
| `gantt` | Construction programmes, project roadmaps, parallel workstreams |
| `multi_timeline` | M&A/fundraising timelines with duration + phase + task detail |

### Infographic archetypes (16, rendered via `chart_row`)
`iceberg`, `sidebar_profile`, `funnel_kpi_strip`, `persona_dashboard`,
`radial_pinwheel`, `hexagonal_honeycomb`, `semicircle_taxonomy`,
`process_curved_arrows`, `pyramid_detailed`, `ladder`, `petal_teardrop`,
`funnel_ribbon`, `dual_donut`, `waffle`, `metaphor_backdrop`, `chart_row`

## Slide templates (37+)

10 curated built-in templates plus 27 additional design system styles, with support
for unlimited private custom templates via the plugin system (see below):

**Built-in:** `executive`, `minimalism`, `newspaper`, `investor`, `consulting`,
`pitch`, `dark`, `editorial`, `boardroom`, `brand`

**Additional styles:** `dmd_stripe`, `dmd_vercel`, `dmd_notion`, `dmd_apple`,
`dmd_spotify`, `dmd_tesla`, `dmd_airbnb`, `dmd_coinbase`, `dmd_shopify`,
`dmd_figma`, `dmd_framer`, `dmd_cursor`, `dmd_warp`, `dmd_supabase`,
`dmd_uber`, `dmd_ferrari`, `dmd_bmw`, `dmd_mongodb`, `dmd_intercom`,
`dmd_webflow`, `dmd_miro`, `dmd_posthog`, `dmd_raycast`, `dmd_revolut`,
`dmd_superhuman`, `dmd_zapier`, `dmd_claude`

**Private / custom templates** — drop a `.py` file in one of these directories
and any `dict` with a `"desc"` key is auto-registered as a new template:

1. Every path in `$INKLINE_TEMPLATES_DIR`
2. `~/.config/inkline/templates/`
3. `./inkline_templates/` in the current working directory

```python
# Use any template by name
export_typst_slides(slides=slides, brand="minimal", template="dmd_stripe")
export_typst_slides(slides=slides, brand="mycorp", template="my_boardroom")  # private
```

## Overflow audit

Inkline enforces content limits per slide layout and runs an audit at export time:

```python
from inkline.intelligence import audit_deck, format_report

warnings = audit_deck(slides)
print(format_report(warnings))
# OVERFLOW AUDIT: 0 errors, 2 warnings, 0 info
# [WARN] slide 3 (content): field 'items' has 15 items but slide capacity is 8...
```

`export_typst_slides()` runs the audit automatically and logs warnings. Pass
`audit=False` to disable.

## CLI

```bash
# Document generation (Markdown input, no LLM required)
inkline-html report.md --brand minimal --title "My Report"
inkline-pdf  report.md --brand mycorp  --title "Quarterly Review"

# Standalone app (requires Claude Code installed and authenticated)
inkline serve                      # WebUI at http://localhost:8082 + auto-opens browser
inkline serve --port 9000          # custom port
inkline serve --no-browser         # start without opening browser
inkline bridge                     # bridge only (headless, for programmatic use)
inkline mcp                        # MCP server for Claude Desktop / Claude.ai (stdio)

# Design system / self-learning (v0.5)
inkline learn                      # process feedback log, update decision matrix
inkline ingest pitchbook.pdf       # extract design patterns from a reference PDF
inkline ingest pitchbook.pdf --name q2_deck     # with custom identifier
```

## Repository layout

```
src/inkline/
├── brands/           # public brand(s) + plugin loader
├── html/             # Markdown → styled HTML
├── pdf/              # WeasyPrint PDF backend
├── pptx/             # python-pptx backend
├── slides/           # Google Slides API
├── typst/            # Typst backend (default)
│   ├── slide_renderer.py    # 21 slide layouts (incl. multi_chart, 13 layouts)
│   ├── chart_renderer.py    # 31 chart/exhibit renderers
│   ├── taste_enforcer.py    # TasteEnforcer — 10 deterministic taste rules
│   ├── theme_registry.py    # template → theme generation
│   └── themes/              # 90 themes in 13 categories
├── intelligence/     # Design advisor + overflow audit + self-learning
│   ├── design_advisor.py          # DesignAdvisor — decision framework + _inject_decision_matrix()
│   ├── decision_matrix_default.yaml # 27 seed rules (top-tier bank/consulting grammar)
│   ├── aggregator.py              # Aggregator — feedback events → confidence updates
│   ├── deck_analyser.py           # DeckAnalyser — PDF → chart heuristics → DM candidates
│   ├── feedback.py                # capture_feedback(), detect_implicit_feedback()
│   ├── pattern_memory.py          # per-brand YAML pattern store
│   ├── slide_fixer.py             # closed-loop overflow fixer (6 graduated levels)
│   ├── overflow_audit.py          # structural + Claude vision audit (15 checks)
│   ├── claude_code.py             # bridge caller + ensure_bridge_running()
│   ├── archon.py                  # pipeline supervisor: phase tracking + issue log
│   ├── vishwakarma.py             # design philosophy constants (4 laws)
│   ├── playbooks/                 # 10 design playbooks
│   └── design_md_styles/          # 27 additional design system styles
└── app/              # Standalone app layer (pip install inkline[app])
    ├── claude_bridge.py   # HTTP bridge → claude CLI (port 8082)
    │                      #   POST /prompt, POST /upload, GET /output/{f}
    │                      #   _record_implicit_feedback() on every /prompt
    ├── mcp_server.py      # MCP server — 7 tools for Claude Desktop / Claude.ai
    │                      #   inkline_generate_deck, inkline_render_slides,
    │                      #   inkline_list_templates, inkline_list_themes,
    │                      #   inkline_submit_feedback, inkline_ingest_reference_deck,
    │                      #   inkline_learn
    ├── cli.py             # inkline serve / bridge / mcp / learn / ingest
    └── static/
        └── index.html     # thin WebUI: file upload, chat, live PDF preview
```

## Vishwakarma design philosophy

All LLM-driven design decisions in Inkline are governed by four laws baked into
the system prompts and routing logic:

1. **Visual hierarchy** — Infographic-first decision ladder. Priority within Tier 1
   is **1C → 1B → 1A**: always try to fill a multi-exhibit layout first, then a
   single structural infographic, then a plain KPI callout. 1A and 1B types are
   also valid as individual exhibit slots within a 1C layout.

   | Priority | Tier | What | Examples |
   |----------|------|------|---------|
   | ① highest | 1C | Multi-exhibit slide | `multi_chart` (8 layouts: hero_left_3, quad, top_bottom, …), `chart_row` |
   | ② | 1B | Structural infographic | `iceberg`, `waffle`, `hexagonal_honeycomb`, `radial_pinwheel`, `ladder`, `funnel_kpi_strip`, `persona_dashboard`, `metaphor_backdrop` + 7 more |
   | ③ | 1A | KPI callout | `kpi_strip`, `icon_stat`, `progress_bars`, `feature_grid` |
   | ④ | 2 | Institutional exhibit | `marimekko`, `entity_flow`, `divergent_bar`, `horizontal_stacked_bar`, `chart_caption`, `dashboard` |
   | ⑤ | 3 | Structural visual | `three_card`, `four_card`, `comparison`, `split`, `timeline`, `process_flow` |
   | ⑥ | 4 | Data table | `table` (≤ 6×6) |
   | ⑦ last | 5 | Text bullets | `content` — ≤ 1 per deck, justify why nothing else fit |

   Scoring rule: ≥ 30% Tier 1C, ≥ 20% Tier 1A/1B, ≥ 20% Tier 2; every deck
   must contain at least one 1C multi-exhibit slide.

2. **Bridge first** — Every LLM call (text and vision) routes through the local
   Claude bridge (`localhost:8082`) before touching the Anthropic API. Zero
   incremental API cost when Claude Max is running.
3. **Visual audit mandatory** — Every deck gets a two-agent design dialogue:
   a vision auditor checks each rendered slide PNG, the design advisor revises
   from the findings. Loop continues until the auditor signs off or max rounds.
4. **Archon oversight** — A single `Archon` instance supervises each pipeline
   run, intercepts all `inkline.*` log records, and writes a structured issues
   report at completion.

See `inkline.intelligence.vishwakarma` for the constants and
`inkline.intelligence.archon.Archon` for the supervisor class.

## Identity

<p align="center">
  <img src="brand/logo/rendered/lockup-horizontal.png" alt="Inkline" width="320">
</p>

<p align="center">
  <img src="brand/logo/rendered/mark-512.png" alt="Inkline mark — ink drop" width="120">&nbsp;&nbsp;&nbsp;
  <img src="brand/logo/rendered/mark-icon-512.png" alt="Inkline app icon" width="120">
</p>

The mark is a stylised lowercase **i** — the tittle replaced by a teardrop ink drop as if ink has just fallen from a nib. Two variants: the standalone ink drop (left) for print and lockups; the rounded-tile app icon (right) for favicons and mobile.

Inkline's full brand system is defined in [`brand/BRAND_GUIDELINES.md`](brand/BRAND_GUIDELINES.md).
The `brand/` directory ships SVG sources, rendered PNGs (mark, wordmark, lockups, app icon), favicon, and colour palette.

**Primary palette:**

| Token | Hex | Usage |
|-------|-----|-------|
| Ink | `#0A0A0A` | Primary text, "ink" half of wordmark |
| Indigo | `#3D2BE8` | Brand primary, "line" half, CTAs, stem |
| Indigo Light | `#6C5FFF` | Gradient start, hover, selected |
| Vellum | `#F7F6F2` | Page background, card fills |
| Slate | `#64748B` | Secondary text, captions, metadata |
| Rule | `#E2E1DC` | Dividers, borders, table rules |

**Accent palette (data & status):**

| Token | Hex | Usage |
|-------|-----|-------|
| Violet | `#7C3AED` | Extended brand, chart complement |
| Cobalt | `#1E40AF` | Links, informational states |
| Vermilion | `#DC2626` | Errors, FAIL states |
| Sage | `#16A34A` | Success, PASS states |
| Amber | `#D97706` | Warnings, caution |

Brand assets are available under the same MIT licence as the code.

## Documentation

- [Technical specification](docs/TECHNICAL_SPEC.md) — architecture, APIs, data models
- [Commercial pitch](docs/PITCH.md) — capabilities, competitive comparison
- [Archon audit workflow](docs/ARCHON_AUDIT.md) — Archon supervisor + audit pipeline
- [Closed-loop audit spec](docs/CLOSED_LOOP_AUDIT_SPEC.md) — two-loop QA architecture
- [Brand guidelines](brand/BRAND_GUIDELINES.md) — full brand system documentation

## Contributing

Pull requests welcome. Please open an issue first for significant changes.

## Testing

```bash
pip install -e .[all] pytest
pytest tests/ -v
```

## License

MIT — see [LICENSE](LICENSE).
