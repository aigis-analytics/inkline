# Inkline Parallel Gap-Closure Program — Reference Retrieval, Archetypes, Benchmark Audit, and Native Infographic Builders

**Date:** 20 June 2026  
**Status:** Approved for implementation after independent audit  
**Primary repo:** `/home/k1mini/inkline`  
**Program owner:** Inkline core  
**Execution model:** multi-lane parallel implementation with shared contracts

---

## 1. Objective

Close the four highest-value remaining capability gaps in Inkline:

1. `reference-driven slide retrieval` that materially affects layout generation
2. `more executable full-slide archetypes`
3. `benchmark-aware audit` rather than mostly proxy audit
4. `richer native slide builders` for professional infographic / page-level compositions

This program must preserve the current architecture:

- playbooks and reference knowledge remain inputs to the `authoring intelligence layer`
- the deterministic renderer remains an execution engine, not a reasoning engine
- `execution_mode=explicit_spec` stays authoritative for locked-spec runs

---

## 2. Current State

Inkline is now materially better than it was before the 7GI/AGEH work, but the remaining structural gap is clear.

### 2.1 What exists today

- storyboard and authoring-trace metadata
- reference-family ingestion and catalog primitives
- an initial full-slide archetype registry
- MCP resources for playbooks, storyboard rules, archetypes, and reference families
- storyboard-aware audit aggregation
- editable institutional PPTX export and inspection
- explicit execution contract for locked-spec vs draft flows

### 2.2 Why this is still insufficient

The system still behaves too conservatively because:

- reference retrieval is mostly metadata lookup, not a strong generation driver
- the archetype set is too small and compiles into a narrow set of generic layouts
- benchmark alignment in audit is mostly inferred from the same rendered-critique proxy score
- native slide builders do not yet expose enough page-level composition primitives to express professional investor-grade infographic slides cleanly

### 2.3 Concrete current limitations in the codebase

At the time of writing:

- `src/inkline/intelligence/archetype_retriever.py` returns simple heuristic candidate lists and does not supply geometry-aware or style-token-aware retrieval
- `src/inkline/intelligence/full_slide_archetypes.py` contains only `8` executable archetypes
- those archetypes mostly compile to broad layouts like `title`, `three_card`, `process_flow`, `team_grid`, `kpi_strip`, `timeline`, `table`, and `chart_caption`
- `src/inkline/intelligence/audit_storyboard.py` scores `archetype_compliance`, `reference_family_alignment`, and `message_delivery` from the same proxy verdict path rather than distinct measured checks
- `src/inkline/pptx/builder.py` is still a builder with strong styling opinions but limited reusable institutional infographic primitives

---

## 3. Research Inputs

This program is informed by:

- existing Inkline playbooks and prior internal search work
- the current reference-driven archetype spec already in `plan_docs`
- external product and research patterns

### 3.1 Product patterns

- `Beautiful.ai Smart Slides` suggests the importance of adaptive, designer-authored full-slide primitives rather than raw templating
- `Pitch Agent` suggests brand-pattern reuse and template-grounded generation rather than purely one-shot synthesis
- `Canva Magic Design for Presentations` suggests story-outline plus branded-slide generation as a coupled workflow
- `Microsoft Copilot for PowerPoint` suggests source-grounded, branded, editable presentation generation is now baseline user expectation

### 3.2 Research patterns

- `PPTAgent` suggests reference-presentation analysis, slide-role extraction, and edit-against-reference generation rather than unconstrained one-shot generation
- `RALF` suggests nearest-neighbor retrieval can materially improve layout decisions when the retrieved examples genuinely affect the generation path
- `PresentBench` suggests evaluation should be instance-specific, rubric-based, and broken into measurable dimensions instead of holistic taste judgments

### 3.3 Design implication

The missing layer is not “more templates.” It is:

- richer `full-slide archetypes`
- stronger `reference-family retrieval`
- better `compiled manifests`
- benchmark-aware and message-aware `audit semantics`
- more expressive `native builders`

---

## 4. Program Principles

1. `Do not move design reasoning into the renderer.`
   The renderer implements selected structures. It does not choose them.

2. `Treat retrieval as a real generation input.`
   Reference retrieval must affect archetype selection, compiled layout choice, or freeform manifest shaping. Pure trace metadata is not enough.

