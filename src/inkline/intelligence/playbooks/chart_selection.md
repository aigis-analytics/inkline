---
domain: charts
audience: [claude-code, design-advisor]
slide_type_relevance: [chart, bar_chart, chart_caption, multi_chart]
brand_affinity: []
last_updated: "2026-04-26"
version: "1.0.0"
description: "Optimal chart type selection for any data shape, communication goal, and audience context."
---

# Chart Selection Playbook

> **Purpose**: Guide the DesignAdvisor in selecting the optimal chart type for any
> given data shape, communication goal, and audience context.
>
> **Authority sources**: FT Visual Vocabulary, Storytelling with Data (Cole
> Nussbaumer Knaflic), From Data to Viz, Datawrapper Chart Guide, UK Government
> Analysis Function guidelines.

---

## 0. PRIME DIRECTIVE: Facts Discipline (read this first)

**You are NOT allowed to invent data.** Inkline operates in two modes:

### Mode A — "Data-in" (caller provides facts, you pick layouts)
The caller gives you raw sections containing facts: numbers, names, claims,
narratives, comparisons. **You may only restate, regroup, or visualise what
is in the input.** You may NOT invent:

- Statistics (no fictional 92x growth, $8.4M ARR, 920 GitHub stars)
- Customer or company names not provided
- Dates, durations, percentages, ratings
- Plausible-sounding details that "feel right" for the audience

If the input has 3 facts, the slide shows 3 facts. If the input is sparse,
the slide is sparse-but-impactful. Action titles and visual emphasis are
your tools — fabrication is not.

### Mode B — "Spec-in" (caller provides exact slide specs)
The caller gives you full slide specs (slide_type + data). You don't run
in this mode. The renderer just executes them.

### Illustrative content marker
When a section has `illustrative=True`, the data is a STAGE PROP for visual
demonstration only. Your slide MUST mark it as ILLUSTRATIVE in:

- The slide caption: "ILLUSTRATIVE — [what the demo shows]"
- The footnote: include "Illustrative example, not real data"
- For chart_caption / dashboard slides, the chart itself will get an
  "ILLUSTRATIVE" watermark from the chart_renderer.

A slide based on illustrative data that does NOT mark itself as such is a
HALLUCINATION and is forbidden.

### Facts grounding examples

```
INPUT:
{
  "section": "Traction",
  "metrics": {"deals_processed": "7+", "verification_accuracy": "93%"},
  "narrative": "Tested on real transaction VDRs in GoM and Angola."
}

GOOD slide spec — uses only the input facts:
{"slide_type": "icon_stat", "data": {
  "section": "Traction", "title": "Validated on real VDRs",
  "stats": [
    {"value": "7+", "icon": "📊", "label": "Deals processed"},
    {"value": "93%", "icon": "✓",  "label": "Verification accuracy"},
  ],
  "footnote": "Tested in GoM and Angola transactions."
}}

BAD slide spec — invents customer names and rates:
{"slide_type": "icon_stat", "data": {
  "stats": [
    {"value": "$8.4M", "label": "ARR"},          ← INVENTED
    {"value": "212%", "label": "NRR"},           ← INVENTED
    {"value": "47", "label": "Customers"},       ← INVENTED
  ],
}}
```

---

## 1. Decision Framework — Start With the Question

Before choosing a chart, answer three questions:

| # | Question | Why it matters |
|---|----------|----------------|
| 1 | **What relationship am I showing?** | Determines the chart *family* (see Section 2) |
| 2 | **How many variables / series?** | Narrows to specific chart *type* |
| 3 | **Who is the audience?** | Sets complexity ceiling (exec = simple; analyst = dense) |

### The FT Visual Vocabulary Categories

The Financial Times organises all chart types into **nine data-relationship
categories**. Use this as the primary lookup:

| Data Relationship | What you are showing | Go-to charts |
|-------------------|----------------------|-------------|
| **Deviation** | Variation (+/−) from a fixed reference | Diverging bar, diverging stacked bar, surplus/deficit filled line |
| **Correlation** | Relationship between 2+ variables | Scatter, bubble, connected scatter, XY heatmap |
| **Ranking** | Position in an ordered list | Ordered bar, slope chart, lollipop, dot strip plot |
| **Distribution** | How values spread / frequency | Histogram, box plot, violin, population pyramid, dot plot |
| **Change over time** | Trends across periods | Line, column, area, slope, fan chart, calendar heatmap |
| **Part-to-whole** | How a total breaks into parts | Stacked bar, pie, donut, treemap, waterfall, Venn |
| **Magnitude** | Size comparisons | Bar, column, paired bar, proportional symbol, isotype |
| **Spatial** | Geographic patterns | Choropleth, proportional symbol map, flow map, dot density |
| **Flow** | Movement / process between nodes | Sankey, chord, network, waterfall |

