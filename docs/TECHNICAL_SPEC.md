# Inkline — Technical Specification

**Version:** 0.3.0
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
3. **Fits on the page** — hard content limits per layout + a structural audit
   pass + optional Claude vision audit on rendered PNGs prevent overflow.
4. **Facts discipline** — in "data-in" mode the LLM advisor may only restate
   the numbers and claims supplied by the caller; it cannot invent statistics.
   Illustrative content must be marked and is auto-tagged in the renderer.
5. **Backend agnostic** — Typst, HTML, WeasyPrint, python-pptx, Google Slides
   all accept the same brand + content model.
6. **Intelligence is optional and pluggable** — rule-based design advisor works
   offline; LLM advisor activates when `ANTHROPIC_API_KEY` is set OR via the
   bundled Claude Code subprocess caller (no API key required, uses the
   user's logged-in Pro/Max subscription).

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
│  TemplateCatalog (771 archetypes + 16 structured recipes)   │
│  OverflowAudit  (capacity + image sizing + Claude vision)   │
│  ClaudeCodeCaller (subprocess bridge, no API key)           │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────┐    ┌──────────────────────────────┐
│  inkline.brands      │───▶│  inkline.typst.theme_registry│
│  BaseBrand registry  │    │  brand + template → theme    │
│  1 public + plugin   │    │  (90 themes, 10 templates)   │
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
│   ├── slide_renderer.py    # TypstSlideRenderer — 20 layouts
│   ├── document_renderer.py # Markdown → Typst document
│   ├── chart_renderer.py    # matplotlib chart generator (11 types)
│   ├── components.py        # Shared Typst primitives (card, badge, footer…)
│   ├── theme_registry.py    # brand_to_typst_theme(), SLIDE_TEMPLATES
│   └── themes/
│       └── __init__.py      # 90 themes across 13 categories
├── intelligence/
│   ├── __init__.py          # DesignAdvisor, audit_deck, audit_image
│   ├── design_advisor.py    # Main entry — design_deck(), design_document()
│   ├── claude_code.py       # build_claude_code_caller() — subprocess LLM bridge
│   ├── content_analyzer.py  # ContentAnalysis, ContentType enum
│   ├── layout_selector.py   # select_layout(), SLIDE_CAPACITY
│   ├── chart_advisor.py     # suggest_chart_type()
│   ├── overflow_audit.py    # audit_deck(), audit_image(), audit_*_with_llm()
│   ├── playbooks/           # 9 playbooks: colour theory, typography, design
│   │                        #   rules, infographic styles, slide layouts,
│   │                        #   chart selection, document design, visual
│   │                        #   libraries, template catalog
│   └── template_catalog/    # 771-template manifest + 16 archetype recipes
│       ├── __init__.py      # find_templates(), get_archetype_recipe()
│       ├── slidemodel_manifest.json          (328 templates)
│       ├── genspark_professional_manifest.json (128 multi-slide decks)
│       └── genspark_manifest.json            (315 single-thumb templates)
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
    auto_fix: bool = True,           # enable closed-loop fixer
    max_overflow_attempts: int = 6,  # inner loop max (structural fixes)
    max_visual_attempts: int = 3,    # outer loop max (LLM vision rounds)
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
LLMCaller = Callable[[str, str], str]   # (system_prompt, user_prompt) -> text

class DesignAdvisor:
    def __init__(
        self,
        brand: str = "minimal",
        template: str = "brand",
        mode: Literal["rules", "advised", "llm"] = "llm",
        api_key: str | None = None,
        model: str = "claude-sonnet-4-6",
        llm_caller: LLMCaller | None = None,    # plug in any caller
        bridge_url: str = "http://localhost:8082",
    ) -> None: ...

    def design_deck(
        self,
        title: str,
        sections: list[dict],
        *,
        date: str = "",
        subtitle: str = "",
        contact: dict | None = None,
        audience: str = "",
        goal: str = "",
        additional_guidance: str = "",            # free-form steering
        reference_archetypes: list[str] | None = None,  # bias toward catalog patterns
    ) -> list[dict]: ...

    def design_document(self, markdown: str, exhibits: list[dict] | None = None) -> str: ...

select_layout(analysis: ContentAnalysis, context: dict | None = None) -> LayoutDecision
SLIDE_CAPACITY: dict[str, int]

# Structural overflow audit (no API needed)
audit_deck(slides: list[dict]) -> list[AuditWarning]
audit_slide(slide_index: int, slide_type: str, data: dict) -> list[AuditWarning]
audit_image(path, *, max_width_cm=20.7, max_height_cm=8.5, dpi=200) -> list[AuditWarning]
audit_chart_image(image_path) -> list[AuditWarning]            # label clipping, aspect
audit_all_chart_images(charts_dir) -> list[AuditWarning]
audit_rendered_pdf(pdf_path, expected_slides: int) -> list[AuditWarning]
format_report(warnings: list[AuditWarning]) -> str
emit_audit_report(warnings: list[AuditWarning]) -> None        # logger output

# Claude vision audit — pixel-grounded check on the rendered slide
# Routes through bridge /vision endpoint first; SDK only if api_key is explicit.
# NEVER auto-reads ANTHROPIC_API_KEY from env — prevents accidental API spend.
audit_slide_with_llm(
    image_path,
    *,
    slide_index: int = -1,
    slide_type: str = "",
    bridge_url: str = "http://localhost:8082",
    api_key: str | None = None,
    model: str = "claude-sonnet-4-6",
) -> list[AuditWarning]

audit_deck_with_llm(
    pdf_path,
    slides: list[dict],
    *,
    bridge_url: str = "http://localhost:8082",
    api_key: str | None = None,
) -> list[AuditWarning]
```

### 4.6 Claude Code bridge caller — `inkline.intelligence.claude_code`

Inkline routes all LLM calls (text and vision) through a local HTTP bridge
server (`claude_bridge.py`, default `http://localhost:8082`) that wraps the
`claude` CLI. This uses the user's logged-in Claude Pro/Max subscription with
**zero API cost**. The bridge is auto-started if not running.

```python
from inkline.intelligence.claude_code import (
    build_claude_code_caller,
    claude_code_available,
    ensure_bridge_running,
    ClaudeCodeNotInstalled,
)

def build_claude_code_caller(
    *,
    model: str = "sonnet",                # or "opus", or full ID
    timeout: int = 300,
    extra_args: list[str] | None = None,  # forwarded to `claude`
) -> LLMCaller

def claude_code_available() -> bool       # is the `claude` CLI on $PATH?

def ensure_bridge_running(
    bridge_url: str = "http://localhost:8082",
    startup_wait: float = 4.0,
) -> bool
# Checks GET /health. If not healthy, looks for ~/.config/inkline/claude_bridge.py
# and starts it as a detached subprocess. Polls up to startup_wait seconds.
# Returns True if bridge is healthy after the check.
# Called automatically by DesignAdvisor._call_llm() before every bridge request.

class ClaudeCodeNotInstalled(RuntimeError): ...
```

**Bridge HTTP endpoints** (aiohttp server on port 8082):

| Endpoint | Method | Body | Description |
|----------|--------|------|-------------|
| `/health` | GET | — | Returns `{"status":"ok","cli_available":true,"source":"claude_max"}` |
| `/prompt` | POST | `{system, user, max_tokens}` | Text LLM call (design, revision) |
| `/vision` | POST | `{system, prompt, image_base64, image_media_type}` | Multimodal visual audit call |

The bridge uses `claude -p --input-format stream-json --output-format stream-json`
for `/vision` to send multimodal messages. Dynamic timeout formula:
`min(600, max(180, 180 + (total_chars // 1000) * 4 + 60))` — scales with prompt size.

**Bridge auto-install location:** `~/.config/inkline/claude_bridge.py`
(also available in `u3126117/inkline-brands-private`).

**Wire up a custom caller** (e.g. for tests):
```python
caller = build_claude_code_caller(model="sonnet")
advisor = DesignAdvisor(brand="aigis", llm_caller=caller, mode="llm")
```

**Default routing in DesignAdvisor._call_llm():**
1. Custom injected `llm_caller` — highest priority
2. Bridge at `bridge_url` (`INKLINE_BRIDGE_URL` env var overrides) — zero API cost
3. Anthropic SDK with explicit `api_key` — only if bridge unreachable + key provided

### 4.7 Template catalog — `inkline.intelligence.template_catalog`

Searchable index of 771 real slide templates (snapshot 2026-04-09) plus 16
structured archetype recipes for common infographic patterns. Manifests
ship as ~1 MB of static JSON inside the package; image previews stay on
remote CDNs unless `INKLINE_TEMPLATE_CATALOG_DIR` points at a local mirror.

```python
from inkline.intelligence.template_catalog import (
    load_manifest,         # name -> dict ('slidemodel', 'genspark_professional', 'genspark_creative')
    find_templates,        # search by tags / palette / keyword
    list_archetypes,       # 16 names: 'iceberg', 'pyramid', 'waffle', 'funnel_ribbon', ...
    get_archetype_recipe,  # structured recipe: palette_rule, layout, slide_type mapping
    suggest_archetype,     # heuristic given content shape
    get_local_image_dir,
    resolve_local_image,   # CDN URL -> local mirror path if available
)
```

**Sources**
- **SlideModel** — 328 templates from `infographics` and `data-visualization`
  tags. Hex palette, tags, item ID, slide count, gallery URLs.
- **Genspark Professional** — 128 multi-slide decks (12-20 page screenshots each).
- **Genspark Creative** — 315 single-thumbnail prompt-driven templates.

**16 archetypes** wired to renderer recipes: `iceberg`, `sidebar_profile`,
`funnel_kpi_strip`, `persona_dashboard`, `radial_pinwheel`,
`hexagonal_honeycomb`, `semicircle_taxonomy`, `process_curved_arrows`,
`pyramid`, `ladder`, `petal_teardrop`, `funnel_ribbon`, `dual_donut`,
`waffle`, `metaphor_backdrop`, `chart_row`.

Pass them via `DesignAdvisor.design_deck(reference_archetypes=["iceberg",
"funnel_ribbon"])` to bias the LLM toward those patterns.

### 4.8 Chart renderer — `inkline.typst.chart_renderer`

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
| `content`        | 6 bullets     | Title + bullet list                          |
| `table`          | 6 rows        | Headers + alternating-row data table; auto-shrinks font when full |
| `bar_chart`      | 8 bars        | Native Typst horizontal bars                 |
| `three_card`     | 3 cards       | One can be accent-filled via `highlight_index` |
| `four_card`      | 4 cards       | 2×2 grid                                     |
| `stat`           | 4 stats       | Big hero numbers                             |
| `kpi_strip`      | 5 KPIs        | Horizontal KPI cards                         |
| `split`          | 6 bullets/side| Two-column narrative                         |
| `timeline`       | 6 milestones  | Horizontal milestone nodes                   |
| `process_flow`   | 4 steps       | Numbered steps with arrows                   |
| `icon_stat`      | 4 stats       | Emoji + big number + label                   |
| `progress_bars`  | 6 bars        | Percentage bars with values                  |
| `pyramid`        | 5 tiers       | Hierarchical pyramid                         |
| `comparison`     | 6 rows/side   | Two-column structured comparison             |
| `feature_grid`   | 6 features    | Icon + title + body grid (new in 0.3)        |
| `dashboard`      | 3 panels      | Multi-panel KPI/chart dashboard (new in 0.3) |
| `chart_caption`  | 5 caption pts | Chart with structured caption sidebar (new in 0.3) |
| `title`, `closing`| n/a          | Cover and contact slides                     |
| `chart`          | 1 image       | Embedded PNG, max 20.7×8.5 cm                |

**20 slide types total.** Capacities are tighter than 0.2.0 because the
Claude-vision audit pass exposed many cases where the previous limits still
overflowed visually; renderers now also auto-shrink table fonts and bullet
sizes as a final safety net.

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
`brand` (brand-only, no overrides), `executive`, `minimalism`, `newspaper`,
`investor`, `consulting`, `pitch`, `dark`, `editorial`, `boardroom`.

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

**Two operating modes** (orthogonal to the intelligence mode):

- **Mode A — "Data-in" (default for `design_deck()`)**
  Caller provides facts (raw metrics, claims, narratives, comparisons).
  Inkline picks layouts and visualizations. Hard constraint: the LLM may
  only restate or regroup facts that are in the input — it MUST NOT
  invent numbers, names, percentages, or statistics. When data is
  illustrative the section sets `illustrative=True` and the renderer
  adds an "ILLUSTRATIVE" tag to the slide.

- **Mode B — "Spec-in"** (call `export_typst_slides()` with raw slides)
  Caller provides full slide specs. Inkline just renders. No LLM in the loop.

**Three intelligence modes** (Mode A only):
- `rules` — purely deterministic content analysis + layout selection
- `advised` — rules baseline, then an LLM reviews and refines
- `llm` — **default** — LLM drives the full plan, rules supply capacity
  constraints as context

The LLM advisor consumes nine playbooks under the hood: design rules
(grid, hierarchy), colour theory, typography, slide layouts, infographic
styles, chart selection, document design, visual libraries, and the
template catalog (16 archetype recipes). Reference archetypes and free-form
guidance can be passed at call time via `reference_archetypes=` and
`additional_guidance=`.

The LLM caller is fully pluggable via `llm_caller=`. Three call paths:
1. **Anthropic SDK** — set `api_key=` or `ANTHROPIC_API_KEY`. Default.
2. **Claude Code subprocess** — `build_claude_code_caller()`. Uses the
   user's Pro/Max subscription via the local `claude` CLI. No API spend.
3. **Custom** — any `Callable[[system, user], str]`. Use this to plug in
   AWS Bedrock, an internal proxy, or a mocked test caller.

### 8.4 Overflow audit (structural + visual)

**Structural pass** (`audit_deck()`) checks every slide against
`SLIDE_CAPACITY` and emits structured warnings. `audit_image()` /
`audit_chart_image()` open PNGs (requires Pillow) and check aspect ratio
plus matplotlib label clipping. `audit_rendered_pdf()` walks a compiled
PDF and reports per-page issues.

**Visual pass** — Claude vision audit (`audit_slide_with_llm()`,
`audit_deck_with_llm()`) — renders the compiled PDF to PNGs and posts each
page to Claude via the bridge `/vision` endpoint (falls back to SDK only if
an explicit `api_key` is passed — never reads `ANTHROPIC_API_KEY` from env).
Claude inspects for actual visual problems and returns `AuditWarning` objects.

`export_typst_slides()` calls the audit loop automatically. Pass `audit=False`
to opt out of the closed-loop system entirely.

### 8.5 Closed-loop overflow fixer (`slide_fixer.py`)

`apply_graduated_fixes()` is called inside the inner overflow loop with an
escalating attempt number:

| Attempt | Fix strategy | Adds slides? |
|---------|-------------|--------------|
| 1 | Content reduction — trim bullets, shorten title to 50 chars, drop footnote | No |
| 2 | Typst source micro-adjustments — reduce spacing/font/padding in `.typ` string | No |
| 3 | Type downgrade — replace complex type with simpler one (see map below) | No |
| 4 | Selective split — only `content`/`table` slides with ≥ 4 items | Yes |
| 5+ | Aggressive combo — content reduction + type downgrade together | No |

**Type downgrade map (`_DOWNGRADE_MAP`):**

```python
{
    "chart_caption": "split",      # drop chart; keep title+bullets as 2-col
    "dashboard":     "chart_caption",
    "feature_grid":  "content",
    "comparison":    "split",
    "split":         "content",
    "four_card":     "three_card",
    "three_card":    "content",
    "table":         "content",
    "timeline":      "content",
    "icon_stat":     "kpi_strip",  # compact strip; no desc text
    "kpi_strip":     "content",
    "progress_bars": "content",
}
```

**Key design decisions:**
- Type downgrade (attempt 3) always runs before split (attempt 4). Splitting
  adds slides and grows the page count; downgrade converts in-place.
- Only `content` and `table` types are splittable (`_SPLITTABLE_TYPES`). Chart
  and card types overflow due to layout constraints, not item count — splitting
  them produces two identically-overflowing slides.
- Minimum 4 items required before splitting (splitting 3-item slides into
  1+2 produces degenerate near-empty slides).

**Hard caps enforced in `validate_and_fix_slides()`:**

```python
MAX_TITLE_CHARS    = 50
MAX_BULLET_CHARS   = 200
MAX_CARD_BODY_CHARS = 80
TABLE_MAX_ROWS     = 6
TABLE_MAX_COLS     = 6
```

### 8.6 Vishwakarma design philosophy (`vishwakarma.py`)

Four laws baked into all Inkline LLM system prompts and routing logic:

**I. Visual hierarchy** — 5-tier decision ladder (must prefer higher tiers):
- Tier 1 (infographic): `icon_stat`, `kpi_strip`, `feature_grid`, `pyramid`, `progress_bars`
- Tier 2 (chart exhibit): `chart_caption`, `dashboard`, `bar_chart`
- Tier 3 (structural visual): `three_card`, `four_card`, `comparison`, `split`, `timeline`, `process_flow`
- Tier 4 (data table): `table` — ≤ 6×6 only
- Tier 5 (text bullets): `content` — at most 1 per deck

Scoring rule: ≥ 50% slides should be Tier 1 or 2; ≤ 1 `content` slide per deck.

**II. Bridge first** — All LLM calls (text + vision) try the local bridge
before the Anthropic API. Prevents accidental API credit spend.

**III. Visual audit mandatory** — Two-agent design dialogue on every deck.
Auditor (vision) checks rendered PNGs; advisor revises from findings.

**IV. Archon oversight** — A single `Archon` supervisor instance per pipeline
run is the one point of contact. It owns phase tracking, issue logging, and
the final structured report the user sees.

**Exported constants:**
```python
VISHWAKARMA_SYSTEM_PREAMBLE   # injected into DesignAdvisor system prompt
VISHWAKARMA_AUDIT_CRITERIA    # injected into visual auditor system prompt
VISUAL_HIERARCHY              # full text of Law I
BRIDGE_FIRST                  # full text of Law II
AUDIT_MANDATORY               # full text of Law III
ARCHON_OVERSIGHT              # full text of Law IV
```

### 8.7 Archon pipeline supervisor (`archon.py`)

`Archon` is a per-run pipeline supervisor. It attaches a logging handler to
the root `inkline` logger and captures every WARNING/ERROR/INFO emitted during
the run, keyed by phase.

```python
from inkline.intelligence.archon import Archon, Issue, PhaseResult

@dataclass
class Issue:
    phase: str
    severity: str   # "INFO" | "WARNING" | "ERROR"
    message: str
    detail: str = ""   # traceback or extended context

@dataclass
class PhaseResult:
    name: str
    started: datetime
    ended: datetime | None
    ok: bool
    issues: list[Issue]

class Archon:
    def __init__(self, report_path: Path, title: str = "", verbose: bool = True)
    def start_phase(self, name: str) -> PhaseResult
    def end_phase(self, phase: PhaseResult, ok: bool) -> None
    def record(self, issue: Issue) -> None
    def write_report(self) -> None    # Markdown to report_path
    def detach(self) -> None          # remove logging handler
```

Usage pattern (from `gen_corsair_deck.py`):
```python
archon = Archon(WORK_DIR / "archon_issues.md", title="Project Corsair Board DD Deck")
phase = archon.start_phase("design_advisor_llm")
try:
    slides = advisor.design_deck(...)
    archon.end_phase(phase, ok=True)
except Exception as e:
    archon.record(Issue(phase="design_advisor_llm", severity="ERROR",
                         message=str(e), detail=traceback.format_exc()))
    archon.end_phase(phase, ok=False)
    archon.write_report()
    archon.detach()
    sys.exit(1)
```

---

## 9. Typst compile pipeline

```
slides (list[dict])
  │
  ▼
PHASE 0: brand + template ──▶ theme (dict)
  │
  ▼
PHASE 1: chart auto-rendering (one-time; skipped if image_path exists)
  │
  ▼
PHASE 2: validate_and_fix_slides() — enforce hard caps (title 50, card 80, table 6×6)
         equalise_card_heights()   — pad shorter cards to match tallest
  │
  ▼
PHASE 3: OUTER LOOP (visual quality, max max_visual_attempts rounds)
  │
  ├── INNER LOOP (structural overflow, max max_overflow_attempts attempts)
  │     │
  │     ├── TypstSlideRenderer(theme).render_deck(DeckSpec)  → .typ source
  │     ├── compile_typst(source, output_path, root, font_paths)
  │     ├── count pages in compiled PDF
  │     │
  │     ├── [pages == slides] ──▶ break inner loop ✓
  │     └── [pages > slides]  ──▶ identify_overflow_slides()
  │                                  ▶ apply_graduated_fixes(attempt++)
  │                                  ▶ loop
  │
  ├── POST-OVERFLOW: audit_rendered_pdf(), audit_chart_images()
  │
  ├── LLM VISUAL AUDIT: audit_deck_with_llm()
  │     │  (sends each slide PNG to Claude via bridge /vision)
  │     │
  │     ├── [no errors]    ──▶ break outer loop ✓ ship PDF
  │     └── [errors found] ──▶ revise_slides_from_review()
  │                              ▶ re-enter inner loop
  │
  └── PHASE 4: emit_audit_report() ── final AuditWarning list to logs
  │
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

Test scope: 75 tests covering brands, slide builder, templates, intelligence
layer, template catalog, and LLM injection.

### What's tested
- Brand registry contents + BaseBrand dataclass
- PPTX element creation (shapes, text boxes, tables, images, lines)
- Slide builder chaining API
- Template listing + individual templates
- Template catalog manifest loading + archetype recipes
- LLM caller injection (mock callers exercising the `llm_caller=` path)
- Utility functions (hex→rgb, luminance, unit conversions)

### What's not yet tested
- Typst PDF compile (requires subprocess + binary)
- End-to-end chart rendering (matplotlib subprocess)
- Live Claude vision audit (requires API key)
- Live Claude Code subprocess caller (requires `claude` CLI)

---

## 14. Versioning & changelog

- **0.3.x** *(current, 2026-04-13)* —
  - **Vishwakarma design philosophy** — four laws (`VISUAL_HIERARCHY`,
    `BRIDGE_FIRST`, `AUDIT_MANDATORY`, `ARCHON_OVERSIGHT`) baked into all
    LLM system prompts via `inkline.intelligence.vishwakarma`.
    Tier-1/2 visual slides mandated; ≤ 1 `content` bullet slide per deck.
  - **Bridge-first routing** — all LLM calls (text + vision) routed through
    local Claude bridge (`localhost:8082`) before Anthropic API. Visual
    audit uses new `/vision` endpoint (stream-json multimodal input).
    `audit_deck_with_llm` never auto-reads `ANTHROPIC_API_KEY` from env.
  - **Bridge auto-start** — `ensure_bridge_running()` in `claude_code.py`
    checks health and starts `~/.config/inkline/claude_bridge.py` if not
    running. Called automatically before every bridge LLM request.
  - **Dynamic bridge timeout** — `min(600, max(180, 180 + (KB)*4 + 60))`
    scales with prompt size; prevents timeouts on large design prompts.
  - **Narrative truncation** — `MAX_NARRATIVE_CHARS = 1200` per section in
    `DesignAdvisor._build_user_prompt()` keeps total prompt under 80 K chars.
  - **Archon pipeline supervisor** — `inkline.intelligence.archon.Archon`:
    phase tracking, log interception (root `inkline` logger only), structured
    Markdown issues report. `Issue` + `PhaseResult` dataclasses.
  - **Overflow fixer convergence fixes** — attempt order: type_downgrade
    (attempt 3) before slide_split (attempt 4). `_SPLITTABLE_TYPES` restricts
    splitting to `content`/`table` only. `chart_caption` added to
    `_DOWNGRADE_MAP`. New conversion handlers for `chart_caption→split`,
    `icon_stat→kpi_strip`, `kpi_strip/progress_bars→content`. Minimum 4
    items before splitting. `max_overflow_attempts` default 3→6.
  - **Hard caps tightened** — `MAX_TITLE_CHARS` 75→50; `MAX_CARD_BODY_CHARS`
    = 80; `TABLE_MAX_ROWS` = `TABLE_MAX_COLS` = 6.
  - **Model IDs updated** — `claude-sonnet-4-20250514` → `claude-sonnet-4-6`
    throughout `design_advisor.py`, `overflow_audit.py`.
  - **AuditWarning fix** — constructor kwargs corrected in `typst/__init__.py`
    overflow-finding conversion.
  - **Off-by-one fix** — overflow slide index now 1-based for
    `revise_slides_from_review`.

- **0.3.0** *(2026-04-09)* —
  - **Pluggable LLM caller** — `DesignAdvisor(llm_caller=...)` accepts any
    `Callable[[system, user], str]`. Default path is Anthropic SDK; bundled
    `claude_code` module provides Claude Code subprocess bridge with no
    API key spend.
  - **Template catalog** — 771 real-world slide templates + 16 archetype
    recipes wired into the design advisor via `reference_archetypes=`.
  - **Visual audit (Claude vision)** — `audit_slide_with_llm()` and
    `audit_deck_with_llm()` post compiled slide PNGs to Claude for
    pixel-grounded layout/contrast/overflow checks.
  - **Facts discipline** — Mode A vs Mode B contract; LLM may not invent
    numbers; illustrative content auto-tagged in the renderer.
  - **3 new slide types** — `feature_grid`, `dashboard`, `chart_caption`
    (total: 20).
  - **Closed-loop fixer** — `slide_fixer.py` with `apply_graduated_fixes()`
    nested inside `export_typst_slides()` two-loop QA pipeline.
  - **9 design playbooks** (was 3) — added `infographic_styles`,
    `slide_layouts`, `chart_selection`, `document_design`,
    `visual_libraries`, `template_catalog`.

- **0.2.0** — Typst backend, 17 slide types, 11 chart types, 90 themes,
  intelligence layer, structural overflow audit, 10 slide templates,
  plugin brand loader.
- **0.1.0** — Initial HTML + PDF backends.
