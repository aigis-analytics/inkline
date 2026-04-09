"""Build A v2 — HAND-CRAFTED Inkline pitch (showcase mode).

A B2C, GitHub-friendly, visually rich pitch that demonstrates Inkline by
USING every major visual capability — multi-exhibit slides, embedded
matplotlib charts, infographic layouts. Each slide is fresh and scannable.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))

from inkline.typst import export_typst_slides, export_typst_document
from inkline.typst.chart_renderer import render_chart_for_brand

OUT = ROOT / "output" / "pitch_compare"
OUT.mkdir(parents=True, exist_ok=True)
CHARTS = OUT / "charts"
CHARTS.mkdir(parents=True, exist_ok=True)

BRAND = "minimal"
TEMPLATE = "pitch"


# ---------------------------------------------------------------------------
# CHART GENERATION — real matplotlib PNGs that get embedded in slides
# ---------------------------------------------------------------------------

def generate_charts():
    """Render the chart PNGs that the deck embeds."""
    print("Generating chart PNGs...")

    # 1. Time-saved comparison (line chart) — Inkline vs traditional
    render_chart_for_brand("line_chart", {
        "x": ["Day 1", "Day 2", "Day 3", "Day 4", "Day 5"],
        "series": [
            {"name": "Traditional (PowerPoint)", "values": [4, 8, 12, 16, 20]},
            {"name": "Inkline", "values": [0.5, 0.5, 0.5, 0.5, 0.5]},
        ],
        "x_label": "Day",
        "y_label": "Hours spent on slides",
    }, str(CHARTS / "time_saved.png"), brand_name=BRAND)

    # 2. Stack comparison (donut) — what's in the box
    render_chart_for_brand("donut", {
        "segments": [
            {"label": "Slide layouts", "value": 20},
            {"label": "Chart types", "value": 11},
            {"label": "Themes", "value": 90},
            {"label": "Output formats", "value": 6},
        ],
        "center_label": "Inkline\nv0.2",
    }, str(CHARTS / "capabilities.png"), brand_name=BRAND)

    # 3. Adoption velocity (area chart) — installs over time (illustrative)
    render_chart_for_brand("area_chart", {
        "x": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
        "series": [
            {"name": "GitHub stars", "values": [10, 45, 120, 280, 540, 920]},
        ],
    }, str(CHARTS / "adoption.png"), brand_name=BRAND)

    # 4. Feature radar — Inkline vs Gamma vs PowerPoint
    render_chart_for_brand("radar", {
        "axes": ["Brand Lock", "PDF Quality", "AI Design", "Python API", "Open Source", "Charts"],
        "series": [
            {"name": "Inkline",     "values": [95, 90, 85, 100, 100, 90]},
            {"name": "Gamma",       "values": [50, 65, 90, 0, 0, 60]},
            {"name": "PowerPoint",  "values": [40, 70, 0, 0, 0, 60]},
        ],
    }, str(CHARTS / "radar.png"), brand_name=BRAND)

    # 5. Cost waterfall — what teams save by switching
    render_chart_for_brand("waterfall", {
        "items": [
            {"label": "Manual cost", "value": 200, "total": True},
            {"label": "Designer", "value": -80},
            {"label": "Analyst time", "value": -90},
            {"label": "Revisions", "value": -25},
            {"label": "Inkline cost", "value": 5, "total": True},
        ],
    }, str(CHARTS / "savings.png"), brand_name=BRAND)

    print(f"  -> {len(list(CHARTS.glob('*.png')))} charts generated")


# ---------------------------------------------------------------------------
# SLIDEPACK — every slide is a different visual showcase
# ---------------------------------------------------------------------------

SLIDES = [
    # 1. TITLE
    {"slide_type": "title", "data": {
        "company": "Inkline",
        "tagline": "Branded documents and decks for teams who'd rather ship than format",
        "date": "Open source · MIT licensed",
        "left_footer": "github.com/u3126117/inkline",
    }},

    # 2. ICON_STAT — the problem in human terms
    {"slide_type": "icon_stat", "data": {
        "section": "The Problem",
        "title": "Where your week actually goes",
        "stats": [
            {"value": "32h", "icon": "⏱", "label": "In PowerPoint", "desc": "per week, per analyst"},
            {"value": "8h", "icon": "📊", "label": "Doing analysis", "desc": "the work you got hired for"},
            {"value": "0h", "icon": "🎨", "label": "With a designer", "desc": "you can't afford one"},
        ],
        "footnote": "Hours wasted formatting are hours not shipping insight.",
    }},

    # 3. CHART_CAPTION — show the time saved with a real chart
    {"slide_type": "chart_caption", "data": {
        "section": "The Solution",
        "title": "From days of formatting to seconds of compilation",
        "image_path": "charts/time_saved.png",
        "caption": "Illustrative comparison; Inkline benchmarked at <2s per deck.",
        "bullets": [
            "Sub-2-second PDF compilation via Typst",
            "Same brand every time, no manual fixes",
            "Drop into any Python pipeline as the render step",
            "Works offline, self-hosted, MIT licensed",
            "Built for AI agents, not humans-with-mice",
        ],
    }},

    # 4. FEATURE_GRID — six capabilities at once
    {"slide_type": "feature_grid", "data": {
        "section": "What's Inside",
        "title": "Six engines, one Python import",
        "features": [
            {"title": "Typst PDF backend", "body": "Rust-based, deterministic, embedded fonts. Sub-2-second compile."},
            {"title": "20 slide layouts", "body": "Title, KPIs, cards, charts, timelines, dashboards, pyramids."},
            {"title": "11 chart types", "body": "Line, waterfall, donut, heatmap, radar, gauge, scatter, more."},
            {"title": "AI design advisor", "body": "Optional Claude-powered layout selection from design playbooks."},
            {"title": "Brand plugin system", "body": "Public package + private brand directory. Zero leakage."},
            {"title": "Overflow audit", "body": "Pre-render check that warns if a slide is too dense."},
        ],
    }},

    # 5. DASHBOARD — chart + stats + bullets all on one slide (the brochure-style)
    {"slide_type": "dashboard", "data": {
        "section": "By the Numbers",
        "title": "What ships in v0.2",
        "image_path": "charts/capabilities.png",
        "stats": [
            {"value": "20", "label": "Slide Layouts"},
            {"value": "11", "label": "Chart Types"},
            {"value": "90+", "label": "Themes"},
        ],
        "bullets": [
            "6 output formats (Typst, HTML, PDF, PPTX, Slides)",
            "7 templates (consulting, pitch, dark, editorial)",
            "Plugin-based brand discovery, MIT licensed",
        ],
    }},

    # 6. PROCESS_FLOW — how it works
    {"slide_type": "process_flow", "data": {
        "section": "How It Works",
        "title": "Three steps from data to publication-quality PDF",
        "steps": [
            {"number": "1", "title": "Describe", "desc": "Pass structured Python sections — metrics, narrative, cards, tables."},
            {"number": "2", "title": "Design", "desc": "AI advisor picks the right layout using built-in design playbooks."},
            {"number": "3", "title": "Render", "desc": "Typst compiles to publication-quality PDF in under two seconds."},
        ],
    }},

    # 7. CHART_CAPTION — radar showing competitive position
    {"slide_type": "chart_caption", "data": {
        "section": "Compare & Contrast",
        "title": "The only tool that scores high on every axis",
        "image_path": "charts/radar.png",
        "caption": "Higher is better; based on public docs and feature inventories.",
        "bullets": [
            "Brand lock that's actually enforced",
            "Python API that AI agents can call",
            "Built-in chart library, no plugins",
            "Open source, no vendor lock-in",
            "Publication-quality PDF output",
        ],
    }},

    # 8. TABLE — compact compare/contrast (5 columns, 6 rows max — fits on slide)
    {"slide_type": "table", "data": {
        "section": "Compare & Contrast",
        "title": "How Inkline stacks up",
        "headers": ["Feature", "Inkline", "PowerPoint", "Gamma", "python-pptx"],
        "rows": [
            ["Brand lock enforced",   "Yes",      "No",     "Partial",  "No"],
            ["Publication PDF",       "Yes",      "Partial","Partial",  "Partial"],
            ["AI design advisor",     "Yes",      "No",     "Yes",      "No"],
            ["Python API for agents", "Yes",      "No",     "No",       "Yes"],
            ["Built-in charts",       "11 types", "Some",   "Some",     "No"],
            ["Open source",           "MIT",      "No",     "No",       "MIT"],
        ],
        "footnote": "Only Inkline combines brand lock, AI design intelligence, charts, and a Python-native API.",
    }},

    # 9. CHART_CAPTION — savings waterfall
    {"slide_type": "chart_caption", "data": {
        "section": "ROI",
        "title": "Why teams switch in their first sprint",
        "image_path": "charts/savings.png",
        "caption": "Per-deck cost; figures illustrative.",
        "bullets": [
            "$200 worth of designer time per deck",
            "8+ hours of analyst formatting",
            "$5 of compute for unlimited Inkline runs",
            "97% cost reduction at 100 decks/year",
        ],
    }},

    # 10. THREE_CARD — who it's for, with middle highlighted
    {"slide_type": "three_card", "data": {
        "section": "Who It's For",
        "title": "Three audiences, one render layer",
        "highlight_index": 1,
        "cards": [
            {"title": "AI builders",
             "body": "The render layer LangChain, CrewAI, and custom agents have been missing. Plug Inkline in as the rendering step."},
            {"title": "Analysts & founders",
             "body": "Tier-1 investor decks and publication-quality reports on demand. No designer in the loop."},
            {"title": "Consultants",
             "body": "McKinsey-style decks generated from structured data. Brand-locked across the firm."},
        ],
    }},

    # 11. CHART_CAPTION — adoption growth (area chart)
    {"slide_type": "chart_caption", "data": {
        "section": "Momentum",
        "title": "Open source, free, and getting faster",
        "image_path": "charts/adoption.png",
        "caption": "Illustrative growth trajectory; v0.2 ships April 2026.",
        "bullets": [
            "MIT licensed from day one",
            "Active development, weekly commits",
            "Plug-in brand system for teams",
            "Built in public on GitHub",
            "Try it: pip install inkline[all]",
        ],
    }},

    # 12. PROGRESS_BARS — what's done, what's coming (6 bars to fit page)
    {"slide_type": "progress_bars", "data": {
        "section": "Roadmap",
        "title": "v0.2 ships now, v0.3 lands by Q3",
        "bars": [
            {"label": "Typst backend",      "pct": 100, "value": "Done"},
            {"label": "20 slide layouts",   "pct": 100, "value": "Done"},
            {"label": "11 chart types",     "pct": 100, "value": "Done"},
            {"label": "AI design advisor",  "pct": 95,  "value": "v0.2"},
            {"label": "Industry themes",    "pct": 60,  "value": "v0.3"},
            {"label": "LLM storyboarding",  "pct": 30,  "value": "v0.3"},
        ],
    }},

    # 13. CLOSING — install command + repo
    {"slide_type": "closing", "data": {
        "company": "Inkline",
        "tagline": "Because your output should be as good as your analysis",
        "name": "pip install \"inkline[all]\"",
        "role": "github.com/u3126117/inkline",
        "email": "MIT licensed  ·  open source  ·  agent-ready",
    }},
]


# ---------------------------------------------------------------------------
# DOCUMENT — info-dense, brochure-style markdown
# ---------------------------------------------------------------------------

DOCUMENT_MD = """# Inkline