---

## 2. Chart-by-Chart Reference

### 2.1 Bar & Column Charts

**Vertical column** — default for comparing discrete categories or showing change
over time when the number of periods is small (< 12).

**Horizontal bar** — preferred when category labels are long, or when showing a
ranked list (sort descending for readability).

**Stacked bar/column** — shows part-to-whole AND magnitude simultaneously. Limit
to 2-4 segments; beyond that, the inner segments become unreadable.

**Grouped (clustered) bar/column** — compares sub-categories side-by-side. Works
with 2-3 groups; more than that creates visual noise.

**100% stacked bar** — pure part-to-whole comparison (removes magnitude). Good for
survey Likert-scale data or composition comparison across categories.

#### Decision rules

```
IF comparing categories AND labels are short → vertical column
IF comparing categories AND labels are long → horizontal bar
IF showing composition of a total → stacked bar
IF comparing composition across groups → 100% stacked bar
IF comparing sub-categories within groups → grouped bar (max 3 groups)
IF showing a ranked list → sorted horizontal bar
```

#### Do's and Don'ts

- DO start the y-axis at zero — truncating bars distorts perceived magnitude.
- DO sort bars meaningfully (by value, alphabetically, or by a logical order).
- DO use direct labels on bars when there are fewer than 10 categories.
- DON'T use 3D effects — they distort area perception.
- DON'T use more than 5-6 colours in a single chart.

---

### 2.2 Line Charts

**Single-series line** — the default for showing a continuous trend over time.

**Multi-series line** — compares trends. Limit to 4-5 lines before the chart
becomes "spaghetti." Use colour + direct labels (not a legend).

**Area chart (filled line)** — adds visual weight to show volume/magnitude under
the curve. Best for a single series or stacked areas (max 3-4).

**Sparkline** — a tiny, word-sized line chart embedded in a table or dashboard
cell. No axes; communicates trend shape only.

#### Decision rules

```
IF continuous data over time (>5 points) → line chart
IF showing volume under a trend → area chart
IF comparing 2-4 trends → multi-series line
IF comparing 5+ trends → small multiples (one line each)
IF inline trend indicator in a table → sparkline
```

#### Do's and Don'ts

- DO label lines directly at their endpoint (not via a legend).
- DO use a thicker stroke for the "focus" line, thinner/greyed for context lines.
- DO include zero on the y-axis unless the range is very narrow and context is
  clear (e.g., stock prices).
- DON'T connect data points that are not sequential or continuous.
- DON'T use area charts for series that cross over each other (use line instead).

---

### 2.3 Pie & Donut Charts

**When pie charts work:**

- Showing 2-3 segments of a single whole (e.g., "72% yes / 28% no").
- The audience is non-technical and the message is simple proportion.
- A single dominant segment needs emphasis.

**When pie charts fail:**

- More than 5 segments — comparisons become impossible.
- Segments are close in size — humans cannot accurately judge angles.
- Comparing across multiple pies — use stacked bars instead.
- Showing change over time — never use a pie for temporal data.
- Values don't sum to a meaningful whole.

**Donut charts** are functionally identical to pies but allow a KPI or total in
the centre. Prefer donut when a summary number adds context.

#### Decision rules

```
IF part-to-whole AND ≤3 segments AND one segment dominates → pie or donut
IF part-to-whole AND 4-5 segments → stacked bar (preferred) or pie (acceptable)
IF part-to-whole AND >5 segments → stacked bar or treemap
IF comparing part-to-whole across groups → 100% stacked bar (NEVER multiple pies)
```

#### Do's and Don'ts

- DO label slices directly with % values.
- DO start the first slice at 12 o'clock and proceed clockwise.
- DO order slices largest-to-smallest (clockwise).
- DON'T use "exploded" slices — they break area comparison.
- DON'T use a pie if the segments don't sum to 100% of a meaningful total.
- DON'T use a pie for more than 5 categories.

---

### 2.4 Scatter Plots & Bubble Charts

**Scatter plot** — shows correlation or clusters between two continuous variables.
Each point is an observation.

**Bubble chart** — a scatter plot with a third variable encoded as bubble area.
Limit to three dimensions (x, y, size). Adding colour as a 4th dimension
approaches the limit of working memory (~4 items).

