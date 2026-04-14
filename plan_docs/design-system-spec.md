# Inkline Design System — Complete Architecture Spec

**Date:** 14 April 2026  
**Status:** Approved for implementation  
**Scope:** Decision framework, renderer taste enforcement, self-learning feedback loop, reference deck ingestion

---

## 0. Goal

Turn Inkline into a design system with *encoded taste* — the outputs it produces are always within the range that a designer with good judgement would approve, without requiring handholding from the user. The system should get measurably better the more it is used.

The three-layer architecture to achieve this:

```
┌────────────────────────────────────────────────────────────────┐
│  LAYER 1 — DECISION FRAMEWORK (LLM prompt)                     │
│  Structured questions → one right chart type                   │
│  Driven by: decision_matrix.yaml                               │
├────────────────────────────────────────────────────────────────┤
│  LAYER 2 — RENDERER CAPABILITIES                               │
│  clean style, accent semantics, 30+ chart/infographic types    │
│  Driven by: chart_renderer.py, slide_renderer.py               │
├────────────────────────────────────────────────────────────────┤
│  LAYER 3 — POST-PROCESSING TASTE ENFORCEMENT                   │
│  Deterministic rules applied after LLM choice                  │
│  Driven by: taste_enforcer.py                                  │
└────────────────────────────────────────────────────────────────┘
         ↑                   ↑                    ↑
  SELF-LEARNING       RENDERER REGISTRY    RULE UPDATES
  (feedback loop      (new types from      (from aggregated
   + deck ingestion)   deck analysis)       feedback stats)
```

---

## 1. Layer 1: Decision Framework

### 1.1 The problem with option catalogs

The current DesignAdvisor prompt lists 30+ chart types and tells the LLM to "choose the most suitable". More options → more entropy → inconsistent quality. A senior designer doesn't pick from a menu — they answer three questions:

1. **What shape is the data?** (structure)
2. **What is the one thing this slide must prove?** (message)
3. **How much space does the chart have?** (density)

Those three answers determine one correct exhibit type with specific enforced parameters.

### 1.2 Decision matrix schema

Stored at: `~/.config/inkline/decision_matrix.yaml`  
(Bundled default at: `src/inkline/intelligence/decision_matrix_default.yaml`)

```yaml
version: 4
last_updated: "2026-04-14"
source_decks: ["pareto_dc_2026", "launchpad_march_2026"]
rules:
  - id: DM-001
    data_structure: "single_number"       # what shape is the data
    message_type: "status_at_a_glance"    # what the slide must prove
    density: any
    chart_type: kpi_strip
    enforce:
      style: clean
    confidence: 0.95
    observations: 12                      # times this rule fired + was accepted

  - id: DM-002
    data_structure: "two_values_comparison"
    message_type: "change_over_time"
    density: any
    chart_type: dumbbell
    enforce:
      accent_direction: increase
    confidence: 0.88
    observations: 7

  - id: DM-003
    data_structure: "n_categories_one_value"
    message_type: "ranking_or_comparison"
    density: full_width
    chart_type: grouped_bar
    enforce:
      style: clean
      accent_index: auto          # post-processor infers from highest/narrative
      orientation: horizontal_if_labels_long
    confidence: 0.92
    observations: 31

  - id: DM-004
    data_structure: "n_categories_one_value"
    message_type: "ranking_or_comparison"
    density: panel               # inside multi_chart
    chart_type: grouped_bar
    enforce:
      style: clean
      accent_index: auto
      label_density: compact
    confidence: 0.91
    observations: 18

  # ... full set in decision_matrix_default.yaml
```

**Data structure vocabulary** (canonical values for Axis 1):

| Value | Meaning |
|---|---|
| `single_number` | One KPI, one metric |
| `two_values_comparison` | Before/after, A vs B |
| `n_categories_one_value` | Bar chart territory |
| `n_categories_time_series` | Multiple bars over time, or line |
| `n_categories_composition` | Shares that sum to 100% |
| `part_of_whole` | Donut, treemap territory |
| `two_continuous_variables` | Scatter territory |
| `matrix_rows_cols` | Heatmap, scoring_matrix |
| `steps_over_time` | Gantt, timeline, ladder |
| `state_transition` | transition_grid, sankey |
| `network_relationships` | entity_flow |
| `text_heavy_structured` | Table, feature_grid, icon_stat |
| `mixed_media` | Infographic, sidebar, iceberg |

**Message type vocabulary** (canonical values for Axis 2):