Branded documents and decks for teams who'd rather ship than format.

## What Inkline is

Inkline is a Python toolkit that turns structured data into investor-ready
decks, due-diligence reports, and executive briefings — automatically, in your
brand. You describe what you want to say. Inkline picks the layout, the chart,
and the colour, and compiles to PDF in under two seconds.

It is open source, MIT licensed, and built for the people whose week is being
eaten by PowerPoint.

## The numbers

| Capability | Count |
|------------|------:|
| Slide layouts | 20 |
| Chart types | 11 |
| Visual themes | 90+ |
| Output formats | 6 |
| Brands shipped | 1 public + unlimited private |
| Compile speed | under 2 seconds |
| Licence | MIT |

## The problem it solves

Analysts spend 80% of their week formatting slides instead of analysing data.
AI agents produce brilliant analysis and dump it as raw markdown. Brand
guidelines exist on paper, not in output. Logos stretch, fonts drift, chart
palettes wander. Inkline fixes all of this with a Python API.

## Compare and contrast

| Feature | Inkline | PowerPoint | Gamma | python-pptx |
|---------|---------|------------|-------|-------------|
| Brand lock enforced | Yes | No | Partial | No |
| Publication-quality PDF | Yes | Partial | Partial | Partial |
| AI design advisor | Yes | No | Yes | No |
| Python API for agents | Yes | No | No | Yes |
| Built-in chart library | 11 types | Some | Some | No |
| Open source | MIT | No | No | MIT |

