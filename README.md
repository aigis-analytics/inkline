# Inkline

**Branded document & presentation toolkit — Typst, HTML, PDF, PPTX, Google Slides.**

Inkline turns structured data or Markdown into publication-quality, brand-consistent
output. It ships with 90 built-in themes, 37 slide templates (10 curated + 27
additional design system styles), 21 slide layouts, 20+ chart/exhibit types
(standard charts + 16 infographic archetypes + institutional exhibit types),
a 1-brand public registry (extensible via plugins), an LLM-driven design advisor
with a pluggable caller (Anthropic SDK or Claude Code subprocess — no API key
required), 10 design playbooks (chart selection, typography, color theory,
professional exhibit design, etc.), a 771-template archetype catalog, and a
two-layer audit (structural + Claude vision) that keeps content inside the slide
frame and on-brand.

```bash
pip install inkline                # core: Markdown → HTML
pip install inkline[typst]         # + Typst PDF (default backend)
pip install inkline[pdf]           # + WeasyPrint PDF
pip install inkline[charts]        # + matplotlib chart renderer
pip install inkline[slides]        # + Google Slides API
pip install inkline[intelligence]  # + LLM design advisor (Anthropic)
pip install inkline[all]           # everything
```

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
| consulting   | McKinsey, BCG, Bain, Deloitte, PwC, EY, KPMG      |
| corporate    | Goldman, JPMorgan, MS, BlackRock                  |
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

## Chart types (20+)

### Standard charts (11)
`line_chart`, `area_chart`, `scatter`, `waterfall`, `donut`, `pie`,
`stacked_bar`, `grouped_bar`, `heatmap`, `radar`, `gauge`

### Institutional exhibit types (4)
| Type | Description |
|------|-------------|
| `marimekko` | Proportional mosaic — column width and cell height both encode data; no axes |
| `entity_flow` | Legal/org structure diagram with tiered grey palette (dark=focal, mid=intermediary, light=peripheral) |
| `divergent_bar` | Vertical bars above/below zero baseline; floating value labels; no y-axis |
| `horizontal_stacked_bar` | 100% stacked horizontal bars showing composition shift over time |

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
inkline-html report.md --brand minimal --title "My Report"
inkline-pdf  report.md --brand mycorp  --title "Quarterly Review"
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
│   ├── slide_renderer.py    # 21 slide layouts (incl. multi_chart)
│   ├── chart_renderer.py    # 20+ chart/exhibit renderers
│   ├── theme_registry.py    # template → theme generation
│   └── themes/              # 90 themes in 13 categories
└── intelligence/     # Design advisor + overflow audit
    ├── design_advisor.py    # DesignAdvisor — LLM design planning + revision
    ├── slide_fixer.py       # Closed-loop overflow fixer (6 graduated fix levels)
    ├── overflow_audit.py    # Structural + Claude vision audit (15 checks)
    ├── claude_code.py       # Bridge caller + ensure_bridge_running()
    ├── archon.py            # Pipeline supervisor: phase tracking + issue log
    ├── vishwakarma.py       # Design philosophy constants (4 laws)
    ├── content_analyzer.py
    ├── layout_selector.py
    ├── chart_advisor.py
    ├── playbooks/           # 10 design playbooks (colour, typography, layouts,
    │                        #   professional exhibit design, …)
    └── design_md_styles/    # 27 additional design system styles
```

## Vishwakarma design philosophy

All LLM-driven design decisions in Inkline are governed by four laws baked into
the system prompts and routing logic:

1. **Visual hierarchy** — Infographic-first decision ladder: icon/KPI strips →
   chart exhibits → structural visuals → data tables → text bullets. Text bullets
   are a last resort; ≥ 50% of slides should be tier 1 or 2.
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

## Documentation

- [Technical specification](docs/TECHNICAL_SPEC.md) — architecture, APIs, data models
- [Commercial pitch](docs/PITCH.md) — capabilities, competitive comparison
- [Archon audit workflow](docs/ARCHON_AUDIT.md) — Archon supervisor + audit pipeline
- [Closed-loop audit spec](docs/CLOSED_LOOP_AUDIT_SPEC.md) — two-loop QA architecture

## Testing

```bash
pip install -e .[all] pytest
pytest tests/ -v
```

## License

MIT — see [LICENSE](LICENSE).