3. `Prefer explainable selection over opaque style transfer.`
   The system should be able to say which reference family, which reference slides, which archetype candidates, and why.

4. `Separate hard checks from advisory checks.`
   Audit must distinguish render defects, archetype compliance, benchmark alignment, and style advisories.

5. `Keep execute-mode deterministic.`
   Locked-spec rendering must remain deterministic and LLM-free at execution time.

6. `Design for editable output.`
   New primitives should improve PDF quality and native PPTX editability together, not trade one off casually against the other.

---

## 5. Scope

### 5.1 In scope

- reference-family retrieval and scoring that changes generated slide manifests
- significant expansion of executable full-slide archetypes
- benchmark-aware audit dimensions with measurable checks
- new PPTX/Typst/native composition primitives for infographic slides
- program orchestration across parallel engineering lanes
- research corpus enrichment using benchmark decks and internet-backed pattern gathering

### 5.2 Out of scope

- arbitrary image-prompt style cloning
- a WYSIWYG editor
- full learned end-to-end layout generation
- mandatory LLM coupling inside the deterministic renderer

---

## 6. Target End State

After this program:

- an external LLM can ask Inkline MCP for candidate `full-slide archetypes` and benchmark slides for a slide role like `key_people`
- reference retrieval can influence the chosen archetype and the compiled manifest materially
- the archetype library covers a real institutional deck grammar, not only generic grids
- the audit can say:
  - whether the slide visually passed
  - whether it matched the intended archetype
  - whether it aligned to the chosen reference family
  - whether it delivered the declared message
- the native builders can express more of the slides that good human analysts build directly in PowerPoint

---

## 7. Parallel Delivery Model

The program should run as `5` coordinated streams:

- `Lane 0` shared contracts and governance
- `Lane A` reference-driven retrieval
- `Lane B` executable archetype expansion
- `Lane C` benchmark-aware audit
- `Lane D` native infographic/page builders

These lanes can run mostly in parallel once `Lane 0` stabilizes the shared contracts.

### 7.1 Required shared contracts

Before parallel work proceeds, lock:

- archetype manifest schema
- reference-slide manifest schema
- compiled-slide-manifest schema
- benchmark-alignment audit schema
- builder primitive registry naming
- artifact path / confidentiality / licensing rules

This is a short stabilization step, not a long phase.

### 7.2 Contract ownership and migration

The current codebase uses v1-style ad hoc dict schemas spread across:

- `src/inkline/intelligence/full_slide_archetypes.py`
- `src/inkline/intelligence/reference_ingest.py`
- `src/inkline/intelligence/reference_catalog.py`
- `src/inkline/intelligence/audit_storyboard.py`

So Lane 0 must explicitly own schema normalization and migration.

Required v2 contracts:

- `ReferenceSlideManifestV2`
- `FullSlideArchetypeManifestV2`
- `CompiledSlideManifestV2`
- `BenchmarkAuditV1`

Required migration rule:

- all v1 manifests remain readable
- all v2 manifests must serialize deterministically
- write-paths emit v2 only after validators exist
- read-paths accept v1 and normalize to v2 in memory

Required validator API surface:

- `validate_reference_slide_manifest(payload) -> normalized_v2`
- `validate_full_slide_archetype(payload) -> normalized_v2`
- `validate_compiled_slide_manifest(payload) -> normalized_v2`
- `validate_benchmark_audit(payload) -> normalized_v1`

### 7.3 Minimum field contracts

#### ReferenceSlideManifestV2

Required fields:

- `schema_name`
- `schema_version`
- `reference_slide_id`
- `reference_family_id`
- `source_slide_index`
- `role`
- `composition_family`
- `density_class`
- `style_tokens`
- `zone_map`
- `content_slots`
- `usable_for_retrieval`

Optional fields:

- `archetype_tag`
- `hero_kind`
- `evidence_kind`
- `benchmark_quality_weight`
- `strong_exemplar`
- `do_not_imitate`
- `preview_path`
- `curation_notes`

#### FullSlideArchetypeManifestV2

Required fields:

- `schema_name`
- `schema_version`
- `id`
- `functional_roles`
- `deck_types`
- `content_schema`
- `visual_intent`
- `compile_targets`
- `compile_variants`
- `density_class`
- `allowed_primitives`
- `audit_checks`

