# Gap Closure Specification

**Date:** 17 April 2026
**Status:** Approved for implementation
**Scope:** Six priority groups closing gaps identified in `design-sources-and-philosophy.md`

---

## Status Table

| ID | Item | Priority | Effort | Status |
|----|------|----------|--------|--------|
| 1.1 | Senior designer role framing in system prompt | P1 | XS | Pending |
| 1.2 | Decision-sequence framework in SLIDE_TYPE_GUIDE | P1 | S | Pending |
| 1.3 | Mandatory 3-step quality check in Phase 1 | P1 | S | Pending |
| 1.4 | Before/after examples in SLIDE_TYPE_GUIDE | P1 | S | Pending |
| 1.5 | Make design_brief mandatory for decks ≥5 sections | P1 | S | Pending |
| 1.6 | UPGRADE trigger for opener/exec summary slides | P1 | S | Pending |
| 1.7 | Tier 1B ≥15% requirement in Vishwakarma | P1 | S | Pending |
| 2.1 | New anti-patterns: TP-07, SP-05, DP-04, DP-05, DP-03 upgrade, AP-05, AP-06 | P2 | M | Pending |
| 2.2 | Quality scoring dimensions 7 & 8 + chart annotation check | P2 | M | Pending |
| 3.1 | Tighten PL-02 for chart-context bullets | P3 | S | Pending |
| 3.2 | PL-13 financial abbreviation normalization | P3 | S | Pending |
| 3.3 | Tighten character limits (content 80→70, card 85→75, fn 90→80) | P3 | XS | Pending |
| 3.4 | Font weight tokens in brand schema | P3 | S | Pending |
| 4.1 | `credentials` tombstone slide type | P4 | M | Pending |
| 4.2 | `testimonial` slide type | P4 | S | Pending |
| 4.3 | `before_after` slide type | P4 | S | Pending |
| 5.1 | `bump_chart` chart type | P5 | M | Pending |
| 5.2 | `staircase` chart type | P5 | XS | Pending |
| 5.3 | `marimekko` quality check (already implemented) | P5 | XS | Done |
| 6.1 | Decision matrix YAML + wire into DesignAdvisor | P6 | S | Done (YAML exists) |
| 6.2 | `inkline learn` CLI command (full implementation) | P6 | S | Done (stub exists) |
| 6.3 | Implicit feedback parser in bridge | P6 | S | Pending |
| 6.4 | Complete pattern_memory.py with record_pattern/get_preferred_types | P6 | M | Pending |

---

## Priority 1 — LLM Prompt Improvements

### 1.1 Role framing
**File:** `design_advisor.py` — prepend to `_build_system_prompt()` return value (or to the
`SLIDE_TYPE_GUIDE` string at the top, before the prime directive block).

Text to prepend:
```
You are a senior presentation designer who has built investor and board decks for top-tier
professional services clients. Your default reflex is visual, not textual. You make confident
design decisions without hedging.
```

### 1.2 Decision-sequence framework
Replace or augment the current three-step chart selection block with a slide-type decision
sequence. Add it to `SLIDE_TYPE_GUIDE` between the PRIME DIRECTIVE and the HARD CAPACITY LIMITS:

```
SLIDE TYPE DECISION SEQUENCE (follow in order):

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
  4-8 tombstone items         → credentials
  complex multi-facet data    → multi_chart (pick layout by count)
```

### 1.3 Quality check injection
After `_build_plan_user_prompt()` constructs the planning prompt, append:

```
Before returning your slide plan, run this three-step check:
1. TIER CHECK: Count slides by tier. If tier-5 (content) > 1, return to those slides
   and convert the weakest to tier 1 or 2.
2. CONSOLIDATION CHECK: Find any two adjacent slides covering related data facets.
   Can they share a multi_chart layout? If yes, consolidate.
3. ACTION TITLE CHECK: Verify every slide title contains at least one of: a
   number/metric, a comparison word (more, fewer, higher, faster, lower), or a direction
   word (grew, declined, exceeded, fell, surpassed). If not, rewrite to state the insight.
Only return your JSON after completing this check.
```

