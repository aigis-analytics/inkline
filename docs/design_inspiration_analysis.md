# Design Inspiration Analysis: Launchpad & Pareto
## Exhibit Patterns, Visual Strategies, and Inkline Deployment Specs

---

## Overview

This document catalogues every significant visual design strategy and bespoke exhibit type
from two reference decks:

- **Launchpad** — `Launchpad-Brochure-and-Fact-Sheet-March-2026.pdf`
  A3 landscape brochure (1191 × 842 pt). Property investment marketing document.
  Brand: dark forest green `#29433A` + burnt orange `#F57821` + soft mint `#C9E8DD`

- **Pareto** — `20260210_Pareto Securitie_Datacenter financing_vF.pdf`
  Widescreen landscape (780 × 540 pt). Investment bank pitch book. 
  Brand: deep navy `#004268` + magenta accent `#DE0080` + steel blue `#82B0BF` + light blue-grey `#E6F0F2`

Each pattern is described with: what it does, what data it's best for, and what would be
required to deploy it inside Inkline.

---

## 1. CROSS-CUTTING DESIGN PHILOSOPHY

### 1.1 Information hierarchy through scale, not decoration

Both decks communicate hierarchy entirely through **type size and weight**, not borders,
boxes, or rules. A 26pt title + 14pt subtitle + 9pt body creates three clear levels with
no dividers needed. Pareto applies this absolutely consistently on every slide — the page
feels professional because the rhythm never breaks.

**Inkline implication:** The current `SLIDE_TYPE_GUIDE` prescribes this but chart and table
renderers often add excess chrome. The explicit rule to follow: any visual that can say
something with a number at 24pt should not put a box around it.

---

### 1.2 Action titles state the conclusion, not the topic

Pareto: *"Private equity is gaining mkt. share in the Nordic HY market — with Pareto the
leading arranger in PE-backed issuance."* The subtitle extends the headline argument
rather than describing the slide. Every slide title is a thesis statement.

Launchpad: *"FORECASTED 7.5% YIELD FOR STUDIOS"* — the conclusion IS the title, the
exhibit proves it.

**Inkline implication:** Already in the prompt. But the LLM often drifts toward topic
titles under deadline. The DesignAdvisor prompt should flag this harder as a failure mode.

---

### 1.3 Colour as signal, not decoration

Both decks use accent colour to direct attention to the single most important element on
each page. Pareto uses magenta `#DE0080` exclusively for: (a) the single most important
number in a table row, (b) the current-period bar in a bar chart, (c) call-out labels on
scatter plots. It never uses magenta for decoration.

Launchpad uses orange `#F57821` for: large KPI card panels, structural page anchors
(left-edge accent bands), and nothing else.

**Inkline implication:** The chart renderers have no mechanism for the LLM to designate one
bar/series/segment as the "hero" to receive accent colour. The rest should use a muted
palette. This is the single biggest gap between current renderers and these examples.
**Required: a `highlight_index` or `accent_series` field in chart_data.**

---

## 2. LAUNCHPAD EXHIBIT PATTERNS

---

### LP-1: Full-Bleed Accent Panel

**Description:** A solid-colour rectangle that occupies one full side of the page (usually
right or left third) and bleeds to all three edges. The main content sits in the remaining
two-thirds. The panel contains no content — it is pure visual weight. Photos sit on top of
it, bleeding further.

**Effect:** Creates a sense of luxury and editorial quality. Immediately communicates brand
colour. Gives the page a structured spine without a visible rule or divider.

**Best for:** Introduction slides, section openers, any page where you need strong
first-impression visual weight with relatively modest content (2-3 paras of text +
imagery).

**Dimensions/specs for Inkline:**
- Panel width: 35–45% of page width, full height, zero margin
- Fill: primary brand dark or accent colour
- Content sits in remaining 55–65% with 40pt left margin
- Photo image: drops into the panel area, typically 60% panel width, vertically centred
  or top-aligned with 20pt bleed outside panel boundary
- Typst implementation: use `rect(fill: brand-dark, height: 100%, width: 40%)` in a grid,
  place image with `image(fit: "cover")` in an overlapping `place()` block
- Current closest: `split` slide type — but without the bleed and without photo placement

---

