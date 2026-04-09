# Template Catalog & Archetype Recipes Playbook

> **Purpose**: Give the DesignAdvisor concrete, replicable recipes for the slide
> archetypes that real-world template marketplaces (SlideModel, Genspark) ship.
> Complements `slide_layouts.md` (general patterns) and `infographic_styles.md`
> (composition) by adding **structural coordinates** and **catalog references**.
>
> **How it differs from slide_layouts.md**: that playbook covers consulting-grade
> generic patterns (action titles, pyramid principle, KPI dashboard). This one
> covers *named archetypes* with replication instructions in slide-relative
> coordinates, derived from hand-analysis of ~30 representative templates.
>
> **Source**: Synthesised from 771 real templates (328 SlideModel + 128 Genspark
> Pro multi-slide decks + 315 Genspark Creative). Theme palettes pulled from real
> `theme1.xml` files in 4 free .pptx bundles.

---

## 0. Catalog access

The shipped template metadata lives at `inkline.intelligence.template_catalog`:

```python
from inkline.intelligence.template_catalog import (
    find_templates,           # filter by tag, color, slide_count, archetype
    load_manifest,            # raw JSON manifest access
    list_archetypes,          # the 16 archetypes covered in this playbook
    get_archetype_recipe,     # structured recipe for one archetype
)

# Example: find a dashboard template with a navy palette
hits = find_templates(tags=["dashboard"], color="#003366")
for t in hits[:5]:
    print(t["title"], t["palette"][:5], t["slides"][0])
```

The manifests ship inside the package (~1 MB total). Image previews are not
shipped — manifest entries contain CDN URLs you can fetch on demand. If you have
a local image catalog (e.g. for offline grounding), set the env var
`INKLINE_TEMPLATE_CATALOG_DIR` and the helpers will resolve image paths against
that directory.

---

## 1. Universal rules (extracted from real templates)

These are the rules every well-designed template in the catalog follows. They
extend the general guidance in `slide_layouts.md` with empirically-grounded
specifics.

### 1.1 Layout
1. **One hero per slide.** A single big number, one big chart, one big shape, or
   one big metaphor — the eye lands on it within ~0.5 seconds.
2. **Asymmetric is normal, symmetric is for taxonomies.** Dashboards and content
   slides use 1/3 + 2/3 splits, sidebars + grids. Symmetric circular/radial
   layouts are reserved for "N-item framework" slides.
3. **Tile grids are 2×3, 3×2, or 3×3.** Never 4×4 (too dense). Each tile has
   white background, soft border or shadow, generous internal padding.
4. **Cards float on a coloured or grey field.** White cards on `#F4F5F7`-ish
   background with a 10–20% opacity drop shadow is the modern dashboard idiom.
5. **Title bar at top, no rule line.** Slide title is a sans-serif 28–36pt,
   top-left, with 28–48px clear space below it. Underline rules are out of fashion.
6. **Equal-margin canvas.** All content sits inside a ~64px (5%) margin from the
   slide edge. Nothing is glued to the corners.

### 1.2 Type ramp (verified across 30+ templates)
| Element | Size | Weight | Notes |
|---|---|---|---|
| Hero number / KPI | 48–96pt | Bold/Black | Tabular figures |
| Slide title | 28–36pt | Bold | Top-left, ~5% margin |
| Tile section title | 14–16pt | Semibold | Title-case |
| Body / description | 9–11pt | Regular | Line-height 1.5× |
| Axis / data caption | 8–9pt | Regular | Charcoal not black |
| Section divider header | 40–48pt | Black | ALL-CAPS |

**Real on-slide fonts** (verified from .pptx XML, not theme defaults):
- Arial dominates by ~10:1 over Calibri even when Office theme says Calibri Light.
- Arial Narrow is the workhorse for tight tile labels.
- Decorative accent (rare): a single hand-drawn font like *ByTheButterfly* for
  cover slides only.
