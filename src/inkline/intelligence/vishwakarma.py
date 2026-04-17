"""Vishwakarma — Inkline's foundational design philosophy.

Vishwakarma (Sanskrit: विश्वकर्मा) is the divine architect and craftsman of
the gods. As Inkline's design standard, Vishwakarma governs every decision
about how information is presented. Every slide deck Inkline produces is an
act of craftsmanship, not a document dump.

This module is the single source of truth for the four laws. It is imported
by the DesignAdvisor (LLM system prompt), the visual auditor (audit criteria),
and every Archon-supervised pipeline (build law enforcement).

FOUR LAWS
---------
I.   Infographic first — visual hierarchy is non-negotiable
II.  Bridge first — zero API spend when Claude Max is available
III. Visual audit mandatory — nothing ships without the design dialogue
IV.  Archon oversight — one supervisor, one report, one output

Import this module anywhere Inkline decisions are made.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# I. VISUAL HIERARCHY
# ---------------------------------------------------------------------------

VISUAL_HIERARCHY = """
╔══════════════════════════════════════════════════════════════════════╗
║              VISHWAKARMA VISUAL HIERARCHY — NON-NEGOTIABLE           ║
╚══════════════════════════════════════════════════════════════════════╝

PRIORITY ORDER WITHIN TIER 1: always attempt 1C → 1B → 1A in that order.
  Can the content support multiple exhibits on one slide?  → try 1C first.
  Does a single structural infographic capture the concept? → try 1B next.
  Is it purely a number/metric callout?                    → fall back to 1A.
  None of the above?                                       → proceed to Tier 2.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TIER 1C — MULTI-EXHIBIT SLIDE  [HIGHEST PRIORITY within Tier 1]
──────────────────────────────────────────────────────────────────────
USE THIS whenever a section has 2–4 related data facets that belong
together. A single information-dense slide beats two sparse slides.

Step 1 — pick the layout:
  1 dominant exhibit + 2 supporting?   → layout="hero_left_3"  (50/25/25)
  2 exhibits, equal weight?            → layout="equal_2"
  3 exhibits, equal weight?            → layout="equal_3"
  4 exhibits, 2×2 grid?               → layout="quad"
  Wide hero + narrow callout?          → layout="hero_left"    (65/35)
  Wide summary + detail row below?     → layout="top_bottom"
  4 exhibits, wide top + 3 below?      → layout="top_bottom"   (top=1, bottom=3)

Step 2 — for EACH exhibit slot, apply the 1B → 1A → Tier 2 selector:
  ┌──────────────────────────────────────────────────────────────────┐
  │ Ask: what type of content goes in THIS slot?                     │
  │  Structural concept / proportion / flow?  → pick from 1B below  │
  │  Pure metric / KPI?                       → pick from 1A below  │
  │  Data series / trend / distribution?      → pick from Tier 2    │
  └──────────────────────────────────────────────────────────────────┘

HINT: hero slots (large) suit 1B archetypes or Tier 2 institutional
exhibits; supporting slots (small) suit 1A callouts or compact charts.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TIER 1B — STRUCTURAL INFOGRAPHIC  [use standalone OR as a 1C exhibit slot]
──────────────────────────────────────────────────────────────────────
All rendered by matplotlib via render_chart(chart_type=...). Pick by content shape:

  HIERARCHY / LAYERS:
    Above/below split?                 → iceberg
    Tiered strategic pyramid?          → pyramid_detailed
    Maturity/progression steps?        → ladder

  COMPOSITION / PROPORTION:
    Square grid % fill?                → waffle
    Radial proportions around a hub?   → radial_pinwheel
    Concentric ring comparison?        → dual_donut
    Petals/teardrops from centre?      → petal_teardrop

  CLASSIFICATION / TAXONOMY:
    Hex tile grid for categories?      → hexagonal_honeycomb
    Semicircular taxonomy/types?       → semicircle_taxonomy

  PROCESS / FLOW:
    Left-to-right curved arrows?       → process_curved_arrows
    Funnel with KPI strip below?       → funnel_kpi_strip
    Ribbon-style funnel with %?        → funnel_ribbon

  PEOPLE / PERSONAS:
    Profile card with stats?           → persona_dashboard  or  sidebar_profile

  NARRATIVE WITH METAPHOR:
    Concept with landscape theme?      → metaphor_backdrop

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TIER 1A — KPI CALLOUT  [use standalone OR as a supporting slot in 1C]
──────────────────────────────────────────────────────────────────────
Use only when the content IS a set of metrics with no structural story.

  3-5 hero metrics?         → kpi_strip
  Single hero number?       → icon_stat  (emoji + big number + label)
  Ranked progress/scores?   → progress_bars
  6 capabilities/features?  → feature_grid  (3×2 grid, numbered icons)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TIER 2 — INSTITUTIONAL EXHIBIT  [standalone OR as a 1C exhibit slot]