### LP-2: Hero Typography Header (Two-Line with Distinct Weights)

**Description:** Section headers use two lines at different weights/sizes:
- Line 1: 46pt, regular weight, all-caps — the *mood word* or *evocative descriptor*
  e.g. `LIGHT & AIRY`, `FUN & GAMES`, `COME & GO`, `REGENERATION & INVESTMENT`
- Line 2: 24pt, bold — the *functional category* e.g. `THE APARTMENTS`, `CONNECTIVITY`

The mood word (line 1) is large enough to be art. The functional label (line 2) anchors it
to content.

**Effect:** Creates editorial brochure energy. The mood word communicates brand feeling
before the reader has processed the content.

**Best for:** Every new section in a brochure-style deck. Product/property marketing,
company overviews, investor materials with strong brand identity.

**Dimensions/specs for Inkline:**
- Add a new `section_hero` slide type — or add `hero_label` + `hero_title` fields to the
  existing `title`/`section_divider` types
- Typst: `text(size: 46pt, weight: "regular", fill: accent, upper(hero_label))` +
  newline + `text(size: 24pt, weight: "bold", fill: white, hero_title)`
- This would require a new Typst template segment or extension of `section_divider`

---

### LP-3: KPI Forecast Cards (Stacked Orange Boxes)

**Description:** Three identical rectangular boxes (247 × 72 pt each) stacked vertically
on the right edge of the page. Each box contains:
- Line 1 (bold, ~14pt): The metric value — `FORECASTED 7.5% YIELD`
- Line 2 (regular, ~10pt): The descriptor — `FOR STUDIOS`

Boxes are filled with the accent colour (orange), white text, tight internal padding.
They sit flush to the page edge (zero right margin).

**Effect:** Three key numbers communicated in under 1 second. Zero cognitive overhead.
Each number has equal visual weight — they form a scannable column.

**Best for:** Investment returns summary (yield / capital growth / price per unit), any
three-metric hero panel. Works when metrics are of equal importance and can be stated in
10–15 words each.

**Dimensions/specs for Inkline:**
- This is a specialised variant of `kpi_strip` rotated to vertical
- Or: add `vertical_kpi` as a parameter on `kpi_strip`
- Each card: 247pt wide × 72pt tall, 0 right margin, 10pt padding
- Typst: column of three `block(fill: accent, width: 100%, inset: 10pt)` with grid layout
- Fits 3–4 items. Font: 13pt bold for value, 9pt for descriptor
- **Already partially achievable** via `kpi_strip` with `vertical: true` flag (not yet
  implemented). The flush-to-edge behaviour requires a new layout parameter.

---

### LP-4: Photo Grid with Aspect-Matched Cells

**Description:** Pages 7 and 8 show amenity photos arranged in a grid where each cell
has a defined aspect ratio (approximately 16:9 or 4:3) and a consistent padding from its
neighbours. Cells have light grey backgrounds (for loading state / whitespace). There is
no caption under photos — the amenity list is a separate component.

Combined with a vertical list of bold amenity names (10pt bold, ALL-CAPS, each on its
own line with a vertical gap), the page communicates 6 amenities in a highly scannable
format.

**Effect:** Feels like a premium property brochure. Photos prove the claims.

**Best for:** Amenity showcases, product feature pages, team/portfolio pages.

**Inkline deployment:** The current `feature_grid` slide type has text cells but no photo
cells. Inkline currently has no photo-grid layout. This would require:
- A new `photo_grid` slide type with `items: [{image_path, caption?}]`
- Or extend `multi_chart` to support non-chart image cells (images from uploads, not renders)
- Medium complexity — mostly a Typst template change, not a renderer change

---

### LP-5: Connectivity Timing List

**Description:** Page 11 shows transit times as a structured list with three columns:
- Column 1 (bold 11pt): Destination name — `STRATFORD INTERNATIONAL`
- Column 2: Mode of transport label (BY TRAIN / BY CAR)
- Column 3 (regular 10pt): Travel time — `14 mins`

No table borders. The structure comes from consistent x-positions. Two transport modes
presented in parallel columns (train left, car right).

A large contextual statement leads the page: *"Launchpad is a short walk from Gravesend
station…"* at 14pt bold.

