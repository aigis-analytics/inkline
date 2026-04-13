# Professional Exhibit Design Playbook

> **Purpose**: Translate the specific design patterns used by top-tier investment
> banks (Pareto Securities, Goldman Sachs, McKinsey, etc.) into concrete, implementable
> rules for the DesignAdvisor. These patterns were extracted from analysis of real
> institutional-grade presentations and represent the gap between amateur slide design
> and boardroom-grade output.
>
> **Key principle**: Information density is achieved through technique, not through
> reducing data. The goal is maximum data in minimum visual space, with zero
> cognitive overhead.

---

## 0. THE PRIME RULE: Exhibits Over Text, Always

A professional exhibit encodes data **visually** — in position, size, color, and shape.
Text is a label, not a vehicle for data delivery. Every time you write a sentence of
explanation, ask: could a chart, a badge, a proportional box, or a colored band say
this faster?

The hierarchy from most to least preferred:
1. **Proportional visual** (Marimekko, stacked bar, waffle — size IS the data)
2. **Positional visual** (scatter, bar, line — position IS the data)
3. **Color-encoded visual** (heatmap, treemap — hue/saturation IS the data)
4. **Structural visual** (process flow, entity diagram — relationship IS the data)
5. **Table with visual anchors** (sorted, highlighted, no prose in cells)
6. **Bullet list** — last resort; use only when structure doesn't exist

---

## 1. Axis Elimination

### Rule: Drop axes when you have direct labels

Every axis (x-axis line, y-axis line, tick marks, axis title) should be **earned** by
proving it adds information that direct labels cannot provide. In most presentation
charts, it does not. Remove it.

**When to eliminate completely:**
- Bar charts where value labels float above/inside each bar → drop y-axis entirely
- Waterfall charts where each bar is labeled → drop both axes
- Combo bar+line where bars are labeled → drop both y-axes; rely on direct labels
- Donut/pie charts → never have axes; no legend either if labels embed in segments
- Marimekko / mosaic charts → no axes at all; cell labels carry all information

**When to keep axes (with minimal styling):**
- Continuous time-series line charts spanning > 24 months → keep x-axis (dates)
- Multi-series comparative line charts → keep y-axis for relative scale reading
- Scatter plots with positional meaning → keep both axes (label them once)

**How to implement in Inkline:**
Use `ax.axis("off")` + direct `ax.text()` annotations for bar/waterfall/donut.
For time-series lines, use `ax.spines["top"].set_visible(False)` + `ax.spines["right"].set_visible(False)` and suppress all tick marks except major x-axis labels.

---

## 2. Legend Elimination

### Rule: If you can label it, you don't need a legend

A legend forces the reader to look back and forth between the chart and the key.
Every legend box is a legibility tax. Eliminate it by:

**Embedding labels in the chart:**
- Donut/pie: Place `{category}\n{pct}%` at the arc midpoint (radially, ~3pt outside the arc)
- Bar chart: Value label above bar, same color as bar — no legend for series identity
- Stacked bar: Label the dominant segment inside the bar; suppress labels for segments <8%
- Line chart with ≤3 series: End-of-line labels (right edge of chart) in the line's color
- Scatter: Label each point cluster directly (no dots — the label IS the marker)

**Logo-as-legend:**
When the series is a company/brand, use the brand logo flush-right of the chart as the
legend entry. Recognition is instant; text is not needed.

**Per-chart hue-family isolation:**
When multiple donut/pie charts appear on one slide, assign each chart its own base color
(e.g., navy family, teal family, amber family). Shades within a family distinguish
segments within one chart. This prevents cross-chart color collision without a legend.

**When a legend IS acceptable:**
- ≥4 non-obvious series in a complex line chart
- Color encodes a derived category (e.g., "high/medium/low risk") that isn't self-evident
- Chart is so small that inline labels would collide

---

## 3. Color Discipline: 3-Color Maximum

### Rule: Every color must earn its presence by encoding information

Professional institutional decks use **3–4 colors maximum** per slide. More colors
signal amateur design. Color should encode function, not decoration.

