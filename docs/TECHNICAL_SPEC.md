# Inkline — Technical Specification

**Version:** 0.5.0
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
7. **Encoded taste** — the system produces outputs within the range that a designer
   with good judgement would approve, without user handholding. Taste is encoded as
   a three-layer architecture: (1) structured decision framework in the LLM prompt,
   (2) renderer capabilities with semantic parameters, (3) deterministic post-processing
   that enforces style rules regardless of LLM output.
8. **Self-improving** — user feedback and reference deck ingestion continuously update
   the decision matrix, improving chart selection quality over time.

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
│  LAYER 1 — Decision Framework (LLM prompt)                  │
│    DesignAdvisor: 3-step decision sequence (data_structure  │
│    → message_type → enforce params)                         │
│    decision_matrix.yaml: 27+ rules, live confidence scores  │
│    6 Taste Rules + Vishwakarma laws injected into prompt    │
│                                                             │
│  ContentAnalyzer → LayoutSelector → ChartAdvisor            │
│  TemplateCatalog (771 archetypes + 16 structured recipes)   │
│  OverflowAudit  (15 structural/exhibit checks + vision)     │
│  Aggregator     (feedback → confidence → rule promotion)    │
│  DeckAnalyser   (PDF ingestion → DM candidate rules)        │
│  ClaudeCodeCaller (subprocess bridge, no API key)           │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼  Phase 0b
┌─────────────────────────────────────────────────────────────┐
│  LAYER 3 — TasteEnforcer (deterministic, before rendering)  │
│  10 rules: grouped_bar→clean, donut≤6→direct, scatter→      │
│  annotated, auto accent_index, panel title suppression, …   │
│  Always fires regardless of what the LLM requested.         │
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

  ┌──────────────────────────────────────────────────┐
  │  Self-learning feedback loop (background)        │
  │  User accepts/rejects/modifies slide             │
  │    → FeedbackEvent → feedback_log.jsonl          │
  │    → Aggregator updates rule confidence          │
  │    → Modified chart type → propose new rule      │
  │    → Candidate promoted at ≥5 obs + ≥70% rate    │
  │  Reference deck ingestion:                       │
  │  inkline ingest deck.pdf                         │
  │    → DeckAnalyser (pymupdf)                      │
  │    → patterns.md + DM candidate rules            │
  └──────────────────────────────────────────────────┘
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
│   ├── slide_renderer.py    # TypstSlideRenderer — 21 layouts (incl. multi_chart)
│   ├── document_renderer.py # Markdown → Typst document
│   ├── chart_renderer.py    # matplotlib chart generator (20+ types)
│   ├── components.py        # Shared Typst primitives (card, badge, footer…)
│   ├── theme_registry.py    # brand_to_typst_theme(), SLIDE_TEMPLATES
│   └── themes/
│       └── __init__.py      # 90 themes across 13 categories
├── intelligence/
│   ├── __init__.py          # DesignAdvisor, audit_deck, audit_image
│   ├── design_advisor.py    # Main entry — design_deck(), _inject_decision_matrix()
│   ├── decision_matrix_default.yaml  # 27 seed rules (top-tier investment banks and consulting firms)
│   ├── aggregator.py        # Aggregator — feedback → confidence → rule promotion
│   ├── deck_analyser.py     # DeckAnalyser — PDF → chart detection → DM candidates
│   ├── claude_code.py       # build_claude_code_caller() — subprocess LLM bridge
│   ├── content_analyzer.py  # ContentAnalysis, ContentType enum
│   ├── layout_selector.py   # select_layout(), SLIDE_CAPACITY
│   ├── chart_advisor.py     # suggest_chart_type()
│   ├── overflow_audit.py    # audit_deck(), audit_image(), audit_*_with_llm()
│   │                        #   15 structural checks incl. axis/legend/insight-title
│   ├── feedback.py          # capture_feedback(), detect_implicit_feedback()
│   ├── pattern_memory.py    # per-brand YAML pattern store (brand preferences)
│   ├── slide_fixer.py       # closed-loop overflow fixer (6 graduated levels)
│   ├── archon.py            # pipeline supervisor: phase tracking + issue log
│   ├── vishwakarma.py       # design philosophy constants (4 laws)
│   ├── playbooks/           # 10 playbooks: colour theory, typography, design
│   │                        #   rules, infographic styles, slide layouts,
│   │                        #   chart selection, document design, visual
│   │                        #   libraries, template catalog,
│   │                        #   professional exhibit design
│   └── template_catalog/    # 771-template manifest + 16 archetype recipes
│       ├── __init__.py      # find_templates(), get_archetype_recipe()
│       ├── slidemodel_manifest.json          (328 infographic templates)
│       ├── genspark_professional_manifest.json (128 multi-slide decks)
│       └── genspark_manifest.json            (315 single-thumbnail templates)
├── typst/
│   ├── __init__.py          # export_typst_slides(), export_typst_document()
│   ├── compiler.py          # Typst subprocess wrapper
│   ├── slide_renderer.py    # TypstSlideRenderer — 21 layouts (incl. multi_chart)
│   ├── document_renderer.py # Markdown → Typst document
│   ├── chart_renderer.py    # matplotlib chart generator (31 types)
│   ├── taste_enforcer.py    # TasteEnforcer — 10 deterministic taste rules
│   ├── components.py        # Shared Typst primitives (card, badge, footer…)
│   ├── theme_registry.py    # brand_to_typst_theme(), SLIDE_TEMPLATES
│   └── themes/
│       └── __init__.py      # 90 themes across 13 categories
└── assets/
    └── fonts/               # bundled fonts