**Effect:** Transport data is instantly readable. Far cleaner than a table. Feels natural.

**Best for:** Location connectivity, competitive access comparisons, timeline durations,
any structured 3-column row data where values are short and rows are 4–8 items.

**Inkline deployment:** This is a variant of `comparison` but with 3 columns and no
headers. The cleanest implementation would be:
- Use `table` with 3 columns, no header row, no visible borders, alternating row padding
- Or add a `triples_list` layout (label | annotation | value) — a lightweight new type
- Low complexity — achievable within existing `table` by styling with `stroke: none`

---

### LP-6: Architectural Floor Plan with Zonal Colouring

**Description:** Pages 9 and 10 show building floor plans with rooms coloured by zone
type:
- Green mint: communal/social spaces  
- Light orange/peach: circulation/services
- Near-white: private studios

Street names label the perimeter. Room numbers label individual units. A key in the
bottom corner explains colours. Two plans shown side by side (ground floor / upper floor).

**Effect:** Instantly communicates building organisation and amenity placement.

**Best for:** Property brochures, building projects, campus maps, office layouts.

**Inkline deployment:** This is too bespoke to auto-render from LLM-generated data — it
requires actual architectural CAD output. Outside scope for automated Inkline renders.
Could be supported as an `image_path` embed (user provides the plan image). Not a
chart renderer candidate.

---

### LP-7: Development Programme Timeline (Gantt-Style Bars)

**Description:** Page 13 shows a construction programme as horizontal bars across a
date axis. Four phases shown:
- Demolition & site remediation (narrow bar, early)
- Foundations & substructure
- Superstructure
- MEP, fitout + Practical Completion (widest bar, latest)

Dates mark the start of each phase on the x-axis. Each bar is a dark navy fill.
The phase labels sit above each bar. No gridlines, no y-axis ticks.

**Effect:** Communicates project timeline in exactly the format project managers expect.

**Best for:** Construction programmes, product development roadmaps, transaction timelines
with parallel workstreams, any multi-track Gantt-style schedule.

**Inkline deployment:**
- This is distinct from the current `timeline` slide type (which is a horizontal
  milestone chain, not parallel tracks)
- Would require a new `gantt` chart renderer:
  - `chart_data: {tracks: [{label, start_date, end_date, colour?}], date_range: [start, end]}`
  - Matplotlib implementation: horizontal `barh` with date-based x-axis, yticks as track labels
  - Medium complexity renderer addition

---

### LP-8: Fact Sheet Grid

**Description:** Page 17 shows a 3×2 grid of information cells. Each cell has:
- Bold label (13.7pt): `Nearest Train Station`, `Number of Studios`, etc.
- Large value below (10.9pt bold): `Gravesend Train Station`, `477`, `£169,000`
- Sub-value if needed: `2 min walk`
- Light background fill (lilac tint)
- No borders — whitespace separation only

**Effect:** The critical deal facts, scannable at a glance. Feels like a term sheet summary.

**Best for:** Deal fact sheets, property summaries, product specs, any ≤6 key facts that
need to be scannable.

**Inkline deployment:**
- Very close to `icon_stat` without icons
- Or a 3×2 variant of `four_card` with no icons and tighter cell padding
- Could be achieved by adding `style: "fact_sheet"` parameter to `kpi_strip` or `icon_stat`
- Low complexity

---

### LP-9: Map + Categorised Amenity List

**Description:** Page 12 shows a streetmap (image) in the top half of the page. Below
the map, local amenities are listed in 3–4 category columns:
- `RETAIL`, `HEALTH & WELLBEING`, `BARS, RESTAURANTS & CAFES`
- Each column: category name (12pt bold, spaced-out tracking) then 4–6 venue names
- Two venues per row (two columns within each category column)

**Effect:** The map shows where, the list shows what's there. Immediately useful.

**Best for:** Location context pages for any property/office/venue. Works for competitive
landscape slides (map + competitor list).

**Inkline deployment:**
- The map part requires a user-provided image path
- The amenity list below is a `feature_grid` variant with category headers per column
- Could be implemented as `map_amenity` slide: `{image_path, categories: [{name, items[]}]}`
- Medium complexity — new slide template

---

## 3. PARETO EXHIBIT PATTERNS

---

