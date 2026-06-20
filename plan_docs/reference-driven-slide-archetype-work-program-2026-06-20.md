# Inkline Reference-Driven Slide Archetype System — Work Program

**Date:** 20 June 2026
**Status:** Execution-ready after spec audit
**Parent spec:** `plan_docs/reference-driven-slide-archetype-system-spec-2026-06-20.md`
**Primary repo:** `/home/k1mini/inkline`

---

## 1. Delivery Objective

Implement a phased system that lets Inkline:

- ingest benchmark decks into reusable `reference families`
- reason about `full-slide archetypes` rather than only local layouts/exhibits
- serialize and persist `storyboard` and `key message` metadata
- align the visual auditor with the same archetype and message vocabulary
- preserve Execute Mode determinism and current renderer contracts

This is **not** a single sprint. It is a staged program with hard stop points.

---

## 2. Program Guardrails

1. Do not break `Execute Mode` render determinism.
2. Do not make the renderer depend on LLM calls.
3. Do not commit private or client-confidential reference assets to the public repo.
4. Treat `full-slide archetype` as an authoring/audit abstraction that compiles down to existing layout/template/freeform constructs.
5. Do not ship a monolithic “smart deck system” in one branch. Land and verify phases independently.

---

## 3. Phase Plan

### Phase 1 — Storyboard Metadata MVP

#### Goal

Add the metadata contract required for future archetype-aware authoring and auditing without changing the renderer’s core behavior.

#### Deliverables

- storyboard schema definitions
- markdown front-matter + per-section directive support for storyboard fields
- JSON/YAML fixture support for storyboard fields
- stable slide IDs
- `authoring_trace.json` schema and basic persistence
- canonical `schema_name` / `schema_version` contract across storyboard, trace, reference manifests, and audit artifacts
- one metadata precedence / merge policy shared by authoring, parser, runtime bridge, and audit
- single validation/merge boundary owned by the storyboard resolver
- legacy-spec compatibility shim for missing storyboard metadata

#### Files

- `src/inkline/authoring/preprocessor.py`
- `src/inkline/app/cli.py`
- `src/inkline/app/institutional.py`
- `src/inkline/intelligence/storyboard.py` (new)
- `src/inkline/intelligence/storyboard_schema.py` (new)
- `src/inkline/typst/__init__.py` or current export path modules where metadata passthrough is wired
- `docs/USER_GUIDE.md`
- `README.md`

#### Implementation steps

1. Define `StoryboardDeck`, `StoryboardSlide`, and `StoryboardBundle` dataclasses or TypedDicts.
2. Add schema validation helpers.
3. Add one metadata merge resolver with conflict logging and hard-fail behavior for malformed higher-precedence fields.
4. Extend markdown preprocessing to accept:
   - `_slide_role`
   - `_archetype`
   - `_key_message`
   - optional `slide_id`
5. Extend JSON/YAML fixture support to preserve embedded storyboard blocks.
6. Generate stable `slide_id` if missing.
7. Persist `authoring_trace.json` next to output artifacts when present.
8. Ensure Execute Mode ignores missing storyboard metadata.

#### Tests

- markdown round-trip with storyboard front matter
- per-section directives preserved
- fixture JSON/YAML round-trip
- stable slide ID generation
- renderer unaffected when storyboard absent
- conflicting metadata resolves according to canonical precedence order
- malformed higher-precedence metadata hard-fails validation rather than silently falling back

#### Phase gate

- Existing render commands still work unchanged for legacy specs.
- No LLM dependency introduced in Execute Mode.

---

### Phase 2 — Full-Slide Archetype Vocabulary

#### Goal

Introduce the new authoring/audit abstraction layer without changing the renderer object model.

#### Deliverables

- `full_slide_archetypes` playbook
- schema for full-slide archetypes
- compiler mapping from full-slide archetype → layout/template/freeform
- versioned `compiled_slide_manifest` contract
- initial institutional archetype set
- PPTX parity/editability exception model

#### Files

- `src/inkline/intelligence/full_slide_archetypes.py` (new)
- `src/inkline/intelligence/playbooks/full_slide_archetypes.md` (new)
- `src/inkline/app/mcp_resources.py`
- `src/inkline/intelligence/design_advisor.py`
- `tests/authoring/...` or `tests/intelligence/...`

#### Implementation steps

1. Define canonical schema:
   - `id`
   - `functional_roles`
   - `content_schema`
   - `visual_intent`
   - `compile_targets`
   - `benchmark_refs`
   - `audit_checks`
2. Add loader APIs similar to current playbook/archetype utilities.
3. Add MCP resource endpoints:
   - `inkline://archetypes/full_slide`
   - `inkline://archetypes/full_slide/<id>`
4. Encode the first institutional archetype set from the parent spec.
5. Add compile mapping:
   - direct to current layout
   - direct to template + layout
   - or to `freeform`