```

**Per-user config at `~/.config/inkline/`:**
```
~/.config/inkline/
├── decision_matrix.yaml     # live DM (bootstrapped from decision_matrix_default.yaml)
├── feedback_log.jsonl       # all feedback events (one JSON per line)
├── patterns/                # per-brand YAML pattern memory
│   └── {brand}.yaml
└── reference_decks/         # ingested reference decks
    └── {deck_name}/
        ├── analysis.json    # structured chart/layout inventory
        └── patterns.md      # human-readable pattern summary
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
    slide_type: str                        # one of 21 types
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

Searchable index of 771 curated slide templates plus 16 structured archetype
recipes for common infographic patterns. Manifests ship as ~1 MB of static
JSON inside the package; image previews can be mirrored locally via
`INKLINE_TEMPLATE_CATALOG_DIR`.

```python
from inkline.intelligence.template_catalog import (
    load_manifest,         # name -> dict; valid names: 'slidemodel', 'genspark_professional', 'genspark_creative'
    find_templates,        # search by tags / palette / keyword
    list_archetypes,       # 16 names: 'iceberg', 'pyramid', 'waffle', 'funnel_ribbon', ...
    get_archetype_recipe,  # structured recipe: palette_rule, layout, slide_type mapping
    suggest_archetype,     # heuristic given content shape
    get_local_image_dir,
    resolve_local_image,   # local mirror path if available
)
```

The catalog ships as ~1 MB of static JSON manifests (771 templates total):
- 328 infographic and data-visualisation templates with hex palettes and tag metadata
- 128 multi-slide professional deck layouts (12-20 pages each)
- 315 single-thumbnail creative templates with prompt-driven titles

**16 archetypes** wired to renderer recipes: `iceberg`, `sidebar_profile`,
`funnel_kpi_strip`, `persona_dashboard`, `radial_pinwheel`,
`hexagonal_honeycomb`, `semicircle_taxonomy`, `process_curved_arrows`,
`pyramid_detailed`, `ladder`, `petal_teardrop`, `funnel_ribbon`, `dual_donut`,
`waffle`, `metaphor_backdrop`, `chart_row`.

Pass them via `DesignAdvisor.design_deck(reference_archetypes=["iceberg",
"funnel_ribbon"])` to bias the LLM toward those patterns.

### 4.8a Design playbooks — `inkline.intelligence.playbooks`

Ten Markdown playbooks loaded by the DesignAdvisor. CORE playbooks are loaded
in full; SUMMARY playbooks are truncated to ~4 K chars.

| Playbook | Load mode | Content |
|----------|-----------|---------|
| `chart_selection` | CORE | Rules for choosing chart type based on data shape and goal |
| `infographic_styles` | CORE | Visual formats beyond charts: timelines, comparisons, icon grids, flowcharts |
| `professional_exhibit_design` | CORE | Axis elimination, 3-colour discipline, insight-as-headline, Marimekko/entity-flow/divergent-bar patterns, 6 density techniques |
| `slide_layouts` | SUMMARY | Consulting-grade slide structures, Pyramid Principle, layout patterns |
| `template_catalog` | SUMMARY | 16 archetype recipes + decision matrix (section 6 bulk manifest omitted) |
| `color_theory` | CORE | Palette selection, WCAG accessibility, 60-30-10 rule |
| `typography` | CORE | Font selection, pairing rules, type scales |
| `document_design` | SUMMARY | Report formatting, financial tables, RAG displays, callouts |
| `visual_libraries` | SUMMARY | Reference catalogue of open-source chart libraries |
| `design_md_styles` | DYNAMIC | 27 brand design systems (colour palettes, typography, style tags) — generated at runtime |