### PT-1: Consistent Section-Tab Header Architecture

**Description:** Every single slide in the Pareto deck (all 58) uses the exact same header
structure:
- Row 1: 8pt bold ALL-CAPS section name in a navy bar, flush left — `FINANCING ALTERNATIVES`
- Row 2: 26pt regular slide title — `A bird's view of available liquidity pools`
- Row 3: 14pt regular subtitle/context — `Illustrative overview of key funding sources…`
- Total header zone: approximately top 90pt of a 540pt page

The body content starts at a fixed y-position (~108pt from top) on every page.
This creates predictable visual rhythm across the entire deck.

**Effect:** The reader always knows where to find the title. Navigation feels effortless.
Instantly professional — looks like a Goldman/Barclays pitchbook.

**Inkline implication:** The current `section` + `title` field pattern already handles
this, but the visual rendering (the coloured section tab band) is not consistently applied
to all slide types. The aigis/aria templates should enforce this header band on all content
slides.

---

### PT-2: Hero Metric Strip (Split by Category)

**Description:** Page 4 shows two groups of metrics separated by a vertical divider:
- Left group: "Debt Capital Markets (2021-2024)"
- Right group: "Equity Capital Markets (2021-2024)"
- Each group has 3 metrics at 15pt bold: value + 9pt descriptor below

The metrics sit on a light-coloured background strip (~30pt tall) with no borders.
Values are stark: `EUR 30bn` / `~370` / `>50%`.

**Effect:** Six numbers communicated in one glance. The categorical split tells a
story: we are balanced across both DCM and ECM.

**Best for:** Firm/fund credentials, comparative performance, before/after metrics.
Works for any ≤6 metrics that fall into exactly 2 natural categories.

**Inkline deployment:**
- Closest: `kpi_strip` with `highlight: true` on one item
- To fully replicate: add `groups: [{label, kpis[]}]` to `kpi_strip` data schema
- Would render as two labelled sub-strips within one slide
- Low-medium complexity

---

### PT-3: Axis-Free Bar Chart with Direct Data Labels

**Description:** Page 10 (and others) shows a bar chart where:
- There is NO y-axis and NO y-axis gridlines
- Each bar has its value directly above it (or inside the top of the bar for tall bars)
- The x-axis has minimal labelling — just year names, no tick marks
- A sparse descriptive callout (e.g. `PSEC TOTAL DEBT RAISED / LAST 5 YEARS / (EURbn)`)
  is embedded in the lower-left white space of the chart area, at 12pt bold — this IS
  the chart title, positioned inside the chart, not above it

**Effect:** 40% less visual chrome. The data speaks. Feels like FT/Bloomberg infographic
style, not Excel.

**Best suited for:** Any bar chart where the comparison is the story (relative heights
obvious), exact values matter (label on bar), and the audience is sophisticated. Works
for 4–10 bars. Breaks down for >12 bars where labels crowd.

**Dimensions/specs for Inkline:**
- Add `style: "clean"` parameter to `grouped_bar`, `stacked_bar`, `waterfall` chart_data
- When `style: "clean"`:
  - `ax.spines["left"].set_visible(False)` + `ax.spines["right"].set_visible(False)` +
    `ax.spines["top"].set_visible(False)`
  - Remove y-axis ticks: `ax.yaxis.set_visible(False)`
  - Add direct labels above each bar: `ax.text(x, val + offset, f"{val:.1f}", ha="center")`
  - Place chart_title as text annotation inside chart body (lower-left) at ~12pt bold
  - Keep only bottom spine and x-axis labels
- Also add `accent_index: 2` (0-based) to highlight one bar in accent colour; all others
  use the muted secondary palette colour
- Low complexity — a few renderer parameters

---

### PT-4: Annotated Scatter Plot (Tombstone Scatter)

**Description:** Page 38 shows bonds plotted as dots where:
- X-axis: time to maturity (years)
- Y-axis: credit spread (bps)
- Each dot has: a small label (company name) + a callout showing "Outstanding bond: **515**"
  in 10pt bold, with a secondary line "*(700 at issuance)*" in 8pt muted
- Some dots have a secondary annotation box showing "At issuance: **450**"
- No legend — every data point is self-labelling