6. Define `compiled_slide_manifest` schema and parity assertions for PDF/PPTX/editable PPTX.
7. Document normalization with current concepts: layout/template/archetype/freeform.

#### Tests

- resource listing and retrieval
- schema validation
- compile target resolution
- failure when required content schema missing
- compiled manifest validates and contains only renderer-native constructs

#### Phase gate

- No archetype compiles to an unsupported renderer primitive.
- Every MVP archetype resolves to an existing layout or `freeform`.

---

### Phase 3 — Reference-Family Ingestion MVP

#### Goal

Support benchmark-driven design grounding using local/private curated decks first, with explicit provenance and governance.

#### Deliverables

- PPTX-first ingestion path
- local private reference catalog
- resource schemas for `reference_family` and `reference_slide`
- manual curation CLI or lightweight file-based workflow
- classification enforcement at ingest/package time

#### Files

- `src/inkline/intelligence/reference_ingest.py` (new)
- `src/inkline/intelligence/reference_catalog.py` (new)
- `src/inkline/intelligence/reference_schema.py` (new)
- `src/inkline/app/cli.py`
- `src/inkline/app/mcp_resources.py`
- `docs/USER_GUIDE.md`
- `README.md`

#### Implementation steps

1. Define storage paths:
   - packaged defaults
   - local private catalog
2. Build PPTX extractor:
   - shapes
   - text boxes
   - fonts
   - colors
   - image zones
3. Normalize geometry into `[0,1]` coordinate boxes.
4. Emit:
   - `reference_family.json`
   - per-slide manifests
   - preview PNGs in local private store only
5. Add governance fields:
   - license class
   - provenance
   - confidence
   - version
6. Add CLI:
   - `inkline ingest-reference deck.pptx --family ccc_angola_focus_v1`
   - or equivalent
7. Add manual curation support:
   - editable `curation_overrides.yaml`
   - `strong_exemplar`
   - `do_not_imitate`
   - notes and override precedence logging

#### Tests

- PPTX ingest emits normalized manifest
- private/public precedence resolution
- confidential assets are never written into packaged paths
- curator overrides persist and win over inferred labels

#### Phase gate

- Benchmark ingestion works locally without contaminating public repo assets.
- Reference families can be listed via MCP resources.

---

### Phase 4 — Authoring Retrieval and Traceability

#### Goal

Let the authoring layer retrieve and choose candidate full-slide archetypes and reference slides, while keeping decisions explainable.

#### Deliverables

- archetype retrieval API
- reference-family filtering
- deterministic tie-breaking
- `authoring_trace.json` with scores and rationale

#### Files

- `src/inkline/intelligence/archetype_retriever.py` (new)
- `src/inkline/intelligence/design_advisor.py`
- `src/inkline/intelligence/storyboard.py`
- `tests/intelligence/...`

#### Implementation steps

1. Implement metadata/heuristic retrieval first:
   - role
   - content schema
   - deck type
   - benchmark family
2. Return top-k candidates with scores.
3. Define deterministic tie-break ordering.
4. Emit chosen archetype plus rejected candidates into `authoring_trace.json`.
5. Add fallback behavior:
   - baseline approved layout family if no match above threshold
6. Keep embedding/vector retrieval out of MVP.

#### Tests

- deterministic ranking on repeated runs
- fallback recorded when threshold not met
- explainability artifact emitted

#### Phase gate

- Retrieval works without embeddings.
- Results are reproducible enough for debugging.

---

### Phase 5 — Archetype-Aware Auditor

#### Goal

Upgrade the auditor to use the same storyboard/archetype/reference-family vocabulary as authoring, while separating hard checks from advisory judgments.

#### Deliverables

- new audit metadata contract
- hard vs soft scoring split
- `not_evaluated` dimension handling
- archetype-compliance checks where measurable
- reference-family alignment checks where explicit tokens exist
- deck-level verdict contract and aggregation rules
- minimum evaluated-dimension policy for client-facing decks
- versioned default threshold settings shared by tests and audit runtime

#### Files

- `src/inkline/intelligence/overflow_audit.py`
- `src/inkline/intelligence/vishwakarma.py`
- `src/inkline/app/institutional.py`
- `tests/intelligence/...`
- `docs/templates/manual_qa_checklist_institutional.md`

#### Implementation steps

1. Extend audit input payload with:
   - storyboard
   - slide role
   - full-slide archetype
   - reference family
2. Add audit dimension model:
   - `visual_quality`
   - `archetype_compliance`
   - `reference_family_alignment`
   - `message_delivery`
3. Mark each dimension as:
   - hard-scored
   - advisory
   - not evaluated
4. Add measurable archetype checks:
   - portrait dominance
   - card counts
   - column symmetry/asymmetry
   - footer strip presence