Inject at the end of the user prompt in `_plan_deck_llm()`.

### 1.4 Before/after examples
Add to `SLIDE_TYPE_GUIDE` after the SLIDE TYPE CATALOGUE section:

```
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
```

### 1.5 Mandatory design_brief
In `design_deck()`, before calling `_design_deck_llm()`: if `brief is None` and
`len(sections) >= 5`, generate a default brief:

```python
if brief is None and len(sections) >= 5:
    brief = generate_brief(
        sections=sections, goal=goal or "Board-level audience; goal: clear decision support.",
        audience=audience or "Board-level audience",
        title=title,
    )
```

### 1.6 Opener upgrade instruction
Add to `_build_plan_system_prompt()` output (after PLANNING RULES):

```
OPENER RULE — first two content slides after title:
For the first two content slides, and for any section with a single dominant insight,
use a single bold exhibit (stat, icon_stat with display_xl, or a Tier 1B structural
infographic). Do NOT use multi_chart for these slides. The opener must create visual impact.
```

### 1.7 Tier 1B minimum
In `vishwakarma.py`, update `VISHWAKARMA_SYSTEM_PREAMBLE` scoring block:
- Existing: `TIER 1A+1B (infographic): should be ≥ 20% of content slides`
- Change to two separate lines:
  - `TIER 1A (KPI callout): should be ≥ 10% of content slides`
  - `TIER 1B (structural infographic): should be ≥ 15% of content slides`

Update AMBITION CHECK: add after the UPGRADE step:
```
  TIER 1B CHECK — count radial_pinwheel, hexagonal_honeycomb, waffle, iceberg,
  funnel_kpi_strip, persona_dashboard, dual_donut, ladder, and pyramid_detailed slides.
  If count / content_slides < 0.15, add at least one 1B infographic.
```

---

## Priority 2 — Anti-Patterns & Quality Scoring

### 2.1 New anti-patterns (`anti_patterns.py`)

**TP-07** — Action title verification
- Skip: title, closing, section_divider
- Flag if title has NO digit, NO comparison word, NO direction word → warning
- Comparison words: more, fewer, higher, lower, faster, slower, better, worse, greater, less, above, below
- Direction words: grew, declined, rose, fell, increased, decreased, exceeded, surpassed, outperformed, underperformed, improved, worsened, gained, lost

**SP-05** — Appendix problem detection
- content_count = slides with slide_type in (content, table)
- multi_chart_count = slides with slide_type == multi_chart
- If content_count > 0.30 * total_content_slides AND multi_chart_count < 0.15 * total_content_slides → warning

**DP-04 (new)** — Data dump (no dominant element)
- NOTE: existing DP-04 is "Time series with <3 data points" — this becomes a NEW check.
- For chart, chart_caption, dashboard, multi_chart slides: check if accent_index OR stat callout OR non-empty bullets. None present → warning.
- To avoid conflict, rename this DP-06 (since DP-04 is taken).

**DP-05** — Apology footnote
- Scan footnote field for: approximate, estimated, assumed, subject to change, indicative, not guaranteed → warning

**DP-03 upgrade** — Orphaned number severity
- When template is investor, pitch, or boardroom AND metrics found in narrative → error (not warning)
- Otherwise keep as warning
- The template context is passed via optional `template` parameter to `check_anti_patterns()`

**AP-05** — Symmetric deck (low visual rhythm)
- Compute sequence of slide types for content slides only
- If std dev of type-change count < 1.5 AND deck ≥ 8 slides → warning

**AP-06** — Section transition without divider
- Improve LP-04 which already does this at "info" level
- Add AP-06 as a "warning" level version: consecutive slides from different sections with no divider → warning (upgrade from LP-04 info)

### 2.2 Quality scoring additions (`quality_scorer.py`)