**Effect:** Each deal is a distinct entity with a name and story, not just a data point.
The scatter communicates the market at a glance; the labels make it actionable.

**Best for:** Comparable bond/loan pricing analysis, competitive comps analysis, any
"market landscape" where individual names matter as much as the aggregate picture.
Works for 4–15 data points.

**Dimensions/specs for Inkline:**
- A new `annotated_scatter` chart type (distinct from the current `scatter`)
- `chart_data: {points: [{x, y, label, value_label?, secondary_label?, accent?}],
    x_label?, y_label?, accent_index?}`
- Renderer: plots each point with `ax.annotate()` using `xytext` offset per point to
  avoid overlaps, draws a thin line from dot to label box
- For the "at issuance vs current" variant: two y-values per point with a connecting
  vertical line (like a dumbbell chart)
- Medium complexity — annotation placement requires auto-layout to avoid label collisions

---

### PT-5: Transaction Credentials Grid (Deal Card Array)

**Description:** Page 9 shows a 2×4 grid (8 deal cards) each containing:
- Company/project name (9pt bold, all-caps)
- Instrument type (9pt regular): `Direct Lending`, `Private Placement`
- Deal size (9pt regular): `USD 148m`, `EUR 360m`
- Company logo (small image ~30×20pt)
- Light grey background fill per card, thin white border between cards

**Effect:** "Look at all the deals we've done." Instantly communicates track record depth.

**Best for:** Transaction credentials, portfolio companies, reference clients, case study
collections. Works for 4–12 items.

**Dimensions/specs for Inkline:**
- This is a specialised `feature_grid` variant with logos
- Or a new `credentials_grid` slide type:
  `{items: [{name, type, size, logo_path?}], cols: 3|4}`
- Without logos: achievable now with `feature_grid` (6 items max)
- With logos: requires `image()` placement in each cell — medium complexity Typst change

---

### PT-6: Two-Panel Chart Page (Equal Split, Per-Panel Headers)

**Description:** Pages 6, 14, 23, 32, 33: Two independent charts placed side-by-side at
~50/50 split, each with its own:
- 12pt bold sub-heading directly above the chart
- Optional small detail label (9pt, e.g. `Outstanding volumes over two decades`)

The sub-headings are flush left within their respective columns. There is no overall
"chart container" — the charts float in their columns.

**Effect:** Two related but independent data stories on one slide. More information density
than a single chart slide, but less cluttered than a 4-panel page.

**Best for:** Before/after comparisons, two correlated metrics, left panel = volume /
right panel = composition, any "here is the market and here is our position in it" story.

**Inkline deployment:**
- Already supported via `multi_chart` with `layout: "equal_2"` or `"hero_left"`
- The per-panel sub-heading is NOT currently supported (current `charts` array has
  `title` per chart, but this renders as a chart title inside the image, not above it)
- **Improvement needed:** Add `panel_title` to each chart in a `multi_chart` slide, rendered
  as a Typst text block above the image, not inside the matplotlib figure
- Low complexity — a Typst template change to the `multi_chart` renderer

---

### PT-7: Bold In-Line Emphasis with Accent Colour

**Description:** Page 6: Body copy reads in regular weight/colour, then mid-sentence
the key claim switches to bold + accent colour:
*"…holding roughly 50% market share over the past 10 years, versus* **15% for the closest
competitor**"*

This is not a callout box or a pull quote — it is seamlessly embedded in the paragraph.

**Effect:** Forces the reader's eye to the exact data point that makes the argument. Zero
visual overhead.

**Best for:** Any content slide where one fact is significantly more important than the
supporting context. Competitive comparisons, performance claims, risk disclosures where
one item is critical.

**Inkline deployment:**
- Typst supports inline styling: `"text" + text(weight: "bold", fill: accent)["key claim"]`
- Current `content` slide type only supports plain string bullets
- Would require adding `{text: "...", emphasis: "key phrase"}` to bullet items
- Or: support markdown-style `**bold**` within bullet strings and parse to Typst markup
- Low-medium complexity

---

### PT-8: Transition Heatmap (Year × Percentage Grid)

**Description:** Page 55 shows income transition visualised as a grid where:
- Columns: % of income from new source (0% to 100%, in 10% increments)
- Rows: Years (2024–2028)
- Each cell is filled with a colour indicating the proportion of crypto vs HPC/AI income
  in that cell

