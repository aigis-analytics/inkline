# Visual-First Exhaustion Protocol (VFEP) — Inkline Slide Generation Spec

**Status:** Approved for implementation
**Date:** 2026-04-17
**Scope:** End-to-end fix for 8 structural defects observed in generated decks, plus introduction of the Visual-First Exhaustion Protocol that governs slide-type selection across the planning and rendering pipeline.

---

## Executive Summary

A root cause analysis of a recently generated Inkline deck found 15 of 17 problem slides collapsed to a single text-heavy `split` layout, the title and closing slides rendered nearly empty, and every output bore a hardcoded GitHub footer. The defects trace to four overlapping causes: (1) the planner is forbidden from selecting text layouts, which forces every chartless section into a downstream `split` fallback; (2) `layout_selector._alternative_layout` rotates between two text layouts rather than pushing the LLM toward visuals; (3) `MinimalBrand` hardcodes attribution text directly into the footer slot; and (4) the title/closing renderers lean on `#v(1fr)` with no adaptive content. This spec defines fixes for all eight issues, introduces the Visual-First Exhaustion Protocol (VFEP) — a five-tier cascade that demands a written exhaustion note before any text fallback — and adds a `plan_auditor.py` that rejects plans exceeding the 30 % text-fallback cap. The result is a planning system that treats `split` and `content` as residual layouts, not defaults.

---

## 1. Issue Inventory

### Issue 1 — Text Truncation by `_clamp`

**Problem.** `FIELD_LIMITS` in the renderer truncates text before Typst sees it, often well below the actual capacity of the slide region. Limits were estimated by eye and never validated against rendered PDFs.

**Root cause.** `src/inkline/typst/slide_renderer.py:218–223` (`_clamp`) and the `FIELD_LIMITS` dictionary at lines 235–360. Examples: `four_card.cards.title: 36`, `four_card.cards.body: 120`, `split.left.items: 55`.

**Fix.** Run a renderer-anchored revalidation pass per slide type. For each (slide_type, field), render a representative slide loaded with the maximum-allowed string and inspect the resulting PDF for line-break and box-overflow behaviour. Raise the limit until the next character would cause an `Auditor` overflow flag; freeze it one character below. Proposed starting points (to be confirmed by the test pass):

| Field | Current | Proposed |
|---|---|---|
| `four_card.cards.title` | 36 | 42 |
| `four_card.cards.body` | 120 | 145 |
| `split.left.items` | 55 | 65 |
| `split.right.items` | 55 | 65 |
| `three_card.cards.body` | 85 | 95 |
| `process_flow.steps.body` | 80 | 90 |

**Acceptance.** Every revised limit produces zero `OVERFLOW` audit flags on a stress deck where each field is filled to capacity. Truncation happens only when the LLM exceeds the new ceiling.

---

### Issue 2 — Hardcoded Footer Branding

**Problem.** Every generated deck (regardless of brand or audience) carries `Branded documents and decks · github.com/u3126117/inkline` in its footer.

**Root cause.** `src/inkline/brands/minimal.py:37` hardcodes the string into `footer_text`. `theme_registry.brand_to_typst_theme()` at `theme_registry.py:218` passes `brand.footer_text` straight into the theme dict, which the renderer injects into every slide footer beyond slide 1. There is no path to suppress it.

**Fix.** Split the concept into two fields on `BaseBrand`:

```python
class BaseBrand:
    footer_text: str = ""                # User attribution; empty by default
    attribution_text: str = ""           # Opt-in Inkline credit
    show_attribution: bool = False       # Default: no tool credit on external decks
```

In `MinimalBrand`:

```python
footer_text = ""                                                        # silent by default
attribution_text = "Branded documents and decks · github.com/u3126117/inkline"
show_attribution = False
```

`brand_to_typst_theme()` builds the rendered footer string as
`brand.footer_text` if non-empty, then appends `brand.attribution_text` only when `show_attribution=True`.

**Acceptance.** Default `inkline_generate_deck` runs produce a clean empty footer area on slides ≥2. Setting `show_attribution=True` re-enables the GitHub line. Brand subclasses can specify their own `footer_text` without touching attribution.

---

