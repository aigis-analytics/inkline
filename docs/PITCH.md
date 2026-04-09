# Inkline

**The branded document engine for teams who need McKinsey-grade output at API speed.**

---

## What is Inkline?

Inkline is a Python toolkit that turns your data into investor-ready decks,
due-diligence reports, and executive briefings — automatically, in your brand.

You describe *what* you want to say. Inkline handles the design.

- 92 themes — consulting, tech, luxury, editorial, industry-specific
- 17 slide layouts — hero stats, timelines, pyramids, comparisons, waterfalls
- 11 chart types — line, waterfall, donut, heatmap, radar, gauge
- 7 pre-built brand identities + unlimited custom brands
- An AI design advisor that picks the right layout for the content
- An overflow audit that guarantees every slide fits on the page

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
Inkline enforces per-layout content capacities and audits every deck before
compiling. If a slide has too many bullets, you get a warning with a fix.

### 5. "We can't afford a visual designer for every report"
Inkline's design advisor uses MBB playbooks (hierarchy, colour theory, data
viz best practices) to make design decisions a junior analyst wouldn't.

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
- It's the only open-source toolkit that combines Typst PDF output, LLM design
  decisions, overflow auditing, and a brand-first mental model.
- It treats "consistency" as a hard constraint, not a best-effort aspiration.
- It's built for agents, not humans-with-mice.

**Where Inkline is not the right tool:**
- You want point-and-click editing → use PowerPoint, Keynote, Canva, or Gamma.
- You want animated web presentations → use Slidev or reveal.js.
- You need live collaboration inside a document → use Google Slides directly.

---

## Under the hood

- **Typst** — the default PDF engine. Rust-based. Fonts embedded. Deterministic.
  Think "LaTeX's successor" but with Python-level ergonomics.
- **Matplotlib** — for charts. Agg backend, no display needed.
- **BaseBrand dataclass** — 8 palette colours + typography + assets + metadata.
- **Intelligence layer** — ContentAnalyzer → LayoutSelector → ChartAdvisor →
  DesignAdvisor (rules / advised / LLM modes).
- **Overflow audit** — `SLIDE_CAPACITY` constants per layout, image aspect-ratio
  checks, automatic truncation in the renderer as a safety net.

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
    brand="aigis",
    template="consulting",
)
```

→ You get a 4-slide investor deck in the Aigis brand, with McKinsey-style
layouts, auto-audited for overflow, compiled to PDF in <2 seconds.

---

## Try it

```bash
pip install "inkline[all] @ git+https://github.com/u3126117/inkline.git"
```

Read the [technical spec](TECHNICAL_SPEC.md) for the full API surface, or jump
into the [README](../README.md) for more examples.

---

## Roadmap

- More themes (industry-specific for healthcare, legal, energy, real estate)
- Automatic slide-to-slide narrative flow (LLM storyboarding)
- Export to Keynote (.key)
- Mermaid / Graphviz diagram integration
- Interactive live preview server

---

**Inkline — because your output should be as good as your analysis.**