- Always set both `latin` and `ea`/`cs` typefaces with full CJK fallback chains
  (`맑은 고딕`, `宋体`, `新細明體`, `ＭＳ Ｐゴシック`, plus Indic/Thai/Cherokee fonts) so
  international platforms render predictably.

### 1.3 Palette discipline
1. **Palette size = 6–10 hex codes.** Slot 0 is almost always white. Slots 1–2
   are dominant brand hues, 4–6 supporting tints, 1–2 neutral greys.
2. **Greys do the heavy lifting.** `#FFFFFF / #F4F5F7 / #CCCCCC / #999999 / #333333`
   make up most surface area. Saturated colours are reserved for *data* and
   *call-outs*.
3. **One accent per tile.** Each KPI tile uses one of the palette colours; the
   tile next to it uses a different one. Never the same colour on adjacent tiles.
4. **Gradients are subtle.** Hero tiles use a 2-stop gradient on the same hue
   (`#66CCAA → #88DDBB`), never rainbow. Full-bleed gradients are vertical, two
   tones of the same family.
5. **Two colour modes ship together.** A well-designed template ships in both
   *light* and *dark/coloured* variants of the same layout — see §3 "two-variant
   ship pattern".

### 1.4 Theme palettes from real .pptx XML

These are pulled from actual `ppt/theme/theme1.xml` files in the SlideModel free
bundle and provide reference palettes you can adapt:

| Mood | Accent 1 | Accent 2 | Accent 3 | Accent 4 | Accent 5 | Accent 6 |
|---|---|---|---|---|---|---|
| Vibrant tech | `#16A1CA` | `#099481` | `#7DBC2D` | `#EEA720` | `#E13A62` | `#9132A6` |
| Bold marketing | `#EA3D15` | `#F99325` | `#6DAF27` | `#188ED6` | `#4EB9C1` | `#73166F` |
| Burgundy editorial | `#6C2B43` | `#DF3621` | `#FD9E01` | `#94BA46` | `#00B09B` | `#0178BC` |
| Cool corporate | `#0779B7` | `#019ADD` | `#6BC2ED` | `#A7CCDF` | `#595959` | `#3F3F3F` |
| Office defaults | `#5B9BD5` | `#ED7D31` | `#A5A5A5` | `#FFC000` | `#4472C4` | `#70AD47` |

**dk2 / lt2** for these themes is `#44546A / #E7E6E6` (Office), `#1F497D / #EEECE1`
(corporate). Hyperlink defaults: `#0563C1 / #954F72` (modern) or `#0000FF / #800080`
(legacy).

### 1.5 Iconography
- Line icons inside circles, never flat-fill icons.
- Standard slot is 24–32px square in a 40–48px circle.
- Always pair an icon with a number when both are present — the user reads
  icon→number→label in that order.
- Glyphs over photos for frameworks; photos over glyphs for marketing/luxury decks.

### 1.6 Charts
- Use the smallest chart that tells the story: sparkline > line > bar > pie >
  donut > waffle > 3D anything.
- Donut > pie, always. Donuts have a hole for a hero number.
- **Waffle/square-pie** is the right answer for tight % comparisons (49% vs 51%)
  where pie/bar fail visually. 10×10 unit grids, one stack per category.
- **Sparkline + hero number is the dashboard atom.** Mini line chart underneath
  a 48pt KPI value. Repeat 6–8 times to make a dashboard.
- Line charts have ≤4 series, one in the brand accent and the rest in muted greys.
- Bar charts use 4–6 categories, axis labels at base, data labels above the bar.
- Always label the axis even on small charts.
- No legend if you can avoid it — inline labels on chart end-points beat a legend.

---

## 2. Archetype recipes (16 patterns)

For each archetype: **what it is**, **why it works**, **structural recipe in
slide-relative coordinates** (so you can drop it into Inkline's `pptx.builder` or
`typst.slide_renderer` directly), **palette rule**, and **when to use**.