#### Decision rules

```
IF exploring correlation between 2 numeric variables → scatter
IF showing correlation + a 3rd magnitude variable → bubble
IF showing correlation over time → connected scatter
IF >500 data points with overlaps → density plot or hex-bin
```

#### Do's and Don'ts

- DO scale bubble *area* (not radius) to the data value.
- DO add a trend line or R² annotation when correlation is the story.
- DO use semi-transparent fills when points overlap.
- DON'T use scatter for categorical data (use a strip/jitter plot instead).
- DON'T encode more than 4 dimensions — it overloads cognition.

---

### 2.5 Waterfall Charts

Show how a starting value is affected by a series of positive and negative
contributions to reach a final total. Classic use: revenue bridges, P&L
walk-throughs, variance analysis.

#### Decision rules

```
IF showing cumulative effect of additions/subtractions → waterfall
IF financial bridge (revenue → profit, budget → actual) → waterfall
IF simple before/after comparison → paired bar or bullet chart
```

#### Do's and Don'ts

- DO colour-code increases (green/blue) vs. decreases (red/orange).
- DO show connector lines between columns for clarity.
- DO label each bar with its delta value.
- DON'T use waterfall for non-additive data.

---

### 2.6 Funnel Charts

Show progressive reduction through sequential stages (e.g., sales pipeline,
conversion funnel, hiring process).

#### Decision rules

```
IF sequential stages with decreasing volume → funnel
IF stages can increase as well as decrease → bar chart (not funnel)
IF comparing funnels across segments → grouped horizontal bar
```

---

### 2.7 Heatmaps

Use colour intensity across a matrix to reveal patterns in two-dimensional
categorical data. Good for: correlation matrices, time-of-day patterns,
cross-tabulations.

#### Decision rules

```
IF two categorical axes + one numeric value → heatmap
IF showing temporal pattern (day × hour) → calendar heatmap
IF showing correlation matrix → XY heatmap with diverging palette
```

#### Do's and Don'ts

- DO use a sequential palette for single-direction data (0 → max).
- DO use a diverging palette when there is a meaningful midpoint (e.g., 0).
- DO include a colour legend with labelled endpoints.
- DON'T use too many colour steps — 5-7 bins is optimal.

---

### 2.8 Treemaps

Show hierarchical part-to-whole relationships using nested rectangles sized by
value. Good for: budget breakdowns, portfolio composition, file-system usage.

#### Decision rules

```
IF hierarchical data + part-to-whole → treemap
IF flat (non-hierarchical) part-to-whole → stacked bar or pie
IF many small segments are important → treemap (NOT pie)
```

#### Do's and Don'ts

- DO label the largest rectangles directly.
- DO use colour to encode a second variable (e.g., growth rate).
- DON'T use treemaps when precise comparison is needed (rectangles are hard to
  compare accurately).

---

### 2.9 Gauge / Meter Charts

Show a single KPI's progress toward a target on a radial or linear scale.

#### Decision rules

```
IF single KPI with a known target/range → gauge
IF multiple KPIs at once → bullet chart (linear) instead of multiple gauges
IF showing progress over time → line chart (not gauge)
```

#### Do's and Don'ts

- DO clearly mark the target and current value.
- DO use colour zones (green/amber/red) for status.
- DON'T use gauge for comparisons — it wastes space.
- DON'T use more than 3-4 gauges on a single page.

---

### 2.10 Sankey / Flow Diagrams

Show how quantities flow, split, and merge across stages or categories. Width of
each link is proportional to the quantity.

#### Decision rules

```
IF showing flow between source → destination → sankey
IF showing energy/budget/traffic splitting across stages → sankey
IF simple additive walk → waterfall (simpler)
IF showing network connections without quantity → network diagram
```

#### Do's and Don'ts

- DO keep to 2-4 levels (columns) of nodes.
- DO use colour to distinguish source categories.
- DON'T use Sankey for small datasets (< 5 flows) — a table is clearer.

---

### 2.11 Radar / Spider Charts

Compare multiple variables across one or a few entities. The shape of the polygon
conveys an overall "profile."

#### Decision rules

```
IF comparing 5-8 variables for 1-2 entities → radar
IF comparing 3+ entities → small multiples or parallel coordinates
IF >8 variables → parallel coordinates or heatmap
IF precise value readout is needed → bar chart
```

#### Do's and Don'ts