Optional fields:

- `benchmark_refs`
- `pptx_editability_policy`
- `anti_patterns`

#### CompiledSlideManifestV2

Required fields:

- `schema_name`
- `schema_version`
- `slide_id`
- `source_archetype`
- `compile_target`
- `variant_id`
- `render_payload`

Optional fields:

- `source_reference_family`
- `source_reference_slide_ids`
- `builder_recipe_id`
- `benchmark_tokens_applied`
- `pptx_editability_exceptions`

#### BenchmarkAuditV1

Required fields:

- `schema_name`
- `schema_version`
- `engineering_pass`
- `design_pass`
- `benchmark_alignment_pass`
- `message_pass`
- `ship_recommendation`
- `slides`

Each slide entry in `slides` must include:

- `slide_id`
- `hard_render`
- `archetype_compliance`
- `benchmark_alignment`
- `message_delivery`
- `required_fix`

---

## 8. Lane 0 — Shared Contracts and Governance

### 8.1 Goal

Create the contracts that let the other lanes move independently without drift.

### 8.2 Deliverables

- `schema_reference_slide_v2`
- `schema_full_slide_archetype_v2`
- `schema_compiled_slide_manifest_v2`
- `schema_benchmark_audit_v1`
- confidentiality / licensing policy for reference assets
- fixture matrix for cross-lane integration

### 8.3 Files

- `src/inkline/intelligence/reference_schema.py`
- `src/inkline/intelligence/full_slide_archetypes.py`
- `src/inkline/intelligence/audit_storyboard.py`
- `src/inkline/app/mcp_resources.py`
- `docs/USER_GUIDE.md`
- `README.md`

### 8.4 Acceptance criteria

- all downstream lanes can import the same schemas without redefinition
- all audit artifacts serialize these schemas consistently
- confidential/private benchmark assets stay outside the public packaged corpus

---

## 9. Lane A — Reference-Driven Retrieval That Materially Affects Generation

### 9.1 Goal

Upgrade retrieval from “candidate metadata attached to trace” to “retrieval that changes the generated slide path.”

### 9.2 Current gap

Today retrieval is too weak:

- archetype selection is heuristic and shallow
- reference slides are looked up, but they do not strongly shape manifest generation
- reference-family alignment is mostly advisory metadata, not a structural driver

### 9.3 Required capability

Retrieval must influence at least one of:

- chosen full-slide archetype
- chosen compile target
- chosen freeform composition recipe
- spacing/token defaults
- benchmark-specific audit expectations

### 9.4 Technical design

Build a `reference retrieval stack` with four layers:

1. `Family filter`
   Resolve allowed candidate families by deck metadata, confidentiality class, and operator override.

2. `Slide-role retrieval`
   Retrieve candidate reference slides by:
   - declared role
   - content schema match
   - deck type
   - archetype tags
   - style cluster

3. `Token extraction`
   Persist benchmark signals such as:
   - title zone geometry
   - panel count
   - dominant composition axis
   - chrome pattern
   - image dominance ratio
   - headshot crop treatment
   - label/badge conventions
   - footer / page furniture conventions

4. `Manifest steering`
   Let retrieval alter:
   - archetype ranking
   - compile target selection
   - compile parameters
   - freeform recipe variant

### 9.5 Required data additions

Each reference slide manifest should store:

- `role`
- `archetype_tag`
- `composition_family`
- `style_tokens`
- `zone_map`
- `content_slots`
- `hero_kind`
- `evidence_kind`
- `density_class`
- `strong_exemplar`
- `do_not_imitate`
- `usable_for_retrieval`

### 9.6 Retrieval scoring

Score candidates across:

- role match
- deck-type match
- content-schema match
- density match
- reference-family match
- style-token match
- benchmark quality weight
- curator confidence

Use this default weighted score until overridden:

| Dimension | Weight |
|---|---:|
| role match | `0.28` |
| content-schema match | `0.18` |
| deck-type match | `0.10` |
| density match | `0.08` |
| composition-family match | `0.14` |
| style-token match | `0.10` |
| benchmark quality weight | `0.07` |
| curator confidence | `0.05` |

Thresholds:

