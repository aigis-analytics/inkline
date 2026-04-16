# Impeccable Design Intelligence — Inkline Enhancement Spec

**Status:** Approved for implementation
**Date:** 2026-04-16
**Inspired by:** [Impeccable](https://github.com/pbakaus/impeccable) — 18 design commands for AI-generated UIs
**Scope:** 4 new capabilities for Inkline's design intelligence layer

---

## Problem Statement

Inkline generates branded slides and documents via DesignAdvisor + Typst. The output quality
is good but inconsistent — there's no systematic way to:

1. **Detect known bad patterns** before they ship (e.g. consecutive text slides, weak titles,
   axis clutter, legend waste, poor colour contrast)
2. **Score output quality** quantitatively so we can track improvement over time
3. **Auto-polish** generated output with deterministic fixes (trim titles, balance cards,
   optimise chart sizing) without a full LLM re-pass
4. **Generate a design brief** that captures audience/goal/story-arc intent before generation
   starts, improving first-pass quality

Impeccable solves this for web UIs with structured prompts. We adapt the same philosophy
to document/slide generation — but as **executable code** (not prompts), integrated into
Inkline's Archon pipeline.

---

## Design Principles

- **Deterministic over LLM** — anti-pattern checks and polish fixes are rules, not LLM calls.
  LLM is only used for design brief generation (where creativity matters).
- **Additive** — these are new modules that plug into the existing Archon pipeline. No changes
  to DesignAdvisor's core logic. No changes to Typst renderers.
- **Composable** — each capability works independently. You can run anti-pattern detection
  without scoring, or polish without a design brief.
- **Observable** — every check produces structured output (JSON/dict) that feeds into
  Archon's issue tracking and the feedback system.

---

## Feature 1: Anti-Pattern Library

### Purpose
Codified rules that flag known bad design patterns in slide specs **before rendering**.
Runs after DesignAdvisor Phase 2 output, before Typst compilation. Catches problems that
overflow_audit misses (which only checks capacity, not design quality).

### Module
`inkline/intelligence/anti_patterns.py`

### Anti-Pattern Catalogue

Each rule has: `id`, `category`, `severity` (error/warning/info), `check(slides) → list[Issue]`.

#### Layout Patterns (LP-*)

| ID | Rule | Severity | Check |
|---|---|---|---|
| LP-01 | 3+ consecutive text-heavy slides (content, narrative) | error | Sliding window over slide sequence |
| LP-02 | No visual slide in first 3 slides after title | warning | Check slides[1:4] for chart/dashboard/kpi_strip/icon_stat |
| LP-03 | Cards-in-cards nesting (split containing cards) | warning | Recursive data structure check |
| LP-04 | Missing section_divider between topic changes | info | Track `section` field changes |
| LP-05 | >60% of slides are content/narrative type | error | Type distribution count |
| LP-06 | Deck has no closing slide | warning | Check last slide type |
| LP-07 | Identical slide types used 3+ times consecutively | warning | Sequence analysis |

#### Typography Patterns (TP-*)

| ID | Rule | Severity | Check |
|---|---|---|---|
| TP-01 | Title >50 chars (hard limit) | error | len(title) check |
| TP-02 | Title is generic/non-actionable ("Overview", "Summary", "The Problem") | warning | Regex against weak title list |
| TP-03 | Bullet text >120 chars (wraps badly) | warning | Per-item length check |
| TP-04 | >6 bullet items on any slide | error | Item count (redundant with overflow_audit but catches edge cases) |
| TP-05 | ALL CAPS in body text (not titles) | info | Regex for words >3 chars in all caps |
| TP-06 | Stat value >16 chars (won't fit in kpi_strip) | error | Length check on stat/kpi values |

#### Colour & Visual Patterns (CP-*)

| ID | Rule | Severity | Check |
|---|---|---|---|
| CP-01 | Chart missing accent_index (no emphasis) | warning | Check chart_request for accent_index |
| CP-02 | >6 segments in donut/pie without direct labels | warning | Segment count + label_strategy check |
| CP-03 | Bar chart with >12 categories (horizontal not set) | warning | Check orientation field |
| CP-04 | Chart using legend when direct labels would work | info | legend_position present + <=6 series |

#### Data Patterns (DP-*)

| ID | Rule | Severity | Check |
|---|---|---|---|
| DP-01 | Table with <4 rows (should be icon_stat or kpi_strip) | info | Row count heuristic |
| DP-02 | Single-series bar chart (could be progress_bars) | info | Series count check |
| DP-03 | Metrics in narrative text, not extracted to stats | warning | Regex for numbers+units in narrative fields |
| DP-04 | Time series with <3 data points | warning | Series length check |

#### Structural Patterns (SP-*)

| ID | Rule | Severity | Check |
|---|---|---|---|
| SP-01 | Deck <5 slides (too thin) or >25 slides (too long) | warning | len(slides) |
| SP-02 | No chart/dashboard/multi_chart in entire deck | error | Type set check |
| SP-03 | Duplicate slide titles | warning | Title dedup |
| SP-04 | footnote on >50% of slides (overuse) | info | Footnote presence count |

### Interface

```python
from inkline.intelligence.anti_patterns import check_anti_patterns, AntiPatternResult

results: list[AntiPatternResult] = check_anti_patterns(slides)

# AntiPatternResult:
#   rule_id: str          — "LP-01"
#   category: str         — "layout"
#   severity: str         — "error" | "warning" | "info"
#   message: str          — human-readable description
#   slide_indices: list[int]  — affected slides (0-based)
#   suggestion: str       — recommended fix
```

### Integration Points
- **Archon Phase 2b** (new phase, after design_advisor_llm, before save_slide_spec):
  Run `check_anti_patterns(slides)`. Errors block, warnings logged, info noted.
- **TasteEnforcer**: Some anti-patterns (CP-01, CP-03) overlap with taste rules.
  Anti-patterns DETECT; TasteEnforcer FIXES. They complement each other.
- **Feedback system**: Anti-pattern hits recorded in feedback_log.jsonl for learning.

---

## Feature 2: Quality Scoring

### Purpose
Quantitative 0-100 score for a deck, broken into 6 dimensions. Enables tracking improvement
over time and gives the user a concrete "is this deck good enough?" signal.

### Module
`inkline/intelligence/quality_scorer.py`

### Scoring Dimensions (each 0-100, weighted to final score)

| Dimension | Weight | What it measures |
|---|---|---|
| **Visual Variety** | 20% | Slide type distribution — penalise monotony, reward diverse exhibit types |
| **Data-Ink Ratio** | 20% | % of slides that are visual (chart/dashboard/kpi/icon_stat/progress_bars) vs text |
| **Typography** | 15% | Title quality (action titles, length), bullet discipline, stat formatting |
| **Colour Discipline** | 15% | Accent usage consistency, chart colour count <=6, brand palette adherence |
| **Flow** | 15% | Story arc (opening impact, middle substance, closing action), section divider presence |
| **Density** | 15% | Content per slide — not too sparse (empty cards), not too dense (>6 items) |

### Scoring Logic

All scoring is **deterministic** — no LLM calls. Pure heuristics on slide spec data.

```python
# Visual Variety (0-100)
unique_types = len(set(s["slide_type"] for s in slides))
type_ratio = unique_types / len(slides)
# Score: 100 if ratio >= 0.6, linear scale down. Penalty for 3+ consecutive same type.

# Data-Ink Ratio (0-100)
VISUAL_TYPES = {"chart", "chart_caption", "dashboard", "multi_chart", "kpi_strip",
                "icon_stat", "stat", "progress_bars", "bar_chart", "feature_grid"}
visual_pct = sum(1 for s in slides if s["slide_type"] in VISUAL_TYPES) / max(len(slides) - 2, 1)  # exclude title+closing
# Score: 100 if visual_pct >= 0.7, 0 if visual_pct < 0.2, linear between.

# Typography (0-100)
# -10 per generic title, -5 per title >45 chars, -3 per bullet >100 chars
# +5 per action title (contains number or comparison word)

# Colour Discipline (0-100)
# -15 per chart missing accent_index, -10 per chart with >6 colours
# -5 per donut with legend instead of direct labels

# Flow (0-100)
# +20 if first content slide is visual (kpi/chart/icon_stat)
# +15 if closing slide present
# +10 if section_dividers used between topic changes
# -10 per abrupt topic change (section field changes without divider)

# Density (0-100)
# Per slide: score based on item count vs capacity
# Penalty for <50% capacity utilisation (too sparse) or >90% (too dense)
# Average across all slides
```

### Interface

```python
from inkline.intelligence.quality_scorer import score_deck, QualityScore

score: QualityScore = score_deck(slides, brand=None)

# QualityScore:
#   total: int              — 0-100 weighted score
#   grade: str              — "A" (90+), "B" (75+), "C" (60+), "D" (40+), "F" (<40)
#   dimensions: dict[str, int]  — per-dimension scores
#   issues: list[str]       — specific deductions with explanations
#   suggestions: list[str]  — top 3 improvement actions
```

### Integration Points
- **Archon Phase 2b**: Run after anti-patterns. Score logged in Archon report.
  Score < 40 triggers warning. Score < 25 suggests regeneration.
- **Bridge response**: Score included in bridge JSON response for WebUI display.
- **Feedback system**: Score recorded per generation for trend tracking.

---

## Feature 3: Auto-Polish Pass

### Purpose
Deterministic post-processing that fixes minor quality issues without re-running the LLM.
Runs after anti-pattern detection and scoring, before Typst compilation. Think of it as
"auto-format for slide specs".

### Module
`inkline/intelligence/polish.py`

### Polish Rules

Each rule: `id`, `applies_to` (slide types), `fix(slide) → slide` (mutates in-place).

| ID | Rule | What it fixes |
|---|---|---|
| PL-01 | **Trim long titles** | Titles 46-60 chars: attempt smart truncation (remove articles, abbreviate). >60: truncate at word boundary + "..." |
| PL-02 | **Trim verbose bullets** | Items >100 chars: split at sentence boundary, keep first sentence |
| PL-03 | **Balance card heights** | three_card/four_card: if one card body is 3x longer than shortest, trim to match |
| PL-04 | **Remove empty cards** | Cards with empty body get body set to title (prevent blank space) |
| PL-05 | **Normalise stat values** | "$4,200,000" → "$4.2M", "15000" → "15K" (for kpi_strip, icon_stat, stat) |
| PL-06 | **Fix orphaned footnotes** | Footnote present but body is just "Source: ..." → move to footnote field |
| PL-07 | **Deduplicate section labels** | Same `section` value on adjacent slides → keep first, clear rest |
| PL-08 | **Chart accent inference** | Bar/grouped_bar missing accent_index → infer from highest value (already in TasteEnforcer R-05, promote to polish for all chart types) |
| PL-09 | **Sentence-case titles** | "THIS IS A TITLE" → "This Is a Title". Skip if intentionally styled (brand override) |
| PL-10 | **Strip trailing periods** | Bullet items and card bodies: remove trailing period for consistency |
| PL-11 | **Ensure closing contact** | If closing slide has empty email/role fields, fill from brand config if available |
| PL-12 | **Compact sparse tables** | Table with 1-2 columns and <3 rows → suggest conversion to kpi_strip (advisory only, no auto-fix) |

### Interface

```python
from inkline.intelligence.polish import polish_deck, PolishResult

result: PolishResult = polish_deck(slides, brand=None)

# PolishResult:
#   slides: list[dict]      — polished slides (mutated in-place, also returned)
#   applied: list[dict]     — rules applied: [{rule_id, slide_index, description, before, after}]
#   advisories: list[str]   — suggestions that weren't auto-applied (PL-12 etc.)
```

### Integration Points
- **Archon Phase 2c** (new phase, after scoring, before save_slide_spec):
  Run `polish_deck(slides)`. Applied fixes logged in Archon report.
- **TasteEnforcer**: Polish runs BEFORE TasteEnforcer (polish fixes content-level issues,
  taste enforcer fixes chart-level rendering directives). No overlap — complementary.
- Ordering: `DesignAdvisor → Anti-Patterns → Score → Polish → TasteEnforcer → Typst`

---

## Feature 4: Design Brief Generation

### Purpose
Before DesignAdvisor runs, generate a structured design brief from the input sections +
audience/goal metadata. The brief captures the **story arc**, **key message per section**,
and **visual strategy** — giving DesignAdvisor Phase 1 (plan) much better context.

This is the one feature that uses an **LLM call** (like Impeccable's `/shape` command).

### Module
`inkline/intelligence/design_brief.py`

### Brief Schema

```python
@dataclass
class DesignBrief:
    deck_purpose: str           # 1-2 sentence summary of what this deck achieves
    audience_profile: str       # Who will see this and what they care about
    story_arc: str              # 3-act structure: setup → evidence → ask
    key_message: str            # The single takeaway the audience should remember
    visual_strategy: str        # e.g. "data-heavy with charts", "narrative with infographics"
    section_briefs: list[dict]  # Per-section: {title, intent, suggested_exhibit, key_metric}
    tone: str                   # "formal", "conversational", "urgent", "celebratory"
    constraints: list[str]      # e.g. "max 15 slides", "no financial projections"
    anti_goals: list[str]       # What this deck should NOT do (e.g. "don't oversell")
```

### Generation Logic

**Single LLM call** with a focused prompt:

```
You are a presentation strategist. Given these input sections and context,
produce a design brief that will guide slide deck creation.

Input sections:
{sections_summary}  # title + first 200 chars of each section

Context:
- Audience: {audience}
- Goal: {goal}
- Brand: {brand}
- Constraints: {constraints}

Output a JSON object matching the DesignBrief schema.
Focus on:
1. What is the story arc? (What problem → what evidence → what ask)
2. For each section, what exhibit type best serves the message?
3. What visual strategy matches this audience? (investors want data, boards want summaries)
4. What should this deck explicitly NOT do?
```

**Fallback (no LLM):** Rules-based brief using heuristics:
- Audience "investors" → visual_strategy = "data-heavy", tone = "formal"
- Audience "team" → visual_strategy = "narrative", tone = "conversational"
- >5 sections with metrics → suggest chart-heavy
- <3 sections → suggest condensed executive format

### Interface

```python
from inkline.intelligence.design_brief import generate_brief, DesignBrief

brief: DesignBrief = generate_brief(
    sections=sections,
    audience="investors",
    goal="secure Series B term sheet",
    brand="aigis",
    constraints=["max 20 slides", "no revenue projections beyond 2027"],
)

# Brief is then passed to DesignAdvisor:
advisor = DesignAdvisor(brand="aigis", template="consulting", mode="llm")
slides = advisor.design_deck(
    title="Series B",
    sections=sections,
    brief=brief,  # NEW parameter — optional, enhances Phase 1 planning
)
```

### Integration Points
- **Archon Phase 0** (new phase, before parse_markdown): Generate brief from raw input.
  Brief stored in Archon context, passed to Phase 2.
- **DesignAdvisor._plan_deck_llm()**: If `brief` is provided, inject `brief.story_arc`,
  `brief.visual_strategy`, and `brief.section_briefs` into the Phase 1 planning prompt.
  This replaces the generic "prefer visuals" instruction with specific per-section guidance.
- **Bridge prompt**: When user provides audience/goal in the bridge prompt, extract and
  pass to `generate_brief()` automatically.

---

## Pipeline Integration — Updated Archon Phases

Current pipeline:
```
Phase 1: parse_markdown
Phase 2: design_advisor_llm
Phase 3: save_slide_spec
Phase 4: export_pdf_with_audit
```

New pipeline:
```
Phase 0: design_brief        (NEW — LLM call, optional)
Phase 1: parse_markdown
Phase 2: design_advisor_llm  (receives brief if available)
Phase 2b: anti_patterns       (NEW — deterministic check)
Phase 2c: quality_score       (NEW — deterministic scoring)
Phase 2d: polish              (NEW — deterministic fixes)
Phase 3: taste_enforcer       (existing, unchanged)
Phase 4: save_slide_spec
Phase 5: export_pdf_with_audit
```

The new phases (2b, 2c, 2d) add ~50ms total (pure Python, no LLM). Phase 0 adds one LLM
call (~2-5s) but is optional and can be skipped with `brief=None`.

---

## File Summary

| File | Action | Lines (est.) |
|---|---|---|
| `src/inkline/intelligence/anti_patterns.py` | NEW | ~350 |
| `src/inkline/intelligence/quality_scorer.py` | NEW | ~250 |
| `src/inkline/intelligence/polish.py` | NEW | ~300 |
| `src/inkline/intelligence/design_brief.py` | NEW | ~200 |
| `src/inkline/intelligence/design_advisor.py` | MODIFY | Add `brief` param to `design_deck()` and `_plan_deck_llm()` |
| `src/inkline/intelligence/__init__.py` | MODIFY | Export new modules |
| `CLAUDE.md` | MODIFY | Add new phases to pipeline reference |

---

## Implementation Order

1. `anti_patterns.py` — standalone, no dependencies
2. `quality_scorer.py` — standalone, uses same slide spec format
3. `polish.py` — standalone, operates on slide specs
4. `design_brief.py` — needs LLM routing (reuse DesignAdvisor's `_call_llm` pattern)
5. Wire into `design_advisor.py` — add `brief` parameter
6. Update `CLAUDE.md` pipeline reference
7. Update `__init__.py` exports

---

## Verification

1. `python3 -c "from inkline.intelligence.anti_patterns import check_anti_patterns"` — import check
2. `python3 -c "from inkline.intelligence.quality_scorer import score_deck"` — import check
3. `python3 -c "from inkline.intelligence.polish import polish_deck"` — import check
4. `python3 -c "from inkline.intelligence.design_brief import generate_brief"` — import check
5. Create a test deck with known bad patterns, verify anti-pattern detection catches them
6. Score the test deck, verify score reflects the issues
7. Polish the test deck, verify fixes are applied
8. Generate a brief for a sample section set, verify schema compliance

---

## Non-Goals

- **No changes to Typst renderers** — these features operate on slide specs, not Typst code
- **No new LLM calls for anti-patterns/scoring/polish** — deterministic only
- **No UI changes** — output goes through Archon logging and bridge JSON response
- **No breaking changes to DesignAdvisor API** — `brief` param is optional
- **No dependency additions** — pure Python, uses existing stdlib + dataclasses