## Who it is for

- **AI agent builders** — the render layer LangChain and CrewAI have been missing
- **Analysts and founders** — tier-1 investor decks and reports on demand
- **Consultants** — McKinsey-style decks generated from structured data
- **RevOps teams** — automated monthly briefings with consistent branding
- **Open source maintainers** — drop-in branded documentation generation

## Try it

```bash
pip install "inkline[all] @ git+https://github.com/u3126117/inkline.git"
```

## A 60-second example

```python
from inkline.typst import export_typst_slides

export_typst_slides(
    slides=[
        {"slide_type": "title",     "data": {"company": "Acme", "tagline": "Series B"}},
        {"slide_type": "icon_stat", "data": {"title": "Traction", "stats": [
            {"value": "8.4M", "icon": "money", "label": "ARR"},
            {"value": "212%", "icon": "growth", "label": "NRR"},
        ]}},
        {"slide_type": "feature_grid", "data": {"title": "Why now", "features": [...]}},
        {"slide_type": "closing",   "data": {"name": "Jane", "role": "CEO"}},
    ],
    output_path="acme_pitch.pdf",
    brand="minimal",
    template="pitch",
)
```

## Roadmap

- **v0.2** ships now: 20 layouts, 11 charts, AI advisor, plugin brands
- **v0.3** Q3 2026: industry themes (healthcare, legal, energy), LLM storyboarding
- **v0.4** Q4 2026: live preview server, Keynote export, diagram integration