- `>= 0.78`: preferred
- `0.62 - 0.7799`: usable
- `0.45 - 0.6199`: advisory only
- `< 0.45`: do not use automatically

Include deterministic tie-breakers:

- `strong_exemplar`
- higher curator confidence
- lower override debt
- stable manifest sort key

### 9.6A Retrieval trace contract

Every retrieval-backed choice must emit:

```json
{
  "retrieval_trace": {
    "role": "people",
    "reference_family": "ccc_angola_focus_v1",
    "candidate_reference_slides": [
      {"id": "ccc_angola_focus_v1_s04", "score": 0.84, "composition_family": "centered_headshots_row"}
    ],
    "candidate_archetypes": [
      {"id": "key_people_circular_headshots_row", "score": 0.81}
    ],
    "chosen_archetype": "key_people_circular_headshots_row",
    "chosen_variant": "centered_headshots_row_v1",
    "chosen_builder_recipe": "key_people_circular_headshots_row",
    "benchmark_tokens_applied": ["portrait_crop_circle", "headline_centered", "card_shadow_soft"]
  }
}
```

### 9.7 Material generation hooks

Retrieval is only “material” if at least one of these happens:

- archetype `A` beats archetype `B` because reference evidence changes its score
- a generic archetype compiles to variant `v2` because the benchmark family indicates a centered-card rather than left-rail composition
- a freeform manifest receives benchmark-derived token defaults
- benchmark family injects slide-family-specific audit checks

### 9.8 Files

- `src/inkline/intelligence/reference_catalog.py`
- `src/inkline/intelligence/reference_ingest.py`
- `src/inkline/intelligence/archetype_retriever.py`
- `src/inkline/intelligence/full_slide_archetypes.py`
- `src/inkline/intelligence/storyboard.py`
- `tests/intelligence/test_reference_ingest.py`
- `tests/intelligence/test_storyboard_system.py`

### 9.9 Acceptance criteria

- a `key_people` request can retrieve at least `3` candidate reference slides with distinct composition families
- retrieval can change the chosen archetype or compiled variant in a deterministic test fixture
- authoring trace records not only candidates but the exact retrieval effect on the chosen output

---

## 10. Lane B — More Executable Full-Slide Archetypes

### 10.1 Goal

Expand the full-slide archetype system from a thin MVP into a real institutional deck grammar.

### 10.2 Current gap

Only `8` executable archetypes exist today, and many compile into overly generic layouts.

### 10.3 Required coverage

Minimum target for the first serious expansion: `24-32` executable archetypes.

### 10.4 Initial families to add

#### Covers / dividers

- `cover_hero_full_bleed_title_block`
- `cover_editorial_split_photo`
- `divider_full_bleed_section_label`

#### Thesis / proposition

- `numbered_horizontal_proposition_rail`
- `thesis_three_pillar_cards`
- `thesis_two_zone_argument_map`
- `value_creation_step_rail`

#### People / network / local access

- `executive_bio_cards_centered`
- `key_people_circular_headshots_row`
- `boots_on_ground_split_team_access`
- `advisor_network_constellation`

#### Process / timeline

- `banker_vertical_process_spine`
- `horizontal_milestone_timeline_cards`
- `phased_execution_swimlane`
- `mna_process_step_gate`

#### Economics / size of prize

- `firepower_two_zone_summary`
- `value_bridge_waterfall_with_callouts`
- `reserves_cashflow_growth_ladder`
- `sources_uses_stack_with_equity_recycle`

#### Opportunity / pipeline / map

- `live_pipeline_ranked_grid`
- `market_map_reference_exhibit`
- `opportunity_bucket_matrix`
- `stakeholder_landscape_tiers`

#### Appendix / dense evidence

- `appendix_ranked_table_card`
- `appendix_matrix_with_callouts`
- `appendix_evidence_split_table_note`
- `appendix_case_study_panel`

### 10.5 Archetype structure

Each archetype must define:

- functional roles
- required and optional content schema
- benchmark references
- compile target kind
- compile target variants
- allowed builder primitive sets
- density class
- audit checks
- PPTX editability exception policy

### 10.5A Compile variant contract

Each archetype variant must define:

- `variant_id`
- `target_kind`
- `target_id`
- `builder_recipe_id` if applicable
- `required_primitives`
- `default_tokens`
- `density_band`
- `editable_pptx_supported`
- `fallback_policy`

“Meaningfully distinct compiled outputs” is considered satisfied only when variants differ in at least two of:

- composition axis
- hero zone placement
- panel count
- builder recipe
- chrome family
- density band

### 10.6 Compile strategy

Do not let all archetypes collapse into the same generic layouts.

Each archetype must compile via one of:

- existing layout with stricter variant parameters
- template+layout pairing
- freeform manifest using builder primitives

The success condition is not “more archetype names.” It is “more materially different compiled outputs.”

### 10.7 Files

- `src/inkline/intelligence/full_slide_archetypes.py`
- `src/inkline/intelligence/playbooks/full_slide_archetypes.md`
- `src/inkline/app/mcp_resources.py`
- `tests/intelligence/test_storyboard_system.py`
- `tests/pptx/test_institutional_metadata.py`

### 10.8 Acceptance criteria

- at least `24` executable archetypes with tests
- at least `12` of those compile to meaningfully distinct outputs beyond the current generic layout family
- MCP returns full metadata for each archetype
- archetype selection for `cover`, `key_people`, `timeline`, `economics`, and `pipeline` returns multiple viable candidates

---

## 11. Lane C — Benchmark-Aware Audit

### 11.1 Goal

Upgrade the audit from a mostly proxy-driven system to a real multi-dimensional benchmark-aware sign-off layer.

### 11.2 Current gap

The current `audit_storyboard.py` derives multiple dimensions from the same critique proxy verdict:

- `archetype_compliance`
- `reference_family_alignment`
- `message_delivery`

That is not a real measurement system.

### 11.3 Required audit model

Split audit into four classes:

1. `hard render defects`
   - clipping
   - overlap
   - off-page elements
   - missing assets
   - illegal fallback in locked editable mode

2. `archetype compliance`
   - did the slide structurally match the declared archetype?

3. `benchmark alignment`
   - did the slide resemble the declared reference family within allowed variance?

4. `message delivery`
   - did the headline and page structure clearly deliver the declared key message / role?

### 11.4 Required measurable checks

For archetype compliance:

- expected panel count
- expected composition axis
- expected hero zone occupancy
- expected text density range
- expected image/headshot dominance
- expected footer/header chrome presence where archetype requires it

For benchmark alignment:

- composition-family match
- token-family match
- zone-map similarity
- density-class similarity
- title treatment family match
- furniture/chrome similarity

For message delivery:

- presence of dominant headline zone
- evidence zone prominence
- mismatch between declared role and actual slide grammar
- excessive equal-weight fragmentation

### 11.4A Measurement sources and thresholds

Default measurable sources:

- `zone_map` from reference manifests
- `normalized_geometry` from reference ingest
- rendered slide geometry / critique metadata where available
- compiled manifest fields
- export metadata sidecars for PPTX

Default thresholds:

| Check | Pass threshold | Warn threshold |
|---|---:|---:|
| panel count match | exact | +/- 1 |
| composition axis match | exact | n/a |
| hero occupancy ratio | within `0.12` | within `0.20` |
| density band match | exact or adjacent | n/a |
| chrome family match | exact | partial |
| title treatment family | exact | partial |
| role/archetype mismatch | none | any mismatch = warn |

If a required measurement source is absent:

- mark the dimension `not_evaluated`
- do not silently convert it into the generic critique proxy score
- include `reason` in the audit artifact

### 11.5 Audit outputs

Add new artifact section:

```json
{
  "benchmark_audit": {
    "schema_version": 1,
    "slide_results": [
      {
        "slide_id": "s04_key_people",
        "hard_render": {"status": "pass"},
        "archetype_compliance": {"status": "scored", "score": 0.84},
        "benchmark_alignment": {"status": "scored", "score": 0.79},
        "message_delivery": {"status": "warn", "score": 0.63},
        "required_fix": false
      }
    ]
  }
}
```

### 11.6 Separation of verdicts

Deck verdict should be decomposed into:

- `engineering_pass`
- `design_pass`
- `benchmark_alignment_pass`
- `message_pass`
- final `ship_recommendation`

This prevents style critiques from being confused with actual broken output.

### 11.7 Files