### Issue 3 — All 15 Problem Slides Resolved to `split`

**Problem.** Variety collapsed: every chartless section emitted the same two-column text layout.

**Root cause A.** `design_advisor.py:997–1002` lists `content`, `split`, `table`, `four_card`, `three_card` under `FORBIDDEN AT PLANNING TIME`. The planner cannot pick any of them, so the renderer falls back to its default — `split` — for every section without chart-ready data.

**Root cause B.** `layout_selector.py:215–228` defines `_alternative_layout`, which maps `content → split` and `split → content`. The "anti-monotony" function ping-pongs between the two text layouts.

**Root cause C.** `layout_selector.py:154–156` returns `"split"` for every Risk section that lacks RAG data.

**Root cause D.** `layout_selector.py:176–191` returns `"split"` for any MIXED-content section whose narrative exceeds 100 characters.

**Fix.** Replace the FORBIDDEN block with the VFEP planner instruction (see §3) so the planner is required to attempt visual extraction at four tiers before declaring a text fallback. Replace `_alternative_layout` with a tier-aware rotation map (see §3, Component 2). Replace the unconditional `split` returns in `_layout_for_risk` and `_layout_for_mixed` with a tier-aware extractor that examines the section text for metrics, sequences, contrasts, and groupings before falling back.

**Acceptance.** On the regression deck, no more than 30 % of non-structural slides resolve to `split` or `content`. No three consecutive slides share the same `slide_type`. Risk and MIXED sections without RAG data resolve to varied layouts depending on extracted features.

---

### Issue 4 — Sparse Title Slide

**Problem.** Title slides with short company name + tagline render as two empty halves split by a horizontal rule.

**Root cause.** `src/inkline/typst/slide_renderer.py:587–648` (`_title_slide`) wraps content in two `#v(1fr)` blocks with no secondary headline, no accent block, no adaptive spacing.

**Fix.** Add an optional `secondary_headline` field to the title-slide schema. When present, render below the horizontal rule at 14 pt. Lower the upper `#v(1fr)` to `#v(0.6fr)` when `secondary_headline` is present so the lower half is visually filled. Keep the existing layout when both subtitle and secondary_headline are empty.

```typst
#v(if (secondary_headline != none) { 0.6fr } else { 1fr })
// company / tagline / rule
#if (secondary_headline != none) [
  #v(20pt)
  #text(14pt, fill: muted)[#secondary_headline]
]
#v(1fr)
```

**Acceptance.** Title slides with `secondary_headline` set render with vertically balanced upper/lower regions. Title slides without it render unchanged from the current baseline.

---

### Issue 5 — Sparse Closing Slide

**Problem.** `_closing_slide` collapses to company name (44 pt) + tagline (12 pt) and leaves the lower half empty. Required `name`/`role`/`email` fields render literal blank lines when missing.

**Root cause.** `src/inkline/typst/slide_renderer.py:1036–1078` (`_closing_slide`) hard-requires the contact triple, uses `#v(1fr)` flanking the contact block, and offers no CTA/website field.

**Fix.** Extend the closing-slide schema with optional `cta` and `website` fields and add an empty-contact branch:

| Field present? | Render |
|---|---|
| `cta` | Bold accent-colour text at 16 pt, above the contact block |
| `website` | 10 pt muted, below the email line |
| All of `name`, `role`, `email` empty | Minimal closing: company + tagline centered with a decorative accent rule (no contact block) |

Adjust typography for visual balance: company name `44pt → 36pt`, tagline `12pt → 16pt`. The smaller name + larger tagline sit closer in scale and make a less top-heavy slide.

**Acceptance.** Closing slides with no contact fields render the minimal centered variant. Closing slides with `cta` and `website` render those above/below the contact block respectively. Manual side-by-side comparison shows visible improvement in vertical balance.

---

### Issue 6 — Layout Variety Collapse (Coupled With Issue 3)

**Problem.** Variety in the plan does not survive the layout-selection pass.

**Root cause.** Same as Issue 3, plus the absence of plan-time auditing. The planner has no visibility into the cumulative slide-type histogram; the selector has no memory of recent picks.