| Value | Typical exhibit |
|---|---|
| `status_at_a_glance` | KPI strip, gauge |
| `ranking_or_comparison` | Bar (clean), dumbbell |
| `change_over_time` | Line, dumbbell, waterfall |
| `part_of_whole_breakdown` | Stacked bar, donut, waterfall |
| `process_or_sequence` | Timeline, Gantt, multi_timeline, ladder |
| `capability_comparison` | Scoring matrix |
| `geographic_distribution` | Map (future), heatmap |
| `concentration_or_outlier` | Scatter (annotated) |
| `state_migration` | Transition grid |
| `narrative_with_data` | Split slide, sidebar, iceberg |
| `feature_enumeration` | Icon stat, feature grid |
| `hierarchical_structure` | Entity flow, treemap |

### 1.3 DesignAdvisor prompt rewrite

The `SLIDE_TYPE_GUIDE` section in `design_advisor.py` must be replaced with a structured decision sequence:

```
DECISION SEQUENCE (follow in order, stop when you reach a conclusion):

STEP 1 — What shape is the data?
  Identify the data_structure from this list: [single_number | two_values_comparison |
  n_categories_one_value | n_categories_time_series | n_categories_composition |
  part_of_whole | two_continuous_variables | matrix_rows_cols | steps_over_time |
  state_transition | network_relationships | text_heavy_structured | mixed_media]

STEP 2 — What is the one thing this slide must prove?
  Identify the message_type from this list: [status_at_a_glance | ranking_or_comparison |
  change_over_time | part_of_whole_breakdown | process_or_sequence |
  capability_comparison | concentration_or_outlier | state_migration |
  narrative_with_data | feature_enumeration | hierarchical_structure]

STEP 3 — Apply the decision matrix rule for this (data_structure, message_type) pair.
  [matrix injected here at runtime from decision_matrix.yaml]

STEP 4 — Apply any enforce: parameters from the matched rule.
  These are MANDATORY — do not override them.

STEP 5 — If no rule matches, fall back to: grouped_bar with style=clean.
  Log the unmatch so it can be reviewed for matrix extension.
```

The key constraint: **Claude never sees the full option list**. It sees the vocabulary for Steps 1 and 2, then the matrix entry for the matched pair. This prevents entropy from option paralysis.

---

## 2. Layer 3: Post-Processing Taste Enforcer

### 2.1 Location

New file: `src/inkline/typst/taste_enforcer.py`

Called in `src/inkline/typst/__init__.py` after DesignAdvisor returns slide specs and before rendering begins.

### 2.2 Rule set

```python
TASTE_RULES = [
    # R-01: grouped_bar always clean in full-width context
    {
        "id": "R-01",
        "match": {"chart_type": "grouped_bar"},
        "condition": lambda d: d.get("style") not in ("clean",),
        "enforce": {"style": "clean"},
        "reason": "axis chrome adds noise; clean style is always preferable for bar data",
    },

    # R-02: stacked_bar always clean
    {
        "id": "R-02",
        "match": {"chart_type": "stacked_bar"},
        "condition": lambda d: d.get("style") not in ("clean",),
        "enforce": {"style": "clean"},
        "reason": "same as R-01",
    },

    # R-03: donut with ≤6 segments → direct labels
    {
        "id": "R-03",
        "match": {"chart_type": "donut"},
        "condition": lambda d: len(d.get("segments", [])) <= 6,
        "enforce": {"label_style": "direct"},
        "reason": "legend wastes space when segments are few enough to label directly",
    },

    # R-04: scatter with named points → annotated labels
    {
        "id": "R-04",
        "match": {"chart_type": "scatter"},
        "condition": lambda d: any(p.get("label") for p in d.get("points", [])),
        "enforce": {"label_style": "annotated"},
        "reason": "named points need callout boxes; plain dots lose the message",
    },

    # R-05: auto-assign accent_index on grouped_bar if missing
    {
        "id": "R-05",
        "match": {"chart_type": "grouped_bar"},
        "condition": lambda d: "accent_index" not in d,
        "enforce": {"accent_index": "__infer_from_highest__"},
        "reason": "accent as semantic signal; highest bar gets emphasis",
    },

    # R-06: panel chart in multi_chart → suppress title (panel header carries it)
    {
        "id": "R-06",
        "match": {"context": "panel"},
        "condition": lambda d: d.get("chart_title"),
        "enforce": {"chart_title": None},
        "reason": "panel header already names the chart; embedded title duplicates",
    },

    # R-07: bar with >12 categories → convert to horizontal
    {
        "id": "R-07",
        "match": {"chart_type": "grouped_bar"},
        "condition": lambda d: len(d.get("categories", [])) > 12,
        "enforce": {"orientation": "horizontal"},
        "reason": "vertical bars become unreadable past ~12 categories",
    },

    # R-08: line chart → always suppress right/top spines, no grid
    {
        "id": "R-08",
        "match": {"chart_type": "line"},
        "condition": lambda _: True,
        "enforce": {"spine_style": "minimal", "grid": False},
        "reason": "Pareto/Goldman standard: clean line on bottom/left axes only",
    },
]
```