Load a specific subset via `load_playbooks_for_task(task_type)`:
- `"chart"` → `chart_selection`, `color_theory`, `professional_exhibit_design`
- `"slide"` → `slide_layouts`, `template_catalog`, `typography`, `color_theory`, `professional_exhibit_design`
- `"infographic"` → `infographic_styles`, `template_catalog`, `color_theory`, `typography`, `professional_exhibit_design`
- `"document"` → `document_design`, `typography`, `color_theory`
- `"full"` → all 10

### 4.9 Chart renderer — `inkline.typst.chart_renderer`

```python
render_chart(
    chart_type: str,                   # 11 standard + 4 institutional + 16 infographic
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
    color_mode: str = "palette",       # "palette" | "mono"
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
| `multi_chart`    | 2–6 images    | Multi-exhibit grid: 13 asymmetric layouts (new in 0.3.5+) |
| `title`, `closing`| n/a          | Cover and contact slides                     |
| `chart`          | 1 image       | Embedded PNG, max 20.7×8.5 cm                |

**21 slide types total.** Capacities are tighter than 0.2.0 because the
Claude-vision audit pass exposed many cases where the previous limits still
overflowed visually; renderers now also auto-shrink table fonts and bullet
sizes as a final safety net.

#### `multi_chart` layouts

| Layout | Column spec | Charts | Typical use |
|--------|------------|--------|-------------|
| `equal_2` | 1fr / 1fr | 2 | Side-by-side comparison |
| `equal_3` | 1fr / 1fr / 1fr | 3 | Three-metric overview |
| `equal_4` | 1fr × 4 | 4 | Four-panel equal dashboard |
| `hero_left` | 2fr / 1fr | 2 | Main chart + supporting callout (65/35) |
| `hero_left_3` | 2fr / 1fr / 1fr | 3 | Hero + two supporting panels (50/25/25) |
| `hero_right_3` | 1fr / 1fr / 2fr | 3 | Two context panels + hero (25/25/50) |
| `quad` | (1fr, 1fr) × 2 rows | 4 | Full 2×2 data page |
| `top_bottom` | stack: 1 wide + 1–3 below | 2–4 | Summary chart + detail exhibits |
| `three_top_wide` | 3 small top + 1 wide bottom | 4 | Overview trio + main exhibit |
| `left_stack` | 1 hero left + 2 stacked right | 3 | Feature + two supporting |
| `right_stack` | 2 stacked left + 1 hero right | 3 | Two context + hero right |
| `mosaic_5` | 2 top + 3 bottom | 5 | Rich mosaic analysis page |
| `six_grid` | 3×2 equal grid | 6 | Comprehensive 6-exhibit summary |

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

90 built-in themes in 13 categories registered in `inkline.typst.themes`. Each theme
is a dict with the same keys as a brand theme (`bg`, `title_bg`, `accent`,
`chart_colors`, etc.).

### Private / custom themes

User themes are auto-loaded at import time from:
1. `$INKLINE_THEMES_DIR` (colon-separated paths)
2. `~/.config/inkline/themes/` (default)
3. `./inkline_themes/` (current working directory)

Any `.py` file in these directories is scanned; top-level `dict` instances with
a `"name"` key are registered into `ALL_THEMES`. Errors are logged as warnings
and never raise.

### Slide templates (layout-style overrides)

37+ templates in `inkline.typst.theme_registry.SLIDE_TEMPLATES`:
- **10 curated built-in:** `brand`, `executive`, `minimalism`, `newspaper`,
  `investor`, `consulting`, `pitch`, `dark`, `editorial`, `boardroom`
- **27 additional design system styles:** `dmd_stripe`, `dmd_vercel`, `dmd_notion`,
  etc.

A template applies fixed overrides for `title_bg`, `title_fg`, and optionally
`accent`, `accent2`, `bg`, `card_fill`, `surface`, `text`, `muted`, `border`.

### Private / custom templates

User templates are auto-loaded at import time from:
1. `$INKLINE_TEMPLATES_DIR` (colon-separated paths)
2. `~/.config/inkline/templates/` (default)
3. `./inkline_templates/` (current working directory)

Any `.py` file containing `dict` instances with a `"desc"` key is registered.
Template dicts use `_override`-suffixed keys (e.g., `"title_bg_override"`).

```python
# ~/.config/inkline/templates/my_templates.py
my_boardroom = {
    "desc": "In-house board deck — charcoal header, gold accent",
    "title_bg_override": "#1A1A1A",
    "title_fg_override": "#FFFFFF",
    "accent2_override": "#C9A84C",
}
```

---

## 7. Chart types

All charts use matplotlib Agg backend and render to PNG. Default size 8″×4″
is slide-safe. Brand colours are applied in order from `brand.chart_colors`.

### 7.1 Standard charts (11)

| Chart type     | Input shape | Key params |
|----------------|-------------|------------|
| `line_chart`   | `{x, series: [{name, values}]}` | `spine_style: "minimal"`, `grid: false` |
| `area_chart`   | same as `line_chart` | — |
| `scatter`      | `{points: [{x, y, label?, value_label?, secondary_label?}]}` | `label_style: "annotated"` (callout boxes) |
| `waterfall`    | `{items: [{label, value, total?}]}` | `style: "clean"` |
| `donut`        | `{segments: [{label, value}], center_label?}` | `label_style: "direct"` (radial, no legend) |
| `pie`          | same as `donut` | same |
| `stacked_bar`  | `{categories, series: [{name, values}]}` | `style: "clean"`, `accent_series: N` |
| `grouped_bar`  | same as `stacked_bar` | `style: "clean"`, `accent_index: N` |
| `heatmap`      | `{x_labels, y_labels, values: [[...]]}` | — |
| `radar`        | `{axes: [...], series: [{name, values}]}` | — |
| `gauge`        | `{value: 0-100, label?: str}` | — |

**Enhanced parameters (v0.5):**
- `style: "clean"` on bar charts: removes y-axis, gridlines, and places value labels directly on bars (institutional style)
- `accent_index: N` on `grouped_bar`: bar N receives accent colour; all others receive muted palette
- `accent_series: N` on `stacked_bar`: series N receives accent colour
- `label_style: "direct"` on `donut`/`pie`: radial labels at segment midpoints, no legend panel
- `label_style: "annotated"` on `scatter`: callout box with arrow for each named point

### 7.2 Institutional exhibit types (4)

Designed to meet the same visual discipline standards as institutional
bank and strategy consulting decks: axis elimination, floating labels,
3-colour discipline, insight-as-headline.

| Chart type | Input shape | Design intent |
|------------|-------------|---------------|
| `marimekko` | `{columns: [{label, total, segments: [{label, value}]}]}` | Proportional mosaic — column width and cell height both encode data; no axes or gridlines |
| `entity_flow` | `{nodes: [{id, label, tier}], edges: [{from, to, label}]}` | Legal/org structure diagram with tiered grey palette (dark=focal, mid=intermediary, light=peripheral) |
| `divergent_bar` | `{items: [{label, value}], positive_label?, negative_label?, y_label?}` | Vertical bars above/below zero baseline; floating value labels; no y-axis; shows net flows |
| `horizontal_stacked_bar` | `{periods: [{label, segments: [{label, value}]}], title?, x_label?}` | 100% stacked horizontal bars; composition shift over time; bar height scales with period count |

### 7.2b New institutional chart types (5, added v0.5)

Derived from top-tier investment bank reference decks.

| Chart type | Input shape | Design intent |
|------------|-------------|---------------|
| `dumbbell` | `{points: [{label, value_start, value_end, start_label?, end_label?}], accent_direction: "higher_is_better"\|"lower_is_better"}` | Before/after pairs or spread migration. End dot gets accent if direction is favourable. |
| `transition_grid` | `{rows: [{label, highlight_col}], col_labels: [...], title?}` | Business model transition / revenue mix shift over time. One highlighted cell per row shows "current position". |
| `scoring_matrix` | `{rows: [{label, scores: [0-3]}], col_labels: [...], title?}` | Capability comparison matrix. Scores 0–3 render as ○◔◕● with graduated cell fills. |
| `gantt` | `{tracks: [{label, start, end, colour?}], date_range?, title?}` | Parallel workstream / construction programme. Horizontal bars, no gridlines, label inside bar. |
| `multi_timeline` | `{phases: [{label, sub_label?, duration?, tasks: [str]}], title?}` | Three-band timeline: duration strip (top) / phase name (middle) / task bullets (bottom). Accent dividers between phases. |

### 7.3 Infographic archetypes (16)

Rendered via `render_chart()` — use these `chart_type` strings directly:

| Archetype | Description |
|-----------|-------------|
| `iceberg` | Above/below waterline split with staggered left/right labels |
| `waffle` | Square grid with percentage fills and legend |
| `sidebar_profile` | Initial-badge sidebar with bullet stats |
| `metaphor_backdrop` | Mountain/horizon metaphor with staggered info cards |
| `funnel_kpi_strip` | Funnel stages with KPI strip below |
| `funnel_ribbon` | Ribbon-style funnel with percentage labels |
| `dual_donut` | Concentric inner/outer donut rings |
| `hexagonal_honeycomb` | Hexagon tile grid for category comparisons |
| `radial_pinwheel` | Radial segments around a central hub |
| `semicircle_taxonomy` | Semicircular taxonomy/classification chart |
| `process_curved_arrows` | Left-to-right curved-arrow process flow |
| `pyramid_detailed` | Multi-tier hierarchy pyramid with labels |
| `ladder` | Ascending step diagram for maturity/progression |
| `petal_teardrop` | Petal/teardrop segments radiating from centre |
| `persona_dashboard` | Mini persona card with stats and avatar |
| `chart_row` | Composite of 2–4 sub-charts in one figure (see §7.4) |

### 7.4 Composite chart row (`chart_row`)

Composes multiple charts into a single PNG using matplotlib `GridSpec`.
Supports asymmetric column widths and two-row layouts:

```python
{
    "charts": [                              # 2–4 chart specs
        {
            "chart_type": "line_chart",
            "title": "Revenue trend",
            "data": {...},
            "_ctx": {                        # optional styling context
                "accent": "#1B2A4A",
                "bg": "#FFFFFF",
                "text_color": "#111827",
                "muted": "#6B7280",
            },
        },
        ...
    ],
    "width_ratios": [2, 1, 1],             # optional — 50/25/25 columns
    "rows": 1,                              # 1 (default) or 2 for 2×N grid
    "row_height_ratios": [1, 1],           # optional — relative row heights
    "top_span": False,                      # optional — first chart spans full top row
}
```

Key schemas for sub-chart `data` fields:
- `grouped_bar` / `stacked_bar`: uses `categories` (not `x`) + `series: [{name, values}]`
- `donut`: uses `segments: [{label, value}]` (not `slices`)

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

The LLM advisor consumes ten playbooks under the hood: design rules
(grid, hierarchy), colour theory, typography, slide layouts, infographic
styles, chart selection, document design, visual libraries, template catalog
(16 archetype recipes), and professional exhibit design (axis elimination,
3-colour discipline, insight-as-headline, Marimekko/entity-flow/divergent-bar
patterns, information density techniques). Reference archetypes and free-form
guidance can be passed at call time via `reference_archetypes=` and
`additional_guidance=`.

The advisor also knows the full `multi_chart` slide type with all 8 layout
options. When designing multi-exhibit slides the LLM selects the layout and
each chart sub-type; callers receive a ready-to-render `multi_chart` spec.

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

The structural pass runs **15 checks** in total:

| # | Check | What it flags |
|---|-------|---------------|
| 1–11 | Capacity, image sizing, aspect ratio, label clipping, bullet length, title length, table density, font size, card body length, color count, whitespace | Standard structural limits |
| 12 | AXIS ELIMINATION | Flags charts with both x- and y-axes where at least one could be dropped in favour of floating labels — flags as WARN |
| 13 | LEGEND NECESSITY | Flags chart slides with a legend but only one data series (legend is redundant noise) |
| 14 | INSIGHT TITLE | Flags slides whose title is a neutral label (e.g. "Revenue") rather than an insight statement (e.g. "Revenue up 34% YoY") |
| 15 | POSITIVE (pass) | Confirms exhibit-quality slides (Marimekko, entity_flow, chart_row) are present — logged as positive signal |

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
    "multi_chart":   "chart_caption",  # multi-exhibit → single chart + caption
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

**I. Visual hierarchy** — 5-tier decision ladder with explicit priority within Tier 1:

**Priority within Tier 1: 1C > 1B > 1A.** Always attempt to use a multi-exhibit
layout first. If a single structural infographic fits, prefer it over a plain KPI
callout. 1A and 1B types are also valid as individual exhibit slots within a 1C layout.

- **Tier 1C** (multi-exhibit — highest priority): `multi_chart` with 2–4 exhibit slots
  in 8 asymmetric layouts; `chart_row` composite PNG. For each slot, apply the
  1B → 1A → Tier 2 sub-selector to pick the best exhibit type.
- **Tier 1B** (structural infographic — matplotlib rendered): `iceberg`, `waffle`,
  `pyramid_detailed`, `ladder`, `radial_pinwheel`, `dual_donut`, `petal_teardrop`,
  `hexagonal_honeycomb`, `semicircle_taxonomy`, `process_curved_arrows`,
  `funnel_kpi_strip`, `funnel_ribbon`, `persona_dashboard`, `sidebar_profile`,
  `metaphor_backdrop`
- **Tier 1A** (KPI callout — use standalone or as supporting slots in 1C):
  `kpi_strip`, `icon_stat`, `progress_bars`, `feature_grid`
- **Tier 2** (institutional exhibit — standalone or as 1C slot): `marimekko`,
  `entity_flow`, `divergent_bar`, `horizontal_stacked_bar`, `chart_caption`, `dashboard`
- **Tier 3** (structural visual): `three_card`, `four_card`, `comparison`, `split`, `timeline`, `process_flow`
- **Tier 4** (data table): `table` — ≤ 6×6 only
- **Tier 5** (text bullets): `content` — at most 1 per deck

Scoring rule: ≥ 30% slides should be Tier 1C; ≥ 20% Tier 1A/1B; ≥ 20% Tier 2;
≤ 1 `content` slide per deck. Every deck must contain at least one Tier 1C slide.

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

### 8.8 Design system — three-layer taste architecture

Inkline v0.5 introduces a structured approach to encoded aesthetic quality.

**Layer 1 — Decision framework (LLM prompt)**

The `DesignAdvisor` system prompt no longer presents an option menu. Instead it
runs a three-step decision sequence:

1. Identify `data_structure` (one of 13 canonical values: `single_number`,
   `n_categories_one_value`, `part_of_whole`, `matrix_rows_cols`, etc.)
2. Identify `message_type` (one of 18 values: `ranking_or_comparison`,
   `part_of_whole_breakdown`, `process_or_sequence`, etc.)
3. Look up the matched rule in `decision_matrix.yaml` → get `chart_type` and
   mandatory `enforce` parameters. Apply them unconditionally.

Six **Taste Rules** are also injected: accent = signal not decoration; axis
reduction; donut-as-distribution-story; named scatter → annotated; typography-led
section openers; multi_chart for parallel stories.

**Layer 2 — Renderer capabilities**

All chart renderers accept semantic parameters that encode taste directly:
`style: "clean"`, `accent_index`, `accent_series`, `label_style`. The LLM can
set these explicitly; the TasteEnforcer sets them if the LLM doesn't.

**Layer 3 — TasteEnforcer (deterministic)**

`TasteEnforcer` in `inkline/typst/taste_enforcer.py` runs as Phase 0b in
`export_typst_slides()` — after DesignAdvisor but before rendering. Ten rules
fire regardless of LLM output:

| Rule | Trigger | Action |
|------|---------|--------|
| R-01 | `grouped_bar` without `style` | Force `style: "clean"` |
| R-02 | `stacked_bar` without `style` | Force `style: "clean"` |
| R-03 | `donut`/`pie` ≤ 6 segments | Force `label_style: "direct"` |
| R-04 | `scatter` with named points | Force `label_style: "annotated"` |
| R-05 | `grouped_bar` missing `accent_index` | Infer from highest value or narrative |
| R-06 | Panel chart with `chart_title` | Clear title (panel header carries it) |
| R-07 | `grouped_bar` with > 12 categories | Force `orientation: "horizontal"` |
| R-08 | `line_chart`/`area_chart` | Force `spine_style: "minimal"`, `grid: false` |
| R-09 | `dumbbell` missing `accent_direction` | Default `"higher_is_better"` |
| R-10 | `waterfall` without `style` | Force `style: "clean"` |

The `accent_index` inference (R-05) scans the slide's `narrative` field for
direction keywords ("highest", "leading", "top") and matches them to category
names. If no match, defaults to the index of the largest value in the first series.

### 8.9 Self-learning feedback loop

**Decision matrix** (`~/.config/inkline/decision_matrix.yaml`)

Bootstrapped on first run from the bundled `decision_matrix_default.yaml` (27 rules).
Active rules are injected into every `DesignAdvisor` system prompt via
`_inject_decision_matrix()`. Rule schema:

```yaml
- id: DM-005
  data_structure: n_categories_one_value
  message_type: ranking_or_comparison
  density: full_width
  chart_type: grouped_bar
  enforce: {style: clean, accent_index: auto}
  confidence: 0.93       # 0.0–1.0; updated by Aggregator
  observations: 0        # feedback event count
  source: [institutional-standard]
  status: active         # active | candidate | low_confidence | flagged