### 2.1 Iceberg / hidden-vs-visible
- **Why it works**: The metaphor instantly communicates "small visible part, big
  hidden part" and splits the slide into two coloured zones for free.
- **Recipe**:
  - Full-bleed background gradient: light blue top → deep blue bottom, transition
    at ~40% slide height (the waterline).
  - Iceberg vector at left of centre, ~40% slide width, white tip above water,
    faceted pale-blue body below.
  - Hero number 1 (visible %) upper right of the tip, ~96pt white, with `%`
    postfix at 60% of the digit size.
  - Hero number 2 (hidden %) lower left, same treatment.
  - Three KPI tiles upper area: semi-transparent white pill with rounded corners,
    line chart + 2 placeholder cards.
  - Lower area: large donut gauge centre, two arrow-up/arrow-down callouts,
    one bar chart card right.
- **Palette**: Pure blue monochrome `#003366 → #99CCFF`. White text everywhere.
- **When**: Risk reports, "what we see vs what we don't" pitches, hidden-cost
  analyses, change-management decks.
- **Avoid**: Multi-coloured palettes — the metaphor demands a single hue.

### 2.2 Sidebar profile + KPI grid
- **Why it works**: Left rail is a permanent identity anchor (photo + name +
  nav-style menu) so the right grid can change every slide while feeling like
  part of the same dossier.
- **Recipe**:
  - Left rail: 22% slide width, mint/teal gradient `#66CCCC → #88DDBB`,
    top-aligned circular profile photo in a white border, name (24pt) and
    designation (14pt), 4 nav-style placeholder rows with line-icon + label,
    soft divider, footer line of body text.
  - Right grid: 6 white cards in a 3×2 layout, 16px gutter, 12px padding.
    Top-left card spans 2 columns and contains a hero KPI (`75%`) plus area
    chart. Other cards: small bar chart, donut, secondary KPI, mint accent
    callout, mini area chart.
  - Soft drop shadow on each card (2px blur, 12% black).
- **Palette**: Mint/teal primary, white cards on `#F4F5F7`, dark slate `#2A3A4F`
  for body.
- **When**: Self-introduction, executive bio dashboards, board-member profile
  slides, single-person ownership pages.
- **Variation**: Drop the photo and reuse the rail for a logo + nav for product
  dashboards.

### 2.3 Funnel KPI strip + chart grid
- **Why it works**: The left rail communicates the conversion funnel by stage
  (Leads → Wins) using diminishing-value tiles, so you don't need a literal
  funnel shape. The right grid then expands one or two stages with charts.
- **Recipe**:
  - Left rail: 28% width. Top tile is a "headline" KPI styled in a teal-to-navy
    gradient. Below it, 5 stacked rectangular tiles each ~12% slide height — one
    per funnel stage — with stage label left, stage value right, increasingly
    darker navy.
  - Centre: 2 donut gauges, vertically stacked, each labelled, with the % in the
    donut hole.
  - Right column: 3 stacked rows, each with a person's name + sub-label +
    conversion % + sparkline.
  - Top-right: sparkline-style vertical-bar histogram for last-N-day trend
    (30 narrow bars, no x-axis ticks).
- **Palette**: Navy `#003366` to teal `#669999` monochromatic. White text on
  tiles, charcoal on white cards.
- **When**: Sales reviews, funnel optimisation, cohort breakdown, conversion-rate
  retros.
- **Critical**: Stage values must be in *decreasing* order top-to-bottom — that
  visual descent IS the funnel.

### 2.4 Multi-tile customer/persona dashboard
- **Why it works**: Packages a full customer profile into ~9 small tiles, each
  titled with a noun (Brands, Risk, Value, Activities…), so the reader can scan
  in any order and still get coherent meaning.