### 2.3 accent_index inference

When `accent_index` is `"__infer_from_highest__"`, the post-processor:

1. Looks at the slide's `narrative` field for keywords: "highest", "leading", "top", "best", "lowest", "worst"
2. If found and a category name matches → uses that category's index
3. Otherwise → defaults to the index of the highest numeric value in `values[0]`

---

## 3. Self-Learning System

### 3.1 Overview

Two distinct learning pathways feed the decision matrix and DesignAdvisor:

```
PATH A: User feedback (post-generation)
  User accepts / rejects / modifies a slide
      ↓
  FeedbackEvent recorded with slide context
      ↓
  Aggregator updates confidence + observations on matched DM rule
      ↓
  Rules with high rejection rates get flagged for review / auto-demoted

PATH B: Reference deck ingestion
  User uploads a PDF → inkline_ingest_reference_deck()
      ↓
  DeckAnalyser (pymupdf) extracts layout + chart patterns
      ↓
  Patterns tagged with source_deck, added to decision_matrix as new rules
      ↓
  DesignAdvisor receives updated matrix at next prompt build
```

### 3.2 Feedback event schema

Stored at: `~/.config/inkline/feedback_log.jsonl` (one JSON object per line)

```json
{
  "ts": "2026-04-14T11:32:00Z",
  "brand": "corsair",
  "deck_id": "corsair_exhibit_v6",
  "slide_index": 4,
  "slide_type": "chart_heavy",
  "chart_type": "grouped_bar",
  "dm_rule_id": "DM-003",
  "data_structure": "n_categories_one_value",
  "message_type": "ranking_or_comparison",
  "action": "accepted",           // accepted | rejected | modified
  "modified_to": null,            // chart_type user changed to, if action=modified
  "enforce_overrides": {},        // params user changed, if action=modified
  "source": "explicit",           // explicit | implicit | auditor_accept
  "comment": ""                   // optional text comment from user
}
```

### 3.3 Aggregator: updating the decision matrix

Run on: each feedback event (incremental), and on-demand via `inkline learn`.

```python
def update_rule_from_feedback(event: FeedbackEvent, matrix: DecisionMatrix) -> None:
    rule = matrix.get_rule(event.dm_rule_id)
    if rule is None:
        return

    rule.observations += 1

    if event.action == "accepted":
        # Nudge confidence up (max 0.99)
        rule.confidence = min(0.99, rule.confidence + 0.01)

    elif event.action == "rejected":
        # Nudge confidence down
        rule.confidence = max(0.10, rule.confidence - 0.05)
        # If confidence drops below 0.40, flag for human review
        if rule.confidence < 0.40:
            rule.status = "flagged"

    elif event.action == "modified":
        # User changed chart type → candidate for a new rule
        if event.modified_to:
            matrix.propose_new_rule(
                data_structure=event.data_structure,
                message_type=event.message_type,
                chart_type=event.modified_to,
                enforce=event.enforce_overrides,
                source_event=event.id,
            )
        # Also demote the existing rule
        rule.confidence = max(0.10, rule.confidence - 0.03)

    matrix.save()
```

**Proposed rule promotion:** A proposed rule auto-promotes to active when:
- `observations >= 5` AND `acceptance_rate >= 0.70`

**Rule demotion:** An active rule auto-demotes to `status: "low_confidence"` when:
- `observations >= 10` AND `confidence < 0.40`

Low-confidence rules are not injected into the DesignAdvisor prompt but are kept in the matrix for audit.

### 3.4 Front-end feedback capture

The MCP server exposes a new tool:

```python
@mcp.tool
def inkline_submit_feedback(
    deck_id: str,
    slide_index: int,
    action: str,                  # "accepted" | "rejected" | "modified"
    modified_chart_type: str = "",
    modified_params: str = "{}",  # JSON string of param overrides
    comment: str = "",
) -> dict:
    """Record user feedback on a rendered slide.

    Call this after the user accepts, rejects, or manually modifies a slide
    in the front-end. Drives the self-learning decision matrix.
    """
```