This functions as a combination of heatmap + progress tracker — showing that as years
progress, the highlighted column moves right (from 0% HPC/AI towards 100% HPC/AI).

**Effect:** A single image shows the entire story of a multi-year transition. The reader
can see not just where you end up but the path there.

**Best for:** Business model transitions, revenue mix shifts over time, any "journey from
A to B" where intermediate states matter. Works whenever there are 4–6 time periods and
a continuous 0–100% spectrum.

**Dimensions/specs for Inkline:**
- This is a specialised variant of the existing `heatmap` renderer
- Could be implemented as `chart_type: "transition_grid"` with:
  `chart_data: {rows: [{label, highlight_col}], col_labels: [...], title?}`
  Where `highlight_col` is the index of the "current position" for each row
- The renderer draws all cells in muted colour, with one cell per row highlighted in accent
- Alternatively: use the existing `heatmap` renderer with carefully chosen value matrix
- Low complexity if added as a parameter to the existing heatmap renderer

---

### PT-9: Bird's Eye Comparison Matrix with Visual Indicators

**Description:** Page 12 shows a matrix comparing financing instruments (Banks, Infra Debt,
ECA, USPP, Senior Secured Bonds, Unsecured Bonds) across multiple criteria. Instead of
text values in cells, the cells contain:
- Filled circles (●●●) for strong suitability
- Partially filled or empty circles for weaker suitability
- Coloured cell backgrounds (teal for high, light grey for medium, white for low)

Row headers are left-aligned attribute names. Column headers are instrument type names.

**Effect:** A decision matrix that communicates gradient suitability, not binary yes/no.
Far more information than a text comparison table. Scannable in ~5 seconds.

**Best for:** Product/service comparison matrices, scoring frameworks, capability
assessments, "which option is best for your situation" analyses.

**Dimensions/specs for Inkline:**
- A new `scoring_matrix` chart renderer:
  `chart_data: {rows: [{label, scores: [0-3]}], col_labels: [...], title?}`
  Score 0 = white/empty, 1 = light-fill + partial circle, 2 = medium fill + filled circle,
  3 = dark fill + filled circle
- Matplotlib renderer: draws a grid using `ax.imshow()` for cell fills + overlaid text
  symbols (●, ◐, ○) at each cell position
- Medium complexity — new renderer, clean layout

---

### PT-10: In-Chart Caption / Embedded Title

**Description:** Page 10: The bar chart has no formal chart title element. Instead, a
multi-line text block sits in the lower-left whitespace of the chart:
```
PSEC TOTAL DEBT RAISED
LAST 5 YEARS
(EURbn)
```
At 12pt bold for line 1–2, 9pt regular for line 3. This text block occupies the negative
space that the bars don't use (lower left, since bars only occupy the upper portion of the
y-range).

**Effect:** The title becomes part of the composition rather than overhead. The chart feels
designed, not generated.

**Best for:** Bar/column charts where bars are tall-ish (use upper 60–70% of plot area)
and the lower-left is clear whitespace. Single-series bar charts work best.

**Inkline deployment:**
- Add a `title_position: "inside_lower_left"` parameter to chart_data for bar charts
- When set: `ax.text(0.02, 0.15, title, transform=ax.transAxes, ...)` instead of
  `ax.set_title(title, ...)`
- Very low complexity — 3-line renderer change

---

### PT-11: Deal Book Snapshot Table

**Description:** Page 21 shows a lender participation table with columns:
- Type | Geography | Lead/Follower | Ticket size (% of overall) | Amount (NOK m)
- Each row: one lender, with the % presented as `(27%)` in smaller text below the NOK value
- Column headers use 8pt bold with a grey header background
- Key aggregate statistic (e.g. "60% oversubscription") shown as a 12pt bold callout
  to the right of the table

The table has no outer border. Row separators are thin horizontal lines only.

**Effect:** Shows the full lender syndicate at a glance. The % callout turns a list into
a story about relative sizes.

**Best for:** Syndication books, cap table summaries, investor allocation tables, any
structured data where both absolute values and % splits matter simultaneously.