```

**Feedback event schema** (`~/.config/inkline/feedback_log.jsonl`)**:**

```json
{
  "event_id": "a3f2b1c4",
  "ts": "2026-04-14T11:32:00Z",
  "deck_id": "corsair_v6",
  "slide_index": 4,
  "action": "modified",           // "accepted" | "rejected" | "modified"
  "dm_rule_id": "DM-005",
  "data_structure": "n_categories_one_value",
  "message_type": "ranking_or_comparison",
  "modified_to": "dumbbell",
  "enforce_overrides": {},
  "source": "explicit"            // "explicit" | "implicit_conversation" | "auditor_accept"
}
```

**Aggregator** (`intelligence/aggregator.py`)**:**

| Event | Effect on matched rule |
|-------|----------------------|
| `accepted` | confidence += 0.01 (capped at 0.99) |
| `rejected` | confidence -= 0.05 (floor 0.10); below 0.40 → `status: "flagged"` |
| `modified` | confidence -= 0.03; `modified_to` → propose candidate rule |

Candidate promotion: `observations ≥ 5` AND `acceptance_rate ≥ 70%` → `status: "active"`

Active demotion: `observations ≥ 10` AND `confidence < 0.40` → `status: "low_confidence"`

**Implicit feedback** (`app/claude_bridge.py`)**:**

The bridge scans every incoming user message for chart correction patterns before
routing to Claude. Patterns detected:

- *"change the bar chart to a dumbbell"* → `{action: "modified", modified_to: "dumbbell"}`
- *"make it horizontal"* → `{action: "modified", enforce_overrides: {orientation: "horizontal"}}`
- *"highlight the 2025 bar"* → `{enforce_overrides: {accent_target: "2025"}}`
- *"too many labels"* → density feedback signal

**Reference deck ingestion** (`inkline ingest deck.pdf`)**:**

`DeckAnalyser` uses pymupdf to analyse PDF pages:
- Classifies each page as `chart_slide`, `kpi_strip`, `text_heavy`, `visual_anchor`, `mixed`
- Detects 8 chart types from drawing path heuristics (rect clusters → bars, circles → donuts, etc.)
- Extracts dominant colour palette from fill colours
- Produces `patterns.md` (same format as `design_inspiration_analysis.md`)
- Appends candidate rules to `decision_matrix.yaml`

---

## 9. Typst compile pipeline

```
slides (list[dict])
  │
  ▼