---

**Inkline. Because your output should be as good as your analysis.**

github.com/u3126117/inkline · MIT licensed · open source
"""


def main():
    print("=" * 70)
    print("BUILD A v2 — HAND-CRAFTED SHOWCASE")
    print("=" * 70)

    # Generate charts first
    generate_charts()

    # Slidepack
    slides_path = OUT / "pitch_slides_handcrafted.pdf"
    print(f"\n[1/2] Building showcase slidepack ({len(SLIDES)} slides)...")
    for i, s in enumerate(SLIDES):
        title = s["data"].get("title", s["data"].get("company", ""))
        print(f"  {i+1:2d}. [{s['slide_type']:14s}] {title[:60]}")

    export_typst_slides(
        slides=SLIDES,
        output_path=str(slides_path),
        brand=BRAND,
        template=TEMPLATE,
        title="Inkline",
        date="April 2026",
        subtitle="Branded documents and decks for teams who'd rather ship than format",
        image_root=str(OUT),
    )
    print(f"\n  PDF: {slides_path} ({slides_path.stat().st_size:,} bytes)")

    # Document
    doc_path = OUT / "pitch_doc_handcrafted.pdf"
    print(f"\n[2/2] Building pitch document...")
    export_typst_document(
        markdown=DOCUMENT_MD,
        output_path=str(doc_path),
        brand=BRAND,
        title="Inkline",
        subtitle="Branded documents and decks for teams who'd rather ship than format",
        date="April 2026",
        author="Inkline open-source toolkit",
        paper="a4",
    )
    print(f"  PDF: {doc_path} ({doc_path.stat().st_size:,} bytes)")

    print(f"\n  Brand: {BRAND}  ·  Template: {TEMPLATE}  ·  Mode: hand-crafted showcase")


if __name__ == "__main__":
    main()