- `src/inkline/intelligence/audit_storyboard.py`
- `src/inkline/intelligence/overflow_audit.py`
- `src/inkline/intelligence/vishwakarma.py`
- `src/inkline/app/institutional.py`
- `tests/app/test_storyboard_mcp_resources.py`
- `tests/pptx/test_institutional_metadata.py`

### 11.8 Acceptance criteria

- hard defects are reported independently from archetype/benchmark/message issues
- benchmark-aware dimensions are no longer simple mirrors of the same proxy verdict
- declared benchmark family causes additional audit dimensions to run or explicitly explain why they are unavailable

---

## 12. Lane D — Richer Native Slide Builders

### 12.1 Goal

Make the renderer capable of expressing the archetypes we want without degenerating into childish boxes and manual-looking line work.

### 12.2 Current gap

The native builders still under-express investor-grade slide design because they lack:

- higher-order page primitives
- variant-rich card systems
- composition-aware freeform helpers
- reusable infographic constructs
- benchmark-derived chrome primitives

### 12.3 Required builder primitives

Add a `professional composition primitive layer` for both Typst and PPTX paths.

Minimum primitives:

- hero title block
- title + subtitle + eyebrow group
- numbered rail
- milestone spine with card nodes
- circular and square portrait cards
- tiered stakeholder strip
- callout badge / tab / label
- two-zone economics panel
- value-bridge ladder / waterfall scaffolding
- appendix dense-table shell with side note
- market-map exhibit frame
- grouped statistic card family
- connector routing with snap points
- card shadow / radius / inset token set

### 12.3A Builder recipe contract

Each builder recipe must declare:

- `recipe_id`
- `supported_archetypes`
- `required_primitives`
- `required_data_fields`
- `pdf_backend_supported`
- `pptx_backend_supported`
- `editable_pptx_supported`
- `parity_expectation`
- `raster_exception_policy`

### 12.4 Builder architecture

Do not hand-draw every slide ad hoc.

Add:

- `primitive registry`
- `composition recipes`
- `variant tokens`
- `safe layout solvers`
- `editable PPTX grouping conventions`

The composition recipe layer should assemble primitives into page-level structures like:

- `key_people_circular_headshots_row`
- `banker_vertical_process_spine`
- `value_bridge_waterfall_with_callouts`

### 12.5 PPTX-specific requirements

- native shapes first, images only where unavoidable
- group related elements logically
- preserve editability semantics in export metadata
- explicit exception tagging for raster-only assets
- maintain parity with rendered PDF within tolerance

### 12.6 Typst-specific requirements

- parallel primitives for page-level rendering
- stronger control of spacing, shadows, labels, and card families
- support archetype-specific chrome and token variants

### 12.7 Files

- `src/inkline/pptx/builder.py`
- `src/inkline/pptx/__init__.py`
- `src/inkline/typst/slide_renderer.py`
- `src/inkline/typst/__init__.py`
- `src/inkline/core/grid.py`
- `tests/pptx/test_institutional_metadata.py`

### 12.8 Acceptance criteria

- at least `10` new reusable composition primitives
- at least `6` new recipe-level slide builders
- new archetypes from Lane B can compile to these recipes without fallback
- PPTX remains editable and grouped sensibly

---

## 13. Parallel Sub-Agent Plan

### 13.1 Why sub-agents

This program has separable research and implementation surfaces. It should not be executed as a single monolithic coding pass.

### 13.2 Sub-agent lanes

Use one focused implementation/research sub-agent per lane:

- `Agent A`: reference retrieval and benchmark manifests
- `Agent B`: archetype registry expansion
- `Agent C`: benchmark-aware audit design
- `Agent D`: PPTX/Typst builder primitives and composition recipes
- `Agent E`: corpus curation and external benchmark harvesting

### 13.3 Required agent inputs

Each sub-agent gets:

- current repo snapshot
- the prior reference-driven archetype spec
- current playbooks
- the new shared contract definitions
- benchmark source links and local reference families

### 13.4 Research protocol

Preferred external research path:

- `Perplexity MCP` when authenticated
- otherwise direct web/primary-source fallback

Research should explicitly harvest:

- commercial product capabilities
- research-paper implementation ideas
- concrete full-slide exemplars
- audit/evaluation rubric patterns