PHASE 0:  brand + template ──▶ theme (dict)
  │
  ▼
PHASE 0b: TasteEnforcer.apply(slides)              ← NEW in v0.5
  │       10 deterministic rules: clean style, accent_index inference,
  │       direct donut labels, annotated scatter, panel title strip
  ▼
PHASE 1:  chart auto-rendering (one-time; skipped if image_path exists)
  │
  ▼
PHASE 2:  validate_and_fix_slides() — enforce hard caps (title 50, card 80, table 6×6)
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
in `render_chart()`. Always add a normalization block at the top accepting at
least one alternative schema (e.g., `categories/series` as well as the bespoke
native format). Then add a DM rule to `decision_matrix_default.yaml` with the
appropriate `data_structure`, `message_type`, and `enforce` params.

### Extend the decision matrix

Add rules to `~/.config/inkline/decision_matrix.yaml` (runtime) or
`src/inkline/intelligence/decision_matrix_default.yaml` (shipped default):

```yaml
- id: DM-028
  data_structure: n_categories_one_value
  message_type: geographic_distribution
  density: full_width
  chart_type: heatmap
  enforce: {}
  confidence: 0.75
  observations: 0
  source: [custom]
  status: active
```

### Submit feedback programmatically

```python
# Via MCP tool
inkline_submit_feedback(
    deck_id="my_deck",
    slide_index=3,
    action="modified",
    modified_chart_type="dumbbell",
    dm_rule_id="DM-005",
    data_structure="n_categories_one_value",
    message_type="ranking_or_comparison",
)
```