- DO normalise all axes to the same scale.
- DO limit to 5-8 axes.
- DO limit to 1-2 overlaid polygons (use small multiples for more).
- DON'T use if variables have different units or incomparable scales.
- DON'T use if the audience needs exact values (radar is for shape/profile).

---

## 3. Quick-Reference Decision Table

| Your data shape | Primary goal | Recommended chart |
|----------------|-------------|-------------------|
| 1 numeric per category | Compare magnitudes | Bar / column |
| 1 numeric over time | Show trend | Line |
| 2-3 segments of a whole | Show proportion | Pie / donut |
| 4+ segments of a whole | Show proportion | Stacked bar / treemap |
| 2 numeric variables | Show correlation | Scatter |
| 3 numeric variables | Correlation + magnitude | Bubble |
| Sequential stages declining | Conversion | Funnel |
| Additive/subtractive walk | Bridge / variance | Waterfall |
| Flow between categories | Movement / allocation | Sankey |
| 5-8 metrics per entity | Profile comparison | Radar |
| Single KPI vs target | Progress | Gauge / bullet |
| 2 categories × 1 value | Pattern detection | Heatmap |
| Hierarchical composition | Nested parts | Treemap |
| Values + uncertainty | Projection | Fan chart / error bars |
| Many distributions | Compare spread | Box plot / violin |
| Geographic data | Spatial patterns | Choropleth / bubble map |

---

## 4. Labelling and Annotation Rules

1. **Direct-label whenever possible** — labels on the data itself beat legends.
   The viewer should never have to look away from the data to decode it.

2. **Use legends only when** direct labelling would cause clutter (> 5 series,
   dense scatter plots).

3. **Annotate the "so what"** — add a text callout to the most important insight
   (e.g., "Revenue overtook costs in Q3 2024").

4. **Axes**: always label both axes with units. Remove gridlines that don't aid
   reading. Use commas or K/M/B suffixes for large numbers.

5. **Data source**: always include a small-print source line below the chart.

---

## 5. Audience Calibration

| Audience | Complexity ceiling | Preferred types |
|----------|-------------------|-----------------|
| C-suite / board | Very low — 1 chart, 1 message | Bar, line, donut, KPI card |
| General business | Low-medium | Bar, line, stacked bar, waterfall |
| Analysts / data team | High | Scatter, heatmap, violin, Sankey |
| Public / media | Low | Bar, line, pie (simple) |
| Technical / engineering | High | Scatter, radar, parallel coordinates |

---

## 6. Anti-Patterns to Reject

| Anti-pattern | Problem | Fix |
|-------------|---------|-----|
| Dual y-axis | Implies false correlation; easy to mislead | Two separate charts, or index both series |
| 3D charts | Distorts area/angle perception | Always use 2D |
| Rainbow colour maps | Not perceptually uniform; fails for colourblind | Sequential or diverging palettes |
| Truncated bar axis | Exaggerates differences | Start at zero |
| Pie with > 5 slices | Unreadable | Stacked bar or treemap |
| Spaghetti lines (>5) | Can't distinguish series | Small multiples |
| Overly dense legend | Forces eye-bouncing | Direct labels |

---

## References

- [FT Visual Vocabulary — GitHub](https://github.com/Financial-Times/chart-doctor/tree/main/visual-vocabulary)
- [From Data to Viz — Decision Tree](https://www.data-to-viz.com/)
- [Datawrapper Blog — Chart Types Guide](https://www.datawrapper.de/blog/chart-types-guide)
- [Atlassian — Essential Chart Types](https://www.atlassian.com/data/charts/essential-chart-types-for-data-visualization)
- [Atlassian — How to Choose Data Visualization](https://www.atlassian.com/data/charts/how-to-choose-data-visualization)
- [Flourish — Choosing the Right Visualization](https://flourish.studio/blog/choosing-the-right-visualisation/)
- [eazyBI — Data Visualization and Chart Types](https://eazybi.com/blog/data-visualization-and-chart-types)
- [UK Government Analysis Function — Data Visualization Charts](https://analysisfunction.civilservice.gov.uk/policy-store/data-visualisation-charts/)
- [Storytelling with Data — Cole Nussbaumer Knaflic](https://www.storytellingwithdata.com/)
- [Data-to-Viz — Pie Chart Caveats](https://www.data-to-viz.com/caveat/pie.html)
- [Highcharts — Radar Chart Explained](https://www.highcharts.com/blog/tutorials/radar-chart-explained-when-they-work-when-they-fail-and-how-to-use-them-right/)
