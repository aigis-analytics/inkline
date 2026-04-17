# Inkline Design Sources and Philosophy

**Date:** 17 April 2026
**Status:** Living document — update as new sources are incorporated
**Scope:** Complete audit of every external design source, reference, and inspiration in
the Inkline codebase, plus research-backed recommendations for improving the design
intelligence layer

---

## Table of Contents

1. [The Design Source Map](#1-the-design-source-map)
2. [Consulting Firm Design DNA](#2-consulting-firm-design-dna)
3. [Information Design Authorities](#3-information-design-authorities)
4. [Design System References](#4-design-system-references)
5. [Template and Archetype Sources](#5-template-and-archetype-sources)
6. [Chart and Visualization Sources](#6-chart-and-visualization-sources)
7. [Typography Sources](#7-typography-sources)
8. [Colour Theory Sources](#8-colour-theory-sources)
9. [Anti-Pattern Sources](#9-anti-pattern-sources)
10. [The Impeccable Influence](#10-the-impeccable-influence)
11. [How the Sources Fit Together](#11-how-the-sources-fit-together)
12. [Gaps: Mentioned but Not Yet Implemented](#12-gaps-mentioned-but-not-yet-implemented)
13. [Design Thinking Improvements (Research-Backed)](#13-design-thinking-improvements-research-backed)

---

## 1. The Design Source Map

This table catalogues every named external source found in the Inkline codebase, across
all Python files, playbooks, and plan_docs specs.

| Source | Where Referenced | Role in Inkline |
|--------|-----------------|-----------------|
| **McKinsey & Company** | `mckinsey.py` template, `slide_layouts.md`, `professional_exhibit_design.md`, `design_advisor.py` playbook refs | Primary reference for consulting slide anatomy and action titles |
| **BCG (Boston Consulting Group)** | `slide_layouts.md`, `professional_exhibit_design.md` | Secondary consulting reference; BCG "smart simplicity" style |
| **Bain & Company** | `slide_layouts.md` | Tertiary consulting reference; balanced text/visual approach |
| **Goldman Sachs** | `taste_enforcer.py` (R-08: "Pareto/Goldman standard"), `design_advisor.py` ("FT/Bloomberg/Goldman standard") | Axis elimination standard for bar and line charts |
| **Pareto Securities** | `design_system_spec.md` source_decks field, `professional_exhibit_design.md` intro | Primary reference deck; 15 patterns extracted (PT-1→PT-15) |
| **Barbara Minto / Pyramid Principle** | `slide_layouts.md` (cited as authority), `design_advisor.py` narrative references | Top-down narrative structure; SCR framework |
| **FT Visual Vocabulary** | `chart_selection.md` (cited as authority) | Nine data-relationship categories; chart selection framework |
| **Edward Tufte** | Implicitly throughout; data-ink ratio concept in `quality_scorer.py` scoring | Data-ink ratio; chartjunk elimination; information density |
| **Cole Nussbaumer Knaflic (Storytelling with Data)** | `chart_selection.md` (cited as authority) | Chart selection discipline; action titles; audience framing |
| **Datawrapper Chart Guide** | `chart_selection.md` (cited as authority) | Chart selection validation |
| **UK Government Analysis Function** | `chart_selection.md` (cited as authority) | Accessibility and clarity standards |
| **ColorBrewer (Cynthia Brewer)** | `color_theory.md` (cited as authority) | Sequential, diverging, qualitative palettes |
| **WCAG 2.1** | `color_theory.md` (cited as authority) | Accessibility contrast requirements |
| **Atlassian Data Visualization Guide** | `color_theory.md` (cited as authority) | Brand colour discipline |
| **Untitled UI** | `design_tokens_spec.md` ("Inspired by Untitled UI design system, 320K users") | 12-shade colour ramp; named type scale; 4px spacing grid |
| **Impeccable (pbakaus/impeccable)** | `impeccable_design_intelligence_spec.md` ("Inspired by Impeccable — 18 design commands for AI-generated UIs") | Anti-pattern library; quality scoring; auto-polish; design brief |
| **SlideModel** | `template_catalog/__init__.py` (328 templates scraped) | Infographic archetype references; design vocabulary |
| **Genspark Professional** | `template_catalog/__init__.py` (128 multi-slide decks) | Real-world deck layout patterns |
| **Genspark Creative** | `template_catalog/__init__.py` (315 single-thumbnail templates) | Creative archetype vocabulary |
| **getdesign.md** | `design_md_styles/__init__.py` ("Source: https://getdesign.md — 66 open-source design system specs, 27 curated") | 27 company design systems (Stripe, Vercel, Apple, etc.) |
| **Slidor** | `typography.md` (cited as authority) | Font pairing guidance |
| **Figma resource library** | `typography.md` (cited as authority) | Typography references |
| **IBM Carbon / Material / Apple HIG / Salesforce Lightning** | `color_theory.md` | Brand colour discipline standards |
| **Launchpad brochure** | `design_system_spec.md` source_decks field | 9 patterns extracted (LP-1→LP-9) |

---

## 2. Consulting Firm Design DNA

### 2.1 McKinsey

McKinsey is the dominant consulting reference in Inkline. A dedicated template
(`slides/templates/mckinsey.py`) implements their visual signature: white background,
dark navy/charcoal text (`#1A2332`), teal accent (`#0891B2`), orange for warnings
(`#EA580C`). Structural elements follow the firm's practice precisely: full-width teal
bars at top and bottom, an accent dash left of every content title, source citation
line at the bottom, and muted slide numbers at bottom-right.

The more significant McKinsey influence is structural. The Pyramid Principle (Barbara
Minto, who developed it at McKinsey) governs the narrative framework in `slide_layouts.md`:
top-down argument structure, action titles that state the conclusion not the topic, and
the three-zone anatomy (action title / exhibit / provenance footer) that every consulting
slide uses. The SCQA opening structure (Situation → Complication → Question → Answer)
appears in `slide_layouts.md` as the recommended presentation opening.

**Where implemented:**
- `slides/templates/mckinsey.py` — visual template
- `slide_layouts.md` playbook — Pyramid Principle, action title rules, three-zone anatomy
- `design_advisor.py` SLIDE_TYPE_GUIDE — "Action titles: state the CONCLUSION, not the topic"
- `professional_exhibit_design.md` section 4 — Insight-as-Headline rule

### 2.2 BCG

BCG's "smart simplicity" — more visual and chart-driven than McKinsey, with bold callouts
highlighting key data — is cited as a secondary reference in `slide_layouts.md`. BCG's
specific contribution to Inkline's philosophy is the emphasis on charts over text, which
is encoded in the VISUAL HEROES priority ordering in `design_advisor.py` and the 60%
visual-type slide requirement. BCG's "squint test" (key messages must be discernible when
squinting) maps to Inkline's at-a-glance scanability requirement ("a great Inkline slide
is SCANNABLE in 3 seconds").

**Where implemented:**
- `slide_layouts.md` — BCG style cited alongside McKinsey and Bain
- `design_advisor.py` SLIDE_TYPE_GUIDE — "AT LEAST 60% of content slides must be visual layouts"
- `vishwakarma.py` — HARD RULE: "A deck where ≥ 20% of slides are 'content' has FAILED"

### 2.3 Goldman Sachs / Pareto Securities (Investment Banking Standard)

Two investment banks provide the most specific chart-grammar rules in Inkline:

**Goldman Sachs** is cited by name for the axis elimination standard in two places:
`design_advisor.py` ("FT/Bloomberg/Goldman standard") and `taste_enforcer.py`
(Rule R-08: "Pareto/Goldman standard: clean line on bottom/left axes only"). This rule
enforces the institutional practice of suppressing right and top spines on line charts.

**Pareto Securities** is cited as a primary reference deck source in `design_system_spec.md`,
contributing 15 named patterns (PT-1 through PT-15) to the initial decision matrix.
`professional_exhibit_design.md` cites "Pareto Securities, Goldman Sachs, McKinsey" in
its opening as the sources from which patterns were extracted.

The `taste_enforcer.py` references "PT-14" (donut direct labels) and "PT-4" (annotated
scatter) directly in its rule comments, showing the traceability from real deck analysis
to enforced code rules.

**Where implemented:**
- `typst/taste_enforcer.py` — R-08 (line chart spine elimination), PT-14 (donut labels), PT-4 (scatter)
- `professional_exhibit_design.md` — all 11 sections derive from IB deck analysis
- `design_system_spec.md` — decision_matrix_default.yaml seeds from Pareto patterns

---

## 3. Information Design Authorities

### 3.1 Edward Tufte

Tufte is the most pervasive theoretical influence on Inkline, even though he is never cited
by name in the code. His two core concepts govern major design decisions:

**Data-ink ratio** (maximise the proportion of ink encoding actual data, erase non-data-ink)
is the theoretical foundation for:
- Axis elimination rules in `taste_enforcer.py` (R-01, R-02, R-08)
- The `quality_scorer.py` "Data-Ink Ratio" scoring dimension (20% weight), which directly
  measures what percentage of slides are visual vs. text
- The `professional_exhibit_design.md` section 1 (Axis Elimination) — "every axis should
  be **earned** by proving it adds information that direct labels cannot provide"
- The FORBIDDEN PATTERNS list in `design_advisor.py`

**Chartjunk** (decorative elements that add visual noise without information) is the
foundation for:
- `anti_patterns.py` CP-* (Colour & Visual Patterns) — specifically CP-04 (legend when
  direct labels would work)
- `taste_enforcer.py` R-06 (suppress panel chart titles that duplicate the header)
- The `color_theory.md` "Forbidden patterns" list

### 3.2 Cole Nussbaumer Knaflic (Storytelling with Data)

Knaflic is cited directly in `chart_selection.md` as an authority source. Her core
philosophy — "simple beats sexy", eliminate clutter, focus attention strategically — maps
to several Inkline systems:

**Selective attention / pre-attentive attributes:** The accent_index system in grouped_bar
charts (one bar highlighted, all others muted) is Knaflic's signature technique for
directing the reader's eye to the most important data point. `taste_enforcer.py` R-05
auto-infers which bar should receive the accent.

**Audience-first design:** The `design_advisor.py` `audience` parameter, and the
`design_brief.py` concept of generating an audience profile before DesignAdvisor runs,
directly implements Knaflic's audience-framing principle.

**Action titles (insight headlines):** Knaflic's rule to write titles as insight
statements rather than topic labels is encoded in `design_advisor.py`, `anti_patterns.py`
TP-02 (flag generic titles), and `professional_exhibit_design.md` section 4.

### 3.3 Financial Times Visual Vocabulary

The FT Visual Vocabulary — a framework developed by the FT's graphics desk to create a
common chart-selection language in their newsroom — is cited as an authority in
`chart_selection.md`. Its nine data-relationship categories structure the first layer
of the chart selection decision tree:

| FT Category | Inkline Mapping |
|-------------|----------------|
| Deviation | `divergent_bar` |
| Correlation | `scatter` (annotated) |
| Ranking | `grouped_bar` (clean, with accent) |
| Distribution | `scatter`, `heatmap` |
| Change over time | `line_chart`, `area_chart`, `waterfall` |
| Part-to-whole | `donut`, `stacked_bar`, `marimekko` |
| Magnitude | `grouped_bar`, `kpi_strip`, `icon_stat` |
| Flow | `entity_flow`, `sankey` |
| Spatial | (future: map) |

The three-question decision framework in `design_advisor.py` (STEP 1: data shape →
STEP 2: message type → STEP 3: mandatory parameters) is a condensed operational
version of the FT Visual Vocabulary approach.

---

## 4. Design System References

### 4.1 Untitled UI

`design_tokens_spec.md` explicitly states "Inspired by Untitled UI design system
(320K users, 10K components, 4px grid)." Untitled UI contributes three specific
technical systems to Inkline:

**12-shade colour ramps:** The shade scale (25, 50, 100, 200, 300, 400, 500, 600,
700, 800, 900, 950) where 500 is the brand colour is taken directly from Untitled UI
(which shares this scale with Tailwind CSS). The HSL-based generation algorithm in
`brands/color_ramp.py` follows the Untitled UI approach of auto-generating semantically
useful shades from a single declared colour.

**Named typography scale:** The 12-level scale (display_xl → overline) mirrors
Untitled UI's font-size naming conventions. The ratio relationships between levels
(display_xl = heading × 1.57) are tuned to produce the same visual hierarchy.

**4pt spacing grid:** Untitled UI's foundational grid (multiples of 4: 4, 8, 16, 24,
32, 48, 64) is adopted directly as `SpacingScale` in `brands/__init__.py`.

**Where implemented:**
- `brands/color_ramp.py` — HSL ramp generator
- `brands/__init__.py` — `TypeScale`, `SpacingScale`, computed properties
- `typst/theme_registry.py` — token emission into Typst template variables

### 4.2 The 27 Company Design Systems (via getdesign.md)

`design_md_styles/__init__.py` sources from `https://getdesign.md`, a repository of
open-source design system specifications. Inkline curates 27 of these into the
`dmd_*` template series. The companies and their primary contribution:

**Fintech/Premium tier** — the template group `dmd_stripe`, `dmd_coinbase`, `dmd_revolut`:
Purple/blue accent palettes, weight-300 display headlines, and the "serious money"
aesthetic. Stripe's design system contributes the concept of generous whitespace with
a single strong typographic hierarchy — a principle directly useful for financial decks.

**Developer/Dark tier** — `dmd_vercel`, `dmd_cursor`, `dmd_warp`, `dmd_supabase`,
`dmd_raycast`: Monochrome or dark-mode palettes (Vercel's `#000000` / `#FFFFFF`
contrast, Supabase's `#1C1C1C`), Geist and monospace fonts, emerald or amber accents.
Vercel's design system specifically demonstrates that near-zero colour usage combined
with exceptional typography creates a premium feel.

**Consumer/Warm tier** — `dmd_airbnb`, `dmd_notion`, `dmd_spotify`: Friendly rounded
elements, warm typography. Notion's `Inter` / `#191919` palette demonstrates that
near-neutral colour plus excellent spacing beats colourful complexity.

**Editorial/Minimal tier** — `dmd_apple`, `dmd_tesla`, `dmd_framer`: Extreme whitespace,
SF Pro and custom display fonts, photographic hero sections. Apple's design system
encodes the principle that each element on a page should be able to justify its presence
or be removed.

**Where implemented:**
- `intelligence/design_md_styles/` — all 27 style definitions
- `typst/theme_registry.py` — DESIGN_MD_TEMPLATES merged into SLIDE_TEMPLATES
- `app/cli.py` — `--template dmd_*` argument support
- `intelligence/design_advisor.py` — `get_playbook_text()` injected into system prompt

### 4.3 IBM Carbon, Apple HIG, Material Design, Salesforce Lightning, GOV.UK

These five major design systems are cited collectively in `color_theory.md` as the
authority for the 2-3 colour brand discipline rule ("This is non-negotiable best practice
across every major design system"). They are not individually implemented but serve as
the collective weight of authority behind the colour rules.

---

## 5. Template and Archetype Sources

### 5.1 SlideModel Catalog (328 templates)

`template_catalog/__init__.py` contains a scraped manifest of 328 SlideModel templates,
filtered by the `infographics` and `data-visualization` tags. These provide:
- Hex palettes (extracted from page metadata)
- Tag classifications (dashboard, timeline, comparison, etc.)
- Slide count and format metadata
- Gallery image CDN URLs for visual reference

The template catalog enables `find_templates()` to locate design precedents by colour,
category, or tag — a "show me something like this" capability for the DesignAdvisor.

### 5.2 Genspark Professional (128 decks) + Genspark Creative (315 templates)

Two AI-generated template corpora that expand the design vocabulary. Genspark
Professional provides multi-slide deck structure references (12-20 pages per deck).
Genspark Creative provides diverse single-slide compositional patterns. Neither carries
colour metadata (UUID + title only), but they add breadth to title-based search.

### 5.3 The 16 Named Archetypes

Inkline's `ARCHETYPES` dict in `template_catalog/__init__.py` defines 16 named
infographic patterns. These are synthesised from SlideModel and Genspark analysis,
not from a single source. Each archetype has a `palette_rule`, `layout` descriptor,
and `inkline_slide_type` mapping:

| Archetype | Visual Concept | Origin Type |
|-----------|---------------|-------------|
| `iceberg` | Hidden-vs-visible split | Consulting (hidden cost analysis) |
| `sidebar_profile` | Rail + KPI grid | Executive biography slides |
| `funnel_kpi_strip` | Funnel with donuts | Sales pipeline visualisation |
| `persona_dashboard` | 3x3 tile grid | Product / UX research |
| `radial_pinwheel` | Donut with 8 segments | Framework / taxonomy |
| `hexagonal_honeycomb` | Hex tile grid | Capability mapping |
| `semicircle_taxonomy` | Dotted arc with radial callouts | 12-item frameworks |
| `process_curved_arrows` | Diagonal curved flow | Customer journey |
| `pyramid` | 5 trapezoid bands | Strategic hierarchy |
| `ladder` | Central ladder with side callouts | Decision escalation |
| `petal_teardrop` | Radial teardrops | Organic growth / iterative process |
| `funnel_ribbon` | Braided ribbon funnel | M&A / data integration |
| `dual_donut` | Two centred rounded cards | Before/after comparison |
| `waffle` | 10x10 square grids | Tight percentage comparison |
| `metaphor_backdrop` | Full-bleed illustration | Cover / section divider |
| `chart_row` | Row of 3-4 charts | Multi-metric snapshot |

---

## 6. Chart and Visualization Sources

### 6.1 Pareto Securities Reference Deck (15 patterns)

The most operationally specific source in Inkline. `design_system_spec.md` states that
the initial decision matrix seeds from "Pareto DC financing deck (15 patterns, PT-1→PT-15)"
and "Launchpad brochure (9 patterns, LP-1→LP-9)." Taste enforcer rules reference these
pattern IDs directly:

- PT-4: Named scatter points use annotated callout labels (R-04)
- PT-6: Panel charts suppress embedded titles (R-06)
- PT-14: Donut with ≤6 segments uses direct radial labels (R-03)

These patterns represent real institutional decisions from an investment banking
presentation, extracted by manual analysis and encoded as deterministic rules.

### 6.2 Vishwakarma Visual Hierarchy (Original to Inkline)

The Vishwakarma hierarchy in `vishwakarma.py` is Inkline's own synthesis — a tiered
priority system (Tier 1C through Tier 5) that governs every layout decision. Its name
references the Hindu divine architect. The hierarchy itself is an original formulation
that synthesises the consulting firm influence (prefer multi-exhibit layouts, data density)
with Tufte (information density through technique) and Knaflic (no text when a visual fits).

The five tiers:
- **1C** (highest): Multi-exhibit slide with 2-4 related facets consolidated
- **1B**: Structural infographic (iceberg, waffle, ladder, etc.)
- **1A**: KPI callout (kpi_strip, icon_stat, feature_grid)
- **2**: Institutional exhibit (chart_caption, dashboard, marimekko)
- **3**: Structural visual (timeline, three_card, four_card)
- **4**: Data table
- **5** (last resort): Text bullets

### 6.3 matplotlib (Chart Rendering Engine)

All charts in Inkline are rendered via matplotlib (`chart_renderer.py`,
`charts/interactive.py`). The "clean" style (`style: "clean"`) is Inkline's bespoke
matplotlib configuration that eliminates axis chrome to produce the Goldman/Pareto
institutional look: no y-axis, no gridlines, value labels floating above bars. This
is not borrowed from a source — it is an original implementation of a widely-known
institutional standard.

### 6.4 Additional Exhibit Types from Institutional Analysis

`professional_exhibit_design.md` section 7 documents exhibit types extracted from
institutional deck analysis that extend Inkline's standard repertoire:

- Marimekko / Mosaic Chart — two-dimensional part-of-whole; cited in the playbook as
  used in "financing mix decompositions"
- Entity / Structure Diagram — legal entity hierarchy and SPV structures; implemented
  as `entity_flow`
- Label-Positioned Scatter — where the company name IS the marker, not a dot
- Divergent Bar — net flows, implemented as `divergent_bar`
- Staircase / Step Line — discrete period measurements
- 100% Stacked Horizontal Bar — composition shift over time, implemented as
  `horizontal_stacked_bar`

---

## 7. Typography Sources

### 7.1 Slidor, Whitepage Studio, Figma, Canva, TypeType, Monotype

`typography.md` cites these six sources for the font classification reference, pairing
rules, and type scale. Their collective contribution:

**Font classification table** (Serif / Sans-serif / Slab serif / Monospace / Display) and
the sub-category taxonomy (Humanist vs. Geometric vs. Grotesque within sans-serif; Old-style
vs. Transitional vs. Modern within serif) — this governs how the DesignAdvisor reasons
about brand font characteristics.

**Pairing strategies** — the five canonical pairing approaches (Serif heading + Sans body;
Geometric + Humanist; Bold + Light weight contrast; Superfamily usage) are drawn from
Slidor and Canva's documented pairing guides.

### 7.2 Source Sans Pro (Default Brand Font)

Inkline's default brand (`minimal`) uses Source Sans Pro (SIL Open Font License), which
appears as the body font throughout slide templates. Source Sans Pro is an Adobe-developed
humanist sans-serif designed specifically for readability in UI contexts — a deliberate
choice for legibility at small sizes in dense slides.

### 7.3 Typst's Font System

The underlying Typst typesetting engine provides the rendering backend. Typst ships
with Source Sans 3 (the updated Source Sans Pro) as its default, and Inkline's
`slide_renderer.py` depends on this. The 45-character slide title limit in
`design_advisor.py` is derived from real font math: "22pt bold Source Sans 3 at
22.6cm → 48 chars theoretical; 45 with safety."

---

## 8. Colour Theory Sources

### 8.1 ColorBrewer (Cynthia Brewer, Penn State)

`color_theory.md` cites ColorBrewer as an authority. ColorBrewer's primary contribution
to Inkline is the three-palette taxonomy that underpins all chart colour decisions:
- **Sequential** — single hue, light-to-dark (used for ordinal/continuous data)
- **Diverging** — two hues meeting at a neutral midpoint (used for deviation charts)
- **Qualitative** — distinct hues for categorical data (used sparingly, only when
  categories genuinely need to be told apart)

### 8.2 WCAG 2.1 (W3C)

Cited in `color_theory.md` as an authority for accessibility requirements. WCAG 2.1
Level AA requires 4.5:1 contrast ratio for normal text and 3:1 for large text. This
is referenced in the playbook's accessibility section, though Inkline does not yet have
automated contrast checking.

### 8.3 The 60-30-10 Rule

The 60-30-10 colour rule appears in three places:
- `color_theory.md` as a core principle
- `two_agent_design_loop_spec.md` as one of the consulting design principles the
  Auditor enforces
- `vishwakarma.py` SCORING section ("60% background, 30% surface, 10% accent")

This rule originates in interior design (often attributed to the design principle that
three-value compositions feel balanced) and has been adopted widely in graphic design.
Inkline applies it to slide space allocation: 60% background, 30% card/surface fills,
10% accent highlight.

---

## 9. Anti-Pattern Sources

### 9.1 The Impeccable Project (pbakaus)

`impeccable_design_intelligence_spec.md` explicitly credits the Impeccable GitHub
project as inspiration: "Inspired by Impeccable — 18 design commands for AI-generated
UIs." Impeccable is a set of slash-command prompts designed to fix the specific failure
modes of AI-generated user interfaces.

Inkline's adaptation translates the web-UI commands into slide-spec equivalents:
- `/audit` → `anti_patterns.py` check_anti_patterns()
- `/critique` → visual_auditor (overflow_audit.py)
- `/distill` → `polish.py` PL-01 (trim long titles), PL-02 (trim verbose bullets)
- `/quieter` → taste_enforcer rules (remove chart decoration)
- `/shape` → `design_brief.py` generate_brief()
- `/typeset` → type_scale system (design_tokens_spec.md)

### 9.2 The Anti-Pattern Catalogue (Original Synthesis)

The 24 anti-patterns in `anti_patterns.py` (LP-*, TP-*, CP-*, DP-*, SP-* categories)
are an original synthesis from multiple sources:
- **Layout Patterns (LP-*)** — derived from consulting firm slide sequence analysis
  (3+ consecutive text slides, no visual in first 3 slides)
- **Typography Patterns (TP-*)** — from `professional_exhibit_design.md` section 4
  and consulting firm title discipline
- **Colour Patterns (CP-*)** — from Tufte (chartjunk), Inkline's own colour rules
- **Data Patterns (DP-*)** — from Knaflic (numbers in prose should be hero-formatted)
  and Tufte (right chart for data shape)
- **Structural Patterns (SP-*)** — empirical (deck too thin/long, no chart in deck)

---

## 10. The Impeccable Influence

Impeccable (https://impeccable.style) deserves a dedicated section because its influence
on Inkline's design intelligence architecture is structural, not just cosmetic.

Impeccable's core insight is that AI systems fail at design not because they lack
capability, but because they lack **structured vocabulary for design decisions**. The
project's 18 commands each target a specific failure mode of AI-generated UIs. Inkline
adapts this philosophy for document/slide generation:

**Deterministic over LLM for quality enforcement.** Impeccable's commands are
deterministic rules applied after generation, not prompts for better generation.
Inkline's `anti_patterns.py`, `quality_scorer.py`, `polish.py`, and `taste_enforcer.py`
all implement this principle — they are pure Python, no LLM calls.

**Vocabulary injection beats model capability.** Impeccable's research showed "a 59%
improvement comes from vocabulary injection rather than a more powerful model." Inkline
encodes this as the SLIDE_TYPE_GUIDE and VISHWAKARMA_SYSTEM_PREAMBLE — structured
vocabulary injected into every DesignAdvisor prompt to constrain and direct LLM choices.

**The /shape interview before generation.** Impeccable's `/shape` command conducts a
structured discovery interview (purpose, audience, constraints) before any design work
begins. Inkline's `design_brief.py` implements the equivalent for slide decks — generating
an audience profile, story arc, and visual strategy before DesignAdvisor's Phase 1 planning.

**Specific improvement commands, not vague "make it better."** Impeccable's `/bolder`,
`/quieter`, `/typeset` are surgical. Inkline's polish rules (PL-01 through PL-12) are
the equivalent: each rule targets one specific quality issue with a deterministic fix.

---

## 11. How the Sources Fit Together

The Inkline design philosophy is a three-layer synthesis:

```
LAYER 1 — THE STANDARD (what good looks like)
  Consulting firms (McKinsey, BCG, Goldman): Narrative structure, action titles,
  information density, the chart-over-text imperative
  ↓ encoded in: SLIDE_TYPE_GUIDE, VISHWAKARMA hierarchy, slide_layouts playbook

LAYER 2 — THE DISCIPLINE (rules that make it consistent)
  Tufte: data-ink ratio, chartjunk elimination
  Knaflic: audience framing, selective attention, action titles
  FT Visual Vocabulary: nine data-relationship categories
  ↓ encoded in: taste_enforcer.py, anti_patterns.py, chart_selection playbook

LAYER 3 — THE EXECUTION (tools that implement it)
  Untitled UI: colour ramps, type scale, spacing grid
  Design.md systems (Stripe, Vercel, etc.): brand aesthetic templates
  Impeccable: deterministic quality enforcement, vocabulary injection
  SlideModel/Genspark: archetype vocabulary, template precedents
  ↓ encoded in: brands/, design_md_styles/, template_catalog/, polish.py
```

The unifying principle across all three layers: **information density achieved through
technique, not through reduction.** The goal is maximum data in minimum visual space
with zero cognitive overhead. Every source — whether consulting firm, information design
theorist, or design system — contributes a specific technique for achieving this.

---

## 12. Gaps: Mentioned but Not Yet Implemented

These sources appear in specs or code comments but do not yet have full implementations:

| Gap | Where Mentioned | What's Missing |
|-----|----------------|----------------|
| **Decision matrix YAML** | `design_system_spec.md` — full spec written | `decision_matrix_default.yaml` file not yet built; rules reference it but file doesn't exist |
| **DeckAnalyser** | `design_system_spec.md` section 4 — PDF ingestion pipeline | `deck_analyser.py` exists as a file but the full implementation (chart type detection heuristics, pattern extraction) is not complete |
| **Reference deck ingestion MCP tool** | `design_system_spec.md` section 4.1 | `inkline_ingest_reference_deck()` MCP tool not yet added to `mcp_server.py` |
| **Self-learning feedback loop** | `design_system_spec.md` section 3; `visual_auditor_self_learning_spec.md` | `aggregator.py` not yet implemented; feedback_log.jsonl schema defined but not wired |
| **Pattern memory** | `visual_auditor_self_learning_spec.md` section 4 | `pattern_memory.py` module exists as a stub; per-brand YAML storage not operational |
| **Two-agent design dialogue** | `two_agent_design_loop_spec.md` | `revise_slides_from_review()` not yet added to DesignAdvisor; Auditor still produces unstructured text output |
| **Design tokens in Typst templates** | `design_tokens_spec.md` non-goals: "No template migration" | Colour ramps, type scale, and spacing tokens are computed but templates still use hardcoded values |
| **OKLCH colour space** | `design_tokens_spec.md` non-goals | Noted as a future enhancement; current ramp uses HSL |
| **`inkline learn` CLI command** | `design_system_spec.md` task 9 | CLI command for full aggregation pass not yet added |
| **Implicit feedback parser** | `design_system_spec.md` section 3.5 | Bridge regex patterns defined but not wired into feedback loop |

---

## 13. Design Thinking Improvements (Research-Backed)

This section synthesises current best-in-class thinking on presentation design, data
visualisation, and LLM prompting for design, with concrete recommendations for Inkline.

---

### 13.1 Consulting Firm Design: What Top Firms Do That Inkline Can Learn From

**BCG's "Smart Simplicity" in practice.** Analysis of real BCG presentations reveals
that BCG's most effective slides do something Inkline currently does inconsistently:
they eliminate ALL supporting text from chart slides. When a chart slide has a callout
strip, BCG's comment column contains bullet *fragments* — 4-6 words each, never sentences.
Inkline's `chart_caption` and `dashboard` layouts allow full sentences in the bullets
array. The polish rule PL-02 (trim verbose bullets to first sentence) should be
tightened: chart-context bullets should be trimmed to fragment style, not just sentence
truncation.

**McKinsey's "so what" test is not yet automated.** McKinsey's core rule is that every
slide title must pass the "so what" test — the reader must be able to ask "so what?"
and find the answer in the title itself. Inkline's anti-pattern TP-02 flags generic
titles ("Overview", "Summary", "The Problem") but does not positively verify that the
title states a conclusion. A stronger check: action titles should contain at least one
of (a) a number/metric, (b) a comparison word (more, fewer, higher, faster), or
(c) a direction word (grew, declined, exceeded, fell). Titles without any of these
are likely topic labels, not insight statements.

**Bain's appendix-first design.** Bain consultants structure decks so that every supporting
detail lives in the appendix, and the main deck contains ONLY what is needed for
the decision. Inkline has no appendix concept. The `anti_patterns.py` SP-01 (deck
>25 slides) is a crude proxy. A better rule: if >30% of slides are `content` or
`table` type and fewer than 30% are Tier 1C multi-chart layouts, the deck has an
appendix problem — too much supporting detail in the main body.

**Recommendation:**
- Add TP-07 to `anti_patterns.py`: "Title without metric, comparison, or direction
  word is likely a topic label, not an action title. Severity: warning."
- Add SP-05: "Deck with >30% content/table slides and <15% multi_chart slides may
  need appendix separation."
- Tighten PL-02 so chart-context bullets are reduced to 5-8 word fragments (not
  full sentences).

---

### 13.2 Information Design: Tufte, Knaflic, and What Research Confirms

**The "memorable visualization" research (Borkin et al., 2013, MIT / Harvard).**
This landmark study of 2,070 visualizations found that memorability is determined
at first glance — a visualisation memorable at one second of exposure was equally
memorable after ten seconds. This has a strong implication for Inkline:

The quality scorer's `Visual Variety` dimension rewards diverse slide types, but this
research suggests the more important dimension is **distinctiveness per slide**: does
each slide have a visual element that is immediately recognisable and unique within
the deck? Two `chart_caption` slides with the same layout are not memorable even if
the data differs.

Key factors that improve memorability from the Borkin research:
1. **Colour** — strategic use of colour makes charts more memorable. Inkline's
   accent_index (one bar highlighted) is correct. The research implies the highlight
   should be genuinely distinctive (high contrast), not just a slightly different shade.
2. **Recognisable objects and pictograms** — charts with embedded icons or pictograms
   (like `icon_stat`) are significantly more memorable than abstract bars. Inkline's
   decision to prioritise `icon_stat` over `content` slides in the visual hierarchy
   is research-backed.
3. **Strategic redundancy** — encoding the same data in two ways (a bar chart AND
   the number printed above) improves recall. `dashboard` (chart + stat callouts) and
   `chart_caption` (chart + insight bullets) implement this. The `stat` slide (hero
   numbers only, no chart) is the weakest for memorability because it offers no
   redundant encoding.
4. **Titles and text annotations** — effective titles dramatically improve both
   understanding and recall. This validates the action title discipline: it is not
   just a consulting convention; it is cognitively effective.

**Knaflic's 2025 addition: AI auditing.** Knaflic's updated "Storytelling with Data"
(2025 edition) adds a chapter on human-AI collaboration, specifically warning against
"letting tools dictate story structure." For Inkline, this is a direct caution: the
DesignAdvisor must never drive narrative from the data shape alone — the human's stated
goal and audience must shape the story arc first. The `design_brief.py` Phase 0
addresses this correctly. It should be non-optional for multi-section decks.

**Recommendation:**
- Make `design_brief.py` Phase 0 mandatory (not optional) for decks with 5+ sections.
- Add a quality scorer check: does each chart slide have at least one of (chart +
  annotation, chart + stat callout, chart + insight bullets)? Pure `chart` type without
  supporting elements scores poorly on memorability.
- Tighten the `stat` slide guidance: pure stat slides (hero numbers only) should be
  required to have an accompanying supporting element in the same layout — at minimum
  a caption or footnote that explains the "so what" behind each number.

---

### 13.3 Prompting LLMs for Better Design Decisions

The single most important research finding from 2025 on LLM design prompting:
**vocabulary injection — giving the LLM precise design terminology and decision
frameworks — improves output quality more than switching to a more powerful model.**
The Impeccable project found a 59% improvement from structured vocabulary alone.

This validates Inkline's existing approach (SLIDE_TYPE_GUIDE, VISHWAKARMA_SYSTEM_PREAMBLE,
playbook injection) but suggests several specific improvements:

**1. Use the decision-sequence format, not a menu.**
`design_system_spec.md` section 1.3 specifies replacing the option-catalog prompt with
a structured STEP 1 → STEP 2 → STEP 3 decision sequence. This is not yet implemented
in `design_advisor.py`. The current SLIDE_TYPE_GUIDE still shows the full catalogue.
Implementation of the decision matrix reduces "option paralysis entropy" — the tendency
for an LLM shown 30 options to make inconsistent selections.

**2. Structured CoT (Chain-of-Thought) for Phase 1 planning.**
Current Phase 1 asks the LLM to produce a plan. It does not ask the LLM to reason
about the plan's quality before returning it. Adding a mandatory self-review step
(the AMBITION CHECK in `vishwakarma.py` is partially this, but it could be more
explicit) before the JSON is finalised would improve consistency:

```
Before returning your slide plan, run this three-step check:
1. Count slides by tier (see VISHWAKARMA scoring above). If tier 5 (content) > 1,
   return to those slides and convert the weakest to tier 1 or 2.
2. Find any two adjacent slides covering related data facets. Can they share a
   multi_chart layout? If yes, consolidate.
3. Verify every slide title contains at least one metric, comparison word, or
   direction word. If not, rewrite to state the insight.
Only return your JSON after completing this check.
```

**3. Role framing with specific expertise.**
Research consistently shows that role-based prompting ("You are a senior McKinsey
consultant who has designed 500 investor decks") improves output quality on
domain-specific tasks. The current DesignAdvisor system prompt begins with the
Vishwakarma preamble. Adding an explicit role statement before it would strengthen
the design register of LLM output.

**4. Negative examples in prompts.**
The current SLIDE_TYPE_GUIDE includes FORBIDDEN PATTERNS (bullet lists when alternatives
exist). Expanding the forbidden patterns with concrete before/after examples — not just
rule statements — improves LLM compliance. The `chart_selection.md` "Facts grounding
examples" section (showing a GOOD vs. BAD slide spec) demonstrates this pattern works.
Apply it to the main SLIDE_TYPE_GUIDE as well.

**5. Constraint the output format before the content.**
Best practice in 2025: specify the exact JSON schema the LLM should produce before
the design task begins, not after. The LLM should be anchored on format first, then
fill the content. This reduces JSON parsing failures and structural drift.

**Concrete recommendations for DesignAdvisor prompts:**
- Prepend a role statement: "You are a senior presentation designer who has built
  investor and board decks for top-tier clients. Your default reflex is visual, not
  textual. You make confident design decisions without hedging."
- Add a mandatory 3-step quality check at the end of Phase 1 (as above)
- Implement the Step 1 → Step 2 → Step 3 decision framework from `design_system_spec.md`
  (replace the option catalog with the decision sequence)
- Add 2-3 concrete before/after examples to SLIDE_TYPE_GUIDE for the most common
  anti-patterns (content → icon_stat; table → comparison; two charts → multi_chart)

---

### 13.4 What AI Presentation Tools Do Well

**Gamma's key design principle: block-based modular composition.** Instead of fixed
slide dimensions, Gamma uses stacked modular blocks (text, chart, image, table) that
adapt to content. This is architecturally opposite to Inkline (which uses fixed-canvas
Typst rendering), but the underlying principle — that content should drive layout, not
the reverse — is what Inkline's DesignAdvisor already attempts. The difference is that
Gamma enforces this computationally; Inkline relies on the LLM to make this judgment.

**Beautiful.ai's adaptive layout templates.** Smart templates automatically adjust
spatial ratios as content is added. This maps directly to Inkline's capacity enforcement
system (char limits, item count caps). Beautiful.ai's sophistication is that it adjusts
spatially in real time; Inkline's is that it truncates deterministically. Neither is
fully satisfying — the ideal would be layout that scales gracefully rather than
truncating. This is a medium-term architecture goal: move from fixed-capacity containers
to adaptive-ratio Typst components.

**Tome's narrative-led design philosophy.** Tome treats slides as chapters in a story,
with smooth contextual transitions. Inkline has the `section_divider` slide type and
the `story_arc` field in `DesignBrief`, but no mechanism to enforce narrative continuity
across slides. An auditor check for narrative coherence (does each slide's section label
and title follow logically from the previous one?) would improve deck-level quality.

**What they all share:** All four major AI presentation tools abstract layout decisions
away from the user. None teaches the user design principles. Inkline's differentiation
is the opposite: it is a *design intelligence* system that encodes principles explicitly,
not just aesthetics implicitly. This is a strategic strength — Inkline can explain why
it made a choice, can refuse bad choices, and can learn. The others cannot.

**Recommendation:**
- Add narrative continuity as a scoring dimension (7th dimension at 10% weight):
  does each slide's section label + title follow logically from the previous slide's
  section? Penalise abrupt topic changes without a `section_divider`.
- Consider adaptive capacity: instead of silently truncating at char limits, polish.py
  should attempt smart restructuring (split one card into two shorter cards, demote
  the slide to a different type) before truncation.

---

### 13.5 The Wow Factor: Making Slides Visually Memorable

Based on the Borkin memorability research and institutional deck analysis, these are
the specific techniques that produce visually memorable slides:

**Technique 1: Visual asymmetry as signal.**
In a grid of uniform elements (bar chart, three equal cards), one visually asymmetric
element signals importance. `accent_index` (one highlighted bar) is a form of this.
Stronger implementation: in `kpi_strip`, the `highlight: true` card should be noticeably
larger or differently weighted, not just a colour change. In `icon_stat`, the first stat
could render at display_xl (44pt) while supporting stats render at display_lg (36pt).

**Technique 2: Numbers at scale.**
The MIT research confirms that big numbers are memorable. Inkline's `stat` slide (hero
numbers at 44-64pt) and `icon_stat` correctly implement this. The design advisor should
be more aggressive in using these types — every section with a single standout metric
should default to an `icon_stat` or `stat`, not a bullet point or caption.

**Technique 3: Named positions in scatter charts.**
Label-positioned scatter (where the entity name IS the marker) consistently outperforms
dot-and-legend scatter in both memorability and comprehension. Inkline's `label_style:
"annotated"` implements this, and `taste_enforcer.py` R-04 enforces it when named points
exist. This rule is correct — ensure it fires reliably and produces high-contrast callout
boxes (white fill, thin border, brand-coloured text).

**Technique 4: The single bold headline.**
Slides that lead with one very large, bold insight statement — and subordinate everything
else to that statement — are more memorable than slides with multiple equal-weight
elements. The Vishwakarma hierarchy (1C at 30% minimum) works against this: multi-chart
layouts by definition have no single dominant element. The balance is correct for
information density, but for high-impact slides (opening, executive summary, call to
action), a single bold exhibit with a dominant title is more memorable than a
four-panel grid.

**Technique 5: Unique chart types.**
The Borkin research specifically found that "unique, distinct visualisations like
treemaps, circular diagrams or layouts that broke the traditional visual mold" are
significantly more memorable than standard bar/line charts. Inkline's Tier 1B
archetypes (radial_pinwheel, hexagonal_honeycomb, waffle, iceberg) are exactly
this. Increase their usage: the Vishwakarma scoring currently requires ≥20% of content
slides to be Tier 1A+1B combined. A stronger goal: ≥15% should be Tier 1B specifically
(structural infographic), since these are the most memorable.

**Recommendation:**
- Upgrade the Vishwakarma SCORING to distinguish 1A (KPI callout) from 1B (structural
  infographic): require ≥15% Tier 1B specifically, not just 1A+1B combined.
- Add a "visual boldness" score to `quality_scorer.py`: slides that use a Tier 1B
  archetype OR use a chart type with named annotation (annotated scatter, marimekko,
  entity_flow) score higher than standard grouped_bar or kpi_strip slides.
- In the DesignAdvisor prompt, add an UPGRADE trigger specifically for the opening
  and executive summary sections: "For the first two content slides and any section
  containing a single dominant insight, consider whether a single bold exhibit (stat,
  icon_stat with one dominant metric, or a Tier 1B infographic) would be more impactful
  than a multi-chart layout."

---

### 13.6 Typography for Commercial Impact

Research confirms that font choice influences perceived credibility by up to 35%. For
slide decks aimed at executive and investor audiences, the typography rules that signal
quality are well-established:

**Sans-serif for screen and slide; serif for emphasis or brand character.**
Source Sans Pro (Inkline's default) is the correct choice for slide body text. For
headings on high-impact slides, a slightly more distinctive sans-serif (Inter, Geist,
or a geometric sans like Avenir or Circular) creates more typographic interest while
remaining highly legible.

**Weight variation over size variation.**
Professional presentation typography achieves hierarchy primarily through weight, not
size. A Bold / Regular weight pair within one family creates hierarchy that feels
intentional. Most of Inkline's templates use size variation (28pt heading, 14pt body).
Adding explicit weight variation — Bold for action titles, Regular for body, Light for
footnotes — would improve the typographic signal.

**Line length control.**
Research on reading comfort (the "65-75 character" rule, documented in Impeccable and
typography research) applies to slide body text. Inkline's char limits for bullets
(80 chars for `content` items, 85 for `three_card` bodies) are within this range. The
footnote limit (90 chars) is slightly over. Tighter limits (70 chars for body, 80 for
card bodies) would improve typographic comfort.

**Overline labels for section identity.**
The `professional_exhibit_design.md` section 4 documents the overline pattern: a
3-5 word section identifier in SMALL-CAPS at ~9pt above the action title. Inkline
implements this as the `section` field in slide data, but the current renderer renders
it as regular (not small-caps) muted text. A genuine small-caps overline would
significantly strengthen the typographic hierarchy signal.

**Abbreviation discipline.**
`professional_exhibit_design.md` section 10 documents the institutional abbreviation
standard (`2025F` not "2025 Forecast", `USDbn` not "USD billion"). This should be
added to `polish.py` as PL-13: detect and replace common verbose financial expressions
with their institutional abbreviations in chart labels and bullet text.

**Recommendation:**
- Tighten body text char limits: `content` items to 70 chars, card bodies to 75 chars,
  footnotes to 80 chars.
- Add `polish.py` PL-13: institutional financial abbreviation normalization.
- Add font weight tokens (heading_weight, body_weight, muted_weight) to the typography
  scale in `brands/__init__.py`, so templates can express hierarchy through weight,
  not just size.
- Consider adding small-caps rendering for `section` overline labels in Typst templates.

---

### 13.7 New Slide Types and Chart Types for Commercial Wow

Based on the institutional deck analysis and research review, these additions would
most meaningfully extend Inkline's commercial output quality:

**Missing chart types:**
- `marimekko` — two-dimensional part-of-whole; specified in `professional_exhibit_design.md`
  section 7.1 but not yet fully implemented as a standalone chart type in `chart_renderer.py`
- `staircase` / step-line — discrete period measurements (mentioned in section 7.5);
  can be implemented as a `line_chart` option with `drawstyle='steps-post'`
- `bump_chart` — ranking change over time; powerful for showing competitive position
  shifts; not yet in the chart catalogue

**Missing slide types:**
- `credentials` / tombstone strip — 6-8 equal-width tombstone cells for track record
  slides (documented in `professional_exhibit_design.md` section 6.2). High commercial
  value for investment banking and professional services decks.
- `testimonial` — large pull-quote with attribution; a standard in pitch decks but
  absent from Inkline's type catalogue
- `before_after` — a structured two-panel layout showing state before and after
  (currently approximated with `comparison` or `split`, but neither has the spatial
  emphasis that "before/after" implies)

**Missing infographic archetypes:**
- `heat_calendar` — a calendar-grid heatmap (think GitHub contribution graph) for
  showing activity, seasonality, or frequency patterns over time
- `population_pyramid` — diverging horizontal bars for age/cohort distributions;
  common in market sizing slides

---

### 13.8 Specific Anti-Patterns to Avoid (Research-Backed Additions)

These patterns are documented in current design research as damaging to slide quality
but are not yet in Inkline's anti-pattern library:

**Pattern: The "data dump" slide.** A slide that shows all available data rather than
the data that proves the point. Every chart has too many series; every table has too
many columns; every bullet list has too many items. Knaflic's principle: "your audience
will remember at most one thing per slide — make sure it is the right thing." Anti-pattern
check: any slide where no single element is visually dominant (no accent, no hero
number, no callout) should be flagged as a data dump.

**Pattern: The orphaned number.** A number in prose text that could be a hero-formatted
metric. `anti_patterns.py` DP-03 addresses this (metrics in narrative text) but only
with a warning. For investor and board audiences, this should be an error: any number
greater than a single digit that appears in a bullet item or narrative field should
be extracted to an `icon_stat` or `kpi_strip` element.

**Pattern: The symmetric deck.** A deck where every slide looks visually similar
(same type, same level of density, same colour distribution). Memorable decks have
visual rhythm: a dramatic opener, sustained middle, and clear closing beat. Inkline's
quality scorer `Visual Variety` dimension rewards type diversity but does not check
for placement rhythm. The opening slide (after title) should be the highest visual
intensity; the middle should vary; the closing should be clean and simple.

**Pattern: The apology footnote.** Footnotes that apologise for the data ("This is
an approximate figure based on limited data") signal uncertainty and undermine the
slide's authority. Footnotes should be source attributions or methodology notes, not
qualifications. `anti_patterns.py` should flag footnotes containing words like
"approximate", "estimated", "assumed", "subject to change" as TP-07 (warning).

---

## Summary: Priority Implementation Queue

Based on this analysis, the highest-ROI improvements to Inkline's design intelligence
are ranked as follows:

| Priority | Improvement | Effort | Impact |
|----------|------------|--------|--------|
| 1 | Implement decision matrix (Step 1→2→3 framework) in DesignAdvisor | Medium | Eliminates LLM option entropy; most consistent chart selection |
| 2 | Add role framing + mandatory quality check to DesignAdvisor prompts | Low | 30-60% improvement in first-pass quality based on prompting research |
| 3 | Make design_brief.py Phase 0 mandatory for decks ≥5 sections | Low | Audience-first framing; prevents narrative-less decks |
| 4 | Add TP-07 (action title verification) to anti_patterns.py | Low | Catches the #1 quality failure in generated decks |
| 5 | Tighten Vishwakarma to distinguish Tier 1A from 1B; require ≥15% Tier 1B | Low | Forces use of memorable infographic archetypes |
| 6 | Add `credentials` / tombstone slide type | Medium | High commercial value for professional services brands |
| 7 | Implement weight tokens in type scale (heading_weight, body_weight) | Medium | Typography hierarchy quality signal |
| 8 | Add financial abbreviation normalisation (PL-13) to polish.py | Low | Institutional register in chart labels |
| 9 | Add narrative continuity as quality scoring dimension | Medium | Deck-level coherence; story arc enforcement |
| 10 | Wire self-learning feedback loop (aggregator.py + decision_matrix.yaml) | High | Compounding improvement from each generation |

---

*Document compiled from codebase audit of `/home/k1mini/inkline/` (17 April 2026) and
research review of consulting firm design standards, information design theory, and
current AI presentation tool design principles.*
