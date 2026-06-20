# Inkline Parallel Gap-Closure Program — Execution Work-Program

**Date:** 20 June 2026  
**Status:** Approved for implementation  
**Parent spec:** `plan_docs/parallel-gap-closure-spec-2026-06-20.md`  
**Primary repo:** `/home/k1mini/inkline`

---

## 1. Delivery Strategy

This program should be executed in `6` slices:

1. `S0` shared contracts and fixtures
2. `S1A` reference-driven retrieval
3. `S1B` executable archetype expansion
4. `S1C` benchmark-aware audit
5. `S1D` native builder primitives and recipes
6. `S2` integration, fixture validation, and sign-off

`S1A` through `S1D` are intended to run in parallel once `S0` is complete.

This document is implementation-ready. `S0` is not a blocker to starting the program; it is the first execution slice and must be completed before the parallel lanes branch.

---

## 2. Slice S0 — Shared Contracts and Fixture Gating

### Goal

Freeze the schemas and test corpus required by the parallel lanes.

### Tasks

1. Extend reference-slide manifests with:
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

2. Extend full-slide archetype manifests with:
   - `compile_variants`
   - `density_class`
   - `allowed_primitives`
   - `pptx_editability_policy`

3. Extend compiled slide manifests with:
   - `source_archetype`
   - `source_reference_family`
   - `source_reference_slide_ids`
   - `builder_recipe_id`
   - `variant_id`
   - `benchmark_tokens_applied`

4. Extend benchmark audit schema with:
   - `hard_render`
   - `archetype_compliance`
   - `benchmark_alignment`
   - `message_delivery`
   - `ship_recommendation`

5. Define fixture families:
   - people slide
   - process/timeline slide
   - economics slide
   - market map / asset overview
   - appendix dense evidence slide

6. Introduce explicit validator entry points:
   - `validate_reference_slide_manifest()`
   - `validate_full_slide_archetype()`
   - `validate_compiled_slide_manifest()`
   - `validate_benchmark_audit()`

7. Define v1 -> v2 normalization rules for all existing dict payloads.

8. Freeze deterministic serialization order for:
   - reference manifests
   - archetype manifests
   - compiled manifests
   - audit artifacts

### Files

- `src/inkline/intelligence/reference_schema.py`
- `src/inkline/intelligence/full_slide_archetypes.py`
- `src/inkline/intelligence/audit_storyboard.py`
- `tests/intelligence/`
- `tests/pptx/`
- `examples/institutional/`

### Gate

- schemas compile and serialize
- fixture definitions checked in
- no lane proceeds against ambiguous fields
- v1 payloads normalize cleanly to v2
- confidentiality tests prove private assets and source labels do not leak
- MCP/resource payload redaction tests prove path/source/preview fields are sanitized

---

## 3. Slice S1A — Reference-Driven Retrieval

### Goal

Make benchmark retrieval materially steer generated outputs.

### Task group A1 — Reference manifest enrichment

1. Update ingest pipeline to compute:
   - normalized title zone
   - title alignment
   - card/grid count
   - dominant composition axis
   - hero occupancy ratio
   - chrome/footer/header presence
   - image/headshot treatment
   - typography treatment class
   - density class

2. Store these fields in reference-slide manifests.

3. Add curation override support for:
   - composition family
   - archetype tag
   - role
   - benchmark quality weight
   - `strong_exemplar`
   - `do_not_imitate`

### Task group A2 — Retrieval scoring

1. Replace the current shallow retrieval path with explicit scoring dimensions:
   - role match
   - deck-type match
   - content-schema match
   - density match
   - composition-family match
   - style-token match
   - curator confidence
   - benchmark quality

2. Add deterministic tie-break ordering.

3. Add thresholds for:
   - `qualified`
   - `advisory only`
   - `do not use`

4. Implement the default weights from the parent spec unless overridden:
   - role match `0.28`
   - content-schema match `0.18`
   - deck-type match `0.10`
   - density match `0.08`
   - composition-family match `0.14`
   - style-token match `0.10`
   - benchmark quality `0.07`
   - curator confidence `0.05`

### Task group A3 — Material generation hooks

1. Add a variant-selection step after archetype scoring.

2. Permit retrieval to alter:
   - chosen archetype
   - chosen compile variant
   - chosen builder recipe
   - token defaults

3. Emit these decisions into `authoring_trace`.

4. Add deterministic trace fields:
   - selected reference slide ids
   - score components
   - chosen archetype
   - chosen variant
   - chosen builder recipe
   - benchmark tokens applied

### Files