**Fix.** The new `plan_auditor.py` (see §3, Component 3) runs immediately after Phase 1 planning, computes the T5 ratio and consecutive-type runs, and rejects plans that exceed the 30 % cap or contain three-in-a-row repeats. Up to 2 LLM revision passes are issued before accepting the best attempt. The `plan_deck_flow` function in `layout_selector.py` maintains a sliding window of the last five slide types and passes it into `_alternative_layout(decision, history)` so the rotation considers recent choices.

**Acceptance.** Any plan with T5 ratio > 0.30 or with three consecutive identical types triggers a revision pass. After at most 2 retries, the audit either passes or accepts the best attempt with a logged warning. Regression deck shows ≥ 5 distinct slide types in any 8-slide window.

---

### Issue 7 — No Dark/Banking Themes

**Problem.** Every deck renders white, regardless of audience or industry. The `dark`, `boardroom`, `executive`, and `investor` templates exist in `theme_registry.SLIDE_TEMPLATES` but are never auto-selected.

**Root cause.** `src/inkline/app/mcp_server.py:69–70` hardcodes defaults `template="consulting"`, `brand="minimal"`. No audience/industry → theme mapping exists.

**Fix.** Add a `banking` template to `SLIDE_TEMPLATES`:

```python
"banking": {
    "desc": "Investment banking — navy header, dark content, muted gold accent",
    "title_bg_override": "#1B3060",
    "title_fg_override": "#FFFFFF",
    "accent_override": "#C9A84C",
    "bg_override": "#FFFFFF",
    "card_fill_override": "#F5F7FA",
    "surface_override": "#F5F7FA",
}
```

Add `_suggest_template_for_audience(audience: str) -> str` to `design_advisor.py` and call it at the top of `DesignAdvisor.design_deck()` when no template is supplied:

```python
AUDIENCE_THEME_MAP = {
    "investors":         "investor",
    "banking":           "banking",
    "investment_bank":   "banking",
    "board":             "boardroom",
    "executive":         "executive",
    "internal":          "consulting",
    "engineering":       "dark",
    "regulator":         "consulting",
    "client_pitch":      "consulting",
}

def _suggest_template_for_audience(audience: str) -> str:
    return AUDIENCE_THEME_MAP.get((audience or "").lower(), "consulting")
```

**Acceptance.** Calling `inkline_generate_deck(audience="investment_bank")` without explicit `template=` produces a deck rendered in the `banking` theme. Calling without `audience` defaults to `consulting`. Existing explicit `template=` callers are unaffected.

---

### Issue 8 — `_alternative_layout` Doesn't Provide Real Alternatives

**Problem.** `_alternative_layout` is supposed to break monotony but the alternatives map is empty for the most common offender (`split`), maintains no state, and can return the same alternative repeatedly.

**Root cause.** `layout_selector.py:215–228`. `split` is missing from the alternatives dict, so it falls through to the default `content` — another text layout. The function takes no history parameter, so consecutive calls return identical results.

**Fix.** Replace with a tier-aware rotation table keyed by current type, returning the next entry from a list — selected by `(history-aware index) mod len(list)`:

```python
ALTERNATIVES = {
    "split":      ["comparison", "feature_grid", "process_flow", "three_card"],
    "content":    ["bar_chart",  "feature_grid", "icon_stat",     "comparison"],
    "four_card":  ["feature_grid", "icon_stat", "three_card",   "bar_chart"],
    "three_card": ["feature_grid", "comparison", "icon_stat",   "process_flow"],
    "table":      ["bar_chart",  "kpi_strip",   "stat",          "dashboard"],
    "stat":       ["kpi_strip",  "icon_stat",   "dashboard",     "bar_chart"],
    "chart":      ["multi_chart", "dashboard",  "kpi_strip",     "comparison"],
}

def _alternative_layout(current: str, history: list[str]) -> str:
    options = ALTERNATIVES.get(current, ["bar_chart", "comparison", "feature_grid"])
    # Skip options already in the recent history; if all are exhausted, fall back to first.
    for option in options:
        if option not in history[-3:]:
            return option
    return options[0]
```

**Acceptance.** `_alternative_layout("split", history=[...])` never returns `content` as the first choice and never returns the same value twice in a row when alternatives remain. Unit tests cover all seven keys.

