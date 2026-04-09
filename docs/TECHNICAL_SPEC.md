# Inkline — Technical Specification

**Version:** 0.2.0
**Language:** Python 3.11+
**License:** MIT
**Status:** Production

---

## 1. Overview

Inkline is a branded document & presentation toolkit. It accepts Markdown or
structured slide data and produces publication-quality output in several formats.
The default backend is **Typst** (Rust-based typesetter) which produces PDFs with
embedded fonts and crisp vector graphics.

### Design principles

1. **Brand first** — every output is bound to a registered brand identity
   (colours, typography, logos, metadata, chart palette).
2. **Data in, art out** — callers describe *what* they want, never *how* to draw it.
3. **Fits on the page** — hard content limits per layout + an audit pass prevent overflow.
4. **Backend agnostic** — Typst, HTML, WeasyPrint, python-pptx, Google Slides
   all accept the same brand + content model.
5. **Intelligence is optional** — rule-based design advisor works offline; LLM
   advisor activates when `ANTHROPIC_API_KEY` is set.

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Caller (App)                           │
│  Markdown, structured slides, or DesignAdvisor invocation   │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────┐
│                    inkline.intelligence                     │
│  ContentAnalyzer → LayoutSelector → ChartAdvisor            │
│  DesignAdvisor  (rules | advised | llm modes)               │
│  OverflowAudit  (hard capacity + image sizing)              │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────┐    ┌──────────────────────────────┐
│  inkline.brands      │───▶│  inkline.typst.theme_registry│
│  BaseBrand registry  │    │  brand + template → theme    │
│  1 public brand      │    │  (90 themes, 11 templates)   │
└──────────────────────┘    └──────────────┬───────────────┘
                                           │
                                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Output backends                          │
│  typst (default) │ html │ pdf │ pptx │ slides               │
│  slide_renderer  │      │     │      │                     │
│  chart_renderer  │      │     │      │                     │
└─────────────────────────────────────────────────────────────┘
```

### Package layout

```
src/inkline/
├── __init__.py              # Public surface: get_brand, export_html, export_pdf, SlideBuilder
├── brands/
│   ├── __init__.py          # BaseBrand, register_brand, get_brand, list_brands
│   ├── minimal.py           # only built-in brand; private brands live in ~/.config/inkline/brands/
├── html/
│   └── __init__.py          # export_html() — markdown → styled HTML
├── pdf/
│   └── __init__.py          # export_pdf() — HTML → WeasyPrint PDF
├── pptx/
│   └── builder.py           # PptxBuilder — python-pptx wrapper
├── slides/                  # Google Slides API wrapper
├── typst/
│   ├── __init__.py          # export_typst_slides(), export_typst_document()
│   ├── compiler.py          # Typst subprocess wrapper
│   ├── slide_renderer.py    # TypstSlideRenderer — 17 layouts
│   ├── doc_renderer.py      # Markdown → Typst document
│   ├── chart_renderer.py    # matplotlib chart generator (11 types)
│   ├── components.py        # Shared Typst primitives (card, badge, footer…)
│   ├── theme_registry.py    # brand_to_typst_theme(), SLIDE_TEMPLATES
│   └── themes/
│       └── __init__.py      # 90 themes across 13 categories
├── intelligence/
│   ├── __init__.py          # DesignAdvisor, audit_deck, audit_image
│   ├── design_advisor.py    # Main entry — design_deck(), design_document()
│   ├── content_analyzer.py  # ContentAnalysis, ContentType enum
│   ├── layout_selector.py   # select_layout(), SLIDE_CAPACITY
│   ├── chart_advisor.py     # suggest_chart_type()
│   ├── overflow_audit.py    # audit_deck(), audit_image()
│   └── playbooks/           # colour theory, typography, design rules
└── assets/
    └── fonts/               # bundled fonts