**The 3-function palette:**
1. **Primary** (dark navy): Dominant data, hero numbers, most important category
2. **Secondary** (steel blue/teal): Supporting data, secondary series
3. **Tertiary/muted** (light gray-blue): Background fills, peripheral/reference data

**Specific encoding rules:**
- Dark = large/important; Light = small/secondary. Use a single hue ramp where
  lightness encodes magnitude (darkest = biggest). Eliminates need for a legend.
- In waterfalls: use secondary brand color for negatives — NOT red (unless brand color is red).
  This keeps palette discipline. Red is too loud for financial data.
- In entity diagrams (org charts, structure charts):
  - Dark fill = focal/primary node
  - Mid-gray = intermediary
  - Light gray = peripheral/external
  - Color encodes importance tier, not category

**What NOT to do:**
- Rainbow category palettes (>4 hues)
- Decorative color on text or borders
- Different accent colors within the same card row or KPI strip
- Chart backgrounds that differ from the slide background

---

## 4. Insight-as-Headline

### Rule: The slide title is the conclusion, not the topic

A neutral title ("Revenue Overview", "Market Data") is wasted space. An action title
states the analytical conclusion the exhibit supports.

**Pattern:**
```
TOPIC TITLE:     "Nordic HY Primary Issuance"
ACTION TITLE:    "Nordic High Yield primary issuance reached record levels in 2025"
```

**Formula:**
- Subject + verb + conclusion phrase + year/timeframe (when relevant)
- Max 12–15 words; use the full title line
- Never end with a colon; never start with "A look at…" or "Overview of…"
- Font: Bold, ~32–36pt, sentence case (not all-caps)

**Section label pattern:**
Below the action title, add a 3–5 word section identifier in SMALL-CAPS, ~9pt, muted:
```
SECTION_LABEL    Action title in large bold here
```

**Pipe-delimited chart subtitles:**
Use `[Chart title] | [Unit]` as the in-chart subtitle, eliminating verbose axis titles.
Example: `Hyperscaler CAPEX | USDbn` instead of adding "USD billions" as an axis label.

---

## 5. The Commentary Column

### Rule: Dedicate ~28–30% of wide slides to a "so what" panel

When a chart or table fills ~70% of a slide, the remaining 30% should be a commentary
column that explains the analytical implication — not a repeat of the data.