**Dimension 7: Narrative Continuity (weight: 0.08)**
- Score = 1.0 - (unsignalled_transitions / max(1, total_transitions))
- Reduce other weights proportionally (all 6 current weights × 0.92 ≈ 0.184/0.184/0.138/0.138/0.138/0.138 → sum = 0.92)

**Dimension 8: Visual Boldness (weight: 0.08)**
- INFOGRAPHIC_TYPES: radial_pinwheel, hexagonal_honeycomb, waffle, iceberg, funnel_kpi_strip, persona_dashboard, dual_donut, ladder, pyramid_detailed
- +0.2 per Tier 1B slide (capped at 1.0)
- +0.1 per chart slide with accent_index set
- -0.1 per content slide beyond first

**Chart annotation check**
- In audit: for each chart/chart_caption/dashboard slide, check that at least one of caption, bullets (non-empty), stats (non-empty) is present. If none → log warning.

---

## Priority 3 — Polish Improvements

### 3.1 PL-02 chart-context tightening
In `_pl02_trim_verbose_bullets()`:
- Detect parent slide type is chart_caption, dashboard, chart, multi_chart
- In that context: after trimming to first sentence, further trim to ≤8 words
- Strip sentence-ending punctuation

### 3.2 PL-13 Financial abbreviation normalization
New rule, applied to: chart labels (chart_data fields), bullet text (items), caption, table headers/cells, slide titles.

Substitutions (case-insensitive, word-boundary aware):
- Year + (Forecast|Estimate|Actual|Actuals|Budget) → Year + F/E/A/B
- USD billion / US$ billion / $ billion → USDbn
- USD million / US$ million / $ million → USDm
- USD thousand → USDk
- basis points → bps
- year-on-year / year on year → YoY
- quarter-on-quarter / quarter on quarter → QoQ
- compound annual growth rate → CAGR
- earnings before interest... (EBITDA long form) → EBITDA

### 3.3 Character limit tightening
In both `anti_patterns.py` and `quality_scorer.py`:
- content bullet items: 80 → 70 chars
- three_card/four_card card body: 85 → 75 chars
- footnote: 90 → 80 chars

### 3.4 Font weight tokens
Add to `BaseBrand` dataclass:
- `heading_weight: int = 700`
- `body_weight: int = 400`
- `muted_weight: int = 300`

Docstring note: "Templates should use these tokens for font-weight rather than hardcoding."

---

## Priority 4 — New Slide Types

### 4.1 `credentials`
Grid of 4-8 tombstone cells (2 rows × 2-4 cols). Renderer: Typst table or grid.

Data shape:
```python
{
  "slide_type": "credentials",
  "data": {
    "section": str,
    "title": str,
    "tombstones": [{"name": str, "detail": str}],  # 4-8 items
    "footnote": str | None
  }
}
```

Anti-pattern: warn if < 4 or > 8 tombstones.
Add to SLIDE_TYPES list and SLIDE_TYPE_GUIDE.
Add Typst renderer in `slide_renderer.py`.

### 4.2 `testimonial`
Large pull-quote with attribution. Quote at ~26pt italic. Attribution in smaller muted text.

Data shape:
```python
{
  "slide_type": "testimonial",
  "data": {
    "section": str,
    "quote": str,          # ≤200 chars
    "attribution": str,    # ≤60 chars
    "image_path": str | None,
    "footnote": str | None
  }
}
```

### 4.3 `before_after`
Two equal panels: Before (left) and After (right). Each panel has 3-5 bullet items.

Data shape:
```python
{
  "slide_type": "before_after",
  "data": {
    "section": str,
    "title": str,
    "left": {"label": str, "items": [str], "colour": str},
    "right": {"label": str, "items": [str], "colour": str},
    "footnote": str | None
  }
}
```

---

## Priority 5 — New Chart Types

### 5.1 `bump_chart`
Inverted Y-axis rank chart. Lines cross to show ranking changes. In `chart_renderer.py`.