```

---

## 3. Data models

### 3.1 `BaseBrand` (brands/__init__.py)

Frozen dataclass with all visual identity tokens.

```python
@dataclass(frozen=True)
class BaseBrand:
    name: str                 # key for get_brand()
    display_name: str
    tagline: str = ""

    # Palette (8 colours, all required)
    primary: str              # accent/CTA
    secondary: str            # accent2/highlights
    background: str           # page background
    surface: str              # dark surface (title bg)
    text: str                 # body text
    muted: str                # captions
    border: str               # lines/rules
    light_bg: str             # card fill

    # Typography
    heading_font: str = "Inter"
    body_font: str = "Inter"
    heading_size: int = 28
    body_size: int = 11

    # Assets
    logo_dark_path: str = ""
    logo_light_path: str = ""

    # Metadata
    confidentiality: str = ""
    footer_text: str = ""

    # Chart palette (list of hex, used in order)
    chart_colors: list[str] = field(default_factory=list)
```

### 3.2 `SlideSpec` / `DeckSpec` (typst/slide_renderer.py)

```python
@dataclass
class SlideSpec:
    slide_type: str                        # one of 17 types
    data: dict[str, Any] = {}              # shape depends on slide_type

@dataclass
class DeckSpec:
    slides: list[SlideSpec]
    title: str = "Untitled"
    date: str = ""
    subtitle: str = ""
```

### 3.3 `LayoutDecision` (intelligence/layout_selector.py)

```python
@dataclass
class LayoutDecision:
    slide_type: str
    num_columns: int = 1
    has_hero: bool = False
    highlight_index: int = -1
    max_items: int = 0        # capacity hint from SLIDE_CAPACITY
    rationale: str = ""
```

### 3.4 Theme dict

Dictionaries generated by `brand_to_typst_theme(brand, template)`. Keys consumed by
`TypstSlideRenderer`: `name`, `desc`, `bg`, `title_bg`, `title_fg`, `text`, `muted`,
`accent`, `accent2`, `border`, `surface`, `card_fill`, `heading_font`, `body_font`,
`heading_size`, `body_size`, `logo_dark_path`, `logo_light_path`, `confidentiality`,
`footer_text`, `chart_colors`.

---

## 4. Public API

### 4.1 Typst backend — `inkline.typst`

```python
export_typst_slides(
    slides: list[dict],
    output_path: str | Path,
    *,
    brand: str = "minimal",
    template: str = "brand",
    title: str = "Untitled",
    date: str = "",
    subtitle: str = "",
    font_paths: list[str | Path] | None = None,
    image_root: str | Path | None = None,
    audit: bool = True,              # run overflow audit before compile
) -> Path

export_typst_document(
    markdown: str,
    output_path: str | Path,
    *,
    brand: str = "minimal",
    title: str = "",
    author: str = "",
    date: str = "",
    font_paths: list[str | Path] | None = None,
) -> Path
```

### 4.2 Legacy backends — `inkline`

```python
export_html(markdown: str, output_path: str | Path, *, brand="minimal", title="") -> Path
export_pdf(markdown: str, output_path: str | Path, *, brand="minimal", title="") -> Path
SlideBuilder(...)  # Google Slides; requires auth
```

### 4.3 Brands — `inkline.brands`

```python
get_brand(name: str) -> BaseBrand
list_brands() -> list[str]
register_brand(brand: BaseBrand) -> None
```

### 4.4 Themes — `inkline.typst.themes`

```python
get_theme(name: str) -> dict
list_themes(category: str | None = None) -> list[str]
list_categories() -> list[str]
search_themes(keyword: str) -> list[str]
ALL_THEMES: dict[str, dict]
THEME_CATEGORIES: dict[str, list[str]]
```

### 4.5 Intelligence — `inkline.intelligence`

```python
class DesignAdvisor:
    def __init__(self, brand: str, template: str = "consulting",
                 mode: Literal["rules", "advised", "llm"] = "advised")
    def design_deck(self, title: str, sections: list[dict],
                    audience: str = "", goal: str = "") -> list[dict]
    def design_document(self, markdown: str, exhibits: list[dict] | None = None) -> str

select_layout(analysis: ContentAnalysis, context: dict | None = None) -> LayoutDecision
SLIDE_CAPACITY: dict[str, int]