**Structure:**
- Gray-background fill panel (light gray, ~#F5F5F5)
- Bold column header in a dark filled rectangle (like "COMMENTS")
- 3–5 bullet fragments (not sentences) explaining what the exhibit means
- Font: ~9–10pt; indent with em-dash list

**When to use:**
- Any slide with a single large chart that needs narrative context
- Competitive positioning slides (chart = fact, column = so what)
- Hybrid capital or deal structure slides (diagram = mechanics, column = significance)

**What NOT to do:**
- Do not use the commentary column to repeat numbers from the chart
- Do not write full sentences — use bullet fragments only
- Do not exceed 5 bullets

---

## 6. Information Density Techniques

These are specific techniques observed in professional decks that pack data without
appearing cluttered:

### 6.1 The KPI Triplet Block
Three stats in one row:
`[icon] [bold headline number] [2-word italic caption]`
- Icon: ~16px, single color (brand accent or muted)
- Number: ~28–32pt bold, dark navy
- Caption: ~9pt italic, subordinate gray
- No borders between triplets — just a thin hairline rule vertical divider

### 6.2 Tombstone Footer Strip
For track record / credentials slides:
- 6–8 equal-width cells in a horizontal row at the bottom of the slide
- Each cell: `[logo] [deal name] [4 data fields]`
- Hairline vertical separators between cells; no horizontal borders
- Alternating light-gray backgrounds for even cells (optional)
- Replaces prose with a visual credential row

### 6.3 Badge Cluster as Proof
Replace superlative prose ("Best in market", "Award-winning") with:
- `[gold ring badge] [bold numeral] [8pt institution name] [8pt award category]`
- 3 badges in a horizontal row = 3 proofs without a single sentence

### 6.4 Icon-as-Data-Column
In tables: replace a categorical text column (e.g., "HQ country") with flag icons or
sector icons. Saves ~80px column width while adding visual richness.

### 6.5 Floating Inter-Node Annotations
In entity/structure diagrams: place relationship text (contract terms, ownership %) in
the **gap between entities**, not inside boxes or in a legend. Float labels:
`[70% LTC]`, `[5-year contract]` positioned on or near the connector line.

### 6.6 Year-Grouped X-Axis
For monthly time-series spanning multiple years: show month ticks labeled only for
tick-marks at year boundaries, with year labels centered below as a secondary row.
Compresses 24+ months of data into clean, scannable width.

### 6.7 Shared Axis Lockstep
When 2–4 charts appear in a grid (2×2 or 1×4), force identical x-axis ranges so
viewers can compare across panels without re-reading axes. Best practice: same date
range, same unit family (if possible).

### 6.8 Ranked Bar + Circle Callout
In market share / competitive ranking charts: the top-ranked item gets its % label
inside a filled circle (or boxed callout). All other items get plain right-end labels.
The visual asymmetry signals market leadership without prose.

---

## 7. Exhibit Type Extensions

These are exhibit types used in professional decks that Inkline should support
**in addition to** the standard 11 chart types:

### 7.1 Marimekko / Mosaic Chart
- **Use case**: Part-of-whole breakdown where 2 dimensions encode size simultaneously
  (width = category share, height = subcategory share)
- **When to choose**: Budget breakdowns, financing mix decompositions (e.g., "$2.9tn
  financing needs: 48% hyperscaler, 28% private credit, 12% PE")
- **Key rules**: No axes, no gridlines; labels embedded inside cells; chroma decreases
  with cell size (darker = larger); max 3 colors

### 7.2 Entity / Structure Diagram
- **Use case**: Legal entity hierarchy, SPV structures, deal parties, org charts
- **When to choose**: Any slide with "who does what to whom" — lenders, sponsors,
  SPVs, counterparties, contracts
- **Key rules**:
  - Rectangular nodes, tiered gray palette (dark=focal, mid=intermediary, light=peripheral)
  - Inline connector labels (not in a legend box)
  - Dashed borders for external/passive entities; solid borders for core entities
  - Left-to-right or top-to-bottom directionality; no diagonal connections

### 7.3 Label-Positioned Scatter
- **Use case**: Pricing/positioning analysis (e.g., competitors plotted by spread vs. maturity)
- **When to choose**: Any "where does X sit vs. Y" question on 2 continuous axes
- **Key rules**:
  - NO dots/markers — the logo or company name IS the marker
  - Horizontal dashed bands (2 at most) segment the continuous Y-axis into tiers
  - Right-margin text boxes explain tier boundaries; no arrows into the chart

### 7.4 Divergent Bar Chart
- **Use case**: Net flows, inflow/outflow, positive/negative changes over time
- **When to choose**: Any time series where values can be positive OR negative in
  the same series (fund flows, inventory changes, EBITDA bridge variations)
- **Key rules**:
  - Bars above zero = primary brand color; bars below = secondary/muted
  - Value labels above/below bar tips (not inside)
  - Y-axis can be retained (baseline is inherently meaningful for divergent charts)
  - Zero baseline rule: always make the 0 line a hairline in brand accent/muted

### 7.5 Staircase / Step Line
- **Use case**: Discrete period measurements (quarterly or annual data where changes
  are sudden, not gradual interpolations)
- **When to choose**: Capex/revenue ratios by quarter, interest rate step changes,
  cohort-level metrics
- **Key rules**: Use `drawstyle='steps-post'` in matplotlib; no smoothing/interpolation
  (smooth lines imply continuous change; steps imply discrete decision points)

### 7.6 100% Stacked Horizontal Bar (Transition/Composition)
- **Use case**: Showing a shift in composition over time (e.g., crypto vs. HPC revenue,
  product mix shift, customer segment transition)
- **When to choose**: When you want to show how a composition CHANGES year-over-year
  (not just point-in-time breakdown)
- **Key rules**:
  - 2 colors only: one for "old/declining", one for "new/growing"
  - Time periods on Y-axis (categorical, not continuous)
  - Gridlines at 25% intervals, hairline weight; no bar value labels
  - Legend replaces all in-chart annotation

---

## 8. Process & Flow Diagram Standards

### Chevron-Chain Timeline
For M&A/financing deal processes (preparation → execution → close):
- 4–6 chevron-shaped header cells, each with: phase name (bold), duration label ON the
  chevron arrow, owner label (italic, parenthetical below)
- Content below each chevron: 3–5 bullet fragments in a clean column (no borders)
- Colors: active phases = dark navy; background phases = medium blue-gray

### Funnel with Lateral Timeline Spine
For lender/investor selection funnels:
- Trapezoid funnel on right (widest = start, narrowest = final)
- Vertical timeline axis on LEFT with date labels
- Terminal outcome box: dark fill with white text + bullet callouts
- Labels embedded inside each funnel tier (n = X lenders)

### Tick-Connected Waterfall Chain
For capital stack / waterfall priority displays:
- Single column of boxes, top to bottom (senior → mezzanine → equity)
- Short vertical tick marks connect boxes (not arrows — ticks imply connection without
  implying one-way flow)
- Fill gradient: darkest at top (senior/safest) → lightest at bottom (equity)
- Labels inside boxes: tranche name + amount + % (3 lines, no borders)

---

## 9. Table Design Rules

Tables are for dense reference data. When used, they must follow these rules:

1. **No gridlines** — use whitespace (generous row height ~32px) for separation
2. **Token-only cells** — max ~12 characters per cell; push explanatory text to column headers
3. **Two-tier spanning headers** — when columns group into categories (e.g., "Secured" covers
   3 columns), use a spanning header row with a distinct fill
4. **Bold total row** — dark fill + white text signals the summation row; no footnote needed
5. **Right-align numbers** — left-align text; center column headers
6. **Icon columns** — replace any text-based categorical column (geography, sector, rating)
   with an icon column; saves width and adds visual richness
7. **Detached sub-table** — when a table has two conceptually distinct sections, separate
   them with a full-width gray label row rather than a thin rule

---

## 10. Typography Discipline

### Font weight as hierarchy (not size alone)
- Level 1 (Action title): Bold, 32–36pt
- Level 2 (Section header, column header): Bold, 10–11pt, often ALL-CAPS small-caps
- Level 3 (Data labels, chart sub-titles): Regular, 9–10pt
- Level 4 (Sources, footnotes, captions): Italic, 7–8pt, muted gray

### Bold lead words in bullets
The first 2–3 words of any bullet should be **bold** and carry the key fact.
The remaining words provide supporting context in regular weight.
This allows the reader to scan headings at a glance without reading full lines.

### Abbreviation standard
- Financial years: `2025F` not "2025 Forecast"
- Currencies: `USDbn` not "USD billion", `EURm` not "EUR million"
- Time periods: `Q3 2025` not "Third quarter of 2025"
- Ranges: `2-4x` not "2 to 4 times leverage"

---

## 11. Summary: Decision Tree for Any Slide

When the DesignAdvisor receives a section to visualise, ask:

```
1. Can the data be encoded as SIZE? → Marimekko or waffle
2. Can the data be encoded as POSITION? → Bar, scatter, line
3. Is it a PART-OF-WHOLE? → Donut (embedded labels) or 100% stacked bar
4. Is it a PROCESS or RELATIONSHIP? → Chevron timeline or entity flow
5. Is it COMPARISON of discrete items? → Ranked horizontal bar + circle callout
6. Is it dense REFERENCE DATA? → Table (with icon columns, no gridlines)
7. Is it TREND over time? → Line (step for discrete, smooth for continuous)
```

In every case:
- Drop axes if direct labels exist
- Drop legends if embedding is possible
- Use ≤3 colors, functionally assigned
- Write the action title as the analytical conclusion
- If 30% of slide is empty after layout → add commentary column
```
