# Inkline

**The branded document engine for teams who need McKinsey-grade output at API speed.**

---

## What is Inkline?

Inkline is a Python toolkit that turns your data into investor-ready decks,
due-diligence reports, and executive briefings — automatically, in your brand.

You describe *what* you want to say. Inkline handles the design.

- **90 themes** — consulting, tech, luxury, editorial, industry-specific
- **20 slide layouts** — hero stats, timelines, pyramids, comparisons,
  waterfalls, dashboards, feature grids, infographics
- **11 chart types** — line, waterfall, donut, heatmap, radar, gauge…
- **771-template archetype catalog** — searchable index of curated slide
  designs plus 16 structured archetype recipes
  (`iceberg`, `funnel_ribbon`, `waffle`, `dual_donut`, `pyramid`…) the
  design advisor can copy
- **Brand plugin system** — 1 public brand + unlimited custom brands
  loaded from `~/.config/inkline/brands/`. Proprietary logos and palettes
  never touch the package source.
- **AI design advisor with pluggable LLM caller** — Anthropic SDK,
  Claude Code subprocess (uses your Pro/Max subscription, no API key),
  or any custom callable
- **Two-layer audit** — structural capacity checks + Claude vision pass on
  the rendered PNGs to catch what content limits cannot
- **Facts discipline** — the LLM cannot invent statistics; illustrative
  data is auto-tagged in the slide

Output formats: **Typst PDF** (default), HTML, WeasyPrint PDF, PPTX, Google Slides.

---

## Who it's for

| Audience                     | Why they need Inkline                                    |
|------------------------------|----------------------------------------------------------|
| **Private equity & VC**      | Turn deal-room data into IC memos and LP updates in minutes |
| **Management consultants**   | Generate McKinsey-style decks without a visual designer  |
| **Founders pitching**        | Produce tier-1 investor decks on demand                  |
| **Analysts & researchers**   | Ship publication-quality reports with embedded charts    |
| **Ops & RevOps teams**       | Automated monthly briefings with consistent branding     |
| **AI agent builders**        | The "render layer" their agents have been missing        |

---

## The problems it solves

### 1. "Our decks look inconsistent"
Every slide ships in your brand's palette, typography, and footer. No more
rogue fonts, stretched logos, or off-brand chart colours.

### 2. "My analyst spends 80% of their time in PowerPoint"
Describe the content once in Python (or let an LLM do it). Inkline picks the
right layout, the right chart, the right colour, and compiles a PDF.

### 3. "My AI agent generates great analysis but ugly output"
Plug Inkline into any LangChain / CrewAI / custom agent as the rendering step.
Your agent's insight becomes a boardroom-ready artefact.

### 4. "Content keeps overflowing the slide"
Two audit layers. First, structural capacity checks fire before compile.
Then a Claude-vision pass renders the PDF, sends each page to Claude, and
flags actual visual problems — overflowing text, clipped chart labels,
illegible contrast, off-brand colours — that hard limits cannot detect.

### 5. "We can't afford a visual designer for every report"
Inkline's design advisor consumes nine playbooks (hierarchy, colour theory,
typography, data viz, infographics, slide layouts, document design, visual
libraries, template catalog) and a 771-template archetype catalog of curated
slide designs. It makes design decisions a junior analyst wouldn't.

### 6. "Our brand assets are confidential — we can't commit them to the public toolkit"
Inkline splits public and private cleanly. The package ships with a
single `minimal` brand; your proprietary brand definitions, logos, and
footer strings live in `~/.config/inkline/brands/` (or any path on
`$INKLINE_BRANDS_DIR`) and are auto-loaded on import. Same code, same
API, zero leakage of identity material into source control.

### 7. "We're already paying for Claude — we don't want a separate API key for our docs tool"
Inkline ships a Claude Code subprocess caller. Run `claude /login` once
to authenticate with your Pro/Max subscription, then point Inkline at it
with `build_claude_code_caller()` — no `ANTHROPIC_API_KEY` needed, no
duplicate billing, no secret to manage.

### 8. "We can't trust LLMs to write our investor deck — they'll make up numbers"
Inkline's design advisor runs in "data-in" mode by default. The LLM may
restate or regroup the facts you supply but it cannot invent statistics,
percentages, or names. Anything illustrative must be flagged at the call
site and is auto-tagged "ILLUSTRATIVE" in the rendered slide.

---

## How it compares

| Feature                       | Inkline | PowerPoint | Gamma | Beautiful.ai | python-pptx | Slidev |
|-------------------------------|:-------:|:----------:|:-----:|:------------:|:-----------:|:------:|
| Brand lock (enforced)         | ✅      | ❌          | ⚠️    | ⚠️            | ❌           | ⚠️     |
| 90+ professional themes       | ✅      | ⚠️          | ✅    | ⚠️            | ❌           | ⚠️     |
| Publication-quality PDF       | ✅      | ⚠️          | ⚠️    | ⚠️            | ⚠️           | ✅     |
| LLM design advisor            | ✅      | ❌          | ✅    | ✅            | ❌           | ❌     |
| Overflow audit & auto-fit     | ✅      | ❌          | ❌    | ⚠️            | ❌           | ❌     |
| Python API (agent-friendly)   | ✅      | ❌          | ❌    | ❌            | ✅           | ❌     |
| Bring your own brand          | ✅      | ✅          | ⚠️    | ✅            | ✅           | ✅     |
| Structured data → slides      | ✅      | ❌          | ⚠️    | ⚠️            | ⚠️           | ❌     |
| Self-hosted, no vendor lock   | ✅      | ❌          | ❌    | ❌            | ✅           | ✅     |
| Chart library built-in        | ✅ (11) | ⚠️          | ⚠️    | ⚠️            | ❌           | ❌     |
| Licence                       | MIT     | Commercial | SaaS  | SaaS          | MIT         | MIT    |

