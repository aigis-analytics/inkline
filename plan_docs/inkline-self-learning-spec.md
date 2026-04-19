# Inkline Self-Learning & Adaptive Improvement — Complete Architecture Spec

**Status:** Proposed
**Model:** claude-opus-4-6
**Date:** 2026-04-19
**Scope:** End-to-end self-learning from generation signals through federated community patterns

---

## 0. Purpose and Framing

Inkline already ships a substantial foundation for self-improvement: `pattern_memory.py`,
`feedback.py`, `aggregator.py`, `anti_patterns.py`, `quality_scorer.py`, `polish.py`,
`design_brief.py`, `deck_analyser.py`, the `inkline_submit_feedback` MCP tool, the
`_record_implicit_feedback` bridge hook, and the `inkline learn` CLI command.

What is missing is a **unified, persistent, structured signal capture layer** — the
plumbing that automatically records every generation event with enough context for the
aggregator to learn from it, even when no explicit feedback is provided.

This spec defines:

1. A **generation session log** (SQLite) that records every deck generation with quality
   scores and enough context to reconstruct what the system chose and why.
2. A **signal capture bridge** that automatically files a feedback event for every slide
   accepted without modification.
3. **Title rewrite learning** — detecting when a user rewrites a title and extracting a
   pattern from the before/after pair.
4. **Anti-pattern accumulation** — automatically recording when a slide goes through
   multiple regeneration cycles (implicit rejection).
5. **Audience and section-type memory** — per-brand, per-audience layout preferences that
   feed DesignAdvisor before the LLM runs.
6. A **federated community layer** — opt-out anonymised pattern delta export (safe
   structural signals only, no content) and community-seeded starter patterns bundled
   with the public repo. Sharing is on by default; users who want full local isolation
   can disable with one config flag.
7. Integration points with the existing `design-system-spec.md` (approved) and the
   `impeccable-design-intelligence-spec.md` (approved).

---

## 1. What Already Exists (Do Not Duplicate)

The following are **implemented and should not be re-architected**, only extended:

| Module | Location | Status |
|---|---|---|
| Pattern memory (per-brand YAML) | `intelligence/pattern_memory.py` | Implemented |
| Explicit feedback capture | `intelligence/feedback.py` | Implemented |
| Decision matrix aggregator | `intelligence/aggregator.py` | Implemented |
| Anti-pattern library | `intelligence/anti_patterns.py` | Implemented |
| Quality scorer (6 dimensions) | `intelligence/quality_scorer.py` | Implemented |
| Auto-polish pass | `intelligence/polish.py` | Implemented |
| Design brief generation | `intelligence/design_brief.py` | Implemented |
| Reference deck analyser | `intelligence/deck_analyser.py` | Implemented |
| `inkline_submit_feedback` MCP tool | `app/mcp_server.py` | Implemented |
| `inkline_ingest_reference_deck` MCP tool | `app/mcp_server.py` | Implemented |
| Implicit feedback from bridge chat | `app/claude_bridge.py` | Implemented |
| `inkline learn` CLI command | `app/cli.py` | Implemented |
| Pattern injection into DesignAdvisor prompts | `intelligence/design_advisor.py` | Implemented |