# Overflow audit
audit_deck(slides: list[dict]) -> list[AuditWarning]
audit_slide(slide_index: int, slide_type: str, data: dict) -> list[AuditWarning]
audit_image(path, *, max_width_cm=20.7, max_height_cm=8.5, dpi=200) -> list[AuditWarning]
format_report(warnings: list[AuditWarning]) -> str
```

### 4.6 Chart renderer — `inkline.typst.chart_renderer`

```python
render_chart(
    chart_type: str,                   # one of 11 types
    data: dict,
    output_path: str | Path,
    *,
    brand_colors: list[str] | None = None,
    accent: str = "#1A7FA0",
    bg: str = "#FFFFFF",
    text_color: str = "#1A1A1A",
    muted: str = "#6B7280",
    width: float = 8.0,                # inches (slide-safe default)
    height: float = 4.0,
    dpi: int = 200,
) -> Path

render_chart_for_brand(chart_type, data, output_path, brand_name="minimal", **kwargs) -> Path
```

---

## 5. Slide layouts & content capacities

Content limits are enforced in `TypstSlideRenderer` (class constants) and mirrored
in `intelligence.layout_selector.SLIDE_CAPACITY`.

| Slide type       | Capacity      | Notes                                        |
|------------------|---------------|----------------------------------------------|
| `content`        | 8 bullets     | Title + bullet list                          |
| `table`          | 12 rows       | Headers + alternating-row data table         |
| `bar_chart`      | 8 bars        | Native Typst horizontal bars                 |
| `three_card`     | 3 cards       | One can be accent-filled via `highlight_index` |
| `four_card`      | 4 cards       | 2×2 grid                                     |
| `stat`           | 4 stats       | Big hero numbers                             |
| `kpi_strip`      | 6 KPIs        | Horizontal KPI cards                         |
| `split`          | 8 bullets/side| Two-column narrative                         |
| `timeline`       | 8 milestones  | Horizontal milestone nodes                   |
| `process_flow`   | 5 steps       | Numbered steps with arrows                   |
| `icon_stat`      | 4 stats       | Emoji + big number + label                   |
| `progress_bars`  | 7 bars        | Percentage bars with values                  |
| `pyramid`        | 6 tiers       | Hierarchical pyramid                         |
| `comparison`     | 8 rows/side   | Two-column structured comparison             |
| `title`, `closing`| n/a          | Cover and contact slides                     |
| `chart`          | 1 image       | Embedded PNG, max 20.7×8.5 cm                |

### Geometry (constants in `TypstSlideRenderer`)

```
SLIDE_WIDTH_CM   = 23.00   # usable content width  (25.4 − 2×1.2 margins)
SLIDE_HEIGHT_CM  = 12.69   # usable content height (14.29 − 2×0.8 margins)
BODY_HEIGHT_CM   =  8.50   # body area after header + footer
```

---

## 5b. Brand plugin system

Only the `minimal` brand ships in the package. Additional brands are
loaded at import time from user-controlled directories — the package
never contains proprietary logos, palettes, or company names.

### Discovery order (first-win per name)

**Brands** (`.py` files containing `BaseBrand` instances):
1. Every path in `$INKLINE_BRANDS_DIR` (colon-separated, like `$PATH`)
2. `$XDG_CONFIG_HOME/inkline/brands/` (default: `~/.config/inkline/brands/`)
3. `./inkline_brands/` in the current working directory

**Assets** (logo PNGs, font files, referenced by relative path):
1. Every path in `$INKLINE_ASSETS_DIR`
2. `~/.config/inkline/assets/`
3. `./inkline_assets/`
4. The package's bundled `src/inkline/assets/` (shipped fonts only)

### Loader

`inkline.brands._load_user_brands()` runs once on first import. For each
`.py` file in the search path (sorted, skipping `_`-prefixed), it:

1. Calls `importlib.util.spec_from_file_location()` under a synthetic
   `inkline._user_brands.<stem>` namespace
2. Executes the module in its own `ModuleType`
3. Iterates top-level attributes; any `BaseBrand` instance is passed to
   `register_brand()`
4. Catches and logs exceptions at `WARNING` — a broken user brand never
   kills the package import

### User brand file template

```python
# ~/.config/inkline/brands/mycorp.py
from inkline.brands import BaseBrand

