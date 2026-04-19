"""Design Advisor — the intelligent orchestrator for Inkline.

Takes structured content (WHAT to present) and decides HOW:
layout, chart type, visual hierarchy, and emphasis.

Two operating modes (orthogonal to the intelligence mode below):

  Mode A — "Data-in" (default for design_deck())
    Caller provides FACTS: raw metrics, claims, narratives, comparisons.
    Inkline (with LLM advisor) picks layouts and visualizations.
    HARD CONSTRAINT: the LLM may only restate/regroup facts that are
    in the input. It MUST NOT invent numbers, names, percentages, or
    statistics. When data is illustrative, the section MUST set
    `illustrative=True` and the renderer adds an "ILLUSTRATIVE" tag.

  Mode B — "Spec-in" (use export_typst_slides directly with raw slides)
    Caller provides full slide specs (slide_type + data).
    Inkline just renders. No LLM in the loop. No interpretation.

Three intelligence modes (only relevant for Mode A):
- "llm" — LLM makes design decisions using playbook context (default)
- "rules" — deterministic heuristics, no API calls (fallback)
- "advised" — rules decide, LLM reviews and suggests tweaks

The LLM mode feeds playbook knowledge as system context and asks
Claude to produce optimal slide specs for the given content.
"""

from __future__ import annotations

import json
import re
import logging
import os
from pathlib import Path
from typing import Any, Callable, Optional

log = logging.getLogger(__name__)

# Type alias for the pluggable LLM caller. Any function that takes a system
# prompt + user prompt and returns the model's text response can be plugged in
# here — no Anthropic SDK dependency required. This is the integration point
# for Claude Code SDK, Claude Max sessions, custom LLM bridges, OpenAI, or any
# other LLM provider.
LLMCaller = Callable[[str, str], str]

# Available slide types that the Typst renderer supports
SLIDE_TYPES = [
    "title", "content", "three_card", "four_card", "stat",
    "table", "split", "chart", "bar_chart", "kpi_strip",
    "timeline", "process_flow", "icon_stat", "progress_bars",
    "pyramid", "comparison", "feature_grid", "dashboard",
    "chart_caption", "multi_chart", "closing", "section_divider",
    # New slide types (P4)
    "credentials", "testimonial", "before_after",
    # New slide types (P5)
    "team_grid",
]

# Slide type descriptions for the LLM
SLIDE_TYPE_GUIDE = """
You are a senior presentation designer who has built investor and board decks for top-tier
professional services clients. Your default reflex is visual, not textual. You make confident
design decisions without hedging.

====================================================================
PRIME DIRECTIVE: PREFER VISUALS OVER TEXT, ALWAYS.
====================================================================

A great Inkline slide is SCANNABLE in 3 seconds, not READ in 30.
Your default reflex should be: "How can I show this visually instead of writing it?"

FORBIDDEN PATTERNS:
- Plain bullet lists ("content" type) when ANY of these alternatives fit:
  numbers → icon_stat/kpi_strip/stat
  comparisons → comparison/split/feature_grid
  steps → process_flow/timeline
  hierarchy → pyramid
  6 items → feature_grid
  trends → chart/chart_caption (request chart_type from caller)
- Tables wider than 6 columns or longer than 6 rows (they overflow the slide).
- Two consecutive text-heavy slides (content + content + content = boring).
- A slide that has only one element if a multi-exhibit layout would work better.

REQUIRED CADENCE:
- AT LEAST 60% of content slides must be visual layouts (icon_stat, kpi_strip,
  feature_grid, dashboard, chart_caption, timeline, process_flow, pyramid,
  progress_bars, comparison, three_card, four_card).
- AT MOST 1 plain "content" (bullet list) slide per deck.
- Every numerical value should be hero-formatted (icon_stat, stat, or kpi_strip).
- Every multi-step concept should be process_flow or timeline.

====================================================================
SLIDE TYPE DECISION SEQUENCE (follow in order for every content slide)
====================================================================

STEP 1 — WHAT IS THE PRIMARY CONTENT TYPE?
  data (metrics/quantitative)  → chart types, icon_stat, kpi_strip, stat
  comparison (A vs B)          → comparison, split, four_card, three_card
  process (sequential steps)   → process_flow (≤4 steps), timeline (≤6 events with dates)
  narrative (conceptual)       → three_card, pyramid, feature_grid

STEP 2 — IS THERE A DOMINANT SINGLE METRIC?
  yes, one hero number         → icon_stat or stat first
  yes, 3-5 KPIs               → kpi_strip
  no dominant metric           → continue to Step 3

STEP 3 — HOW MANY ITEMS?
  exactly 3                    → three_card, process_flow (3 steps), icon_stat (3 stats)
  exactly 4                    → four_card, process_flow (4 steps), multi_chart equal_4
  exactly 6                    → feature_grid (exactly 6), split (6 per side), table
  4-8 tombstone/deal items    → credentials
  complex multi-facet data    → multi_chart (pick layout by count)

====================================================================
ANTI-PATTERN → CORRECT TRANSFORMATION EXAMPLES
====================================================================

BAD: content slide with 3 metrics in bullets
  → GOOD: icon_stat with 3 stats (value + icon + label each)
  Reason: numbers in bullets are scannable only as stats; icon_stat creates 3x visual impact

BAD: table comparing two options (2 columns, 5 rows)
  → GOOD: comparison slide (left.name="Option A", right.name="Option B", rows with metrics)
  Reason: comparison layout highlights delta and makes winner obvious at a glance

BAD: two consecutive chart_caption slides covering related data facets
  → GOOD: single multi_chart slide (layout="equal_2" or layout="hero_left")
  Reason: side-by-side exhibits let the audience see correlation; two slides require page turns

====================================================================
HARD CAPACITY LIMITS — ENFORCED BY RENDERER (TRUNCATION IS AUTOMATIC)
====================================================================
These limits come from FONT MATH: page width 22.6cm, Source Sans 3 at
specified point sizes, box geometry.  The renderer hard-truncates every
field to its limit before sending to Typst, so overflow is impossible —
but truncated text looks bad. Write within these limits the first time.

TITLES — 45 chars max (ALL slide types)
  22pt bold Source Sans 3 at 22.6cm → 48 chars theoretical; 45 with safety.
  Count your title. "Strong 2P NPV10 of $231mm at 1,354 boepd" = 42 ✓
  BAD: "Acme offers proven upside from operations with material 2P NPV" = 61 → TRUNCATED ✗

PER-FIELD CHAR LIMITS (renderer enforces these exactly):
  content   items:           70 chars each  (14pt full-width = 84/line; tighter for readability)
  split     left/right heading: 26 chars    (18pt bold half-col)
            left/right items:  55 chars each
  three_card cards.title:   24 chars   |  cards.body:    75 chars
  four_card  cards.title:   36 chars   |  cards.body:   120 chars
  stat       stats.value: 8/12/16 chars for 4/3/2 stats  ← CRITICAL
             DO NOT write "$18.33/boe" for a 4-stat slide — it wraps.
             Write "18.33" as value, "/boe" as label instead.
             stats.label: 20 chars  |  stats.desc: 26 chars
  comparison left/right_title: 26 chars
             rows.metric: 22 chars  |  rows.left/right: 30 chars each
  table      headers/cells: 20 chars each (safe for 5-col tables)
  timeline   milestones.date: 12  |  .title: 18  |  .body: 70 chars
  bar_chart  bars.label: 25 chars  |  bars.value: 12 chars
  kpi_strip  kpis.value: 10 chars  |  kpis.label: 20 chars
  feature_grid features.title: 22  |  features.body: 80 chars
  chart_caption bullets: 80 chars each  |  caption: 90 chars
  dashboard  stats.value: 10  |  stats.label: 22  |  bullets: 70 chars
  icon_stat  stats.value: 14  |  stats.label: 22  |  stats.desc: 50 chars
  footnote: 80 chars (ALL slide types)

ITEM COUNTS (items beyond limit are SILENTLY DROPPED):
- chart_caption bullets: MAX 4
- dashboard: EXACTLY 3 stats, MAX 3 bullets
- feature_grid: EXACTLY 6 features (3×2 grid)
- table: MAX 6 rows × 6 columns. NEVER exceed 6 columns.
  If data has >6 rows, pick the 6 most important.
  NEVER use table when data has >6 columns — use split or comparison.
- three_card: EXACTLY 3 cards
- four_card: EXACTLY 4 cards
- icon_stat: 3 or 4 stats
- kpi_strip: 3 to 5 kpis
- timeline milestones: MAX 6
- process_flow steps: MAX 4
- progress_bars: MAX 6 bars
- pyramid tiers: MAX 5
- comparison rows: MAX 6 per side
- content bullets: MAX 6 — AVOID this slide type when possible

BALANCE RULE — equal-height grids:
- three_card, four_card, feature_grid: ALL cards/cells render at the SAME HEIGHT.
  Keep body text length similar across cards so content looks balanced.

CHARTS (chart_caption / dashboard):
- Keep chart titles short — they share vertical space with the image.
- MAX 4 bullets in the side panel.

====================================================================
SLIDE TYPE CATALOGUE
====================================================================

VISUAL HEROES (prefer these):
- icon_stat: Big number + emoji + label, in cards. data: {section, title, stats [{value, icon, label, desc?}], footnote}
  Use for: hero metrics with semantic meaning. Pick emoji that match the metric:
  $/£ for money, ⚡ for speed, 📈 for growth, 🎯 for accuracy, ✓ for done, ⏱ for time.
- kpi_strip: 3-5 metric cards in a strip. data: {section, title, kpis [{value, label, highlight}], footnote}
  Use for: dashboards where one metric is the hero (highlight=true).
- stat: 2-4 hero statistics, very large numbers. data: {section, title, stats [{value, label, desc}]}
- feature_grid: 6 features in a 3x2 grid with numbered icons. data: {section, title, features [{title, body, icon?}], footnote}
  Use for: capability showcases, feature catalogs, "what we offer" — better than 4-card when you have 5-6 items.
- dashboard: Chart image (left 60%) + 3 stat callouts + max 3 bullets (right 40%). data: {section, title, image_path, stats [{value, label}], bullets, footnote}
  Use this for the SHOWCASE slide of any deck — the most info-dense, brochure-style layout.
  HARD CAP: 3 stat callouts, 3 bullets max — anything more overflows.
- chart_caption: Chart image (left 65%) + key takeaways panel (right 35%). data: {section, title, image_path, caption, bullets, footnote}
  Use for: any chart that needs context. ALWAYS prefer this over bare 'chart'.
  HARD CAP: 5 short bullets max.
- chart: Bare embedded chart image (full width). data: {section, title, image_path, footnote}
  Use ONLY when the chart speaks entirely for itself. Prefer chart_caption.
- multi_chart: Multiple charts in a configurable grid. data: {section, title, layout, charts [{image_path, title?}], footnote}
  Single-row layouts: "equal_2" (2 charts 50/50), "equal_3" (3 charts 33/33/33), "equal_4" (4 charts 25×25×25×25),
    "hero_left" (2 charts 65/35), "hero_left_3" (3 charts 50/25/25), "hero_right_3" (3 charts 25/25/50).
  Two-row layouts: "quad" (4 charts 2×2), "top_bottom" (1 wide top + 2-3 below),
    "three_top_wide" (3 small top + 1 wide bottom = 4 total), "mosaic_5" (2 top + 3 bottom = 5 total).
  Asymmetric layouts: "left_stack" (1 hero left + 2 stacked right = 3 total),
    "right_stack" (2 stacked left + 1 hero right = 3 total), "six_grid" (3×2 = 6 charts).
  Use for: institutional multi-exhibit slides — market dashboards, 4-panel data pages, 3-donut rows,
           side-by-side comparisons, mosaic analysis pages, comprehensive 5-6 exhibit summaries.
  Each chart in `charts` list needs an image_path AND a chart_request to auto-render.
  CHART COUNTS: equal_2/hero_left=2, equal_3/hero_left_3/hero_right_3/left_stack/right_stack=3,
    equal_4/quad/top_bottom/three_top_wide=4, mosaic_5=5, six_grid=6.
- bar_chart: Native horizontal bars. data: {section, title, bars [{label, value, pct (0-100)}], footnote}
- progress_bars: Labelled percentage bars. data: {section, title, bars [{label, pct, value?}], footnote}

NARRATIVE LAYOUTS:
- timeline: Horizontal milestones with date nodes. data: {section, title, milestones [{date, label, desc?}], footnote}
  Use for: roadmaps, company history, project plans.
- process_flow: Numbered steps with arrows. data: {section, title, steps [{number, title, desc}], footnote}
  Use for: "how it works", workflows, methodologies (3-5 steps).
- pyramid: 3-5 tier hierarchy (top=smallest, bottom=largest). data: {section, title, tiers [{label, desc?}], footnote}
  Use for: strategic hierarchy, priority tiers, funnels, layered architecture.
- three_card: 3 equal cards with optional accent on one. data: {section, title, cards [{title, body}], highlight_index (0-2), footnote}
- four_card: 2x2 grid. data: {section, title, cards [{title, body}], footnote}
- split: Two-column layout (right side gets accent fill). data: {section, title, left_title, left_items, right_title, right_items}
  Use for: us-vs-them, before-vs-after, problem-vs-solution.
- comparison: Structured side-by-side with metrics. data: {section, title, left {name, items [{label, value}]}, right {name, items [{label, value}]}, footnote}

SPECIALITY LAYOUTS:
- credentials: Grid of 4-8 tombstone cells (track record / deal history). data: {section, title, tombstones [{name, detail}], footnote}
  Use for: track record slides, portfolio showcase, deal history. 2 rows × 2-4 cols layout.
  CAPACITY: 4-8 tombstones (warn if fewer or more).
- testimonial: Large pull-quote slide. data: {section, quote, attribution, image_path?, footnote?}
  Use for: client validation, endorsements, social proof. Quote ≤200 chars, attribution ≤60 chars.
- before_after: Two equal panels (left=Before, right=After). data: {section, title, left {label, items, colour?}, right {label, items, colour?}, footnote?}
  Use for: transformation stories, process improvements, before/after comparisons. 3-5 items per side.

- team_grid: Management team / advisory board bios. data: {section, title, members [{name, role, bio, image_path?, logos?}], footnote?}
  Use for: management team, advisory board, key personnel slides. Always place after the title slide or
  before the business model in pitch decks.
  CAPACITY: 2-4 members. 2-3 members → single row; 4 members → 2×2 grid.
  image_path: filename resolved from charts/ dir, or full absolute path. None → initials placeholder.
  logos: optional list of employer logo filenames (max 4 per member); missing files silently skipped.

STRUCTURAL:
- title: Opening slide. data: {company, tagline, date, subtitle, left_footer}
- closing: Final slide. data: {name, role, email, company, tagline}
- table: Data table — MAX 6 ROWS x 6 COLUMNS. data: {section, title, headers, rows, footnote}
  AVOID unless absolutely necessary. Tables with more than 6 columns will overflow.
- content: Plain bullet list. data: {section, title, items, footnote}
  USE SPARINGLY. Only when nothing else fits.

====================================================================
WRITING RULES
====================================================================
- Action titles: state the CONCLUSION, not the topic.
  BAD: "Business Model" → GOOD: "98% gross margin at scale"
  BAD: "The Problem" → GOOD: "Analysts spend 80% of their week in PowerPoint"
- Card body text: 1-2 short sentences max. No paragraphs.
- Bullet items: 5-10 words each. Telegraphic, not prose.
- Footnotes: optional, one short line, source attribution or caveat.
- Bold emphasis in bullets: wrap the single most important claim in **double asterisks**
  e.g. "Achieved **98% gross margin** at scale in FY25"
  The renderer converts this to bold accent-colour inline text (institutional style).

====================================================================
DESIGN TASTE RULES (non-negotiable)
====================================================================
1. ACCENT = SIGNAL, NOT DECORATION.
   Use accent colour for ONE element per slide: the hero bar, the key number,
   the most important comparison outcome. Everything else uses the muted palette.
   NEVER use accent colour on more than one bar, series, or segment per chart.

2. AXIS REDUCTION.
   For bar charts where comparison is visually obvious: always set style: "clean".
   The renderer removes y-axis, gridlines, and places value labels directly on bars.
   This follows FT/Bloomberg standard — not Excel defaults.

3. DONUT AS DISTRIBUTION STORY.
   Three related distributions = three donuts side-by-side (multi_chart equal_3).
   Each donut has label_style: "direct" — radial labels only, no legend panel.
   NEVER use a single donut when three related breakdowns are available.

4. NAMED SCATTER POINTS → ANNOTATED.
   When a scatter has named data points (competitors, deals, assets), label each
   point directly with a callout box. No legend. label_style: "annotated".

5. TYPOGRAPHY-LED SECTION OPENERS.
   When a slide introduces a new section with modest data (≤2 paras of context),
   the header IS the exhibit. Use section_divider or a bold 3-card layout.
   Do not force a chart onto a conceptual/contextual slide.

6. MULTI_CHART FOR PARALLEL STORIES.
   Two independent data stories → multi_chart equal_2.
   Three categorical distributions → multi_chart equal_3 with donuts.
   Four-panel analysis page → multi_chart quad.
   NEVER stack two separate chart_caption slides when a multi_chart fits.

====================================================================
CHART SELECTION — DECISION FRAMEWORK (follow this, not a menu)
====================================================================

To select a chart type, answer THREE questions in order:

STEP 1 — WHAT SHAPE IS THE DATA?
  single_number            → KPI strip, gauge
  two_values_comparison    → dumbbell
  n_categories_one_value   → grouped_bar (clean)
  n_categories_time_series → line_chart or grouped_bar (clean)
  n_categories_composition → stacked_bar or horizontal_stacked_bar
  part_of_whole            → donut (direct labels if ≤6 segments)
  two_continuous_variables → scatter (annotated labels if points are named)
  matrix_rows_cols         → scoring_matrix (capability) or heatmap (intensity)
  steps_over_time          → multi_timeline (phases+tasks) or gantt (parallel tracks)
  state_transition         → transition_grid
  network_relationships    → entity_flow
  text_heavy_structured    → icon_stat, feature_grid, or scoring_matrix

STEP 2 — WHAT IS THE ONE THING THIS SLIDE MUST PROVE?
  status_at_a_glance      → kpi_strip or gauge
  ranking_or_comparison   → grouped_bar (use accent_index to highlight winner)
  change_over_time        → line_chart (trends) or dumbbell (before/after pairs)
  part_of_whole_breakdown → donut (≤6 cats) or stacked_bar (>6 or over time)
  process_or_sequence     → multi_timeline or ladder
  parallel_workstreams    → gantt
  capability_comparison   → scoring_matrix
  concentration_or_outlier → scatter (label_style: "annotated")
  state_migration         → transition_grid
  waterfall_bridge        → waterfall
  above_below_zero        → divergent_bar
  feature_enumeration     → icon_stat or feature_grid
  hierarchical_structure  → entity_flow

STEP 3 — APPLY MANDATORY PARAMETERS:
  grouped_bar / stacked_bar / waterfall → always add style: "clean"
  grouped_bar → always add accent_index (0-based index of most important bar)
  donut ≤6 segments → always add label_style: "direct"
  scatter with named points → always add label_style: "annotated"
  dumbbell → add accent_direction: "higher_is_better" or "lower_is_better"

DEFAULT: When no rule matches, use grouped_bar with style: "clean".

====================================================================
CHART REQUESTS (auto-rendered by Inkline)
====================================================================
When a slide should embed a chart (chart, chart_caption, dashboard types),
you request the chart by adding a "chart_request" field to the slide data.
Inkline's chart_renderer (matplotlib) will auto-render it before compilation.

HOW TO REQUEST A CHART:
1. Set "image_path" to a simple filename (e.g. "market_growth.png")
2. Add a "chart_request" dict with:
   - "chart_type": one of: line_chart, area_chart, scatter, waterfall, donut,
     pie, stacked_bar, grouped_bar, heatmap, radar, gauge,
     horizontal_stacked_bar, entity_flow, ladder, divergent_bar,
     dumbbell, transition_grid, scoring_matrix, gantt, multi_timeline
   - "chart_data": the data dict for that chart type (see below)

Example — donut chart on a dashboard slide:
  {
    "slide_type": "dashboard",
    "data": {
      "title": "Revenue by segment",
      "image_path": "revenue_donut.png",
      "chart_request": {
        "chart_type": "donut",
        "chart_data": {
          "segments": [
            {"label": "Enterprise", "value": 60},
            {"label": "Mid-Market", "value": 30},
            {"label": "SMB", "value": 10}
          ],
          "center_label": "Revenue\nMix"
        }
      },
      "stats": [{"value": "$5.2M", "label": "Total ARR"}],
      "bullets": ["Enterprise drives 60% of revenue"]
    }
  }

Example — bar chart on a chart_caption slide:
  {
    "slide_type": "chart_caption",
    "data": {
      "title": "Market sizing",
      "image_path": "market_bars.png",
      "chart_request": {
        "chart_type": "grouped_bar",
        "chart_data": {
          "categories": ["2024", "2025", "2026"],
          "series": [
            {"name": "TAM", "values": [8.5, 10, 12]},
            {"name": "SAM", "values": [1.5, 2, 2.5]}
          ],
          "y_label": "$ Billion"
        }
      },
      "caption": "DD market growing at 7.8% CAGR",
      "bullets": ["Energy DD is $1-2B of the $10B+ total"]
    }
  }

CHART DATA FORMATS (by chart_type) — use EXACTLY these field names:
- line_chart / area_chart: {x: [...], series: [{name, values}], x_label?, y_label?}
- waterfall: {items: [{label, value, total?}]}
- donut / pie: {segments: [{label, value}], center_label?}
- stacked_bar / grouped_bar: {categories: [...], series: [{name, values}], y_label?}
- radar: {axes: [...], series: [{name, values}]}
- gauge: {value: 0-100, label?}
- scatter: {points: [{x, y, label?, size?}], x_label?, y_label?}
- heatmap: {x_labels: [...], y_labels: [...], values: [[...]]}  ← values is a 2D list
- horizontal_stacked_bar: {periods: [{label, segments: [{label, value}]}], x_label?, title?}
    Use for: 100% composition across categories. Each "period" is one row.
    Example: {periods: [{label: "Legal", segments: [{label: "Complete", value: 40},
                                                    {label: "Partial", value: 45},
                                                    {label: "Absent", value: 15}]}]}
- entity_flow: {nodes: [{id, label, tier (1=focal/2=intermediary/3=peripheral),
                         x (0.0–1.0), y (0.0–1.0), sublabel?}],
                edges: [{from, to, label?, style ("solid"|"dashed")}], title?}
    CRITICAL: Every node MUST have explicit x and y float coordinates (0.0–1.0).
    Layout convention: y=0.85 is top, y=0.1 is bottom. x=0.5 is centre.
    Example: {nodes: [{id:"buyer", label:"Buyer", tier:3, x:0.5, y:0.85},
                      {id:"target", label:"Target LLC", tier:1, x:0.5, y:0.55},
                      {id:"sub", label:"Operating Sub", tier:1, x:0.5, y:0.25}],
              edges: [{from:"buyer", to:"target", label:"100% acquires"},
                      {from:"target", to:"sub", label:"wholly owns"}]}
- ladder: {steps: [{label, body}]}  ← list of 3–6 ascending staircase steps
    Each step is a card: label = short title, body = 1-line description.
    Example: {steps: [{label:"Q1 2026", body:"G9 spud → TD → first oil"},
                      {label:"Q2 2026", body:"G8 spud, G9 plateau"},
                      {label:"Q3 2026", body:"F4 SM71 spud"}]}
- divergent_bar: {items: [{label, value}], positive_label?, negative_label?, y_label?}
    Use for above/below-zero bar charts (inflow/outflow, bridge variances).
    Positive values → primary colour; negative values → secondary colour.
- dumbbell: {points: [{label, value_start, value_end, start_label?, end_label?}],
             y_label?, accent_direction: "higher_is_better"|"lower_is_better"}
    Use for: before/after comparisons, spread migration, analyst estimate vs actual.
    End dot gets accent colour if it moved in the direction specified by accent_direction.
    Example: {points: [{label:"Bond A", value_start:520, value_end:415, start_label:"At issue", end_label:"Current"}],
              accent_direction: "lower_is_better"}
- transition_grid: {rows: [{label, highlight_col}], col_labels: [...], title?}
    Use for: business model transitions, revenue mix shifts, any 0→100% journey.
    Each row is one time period. highlight_col is the current-position column index.
    Example: {rows: [{label:"2025", highlight_col:1}, {label:"2026", highlight_col:3},
                     {label:"2027", highlight_col:6}, {label:"2028", highlight_col:9}],
              col_labels: ["0%","10%","20%","30%","40%","50%","60%","70%","80%","90%","100%"]}
- scoring_matrix: {rows: [{label, scores: [0-3]}], col_labels: [...], title?}
    Use for: capability comparisons, product/service matrices, scoring frameworks.
    Score 0=empty, 1=light, 2=medium, 3=full (renders as ○◔◕● with cell fills).
    Example: {rows: [{label:"Banks", scores:[3,2,2,1,3,0]},
                     {label:"Bonds", scores:[1,3,3,3,2,2]}],
              col_labels: ["Size","Speed","Cost","Flexibility","Rating","Tenor"]}
- gantt: {tracks: [{label, start, end, colour?}], date_range?: [start, end], title?}
    Use for: construction programmes, project roadmaps, parallel workstreams.
    start/end can be date strings ("2026-01", "Q1 2026") or numeric indices.
    Example: {tracks: [{label:"Foundations", start:"Jan 2026", end:"Apr 2026"},
                       {label:"Superstructure", start:"Apr 2026", end:"Sep 2026"},
                       {label:"Fitout", start:"Aug 2026", end:"Dec 2026"}]}
- multi_timeline: {phases: [{label, sub_label?, duration?, tasks: [str]}], title?}
    Use for: M&A processes, fundraising timelines, any phased process with task details.
    Renders as 3 bands: duration strip (top) / phase name (middle) / task bullets (bottom).
    Example: {phases: [{label:"Preparations", sub_label:"Phase I", duration:"1-8 weeks",
                        tasks:["Management accounts","IM preparation"]},
                       {label:"Marketing", sub_label:"Phase II", duration:"4-6 weeks",
                        tasks:["Investor outreach","NDAs","Management meetings"]}]}

ENHANCED PARAMETERS for existing chart types:
- grouped_bar / stacked_bar / waterfall: add style: "clean" for axis-free institutional style
- grouped_bar: add accent_index: N (0-based) to highlight the most important bar in accent colour
- stacked_bar: add accent_series: N to highlight one series in accent colour
- donut / pie: add label_style: "direct" for radial labels outside each segment (no legend)
- scatter: add label_style: "annotated" for callout boxes with arrows on each named point
  Points support extra fields: value_label (bold value), secondary_label (muted sub-text)

RULES:
- ONLY use chart_request with data that is EXPLICITLY in the input sections.
  DO NOT invent data points.
- If input data contains "illustrative": true, add it to chart_data — the
  renderer will add a watermark automatically.
- Use charts when they genuinely add visual value. Don't force a chart when
  a table or icon_stat would be clearer.
- Prefer donut/waterfall/radar for small datasets, line/area for trends.

====================================================================
"""