**The gap:** None of the above automatically fires when a deck is generated and accepted
silently. The feedback system only captures events when the user explicitly calls
`inkline_submit_feedback`, types a correction in the bridge, or runs `inkline feedback`.
This means 90%+ of generation sessions produce zero learning signal.

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│  SIGNAL SOURCES (what produces data)                                │
│                                                                     │
│  A. Generation Hook          B. Session History       C. Deck Diff  │
│     Every design_deck()         SQLite log every         Before/    │
│     call auto-logs              generation + score       after diff  │
│     context + DM rule                                               │
│     choices                  D. Title Rewrite         E. Regen Count│
│                                 Detector                 Anti-pattern│
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│  SIGNAL STORE (~/.local/share/inkline/learning/)                    │
│                                                                     │
│  sessions.db (SQLite)                                               │
│  ├── generation_sessions    — one row per design_deck() call        │
│  ├── slide_choices          — one row per slide in the deck         │
│  ├── title_rewrites         — before/after title pairs              │
│  └── regen_counts           — per (brand, slide_type) regen counts  │
│                                                                     │
│  (existing, unchanged)                                              │
│  feedback_log.jsonl         — explicit + implicit feedback events   │
│  patterns/{brand}.yaml      — learned brand patterns                │
│  decision_matrix.yaml       — chart type decision rules             │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│  PATTERN EXTRACTION PIPELINE (learning/extractor.py)                │
│                                                                     │
│  Background job (nightly via `inkline learn --full`) OR on-demand   │
│                                                                     │
│  1. Session acceptance rate → update DM rule confidence             │
│  2. Title rewrite patterns → add to brand pattern memory            │
│  3. Regen count threshold  → flag anti-pattern to pattern_memory    │
│  4. Audience layout stats  → per-audience preference table          │
│  5. Section-type stats     → update get_preferred_types() backing   │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│  INJECTION POINTS (where learned data flows back into generation)   │
│                                                                     │
│  DesignAdvisor._build_system_prompt()   ← pattern_memory YAML      │
│  DesignAdvisor._plan_deck_llm()         ← audience layout prefs     │
│  decision matrix in DesignAdvisor       ← aggregator confidence     │
│  anti_patterns.check_anti_patterns()   ← accumulated regen flags   │
└─────────────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│  FEDERATED LAYER (opt-out, community improvement)                   │
│                                                                     │
│  Local: all of the above                                            │
│  Export: anonymised pattern deltas (no brand names, no content)     │
│  Import: community starter patterns bundled in public repo          │
│  Privacy: configurable, disabled by default                         │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Signal Store: SQLite Schema

### 3.1 Location

`~/.local/share/inkline/learning/sessions.db`

This is separate from `~/.config/inkline/` (which is for configuration) to follow XDG
conventions: `~/.local/share/` is for application data.

The path is overridable via `INKLINE_LEARNING_DIR` environment variable.

### 3.2 Table: `generation_sessions`

One row per `design_deck()` call. Captures enough context to know whether the output was
good (high quality score, never regenerated) or poor (low score, immediately replaced).

```sql
CREATE TABLE IF NOT EXISTS generation_sessions (
    session_id        TEXT PRIMARY KEY,          -- uuid4
    ts                TEXT NOT NULL,             -- ISO-8601 UTC
    brand             TEXT NOT NULL,
    template          TEXT,
    audience          TEXT,                      -- "investors" | "board" | "team" | ...
    goal              TEXT,                      -- user-provided goal string
    section_count     INTEGER,
    slide_count       INTEGER,
    quality_score     INTEGER,                   -- 0-100 from quality_scorer
    quality_grade     TEXT,                      -- A/B/C/D/F
    anti_pattern_hits TEXT,                      -- JSON array of rule IDs that fired
    dm_rules_used     TEXT,                      -- JSON array of DM rule IDs applied
    mode              TEXT DEFAULT 'llm',        -- llm | rules | advised
    deck_id           TEXT,                      -- user-assigned identifier (optional)
    accepted          INTEGER DEFAULT 0,         -- 1 if user accepted without changes
    replaced          INTEGER DEFAULT 0,         -- 1 if user generated a new deck instead
    regen_count       INTEGER DEFAULT 0          -- how many times this deck_id was regenerated
);
```

### 3.3 Table: `slide_choices`

One row per slide per session. Enables learning which slide types work for which
section/audience/template combinations.

```sql
CREATE TABLE IF NOT EXISTS slide_choices (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id        TEXT NOT NULL REFERENCES generation_sessions(session_id),
    slide_index       INTEGER NOT NULL,
    slide_type        TEXT NOT NULL,
    section_type      TEXT,                      -- inferred from section field
    dm_rule_id        TEXT,                      -- decision matrix rule that drove type choice
    data_structure    TEXT,                      -- DM Axis 1
    message_type      TEXT,                      -- DM Axis 2
    title_length      INTEGER,
    has_chart         INTEGER DEFAULT 0,
    accepted          INTEGER DEFAULT 1,         -- assumed accepted unless modified event filed
    regen_count       INTEGER DEFAULT 0          -- how many times this specific slide was regenerated
);
```