5. Add family-token checks where explicit:
   - palette match
   - title scale band
   - footer chrome presence
6. Add deck verdict aggregation:
   - `pass`
   - `pass_with_warnings`
   - `needs_human_signoff`
   - `fail`
7. Encode client-facing gate rules for hard fails, human sign-off, and warning budgets.
8. Keep message delivery advisory unless explicit evidence is available.

#### Tests

- audit with full metadata
- audit with missing metadata
- `not_evaluated` emitted correctly
- hard/soft dimension separation preserved
- any hard-fail slide defect yields deck verdict `fail`
- missing required evaluated dimensions yields at least `needs_human_signoff`

#### Phase gate

- Auditor remains usable for legacy decks.
- New audit path does not silently infer passes where metadata is missing.

---

### Phase 6 — Research Corpus Expansion and Retrieval Optimization

#### Goal

Scale the system beyond heuristic MVP.

#### Deliverables

- larger benchmark corpus
- optional embedding/index retrieval
- better role/archetype coverage
- more benchmark-family examples

#### Files

- `src/inkline/intelligence/reference_catalog.py`
- `src/inkline/intelligence/archetype_retriever.py`
- new local/private corpora
- new playbook updates

#### Implementation steps

1. Expand benchmark families for:
   - consulting
   - PE / investment
   - board
   - product / tech
2. Add optional embeddings if needed.
3. Keep traceability identical to heuristic mode.
4. Validate retrieval quality against curated test prompts.

#### Phase gate

- Embedding retrieval is optional and feature-gated.
- Heuristic fallback still exists.

---

## 4. Research and Curation Workstream

### Objective

Build the best-in-class slide corpus needed for the archetype system.

### Inputs

- public benchmark decks
- template marketplaces
- existing Inkline template catalog lineage
- internal/private operator benchmark decks

### Outputs

- curated `reference_family` seeds
- tagged `full-slide archetype` exemplars
- benchmark notes for:
  - role
  - geometry
  - style language
  - reuse suitability

### Required tag dimensions

- `deck_type`
- `functional_role`
- `industry`
- `density_class`
- `page_gesture`
- `brand_mood`
- `evidence_mode`

### Initial research target families

- private equity / investment committee
- strategy consulting / MBB-adjacent
- investor relations / capital markets
- product strategy / enterprise SaaS

---

## 5. Test Strategy

### Fixture classes

1. `legacy execute-mode deck`
   Confirms no regression.

2. `storyboard-tagged markdown deck`
   Confirms metadata bridge.

3. `institutional JSON/YAML fixture deck`
   Confirms round-trip with storyboard/archetype fields.

4. `reference-family ingestion fixture`
   Confirms PPTX extraction and governance metadata.

5. `archetype-aware audit fixture`
   Confirms new audit dimensions and fallback reporting.

### Verification artifacts

- `storyboard.json`
- `authoring_trace.json`
- `reference_family.json`
- audit JSON with dimension reporting

---

## 6. Acceptance Gates By Phase

### Phase 1 gate

- Existing render paths unchanged
- storyboard metadata persists cleanly
- schema versions and metadata precedence are explicit and test-covered

### Phase 2 gate

- first institutional archetype set queryable via MCP
- all archetypes compile to existing renderer abstractions

### Phase 3 gate

- local benchmark ingest works on PPTX
- provenance/governance fields present

### Phase 4 gate

- authoring can choose and record candidate archetypes deterministically

### Phase 5 gate

- auditor consumes shared metadata and reports hard/soft dimensions correctly
- deck verdict semantics are deterministic and test-covered

### Phase 6 gate

- larger corpus improves candidate retrieval without breaking explainability

---

## 7. Ownership Suggestions

### Knowledge / taxonomy

- playbooks
- slide role taxonomy
- full-slide archetype definitions
- benchmark-family curation

### Authoring

- storyboard generation
- retrieval
- authoring trace
- override semantics

### Rendering compatibility

- compile mappings from archetype to layout/freeform
- PPTX parity where relevant

### Audit

- hard vs soft checks
- metadata-aware evaluation
- dimension reporting

---

## 8. Immediate Next Actions

1. Approve the revised parent spec.
2. Land Phase 1 and Phase 2 as the first implementation tranche.
3. Keep Phase 3 local/private by default.
4. Do not start Phase 5 until the storyboard and archetype metadata are stable.
5. Build the benchmark corpus in parallel with engineering, but do not block Phase 1 on full corpus completion.

---

## 9. Post-Code Audit Plan

A formal post-code audit should only run after implementation phases land.

For each phase:

1. run focused tests
2. run artifact-based visual checks where relevant
3. run an independent external code/spec audit
4. record residual risks before moving to the next phase

Post-code audit is therefore a phase-exit gate, not a pre-implementation document artifact.