- **Recipe**:
  - 3-column × 3-row tile grid on white background.
  - Top-left tile: gradient header strip with circular profile photo, name
    (16pt bold), social-icon row, interest chips (5 small pill-shaped tags in
    pastel colors), tagline.
  - Each remaining tile: 14pt section title top-left, hero number top-right,
    mini-chart filling the lower 2/3.
  - Mini-chart vocabulary: horizontal bar chart, line chart, column chart, pie
    chart, line sparkline, vertical timeline, 4-icon row with badge counts.
- **Palette**: Multi-accent — magenta `#993399`, pink `#CC3399`, purple `#663399`,
  plus rainbow chart colours. Cards on white. Each chart uses *its own* dedicated
  colour, never shared.
- **When**: Customer profiles, ICP definition, user persona slides,
  account-summary one-pagers.

### 2.5 Radial framework (pinwheel / fan / petal / point)
- **Why it works**: A circle with N segments around a centre label is the most
  readable way to present 4–10 peer concepts that share a parent. The eye traces
  the circle naturally; numbers anchor reading order.
- **Recipe — pinwheel (8 items)**:
  - Donut shape centred, ~50% slide height in diameter, divided into N equal
    segments. First N/2 in one hue family (blues), second N/2 in another (greens).
  - Each segment labelled with: 2-digit number inside the segment, section title
    above the number, 1–2 line description outside the wedge, line-icon next to
    the description.
  - White circle centre with framework name in 18pt bold, 2 lines max.
  - Two side text blocks (left + right of the circle) for intro/source captions.
- **Recipe — radial fan**:
  - Two horizontal half-fans on left and right of the centre, each segment a
    coloured slice from the centre outward. Centre is a vertical pill with the
    diagram name. Labels mirrored left/right.
- **Recipe — petal**:
  - Petal shapes radiating from a central gear icon, each numbered (01–06) at
    the petal's narrow end. Labels on the slide perimeter.
- **Palette**: Either rainbow (one colour per segment) or 2-tone half-circle
  (cool/warm split). Centre stays neutral.
- **When**: N-item taxonomies, framework introductions, "the X principles of Y"
  slides.
- **Companion — spotlight drill-down**: Same diagram, all segments greyed except
  the one being discussed, which keeps its colour. Re-use this pattern for every
  detail slide that follows.

### 2.6 Hexagonal honeycomb
- **Why it works**: Hexagons tessellate perfectly with no whitespace, so 6 items
  + a centre label fit into a tight honeycomb. Visually richer than a circle.
- **Recipe**:
  - Centre hexagon: white fill, 14pt bold framework name (2 lines).
  - 6 surrounding hexagons in 6 distinct colours (cyan, blue, green, amber,
    orange, red), each with a white line-icon at top, 2-line label below.
  - Hexagons share edges with the centre — no gap.
- **Palette**: 6-colour rainbow, full saturation. Centre always white.
- **When**: Process frameworks (Design Thinking, Lean, Agile ceremonies),
  capability maps, team role diagrams.

### 2.7 Semi-circle taxonomy (large N)
- **Why it works**: When N > 8 the full pinwheel gets crowded. A semi-circle
  with items along the curve gives more room for labels and reads left-to-right
  like a process.
- **Recipe**:
  - Dotted arc from bottom-left to bottom-right of the slide, inside a 60%
    slide-width frame.
  - 12 numbered icon-circles positioned along the arc.
  - Label callouts radiate outward from each circle; alternating top/bottom
    labels keep them from colliding.
  - Centre below the arc: framework name in 16pt bold.
- **Palette**: Single brand colour for circles, charcoal for labels. Numbers in
  soft grey behind icons.
- **When**: Stages with many items (12 months, 12 dimensions, 10–14 capabilities,
  periodic-table-style maps).

### 2.8 Linear/curved process flow (curved arrows, road)
- **Why it works**: A directional shape (curving arrow / road / staircase) tells
  the reader "this happens in order, left to right."
- **Recipe — curved arrows**:
  - 4 curved arrow segments stacked diagonally from bottom-left to top-right,
    each in a different colour. Each step has number above (`STEP 01`), label
    colour-matched to the arrow, line-icon overlay, body text right.
  - Final arrow points up-and-right with a target icon, signalling completion.