### 3.4 Table: `title_rewrites`

Records every detected title rewrite (before → after). Used to extract patterns about
what makes a better action title for given content types.

```sql
CREATE TABLE IF NOT EXISTS title_rewrites (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    ts                TEXT NOT NULL,
    brand             TEXT NOT NULL,
    session_id        TEXT,
    slide_index       INTEGER,
    section_type      TEXT,
    original_title    TEXT NOT NULL,
    rewritten_title   TEXT NOT NULL,
    rewrite_source    TEXT DEFAULT 'implicit'    -- implicit | explicit | polish
);
```

### 3.5 Table: `regen_counts`

Aggregated count of how many times a (brand, slide_type, section_type) combination was
regenerated before being accepted. High regen counts indicate problematic pairings.

```sql
CREATE TABLE IF NOT EXISTS regen_counts (
    brand             TEXT NOT NULL,
    slide_type        TEXT NOT NULL,
    section_type      TEXT NOT NULL DEFAULT '',
    total_uses        INTEGER DEFAULT 0,
    total_regens      INTEGER DEFAULT 0,
    regen_rate        REAL DEFAULT 0.0,
    last_updated      TEXT,
    PRIMARY KEY (brand, slide_type, section_type)
);
```

### 3.6 Storage module

New file: `src/inkline/learning/store.py`

```python
class LearningStore:
    """Thread-safe SQLite store for generation signals."""

    def __init__(self, db_path: Path | None = None) -> None: ...

    def record_session(self, session: GenerationSession) -> str:
        """Record a deck generation session. Returns session_id."""

    def record_slide_choice(self, session_id: str, slide: SlideChoice) -> None:
        """Record one slide's type choice within a session."""

    def record_title_rewrite(self, rewrite: TitleRewrite) -> None:
        """Record a title rewrite event."""

    def update_regen_count(self, brand: str, slide_type: str, section_type: str,
                           was_regen: bool) -> None:
        """Increment usage and optionally regen count."""

    def get_high_regen_combos(self, brand: str, min_rate: float = 0.4,
                               min_uses: int = 5) -> list[dict]:
        """Return (slide_type, section_type) pairs with high regen rates."""

    def get_audience_layout_stats(self, brand: str, audience: str) -> dict[str, dict]:
        """Return slide type distribution for a brand + audience combination."""

    def get_section_type_preferences(self, brand: str, section_type: str,
                                      audience: str | None = None) -> list[str]:
        """Return slide types ordered by acceptance rate for a section type."""
```

---

## 4. Generation Hook: Auto-Signal Capture

### 4.1 The Problem

`DesignAdvisor.design_deck()` currently returns a list of slides and exits. There is no
hook that records what the system chose or why. This makes the feedback log a manual
opt-in, which in practice never fires.

### 4.2 Solution: Session Context Manager

New file: `src/inkline/learning/session_context.py`

```python
from contextlib import contextmanager

@contextmanager
def generation_session(
    brand: str,
    template: str = "",
    audience: str = "",
    goal: str = "",
    deck_id: str = "",
    mode: str = "llm",
):
    """Context manager that wraps a design_deck() call and records signals.

    Usage::

        with generation_session(brand="minimal", audience="investors") as ctx:
            slides = advisor.design_deck(...)
            ctx.record_slides(slides)

    On exit, writes to LearningStore and returns a session_id that can be
    used to attach explicit feedback later.
    """
```

This is injected into `DesignAdvisor.design_deck()` automatically when
`INKLINE_LEARNING_ENABLED` is set (default: True). It wraps the call without changing
any existing API signatures.

### 4.3 Auto-Filed Acceptance Events

If a `session_id` is produced by the context manager and the session is never followed
by a `modified` or `rejected` feedback event within a configurable window (default: 24h),
the `inkline learn` pass treats all slides in that session as implicitly accepted and
nudges the relevant DM rule confidence upward.

This is **conservative**: a positive nudge of +0.005 per implicit acceptance (vs +0.01
for explicit acceptance). The rationale: the user may have simply not bothered to file
feedback — silence is weaker evidence than an explicit "accepted" click.

