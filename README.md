# Inkline

**Branded document & presentation toolkit — Typst, HTML, PDF, PPTX, Google Slides.**

Inkline turns structured data or Markdown into publication-quality, brand-consistent
output. It ships with 90 built-in themes, 37 slide templates (10 curated + 27 from
[getdesign.md](https://getdesign.md)), 20 slide layouts, 11 chart types, a 1-brand
public registry (extensible via plugins), an LLM-driven design advisor with a
pluggable caller (Anthropic SDK or Claude Code subprocess — no API key required),
8 design playbooks (chart selection, typography, color theory, etc.), a 771-template
archetype catalog, and a two-layer audit (structural + Claude vision) that keeps
content inside the slide frame and on-brand.

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

## Slide types (17)

**Standard:** `title`, `content`, `three_card`, `four_card`, `stat`, `table`,
`split`, `bar_chart`, `kpi_strip`, `closing`
**Infographic:** `timeline`, `process_flow`, `icon_stat`, `progress_bars`,
`pyramid`, `comparison`
**Embedded:** `chart` (matplotlib PNG/SVG)

## Chart types (11)
`line_chart`, `area_chart`, `scatter`, `waterfall`, `donut`, `pie`,
`stacked_bar`, `grouped_bar`, `heatmap`, `radar`, `gauge`

## Slide templates (37)

10 built-in templates plus 27 design system styles from [getdesign.md](https://getdesign.md):

**Built-in:** `executive`, `minimalism`, `newspaper`, `investor`, `consulting`,
`pitch`, `dark`, `editorial`, `boardroom`, `brand`

**Design.md styles:** `dmd_stripe`, `dmd_vercel`, `dmd_notion`, `dmd_apple`,
`dmd_spotify`, `dmd_tesla`, `dmd_airbnb`, `dmd_coinbase`, `dmd_shopify`,
`dmd_figma`, `dmd_framer`, `dmd_cursor`, `dmd_warp`, `dmd_supabase`,
`dmd_uber`, `dmd_ferrari`, `dmd_bmw`, `dmd_mongodb`, `dmd_intercom`,
`dmd_webflow`, `dmd_miro`, `dmd_posthog`, `dmd_raycast`, `dmd_revolut`,
`dmd_superhuman`, `dmd_zapier`, `dmd_claude`

Each `dmd_*` template extracts color palettes, typography, and visual style from
the company's design system spec and applies them as theme overrides.

```python
# Use Stripe's design system aesthetic
export_typst_slides(slides=slides, brand="minimal", template="dmd_stripe")
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
│   ├── slide_renderer.py    # 20 slide layouts
│   ├── chart_renderer.py    # 11 matplotlib charts
│   ├── theme_registry.py    # template → theme generation
│   └── themes/              # 90 themes in 13 categories
└── intelligence/     # Design advisor + overflow audit
    ├── design_advisor.py
    ├── content_analyzer.py
    ├── layout_selector.py
    ├── chart_advisor.py
    ├── overflow_audit.py
    ├── playbooks/           # design rules, colour theory, typography
    └── design_md_styles/    # 27 curated design systems (getdesign.md)
```

## Documentation

- [Technical specification](docs/TECHNICAL_SPEC.md) — architecture, APIs, data models
- [Commercial pitch](docs/PITCH.md) — capabilities, competitive comparison
- [Archon audit workflow](docs/ARCHON_AUDIT.md) — how the overflow process works

## Testing

```bash
pip install -e .[all] pytest
pytest tests/ -v
```

## License

MIT — see [LICENSE](LICENSE).