──────────────────────────────────────────────────────────────────────
Data-dense, axis-minimal, insight-forward. Use when the exhibit IS the insight.

  Market structure / two-variable mix?  → marimekko
  Legal/ownership/org structure?        → entity_flow
  Net flows / inflow vs outflow?        → divergent_bar
  Composition shift over time?          → horizontal_stacked_bar
  Time series with narrative headline?  → line_chart or area_chart via chart_caption
  Comparisons with commentary?          → grouped_bar or waterfall via chart_caption
  Mix of KPIs + supporting chart?       → dashboard
  Scatter with label-positioned dots?   → scatter via chart_caption

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TIER 3 — STRUCTURAL VISUAL
  Steps/workflow?  → process_flow    Timeline?     → timeline
  Two options?     → comparison or split
  Three themes?    → three_card      Four themes?  → four_card

TIER 4 — DATA TABLE
  Tabular data?    → table  (MAX 6×6; if wider use split or comparison)

TIER 5 — TEXT BULLETS  [LAST RESORT]
  content  → MAX 6 bullets, 10 words each. JUSTIFY why no visual type worked.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

HARD RULE: A deck where ≥ 20% of slides are "content" has FAILED.
TARGET: ≤ 1 content slide per deck.

AMBITION RULE: Every deck must contain at least one 1C multi-exhibit slide.
A deck of only kpi_strip + three_card + content has NOT met the standard.
"""

# ---------------------------------------------------------------------------
# II. BRIDGE-FIRST INTELLIGENCE
# ---------------------------------------------------------------------------

BRIDGE_FIRST = """
╔══════════════════════════════════════════════════════════════════════╗
║                  BRIDGE-FIRST INTELLIGENCE LAW                       ║
╚══════════════════════════════════════════════════════════════════════╝

Every LLM call in the Inkline pipeline routes through the local Claude
bridge (localhost:8082) before touching the Anthropic API.

  POST /prompt  — text design/revision calls (DesignAdvisor)
  POST /vision  — image+text visual audit calls (overflow_audit)

API credits are NEVER consumed when the bridge is available.
The bridge auto-starts from ~/.config/inkline/claude_bridge.py if not running.
"""

# ---------------------------------------------------------------------------
# III. VISUAL AUDIT MANDATORY
# ---------------------------------------------------------------------------

AUDIT_MANDATORY = """
╔══════════════════════════════════════════════════════════════════════╗
║                  VISUAL AUDIT IS MANDATORY                           ║
╚══════════════════════════════════════════════════════════════════════╝

Every rendered deck goes through the two-agent design dialogue:
  Auditor (vision)  — inspects rendered PNG of every slide
  Advisor (design)  — revises slide specs based on audit findings

The dialogue runs until:
  a) No errors remain (PASS), or
  b) max_visual_attempts reached (ships with audit errors in report)

A deck that skips the audit is not a Vishwakarma-compliant output.
"""

# ---------------------------------------------------------------------------
# IV. ARCHON OVERSIGHT
# ---------------------------------------------------------------------------

ARCHON_OVERSIGHT = """
╔══════════════════════════════════════════════════════════════════════╗
║                     ARCHON OVERSIGHT LAW                             ║
╚══════════════════════════════════════════════════════════════════════╝

Every Inkline pipeline run is supervised by an Archon process.

  - Archon intercepts all log messages from the inkline logger tree
  - Archon records every phase with start time, end time, and issues
  - Archon writes a structured issues report at pipeline completion
  - The user sees: the output PDF + the Archon report
  - Nothing ships without Archon signing off (even partial outputs)

Archon is the single point of contact between the pipeline and the user.
Import it from inkline.intelligence.archon, never define it inline.
"""

# ---------------------------------------------------------------------------
# Combined philosophy string — injected into LLM system prompts
# ---------------------------------------------------------------------------

VISHWAKARMA_SYSTEM_PREAMBLE = f"""
╔══════════════════════════════════════════════════════════════════════╗
║           VISHWAKARMA — INKLINE DESIGN PHILOSOPHY                    ║
║           These laws govern every output you produce.                ║
╚══════════════════════════════════════════════════════════════════════╝

{VISUAL_HIERARCHY}