Configurable via `~/.config/inkline/learning_config.yaml`:

```yaml
implicit_acceptance_nudge: 0.005    # per implicit acceptance event
explicit_acceptance_nudge: 0.01     # per explicit accepted event
implicit_acceptance_window_hours: 24
implicit_learning_enabled: true
```

---

## 5. Title Rewrite Learning

### 5.1 Signal capture

Title rewrites are detected in two places:

**A. Bridge implicit feedback** (already partially implemented via `_record_implicit_feedback`).
Extend to also detect:
```python
(re.compile(r'(?:change|rename|update|rewrite|fix)\s+(?:the\s+)?title\s+(?:of\s+slide\s+\d+\s+)?(?:to|as)\s+"?(.+?)"?$', re.I), "title_rewrite"),
(re.compile(r'title\s+should\s+(?:be|say|read)\s+"?(.+?)"?$', re.I), "title_rewrite"),
```

**B. Slide spec diff** (existing `detect_implicit_feedback` in `feedback.py`). Extend to
also capture title changes:
```python
if curr_title != prev_title and curr_title and prev_title:
    store.record_title_rewrite(TitleRewrite(
        brand=brand,
        section_type=section,
        original_title=prev_title,
        rewritten_title=curr_title,
        rewrite_source="implicit",
    ))
```

### 5.2 Pattern extraction from title rewrites

The `inkline learn` pass analyses accumulated title rewrites to extract learnable patterns.

Rules detected:
1. **Specificity pattern**: Rewrites that add a number or percentage → record rule
   `"Action titles for {section_type} should include a specific metric"`
2. **Verb-first pattern**: Rewrites that start with a verb → record rule
   `"Action titles for {section_type} should start with an active verb"`
3. **Length pattern**: If rewritten titles are consistently shorter → record
   `"Titles for {section_type} should be ≤ N characters"`

Extracted patterns are filed into `pattern_memory.py` with `source="title_rewrite_analysis"`,
starting at confidence 0.5, promoted by subsequent acceptance.

### 5.3 Example

| Session | Brand | Section | Original | Rewritten |
|---|---|---|---|---|
| 1 | minimal | market_size | "Market Overview" | "SAM growing 34% CAGR to $8B by 2029" |
| 2 | minimal | market_size | "Total Addressable Market" | "$12B TAM, 40% serviceable" |
| 3 | minimal | market_size | "Market Analysis" | "Market tripling in 5 years" |

Pattern extracted: `"market_size titles should state a specific number or growth figure"`
Confidence: 0.65 (3 observations, all consistent).

---

## 6. Anti-Pattern Accumulation

### 6.1 Regen-rate anti-patterns

When a `(slide_type, section_type)` combination has a regen rate above 40% across at
least 5 uses, it is automatically flagged as a likely mismatch. The extractor:

1. Queries `regen_counts` for high-regen combos per brand.
2. Files a new anti-pattern into `pattern_memory.py`:
   ```yaml
   category: anti_pattern
   rule: "Avoid {slide_type} for {section_type} content (regen rate: 45%)"
   confidence: 0.70
   source: regen_rate_analysis
   ```
3. This pattern is injected into DesignAdvisor prompts via `format_patterns_for_prompt()`,
   which already exists and already injects patterns.

**No new injection code is needed** — the existing pattern memory injection handles this
once the pattern is recorded.

### 6.2 Quality-score anti-patterns

Sessions where `quality_score < 50` are analysed for structural commonalities:
- Did a specific `anti_pattern_hits` rule fire on 3+ consecutive low-score sessions?
  → That rule's severity is upgraded from `warning` to `error` for this brand.
- Did a specific slide type appear in >50% of low-score sessions?
  → Record a brand-level anti-pattern: "Overuse of {slide_type} correlates with low scores"

### 6.3 Integration with `anti_patterns.py`

The existing `check_anti_patterns()` function runs at Phase 2b. It will be extended to
accept a `brand_anti_patterns: list[dict]` optional parameter:

```python
def check_anti_patterns(
    slides: list[dict],
    template: str = "",
    brand_anti_patterns: list[dict] | None = None,  # NEW: learned patterns
) -> list[AntiPatternResult]:
```

When `brand_anti_patterns` is provided, the checker evaluates them alongside the static
rules. If a learned anti-pattern rule matches, it generates an `AntiPatternResult` with
`source="learned"` so it can be distinguished from the static library.

---

## 7. Audience and Section-Type Memory

### 7.1 Problem

The current `pattern_memory.py` stores brand-level patterns but does not capture the
cross-dimension interaction between **brand × audience × section_type → slide_type**.
A `kpi_strip` may be perfect for investors seeing a financials section but wrong for a
team all-hands viewing the same section.

### 7.2 Audience preference injection

New function in `learning/store.py`:

```python
def get_audience_layout_prefs(brand: str, audience: str) -> str:
    """Format audience-specific layout preferences for prompt injection.

    Returns a text block like:
    ────────────────────────────────────────
    AUDIENCE LAYOUT PREFERENCES (brand=minimal, audience=investors)
    ────────────────────────────────────────
    • financials → kpi_strip preferred (82% acceptance, 11 uses)
    • market_size → icon_stat preferred (75% acceptance, 8 uses)
    • risk → three_card preferred (78% acceptance, 6 uses)
    """
```

This is injected into `DesignAdvisor._build_system_prompt()` alongside the existing
`format_patterns_for_prompt()` call, only when `audience` is provided and at least 3
data points exist.

### 7.3 Section-type preferences as a drop-in for `get_preferred_types()`

The existing `pattern_memory.get_preferred_types(brand, section_type)` function returns
slide types ordered by approval rate. The new `store.get_section_type_preferences()`
returns the same shape but backed by SQLite data from `slide_choices`, which is richer
(includes DM rule, audience dimension, actual acceptance events).

Migration path: make `get_preferred_types()` try the SQLite store first, fall back to
the existing YAML-backed implementation. This is fully backwards-compatible.

---

## 8. Pattern Extraction Pipeline

### 8.1 New file: `src/inkline/learning/extractor.py`

The extractor runs as a batch job triggered by `inkline learn` (existing CLI command,
extended) or automatically after every 10th generation session.

```python
class PatternExtractor:
    """Extracts learnable patterns from the generation session store."""

    def __init__(self, store: LearningStore) -> None: ...

    def run(self, brand: str | None = None) -> ExtractionReport:
        """Run the full extraction pass. Returns a summary report."""

    def _extract_regen_anti_patterns(self, brand: str) -> list[dict]: ...
    def _extract_title_rewrite_patterns(self, brand: str) -> list[dict]: ...
    def _extract_audience_prefs(self, brand: str) -> dict: ...
    def _extract_quality_score_trends(self, brand: str) -> dict: ...
```

### 8.2 Extraction triggers

| Trigger | When | What runs |
|---|---|---|
| `inkline learn` | Manual / scheduled | Full pass, all brands |
| `inkline learn --brand minimal` | Manual | Single brand pass |
| After 10th session | Auto (LearningStore) | Incremental extraction for that brand |
| After 3 consecutive low-score sessions | Auto | Quality anti-pattern extraction |

### 8.3 ExtractionReport schema

```python
@dataclass
class ExtractionReport:
    brands_processed: list[str]
    patterns_added: int
    patterns_updated: int
    dm_rules_updated: int
    anti_patterns_promoted: int
    title_patterns_extracted: int
    audience_prefs_updated: int
    summary: str                # human-readable summary string
```

---

## 9. Federated / Multi-Instance Learning

### 9.1 Design constraint

Inkline is a public pip package. Patterns learned from a user's private brand (colours,
terminology, content) must not leave the machine. The federated layer must be:

- **Enabled by default for safe structural signals** — sharing improves the community
  baseline and the user benefits immediately from better starter patterns
- **Opt-out via a single config flag** for users who require full local isolation
- **Hard boundary**: brand names, titles, content, goal strings — these are NEVER exported
  regardless of config. Only anonymous structural signals (rule rates, regen rates,
  anti-pattern hit counts) are eligible for export.