- **Recipe — road**:
  - Curved black road across the slide with white dashed centre line.
  - 5 phase callouts alternating top/bottom along the road, each with a circular
    icon button, phase number, body text.
  - Start flag at left, finish pin at right.
- **Palette**: Bright multi-accent for the steps; the road/path itself is grey
  or black.
- **When**: Customer journeys, onboarding, multi-step processes, transformation
  roadmaps.
- **Critical**: First and last steps need a *visual stop* — start flag, finish
  pin, target icon — so the eye knows where to begin and end.

### 2.9 Pyramid hierarchy
- **Why it works**: The pyramid shape forces ordinal hierarchy and the visual
  mass of each level is proportional to its level — big base, small apex.
- **Recipe**:
  - Pyramid built from 5 horizontal trapezoid bands, each at a different height
    proportional to level.
  - Each band: level label inside the trapezoid (left-aligned), arrow tab
    pointing right with body text, line-icon at the right end.
  - Bottom-to-top color gradient (e.g. green foundation → blue apex).
- **Palette**: Two-hue gradient (green→blue or amber→red) across the bands.
  White or very dark text inside bands.
- **When**: Maslow-style hierarchies, capability stacks, organisational layers,
  content pyramids.

### 2.10 Vertical step model (ladder)
- **Why it works**: A literal ladder lets you label each rung as a stage in a
  process — concrete metaphor for an abstract sequence.
- **Recipe**:
  - Centre: blue ladder vector with N rungs, vertical orientation.
  - Each rung: numbered circle in white (`01`–`05`), coloured label band right.
  - Pastel colour-coding for the bands top-down.
  - Side callouts: grey "Inputs" pill on the left with curved arrows pointing
    in; coloured "Output" pill on the right with curved arrows pointing out.
  - Ellipse at the base labelled with the foundation concept.
- **Palette**: Blue ladder, pastel rung labels, grey + accent side callouts.
- **When**: Cognitive models, decision frameworks, learning ladders, escalation
  paths.

### 2.11 Petal/teardrop step diagram
- **Why it works**: Teardrop shapes radiating from a centre point feel organic
  and dynamic, more inviting than a hard pinwheel for "soft" processes.
- **Recipe**:
  - 7 teardrop shapes radiating from the slide centre, each with the point
    inward and a circular icon-bubble at the wide end.
  - Each teardrop in a different gradient hue, with the colour family rotating
    around the wheel.
  - Numbered "STEP N" pill labels on the perimeter, each colour-matched to its
    teardrop.
  - Description text beside each pill.
- **Palette**: Full saturated rainbow with gradient fill on each teardrop.
- **When**: Soft processes, organic growth journeys, design/creative workflows.

### 2.12 Funnel/conversion ribbon
- **Why it works**: Multiple input streams converging into a single output is
  the literal visualisation of a funnel — much more arresting than a triangle.
- **Recipe**:
  - 4 coloured input ribbons on the left, each labelled with `01–04` and an
    icon + text block.
  - Ribbons twist and braid in the centre of the slide, then exit to the right
    as a single twisted ribbon.
  - Two callout stalks above and two below the convergence point, each with
    body text describing what happens at the join.
- **Palette**: 4 saturated brand colours for the inputs, no neutral.
- **When**: Data integration ("4 sources → 1 warehouse"), team merging,
  capability consolidation, M&A integration.

### 2.13 Dual donut comparison
- **Why it works**: Two large donuts side-by-side invite direct comparison and
  the centre hole gives you a free hero-number slot.
- **Recipe**:
  - Two rounded-square cards centred on the slide, ~30% slide width each, 24px
    gap.
  - Each card: thick gradient-stroke donut (~40% card height), `%` value in the
    centre at 36–48pt bold, card title below the donut (16pt bold), 2-line
    caption (10pt regular).
  - Donut gradients: blue→green for one, blue→purple for the other (or matched
    to brand).