### 13.5 Merge protocol

Each agent must write back:

- findings summary
- recommended schema changes
- acceptance criteria
- implementation tasks by file
- risks

Then a coordinating agent merges those outputs into:

- one master spec
- one execution work-program
- one audit pack

---

## 14. Delivery Phases

### Phase 0 — Contract stabilization

Duration: short gating slice  
Output: locked shared schemas and governance rules

### Phase 1 — Parallel lanes

Run in parallel:

- Lane A
- Lane B
- Lane C
- Lane D
- corpus curation

### Phase 2 — Integration

Integrate:

- retrieval → archetype selection
- archetype → compiled manifest
- compiled manifest → builder recipes
- builder output → benchmark-aware audit

### Phase 3 — Fixture validation

Run a full fixture matrix:

- reference-family retrieval fixture
- key-people archetype fixture
- banker timeline fixture
- economics/value-bridge fixture
- benchmark-aware audit fixture
- editable PPTX parity fixture

---

## 15. Validation Matrix

### 15.1 Reference retrieval

- reference family affects candidate ranking
- reference family affects chosen compile variant
- trace records decision path
- locked-spec regression proves retrieval does not change `execution_mode=explicit_spec` outputs

### 15.2 Archetypes

- new archetypes compile cleanly
- missing required fields fail fast
- archetypes remain queryable through MCP

### 15.3 Audit

- hard failures remain hard failures
- benchmark misalignment can fail or warn independently
- message-delivery warnings are not conflated with clipping

### 15.4 Builders

- native PPTX editability preserved
- PDF/PPTX parity within tolerance
- new recipes actually improve visual quality on fixtures

### 15.4A Parity tolerance

Default parity gates for recipe-backed fixtures:

- rendered PDF page count: exact match
- rendered PPTX page count: exact match
- parity diff score: `<= 0.12` for approved recipe families unless explicitly waived
- export metadata assertions:
  - `editable_native_ratio >= 0.95` for editable institutional fixtures
  - no fallback slides on recipe-backed editable institutional fixtures

### 15.4B Visual sign-off gate

Every new recipe-backed archetype family must pass:

- rendered PDF visual critique
- rendered PPTX visual critique after `soffice` conversion
- human artifact review on the golden fixture family

The program is not complete if it only satisfies schema-level checks.

### 15.5 Confidentiality and packaging

- private/client reference assets must remain under local private catalog roots
- MCP payloads must not expose host-bound paths or raw confidential source labels
- packaged/public catalogs may only contain explicitly reusable benchmark families

### 15.6 Phase-0 gating tests

Lane 0 is not complete until the following exist:

- schema validation tests for all four v2/v1 contracts
- v1 -> v2 normalization tests
- confidentiality tests for local/private reference assets
- deterministic serialization snapshots for reference, archetype, compiled-manifest, and audit payloads
- MCP payload redaction tests for paths, source labels, preview assets, and private family ids

### 15.7 Distinct-output evidence gate

Claims that `12` archetypes or variants are “meaningfully distinct” must be backed by:

- golden artifact snapshots
- one-line visual distinction notes per variant family
- composition difference across at least two declared dimensions

---

## 16. Risks

### 16.1 Too much retrieval, not enough curation

Mitigation:

- strong curator overrides
- explicit `strong_exemplar`
- `do_not_imitate`

### 16.2 Archetype explosion

Mitigation:

- start with `24-32`, not hundreds
- enforce compile-support and tests per archetype

### 16.3 Audit overfitting

Mitigation:

- keep hard defects separate
- keep benchmark alignment partly advisory where similarity is inherently fuzzy

### 16.4 Builder complexity outruns parity

Mitigation:

- add primitives and recipes incrementally
- require PPTX/PDF parity tests for each recipe family

---

## 17. Success Criteria

The program is successful when:

1. reference retrieval materially changes generation on fixture decks
2. the archetype system covers a believable institutional slide grammar
3. benchmark-aware audit produces non-proxy measurements
4. native builders can express investor-grade infographic slides more convincingly
5. the deterministic execute engine still does not invent design choices

---

## 18. Approval State

This spec has completed external `gpt-5.5` audit review and is approved for implementation subject to executing `Lane 0 / Slice S0` first inside the work-program.