- **Two granularities still available**: decision matrix rules only (default enabled), or
  full brand patterns (default disabled — too high a risk of indirect content leakage via
  brand-specific idiom)

### 9.2 What CAN be anonymised safely

These signals contain no content and are safe to share:
- DM rule acceptance/rejection counts by `(data_structure, message_type)` pair
- Slide type regen rates by `section_type` (generic section names only)
- Anti-pattern hit frequencies
- Quality score distributions

These signals are **NOT safe** to share even anonymised:
- Brand names (brand is identifying)
- Actual titles (may contain project names, financials)
- Goal and audience strings (may reveal business context)
- Pattern rule text (may contain brand-specific terminology)

### 9.3 Export format

New file: `src/inkline/learning/federation.py`

```python
def export_pattern_delta(
    since: datetime,
    include_dm_rules: bool = True,
    include_anti_patterns: bool = False,
    dry_run: bool = False,
) -> dict:
    """Export an anonymised pattern delta for community sharing.

    The delta contains ONLY:
    - DM rule acceptance rates by (data_structure, message_type) — no brand
    - Anti-pattern hit frequencies — no brand, no content
    - Quality score trend (improving / stable / degrading) — no details
    - Software version and schema version

    No brand names, no titles, no content, no audience strings.

    Returns the delta dict. If dry_run=False, writes to the configured
    export endpoint (file or HTTP POST).
    """
```

CLI:
```bash
inkline export-patterns --since 2026-01-01 --dry-run   # preview what would be exported
inkline export-patterns                                  # write to community endpoint
```

### 9.4 Community starter patterns (public repo distribution)

The public repo ships a `src/inkline/learning/starter_patterns/` directory containing:

- `dm_rules_community.yaml` — decision matrix rule seeds from community aggregation
  (safe: contains only `data_structure`, `message_type`, `chart_type`, `confidence`)
- `anti_patterns_community.yaml` — anti-pattern frequencies (safe: rule IDs and hit rates)

These are loaded by the `Aggregator` as a bootstrap layer when the local decision matrix
has fewer than 20 observations on a rule. Community confidence never exceeds 0.70 — it
can only be exceeded by local observations.

**Privacy guarantee**: community files contain zero user-generated content. They are
maintained by the project maintainers from opt-out contributions, reviewed before each
release.

### 9.5 Federation configuration

`~/.config/inkline/learning_config.yaml`:

```yaml
# Federation settings — safe structural signals shared by default (opt-out)
federation:
  enabled: true                               # master opt-out switch (set false for full isolation)
  export_dm_rules: true                       # safe: only rule IDs + acceptance rates, no content
  export_anti_patterns: true                  # safe: only rule IDs + hit counts, no content
  export_brand_patterns: false                # NOT recommended — may leak brand context
  community_endpoint: "https://community.inkline.dev/patterns"  # future
  use_community_starter_patterns: true        # read-only; community confidence capped at 0.70
```

---

## 10. Integration with Approved Specs

### 10.1 `design-system-spec.md` (Approved)

The design-system spec defines the decision matrix, `aggregator.py`, and the
`inkline_submit_feedback` MCP tool. **All of that is unchanged.** This spec adds:

- The SQLite `sessions.db` as a richer signal store (JSONL feedback log remains)
- The `PatternExtractor` as the nightly batch job that reads `sessions.db` and
  updates the YAML pattern files + decision matrix
- The `generation_session()` context manager as the zero-friction capture hook

The aggregator continues to process `feedback_log.jsonl` exactly as defined in
`design-system-spec.md`. The new extractor processes `sessions.db`. They are independent
pipelines that write to the same destination (pattern memory + decision matrix).

### 10.2 `impeccable-design-intelligence-spec.md` (Approved)

Anti-patterns, quality scorer, and polish are already implemented. This spec adds:

- Anti-pattern results from Phase 2b are recorded in `generation_sessions.anti_pattern_hits`
- Quality score from Phase 2c is recorded in `generation_sessions.quality_score`
- High regen rates from `regen_counts` feed back as learned anti-patterns (Section 6)
- The `check_anti_patterns()` function is extended to accept learned anti-patterns (Section 6.3)