### Ingest a reference deck

```bash
# CLI
inkline ingest /path/to/pitchbook.pdf --name my_reference_deck

# Python / MCP
inkline_ingest_reference_deck(
    pdf_path="/path/to/pitchbook.pdf",
    deck_name="q2_2026",
    deck_context="investment_banking",
)
```

### Add a TasteEnforcer rule

Append to `_RULES` in `src/inkline/typst/taste_enforcer.py`:

```python
{
    "id": "R-11",
    "match_type": "radar",
    "match_context": None,
    "condition": lambda d: len(d.get("axes", [])) < 4,
    "enforce": {"chart_type_warning": "radar needs ≥4 axes to be readable"},
    "reason": "radar charts with <4 axes look like triangles",
},
```

### Add an exhibit type to the advisor
1. Add a row to the `renderers` dict in `render_chart()`
2. Document the data schema in `SLIDE_TYPE_GUIDE` in `design_advisor.py`
3. Add the chart type to relevant `load_playbooks_for_task()` sets if it
   requires specific playbook context
4. Add a visual audit test run (via bridge `/vision`) before shipping

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

- **0.3.5** *(current, 2026-04-13)* —
  - **Institutional exhibit types (4 new chart renderers)**
    - `marimekko` — proportional mosaic with column-width and cell-height
      encoding, no axes, column totals and row labels embedded.
    - `entity_flow` — tiered legal/org structure diagram; three-shade
      grey palette (dark=focal, mid=intermediary, light=peripheral);
      wrap-text connector labels, clamp-safe coordinates.
    - `divergent_bar` — vertical bars above/below zero baseline; floating
      `+/-` value labels; no y-axis; legend embedded inside chart.
    - `horizontal_stacked_bar` — 100% stacked horizontal bars for
      composition shift over time; bar height scales proportionally to
      the number of periods (`min(0.82, 4.0 / n_periods)`).
  - **`multi_chart` slide type** — 8 asymmetric grid layouts (`equal_2`,
    `equal_3`, `equal_4`, `hero_left`, `hero_left_3`, `hero_right_3`,
    `quad`, `top_bottom`) allow 2–4 pre-rendered exhibit images on a
    single slide. Typst fractional columns (`2fr`, `1fr`, etc.) are
    used for exact proportional widths. `hero_left_3` (50/25/25) and
    `quad` (2×2) are the primary institutional patterns.
  - **Enhanced `chart_row` infographic** — `width_ratios` parameter for
    asymmetric column widths; `rows=2` for 2×N grid layouts;
    `row_height_ratios` and `top_span` for top-span wide+narrow patterns.
    Extracted `_render_chart_into_ax()` helper to eliminate duplication
    between single-row and two-row rendering paths.
  - **16 infographic archetypes** — all rendered via `render_chart()` with
    the archetype's `chart_type` string. Visually audited: 0 FAIL across
    all 16 types. Fixed: iceberg label collision (staggered left/right),
    waffle title+pct legend, sidebar_profile aspect distortion,
    metaphor_backdrop card stagger layout.
  - **`professional_exhibit_design` playbook** — 10th design playbook
    loaded as CORE (full text) in DesignAdvisor. Covers: axis elimination
    rules, legend elimination heuristics, 3-colour discipline, insight-
    as-headline title patterns, commentary column layout, 6 information
    density techniques, 7 exhibit type extensions (Marimekko, entity
    diagram, label-positioned scatter, divergent bar, staircase line,
    100% stacked horizontal bar, tick-connected waterfall), process/flow
    standards, table design rules, typography discipline.
  - **3 new visual auditor checks** (Checks 12–14):
    - Check 12 AXIS ELIMINATION: warns when a chart retains both axes
      where floating labels would suffice.
    - Check 13 LEGEND NECESSITY: warns when a legend is shown for a
      single-series chart (redundant noise).
    - Check 14 INSIGHT TITLE: warns when a slide title is a neutral
      label rather than an actionable insight statement.
  - **`multi_chart` added to downgrade map** — overflows from
    `multi_chart` degrade to `chart_caption` (single chart + caption).
  - **`DesignAdvisor` SLIDE_TYPE_GUIDE updated** — full `multi_chart`
    documentation with layout names, hard caps per layout, and usage
    guidance for multi-exhibit slides.

- **0.3.x** *(2026-04-13)* —
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