Data:
```python
{"chart_type": "bump_chart", "chart_data": {
    "x": ["Q1", "Q2", "Q3"],
    "series": [{"name": str, "values": [int]}]  # rank at each period (1=best)
}}
```

Style: thick lines (3pt), distinct palette colours, rank labels on right, minimal axes.

### 5.2 `staircase`
Line chart with `drawstyle='steps-post'`. Same data format as `line_chart`. Add to
`chart_renderer.py` as a trivial variant of the existing line chart renderer.

### 5.3 `marimekko`
Already implemented (`_render_marimekko`). Verify it renders correctly — no action needed.

---

## Priority 6 — Infrastructure

### 6.1 Decision matrix YAML
File already exists at `intelligence/decision_matrix_default.yaml`.
Wire into `DesignAdvisor.__init__()`: load it and expose as `self.decision_matrix`.
Inject summary into `_build_plan_system_prompt()` as a compact reference block.

### 6.2 `inkline learn` CLI
Already stubbed in `cli.py` calling `Aggregator().run_full_pass()`.
Enhance to: scan feedback_log.jsonl, print summary, print pattern count. Already sufficient.

### 6.3 Implicit feedback parser
In `claude_bridge.py`, in the prompt handler: add a regex pass over incoming prompt text
to detect implicit feedback signals. Log to `~/.local/share/inkline/feedback_log.jsonl`.

Signals:
- "make it more visual" → `too_textual`
- "reduce text" / "less text" → `too_verbose`
- "too many slides" → `too_many_slides`
- "change the template" → `template_change`
- "the title is wrong" / "fix the title" → `bad_title`

### 6.4 `pattern_memory.py` additions
Add three new public functions to the existing module (which already has add_pattern, etc.):

- `record_pattern(brand, slide_type, section_type, approved=True)` — logs to per-brand YAML
- `get_preferred_types(brand, section_type)` — returns ordered list by approval rate
- `get_pattern_summary(brand)` — returns dict of all patterns for a brand

The YAML format uses a simple patterns list compatible with existing `load_brand_patterns()`.

---

## Post-Implementation Test Plan

```bash
# Import checks
python -c "from inkline.intelligence import DesignAdvisor, audit_deck; print('intelligence OK')"
python -c "from inkline.intelligence.anti_patterns import check_anti_patterns; print('anti_patterns OK')"
python -c "from inkline.intelligence.polish import apply_polish; print('polish OK')"
python -c "from inkline.intelligence.quality_scorer import score_deck; print('quality_scorer OK')"

# Unit tests
python -m pytest tests/ -x -q
```

### New slide type sanity
```python
from inkline.intelligence.anti_patterns import check_anti_patterns
slides = [
    {"slide_type": "credentials", "data": {"title": "Track record", "tombstones": [
        {"name": "Project A", "detail": "$100M | 2024"} for _ in range(5)
    ]}},
    {"slide_type": "testimonial", "data": {"quote": "Great product", "attribution": "CEO, Acme"}},
    {"slide_type": "before_after", "data": {"title": "T", "left": {"label": "Before", "items": ["a","b","c"]}, "right": {"label": "After", "items": ["x","y","z"]}}},
]
results = check_anti_patterns(slides)
print("Credentials/testimonial/before_after AP check:", len(results), "issues")
```

### New anti-patterns sanity
```python
slides = [{"slide_type": "content", "data": {"title": "Overview", "items": ["Bullet one", "Bullet two"]}}]
results = check_anti_patterns(slides)
tp07_hits = [r for r in results if r.rule_id == "TP-07"]
print("TP-07 action title check:", len(tp07_hits), "hits (expect 1)")
```

### Quality scorer sanity
```python
from inkline.intelligence.quality_scorer import score_deck
slides = [{"slide_type": "content", "data": {"title": "T", "items": ["x"]}}]
score = score_deck(slides)
assert "narrative_continuity" in score.dimensions
assert "visual_boldness" in score.dimensions
print("Quality scorer dimensions:", list(score.dimensions.keys()))
```