**Where Inkline wins:**
- It's the only open-source toolkit that combines Typst PDF output, a
  pluggable LLM design pipeline (Anthropic SDK or Claude Code subprocess),
  pixel-grounded vision auditing, a 771-template archetype catalog, and a
  brand-first mental model.
- It treats "consistency" and "no fabricated facts" as hard constraints,
  not best-effort aspirations.
- It's built for agents, not humans-with-mice.

**Where Inkline is not the right tool:**
- You want point-and-click editing → use PowerPoint, Keynote, Canva, or Gamma.
- You want animated web presentations → use Slidev or reveal.js.
- You need live collaboration inside a document → use Google Slides directly.

---

## Under the hood

- **Typst** — the default PDF engine. Rust-based. Fonts embedded. Deterministic.
  Think "LaTeX's successor" but with Python-level ergonomics.
- **Matplotlib** — for charts. Agg backend, no display needed. Label-clipping
  audit + brand-palette enforcement.
- **BaseBrand dataclass** — 8 palette colours + typography + assets + metadata.
- **Intelligence layer** — ContentAnalyzer → LayoutSelector → ChartAdvisor →
  DesignAdvisor (rules / advised / LLM modes) → 9 design playbooks +
  16 archetype recipes from a 771-template catalog.
- **Pluggable LLM caller** — `LLMCaller = Callable[[system, user], str]`. Drop
  in the Anthropic SDK, the bundled Claude Code subprocess bridge, an internal
  proxy, or a mock for tests.
- **Two-layer audit** — `SLIDE_CAPACITY` structural checks + Claude vision
  pass on rendered PNGs. Automatic table/bullet auto-shrink in the renderer
  as the final safety net.

---

## 60-second demo

```python
from inkline.typst import export_typst_slides

export_typst_slides(
    slides=[
        {"slide_type": "title", "data": {
            "company": "Corsair Capital",
            "tagline": "Series B Pitch",
            "date": "April 2026",
        }},
        {"slide_type": "kpi_strip", "data": {
            "section": "Traction", "title": "Last 12 months",
            "kpis": [
                {"value": "$8.4M", "label": "ARR",        "highlight": True},
                {"value": "212%",  "label": "Net revenue retention"},
                {"value": "94%",   "label": "Gross margin"},
            ],
        }},
        {"slide_type": "three_card", "data": {
            "section": "Market",
            "title": "Three tailwinds",
            "highlight_index": 1,
            "cards": [
                {"title": "Cloud spend ↑",  "body": "..."},
                {"title": "AI unlocked",   "body": "..."},
                {"title": "Data fragmentation", "body": "..."},
            ],
        }},
        {"slide_type": "closing", "data": {
            "company": "Corsair Capital",
            "name": "Jane Doe", "role": "CEO", "email": "jane@corsair.com",
        }},
    ],
    output_path="corsair_pitch.pdf",
    brand="minimal",
    template="consulting",
)
```

→ You get a 4-slide investor deck in the minimal brand, with McKinsey-style
layouts, auto-audited for overflow, compiled to PDF in <2 seconds.

---

## Try it

```bash
pip install "inkline[all] @ git+https://github.com/u3126117/inkline.git"
```

Read the [technical spec](TECHNICAL_SPEC.md) for the full API surface, or jump
into the [README](../README.md) for more examples.

---

## What's new in 0.3

- **Pluggable LLM caller** — bring your own caller, including the bundled
  Claude Code subprocess bridge that uses your Pro/Max subscription with
  no API key spend
- **771-template archetype catalog** — searchable index of real-world
  decks (SlideModel + Genspark) plus 16 structured archetype recipes
- **Visual audit** — Claude vision pass on rendered slide PNGs catches
  what content limits cannot
- **Facts discipline** — LLM cannot invent statistics; illustrative
  data is auto-tagged
- **3 new slide types** — `feature_grid`, `dashboard`, `chart_caption`
- **Tighter capacities** — most layouts dropped 2 items based on
  visual-audit feedback; tables auto-shrink fonts as a safety net
- **9 design playbooks** (up from 3)

## Roadmap

- More themes (industry-specific for healthcare, legal, energy, real estate)
- Automatic slide-to-slide narrative flow (LLM storyboarding)
- Local image catalog mirror (offline image-grounded design)
- Export to Keynote (.key)
- Mermaid / Graphviz diagram integration
- Interactive live preview server

---

**Inkline — because your output should be as good as your analysis.**