- **Palette**: White cards on white slide, donut strokes carry the colour.
- **When**: Before/after comparisons, two-quarter trends, A/B test results,
  two-segment performance.

### 2.14 Waffle / square-pie
- **Why it works**: Tight % comparisons (51% vs 49%) are invisible on a pie
  chart; a 10×10 grid makes every percentage point a counted unit.
- **Recipe**:
  - Vertical stack of N waffle-grid cards, each labelled with category name +
    count on the left.
  - Each grid is a 10×10 (or relevant rows×cols) field of small filled squares,
    with the unfilled portion in lighter shade.
  - Headline + sub-caption + source line at the slide bottom.
  - Optional 3D extrusion: slight isometric tilt, drop shadow per stack.
- **Palette**: Single hue, with the unfilled units 30% lighter than the filled
  units.
- **When**: Tight % comparisons, time allocation, headcount mix, budget split
  where the differences are small.

### 2.15 Visual metaphor backdrop (cover slides)
- **Why it works**: A whole-slide illustration creates an instant memorable mood
  that pure-data slides can't match. Used sparingly, these become the *cover*
  slides of a deck.
- **Recipe — clothesline**:
  - Light blue sky with cartoon clouds, washing-line strung across at ~30% from
    the top. 3 polaroid-style cards hanging from coloured pegs. PLACEHOLDER text
    in the peg colour.
- **Recipe — tree/world**:
  - Centred half-globe with stylised cartoon trees growing from the top. Slide
    title centred above the globe.
- **Palette**: Bright cartoon palette, never used for data slides.
- **When**: Cover slides, section dividers, hero slides for ESG / sustainability
  / wellness / educational decks.
- **Avoid**: Putting data inside an illustrated metaphor — it competes for
  attention.

### 2.16 Generic chart row
- **Why it works**: When you just need to show 3–4 charts side by side without
  dashboard chrome.