**Inkline deployment:**
- This is the current `table` slide type with a callout stat
- The enhancement needed: support `{value, sub_value}` objects in table cells (not just
  plain strings) — the sub_value renders at smaller font in muted colour below
- Also: a `callout_stat` field on `table` slides that renders a single hero metric to
  the right of the table
- Medium complexity — Typst template extension

---

### PT-12: Multi-Level Process Timeline

**Description:** Page 28 shows a process timeline with three levels of hierarchy on a
single horizontal axis:
- Level 1 (above the axis): Duration callouts `1–8 weeks` / `0.5–2 weeks` / `2 weeks`
- Level 2 (large, at axis): Phase names `Preparations` / `Marketing` / `Settlement` (16pt bold)
  with sub-label `Phase I` / `Phase II` / `Phase III` (12pt bold)
- Level 3 (below axis): Bullet point tasks for each phase (9pt)
- A pink accent divider line `|` marks the boundary between phases

**Effect:** One image tells you timing, structure, AND details of a process — without
text crowding. The three levels prevent any single layer from becoming overwhelming.

**Best for:** M&A processes, fundraising timelines, product launch plans, any process that
has both a phase structure AND detailed tasks that audiences need to see.

**Inkline deployment:**
- The current `timeline` type (horizontal milestones) handles Level 2 only
- Would require a `multi_level_timeline` chart type:
  `chart_data: {phases: [{label, sub_label, duration, tasks: [str]}]}`
- Matplotlib renderer: draws three horizontal bands (duration strip / phase name / tasks)
  with dividers
- Medium complexity — new renderer

---

### PT-13: Two-Column Comparison Table with Row Headers

**Description:** Page 27 shows a structured comparison with:
- Left header column (bold): `Format`, `Indicative timeline`, `Marketing documentation`…
- Centre-left data column: `Private debt` description (4–6 lines per row)
- Centre-right data column: `Nordic public bond` description (4–6 lines per row)
- Column headers in bold navy at top
- Row separators: thin horizontal rules
- Alternating very-light background tints on rows

No outer border. Header row has solid navy background with white text.

**Effect:** Structured comparison that allows multi-line content per cell. More flexible
than the current `comparison` slide type which constrains content length tightly.

**Best for:** Product/structure comparisons, due diligence framework comparisons, any
A-vs-B analysis where each dimension needs 2–4 lines of explanation.

**Inkline deployment:**
- The current `comparison` type handles short (≤30 char) values per cell
- This pattern needs multi-line cell content — which is possible in Typst but requires
  a different template (rows auto-size based on content)
- Enhancement: add `style: "rich"` to `comparison` that allows longer `desc` fields
  per row item
- Medium complexity — Typst template redesign for rich comparison

---

### PT-14: Donut Triptych (Three Small Donuts)

**Description:** Page 43 shows three donut charts side-by-side, each 150pt wide, under
a single slide header. Each donut has:
- A bold sub-title above it: `CURRENCY SPLIT` / `RATING SPLIT` / `IFRS TREATMENT`
- Direct segment labels (not a legend): e.g. `EUR, 30%` positioned at 3 o'clock outside
  each segment
- No legend panel

**Effect:** Three distribution stories in the space of one chart. Each is self-contained.
The reader's eye scans left-to-right across all three and extracts three independent
insights.

**Best for:** Any set of 3 categorical distributions that are conceptually related but
not additive. Fund characteristics (geography/sector/stage), deal statistics
(currency/tenor/seniority), demographic profiles.

**Inkline deployment:**
- Already achievable with `multi_chart` layout `"equal_3"` with three `donut` chart_requests
- The per-chart sub-titles work via the `title` field in each `charts` array element
- The direct-label style (not legend) requires `style: "direct_labels"` in donut chart_data
  (not currently implemented — currently always renders a right-side legend)
- **Enhancement needed:** Add `label_style: "direct"` to donut/pie chart_data to
  position labels at segment midpoints rather than in a legend panel
- Low complexity

---

### PT-15: Annotated Dumbbell / Spread Migration Chart

**Description:** Page 38: Each bond deal is shown as a vertical line segment from its
"at issuance" spread (top of dumbbell) to its "current" spread (bottom), with the current
value shown in bold and "at issuance" shown in muted italics below.