class DesignAdvisor:
    """Intelligent presentation design engine.

    Parameters
    ----------
    brand : str
        Brand name (e.g., "minimal" or any user-registered brand).
    template : str
        Slide template style (e.g., "consulting", "executive", "brand").
    mode : str
        Intelligence mode: "llm" (default), "rules", or "advised".
    api_key : str, optional
        Anthropic API key. Falls back to ANTHROPIC_API_KEY env var.
    model : str
        Model to use for LLM calls.
    """

    #: Default LLM bridge URL. Override via env var ``INKLINE_BRIDGE_URL``
    #: (e.g. ``http://host.docker.internal:8082`` from inside Docker).
    DEFAULT_BRIDGE_URL = "http://localhost:8082"

    def __init__(
        self,
        brand: str = "minimal",
        template: str = "brand",
        mode: str = "llm",
        api_key: str | None = None,
        model: str = "claude-sonnet-4-6",
        llm_caller: Optional["LLMCaller"] = None,
        bridge_url: str | None = None,
    ):
        self.brand = brand
        self.template = template
        self.mode = mode
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.model = model
        self.llm_caller = llm_caller
        # Bridge URL: kwarg > env var > class default
        self.bridge_url = (
            bridge_url
            or os.environ.get("INKLINE_BRIDGE_URL", "")
            or self.DEFAULT_BRIDGE_URL
        )
        # Load decision matrix YAML for deterministic prompt injection
        self.decision_matrix: dict = {}
        _matrix_path = Path(__file__).parent / "decision_matrix_default.yaml"
        if _matrix_path.exists():
            try:
                import yaml as _yaml
                with open(_matrix_path, "r", encoding="utf-8") as _f:
                    self.decision_matrix = _yaml.safe_load(_f) or {}
            except Exception:
                try:
                    # Minimal fallback without yaml dep: just record path available
                    self.decision_matrix = {"_path": str(_matrix_path)}
                except Exception:
                    pass

    def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Route an LLM call: injected caller → bridge → Anthropic SDK.

        Priority:
        1. ``self.llm_caller`` — injected custom caller (e.g. test mocks)
        2. LLM bridge at ``self.bridge_url`` — uses Claude Max subscription
        3. Anthropic SDK with ``self.api_key`` / ``ANTHROPIC_API_KEY``
        """
        if self.llm_caller is not None:
            log.info(
                "DesignAdvisor LLM (injected caller): %d sys / %d user chars",
                len(system_prompt), len(user_prompt),
            )
            return self.llm_caller(system_prompt, user_prompt)

        # Ensure bridge is running before attempting to connect — auto-starts from
        # ~/.config/inkline/claude_bridge.py if present.  Zero-cost (1s timeout
        # health check), never blocks if bridge is already up.
        try:
            from inkline.intelligence.claude_code import ensure_bridge_running
            ensure_bridge_running(self.bridge_url)
        except Exception:
            pass  # Non-fatal — proceed to bridge attempt regardless

        # Try bridge — narrative truncation in _build_user_prompt() keeps prompts
        # under ~80K total (47K system + 33K user), within bridge processing limits.
        # Read timeout matches bridge's dynamic timeout (180 + 4s/KB + 60s buffer, max 600s).
        try:
            import requests as _req
            log.info(
                "DesignAdvisor LLM bridge %s (%d sys / %d user chars)...",
                self.bridge_url, len(system_prompt), len(user_prompt),
            )
            # Poll /status until bridge is idle before sending — avoids 502 when a
            # previous run is still finishing after we killed the calling script.
            for _attempt in range(60):  # up to 5 minutes wait
                try:
                    _st = _req.get(f"{self.bridge_url}/status", timeout=3).json()
                    if not _st.get("active", True):
                        break
                except Exception:
                    pass
                import time as _time; _time.sleep(5)
            for _bridge_attempt in range(3):  # retry up to 3x on empty body
                resp = _req.post(
                    f"{self.bridge_url}/prompt",
                    json={"prompt": user_prompt, "system": system_prompt, "max_tokens": 16000},
                    timeout=(5, None),  # 5s connect; no read timeout — bridge decides when done
                )
                resp.raise_for_status()
                if not resp.content:
                    log.warning("Bridge returned empty body (attempt %d/3), retrying…", _bridge_attempt + 1)
                    import time as _time2; _time2.sleep(2)
                    continue
                data = resp.json()
                if data.get("response"):
                    log.info(
                        "DesignAdvisor LLM bridge OK — %d chars (source=%s)",
                        len(data["response"]), data.get("source", "?"),
                    )
                    return data["response"]
                break  # got a body but no "response" key — fall through to SDK
        except Exception as e:
            log.info("DesignAdvisor LLM bridge unavailable (%s) — falling back to Anthropic API", e)

        # Anthropic SDK fallback
        try:
            import anthropic
        except ImportError as exc:
            raise RuntimeError(
                "Inkline intelligence requires the 'anthropic' package. "
                "Install it with: pip install inkline[intelligence]"
            ) from exc

        if not self.api_key:
            raise RuntimeError(
                "No LLM available: bridge unreachable and ANTHROPIC_API_KEY not set. "
                "Set ANTHROPIC_API_KEY or start the LLM bridge, or use mode='rules'."
            )

        client = anthropic.Anthropic(api_key=self.api_key)
        log.info(
            "DesignAdvisor Anthropic API (%s): %d sys / %d user chars",
            self.model, len(system_prompt), len(user_prompt),
        )
        response = client.messages.create(
            model=self.model,
            max_tokens=16000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return response.content[0].text

    @staticmethod
    def _suggest_template_for_audience(audience: str) -> str:
        """Return a slide template name suited to the stated audience.

        Only called when the caller has not already specified a template
        (i.e. template == "brand"). Keeps template auto-selection lightweight
        without an LLM call.
        """
        a = audience.lower()
        if any(k in a for k in ("bank", "finance", "investment", "equity", "debt", "credit")):
            return "banking"
        if any(k in a for k in ("board", "trustee", "governor", "director", "non-exec")):
            return "boardroom"
        if any(k in a for k in ("investor", "vc", "venture", "fund", "lp", "limited partner")):
            return "investor"
        if any(k in a for k in ("mckinsey", "consultant", "partner", "engagement manager")):
            return "consulting"
        if any(k in a for k in ("pitch", "startup", "founder", "seed", "series")):
            return "pitch"
        if any(k in a for k in ("executive", "c-suite", "ceo", "cfo", "coo", "cto", "svp")):
            return "executive"
        return "brand"  # No strong signal — keep brand default

    def design_deck(
        self,
        title: str,
        sections: list[dict[str, Any]],
        *,
        date: str = "",
        subtitle: str = "",
        contact: Optional[dict] = None,
        audience: str = "",
        goal: str = "",
        design_context: Optional["DesignContext"] = None,
        additional_guidance: str = "",
        reference_archetypes: Optional[list[str]] = None,
        brief: Optional[Any] = None,
    ) -> list[dict[str, Any]]:
        """Design a slide deck from structured content sections.

        Parameters
        ----------
        title : str
            Deck title.
        sections : list[dict]
            Content sections, each with ``type`` and data fields.

            Each section can include a ``"slide_mode"`` field to control how
            much creative freedom the LLM has:

            - ``"exact"`` — Section is a complete slide spec. The LLM does not
              touch it. Must include ``"slide_type"`` and ``"data"`` keys.
              Use this when you know exactly what the slide should look like.
            - ``"guided"`` — Section specifies constraints (e.g., ``slide_type``,
              some ``data`` fields). The LLM fills missing fields but MUST
              preserve everything the user provided. Use this when you want
              the LLM to polish presentation but not change substance.
            - ``"auto"`` (default) — Full LLM control. The LLM picks the best
              slide type and structures all data from the section content.

            If ``slide_mode`` is omitted, defaults to ``"auto"``.

        date : str
            Date string.
        subtitle : str
            Subtitle / tagline.
        contact : dict, optional
            Closing slide contact info.
        audience : str, optional
            Target audience (e.g., "PE fund CIOs", "board members").
        goal : str, optional
            Deck goal (e.g., "secure pre-seed investment", "inform board").
        additional_guidance : str, optional
            Free-form guidance the user wants the LLM to follow on top of the
            playbook rules.
        reference_archetypes : list[str], optional
            Archetype names from ``inkline.intelligence.template_catalog.ARCHETYPES``
            that the LLM should consider for this deck.

        Returns
        -------
        list[dict]
            List of slide specs ready for ``export_typst_slides()``.
        """
        # Phase 0.5: open learning session (fail-safe — never affects generation)
        _learning_cm = None   # the context manager object
        _learning_ctx = None  # the SessionContext yielded by __enter__
        try:
            from inkline.learning.session_context import generation_session as _gen_session
            _learning_cm = _gen_session(
                brand=self.brand,
                template=self.template,
                audience=audience,
                goal=goal,
                mode=self.mode,
            )
            _learning_ctx = _learning_cm.__enter__()
        except Exception as _learn_err:
            log.debug("DesignAdvisor: learning session skipped: %s", _learn_err)
            _learning_cm = None
            _learning_ctx = None

        # Partition sections by slide_mode
        exact_slides = []   # (original_index, slide_spec)
        llm_sections = []   # (original_index, section) — for auto + guided

        for i, section in enumerate(sections):
            mode = section.get("slide_mode", "auto")
            if mode == "exact":
                # Exact mode: section IS the slide spec — pass through directly
                stype = section.get("slide_type", "")
                data = section.get("data", {})
                if stype and stype in SLIDE_TYPES:
                    exact_slides.append((i, {"slide_type": stype, "data": data, "slide_mode": "exact"}))
                else:
                    log.warning(
                        "Section %d has slide_mode='exact' but invalid/missing "
                        "slide_type '%s' — falling back to auto", i, stype,
                    )
                    llm_sections.append((i, section))
            else:
                llm_sections.append((i, section))

        # If ALL sections are exact, no LLM call needed
        if not llm_sections:
            slides = [spec for _, spec in sorted(exact_slides)]
            # Add title + closing if not already present
            if not slides or slides[0]["slide_type"] != "title":
                slides.insert(0, {"slide_type": "title", "data": {
                    "company": title, "tagline": subtitle, "date": date,
                }})
            if contact and (not slides or slides[-1]["slide_type"] != "closing"):
                slides.append({"slide_type": "closing", "data": contact})
            return self._close_learning_session(_learning_cm, _learning_ctx, slides)

        # LLM mode: send auto + guided sections to LLM
        # Auto-suggest a template when the caller left it at the brand default
        # and provided an audience hint — keeps template selection out of the LLM
        # prompt while still producing audience-appropriate styling.
        if self.template == "brand" and audience:
            suggested = self._suggest_template_for_audience(audience)
            if suggested != "brand":
                log.info("DesignAdvisor: auto-selecting template '%s' for audience: %s",
                         suggested, audience)
                self.template = suggested

        if self.mode == "llm" and (self.llm_caller is not None or self.api_key):
            try:
                llm_only = [s for _, s in llm_sections]

                # 1.5: Make design_brief mandatory for decks with ≥5 sections
                if brief is None and len(sections) >= 5:
                    try:
                        from inkline.intelligence.design_brief import generate_brief
                        brief = generate_brief(
                            sections=sections,
                            goal=goal or "Board-level audience; goal: clear decision support.",
                            audience=audience or "Board-level audience",
                            title=title,
                        )
                        log.info("DesignAdvisor: auto-generated design brief for %d-section deck", len(sections))
                    except Exception as _brief_err:
                        log.info("DesignAdvisor: design brief generation skipped (%s)", _brief_err)

                llm_slides = self._design_deck_llm(
                    title, llm_only, date=date, subtitle=subtitle,
                    contact=contact, audience=audience, goal=goal,
                    design_context=design_context,
                    additional_guidance=additional_guidance,
                    reference_archetypes=reference_archetypes,
                    brief=brief,
                )

                # Merge: replace LLM-designed slides with exact ones at
                # their original positions. LLM output is sequential for
                # the auto/guided sections; exact slides are spliced in.
                if exact_slides:
                    llm_slides = self._merge_exact_slides(
                        llm_slides, exact_slides, llm_sections,
                    )

                # Post-process: enforce guided mode constraints
                llm_slides = self._enforce_guided_constraints(
                    llm_slides, sections,
                )

                # Inject per-slide source_section for narrative fidelity audit.
                # Match each non-structural slide to its best source section
                # by title word overlap so the visual auditor knows what the
                # slide was supposed to convey.
                _exempt = {"title", "closing", "section_divider"}
                for slide in llm_slides:
                    if slide.get("slide_type") in _exempt:
                        continue
                    if slide.get("data", {}).get("source_section"):
                        continue  # Already set (e.g. exact mode)
                    slide_words = set(
                        (slide.get("data", {}).get("title") or "").lower().split()
                    ) - {"the", "a", "an", "of", "and", "for", "in", "to", "with"}
                    if not slide_words:
                        continue
                    best_score, best_text = 0, ""
                    for sec in sections:
                        sec_words = set(sec.get("title", "").lower().split())
                        score = len(slide_words & sec_words)
                        if score > best_score:
                            best_score = score
                            best_text = sec.get("narrative", "")
                    if best_text:
                        slide.setdefault("data", {})["source_section"] = best_text[:2000]

                return self._close_learning_session(_learning_cm, _learning_ctx, llm_slides)
            except Exception as e:
                log.warning("LLM mode failed, falling back to rules: %s", e)

        # Fallback: rules-based (exact slides still honored)
        rules_sections = [s for _, s in llm_sections]
        rules_slides = self._design_deck_rules(
            title, rules_sections, date=date, subtitle=subtitle, contact=contact,
        )
        if exact_slides:
            rules_slides = self._merge_exact_slides(
                rules_slides, exact_slides, llm_sections,
            )
        return self._close_learning_session(_learning_cm, _learning_ctx, rules_slides)

    @staticmethod
    def _close_learning_session(cm, ctx, slides: list[dict]) -> list[dict]:
        """Record slides into the SessionContext, then close the context manager. Fail-safe.

        Parameters
        ----------
        cm : context manager object (from generation_session(...))
        ctx : SessionContext yielded by cm.__enter__()
        slides : list of slide spec dicts to record
        """
        if cm is None or ctx is None:
            return slides
        try:
            # Record slides so _persist_session can capture them on __exit__
            ctx.record_slides(slides)
            cm.__exit__(None, None, None)
        except Exception as _err:
            log.debug("DesignAdvisor: learning session close error: %s", _err)
        return slides

    @staticmethod
    def _merge_exact_slides(
        llm_slides: list[dict],
        exact_slides: list[tuple[int, dict]],
        llm_sections: list[tuple[int, dict]],
    ) -> list[dict]:
        """Splice exact slides into LLM output at their original positions.

        The LLM only saw auto/guided sections, so its output indices don't
        account for exact slides. We insert exact slides at the correct
        positions relative to the original section ordering.
        """
        # Build a mapping: original_index → slide_spec
        result_by_idx: dict[int, dict] = {}
        for orig_idx, spec in exact_slides:
            result_by_idx[orig_idx] = spec

        # LLM slides map to llm_sections in order (skip title/closing)
        llm_content = [s for s in llm_slides if s["slide_type"] not in ("title", "closing")]
        title_slide = next((s for s in llm_slides if s["slide_type"] == "title"), None)
        closing_slide = next((s for s in llm_slides if s["slide_type"] == "closing"), None)

        for i, (orig_idx, _) in enumerate(llm_sections):
            if i < len(llm_content):
                result_by_idx[orig_idx] = llm_content[i]

        # Reassemble in original order
        merged = []
        if title_slide:
            merged.append(title_slide)
        for idx in sorted(result_by_idx):
            merged.append(result_by_idx[idx])
        if closing_slide:
            merged.append(closing_slide)

        return merged

    @staticmethod
    def _enforce_guided_constraints(
        slides: list[dict],
        original_sections: list[dict],
    ) -> list[dict]:
        """For guided-mode sections, ensure user-specified fields are preserved.

        The LLM may have changed fields the user explicitly set. This method
        restores them from the original section.
        """
        # Map section titles to original sections for matching
        guided = {
            s.get("section", s.get("title", "")): s
            for s in original_sections
            if s.get("slide_mode") == "guided"
        }
        if not guided:
            return slides

        for slide in slides:
            data = slide.get("data", {})
            section_key = data.get("section", data.get("title", ""))

            orig = guided.get(section_key)
            if not orig:
                continue

            # Mark as guided so the visual auditor stores suggestions for HITL
            slide["slide_mode"] = "guided"

            # Restore user-specified slide_type if provided
            if "slide_type" in orig and orig["slide_type"] in SLIDE_TYPES:
                slide["slide_type"] = orig["slide_type"]

            # Restore user-specified data fields
            user_data = orig.get("data", {})
            for key, value in user_data.items():
                data[key] = value

        return slides

    # ==================================================================
    # LLM-DRIVEN MODE
    # ==================================================================

    def _design_deck_llm(
        self,
        title: str,
        sections: list[dict[str, Any]],
        *,
        date: str = "",
        subtitle: str = "",
        contact: Optional[dict] = None,
        audience: str = "",
        goal: str = "",
        design_context: Optional[Any] = None,
        additional_guidance: str = "",
        reference_archetypes: Optional[list[str]] = None,
        brief: Optional[Any] = None,
    ) -> list[dict[str, Any]]:
        """Use an LLM to design the optimal slide deck (two-phase approach).

        Phase 1 — Plan (fast, ~3K sys + ~6K user):
          LLM creates a deck outline: slide types, action titles, source refs.
          This is a small, fast call that fits comfortably within bridge timeout.

        Phase 2 — Per-slide design (full system prompt, one call per slide):
          Each slide is designed individually from its plan entry + source section.
          The full _build_system_prompt() is used (bridge caches it across calls).
          Slides are designed sequentially; parallelism can be toggled via
          the ``_parallel_slide_design`` flag if the bridge supports concurrency.

        Routing order (handled by ``_call_llm``):
          1. ``self.llm_caller`` — injected custom caller (test mocks, custom providers)
          2. LLM bridge at ``self.bridge_url`` — Claude Max subscription, no API spend
          3. Anthropic SDK using ``self.api_key`` / ``ANTHROPIC_API_KEY`` env var
        """
        # === PHASE 1: Plan deck structure ===
        log.info("DesignAdvisor Phase 1: planning deck structure (%d sections)...", len(sections))
        plan = self._plan_deck_llm(
            title, sections, goal=goal, audience=audience,
            additional_guidance=additional_guidance, brief=brief,
        )
        log.info("DesignAdvisor Phase 1: plan has %d slides", len(plan))
        for i, entry in enumerate(plan):
            log.info("  [%2d] %-22s — %s", i + 1,
                     entry.get("slide_type", "?"),
                     str(entry.get("title", ""))[:55])

        # === PHASE 1a: VFEP audit — reject plans with too many text layouts ===
        from inkline.intelligence.plan_auditor import audit_plan
        _MAX_AUDIT_RETRIES = 2
        for _audit_attempt in range(_MAX_AUDIT_RETRIES):
            audit = audit_plan(plan)
            if audit.passed:
                log.info("DesignAdvisor Phase 1a: VFEP audit passed "
                         "(T5=%d/%d, %.0f%%)", audit.t5_count, audit.content_count, audit.t5_ratio * 100)
                break
            log.warning(
                "DesignAdvisor Phase 1a: VFEP audit FAILED (attempt %d/%d) — "
                "T5=%.0f%%, violations=%d. Retrying planning with feedback.",
                _audit_attempt + 1, _MAX_AUDIT_RETRIES,
                audit.t5_ratio * 100, len(audit.consecutive_violations),
            )
            _vfep_guidance = (
                f"{additional_guidance}\n\nVFEP AUDIT FEEDBACK — MUST FIX BEFORE SUBMITTING:\n"
                f"{audit.feedback}"
            ).strip()
            plan = self._plan_deck_llm(
                title, sections, goal=goal, audience=audience,
                additional_guidance=_vfep_guidance, brief=brief,
            )
        else:
            # After retries, accept whatever we have (Archon still reviews next)
            audit = audit_plan(plan)
            log.warning(
                "DesignAdvisor Phase 1a: VFEP audit still failing after %d retries "
                "(T5=%.0f%%) — proceeding to Archon review.",
                _MAX_AUDIT_RETRIES, audit.t5_ratio * 100,
            )

        # === PHASE 1b: Archon reviews plan before any rendering ===
        # Text-only review: checks story arc, slide type fitness, exhibit
        # opportunities, coverage, and commercial viability.
        # Catches structural problems before spending credits on 20 slide calls.
        log.info("DesignAdvisor Phase 1b: Archon reviewing plan (text-only)...")
        plan = self._review_plan_llm(
            plan, title, sections,
            goal=goal, audience=audience,
            reference_archetypes=reference_archetypes,
        )
        log.info("DesignAdvisor Phase 1b: plan finalised at %d slides", len(plan))
        for i, entry in enumerate(plan):
            log.info("  [%2d] %-22s — %s", i + 1,
                     entry.get("slide_type", "?"),
                     str(entry.get("title", ""))[:55])

        # === PHASE 1.5: Generate visual brief (now that outline is real) ===
        visual_brief = None
        if brief or design_context:
            try:
                from inkline.intelligence.visual_direction import generate_visual_brief
                visual_brief = generate_visual_brief(
                    deck_outline=plan,
                    design_brief=brief,
                    brand=self.brand,
                    n8n_endpoint=getattr(self, "_n8n_endpoint", ""),
                    design_context=design_context,
                    bridge_url=self.bridge_url,
                    llm_caller=self.llm_caller,
                )
                if visual_brief and visual_brief.template != self.template:
                    self.template = visual_brief.template
                    log.info("DesignAdvisor: template override %s (visual direction)", self.template)

                # Inject background images into plan entries for cover + divider slides
                if visual_brief and visual_brief.background_paths:
                    for entry in plan:
                        slot = "cover" if entry.get("slide_type") == "title" else (
                               "divider" if entry.get("slide_type") == "section_divider" else None)
                        if slot and slot in visual_brief.background_paths:
                            entry["background_image"] = visual_brief.background_paths[slot]
                            entry["overlay_opacity"] = visual_brief.overlay_opacity

                log.info("DesignAdvisor Phase 1.5: visual brief ready (register=%s, template=%s)",
                         visual_brief.register if visual_brief else "unknown",
                         visual_brief.template if visual_brief else "unknown")
            except Exception as _vb_err:
                log.warning("DesignAdvisor Phase 1.5: visual brief generation failed (%s)", _vb_err)

        # === PHASE 2: Design each slide from its plan entry ===
        # Build source section lookup (1-based index, matching plan's source_index)
        section_lookup: dict[int, dict] = {i + 1: s for i, s in enumerate(sections)}

        # Deterministic slides never need an LLM call
        _DETERMINISTIC = {"title", "closing", "section_divider"}

        def _make_deterministic(entry: dict) -> dict:
            stype = entry.get("slide_type", "")
            if stype == "title":
                return {"slide_type": "title", "data": {
                    "title": title, "subtitle": subtitle, "date": date,
                }}
            elif stype == "closing":
                return {"slide_type": "closing", "data": contact or {}}
            elif stype == "section_divider":
                return {"slide_type": "section_divider", "data": {
                    "title": entry.get("title", ""),
                }}
            return {}  # Should not happen

        def _design_one(idx: int, entry: dict) -> tuple[int, dict]:
            stype = entry.get("slide_type", "content")
            if stype in _DETERMINISTIC:
                return (idx, _make_deterministic(entry))
            src_idx = entry.get("source_index", 0)
            source_section = section_lookup.get(src_idx, {}).get("narrative", "")
            slide = self._design_slide_from_plan(
                entry, source_section,
                title=title, date=date, subtitle=subtitle,
                contact=contact, audience=audience, goal=goal,
                reference_archetypes=reference_archetypes,
                visual_brief=visual_brief,
            )
            return (idx, slide)

        slides: list[dict] = [{}] * len(plan)

        # Sequential execution by default (bridge may not support concurrency).
        # Set _parallel_slide_design=True to use ThreadPoolExecutor(max_workers=3).
        if getattr(self, "_parallel_slide_design", False):
            from concurrent.futures import ThreadPoolExecutor, as_completed
            with ThreadPoolExecutor(max_workers=3) as pool:
                futures = {pool.submit(_design_one, i, e): i for i, e in enumerate(plan)}
                for future in as_completed(futures):
                    try:
                        idx, slide = future.result()
                        slides[idx] = slide
                        log.info("DesignAdvisor Phase 2: [%2d/%d] %s — %s",
                                 idx + 1, len(plan),
                                 slide.get("slide_type", "?"),
                                 str(slide.get("data", {}).get("title", ""))[:40])
                    except Exception as e:
                        plan_idx = futures[future]
                        log.warning("DesignAdvisor Phase 2: slide %d failed (%s), using fallback",
                                    plan_idx + 1, e)
                        ent = plan[plan_idx]
                        slides[plan_idx] = {"slide_type": "content", "data": {
                            "title": ent.get("title", f"Slide {plan_idx + 1}"),
                            "items": ent.get("key_points", []),
                        }}
        else:
            for i, entry in enumerate(plan):
                try:
                    _, slide = _design_one(i, entry)
                    slides[i] = slide
                    log.info("DesignAdvisor Phase 2: [%2d/%d] %s — %s",
                             i + 1, len(plan),
                             slide.get("slide_type", "?"),
                             str(slide.get("data", {}).get("title", ""))[:40])
                except Exception as e:
                    log.warning("DesignAdvisor Phase 2: slide %d failed (%s), using fallback",
                                i + 1, e)
                    slides[i] = {"slide_type": "content", "data": {
                        "title": entry.get("title", f"Slide {i + 1}"),
                        "items": entry.get("key_points", []),
                    }}

        # Validate slide types
        validated = []
        for slide in slides:
            if not isinstance(slide, dict) or not slide:
                continue
            stype = slide.get("slide_type", "")
            if stype not in SLIDE_TYPES:
                log.warning("Unknown slide type from LLM: %s, skipping", stype)
                continue
            if "data" not in slide:
                slide["data"] = {}
            validated.append(slide)

        if not validated:
            raise ValueError("LLM returned no valid slides")

        log.info("DesignAdvisor LLM (2-phase): designed %d slides for '%s'",
                 len(validated), title)
        return validated

    # ------------------------------------------------------------------
    # Phase 1 helpers — deck planning
    # ------------------------------------------------------------------

    def _build_plan_system_prompt(self) -> str:
        """System prompt for the deck planning phase (~5K chars).

        Gives the planner a working knowledge of slide types and when to use
        each — including chart types for visual exhibits. Design aesthetics are
        applied in Phase 2; the plan is then reviewed by the Archon before any
        slides are rendered.
        """
        return "\n".join([
            "You are a presentation architect working to the standard of the world's leading",
            "investment banks and consulting firms. Given structured content sections, produce an ordered slide plan",
            "that is information-dense, data-driven, and visually rich — every slide must tell a",
            "complete story with chart evidence, not just announce facts in text.",
            "",
            "═══════════════════════════════════════════════════════════════",
            "CORE PRINCIPLE — NUMBERS NEED CONTEXT",
            "═══════════════════════════════════════════════════════════════",
            "A slide showing '4 big numbers' is NOT information-dense. It is lazy.",
            "A metric only becomes an insight when shown alongside its trend, comparator,",
            "or decomposition. NEVER plan a slide that is only numbers — always pair",
            "every metric with a chart that proves, contextualises, or explains it.",
            "",
            "═══════════════════════════════════════════════════════════════",
            "VISUAL-FIRST EXHAUSTION PROTOCOL (VFEP)",
            "═══════════════════════════════════════════════════════════════",
            "Before assigning ANY slide type, work through this 5-tier cascade:",
            "",
            "  T1 — QUANTITATIVE: Does the section contain metrics, percentages, counts,",
            "       financial figures, or time-series data?",
            "       If yes → dashboard, chart_caption, chart, multi_chart, bar_chart, kpi_strip, stat",
            "",
            "  T2 — SEQUENCE / JOURNEY: Does the section describe steps, phases,",
            "       milestones, a timeline, or a before→after progression?",
            "       If yes → multi_chart with entity_flow/ladder panel, process_flow, timeline",
            "",
            "  T3 — CONTRAST / COMPARISON: Does the section juxtapose two or more",
            "       options, scenarios, states, or entities?",
            "       If yes → comparison, three_card, four_card",
            "",
            "  T4 — GROUPED CATEGORIES: Does the section list features, capabilities,",
            "       attributes, or items that can be grouped visually?",
            "       If yes → feature_grid, icon_stat, four_card, three_card, progress_bars",
            "",
            "  T5 — TEXT FALLBACK (LAST RESORT ONLY): Use split, content, or table ONLY",
            "       when T1–T4 genuinely do not apply. When you assign a T5 layout,",
            "       you MUST include this in the notes field:",
            "         vfep_justification: <one sentence explaining why T1-T4 were exhausted>",
            "",
            "HARD LIMITS:",
            "  - No more than 30% of non-structural slides may be T5 (split/content/table).",
            "  - No 3+ consecutive slides of the same slide_type.",
            "  - stat/kpi_strip MAY appear when metrics need no chart context (T1 fallback).",
            "  - timeline/process_flow MAY appear standalone when sequence data is rich.",
            "  - four_card/three_card/feature_grid are PREFERRED over split/content.",
            "",
            "NOTE: timeline / process content can also appear as ONE PANEL inside a multi_chart",
            "  alongside supporting data charts — that is often the best approach.",
            "",
            "═══════════════════════════════════════════════════════════════",
            "AVAILABLE SLIDE TYPES",
            "═══════════════════════════════════════════════════════════════",
            "STRUCTURAL (use as needed):",
            "  title           — opening cover slide",
            "  section_divider — full-bleed transition between major themes",
            "  closing         — final contact/CTA slide",
            "",
            "EXHIBIT TYPES (the primary tools — use these for everything else):",
            "  dashboard    — chart PNG (left 60%) + 3 headline stats + 3 insight bullets (right).",
            "                 Use when a section has ONE dominant chart plus supporting numbers.",
            "                 The stats panel replaces standalone stat/kpi_strip slides.",
            "",
            "  chart_caption — chart PNG (left 65%) + key takeaways panel with bullets (right).",
            "                  Use for any analytical finding where the chart IS the argument.",
            "                  The right panel carries the narrative; never use this as decoration.",
            "",
            "  chart         — full-bleed chart PNG (full width, no panel).",
            "                  Use ONLY when the chart is self-explanatory and needs no annotation.",
            "",
            "  multi_chart   — 2-6 chart PNGs arranged in a professional grid.",
            "                  Use whenever a section warrants multiple exhibits side-by-side.",
            "                  This is the primary vehicle for 'metrics + context' — each panel",
            "                  is a mini-chart (bar, sparkline, donut, gauge), NOT a number.",
            "    Layouts:",
            "      Single-row: equal_2(2), equal_3(3), equal_4(4),",
            "                  hero_left(2), hero_left_3(3), hero_right_3(3)",
            "      Two-row:    quad(4=2×2), top_bottom(1+2-3), three_top_wide(3+1=4), mosaic_5(2+3=5)",
            "      Asymmetric: left_stack(hero+2stacked=3), right_stack(2stacked+hero=3), six_grid(3×2=6)",
            "",
            "  comparison    — two-column head-to-head metrics table with delta column.",
            "                  Use for scenario/case comparison, not general metrics.",
            "",
            "  bar_chart     — native horizontal bar chart (no PNG needed; use for ranked lists).",
            "",
            "═══════════════════════════════════════════════════════════════",
            "CHART TYPES (specify in notes field)",
            "═══════════════════════════════════════════════════════════════",
            "  Standard:    line_chart, area_chart, waterfall, donut, pie,",
            "               stacked_bar, grouped_bar, heatmap, radar, gauge, scatter",
            "  Structural:  iceberg, funnel_ribbon, waffle, dual_donut,",
            "               pyramid_detailed, ladder, entity_flow,",
            "               divergent_bar, chart_row (3 small charts in one PNG)",
            "",
            "═══════════════════════════════════════════════════════════════",
            "DECISION RULES — section content → slide type",
            "═══════════════════════════════════════════════════════════════",
            "  Headline KPIs / summary metrics          → dashboard (chart + stats panel)",
            "                                             NOT stat or kpi_strip",
            "  Time-series data (production, revenue)   → chart_caption + line/area chart",
            "  Financial bridge / NPV walk              → chart_caption + waterfall chart",
            "  Portfolio / market-share breakdown       → chart_caption + donut or stacked_bar",
            "  3-6 metrics that all need trend context  → multi_chart (quad / mosaic_5)",
            "    e.g. 4 assets each with its own bar    → multi_chart quad",
            "    e.g. 5 KPIs each as gauge/sparkline    → multi_chart mosaic_5",
            "  Scenario A vs Scenario B                 → comparison or chart_caption + waterfall bridge",
            "  SWOT / quadrant analysis                 → multi_chart quad (4 styled panels)",
            "  Ranked list (e.g. NPV per well)          → bar_chart or chart_caption + grouped_bar",
            "  Data-rich section, multiple themes       → multi_chart (six_grid / three_top_wide)",
            "  Sequential milestones + supporting data  → multi_chart: one panel = entity_flow/ladder",
            "                                             chart showing the timeline; other panels = data",
            "  Process / workflow + metrics             → multi_chart: left panel = process diagram",
            "                                             (entity_flow chart), right panels = KPI charts",
            "  Qualitative / narrative section          → chart_caption with structural chart",
            "                                             (iceberg, ladder, entity_flow) to visualise",
            "                                             the point — no pure text slides",
            "",
            "═══════════════════════════════════════════════════════════════",
            "SECTION DIVIDER STRUCTURE — MAX 5, THEME-GROUPED",
            "═══════════════════════════════════════════════════════════════",
            "Do NOT add one section_divider per source section — that produces 10-15 dead slides.",
            "Instead, GROUP the source sections into 4-5 major themes and use ONE divider per theme.",
            "Typical theme groupings (adapt to content):",
            "",
            "  Deal / Investment context decks:",
            "    1. Executive Summary   — hook, headline KPIs, board-level verdict",
            "    2. Asset & Operations  — technical, reserves, production, development",
            "    3. Financial           — P&L, FCF, model, forecast, valuation",
            "    4. Risk & Governance   — SWOT, legal, regulatory, decommissioning, management",
            "    5. Conclusion          — recommendation, next steps, pre-bid actions",
            "",
            "  Company / strategy decks:",
            "    1. Market Opportunity  2. Business Model  3. Traction  4. Financials  5. Ask",
            "",
            "  Operational / review decks:",
            "    1. Performance Summary  2. Operations  3. Commercial  4. Risk  5. Outlook",
            "",
            "RULE: Never more than 5 section_dividers per deck.",
            "      Individual report sections fold into the nearest theme group — they do NOT",
            "      each get their own divider. The 'section' badge on each slide handles",
            "      fine-grained labelling; the divider announces a major gear-change only.",
            "",
            "═══════════════════════════════════════════════════════════════",
            "OPENER RULE — first two content slides after title",
            "═══════════════════════════════════════════════════════════════",
            "For the first two content slides (after the title slide), and for any section",
            "containing a single dominant insight (one key number, one key finding), use a",
            "single bold exhibit: stat, icon_stat with one dominant metric at display_xl,",
            "or a Tier 1B structural infographic. Do NOT use multi_chart for these slides.",
            "The opener must create visual impact — it sets the tone for the entire deck.",
            "",
            "═══════════════════════════════════════════════════════════════",
            "PLANNING RULES",
            "═══════════════════════════════════════════════════════════════",
            "- Start title (source_index=0), end closing (source_index=0)",
            "- Use 4-5 section_dividers maximum — group source sections into themes (see above)",
            "- Each source section → 1-2 slides; data-rich sections → 2 slides",
            "- Action titles: state the insight/conclusion, not just the topic",
            "  BAD: 'Financial Performance'   GOOD: '$8.5mm EBITDA on lean cost structure'",
            "- DO NOT invent facts — key_points must come from the source only",
            "- If pre-rendered chart PNGs are listed, reference them by filename in notes",
            "- DENSITY CHECK: before finalising each slide, ask: 'Does this slide show",
            "  data with context?' If the answer is no, upgrade it to dashboard or multi_chart.",
            "",
            "OUTPUT FORMAT — JSON array, each entry:",
            '  {"slide_type": "...", "title": "...", "source_index": N,',
            '   "key_points": ["..."], "notes": "..."}',
            "",
            "- source_index: 1-based (0 = deck metadata / title / closing)",
            "- key_points: 2-4 most important facts/claims from that source section",
            "- notes: specific design instruction for Phase 2 — name the chart type,",
            "  layout variant, and which data drives each panel",
            "",
            "Return JSON inside ```json ... ``` markers.",
        ])

    def _plan_deck_llm(
        self,
        title: str,
        sections: list[dict[str, Any]],
        *,
        goal: str = "",
        audience: str = "",
        additional_guidance: str = "",
        brief: Optional[Any] = None,
    ) -> list[dict[str, Any]]:
        """Phase 1: Ask LLM to outline the deck structure.

        Small, fast call (~3K sys + ~6K user). Returns list of plan entries.
        The plan is then reviewed by _review_plan_llm before per-slide design begins.
        If a DesignBrief is provided, its story arc and visual strategy are injected
        into the planning prompt for higher first-pass quality.
        """
        system_prompt = self._build_plan_system_prompt()

        parts = [f"Create a deck plan for: **{title}**"]
        if audience:
            parts.append(f"Audience: {audience}")
        if goal:
            parts.append(f"Goal: {goal}")

        # Inject design brief context if available
        if brief is not None:
            parts.append("\n## Design Brief (follow this strategy)")
            if getattr(brief, "deck_purpose", ""):
                parts.append(f"Purpose: {brief.deck_purpose}")
            if getattr(brief, "story_arc", ""):
                parts.append(f"Story arc: {brief.story_arc}")
            if getattr(brief, "visual_strategy", ""):
                parts.append(f"Visual strategy: {brief.visual_strategy}")
            if getattr(brief, "key_message", ""):
                parts.append(f"Key message: {brief.key_message}")
            if getattr(brief, "tone", ""):
                parts.append(f"Tone: {brief.tone}")
            if getattr(brief, "anti_goals", None):
                parts.append(f"Anti-goals (do NOT): {', '.join(brief.anti_goals)}")
            if getattr(brief, "section_briefs", None):
                parts.append("\nPer-section guidance:")
                for sb in brief.section_briefs:
                    title_str = sb.get("title", "")
                    exhibit = sb.get("suggested_exhibit", "")
                    intent = sb.get("intent", "")
                    parts.append(f"  - {title_str}: {intent} → suggest {exhibit}")
            parts.append("")

        if additional_guidance:
            parts.append(f"\nAdditional guidance: {additional_guidance.strip()}")

        # Inject chart inventory if pre-rendered charts are available
        _charts_dir = Path.home() / ".local/share/inkline/output/charts"
        if _charts_dir.exists():
            _chart_files = sorted(_charts_dir.glob("*.png"))
            if _chart_files:
                parts.append("\n## Pre-Rendered Charts Available")
                parts.append(
                    "These chart PNGs already exist — reference them by filename in your notes "
                    "instead of requesting new charts for the same data:"
                )
                for _cf in _chart_files:
                    parts.append(f"  {_cf.name}")
                parts.append("")

        parts.append("\n## Content Sections\n")
        for i, sec in enumerate(sections):
            sec_title = sec.get("title", sec.get("section", sec.get("type", "Untitled")))
            narrative = sec.get("narrative", "")
            # 400-char preview — enough for the planner to understand the section
            preview = narrative[:400] + ("..." if len(narrative) > 400 else "")
            parts.append(f"**Section {i + 1}: {sec_title}**")
            if preview:
                parts.append(preview)
            parts.append("")

        parts.append("\n## Three-Step Quality Check (run before returning JSON)")
        parts.append(
            "Before returning your slide plan, run this three-step check:\n"
            "1. TIER CHECK: Count slides by tier. If tier-5 (content) > 1, return to those"
            " slides and convert the weakest to tier 1 or 2.\n"
            "2. CONSOLIDATION CHECK: Find any two adjacent slides covering related data facets."
            " Can they share a multi_chart layout? If yes, consolidate.\n"
            "3. ACTION TITLE CHECK: Verify every slide title contains at least one of: a"
            " number/metric, a comparison word (more, fewer, higher, faster, lower), or a"
            " direction word (grew, declined, exceeded, fell, surpassed). If not, rewrite"
            " to state the insight.\n"
            "Only return your JSON after completing this check."
        )
        parts.append("\nOutput the deck plan as a JSON array inside ```json ... ``` markers.")
        user_prompt = "\n".join(parts)

        log.info("DesignAdvisor Phase 1 call: %d sys / %d user chars",
                 len(system_prompt), len(user_prompt))
        content = self._call_llm(system_prompt, user_prompt)
        return self._parse_plan_response(content)

    def _review_plan_llm(
        self,
        plan: list[dict[str, Any]],
        title: str,
        sections: list[dict[str, Any]],
        *,
        goal: str = "",
        audience: str = "",
        reference_archetypes: Optional[list[str]] = None,
    ) -> list[dict[str, Any]]:
        """Phase 1b: Archon review of the deck plan before any rendering.

        Uses the full design system prompt (bridge caches it from Phase 2 calls).
        Checks story arc, slide type choices, exhibit opportunities, and
        narrative flow. Returns the (potentially revised) plan.

        This is a text-only call — no PDF, no images, no vision. It's cheap and
        catches structural problems before spending API credits on per-slide design.
        """
        system_prompt = self._build_system_prompt(reference_archetypes=reference_archetypes)

        # Format the plan as a readable markdown outline for review
        plan_lines = [f"## Deck Plan: {title}"]
        if audience:
            plan_lines.append(f"**Audience:** {audience}")
        if goal:
            plan_lines.append(f"**Goal:** {goal}")
        plan_lines.append(f"**Slides planned:** {len(plan)}\n")

        for i, entry in enumerate(plan):
            stype = entry.get("slide_type", "?")
            slide_title = entry.get("title", "")
            src_idx = entry.get("source_index", 0)
            key_points = entry.get("key_points", [])
            notes = entry.get("notes", "")
            plan_lines.append(f"**[{i+1}] {stype}** — {slide_title}")
            if key_points:
                for kp in key_points:
                    plan_lines.append(f"  - {kp}")
            if notes:
                plan_lines.append(f"  _(hint: {notes})_")
            if src_idx > 0 and src_idx <= len(sections):
                sec = sections[src_idx - 1]
                sec_title = sec.get("title", "")
                plan_lines.append(f"  _(source: Section {src_idx}: {sec_title})_")
            plan_lines.append("")

        plan_md = "\n".join(plan_lines)

        # Include source section previews so Archon can judge fit
        source_lines = ["\n## Source Content Summaries\n"]
        for i, sec in enumerate(sections):
            sec_title = sec.get("title", sec.get("section", "Untitled"))
            narrative = sec.get("narrative", "")
            preview = narrative[:500] + ("..." if len(narrative) > 500 else "")
            source_lines.append(f"**Section {i+1}: {sec_title}**")
            if preview:
                source_lines.append(preview)
            source_lines.append("")

        # Inject available chart PNGs into the review prompt
        _archon_chart_note = ""
        _charts_dir = Path.home() / ".local/share/inkline/output/charts"
        if _charts_dir.exists():
            _chart_files = sorted(_charts_dir.glob("*.png"))
            if _chart_files:
                _names = ", ".join(cf.name for cf in _chart_files)
                _archon_chart_note = (
                    f"\n## Pre-rendered chart PNGs available\n"
                    f"These files can be used directly as image_path in chart_caption/chart slides:\n"
                    + "\n".join(f"  {cf.name}" for cf in _chart_files)
                    + "\nWhen upgrading a slide to chart_caption, specify the matching filename in notes.\n"
                )

        user_prompt = "\n".join([
            "You are reviewing a deck plan BEFORE any slides are rendered.",
            "Your job: evaluate the plan's story arc, slide type choices, and exhibit",
            "opportunities — then either approve it or revise it.",
            "",
            plan_md,
            "\n".join(source_lines),
            _archon_chart_note,
            "=" * 60,
            "REVIEW CRITERIA",
            "=" * 60,
            "",
            "1. STORY ARC & STRUCTURE",
            "   Does the deck flow logically from hook → evidence → ask?",
            "   Does it answer: 'why this deal / opportunity / decision, why now, why us?'",
            "   COUNT section_dividers. If more than 5, you MUST consolidate them.",
            "   Source sections should be GROUPED into 4-5 major themes — not given individual dividers.",
            "   Typical groupings: Executive Summary / Asset & Operations / Financial /",
            "   Risk & Governance / Conclusion. Merge any excess dividers into the nearest theme.",
            "",
            "2. SLIDE TYPE + CHART TYPE FIT — MANDATORY EXHIBIT QUOTA",
            "   COUNT the content slides (exclude title/closing/section_divider).",
            "   AT LEAST 70% must be chart_caption, chart, dashboard, or multi_chart.",
            "   stat, kpi_strip, icon_stat, timeline, process_flow are BANNED — low density.",
            "   If any of these appear, you MUST upgrade them:",
            "     stat/kpi_strip with financial data  → dashboard (chart + stats panel)",
            "     stat/kpi_strip with multiple KPIs   → multi_chart (each panel = mini-chart)",
            "     timeline / process_flow             → multi_chart (one panel = structural chart",
            "                                           e.g. entity_flow/ladder; other panels = data)",
            "     three_card / four_card / content     → chart_caption or multi_chart",
            "   Additional mandatory upgrades:",
            "   - Production/reserves over time → chart_caption + line/area chart",
            "   - FCF/revenue projections → chart_caption + use matching PNG from above",
            "   - Financial walk / bridge data → chart_caption + waterfall (not table)",
            "   - Market share / portfolio breakdown → chart_caption + donut or stacked_bar",
            "   - Risk matrix / 2D assessment → chart_caption + heatmap",
            "   - Funnel / pipeline conversion → chart_caption + funnel_ribbon",
            "   - Progress vs target → chart_caption + gauge or waffle",
            "   - Growth over time → chart_caption + line_chart or area_chart",
            "   - Multi-metric portfolio → dashboard (chart + 3 stats + bullets) OR multi_chart",
            "   - Side-by-side scenarios → comparison or chart_caption + waterfall bridge",
            "   - Milestone history → timeline",
            "   - Process / how-it-works → process_flow",
            "   When upgrading, set notes to specify chart_type AND PNG filename if available.",
            "",
            "3. COVERAGE — Are any critical source sections missing or under-served?",
            "   Does the plan weight emphasis toward the most commercially important points?",
            "",
            "4. VISUAL VARIETY — No 3+ consecutive text/content slides. Mix chart and",
            "   narrative layouts throughout the deck.",
            "",
            "5. COMMERCIAL VIABILITY — Would the audience leave knowing exactly what action",
            "   to take and why? Is the key ask/recommendation prominent?",
            "",
            "=" * 60,
            "OUTPUT FORMAT",
            "=" * 60,
            "",
            "Return a JSON object inside ```json ... ``` markers:",
            "",
            '{"verdict": "approved" | "revised",',
            ' "feedback": ["concise note about each change or observation"],',
            ' "revised_plan": [...]}',
            "",
            "- verdict 'approved': revised_plan is the original plan unchanged.",
            "- verdict 'revised': revised_plan is the improved plan.",
            "- feedback: 3-5 concise notes explaining changes or confirming quality.",
            "- DO NOT invent new facts. key_points must come from the source sections.",
            "- revised_plan entries follow the same schema: {slide_type, title,",
            "  source_index, key_points, notes}.",
        ])

        log.info("DesignAdvisor Phase 1b (plan review): %d sys / %d user chars",
                 len(system_prompt), len(user_prompt))
        content = self._call_llm(system_prompt, user_prompt)

        # Parse the review response
        json_str = content.strip()
        for fence in ("```json", "```"):
            if fence in content:
                try:
                    start = content.index(fence) + len(fence)
                    end = content.index("```", start)
                    json_str = content[start:end].strip()
                    break
                except ValueError:
                    pass

        if json_str and json_str[0] not in ("{", "["):
            for bracket in ("{", "["):
                idx = json_str.find(bracket)
                if idx != -1:
                    json_str = json_str[idx:]
                    break

        try:
            review = json.loads(json_str)
        except json.JSONDecodeError as e:
            log.warning("Plan review parse failed (%s) — using original plan", e)
            return plan

        # Graceful fallback if LLM returned wrong structure (e.g. a slide array)
        if not isinstance(review, dict):
            log.warning("Plan review returned unexpected type %s — using original plan",
                        type(review).__name__)
            return plan

        verdict = review.get("verdict", "approved")
        feedback = review.get("feedback", [])
        revised = review.get("revised_plan", plan)

        for note in feedback:
            log.info("Plan review feedback: %s", note)

        if verdict == "revised" and isinstance(revised, list) and revised:
            log.info("Plan review REVISED plan: %d → %d slides", len(plan), len(revised))
            return revised
        else:
            log.info("Plan review APPROVED plan (%d slides)", len(plan))
            return plan

    def _parse_plan_response(self, content: str) -> list[dict[str, Any]]:
        """Parse the planning LLM's JSON response into plan entries."""
        json_str = content.strip()
        if "```json" in content:
            try:
                start = content.index("```json") + 7
                end = content.index("```", start)
                json_str = content[start:end].strip()
            except ValueError:
                pass
        elif "```" in content:
            try:
                start = content.index("```") + 3
                end = content.index("```", start)
                json_str = content[start:end].strip()
            except ValueError:
                pass

        if json_str and json_str[0] not in ("[", "{"):
            for bracket in ("[", "{"):
                idx = json_str.find(bracket)
                if idx != -1:
                    json_str = json_str[idx:]
                    break

        try:
            plan = json.loads(json_str)
        except json.JSONDecodeError as e:
            log.error("Failed to parse plan response: %s\nRaw (first 500): %s", e, content[:500])
            raise

        if isinstance(plan, dict):
            plan = [plan]
        if not isinstance(plan, list):
            raise ValueError(f"Plan LLM returned unexpected type: {type(plan)}")
        return plan

    # ------------------------------------------------------------------
    # Phase 2 helpers — per-slide design
    # ------------------------------------------------------------------

    def _build_slide_design_prompt(
        self,
        plan_entry: dict[str, Any],
        source_section: str,
        *,
        title: str = "",
        date: str = "",
        subtitle: str = "",
        contact: Optional[dict] = None,
        audience: str = "",
        goal: str = "",
        visual_brief: Optional[Any] = None,
    ) -> str:
        """Build a focused per-slide user prompt from a plan entry."""
        stype = plan_entry.get("slide_type", "content")
        slide_title = plan_entry.get("title", "")
        key_points = plan_entry.get("key_points", [])
        notes = plan_entry.get("notes", "")

        parts = [
            f"Design ONE slide for the deck: **{title}**",
            f"Brand: {self.brand} | Template: {self.template}",
        ]
        if audience:
            parts.append(f"Audience: {audience}")
        if goal:
            parts.append(f"Deck goal: {goal}")

        parts += [
            "",
            "## Slide assignment",
            f"Planned type: {stype}",
            f"Planned title: {slide_title}",
        ]
        if key_points:
            parts.append("Key points to convey:")
            for kp in key_points:
                parts.append(f"  - {kp}")
        if notes:
            parts.append(f"Design hint: {notes}")

        if source_section:
            trunc = source_section[:2000]
            omitted = len(source_section) - len(trunc)
            parts += [
                "",
                "## Source content — extract all data, numbers, names, and claims from this:",
                trunc,
            ]
            if omitted > 0:
                parts.append(f"[...{omitted} chars omitted]")

        if stype == "title":
            parts += ["", "## Deck metadata",
                      f"Title: {title}", f"Subtitle: {subtitle}", f"Date: {date}"]
        elif stype == "closing" and contact:
            parts += ["", "## Contact info", json.dumps(contact, indent=2)]

        # For chart-type slides, inject available pre-rendered PNGs as naming hints only
        _chart_types = {"chart_caption", "chart", "dashboard", "multi_chart"}
        if stype in _chart_types:
            _charts_dir = Path.home() / ".local/share/inkline/output/charts"
            if _charts_dir.exists():
                _chart_files = sorted(_charts_dir.glob("*.png"))
                if _chart_files:
                    parts += [
                        "",
                        "## Previously rendered PNG filenames (naming reference only)",
                        "Use these as inspiration for image_path naming conventions.",
                        "You MUST still generate a chart_request for every visual slide —",
                        "these filenames are NOT permission to skip chart generation.",
                    ]
                    for _cf in _chart_files:
                        parts.append(f"  {_cf.name}")

        # Inject visual direction constraints if available
        if visual_brief:
            parts += [
                "",
                "## Visual Direction Constraints",
                f"Accent colour: {visual_brief.accent} — apply to ONE element only per slide.",
            ]
            slot = "cover" if plan_entry.get("slide_type") == "title" else (
                   "divider" if plan_entry.get("slide_type") == "section_divider" else None)
            if slot and slot in visual_brief.background_paths:
                parts.append(f"This slide has a full-bleed background image. Keep text minimal and high-contrast.")
            parts.append(f"Content density: {visual_brief.avg_density}")

        parts += [
            "",
            "## Output format",
            "Return ONLY a single slide spec as JSON:",
            '  {"slide_type": "...", "data": {...}}',
            "",
            "Rules:",
            "- Use action titles (state the conclusion, not the topic)",
            "- Base ALL data strictly on the source content above",
            "- DO NOT invent statistics, names, or metrics",
            "- If source is sparse, design a sparse-but-impactful slide",
            "- For ALL visual slide types (chart_caption/chart/dashboard/multi_chart):",
            "  you MUST include a chart_request with full data + design spec.",
            "  Set image_path to a descriptive filename (snake_case .png).",
            "  NEVER omit chart_request for a visual slide — it is mandatory.",
            "",
            "Return JSON inside ```json ... ``` markers.",
        ]
        return "\n".join(parts)

    # Regex patterns that look like internal financial-model variable names.
    # These sometimes leak from source documents into LLM-generated slide text.
    _VAR_NAME_RE = re.compile(
        r"\bv[A-Z][A-Z0-9_]{2,}_[A-Z]+\b"   # e.g. vMGMT_CASE, vCPR_CASE
        r"|_v[A-Z][A-Z0-9_]*\b"              # e.g. _vF, _vP2
        r"|\b[A-Z][A-Za-z0-9_]+_FM_v\d\b"   # e.g. ProjectAlpha_FM_v3
        r"|\w+\.xlsm\b|\w+\.xlsx\b",         # spreadsheet filenames
        re.ASCII,
    )
    _VAR_NAME_REPLACEMENTS: dict[str, str] = {
        "vMGMT_CASE": "Management Case",
        "vCPR_CASE": "CPR Case",
        "v2P_CASE": "2P Case",
        "v1P_CASE": "1P Case",
    }

    def _sanitise_slide_spec(self, spec: dict) -> dict:
        """Strip internal variable/file names from all string fields in a slide spec.

        The LLM occasionally copies token names like vMGMT_CASE directly from
        the source financial model into slide titles, labels, and values.
        This post-processor replaces known patterns with plain English.
        """
        def _clean(val):
            if not isinstance(val, str):
                return val
            for token, replacement in self._VAR_NAME_REPLACEMENTS.items():
                val = val.replace(token, replacement)
            # Strip any remaining matches of the general pattern
            val = self._VAR_NAME_RE.sub(
                lambda m: self._VAR_NAME_REPLACEMENTS.get(m.group(0), m.group(0)),
                val,
            )
            return val

        def _walk(obj):
            if isinstance(obj, dict):
                return {k: _walk(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [_walk(v) for v in obj]
            return _clean(obj)

        return _walk(spec)

    def _design_slide_from_plan(
        self,
        plan_entry: dict[str, Any],
        source_section: str,
        *,
        title: str = "",
        date: str = "",
        subtitle: str = "",
        contact: Optional[dict] = None,
        audience: str = "",
        goal: str = "",
        reference_archetypes: Optional[list[str]] = None,
        visual_brief: Optional[Any] = None,
    ) -> dict[str, Any]:
        """Phase 2: Design a single slide from its plan entry + source content.

        Uses the full _build_system_prompt() which is cached by the bridge
        across all per-slide calls in the same deck (same content hash).
        """
        system_prompt = self._build_system_prompt(
            reference_archetypes=reference_archetypes, visual_brief=visual_brief
        )
        user_prompt = self._build_slide_design_prompt(
            plan_entry, source_section,
            title=title, date=date, subtitle=subtitle,
            contact=contact, audience=audience, goal=goal,
            visual_brief=visual_brief,
        )

        content = self._call_llm(system_prompt, user_prompt)

        # Parse single slide (may be object {} or single-element array [{}])
        json_str = content.strip()
        if "```json" in content:
            try:
                start = content.index("```json") + 7
                end = content.index("```", start)
                json_str = content[start:end].strip()
            except ValueError:
                pass
        elif "```" in content:
            try:
                start = content.index("```") + 3
                end = content.index("```", start)
                json_str = content[start:end].strip()
            except ValueError:
                pass

        if json_str and json_str[0] not in ("[", "{"):
            for bracket in ("[", "{"):
                idx = json_str.find(bracket)
                if idx != -1:
                    json_str = json_str[idx:]
                    break

        try:
            parsed = json.loads(json_str)
        except json.JSONDecodeError as e:
            log.warning("Slide parse failed for '%s': %s — using content fallback",
                        plan_entry.get("title", "?"), e)
            return {"slide_type": "content", "data": {
                "title": plan_entry.get("title", ""),
                "items": plan_entry.get("key_points", []),
            }}

        # Unwrap single-element array
        if isinstance(parsed, list):
            parsed = parsed[0] if parsed else {}

        if not isinstance(parsed, dict):
            parsed = {}

        # Validate slide type; fall back to plan's type if LLM went off-piste
        stype = parsed.get("slide_type", "")
        if stype not in SLIDE_TYPES:
            fallback_type = plan_entry.get("slide_type", "content")
            if fallback_type not in SLIDE_TYPES:
                fallback_type = "content"
            log.warning("Slide '%s' returned unknown type '%s', using '%s'",
                        plan_entry.get("title", "?"), stype, fallback_type)
            parsed["slide_type"] = fallback_type

        if "data" not in parsed:
            parsed["data"] = {}

        # Embed source section so the Archon visual auditor can check narrative
        # fidelity without re-running the full source match (it's already here).
        _EXEMPT_SOURCE = {"title", "closing", "section_divider"}
        if source_section and parsed.get("slide_type") not in _EXEMPT_SOURCE:
            parsed["data"].setdefault("source_section", source_section[:2000])

        # Strip internal variable/file names that sometimes leak from source docs.
        parsed = self._sanitise_slide_spec(parsed)

        return parsed

    def _inject_decision_matrix(self) -> str:
        """Return a compact text block of active DM rules for injection into the system prompt."""
        try:
            from inkline.intelligence.aggregator import load_decision_matrix
            dm = load_decision_matrix()
            active_rules = [r for r in dm.get("rules", []) if r.get("status") == "active"]
            if not active_rules:
                return "(No active decision matrix rules loaded.)"
            lines = [
                "The table below shows proven (data_structure, message_type) → chart_type mappings.",
                "Use these as your primary guide. When your data+message pair matches a row,",
                "apply the chart_type AND the enforce parameters listed.",
                "",
                "data_structure | message_type | chart_type | enforce",
                "-" * 70,
            ]
            for r in active_rules:
                enforce_str = ", ".join(f"{k}={v}" for k, v in r.get("enforce", {}).items()) or "—"
                lines.append(
                    f"{r['data_structure']} | {r['message_type']} | {r['chart_type']} | {enforce_str}"
                )
            return "\n".join(lines)
        except Exception as e:
            log.debug("Decision matrix injection failed: %s", e)
            return "(Decision matrix unavailable.)"

    def _build_system_prompt(
        self,
        reference_archetypes: Optional[list[str]] = None,
        visual_brief: Optional[Any] = None,
    ) -> str:
        """Build the system prompt with playbook context.

        Uses tiered loading to keep the system prompt under ~30K chars:
        - slide_layouts: full text (layout rules are essential)
        - SLIDE_TYPE_GUIDE: full text (critical for JSON output format)
        - template_catalog, typography, color_theory: condensed summaries
        """
        from inkline.intelligence.playbooks import load_playbook, load_playbook_summary

        # Tiered playbook loading — all as summaries to keep total system prompt
        # under ~40K chars. SLIDE_TYPE_GUIDE + VISHWAKARMA already cover the
        # essential layout rules; playbooks add depth, not the primary source.
        CORE_PLAYBOOKS: list[str] = []
        SUMMARY_PLAYBOOKS = [
            "slide_layouts", "professional_exhibit_design",
            "template_catalog", "typography", "color_theory",
        ]

        from inkline.intelligence.vishwakarma import VISHWAKARMA_SYSTEM_PREAMBLE

        parts = [
            "You are Inkline's DesignAdvisor — an expert graphic designer and visual storyteller.",
            "You design compelling, professional slide decks that communicate information with maximum impact.",
            "",
            VISHWAKARMA_SYSTEM_PREAMBLE,
            "",
            "=" * 60,
            "PRIME DIRECTIVE: NEVER INVENT FACTS",
            "=" * 60,
            "",
            "You are NOT a copywriter. You are a designer.",
            "",
            "STRICT RULES:",
            "- USE ONLY the data, claims, numbers, names, percentages, and",
            "  narratives that are EXPLICITLY in the input sections.",
            "- DO NOT invent statistics. DO NOT make up customer counts, growth",
            "  rates, GitHub stars, contributor counts, ARR figures, or any other",
            "  quantitative claim that isn't in the input.",
            "- DO NOT add hypothetical examples ('teams like Acme...') unless they",
            "  are explicitly in the input.",
            "- If a section has an `illustrative=True` flag, the data is for",
            "  visual demonstration only — your slide MUST mark it as ILLUSTRATIVE",
            "  in the footnote/caption (e.g., 'Illustrative example — not real data').",
            "- If you need a chart and the input provides a chart_path, use that",
            "  path. Do NOT invent additional chart paths or describe charts that",
            "  weren't provided.",
            "",
            "Your job is to PICK LAYOUTS and STRUCTURE the provided facts —",
            "not to fill in plausible-sounding details. If a section is sparse,",
            "design a sparse-but-impactful slide. If you cannot honestly support",
            "a claim with the input data, OMIT it.",
            "",
            "Action titles are great. Hallucinated metrics are not.",
            "",
            "NAMING RULE: Never copy internal variable, file, or model names from",
            "the source material into slide text (e.g. vMGMT_CASE, vCPR_CASE, _vF,",
            "ProjectAlpha_FM_v3.xlsm). Use plain descriptive language instead",
            "(e.g. 'Management Case', 'CPR Case', 'Financial Model').",
            "",
            "",
            "Your job: given structured content sections, decide the BEST slide type and data layout",
            "for each section. You produce a JSON array of slide specs.",
            "",
            SLIDE_TYPE_GUIDE,
            "",
            "=" * 60,
            "ACTIVE DECISION MATRIX RULES",
            "=" * 60,
            "",
            self._inject_decision_matrix(),
            "",
            "=" * 60,
            "DESIGN KNOWLEDGE",
            "=" * 60,
            "",
        ]

        # Core playbooks: include full text
        for name in CORE_PLAYBOOKS:
            try:
                content = load_playbook(name)
                parts.append(f"## {name.replace('_', ' ').title()}")
                parts.append(content)
                parts.append("")
            except Exception as e:
                log.warning("Failed to load core playbook '%s': %s", name, e)

        # Summary playbooks: condensed to reduce token count
        # professional_exhibit_design gets 6K to capture exhibit-type rules;
        # others stay at 4K.
        SUMMARY_MAX = {"professional_exhibit_design": 6000}
        for name in SUMMARY_PLAYBOOKS:
            try:
                content = load_playbook_summary(name, max_chars=SUMMARY_MAX.get(name, 4000))
                parts.append(f"## {name.replace('_', ' ').title()} (summary)")
                parts.append(content)
                parts.append("")
            except Exception as e:
                log.warning("Failed to load summary playbook '%s': %s", name, e)

        # Include design.md style catalog (27 curated design systems)
        try:
            from inkline.intelligence.design_md_styles import get_playbook_text
            parts.append(get_playbook_text())
            parts.append("")
        except Exception:
            pass  # Non-blocking: design_md_styles is optional

        # Optional: inline structured archetype recipes the caller pinned
        if reference_archetypes:
            from inkline.intelligence.template_catalog import get_archetype_recipe
            parts.append("=" * 60)
            parts.append("PINNED ARCHETYPES")
            parts.append("=" * 60)
            parts.append("")
            parts.append(
                "The caller has pinned these archetype recipes — bias your slide "
                "selection toward these patterns where the data fits:"
            )
            parts.append("")
            for arch_name in reference_archetypes:
                try:
                    recipe = get_archetype_recipe(arch_name)
                except ValueError:
                    log.warning("Unknown pinned archetype '%s', skipping", arch_name)
                    continue
                parts.append(f"### {arch_name}: {recipe['name']}")
                parts.append(f"  best_for: {', '.join(recipe['best_for'])}")
                parts.append(f"  layout: {recipe['layout']}")
                parts.append(f"  palette_rule: {recipe['palette_rule']}")
                parts.append(f"  inkline_slide_type: {recipe['inkline_slide_type']}")
                parts.append(f"  n_items: {recipe['n_items']}")
                parts.append("")

        # Inject learned patterns for this brand
        try:
            from inkline.intelligence.pattern_memory import format_patterns_for_prompt
            pattern_text = format_patterns_for_prompt(self.brand)
            if pattern_text:
                parts.append("")
                parts.append(pattern_text)
        except Exception:
            pass

        # Inject visual direction if available (locked global visual decisions)
        if visual_brief:
            parts.append("")
            parts.append("=" * 60)
            parts.append("VISUAL DIRECTION")
            parts.append("=" * 60)
            parts.append(
                "These visual decisions are LOCKED for this deck. Apply them consistently "
                "in every slide design. These are global constraints from the Visual Direction Agent."
            )
            parts.append("")
            parts.append(visual_brief.to_json_for_prompt())
            parts.append("")

        return "\n".join(parts)

    # Maximum chars for a section's narrative field in the user prompt.
    # Bridge handles ~80K total (47K system + 33K user) within its 300s timeout.
    # With ~16 sections × 1200 chars avg + 8K overhead ≈ 27K user + 47K sys = 74K.
    MAX_NARRATIVE_CHARS = 1200

    def _build_user_prompt(
        self,
        title: str,
        sections: list[dict[str, Any]],
        *,
        date: str = "",
        subtitle: str = "",
        contact: Optional[dict] = None,
        audience: str = "",
        goal: str = "",
        additional_guidance: str = "",
    ) -> str:
        """Build the user prompt with content to design.

        Narratives are truncated at sentence boundaries to keep the total
        prompt size within the LLM bridge limit (~80K chars total).
        """
        parts = [
            f"Design a slide deck for: **{title}**",
        ]
        if subtitle:
            parts.append(f"Subtitle: {subtitle}")
        if date:
            parts.append(f"Date: {date}")
        if audience:
            parts.append(f"Target audience: {audience}")
        if goal:
            parts.append(f"Goal: {goal}")
        if additional_guidance:
            parts.append("")
            parts.append("## Additional guidance from the caller")
            parts.append("Apply this on top of the playbook rules:")
            parts.append(additional_guidance.strip())

        parts.append(f"\nBrand: {self.brand}")
        parts.append(f"Template style: {self.template}")

        parts.append("\n## Content Sections\n")
        parts.append("Each section below is content that needs to become one (or occasionally two) slides.")
        parts.append("Decide the best slide_type for each, choose action titles, and structure the data.\n")
        parts.append("SECTION MODES:")
        parts.append("- `auto` (default): You have full creative control over slide_type and data.")
        parts.append("- `guided`: The user has specified certain fields (e.g., slide_type, some data")
        parts.append("  fields like rows, cards, title). You MUST PRESERVE those fields exactly as")
        parts.append("  provided. Fill in any MISSING fields (e.g., footnote, highlight_index) and")
        parts.append("  polish the presentation, but DO NOT change user-specified content.")
        parts.append("  If the user specifies `slide_type: table` with 8 rows, output a table with 8 rows.\n")

        for i, section in enumerate(sections):
            slide_mode = section.get("slide_mode", "auto")
            mode_tag = f" [MODE: {slide_mode.upper()}]" if slide_mode != "auto" else ""
            parts.append(f"### Section {i+1}: {section.get('section', section.get('type', section.get('title', 'Untitled')))}{mode_tag}")
            parts.append(f"Original title: {section.get('title', '')}")

            # Truncate long narratives to keep user prompt within bridge limits.
            # Guided sections are never truncated — user-specified content must be preserved.
            sec_for_prompt = dict(section)
            if slide_mode == "auto":
                narrative = sec_for_prompt.get("narrative", "")
                if len(narrative) > self.MAX_NARRATIVE_CHARS:
                    # Cut at sentence boundary nearest to the limit
                    trunc = narrative[:self.MAX_NARRATIVE_CHARS]
                    # Find last sentence-ending character
                    for end_char in ("\n\n", ".\n", ". ", ".\t"):
                        idx = trunc.rfind(end_char)
                        if idx > int(self.MAX_NARRATIVE_CHARS * 0.6):
                            trunc = trunc[:idx + len(end_char)].rstrip()
                            break
                    omitted_pct = int((len(narrative) - len(trunc)) / len(narrative) * 100)
                    sec_for_prompt["narrative"] = trunc + f"\n[...{omitted_pct}% omitted — key data above is sufficient for slide design]"

            parts.append(f"```json\n{json.dumps(sec_for_prompt, indent=2, default=str)}\n```\n")

        if contact:
            parts.append(f"### Closing Contact\n```json\n{json.dumps(contact, indent=2)}\n```\n")

        parts.append("## Output Format")
        parts.append("")
        parts.append("Return ONLY a JSON array of slide specs. Each slide spec has:")
        parts.append('  {"slide_type": "...", "data": {...}}')
        parts.append("")
        parts.append("Start with a title slide and end with a closing slide.")
        parts.append("Use action titles throughout (state the conclusion, not the topic).")
        parts.append("Ensure visual variety — vary slide types across the deck.")
        parts.append("For three_card slides, set highlight_index to accent the most impactful card.")
        parts.append("For split slides, put the key message on the right (accent panel).")
        parts.append("")
        parts.append("Return the JSON array inside ```json ... ``` markers.")

        return "\n".join(parts)

    def _parse_llm_response(
        self,
        content: str,
        title: str,
        date: str,
        subtitle: str,
        contact: Optional[dict],
    ) -> list[dict[str, Any]]:
        """Parse the LLM's JSON response into slide specs."""
        # Extract JSON — handle fenced code blocks OR bare JSON array/object
        json_str = content.strip()
        if "```json" in content:
            try:
                start = content.index("```json") + 7
                end = content.index("```", start)
                json_str = content[start:end].strip()
            except ValueError:
                pass
        elif "```" in content:
            try:
                start = content.index("```") + 3
                end = content.index("```", start)
                json_str = content[start:end].strip()
            except ValueError:
                pass

        # If still not starting with [ or {, try to find the first array/object
        if json_str and json_str[0] not in ("[", "{"):
            for bracket in ("[", "{"):
                idx = json_str.find(bracket)
                if idx != -1:
                    json_str = json_str[idx:]
                    break

        try:
            slides = json.loads(json_str)
        except json.JSONDecodeError as e:
            log.error("Failed to parse LLM response as JSON: %s\nRaw response (first 500): %s",
                      e, content[:500])
            raise

        # Validate slide types
        validated = []
        for slide in slides:
            if not isinstance(slide, dict):
                continue
            stype = slide.get("slide_type", "")
            if stype not in SLIDE_TYPES:
                log.warning("Unknown slide type from LLM: %s, skipping", stype)
                continue
            if "data" not in slide:
                slide["data"] = {}
            validated.append(slide)

        if not validated:
            raise ValueError("LLM returned no valid slides")

        return validated

    # ==================================================================
    # TWO-AGENT DESIGN DIALOGUE — Revision from Auditor feedback
    # ==================================================================

    def revise_slides_from_review(
        self,
        slides: list[dict[str, Any]],
        review_findings: list,
        original_sections: Optional[list[dict[str, Any]]] = None,
    ) -> list[dict[str, Any]]:
        """Receive Visual Auditor's review and revise slides accordingly.

        For each finding:
        - If Auditor proposes a redesign: evaluate it, accept or modify
        - If Auditor flags a mechanical issue: apply the fix
        - If Auditor makes a subjective suggestion: use LLM to decide

        Parameters
        ----------
        slides : list[dict]
            Current slide specs.
        review_findings : list
            Auditor findings (AuditWarning objects or dicts with
            severity, category, message, proposed_redesign).
        original_sections : list[dict], optional
            Original section data for context.

        Returns
        -------
        list[dict]
            Revised slide specs.
        """
        # Separate findings with proposed redesigns from text-only findings
        redesign_proposals = []
        other_findings = []

        for finding in review_findings:
            if hasattr(finding, "severity"):
                severity = finding.severity
                msg = finding.message
                proposed = getattr(finding, "proposed_redesign", None)
                slide_idx = getattr(finding, "slide_index", -1)
            elif isinstance(finding, dict):
                severity = finding.get("severity", "info")
                msg = finding.get("message", "")
                proposed = finding.get("proposed_redesign")
                slide_idx = finding.get("slide_index", -1)
            else:
                continue

            if severity not in ("error", "warn"):
                continue

            if proposed and isinstance(proposed, dict) and proposed.get("slide_type"):
                redesign_proposals.append({
                    "slide_index": slide_idx,
                    "proposed": proposed,
                    "reason": msg,
                })
            else:
                other_findings.append({
                    "slide_index": slide_idx,
                    "message": msg,
                    "severity": severity,
                })

        if not redesign_proposals and not other_findings:
            return slides

        # Authority model based on slide_mode:
        #
        # ERRORS (clipping, overflow, missing content, truncation):
        #   → Always fix, even on exact/guided slides.
        #     These are mechanical failures that break the user's intent.
        #
        # DESIGN SUGGESTIONS (layout_change, infographic, whitespace):
        #   → Auto-apply on auto slides
        #   → Store for HITL on exact/guided slides
        #
        modified = list(slides)
        accepted_count = 0
        protected_indices = {
            i for i, s in enumerate(slides)
            if s.get("slide_mode") in ("exact", "guided")
        }
        hitl_suggestions: list[dict] = []

        for proposal in redesign_proposals:
            idx = proposal["slide_index"] - 1  # Convert 1-based to 0-based
            if idx in protected_indices:
                # Design redesigns on protected slides → HITL only
                hitl_suggestions.append({
                    "slide_index": idx + 1,
                    "current_type": modified[idx].get("slide_type", ""),
                    "proposed_type": proposal["proposed"].get("slide_type", ""),
                    "reason": proposal["reason"],
                    "proposed_redesign": proposal["proposed"],
                    "status": "pending_review",
                })
                log.info("Suggestion stored for HITL: slide %d (%s → %s)",
                         idx + 1, modified[idx].get("slide_type", ""),
                         proposal["proposed"].get("slide_type", ""))
                continue  # Don't auto-apply
            if 0 <= idx < len(modified):
                proposed = proposal["proposed"]
                old_type = modified[idx].get("slide_type", "")
                new_type = proposed.get("slide_type", "")

                if new_type in SLIDE_TYPES:
                    modified[idx] = {
                        "slide_type": new_type,
                        "data": proposed.get("data", modified[idx].get("data", {})),
                    }
                    accepted_count += 1
                    log.info(
                        "Design revision: slide %d %s → %s (%s)",
                        idx + 1, old_type, new_type, proposal["reason"][:50],
                    )

                    # Record in pattern memory
                    try:
                        from inkline.intelligence.pattern_memory import record_accepted_redesign
                        record_accepted_redesign(
                            self.brand, old_type, new_type, proposal["reason"][:100],
                        )
                    except Exception:
                        pass

        # Split non-redesign findings by severity:
        # - ERRORS on protected slides → still fix (mechanical failures)
        # - WARNINGS on protected slides → store for HITL
        # - Everything on auto slides → fix
        fixable_findings = []
        for f in other_findings:
            idx = f["slide_index"] - 1
            is_protected = idx in protected_indices
            is_error = f["severity"] == "error"

            if not is_protected:
                # Auto slides: fix everything
                fixable_findings.append(f)
            elif is_error:
                # Protected slide with error: still fix (broken = not respecting intent)
                fixable_findings.append(f)
                log.info("Fixing error on protected slide %d: %s", f["slide_index"], f["message"][:60])
            else:
                # Protected slide with warning: HITL suggestion
                hitl_suggestions.append({
                    "slide_index": f["slide_index"],
                    "message": f["message"],
                    "severity": f["severity"],
                    "status": "pending_review",
                })

        if fixable_findings and (self.llm_caller is not None or self.api_key):
            try:
                modified = self._revise_via_llm(modified, fixable_findings, original_sections)
            except Exception as e:
                log.warning("LLM revision failed: %s", e)

        # Save HITL suggestions to file
        if hitl_suggestions:
            self._save_suggestions(hitl_suggestions)

        if accepted_count:
            log.info("Design dialogue: accepted %d proposals, %d stored for HITL",
                     accepted_count, len(hitl_suggestions))

        return modified

    def _save_suggestions(self, suggestions: list[dict]) -> None:
        """Save HITL suggestions to suggestions.json alongside the output."""
        import os
        suggestions_path = Path(os.environ.get(
            "INKLINE_SUGGESTIONS_PATH",
            Path.home() / ".config" / "inkline" / "suggestions.json",
        ))
        # Append to existing suggestions
        existing = []
        if suggestions_path.exists():
            try:
                existing = json.loads(suggestions_path.read_text(encoding="utf-8"))
            except Exception:
                existing = []

        existing.extend(suggestions)
        suggestions_path.write_text(
            json.dumps(existing, indent=2, default=str, ensure_ascii=False),
            encoding="utf-8",
        )
        log.info("Saved %d HITL suggestions to %s", len(suggestions), suggestions_path)

    def _revise_via_llm(
        self,
        slides: list[dict[str, Any]],
        findings: list[dict],
        original_sections: Optional[list[dict[str, Any]]] = None,
    ) -> list[dict[str, Any]]:
        """Revise ONLY the specific slides flagged by the auditor.

        Sends only affected slides to the LLM, then splices results
        back into the original list. Unflagged slides are never touched.
        """
        # Identify which slides are flagged (0-based indices)
        flagged_indices = set()
        for f in findings:
            idx = f["slide_index"] - 1  # Convert 1-based to 0-based
            if 0 <= idx < len(slides):
                flagged_indices.add(idx)

        if not flagged_indices:
            return slides

        # Extract only the flagged slides
        flagged_slides = [(i, slides[i]) for i in sorted(flagged_indices)]

        system_prompt = self._build_system_prompt()

        # Check if any findings are overflow-related — require stricter constraints
        has_overflow = any("overflow" in f.get("message", "").lower() for f in findings)

        parts = [
            "Fix ONLY the specific issues listed below. Return the revised slides as JSON.",
            "DO NOT change company names, numbers, or factual data.",
            "DO NOT add new image_path references.",
            "Only adjust layout, text formatting, or slide_type if needed.",
        ]
        if has_overflow:
            parts += [
                "",
                "CRITICAL OVERFLOW CONSTRAINT:",
                "- Each slide MUST fit on exactly ONE page. Overflow onto a second page is a hard failure.",
                "- To fix overflow: reduce items, shorten text, or switch to a SIMPLER slide type.",
                "- SAFE types that reliably fit: content, split, three_card, stat, icon_stat.",
                "- AVOID or DOWNGRADE: feature_grid, dashboard, comparison, four_card, table with many rows.",
                "- Do NOT switch to a denser slide type. If unsure, use 'content' with bullet points.",
            ]
        parts += [
            "",
            "Issues to fix:\n",
        ]

        for f in findings:
            idx = f["slide_index"] - 1
            if idx in flagged_indices:
                parts.append(f"- Slide {f['slide_index']} [{f['severity']}]: {f['message']}")

        parts.append(f"\nSlides to revise ({len(flagged_slides)} of {len(slides)}):")
        for i, s in flagged_slides:
            parts.append(f"\n// Slide {i+1}:")
            parts.append(json.dumps(s, indent=2, default=str)[:1500])

        parts.append("\nReturn ONLY the revised slides as a JSON array (same count as above).")
        parts.append("Return inside ```json ... ``` markers.")

        user_prompt = "\n".join(parts)

        try:
            content = self._call_llm(system_prompt, user_prompt)
            revised = self._parse_llm_response(content, "", "", "", None)

            # Splice revised slides back into the original list
            if len(revised) == len(flagged_slides):
                result = list(slides)
                for (orig_idx, _), new_slide in zip(flagged_slides, revised):
                    result[orig_idx] = new_slide
                return result
        except Exception as e:
            log.warning("LLM slide revision failed: %s", e)

        return slides

    # ==================================================================
    # RULES-BASED MODE (fallback)
    # ==================================================================

    def _design_deck_rules(
        self,
        title: str,
        sections: list[dict[str, Any]],
        *,
        date: str = "",
        subtitle: str = "",
        contact: Optional[dict] = None,
    ) -> list[dict[str, Any]]:
        """Rules-based deck design (no API calls)."""
        from inkline.intelligence.content_analyzer import analyze_content
        from inkline.intelligence.layout_selector import plan_deck_flow

        analyses = [analyze_content(s) for s in sections]
        layouts = plan_deck_flow(analyses)

        slides = []

        # Title slide
        slides.append({
            "slide_type": "title",
            "data": {
                "company": title,
                "tagline": subtitle,
                "date": date,
                "left_footer": "",
            },
        })

        # Content slides
        for section, analysis, layout in zip(sections, analyses, layouts):
            slide = self._section_to_slide(section, analysis, layout)
            if slide:
                slides.append(slide)

        # Closing slide
        if contact:
            slides.append({
                "slide_type": "closing",
                "data": contact,
            })

        log.info(
            "DesignAdvisor rules: planned %d slides for '%s'",
            len(slides), title,
        )
        return slides

    def design_document(
        self,
        markdown: str = "",
        *,
        title: str = "",
        subtitle: str = "",
        date: str = "",
        author: str = "",
        exhibits: Optional[list[dict]] = None,
    ) -> dict:
        """Design a document layout from markdown and optional exhibits."""
        return {
            "markdown": markdown,
            "title": title,
            "subtitle": subtitle,
            "date": date,
            "author": author,
            "brand": self.brand,
            "exhibits": exhibits or [],
        }

    # -- Rules-mode slide builders -----------------------------------------

    def _section_to_slide(self, section: dict, analysis: Any, layout: Any) -> dict | None:
        section_label = section.get("section", section.get("type", "").replace("_", " ").title())
        section_title = section.get("title", "")
        slide_type = layout.slide_type

        builders = {
            "content": self._build_content_slide,
            "three_card": lambda s, l, t: self._build_card_slide(s, l, t, 3, layout.highlight_index),
            "four_card": lambda s, l, t: self._build_card_slide(s, l, t, 4, layout.highlight_index),
            "feature_grid": lambda s, l, t: self._build_card_slide(s, l, t, 6, -1),
            "stat": self._build_stat_slide,
            "kpi_strip": self._build_kpi_slide,
            "table": self._build_table_slide,
            "split": self._build_split_slide,
            "bar_chart": self._build_bar_chart_slide,
            "chart": self._build_chart_slide,
            "timeline": self._build_timeline_slide,
        }
        builder = builders.get(slide_type, self._build_content_slide)
        return builder(section, section_label, section_title)

    def _build_content_slide(self, section: dict, label: str, title: str) -> dict:
        items = section.get("items", [])
        # Normalize dict items to strings
        if items and isinstance(items[0], dict):
            items = self._dict_items_to_strings(items)
        if not items and section.get("cards"):
            items = [f"*{c.get('title', '')}* -- {c.get('body', '')}" for c in section["cards"]]
        if not items and section.get("left"):
            items = section["left"].get("items", [])
            items += section.get("right", {}).get("items", [])
        if not items and section.get("narrative"):
            sentences = [s.strip() for s in section["narrative"].replace("\n", " ").split(".") if s.strip()]
            items = [f"{s}." for s in sentences[:6]]
        return {"slide_type": "content", "data": {"section": label, "title": title or label, "items": items, "footnote": section.get("footnote", "")}}

    def _build_card_slide(self, section: dict, label: str, title: str, n: int, highlight: int) -> dict:
        cards = section.get("cards", [])
        if not cards and section.get("items"):
            raw = section["items"]
            if raw and isinstance(raw[0], dict):
                # Dict items — extract title/body from known key patterns
                cards = self._dict_items_to_cards(raw[:n])
            else:
                cards = [{"title": item, "body": ""} for item in raw[:n]]
        if not cards and section.get("metrics"):
            cards = [{"title": k, "body": str(v)} for k, v in list(section["metrics"].items())[:n]]
        # Map n to slide type
        if n <= 3:
            slide_type = "three_card"
        elif n == 4:
            slide_type = "four_card"
        else:
            slide_type = "feature_grid"
        data: dict[str, Any] = {"section": label, "title": title or label, "cards": cards[:n], "footnote": section.get("footnote", "")}
        if highlight >= 0:
            data["highlight_index"] = highlight
        return {"slide_type": slide_type, "data": data}

    def _build_stat_slide(self, section: dict, label: str, title: str) -> dict:
        metrics = section.get("metrics", {})
        stats = [{"value": str(v), "label": k, "desc": ""} for k, v in list(metrics.items())[:4]]
        return {"slide_type": "stat", "data": {"section": label, "title": title or label, "stats": stats}}

    def _build_kpi_slide(self, section: dict, label: str, title: str) -> dict:
        metrics = section.get("metrics", {})
        kpis = [{"value": str(v), "label": k, "highlight": i == 0} for i, (k, v) in enumerate(list(metrics.items())[:5])]
        return {"slide_type": "kpi_strip", "data": {"section": label, "title": title or label, "kpis": kpis, "footnote": section.get("footnote", "")}}

    def _build_table_slide(self, section: dict, label: str, title: str) -> dict:
        table_data = section.get("table_data", {})
        return {"slide_type": "table", "data": {"section": label, "title": title or label, "headers": table_data.get("headers", []), "rows": table_data.get("rows", []), "footnote": section.get("footnote", "")}}

    def _build_split_slide(self, section: dict, label: str, title: str) -> dict:
        left = section.get("left", {})
        right = section.get("right", {})
        if not left and section.get("cards"):
            cards = section["cards"]
            mid = len(cards) // 2
            left = {"title": cards[0].get("title", ""), "items": [c.get("body", "") for c in cards[:mid]]}
            right = {"title": cards[mid].get("title", "") if mid < len(cards) else "", "items": [c.get("body", "") for c in cards[mid:]]}
        if not left and section.get("narrative"):
            words = section["narrative"].split()
            mid = len(words) // 2
            left = {"title": "Overview", "items": [" ".join(words[:mid])]}
            right = {"title": "Details", "items": [" ".join(words[mid:])]}
        return {"slide_type": "split", "data": {"section": label, "title": title or label, "left_title": left.get("title", ""), "left_items": left.get("items", []), "right_title": right.get("title", ""), "right_items": right.get("items", [])}}

    def _build_bar_chart_slide(self, section: dict, label: str, title: str) -> dict:
        items = section.get("items", [])
        values = section.get("values", [])
        if not items or not values:
            if section.get("table_data"):
                return self._build_table_slide(section, label, title)
            return self._build_content_slide(section, label, title)
        max_val = max(values) if values else 1
        bars = [{"label": item, "value": str(val), "pct": round(val / max_val * 100)} for item, val in zip(items, values)]
        return {"slide_type": "bar_chart", "data": {"section": label, "title": title or label, "bars": bars, "footnote": section.get("footnote", "")}}

    def _build_chart_slide(self, section: dict, label: str, title: str) -> dict:
        return {"slide_type": "chart", "data": {"section": label, "title": title or label, "image_path": section.get("image_path", ""), "footnote": section.get("footnote", "")}}

    def _build_timeline_slide(self, section: dict, label: str, title: str) -> dict:
        """Build a timeline slide from dict items with date/label keys."""
        items = section.get("items", [])
        milestones = []
        for item in items:
            if isinstance(item, dict):
                date = item.get("date") or item.get("timing") or item.get("year") or ""
                lbl = item.get("label") or item.get("name") or item.get("title") or ""
                desc = item.get("description") or item.get("body") or item.get("detail") or ""
                milestones.append({"date": str(date), "label": str(lbl), "description": str(desc)})
            else:
                milestones.append({"date": "", "label": str(item), "description": ""})
        return {"slide_type": "timeline", "data": {"section": label, "title": title or label, "milestones": milestones, "footnote": section.get("footnote", "")}}

    @staticmethod
    def _dict_items_to_cards(items: list) -> list:
        """Convert a list of dict items to card dicts with title/body keys."""
        cards = []
        for item in items:
            if not isinstance(item, dict):
                cards.append({"title": str(item), "body": ""})
                continue
            card_title = item.get("title") or item.get("name") or item.get("well") or item.get("action") or item.get("risk") or ""
            card_body = item.get("body") or item.get("detail") or item.get("value") or item.get("status") or ""
            severity = item.get("severity") or item.get("priority") or ""
            if severity and not card_body:
                card_body = f"Severity: {severity}"
            cards.append({"title": str(card_title), "body": str(card_body)})
        return cards

    @staticmethod
    def _dict_items_to_strings(items: list) -> list:
        """Convert a list of dict items to display strings."""
        result = []
        for item in items:
            if isinstance(item, str):
                result.append(item)
            elif isinstance(item, dict):
                name = item.get("title") or item.get("name") or item.get("well") or item.get("action") or item.get("risk") or ""
                detail = item.get("body") or item.get("detail") or item.get("value") or item.get("status") or ""
                severity = item.get("severity") or item.get("priority") or ""
                if name and detail:
                    result.append(f"{name} — {detail}")
                elif name and severity:
                    result.append(f"{name} [{severity}]")
                elif name:
                    result.append(name)
                else:
                    result.append("; ".join(f"{k}: {v}" for k, v in item.items()))
            else:
                result.append(str(item))
        return result