- **Recipe**:
  - Slide title top-left, optional rule line below.
  - Row of 3 or 4 charts (line, area, bar, column) all the same size and Y-scale
    style. Each chart: "Sample Text" pill caption above, 2-line description
    below in a rounded-corner outlined card. Right-arrows between cards to imply
    flow (or remove arrows if it's just a comparison).
- **Palette**: 2-3 chart colours (typically navy, mustard, teal). Charts unboxed;
  descriptions in soft outlined cards.
- **When**: Multi-chart KPI snapshots, comparison rows, "look at these together"
  data slides.

---

## 3. Cross-cutting techniques

### 3.1 Spotlight drill-down
The same N-item framework slide is reused N times, each time with all segments
greyed out except the one being discussed (which keeps its full colour). This
gives you N detail slides for free with perfect visual continuity. The
DesignAdvisor should generate spotlight variants automatically when a deck
discusses a framework's items in detail.

### 3.2 Two-variant ship pattern
Every layout should ship in *two* colour variants of the same structure: light
(white background, dark text) and dark/coloured (deep gradient, white text). The
LLM-mode DesignAdvisor should produce both when the user provides a brand with
both `light_bg` and `dark_bg` defined.

### 3.3 Hero-number atom
The smallest reusable unit: `[icon] [hero number] [label] [optional sparkline]`.
A dashboard is just 6–8 of these arranged in a tile grid. Inkline already
implements this via the `kpi_strip` and `icon_stat` slide types in
`design_advisor.SLIDE_TYPES`.

### 3.4 Section spotlight + content arc
A Genspark Pro-style 12–20 slide deck follows this spine:
1. **Cover** — full-bleed colour or photo, ALL-CAPS headline 40–60pt
2. **Section divider — Introduction** — large ALL-CAPS section label, 1-paragraph body
3. **Context / market landscape** — photo + 3-bullet block split
4. **Data slide 1** — chart 60%, headline + 3-line description 40%
5. **Data slide 2** — minimal table with column-header pill-tabs
6. **Framework / process** — single 3- to 6-step diagram
7. **Opportunities / call-out** — large headline, 2-column body, decorative shape
8. **Summary** — numbered list (01–05) with 1-line descriptions

### 3.5 Decorative shape vocabulary
Genspark decks repeatedly use the same small set of decorative elements to add
visual rhythm without clutter:
- Yellow filled circle (star burst alternative)
- Red 5-point star (single, oversized, used as a punctuation mark)
- Blue/coral wave at slide top or bottom edge
- Faint dot grid as a background texture in one corner

These elements make a deck feel "designed" rather than "templated".

---

## 4. Decision matrix — which archetype?

| User intent / data shape | Best archetype | Inkline slide_type closest match |
|---|---|---|
| Show a single big % vs hidden % | §2.1 Iceberg | dashboard (custom recipe) |
| Personal/profile bio with metrics | §2.2 Sidebar profile | split + kpi_strip |
| Sales funnel with stage detail | §2.3 Funnel KPI strip | kpi_strip + chart_caption |
| Customer/persona summary | §2.4 Multi-tile persona | dashboard / feature_grid |
| 4–10 peer items in one framework | §2.5 Radial framework | feature_grid (or custom) |
| 6 peer items, design-thinking style | §2.6 Hexagonal honeycomb | feature_grid |
| 10–14 items along a curve | §2.7 Semi-circle taxonomy | timeline (curved) |
| 3–5 step process | §2.8 Curved arrows / road | process_flow |
| 3–5 level hierarchy | §2.9 Pyramid | pyramid |
| Cognitive/decision ladder | §2.10 Vertical step ladder | pyramid (vertical variant) |
| Soft/organic process | §2.11 Petal/teardrop | process_flow (custom) |
| 4 sources → 1 output | §2.12 Funnel ribbon | chart (custom svg) |
| Two %s side by side | §2.13 Dual donut | comparison + bar_chart |
| Tight % comparison (49 vs 51) | §2.14 Waffle | bar_chart (custom waffle) |
| Cover/section divider | §2.15 Metaphor backdrop | title (with image) |
| 3–4 charts in a row | §2.16 Generic chart row | chart_caption ×N |

---

## 5. When to reach for this catalog

The DesignAdvisor should consult this playbook when:

- The user asks for a layout, dashboard, infographic, framework slide, or pitch
  deck.
- The user asks "how should I show X" where X is a comparison, taxonomy,
  process, hierarchy, KPI, funnel, or trend.
- The user supplies reference images of templates and asks DesignAdvisor to
  emulate them.
- A report-generation pipeline (Inkline-driven or wrapped by a host application)
  is about to emit a slide and the LLM has never seen this archetype before.
- The user provides `additional_guidance` mentioning "make it look like X" where
  X is a recognisable template style.

The DesignAdvisor should NOT consult this playbook when:

- The user is asking a non-visual question.
- The user has explicitly asked for a minimal, no-decoration slide.

---

## 6. Catalog manifests

The shipped manifests are at `inkline.intelligence.template_catalog`:

- `slidemodel_manifest.json` — 328 templates, hex palettes, tags, item IDs,
  slide counts, gallery URLs
- `genspark_professional_manifest.json` — 128 multi-slide decks, 12–20 page
  screenshot URLs each
- `genspark_manifest.json` — 315 single-slide creative templates

Use the helper functions in `inkline.intelligence.template_catalog` to query
them rather than parsing the JSON yourself — that way the schema can evolve
without breaking callers.

---

## 7. References

- SlideModel: https://slidemodel.com
- Genspark AI Slides: https://www.genspark.ai/ai_slides
- Theme palettes: extracted from `ppt/theme/theme1.xml` in 4 free SlideModel
  bundle files.
- Catalog scraped 2026-04-09. Manifests are static snapshots at that date.
- Existing related Inkline playbooks: `slide_layouts.md`, `infographic_styles.md`,
  `color_theory.md`, `typography.md`.