- `src/inkline/intelligence/reference_ingest.py`
- `src/inkline/intelligence/reference_catalog.py`
- `src/inkline/intelligence/archetype_retriever.py`
- `src/inkline/intelligence/storyboard.py`
- `src/inkline/intelligence/full_slide_archetypes.py`
- `tests/intelligence/test_reference_ingest.py`
- `tests/intelligence/test_storyboard_system.py`

### Acceptance

- retrieval changes generated variant selection on at least `3` fixture families
- trace clearly records the retrieval effect
- trace assertions are covered in tests, not just manual artifact inspection
- locked-spec regression proves retrieval steering does not alter `execution_mode=explicit_spec` outputs

---

## 4. Slice S1B — Executable Archetype Expansion

### Goal

Expand from `8` archetypes to a real institutional page grammar.

### Task group B1 — Registry expansion

Add archetypes for:

- covers/dividers
- thesis/proposition
- people/network
- timeline/process
- economics/firepower
- opportunity/pipeline/map
- appendix/dense evidence

Target:

- `24-32` executable archetypes

### Task group B2 — Compile variants

For each new archetype:

1. decide compile path:
   - existing layout
   - template + layout
   - builder recipe / freeform

2. define content schema requirements
3. define density class
4. define benchmark refs
5. define audit checks
6. define:
   - `variant_id`
   - `builder_recipe_id`
   - `editable_pptx_supported`
   - `fallback_policy`

### Task group B3 — MCP surface

1. Ensure every archetype is queryable via:
   - `inkline://archetypes/full_slide`
   - `inkline://archetypes/full_slide/<id>`

2. Add fields needed by external LLM authoring:
   - role fit
   - expected message shape
   - expected hero zone
   - density class
   - compile target
   - benchmark families commonly associated

### Files

- `src/inkline/intelligence/full_slide_archetypes.py`
- `src/inkline/intelligence/playbooks/full_slide_archetypes.md`
- `src/inkline/app/mcp_resources.py`
- `tests/intelligence/test_storyboard_system.py`
- `tests/app/test_storyboard_mcp_resources.py`

### Acceptance

- archetype count reaches target
- at least `12` produce meaningfully distinct compiled outputs
- missing required schema fails fast with precise error
- each distinct output claim is backed by fixture comparisons or snapshot tests
- each distinct output family includes a reviewed rendered artifact, not only manifest differences

---

## 5. Slice S1C — Benchmark-Aware Audit

### Goal

Turn audit into a multi-dimensional sign-off system rather than a single proxy verdict.

### Task group C1 — Dimension split

Implement explicit audit dimensions:

- `hard_render`
- `archetype_compliance`
- `benchmark_alignment`
- `message_delivery`

### Task group C2 — Measurable checks

Add measurable checks for:

- panel count
- composition axis
- hero occupancy
- density band
- image dominance
- title treatment family
- chrome family
- role/archetype mismatch

Also implement default threshold logic from the parent spec for:

- panel count match
- composition axis match
- hero occupancy ratio
- density band match
- chrome family match
- title treatment family match

### Task group C3 — Verdict logic

1. Add independent verdicts:
   - `engineering_pass`
   - `design_pass`
   - `benchmark_alignment_pass`
   - `message_pass`
   - `ship_recommendation`

2. Keep hard failures blocking.

3. Keep benchmark/style failures separately classified.

4. Where a measurement source is missing, record:
   - `status=not_evaluated`
   - a machine-readable `reason`
   - no silent substitution with the generic proxy verdict

### Task group C4 — Artifact output

Write enriched audit output into:

- PDF critique artifacts
- PPTX rendered critique artifacts
- storyboard-aware audit summaries

### Files

- `src/inkline/intelligence/audit_storyboard.py`
- `src/inkline/app/institutional.py`
- `src/inkline/intelligence/vishwakarma.py`
- `src/inkline/intelligence/overflow_audit.py`
- `tests/pptx/test_institutional_metadata.py`
- `tests/app/test_storyboard_mcp_resources.py`

### Acceptance

- benchmark alignment is not populated from the same simple proxy field as archetype compliance
- hard defects remain independently detectable
- missing measurement sources degrade explicitly and predictably
- recipe-backed fixture decks must pass rendered PDF and rendered PPTX critique before sign-off

---

## 6. Slice S1D — Native Builder Primitives and Recipes

### Goal

Give the renderer enough page-level expressive power to implement the new archetypes cleanly.

### Task group D1 — Primitive registry

Add reusable primitives for:

- title groups
- badges/tabs
- portrait cards
- metric cards
- milestone nodes
- numbered rails
- connector routing
- callout badges
- exhibit frames
- dense appendix shells

For each primitive, define:

- primitive id
- supported backends
- editable PPTX support
- layout constraints
- token inputs

### Task group D2 — Recipe layer

Create composition recipes for:

- `key_people_circular_headshots_row`
- `boots_on_ground_split_team_access`
- `banker_vertical_process_spine`
- `horizontal_milestone_timeline_cards`
- `value_bridge_waterfall_with_callouts`
- `live_pipeline_ranked_grid`
- `stakeholder_landscape_tiers`
- `appendix_evidence_split_table_note`

For each recipe, define:

- `recipe_id`
- required primitives
- required data schema
- supported archetypes
- parity expectation
- raster exception policy

### Task group D3 — PPTX editability discipline

1. prefer native shapes and text
2. add logical groupings
3. annotate raster-only exceptions
4. verify parity against rendered PDF output

### Task group D4 — Typst parity

Mirror the new recipe families in the Typst path to avoid PDF/PPTX divergence.

### Files

- `src/inkline/pptx/builder.py`
- `src/inkline/pptx/__init__.py`
- `src/inkline/typst/slide_renderer.py`
- `src/inkline/typst/__init__.py`
- `src/inkline/core/grid.py`
- `tests/pptx/test_institutional_metadata.py`

### Acceptance

- at least `10` new primitives
- at least `6` recipe-level slide families
- no unjustified fallback on recipe-backed archetypes
- every new recipe has PDF/PPTX parity checks and editable PPTX expectations
- parity tolerance is explicitly enforced:
  - page count exact match
  - parity diff score `<= 0.12` unless waived
  - `editable_native_ratio >= 0.95` on editable institutional fixtures

---

## 7. Slice S2 — Integration and Sign-Off

### Goal

Wire the lanes together and verify the system on real fixture decks.

### Tasks

1. connect retrieval outputs to archetype/variant selection
2. connect chosen archetype to builder recipe or compile variant
3. connect builder outputs to benchmark-aware audit checks
4. run the fixture matrix
5. run editable PPTX inspection and rendered PPTX audit
6. produce before/after artifacts for sign-off

7. run explicit confidentiality checks on benchmark catalogs and MCP payloads

### Acceptance

- one locked-spec fixture deck per family renders cleanly
- benchmark-aware audit produces distinct dimension scores
- PPTX editability stays acceptable
- private/local reference assets stay out of public/packageable outputs
- every fixture family has:
  - rendered PDF audit artifact
  - rendered PPTX audit artifact
  - human-reviewed golden artifact snapshot

---

## 8. Recommended Sub-Agent Assignment

### Agent 0 — Integrator / contract owner

Owns:

- schemas
- fixture matrix
- final merges

### Agent A — Retrieval

Owns:

- reference manifest enrichment
- retrieval scoring
- generation steering hooks

### Agent B — Archetypes

Owns:

- registry expansion
- archetype schema quality
- MCP exposure

### Agent C — Audit

Owns:

- benchmark-aware dimensions
- verdict logic
- artifact contracts

### Agent D — Builders

Owns:

- primitive registry
- recipe implementations
- PPTX/Typst parity

### Agent E — Corpus / research

Owns:

- benchmark deck tagging
- full-slide exemplar catalog
- external best-practice research notes

---

## 9. Testing Plan

### Unit / schema tests

- manifest validation
- v1 -> v2 normalization
- retrieval scoring determinism
- archetype required-field validation
- audit dimension serialization

### Integration tests

- retrieval changes chosen variant
- archetype compiles to recipe-backed output
- benchmark family triggers benchmark-aware audit dimensions
- editable PPTX export remains compliant
- confidentiality filtering survives ingestion and MCP exposure

### Golden artifact tests

- compare rendered PDF baselines
- compare rendered PPTX baselines
- inspect export metadata
- review visual distinction evidence for the claimed `12` materially distinct outputs

### Required fixture / golden matrix

The program must maintain approved golden fixtures for:

- `fixture_cover_family`
- `fixture_key_people_family`
- `fixture_process_timeline_family`
- `fixture_economics_family`
- `fixture_market_map_family`
- `fixture_appendix_dense_family`

Each fixture family must include:

- source spec
- expected storyboard / trace artifacts
- rendered PDF baseline
- rendered PPTX baseline
- PPTX export metadata baseline
- audit artifact baseline

---

## 10. Stop Conditions

Pause the program if any of these happen:

- execute mode starts depending on LLM reasoning
- archetype additions outpace builder support
- benchmark assets risk leaking into packaged/public resources
- audit becomes too subjective to produce stable regression results

---

## 11. Immediate Next Output

Execution should start with `S0`, then branch into `S1A-S1D` in parallel once the shared contracts and fixture gates are landed.