MyCorp = BaseBrand(
    name="mycorp",
    display_name="My Corporation",
    primary="#0B5FFF", secondary="#00C2A8",
    background="#FFFFFF", surface="#0A2540", text="#111827",
    muted="#6B7280", border="#E5E7EB", light_bg="#F8FAFC",
    heading_font="Inter", body_font="Inter",
    logo_dark_path="mycorp_logo_white.png",   # resolved from asset dirs
    logo_light_path="mycorp_logo_dark.png",
    confidentiality="Private & Confidential",
    footer_text="My Corporation Pty Ltd",
)
```

### Docker / container integration

Mount the brand directory read-only and set the env vars. Example for
an agentic application container:

```yaml
services:
  agent:
    volumes:
      - ~/.config/inkline:/root/.config/inkline:ro
    environment:
      - INKLINE_BRANDS_DIR=/root/.config/inkline/brands
      - INKLINE_ASSETS_DIR=/root/.config/inkline/assets
```

### Introspection

```python
from inkline.brands import brand_search_paths, asset_search_paths, list_brands
brand_search_paths()   # [Path('/home/user/.config/inkline/brands'), ...]
asset_search_paths()   # [Path('/home/user/.config/inkline/assets'), ...]
list_brands()          # ['minimal', 'mycorp', ...]
```

---

## 6. Themes

90 themes in 13 categories registered in `inkline.typst.themes`. Each theme is a
dict with the same keys as a brand theme (bg, title_bg, accent, chart_colors, etc.).

### Slide templates (layout-style overrides)

10 templates in `inkline.typst.theme_registry.SLIDE_TEMPLATES`:
`executive`, `minimalism`, `newspaper`, `investor`, `consulting`, `pitch`, `dark`,
`editorial`, `boardroom`, `brand` (brand-only, no overrides).

A template applies fixed overrides for `title_bg`, `title_fg`, and optionally
`accent`, `accent2`, `bg`, `card_fill`, `surface`, `text`, `muted`, `border`.

---

## 7. Chart types

All 11 charts use matplotlib Agg backend and render to PNG. Default size 8″×4″
is slide-safe. Brand colours are applied in order from `brand.chart_colors`.

| Chart type     | Input shape                                    |
|----------------|-----------------------------------------------|
| `line_chart`   | `{x: [...], series: [{name, y: [...]}...]}`   |
| `area_chart`   | same as line_chart                             |
| `scatter`      | `{points: [[x,y], ...], labels?: [...]}`       |
| `waterfall`    | `{labels: [...], values: [...]}`               |
| `donut`        | `{labels: [...], values: [...]}` (≤6 segments) |
| `pie`          | same as donut                                  |
| `stacked_bar`  | `{categories: [...], series: [{name, values}]}`|
| `grouped_bar`  | same as stacked_bar                            |
| `heatmap`      | `{x_labels, y_labels, matrix: [[...]]}`        |
| `radar`        | `{axes: [...], series: [{name, values}]}`      |
| `gauge`        | `{value: 0-100, label: str}`                   |

---

## 8. Intelligence layer

### 8.1 ContentAnalyzer

Classifies a section of content into a `ContentType` enum:
`METRICS`, `TABLE`, `TIME_SERIES`, `COMPARISON`, `RANKING`, `RISK`,
`POSITIONING`, `FLOW`, `MIXED`.

### 8.2 LayoutSelector

Maps `ContentAnalysis` → `LayoutDecision`. Rules-based. Every decision carries
its layout's capacity via `max_items` for the caller (including LLM advisors)
to respect.

### 8.3 DesignAdvisor

Three modes:
- `rules` — purely deterministic content analysis + layout selection
- `advised` — rules baseline, then an LLM reviews and refines
- `llm` — LLM drives the full plan, rules supply capacity constraints as context

Plays three playbooks under the hood: design rules (grid, hierarchy), colour
theory (accent vs. muted), and typography (scales, pairings).

### 8.4 Overflow audit

`audit_deck()` checks every slide against `SLIDE_CAPACITY` and emits structured
warnings. `audit_image()` opens PNGs (requires Pillow) and checks that their
aspect ratio won't push them off the slide when fit to width.

`export_typst_slides()` calls `audit_deck()` automatically and logs warnings.
Pass `audit=False` to opt out.

---

## 9. Typst compile pipeline

```
slides (list[dict])
  │
  ▼