This is the scatter plot combined with a connector line to show movement over time
(compression = positive, widening = negative).

**Effect:** Immediately shows which deals have performed (spread tightened) vs weakened.
The compression/widening is visible at a glance without needing to do mental arithmetic.

**Best for:** Bond pricing performance, analyst estimate vs actual comparisons, before/after
metric pairs where the direction of change is the story.

**Inkline deployment:**
- A new `dumbbell` chart type:
  `chart_data: {points: [{label, value_start, value_end, start_label?, end_label?}],
    y_label?, accent_direction: "lower_is_better"|"higher_is_better"}`
- Renderer: horizontal barh-style layout, each item gets two dots connected by a vertical
  line. The "end" dot gets accent colour if it moved in the right direction.
- Medium complexity — new renderer

---

## 4. PRIORITISED INKLINE DEPLOYMENT ROADMAP

Ranked by: (impact × frequency of use) / implementation complexity

| Priority | Pattern | Type | Complexity | Impact |
|----------|---------|------|-----------|--------|
| 1 | **PT-3: Axis-free bars + direct labels + accent_index** | Renderer enhancement | Low | Very High |
| 2 | **PT-14: Donut triptych (direct labels)** | Renderer enhancement | Low | High |
| 3 | **PT-10: In-chart embedded title** | Renderer param | Very Low | High |
| 4 | **LP-3: KPI forecast cards (stacked vertical)** | New slide type param | Low | High |
| 5 | **PT-6: Per-panel titles in multi_chart** | Typst template | Low | High |
| 6 | **PT-7: Bold in-line emphasis in text** | Typst markup + LLM spec | Medium | Medium |
| 7 | **PT-8: Transition heatmap** | New renderer | Low | Medium |
| 8 | **PT-9: Scoring matrix with visual indicators** | New renderer | Medium | Medium |
| 9 | **PT-12: Multi-level process timeline** | New renderer | Medium | Medium |
| 10 | **LP-7: Gantt chart (parallel tracks)** | New renderer | Medium | Medium |
| 11 | **PT-4: Annotated scatter / tombstone scatter** | New renderer | Medium | Medium |
| 12 | **PT-15: Dumbbell chart** | New renderer | Medium | Medium |
| 13 | **LP-8: Fact sheet grid** | Style param on kpi_strip | Low | Low |
| 14 | **LP-1: Full-bleed accent panel** | New Typst template | High | High (brochure only) |
| 15 | **PT-5: Credentials grid with logos** | New slide type | High | Medium |

---

## 5. DESIGN ADVISOR PROMPT GAPS

The following principles from these reference decks are **not** currently articulated in
the DesignAdvisor system prompt and should be added:

1. **Accent = signal, not decoration.** Use accent colour for ONE element per slide: the
   hero bar, the most important number, the key comparison outcome. Everything else uses
   the primary or muted palette.

2. **Axis reduction.** For bar charts where relative heights are visually obvious and
   exact values are important: prefer axis-free + direct label style. Add `style: "clean"`
   guidance.

3. **In-chart title placement.** For bar charts with tall bars, place the title inside the
   chart body lower-left. Saves vertical space on smaller chart_caption panels.

4. **Donut as distribution story, not pie.** Three donuts for three related distributions
   is a proven pattern. The LLM should be guided to use `multi_chart` + three `donut`
   charts when presenting 3 categorical breakdowns of the same entity.

5. **Typography-led section headers.** When a slide is primarily a section opener or
   context-setter (not data-dense), the header can be the exhibit. A 46pt mood word +
   24pt category + 12pt body para IS a valid slide — it does not need a chart.

6. **Credentials / track record slides.** The LLM has no explicit guidance for organising
   historical transactions or portfolio companies. The `feature_grid` is the closest match
   but the naming and description don't map to this use case. Add explicit guidance.

7. **Direct-label approach for scatter plots.** When plotting 4–15 named data points on a
   scatter, label each point directly rather than using a legend. More readable, more
   informative.

---

*Analysis generated 2026-04-14. Based on structural extraction of both PDFs via pymupdf.*
*Layout measurements in points (1pt = 1/72 inch). Page dimensions: Launchpad A3 landscape
(1191×842pt), Pareto widescreen (780×540pt).*