### 10.3 Updated Archon pipeline

```
Phase 0: design_brief         (existing — LLM, optional)
Phase 0.5: open_session       (NEW — opens generation_session() context)
Phase 1: parse_markdown
Phase 2: design_advisor_llm   (receives brief + audience prefs from SQLite)
Phase 2b: anti_patterns        (existing + learned anti-patterns from store)
Phase 2c: quality_score        (existing — score recorded to session)
Phase 2d: polish               (existing)
Phase 3: taste_enforcer        (existing)
Phase 4: save_slide_spec       (NEW: records slide_choices to session)
Phase 5: export_pdf_with_audit (existing)
Phase 5.5: close_session       (NEW — commits session_id, auto-queues implicit acceptance)
```

Phase 0.5 and 5.5 add negligible latency (pure Python + SQLite INSERT, < 5ms).

---

## 11. Privacy Model

The privacy model is **local-first with opt-out community sharing**. A hard content
boundary protects all user data: only anonymous structural signals can ever leave the
machine, and only via the federation layer.

| Data | Where stored | Who sees it | Exported by default |
|---|---|---|---|
| Brand patterns | `~/.config/inkline/patterns/` | Local only | Never |
| Feedback log | `~/.config/inkline/feedback_log.jsonl` | Local only | Never |
| Decision matrix | `~/.config/inkline/decision_matrix.yaml` | Local only | Never |
| Generation sessions | `~/.local/share/inkline/learning/sessions.db` | Local only | Never |
| Title rewrites | `sessions.db` | Local only | Never |
| DM rule acceptance rates | Derived — no content | Community | **Yes** (opt-out with `export_dm_rules: false`) |
| Anti-pattern hit rates | Derived — no content | Community | **Yes** (opt-out with `export_anti_patterns: false`) |
| Brand patterns (structural) | Derived — no content | Community | No (opt-in, `export_brand_patterns: true`) |

To disable all outbound sharing: set `federation.enabled: false` in
`~/.config/inkline/learning_config.yaml`.

`inkline privacy` command shows a summary of what is stored and what is being exported
under current config.

---

## 12. File Changes

| File | Action | Description |
|---|---|---|
| `src/inkline/learning/__init__.py` | NEW | Package init |
| `src/inkline/learning/store.py` | NEW | SQLite signal store + dataclasses |
| `src/inkline/learning/session_context.py` | NEW | `generation_session()` context manager |
| `src/inkline/learning/extractor.py` | NEW | Batch pattern extraction pipeline |
| `src/inkline/learning/federation.py` | NEW | Export / import community patterns |
| `src/inkline/learning/starter_patterns/dm_rules_community.yaml` | NEW | Community DM seeds |
| `src/inkline/learning/starter_patterns/anti_patterns_community.yaml` | NEW | Community AP seeds |
| `src/inkline/intelligence/design_advisor.py` | MODIFY | Inject `generation_session()` context; inject audience prefs |
| `src/inkline/intelligence/anti_patterns.py` | MODIFY | Add `brand_anti_patterns` parameter |
| `src/inkline/intelligence/feedback.py` | MODIFY | Record title rewrites to `store.record_title_rewrite()` |
| `src/inkline/intelligence/pattern_memory.py` | MODIFY | `get_preferred_types()` tries SQLite first |
| `src/inkline/intelligence/aggregator.py` | MODIFY | Load community starter patterns as bootstrap |
| `src/inkline/app/claude_bridge.py` | MODIFY | Extend `_record_implicit_feedback()` to detect title rewrites |
| `src/inkline/app/cli.py` | MODIFY | Extend `inkline learn` to run `PatternExtractor`; add `inkline privacy`, `inkline export-patterns` |

---

## 13. Implementation Sequence

The recommended implementation order allows each step to be tested independently:

| # | Task | Complexity | Spec Section |
|---|---|---|---|
| 1 | `learning/store.py` — SQLite schema + CRUD | Low | §3 |
| 2 | `learning/session_context.py` — context manager | Low | §4 |
| 3 | Wire context manager into `DesignAdvisor.design_deck()` | Low | §4, §10.3 |
| 4 | Record `slide_choices` in Phase 4 (save_slide_spec) | Low | §3.3 |
| 5 | Extend `feedback.py` to record title rewrites | Low | §5.1B |
| 6 | Extend bridge to detect title rewrite patterns | Low | §5.1A |
| 7 | `learning/extractor.py` — regen anti-pattern extraction | Medium | §8 |
| 8 | `learning/extractor.py` — title rewrite pattern extraction | Medium | §5.2 |
| 9 | `learning/extractor.py` — audience preference extraction | Medium | §7.2 |
| 10 | Extend `anti_patterns.check_anti_patterns()` with brand_anti_patterns | Low | §6.3 |
| 11 | Extend `inkline learn` CLI to run `PatternExtractor` | Low | §8.2 |
| 12 | Add `inkline privacy` and `inkline export-patterns` CLI commands | Low | §11, §9.3 |
| 13 | `learning/federation.py` — export format | Medium | §9.3 |
| 14 | `learning/starter_patterns/` — seed community YAML files | Low | §9.4 |
| 15 | Aggregator bootstrap from community patterns | Low | §9.4, §10.1 |

Steps 1–6 form the signal capture layer (no behaviour change to generation).
Steps 7–11 form the learning loop (generation quality improves).
Steps 12–15 form the federation layer (opt-out, community improvement — on by default).

---

## 14. Key Architectural Decisions

**D1: SQLite over JSONL for session data**

`feedback_log.jsonl` is a good audit log but bad for querying. "What is the regen rate
for `kpi_strip` on `financials` sections across all brands?" requires a full file scan in
JSONL; it is a single indexed query in SQLite. The JSONL log is kept for explicit feedback
events (it is already implemented and working), and SQLite is introduced only for the new
session/slide-choice/regen data.

**D2: Conservative implicit acceptance nudges**

Silence (no feedback filed) is treated as weak acceptance, not strong acceptance.
Confidence nudge of +0.005 vs +0.01 for explicit. This prevents a quiet period from
incorrectly boosting rules that users simply never bothered to rate.

**D3: Pattern extraction is batch, not real-time**

Extracting title rewrite patterns, regen anti-patterns, and audience preferences requires
seeing multiple sessions to be statistically meaningful. Running extraction on every session
would produce noisy, prematurely-promoted patterns. The batch extractor runs nightly or
after a configurable number of sessions.

**D4: Community patterns cap at 0.70 confidence**

Community-seeded starter patterns are useful to bootstrap a new Inkline installation
before the user has enough sessions to learn from. But community patterns reflect
generic best practices, not this user's specific brand preferences. Capping at 0.70
ensures local user data can always override the community baseline.

**D5: No ML / no model weights**

All learning is statistical confidence nudging and threshold-based promotion/demotion,
exactly as in `design-system-spec.md`. This keeps the system fully interpretable, auditable,
and inspectable via YAML and SQLite — no opaque parameters.

**D6: API is backward-compatible**

The `generation_session()` context manager wraps `design_deck()` by injecting it
internally — the caller API is unchanged. The `check_anti_patterns()` new parameter is
optional with a default of `None`. The `get_preferred_types()` SQLite lookup is a
try/fallback — existing YAML data continues to work if the SQLite store is empty.

---

## 15. Non-Goals

- **No cross-session personalisation by user identity** — Inkline assumes single-user
  per machine (the XDG directories are per-user OS accounts). Multi-user isolation is
  out of scope.
- **No ML model training** — no neural weights, no embedding, no vector stores. All
  learning is rule-based statistics.
- **No automatic brand pattern deletion** — patterns are demoted but never deleted.
  Audit trail preserved. Users can prune manually via `inkline patterns --prune`.
- **No server-side storage** — even with federation enabled, data is exported as a
  one-way aggregate. There is no "sync" or "pull my patterns from the server".
- **No UI for learning management** — all interaction is via the existing CLI commands
  (`inkline learn`, `inkline patterns`, `inkline privacy`). A web UI for this is a
  future concern.
- **No changes to Typst renderers** — learning operates entirely on slide specs, before
  rendering.