SCORING: Before finalising your slide list, count your slide types.
  - TIER 1C (multi-exhibit):              should be ≥ 30% of content slides
  - TIER 1A (KPI callout):               should be ≥ 10% of content slides
  - TIER 1B (structural infographic):    should be ≥ 15% of content slides
  - TIER 2 (institutional exhibit):       should be ≥ 20% of content slides
  - TIER 3 (structural visual):           ≤ 30% of content slides
  - TIER 4 (table):                       ≤ 2 per deck
  - TIER 5 (content/bullets):             ≤ 1 per deck — if you have more, REVISE

AMBITION CHECK: Before returning JSON, run this scan in order:

  1. CONSOLIDATION — find groups of 2-4 adjacent slides covering related facets.
     Can they share one slide as a 1C multi_chart? If yes, consolidate.
     For each slot in the layout, re-apply the 1B → 1A → Tier 2 selector.

  1.5 TIER 1B CHECK — count radial_pinwheel, hexagonal_honeycomb, waffle, iceberg,
       funnel_kpi_strip, persona_dashboard, dual_donut, ladder, and pyramid_detailed slides.
       If count / content_slides < 0.15, add at least one 1B structural infographic.
       Candidates: any section showing structure/hierarchy/composition/flow as text.

  2. UPGRADE — for every remaining single-exhibit slide:
     - Showing structure/hierarchy as text? → iceberg, pyramid_detailed, or ladder
     - Showing composition as text/table?   → waffle, radial_pinwheel, or dual_donut
     - Showing market structure?            → marimekko or horizontal_stacked_bar
     - Showing org/legal structure?         → entity_flow
     - Showing flow/process as text?        → process_curved_arrows or funnel_kpi_strip
     - Showing 3-5 metrics without a chart? → kpi_strip or icon_stat

  3. TITLE CHECK — every chart/exhibit slide title should state the insight
     ("Revenue up 34% YoY") not the subject ("Revenue").

If your plan has > 1 bullet-list "content" slide, go back and convert
the weakest ones to Tier 1 or Tier 2 before returning the JSON.
"""

# ---------------------------------------------------------------------------
# Audit criteria injected into the visual auditor system prompt
# ---------------------------------------------------------------------------

VISHWAKARMA_AUDIT_CRITERIA = """
You are auditing this slide against the Vishwakarma design standard.

TIER PRIORITY VIOLATIONS (always flag as ERROR):
- Two or more consecutive single-exhibit slides covering related facets that
  should have been consolidated into one multi_chart (1C) layout
- A single chart slide that could have been the hero exhibit in a multi_chart
  layout with supporting KPI callouts alongside it
- A "content" text slide that could have been any of: icon_stat, kpi_strip,
  iceberg, waffle, hexagonal_honeycomb, marimekko, entity_flow, chart_caption,
  process_flow, timeline, comparison, or three_card
- A slide where numbers are presented as plain text instead of hero-formatted
- A slide showing market structure/composition as text or a basic bar chart
  instead of marimekko or horizontal_stacked_bar
- A slide showing org/legal/ownership structure as text instead of entity_flow
- More than 6 bullets on a content slide
- A table wider than 6 columns or taller than 6 rows

EXHIBIT QUALITY (flag as WARNING):
- A multi_chart layout with mismatched exhibit types — hero slot should hold
  the most complex 1B or Tier 2 exhibit; supporting slots hold 1A callouts
- A kpi_strip or icon_stat slide used standalone when there is structural
  content that would suit iceberg, waffle, or radial_pinwheel instead
- A chart with both x and y axes where one is redundant (floating labels suffice)
- A chart with a legend for only one data series (redundant noise)
- A slide title that is a neutral label ("Revenue") not an insight statement
  ("Revenue up 34% YoY — ahead of plan")

LAYOUT QUALITY (flag as WARNING):
- Card bodies longer than 2 short sentences
- Chart image visually clipped or cut off
- Title truncated mid-word (sign of >50 char title)
- Blank/empty sections that should have content
- Inconsistent card heights or unbalanced column widths

VISUAL OVERFLOW (always flag as ERROR):
- Any content visibly cut off at slide boundary
- Footer or page number missing
- Logo missing from header
"""


__all__ = [
    "VISUAL_HIERARCHY",
    "BRIDGE_FIRST",
    "AUDIT_MANDATORY",
    "ARCHON_OVERSIGHT",
    "VISHWAKARMA_SYSTEM_PREAMBLE",
    "VISHWAKARMA_AUDIT_CRITERIA",
]
