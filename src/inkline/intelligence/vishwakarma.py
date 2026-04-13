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

TIER 1 — INFOGRAPHIC (always try this first)
  Numbers?           → icon_stat (hero metric + emoji) or kpi_strip
  Proportions?       → donut / pie via chart_caption or dashboard
  Ranking/funnel?    → pyramid
  Progress/score?    → progress_bars
  6 capabilities?    → feature_grid (3×2 grid, numbered icons)

TIER 2 — CHART EXHIBIT (when data has a trend, series, or distribution)
  Time series?       → line_chart or area_chart via chart_caption
  Comparisons?       → grouped_bar or waterfall via chart_caption
  Composition?       → stacked_bar or donut via dashboard
  Relationship?      → scatter via chart_caption
  Mix of numbers?    → dashboard (chart + 3 stats + 3 bullets)

TIER 3 — STRUCTURAL VISUAL (when content is a relationship or narrative)
  Steps/workflow?    → process_flow (3-5 steps)
  Timeline?          → timeline (up to 6 milestones)
  Two options?       → comparison or split
  Three themes?      → three_card
  Four themes?       → four_card
  Strategic layers?  → pyramid

TIER 4 — DATA TABLE (structured data ONLY, no prose)
  Tabular data?      → table (MAX 6×6 — if wider, use split or comparison)

TIER 5 — TEXT BULLETS (LAST RESORT — use only when nothing else fits)
  content            → MAX 6 bullets, 10 words each, telegraphic not prose
                       JUSTIFY in your output why no visual type worked.

HARD RULE: A deck where ≥ 20% of slides are "content" type has FAILED
the Vishwakarma standard. The DesignAdvisor must revise until < 20%.
TARGET: ≤ 1 content slide per deck.
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
  - TIER 1+2 (infographic/chart): should be ≥ 50% of content slides
  - TIER 3 (structural visual):   should be ≥ 20% of content slides
  - TIER 4 (table):               ≤ 2 per deck
  - TIER 5 (content/bullets):     ≤ 1 per deck — if you have more, REVISE

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
  chart_caption, process_flow, timeline, comparison, or three_card
- A slide where numbers are presented as plain text instead of hero-formatted
- More than 6 bullets on a content slide
- A table wider than 6 columns or taller than 6 rows
- Two consecutive text-heavy slides in the same deck

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
