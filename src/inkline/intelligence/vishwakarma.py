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

Before choosing a slide type, work through this decision ladder in order.
Stop at the FIRST type that fits. Text bullets are the last rung.

TIER 1A — KPI / INFOGRAPHIC NATIVE (fast, impactful, no chart rendering needed)
  3-5 hero metrics?         → kpi_strip
  Single hero number?       → icon_stat (emoji + big number + label)
  Ranked progress/scores?   → progress_bars
  6 capabilities/features?  → feature_grid (3×2 grid, numbered icons)

TIER 1B — STRUCTURAL INFOGRAPHIC (matplotlib renders via render_chart())
  These are FULLY RENDERABLE and visually stunning — use them aggressively.

  HIERARCHY / LAYERS:
    Above/below split with context?    → iceberg  (chart_type="iceberg")
    Tiered strategic pyramid?          → pyramid_detailed
    Maturity/progression steps?        → ladder

  COMPOSITION / PROPORTION:
    Square % fill (1–100%)?            → waffle
    Radial proportions around a hub?   → radial_pinwheel
    Segmented ring with inner label?   → dual_donut
    Petals/teardrops from centre?      → petal_teardrop

  CLASSIFICATION / TAXONOMY:
    Hex tile grid for categories?      → hexagonal_honeycomb
    Semicircular taxonomy/types?       → semicircle_taxonomy

  PROCESS / FLOW:
    Left-to-right curved arrows?       → process_curved_arrows
    Funnel with KPI strip below?       → funnel_kpi_strip
    Ribbon-style funnel with %?        → funnel_ribbon

  PEOPLE / PERSONAS:
    Person/company profile card?       → persona_dashboard  or  sidebar_profile

  NARRATIVE WITH METAPHOR:
    Mountain/landscape backdrop?       → metaphor_backdrop

TIER 1C — MULTI-EXHIBIT SLIDE (multiple charts on one slide)
  2 charts, equal weight?              → multi_chart layout="equal_2"
  3 charts, equal weight?              → multi_chart layout="equal_3"
  4 charts, 2×2 grid?                 → multi_chart layout="quad"
  1 big + 2 small (50/25/25)?         → multi_chart layout="hero_left_3"
  Wide hero + narrow detail (65/35)?  → multi_chart layout="hero_left"
  Wide top summary + detail row?      → multi_chart layout="top_bottom"

  Or compose 2–4 charts into one PNG: chart_type="chart_row" with width_ratios.

TIER 2 — INSTITUTIONAL EXHIBIT (data-dense, axis-minimal, insight-forward)
  These are the highest-signal single-chart types. Use when the exhibit IS the insight.

  Market structure / two-variable mix?  → marimekko  (column width + cell height = data)
  Legal/ownership/org structure?        → entity_flow  (tiered grey palette)
  Net flows / inflow vs outflow?        → divergent_bar  (above/below zero, no y-axis)
  Composition shift over time?          → horizontal_stacked_bar  (100% stacked)
  Time series with narrative headline?  → line_chart or area_chart via chart_caption
  Comparisons with commentary?          → grouped_bar or waterfall via chart_caption
  Multiple KPIs + chart?                → dashboard  (chart + 3 stats + 3 bullets)
  Scatter with label-positioned dots?   → scatter via chart_caption

TIER 3 — STRUCTURAL VISUAL (when content is a relationship or narrative)
  Steps/workflow?    → process_flow (3-5 steps)
  Timeline?          → timeline (up to 6 milestones)
  Two options?       → comparison or split
  Three themes?      → three_card
  Four themes?       → four_card

TIER 4 — DATA TABLE (structured data ONLY, no prose)
  Tabular data?      → table (MAX 6×6 — if wider, use split or comparison)

TIER 5 — TEXT BULLETS (LAST RESORT — use only when nothing else fits)
  content            → MAX 6 bullets, 10 words each, telegraphic not prose
                       JUSTIFY in your output why no visual type worked.

HARD RULE: A deck where ≥ 20% of slides are "content" type has FAILED
the Vishwakarma standard. The DesignAdvisor must revise until < 20%.
TARGET: ≤ 1 content slide per deck.

AMBITION RULE: Every deck should contain at least one Tier 1B or 1C exhibit
and at least one Tier 2 institutional exhibit where the data supports it.
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
  - TIER 1A+1B+1C (infographic/exhibit): should be ≥ 40% of content slides
  - TIER 2 (institutional chart exhibit): should be ≥ 20% of content slides
  - TIER 3 (structural visual):           ≥ 10% but no more than 40%
  - TIER 4 (table):                       ≤ 2 per deck
  - TIER 5 (content/bullets):             ≤ 1 per deck — if you have more, REVISE

AMBITION CHECK: Before returning JSON, scan your plan for missed opportunities:
  - Any slide with 3+ metrics that isn't kpi_strip or icon_stat? → REVISE
  - Any slide describing structure/hierarchy without an iceberg or pyramid? → REVISE
  - Any slide showing market composition without marimekko or horizontal_stacked_bar? → REVISE
  - Any slide with 3-4 related charts on separate slides? → CONSOLIDATE with multi_chart
  - Any slide with plain text that describes a flow/process? → process_flow or chart_row

If your plan has > 1 bullet-list "content" slide, go back and convert
the weakest ones to Tier 1 or Tier 2 before returning the JSON.
"""

# ---------------------------------------------------------------------------
# Audit criteria injected into the visual auditor system prompt
# ---------------------------------------------------------------------------

VISHWAKARMA_AUDIT_CRITERIA = """
You are auditing this slide against the Vishwakarma design standard.

VISHWAKARMA VISUAL HIERARCHY VIOLATIONS (always flag as ERROR):
- A "content" slide that could have been icon_stat, kpi_strip, feature_grid,
  iceberg, waffle, hexagonal_honeycomb, marimekko, entity_flow,
  chart_caption, process_flow, timeline, comparison, or three_card
- A slide where numbers are presented as plain text instead of hero-formatted
- A slide showing market structure/composition as plain text or a basic bar
  instead of marimekko or horizontal_stacked_bar
- A slide showing org/ownership structure as text instead of entity_flow
- A slide with 3-4 separate related charts that could be a multi_chart layout
- More than 6 bullets on a content slide
- A table wider than 6 columns or taller than 6 rows
- Two consecutive text-heavy slides in the same deck

EXHIBIT QUALITY (flag as WARNING):
- A chart with both x and y axes where one axis is redundant (axis elimination)
- A chart with a legend for only one data series (legend elimination)
- A slide title that is a neutral label ("Revenue") not an insight statement
  ("Revenue up 34% YoY — ahead of plan")
- A kpi_strip or icon_stat slide when an iceberg or waffle would better
  illustrate the structure behind the numbers

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