overflow_audit.audit_deck() ──▶ log warnings
  │
  ▼
brand + template ──▶ theme (dict)
  │
  ▼
TypstSlideRenderer(theme).render_deck(DeckSpec)
  │  (emits .typ source string)
  ▼
compile_typst(source, output_path, root, font_paths)
  │  (invokes typst-py with bundled fonts + user font_paths)
  ▼
PDF on disk
```

`compile_typst` passes `--root` so relative image paths resolve correctly
when slides embed PNGs. Font paths include `src/inkline/assets/fonts` plus any
caller-supplied directories.

---

## 10. Extensibility

### Add a brand
```python
from inkline.brands import register_brand, BaseBrand
register_brand(BaseBrand(name="mycorp", ...))
```

### Add a theme
Append a dict to `ALL_THEMES` in `src/inkline/typst/themes/__init__.py` and add
it to a category list in `THEME_CATEGORIES`.

### Add a slide template
Add a dict to `SLIDE_TEMPLATES` in `src/inkline/typst/theme_registry.py` with
`_override` suffixed keys.

### Add a slide layout
1. Add a new `_*_slide()` method to `TypstSlideRenderer`
2. Register it in `_render_slide()`'s dispatch dict
3. Add the capacity constant at class level
4. Add it to `SLIDE_CAPACITY` in `layout_selector.py`
5. Add content field mapping in `overflow_audit._CONTENT_FIELDS`
6. Add a test in `tests/`

### Add a chart type
Add a renderer function to `chart_renderer.py` and register it in the dispatch
in `render_chart()`.

---

## 11. Dependencies

### Runtime
- Python ≥ 3.11
- `markdown ≥ 3.5` (core)
- `typst ≥ 0.13` (optional; `[typst]` extra)
- `weasyprint ≥ 60` (optional; `[pdf]` extra)
- `matplotlib ≥ 3.7` (optional; `[charts]` extra)
- `anthropic ≥ 0.25` (optional; `[intelligence]` extra)
- `google-api-python-client ≥ 2.100` (optional; `[slides]` extra)
- `Pillow` (optional; used by overflow audit for image inspection)

### Bundled assets
- Fonts in `src/inkline/assets/fonts/`
- Brand logos in `src/inkline/assets/`

---

## 12. Deployment

Inkline is a pure-Python package built with hatchling. Install directly from
GitHub:

```bash
pip install "inkline[all] @ git+https://github.com/u3126117/inkline.git"
```

Or clone + editable install:

```bash
git clone https://github.com/u3126117/inkline.git
cd inkline
pip install -e .[all]
```

The Typst compiler is pulled in via the `typst` Python package (PyPI) which
bundles the Rust binary. No external `typst` binary required.

---

## 13. Testing

```bash
pytest tests/ -v
```

Test scope: 46 tests covering brands, slide builder, templates, utils.

### What's tested
- Brand registry contents + BaseBrand dataclass
- PPTX element creation (shapes, text boxes, tables, images, lines)
- Slide builder chaining API
- Template listing + individual templates
- Utility functions (hex→rgb, luminance, unit conversions)

### What's not yet tested
- Typst rendering (requires subprocess)
- Chart rendering (matplotlib)
- Overflow audit warnings
- LLM design advisor

---

## 14. Versioning & changelog

- **0.2.0** — Typst backend, 17 slide types, 11 chart types, 90 themes,
  intelligence layer, overflow audit, 11 slide templates, plugin brand loader.
- **0.1.0** — Initial HTML + PDF backends.