The Claude.ai bridge (`claude_bridge.py`) adds implicit feedback detection: if a user sends a message like "change that bar chart to a dumbbell" or "make it horizontal", the bridge parses the correction and auto-files a `modified` feedback event before re-rendering.

### 3.5 Implicit feedback from conversation

The bridge monitors messages for chart correction patterns:

```python
IMPLICIT_PATTERNS = [
    (r"change (?:the |that )?([\w_]+) (?:chart )?to (?:a |an )?([\w_]+)", "chart_type_change"),
    (r"make (?:it |the chart )?(horizontal|vertical)", "orientation_change"),
    (r"(remove|hide|show) (?:the )?(legend|axis|labels|title)", "param_change"),
    (r"highlight (?:the )?([\w\s]+)(?:bar|column|segment)", "accent_change"),
    (r"too (?:many|much) (labels|bars|categories|data)", "density_feedback"),
]
```

Each match → `FeedbackEvent(action="modified", source="implicit_conversation")`.

---

## 4. Reference Deck Ingestion Pipeline

### 4.1 New MCP tool

```python
@mcp.tool
def inkline_ingest_reference_deck(
    pdf_path: str,
    deck_name: str,
    deck_context: str = "",       # "investment_banking" | "consulting" | "corporate"
    overwrite: bool = False,
) -> dict:
    """Ingest a reference PDF deck to extract design patterns.

    Analyses slide layouts, chart types, colour usage, and typography
    patterns from the PDF. Extracted patterns are added to the decision
    matrix and made available to the DesignAdvisor.

    Returns a summary of patterns extracted.
    """
```

### 4.2 DeckAnalyser

New file: `src/inkline/intelligence/deck_analyser.py`

Builds on the pymupdf analysis already done manually for Pareto/Launchpad, made fully automated:

```python
class DeckAnalyser:
    """Automated design pattern extractor from PDF reference decks."""

    SLIDE_CLASSIFIERS = [
        # (pattern_fn, label)
        (lambda b: _has_chart(b), "chart_slide"),
        (lambda b: _has_table(b), "table_slide"),
        (lambda b: _has_large_text_block(b), "text_heavy"),
        (lambda b: _high_icon_density(b), "infographic"),
        (lambda b: _full_bleed_image(b), "visual_anchor"),
        (lambda b: _has_kpi_blocks(b), "kpi_strip"),
    ]

    def analyse(self, pdf_path: Path) -> DeckAnalysis:
        doc = fitz.open(str(pdf_path))
        slides = []

        for page_num, page in enumerate(doc):
            blocks = page.get_text("dict")["blocks"]
            drawings = page.get_drawings()
            images = page.get_images()

            slide = SlideAnalysis(
                page=page_num + 1,
                width=page.rect.width,
                height=page.rect.height,
                layout_class=self._classify(blocks, drawings, images),
                colour_palette=self._extract_palette(drawings),
                chart_types=self._detect_chart_types(drawings, blocks),
                text_structure=self._extract_text_hierarchy(blocks),
                whitespace_ratio=self._calc_whitespace(blocks, drawings, images, page.rect),
                label_strategy=self._detect_label_strategy(drawings, blocks),
            )
            slides.append(slide)

        return DeckAnalysis(
            deck_name=pdf_path.stem,
            slide_count=len(slides),
            slides=slides,
            global_palette=self._merge_palettes(slides),
            dominant_layouts=self._count_layouts(slides),
            chart_vocabulary=self._collect_chart_types(slides),
        )
```

**Chart type detection heuristics** (from drawing path analysis):

| Drawing signature | Inferred chart type |
|---|---|
| Multiple equal-width `rect` patches in a row, similar height | vertical bar |
| Multiple equal-height `rect` patches in a column | horizontal bar |
| Stacked `rect` patches, same x-position | stacked bar |
| Circular/elliptical path + inner circle path | donut |
| Path with many line segments, monotone x | line chart |
| Circles of varying sizes scattered | bubble/scatter |
| Rectangular grid with fill variation | heatmap / scoring_matrix |
| Horizontal rectangles with left-anchored start | Gantt |
| Two dots connected by a line, horizontal | dumbbell |

### 4.3 Pattern extraction → decision matrix

After analysis, each detected chart type on each slide gets a candidate rule:

```python
def _extract_dm_candidates(analysis: DeckAnalysis) -> list[DMCandidate]:
    candidates = []
    for slide in analysis.slides:
        for chart_type in slide.chart_types:
            # Infer data_structure from chart type
            data_structure = CHART_TO_DATA_STRUCTURE.get(chart_type, "unknown")
            # Infer message_type from surrounding text (section headers, bullet points)
            message_type = _infer_message_type(slide.text_structure, chart_type)
            candidates.append(DMCandidate(
                data_structure=data_structure,
                message_type=message_type,
                chart_type=chart_type,
                enforce=_infer_enforce_params(slide, chart_type),
                source_deck=analysis.deck_name,
                source_page=slide.page,
                confidence=0.50,    # starts low; promoted by acceptance
            ))
    return candidates
```

### 4.4 Stored analysis output

Each ingested deck produces:

1. `~/.config/inkline/reference_decks/{deck_name}/analysis.yaml` — full structured analysis
2. `~/.config/inkline/reference_decks/{deck_name}/patterns.md` — human-readable pattern summary (same format as `design_inspiration_analysis.md`)
3. Appended candidate rules in `decision_matrix.yaml` with `source_deck: deck_name` and `status: "candidate"`

The patterns.md can be reviewed and edited before rules are promoted to `status: "active"`.

---

## 5. Integration Map

```
inkline_generate_deck()
    │
    ├─ Phase 1: DeckPlanner (LLM)
    │      reads: decision_matrix.yaml (active rules injected into prompt)
    │      reads: pattern_memory/{brand}.yaml
    │
    ├─ Phase 2: DesignAdvisor (per slide, LLM)
    │      uses: decision framework (Step 1-5) instead of option catalog
    │      applies: matched DM rule enforce: params
    │
    ├─ TasteEnforcer.apply(slide_specs)   ← NEW
    │      applies: TASTE_RULES deterministically
    │      resolves: accent_index inference
    │
    ├─ _auto_render_charts()
    │
    └─ feedback_log.jsonl ← written with dm_rule_id, context
           │
           └─ aggregator.update()  ← runs after each event
                  updates: decision_matrix.yaml confidence + observations
                  proposes: new rules when modification pattern detected


inkline_submit_feedback()  ← NEW MCP tool
    writes: feedback_log.jsonl
    calls: aggregator.update()


inkline_ingest_reference_deck()  ← NEW MCP tool
    runs: DeckAnalyser
    writes: reference_decks/{name}/analysis.yaml
    appends: candidate rules to decision_matrix.yaml


inkline learn  ← NEW CLI command
    runs: full aggregation pass over feedback_log.jsonl
    promotes: candidate rules meeting threshold
    demotes: low-confidence active rules
    prints: summary report
```

---

## 6. decision_matrix_default.yaml — Full Initial Content

The default matrix ships with 26 rules derived from:
- Pareto DC financing deck (15 patterns, PT-1→PT-15)
- Launchpad brochure (9 patterns, LP-1→LP-9)
- Goldman/McKinsey standard chart grammar (baseline reference)

Each rule covers one (data_structure, message_type) pair. Where multiple decks agree → confidence starts at 0.80+. Where only one source → confidence starts at 0.60.

Full content defined in implementation phase (derived from `design_inspiration_analysis.md`).

---

## 7. Implementation Sequence

| # | Task | Files | Complexity |
|---|---|---|---|
| 1 | Build `decision_matrix_default.yaml` from existing analysis | new | Medium |
| 2 | `taste_enforcer.py` + wire into `__init__.py` | new + edit | Low |
| 3 | Rewrite `design_advisor.py` prompt (decision sequence + matrix injection) | edit | Medium |
| 4 | `feedback_log.jsonl` schema + `inkline_submit_feedback` MCP tool | edit | Low |
| 5 | `aggregator.py` (confidence updates, rule promotion/demotion) | new | Medium |
| 6 | Implicit feedback parser in `claude_bridge.py` | edit | Medium |
| 7 | `deck_analyser.py` (DeckAnalyser class + chart heuristics) | new | High |
| 8 | `inkline_ingest_reference_deck` MCP tool | edit | Low |
| 9 | `inkline learn` CLI command | edit | Low |
| 10 | Promote Pareto/Launchpad analysis into initial matrix (from design_inspiration_analysis.md) | new | Low |

Total: ~10 discrete tasks. Tasks 1-6 form the live self-learning loop. Tasks 7-9 add reference deck ingestion. Task 10 seeds the initial matrix.

---

## 8. What This Does NOT Include (by design)

- **ML/neural training** — all learning is statistical (confidence nudging + threshold promotion). No model weights. Fully interpretable and auditable.
- **Cloud sync** — all state is local (`~/.config/inkline/`). No external calls.
- **Per-user isolation** — patterns shared across all users on the same machine. Multi-user isolation is a future concern.
- **Automatic rule deletion** — rules are demoted, never deleted. Audit trail preserved.