---

## 2. The Visual-First Exhaustion Protocol (VFEP)

VFEP is the planning discipline that governs the entire pipeline. The principle: **text-heavy layouts are residual**. They are what remains after a section has demonstrably failed to yield a quantitative, sequential, comparative, or categorical visual representation.

### 2.1 The Five-Tier Exhaustion Stack

```
┌─────────────────────────────────────────────────────────────────┐
│ TIER 1 — QUANTITATIVE VISUAL                                    │
│   layouts: chart_caption, bar_chart, kpi_strip, stat,           │
│            dashboard, multi_chart                               │
│   trigger: ANY numbers, %, monetary, durations, counts          │
├─────────────────────────────────────────────────────────────────┤
│ TIER 2 — SEQUENCE / JOURNEY                                     │
│   layouts: process_flow, timeline                               │
│   trigger: chronological chain, causal progression, stages      │
├─────────────────────────────────────────────────────────────────┤
│ TIER 3 — COMPARISON / CONTRAST                                  │
│   layouts: comparison, three_card (before/after variant)        │
│   trigger: binary or ranked contrast — old vs new, X vs Y       │
├─────────────────────────────────────────────────────────────────┤
│ TIER 4 — GROUPED CATEGORIES / INFOGRAPHIC                       │
│   layouts: feature_grid, icon_stat, three_card, four_card*      │
│   trigger: 3–6 distinct enumerable items + natural icons        │
│   *visual variant only (with icons/visual emphasis)             │
├─────────────────────────────────────────────────────────────────┤
│ TIER 5 — STRUCTURED TEXT (LAST RESORT)                          │
│   layouts: split, content                                       │
│   requires: written exhaustion note for T1–T4                   │
│   cap:      ≤ 30 % of non-structural slides in any deck         │
└─────────────────────────────────────────────────────────────────┘
```

Worked examples:

| Content snippet | Tier hit | Layout |
|---|---|---|
| "£415k per APP-fraud case" | T1 (currency, count) | `stat` |
| "95 % false positive rate" | T1 (percentage) | `kpi_strip` |
| "device drift → payee search → micro-payment → transfer" | T2 (4-step flow) | `process_flow` |
| "Static model sees snapshot; RadarSeq sees trajectory" | T3 (X vs Y) | `comparison` |
| "4 signal dimensions: utilisation, MCC spend, DD failure, balance drift" | T4 (4 enumerated) | `feature_grid` |
| "Working-capital squeeze deepens as directors loan personal funds, then HMRC payments slip" | T2 (3-stage progression) | `process_flow` |

### 2.2 Architecture

```
┌───────────────────────────────────┐
│  DesignAdvisor.design_deck()      │
└────────────────┬──────────────────┘
                 │
                 ▼
       ┌─────────────────────┐
       │  Phase 1: PLAN      │  prompt now contains VFEP stack
       │  (LLM call)         │  exhaustion notes required for T5
       └─────────┬───────────┘
                 │ slides[]
                 ▼
       ┌─────────────────────┐
       │  plan_auditor       │  ▲  rejects plan if
       │  audit_plan()       │  │   - T5 ratio > 0.30
       └─────────┬───────────┘  │   - 3+ consecutive same type
                 │               │   - missing exhaustion notes
        pass ◄───┤               │
                 │ fail (≤2 retries)
                 ▼               │
       ┌─────────────────────┐  │
       │  Phase 1 retry      │──┘
       │  with violations    │
       └─────────┬───────────┘
                 │
                 ▼
       ┌─────────────────────┐
       │  Phase 2: per-slide │
       │  layout_selector    │  history-aware rotation
       └─────────┬───────────┘
                 │
                 ▼
              renderer
```

### 2.3 Component 1 — `design_advisor.py` Planner Prompt

Replace `design_advisor.py:997–1002` (`FORBIDDEN AT PLANNING TIME` block) with the VFEP instruction block:

```
═══════════════════════════════════════════════════════════════
VISUAL-FIRST EXHAUSTION PROTOCOL (VFEP) — MANDATORY
═══════════════════════════════════════════════════════════════
For EVERY content section, attempt visual extraction in tier order.
You may NOT assign split/content/four_card without a written T1–T4
exhaustion note.

T1 — METRICS: numbers, %, monetary, durations, counts?
     YES → chart_caption | dashboard | kpi_strip | stat | bar_chart | multi_chart

T2 — SEQUENCE: progression, journey, stages?
     YES → process_flow | timeline (or one panel of multi_chart)

T3 — CONTRAST: before/after, old/new, X-vs-Y?
     YES → comparison or two-panel chart_caption

T4 — CATEGORIES: 3–6 labelled items with natural icons?
     YES → feature_grid | three_card | icon_stat

T5 — TEXT FALLBACK: only after T1–T4 all fail. Use split or content.
     REQUIRED note: "T1: <reason>. T2: <reason>. T3: <reason>.
                     T4: <reason>. Using split."

HARD CAP: ≤ 30 % of non-structural slides may be T5.
If your plan exceeds this, revise upward — find visual angles you missed.

NOTE: four_card and three_card are VISUAL only when their cards have
icons / visual emphasis. Plain-text four_card (title + body only) counts
as T5 for cap purposes.
═══════════════════════════════════════════════════════════════
```

The structured slide JSON gains an optional `notes` field. Auditing checks the field for the `"T1: … T2: … T3: … T4: …"` pattern when `slide_type ∈ {split, content}` or when a card layout appears without per-card icons.

### 2.4 Component 2 — `layout_selector.py` Tier-Aware Rotation

Add a `VisualTier` enum:

```python
class VisualTier(IntEnum):
    QUANTITATIVE = 1
    SEQUENCE     = 2
    CONTRAST     = 3
    CATEGORICAL  = 4
    TEXT         = 5

LAYOUT_TIER = {
    "chart_caption": 1, "bar_chart": 1, "kpi_strip": 1, "stat": 1,
    "dashboard": 1, "multi_chart": 1, "chart": 1,
    "process_flow": 2, "timeline": 2,
    "comparison": 3,
    "feature_grid": 4, "icon_stat": 4, "three_card": 4, "four_card": 4,
    "split": 5, "content": 5, "table": 5,
}
```

Add a sliding-window history to `plan_deck_flow`:

```python
def plan_deck_flow(decisions: list[Decision]) -> list[str]:
    chosen: list[str] = []
    history: deque[str] = deque(maxlen=5)
    for d in decisions:
        layout = _select_layout(d, history)
        if _three_in_a_row(history, layout):
            layout = _step_up_tier(d, history)   # force tier ↑
        chosen.append(layout)
        history.append(layout)
    return chosen
```

`_step_up_tier` re-asks the selector for a layout with `tier <= current_tier - 1`, walking up the stack until a viable layout is found. If none is viable (the section truly has no visual content), the layout is kept and the plan_auditor logs a violation that surfaces in the next revision pass.

### 2.5 Component 3 — New `plan_auditor.py`

New file: `src/inkline/intelligence/plan_auditor.py`.

```python
@dataclass
class PlanAuditResult:
    passed: bool
    violations: list[str]
    t5_ratio: float
    consecutive_violations: list[tuple[int, str]]   # (start_index, slide_type)
    missing_exhaustion_notes: list[int]             # slide indices
    recommendation: str

def audit_plan(slides: list[dict], sections: list[dict]) -> PlanAuditResult:
    """Audit a Phase 1 plan against VFEP rules.

    Rejects plans with:
      - T5 ratio > 0.30 (excluding title + closing + section_divider)
      - 3+ consecutive identical slide_types
      - T5 slide_type without an exhaustion note matching the T1–T4 pattern
    """
```

Integration: `DesignAdvisor._plan_deck_llm()` runs `audit_plan` after the LLM returns. If `passed=False`, the violation list and per-slide notes are appended to the planner prompt and the call is reissued. Maximum 2 retries; on the third attempt the best of the three plans (lowest violation count) is accepted with a `WARNING` logged to the Archon audit trail. The retry prompt explicitly names the offending slides and quotes the cap that was breached, so the LLM has concrete edits to make.

---

## 3. Quality Gates

A change set is considered "done" when **every** item below is verified on the regression deck used to surface the original 8 issues:

| Gate | Measurement | Target |
|---|---|---|
| G-1 Truncation | `_clamp` calls per deck | 0 (all fields fit within new `FIELD_LIMITS`) |
| G-2 Footer | Default-brand footer text | Empty for all slides ≥ 2 |
| G-3 Variety | Distinct `slide_type` count in any 8-slide window | ≥ 5 |
| G-4 Title balance | Vertical fill ratio of title slide | ≥ 0.55 |
| G-5 Closing balance | Vertical fill ratio of closing slide | ≥ 0.55 |
| G-6 Variety (audit) | T5 ratio across non-structural slides | ≤ 0.30 |
| G-7 Banking theme | `audience="investment_bank"` deck | Renders in `banking` theme |
| G-8 Rotation | `_alternative_layout` consecutive identical returns | 0 across 100 calls with varied history |
| G-9 VFEP enforcement | Plans with T5 ratio > 0.30 | Rejected at audit, retried up to 2× |
| G-10 Exhaustion notes | T5 slides | 100 % carry the `T1: … T2: … T3: … T4: …` note |

Pre-merge checklist:
1. `pytest tests/intelligence/test_plan_auditor.py` — all green
2. `pytest tests/typst/test_field_limits.py` — all green
3. `pytest tests/intelligence/test_layout_selector.py::test_alternative_rotation` — all green
4. Render the regression deck via `inkline_generate_deck(...)` and confirm gates G-1 through G-10 by inspection.
5. Render a banking deck via `inkline_generate_deck(audience="investment_bank")` and confirm theme application.
6. Render a deck with empty contact fields and confirm closing-slide minimal variant.

---

## 4. Implementation Order

| # | Task | Files | Depends on |
|---|---|---|---|
| 1 | Footer split (`footer_text` / `attribution_text` / `show_attribution`) | `brands/base.py`, `brands/minimal.py`, `theme_registry.py` | — |
| 2 | `banking` template + `_suggest_template_for_audience` | `theme_registry.py`, `design_advisor.py`, `app/mcp_server.py` | — |
| 3 | Title slide `secondary_headline` + adaptive spacing | `typst/slide_renderer.py` | — |
| 4 | Closing slide `cta` / `website` / minimal variant + typography re-balance | `typst/slide_renderer.py` | — |
| 5 | `_alternative_layout` rotation rewrite + history plumbing in `plan_deck_flow` | `layout_selector.py` | — |
| 6 | `LAYOUT_TIER` + `VisualTier` enum + `_step_up_tier` | `layout_selector.py` | 5 |
| 7 | New `plan_auditor.py` module | `intelligence/plan_auditor.py` | 6 |
| 8 | VFEP planner prompt block + retry loop in `_plan_deck_llm()` | `design_advisor.py` | 7 |
| 9 | Tier-aware overrides in `_layout_for_risk` and `_layout_for_mixed` (replace unconditional `split`) | `layout_selector.py` | 6 |
| 10 | `FIELD_LIMITS` revalidation pass + new ceilings | `typst/slide_renderer.py`, `tests/typst/test_field_limits.py` | — |
| 11 | Wire all gates into the regression test suite | `tests/` | 1–10 |

Tasks 1–4 are independent and can land first; 5–8 form the VFEP core and must land together; 9 follows once VFEP is in place; 10 is independent and benefits from being validated against VFEP-shaped plans. Total: ~11 discrete tasks, expected ~3 working days end-to-end.

---

## 5. Non-Goals

- **No new chart renderers.** All visual layouts referenced (chart_caption, dashboard, multi_chart, comparison, feature_grid, icon_stat, etc.) already exist; VFEP only changes selection discipline.
- **No new LLM dependencies.** The retry loop reuses the existing planner LLM call path; `plan_auditor` is pure Python.
- **No brand-by-brand footer migration in this spec.** Only `MinimalBrand` is updated; other brands keep their existing strings until they opt in by setting `show_attribution=False`.
- **No automatic regeneration when the third audit attempt fails.** The best-of-three plan is accepted with a logged warning; the user can call `inkline_regenerate` if needed.
- **No change to the Typst chart renderers.** This spec operates above the renderer surface.
