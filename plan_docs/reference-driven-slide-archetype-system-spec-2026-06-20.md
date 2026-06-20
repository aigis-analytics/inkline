# Inkline Reference-Driven Slide Archetype System — Specification

**Date:** 20 June 2026
**Status:** Draft for audit
**Primary repo:** `/home/k1mini/inkline`
**Objective:** Upgrade Inkline from a layout/exhibit-oriented deck generator into a reference-driven, storyboard-aware presentation system that can generate and audit full-slide designs against benchmark decks, explicit messaging intent, and shared design knowledge.

---

## 1. Executive Summary

Inkline today has strong foundations:

- a deterministic execution engine for `PDF` / `PPTX`
- an MCP knowledge layer with playbooks, slide-type guidance, archetypes, and anti-patterns
- an optional authoring layer (`DesignAdvisor`, bridge, Draft Mode)
- a post-render visual audit layer (`Vishwakarma` / critique)

But it still underperforms on high-end investor and consulting decks because it reasons primarily in terms of:

- exhibit types
- generic layouts
- local spacing / overflow

rather than:

- full-slide functional archetypes
- benchmark slide families
- deck-level story progression
- message-carrying page roles
- stylistic correspondence to a reference deck

The result is predictable:

- slides are often structurally valid but visually cautious
- decks are coherent in content but weak in editorial force
- the visual auditor can flag broad problems but is not grounded in the same archetype and storyboard system as the authoring layer

This spec introduces a new core system:

1. `Reference Deck Ingestion`
   Parse best-in-class example decks into reusable design signals and slide-archetype exemplars.
2. `Full-Slide Archetype MCP`
   Add a new MCP layer for complete slide designs indexed by functional role, message shape, and content schema.
3. `Storyboard + Key Message Contract`
   Require the authoring layer to emit deck-level intent in machine-readable form.
4. `Aligned Auditor`
   Make the visual auditor check against the same archetype language, reference family, and storyboard objectives as the authoring layer.

---

## 2. Problem Statement

### 2.1 Current failure mode

Inkline can render:

- clean decks
- overflow-safe decks
- editable institutional PPTX output for some slide families

But that is not enough for professional investor-grade slide design.

The key observed failure mode is:

> The system generates safe, box-driven, template-like slides instead of bold, persuasive, full-page designs with strong editorial hierarchy.

Examples from the AGEH / 7GI Angola workflow showed:

- covers that behaved like title slides rather than presentation covers
- proposition slides that used equal-weight cards instead of a stronger narrative gesture
- people slides that were valid but generic
- economics and timeline slides that conveyed logic without enough design conviction

### 2.2 Root cause

The root cause is not primarily Typst or the PPTX renderer.

The root cause is a missing intermediate abstraction layer:

- the authoring system lacks a first-class concept of `full-slide archetypes`
- the auditor lacks a first-class concept of `expected slide family and message role`
- the reference-deck workflow is ad hoc, not formalized
- the system optimizes for acceptable layouts, not persuasive page design

---

## 3. External Research Summary

### 3.1 Commercial product patterns

The best current presentation products consistently rely on full-slide systems rather than raw freeform generation.

#### Beautiful.ai

Beautiful.ai explicitly positions `Smart Slides` as built-in designer-quality layouts that:

- auto-align
- auto-resize
- adapt as content changes
- stay on brand through theme/brand control

This is not merely a chart library. It is a full-slide adaptive layout system.

Sources:

- [Beautiful.ai Smart Slides](https://www.beautiful.ai/smart-slides)
- [Beautiful.ai slide templates](https://www.beautiful.ai/slide-templates)

#### Pitch Agent

Pitch Agent explicitly claims it:

- builds from real templates
- uses fully custom layouts
- reflects the patterns that define the brand
- produces editable, on-brand slides

This is closer to reference-family generation than generic templating.

Sources:

- [Pitch Agent announcement](https://pitch.com/whats-new/introducing-pitch-agent)
- [Pitch AI presentation maker](https://pitch.com/use-cases/ai-presentation-maker)
- [Pitch template library](https://help.pitch.com/en/articles/3752837-create-a-template)

#### Canva Magic Design

Canva’s presentation workflow emphasizes:

- generating a draft deck from a prompt
- producing outline + narrative flow
- then applying Brand Kit

So Canva couples story structure with design generation rather than treating them separately.

Sources:

- [Canva AI presentation maker](https://www.canva.com/create/ai-presentations/)
- [Canva Magic Design help](https://www.canva.com/help/using-magic-presentations/)

#### Microsoft Copilot in PowerPoint

Microsoft’s Copilot workflow emphasizes:

- creating presentations from files
- branded presentation generation
- tone/style controls
- preserving PowerPoint-native editability

This is important because it shows the market expects:

- source-grounded authoring
- branded output
- message-shaping controls

Sources:

- [Create a new presentation with Copilot in PowerPoint](https://support.microsoft.com/en-us/powerpoint/copilot/create-a-new-presentation-with-copilot-in-powerpoint)
- [Create a branded presentation from a file](https://support.microsoft.com/en-us/powerpoint/copilot-tutorial-create-a-branded-presentation-from-a-file)

#### Presentations.AI

Presentations.AI positions itself around:

- high-quality on-brand decks
- editable PowerPoint output
- transforming ideas/documents/data into presentation-ready decks

Source:

- [Presentations.AI](https://www.presentations.ai/)

### 3.2 Research patterns

The academic literature supports three design directions highly relevant to Inkline:

#### Retrieval-guided layout generation

`RALF` shows that layout generation improves when the model can retrieve reference layouts and use them as guidance during generation.

Source:

- [RALF](https://arxiv.org/html/2311.13602v3)

#### Reference-slide editing instead of one-shot generation

`PPTAgent` analyzes reference presentations, extracts slide-level functional types and content schemas, then generates by selecting reference slides and editing toward them.

This is especially relevant to Inkline.

Source:

- [PPTAgent](https://arxiv.org/html/2501.03936v3)

#### Fine-grained rubric-based evaluation

`PresentBench` argues that useful slide evaluation must be:

- instance-specific
- checklist-based
- audience-aware
- message-aware
- structure-aware

Source:

- [PresentBench](https://arxiv.org/html/2603.07244v1)

### 3.3 Implication for Inkline

Inkline should not try to outcompete these systems by adding more generic slide templates.

It should instead:

- formalize reference retrieval
- formalize full-slide archetypes
- formalize storyboard intent
- formalize archetype-aware audit

---

## 4. Goals

### 4.1 Product goals

Inkline should be able to:

1. ingest best-in-class example decks and extract reusable design families
2. generate new decks that follow the same design philosophy and page language
3. choose from complete slide archetypes, not just local exhibit types
4. require a machine-readable storyboard and key message map
5. audit rendered output against:
   - visual quality
   - chosen archetypes
   - benchmark family
   - deck-level message intent

### 4.2 Non-goals

This spec does not attempt:

- a pixel-perfect “clone any deck” engine
- a WYSIWYG editor
- total automation of design taste without human review
- arbitrary style transfer from a single image prompt

The aim is a controlled, retrieval-aware system with explainable choices.

### 4.3 Mode boundaries

This spec must respect Inkline’s core product split.

#### Execute Mode

Execute Mode remains:

- deterministic at render time
- able to render from markdown or JSON/YAML specs with no LLM call
- unaffected by retrieval, storyboard inference, or benchmark-family selection unless that metadata has already been authored upstream

Execute Mode may consume:

- explicit `storyboard` metadata already embedded in the spec
- explicit `full_slide_archetype` fields already embedded in the spec
- explicit `reference_family` tags already embedded in the spec

But it does **not** perform:

- reference retrieval
- archetype ranking
- storyboard inference
- benchmark-family selection

#### Draft Mode / authoring layer

The following capabilities are Draft Mode or authoring-layer responsibilities:

- generating `storyboard.json`
- selecting a `reference_family`
- retrieving candidate archetypes
- ranking reference slides
- emitting `authoring_trace.json`
- revising slides in response to archetype-aware audit feedback

#### Audit mode

The auditor may run in either mode, but with different scope:

- `Execute Mode audit`: validate rendered output against explicitly supplied metadata only
- `Draft Mode audit`: validate rendered output against generated storyboard, archetypes, and reference-family choices

#### Existing hard-gate policy preserved

Nothing in this spec weakens Inkline’s current hard-gate policy for client-facing decks.

For investor, board, PE, or client-facing decks:

- post-render visual audit remains mandatory
- rendered PDF/PPTX remains the sign-off surface
- skipped or unavailable critical audit dimensions are not treated as a pass

What changes is the richness of audit context, not the existence of the gate.

#### Hard rule

The deterministic renderer contract remains unchanged.

This spec introduces:

- new authoring metadata
- new knowledge resources
- new audit inputs

not a requirement that the renderer itself perform LLM-driven reasoning.

---

## 5. Core Design Principles

1. `Full slide first`
   The system must reason about whole slides before it reasons about slot-level exhibits.

2. `Reference grounded`
   Strong example decks should inform generation through structured retrieval and style extraction.

3. `Storyboard explicit`
   A deck’s narrative, audience, and slide roles must be serialized and auditable.

4. `Authoring and auditing share vocabulary`
   The same slide-archetype and message-role terms must be available to both layers.

5. `Deck-level quality matters`
   A slide is not good enough if it is locally tidy but weak in the deck sequence.

6. `Human-guided but machine-repeatable`
   Analysts and operators should be able to steer the system with reference decks and storyboard guidance, but the resulting process should still be deterministic and inspectable.

---

## 6. Proposed Architecture

### 6.1 New layers

Add four new layers on top of the existing Inkline stack:

```
Input material / user prompt / source docs
    ↓
Storyboard + message planner
    ↓
Reference deck retriever + slide archetype selector
    ↓
Spec authoring layer (full-slide archetypes + slot exhibits)
    ↓
Deterministic renderer (PDF / PPTX)
    ↓
Archetype-aware / storyboard-aware visual auditor
```

### 6.2 New concepts

#### A. Reference Family

A reusable style cluster extracted from one or more benchmark decks.

Examples:

- `ccc_angola_focus_v1`
- `institutional_navy_orange_pe`
- `minimal_fintech_dark_hero`

Each family stores:

- color system
- typography choices
- cover treatment
- chrome conventions
- card/shadow language
- image usage norms
- common slide families
- spatial density norms

#### B. Slide Functional Role

What the slide is doing in the deck.

Examples:

- `cover`
- `thesis`
- `proposition`
- `team`
- `economics`
- `pipeline`
- `market_map`
- `timeline`
- `execution_plan`
- `appendix_ranked_table`

#### C. Full-Slide Archetype

The complete page design pattern chosen for a slide role.

Examples:

- `cover_hero_photo_left_text_block`
- `numbered_horizontal_proposition_rail`
- `executive_bio_cards_centered`
- `firepower_two_zone_summary`
- `banker_vertical_process_spine`
- `appendix_ranked_table_card`

Each archetype includes:

- functional role(s)
- content schema
- layout anatomy
- visual hierarchy rules
- benchmark examples
- allowed slot types
- anti-patterns

#### D. Storyboard Contract

A machine-readable representation of deck-level intent.

Includes:

- audience
- objective
- deck thesis
- tonal register
- slide sequence
- per-slide key message
- per-slide functional role
- required evidence type

### 6.3 Taxonomy normalization

This spec adds one new semantic layer, but it must not duplicate renderer abstractions.

| Concept | Existing / New | Purpose | Renderer-facing? |
|---|---|---|---|
| `slide role` | New | What job the slide performs in the deck | No |
| `full-slide archetype` | New | Semantic full-page design pattern selected during authoring and audit | No |
| `layout` | Existing | Inkline slide/layout family such as `three_card`, `timeline`, `chart_caption` | Yes |
| `template` | Existing | Theme / deck-level design family / packaged template | Indirect |
| `MCP archetype` | Existing | Current archetype catalog object from playbooks/template catalog | No |
| `freeform` | Existing | Escape hatch for arbitrary composed slides | Yes |
| `reference family` | New | Benchmark style cluster extracted from example decks | No |

#### Normalization rule

A `full-slide archetype` is a semantic authoring/audit object that must compile down to one of:

- an existing layout
- an existing template + layout combination
- a `freeform` manifest
- a future renderer primitive explicitly added later

It is **not** a second renderer object model.

#### Compiler ownership rule

Every `full-slide archetype` must compile through a single intelligence-layer compiler table.

That compiler table owns:

- mapping from `full-slide archetype` → `layout`
- mapping from `full-slide archetype` → `template + layout`
- mapping from `full-slide archetype` → `freeform manifest`

The renderer must never interpret `full-slide archetype` directly.

#### Compiled manifest contract

The compiler output is a versioned manifest passed to the existing renderer.

Minimum contract:

```yaml
schema_name: compiled_slide_manifest
schema_version: 1
slide_id: s04_team
source_archetype: executive_bio_cards_centered
compile_target:
  kind: freeform   # one of: layout | template_layout | freeform
  layout_id: freeform
  template_id: null
render_payload:
  slide_type: freeform
  data: {...}
parity_requirements:
  pdf_visual_parity: required
  pptx_visual_parity: required
  pptx_native_editability: required
```

Rules:

- the compiler must emit only renderer-native constructs
- `render_payload` is the sole renderer input
- parity requirements are test assertions, not hints
- for institutional/client-facing decks, compiled manifests must preserve native editable PPTX objects except where image assets are intentional

#### PPTX parity exception model

Allowed exception classes:

- source logos and raster photos
- operator-approved reused map/image slides
- benchmark-derived background textures

Rules:

- exception classes must be explicitly declared in the compiled manifest
- undeclared fallback-to-image behavior is a hard failure
- if a slide uses declared image exceptions, audit must record `pptx_editability_exceptions`
- client-facing sign-off may still pass if exceptions are declared, intentional, and limited to non-editable asset classes rather than whole-slide flattening

#### Example

`executive_bio_cards_centered`

may compile to:

- `layout=freeform` with centered circular portrait cards in Typst/PPTX
- or to a future native `team_grid_centered` layout if the renderer later adds it

The authoring and audit layers speak in `full-slide archetypes`; the renderer consumes compiled layout manifests.

---

## 7. Reference Deck Ingestion System

### 7.1 Purpose

Convert high-quality example decks into reusable, queryable design knowledge.

### 7.2 Inputs

- `PPTX`
- optionally paired notes from the operator

For the implementation MVP, `PPTX` is the only supported ingestion source.

`PDF` support is a later-phase extension and must not be treated as part of the initial implementation contract.

### 7.3 Extraction outputs

For each ingested deck:

1. `Deck metadata`
   - title
   - source / client context
   - deck type
   - sector / audience tags

2. `Style tokens`
   - colors
   - fonts
   - logo placement
   - footer/header conventions
   - shadow/radius treatments

3. `Slide-level classification`
   - functional role
   - archetype candidate
   - information type
   - density class
   - hero zone placement

4. `Element map`
   - text blocks
   - images
   - major cards
   - chart/table zones
   - connectors / arrows / rails / timelines

5. `Benchmark exemplar set`
   For each slide, save:
   - preview image
   - normalized geometry
   - extracted text structure
   - inferred archetype label

### 7.3a Extraction method contract

The implementation MVP defines one normative extractor:

#### PPTX extractor

Primary source for:

- shape geometry
- text box boundaries
- font families / sizes
- fill colors
- image placement
- connector and line primitives
- slide notes where available

#### PDF extractor

Deferred.

PDF ingestion may be added in a later phase as an explicitly lower-confidence fallback, but it is not part of the MVP acceptance contract.

#### Normalized geometry

Normalized geometry means all major element bounding boxes are represented in slide-relative coordinates:

- `x`, `y`, `w`, `h` as values in `[0,1]`
- plus element type and reading order

This allows reference slides from different page sizes to be compared structurally.

#### Extracted text structure

This includes:

- title candidate
- subtitle candidate
- body blocks
- table-like blocks
- caption/footer blocks

Each block should store:

- raw text
- inferred hierarchy level
- source confidence

### 7.4 Operator-in-the-loop

This ingestion system must support manual curation.

Required workflows:

- relabel slide role
- relabel archetype
- mark “strong exemplar”
- mark “do not imitate”
- write short notes such as:
  - “good spacing, weak copy”
  - “excellent people slide”
  - “good card system”

#### Curation surface and persistence

MVP operator curation is file-first with CLI support.

Required surface:

- CLI command to initialize curation files for an ingested reference family
- CLI command to validate and persist curation updates
- local manifest files under the reference-family directory

Minimum persistence files:

- `reference_family_manifest.json`
- `reference_slide_manifest.json`
- optional `curation_overrides.yaml`

`curation_overrides.yaml` minimum shape:

```yaml
reference_family_id: ccc_angola_focus_v1
slides:
  - reference_slide_id: ccc_angola_focus_v1_s04
    role_override: team
    archetype_override: executive_bio_cards_centered
    exemplar_strength: strong
    imitate: true
    notes:
      - excellent people slide
```

Conflict/update rules:

- curator overrides take precedence over auto-inferred labels
- all override application must be logged in the family manifest
- deleting an override reverts to the latest inferred value on re-ingest
- packaged resources are immutable; curation occurs only in local catalog space

### 7.5 Storage

New local store:

- `reference_families/`
- `reference_slides/`
- `archetype_exemplars/`

Suggested paths:

- `src/inkline/intelligence/reference_catalog/` for package defaults
- `~/.config/inkline/reference_catalog/` for private/operator-curated material

### 7.6 Governance and provenance

Every ingested reference deck or slide must carry:

- `source_id`
- `source_path` or source URI
- `license_classification`
  - `public_reusable`
  - `public_reference_only`
  - `private_internal`
  - `client_confidential`
- `ingestion_method`
  - `pptx_native`
  - `pdf_approximate`
- `confidence_score`
- `ingested_at`
- `version`
- `curated_by`

#### Public/private rule

The public Inkline repo must never ship:

- proprietary client decks
- extracted private slide previews
- confidential benchmark assets

Public package data may only include:

- openly reusable benchmark examples
- archetype metadata synthesized from them
- sanitized, non-proprietary manifests

Private and confidential assets must live under:

- `~/.config/inkline/reference_catalog/`

#### Enforcement rule

The ingest/package flow must enforce classification:

- `client_confidential` and `private_internal` assets may only be written to local catalog paths
- package-build commands must refuse to include local confidential manifests or previews
- if classification is missing, ingest fails closed
- if a manifest marked `public_reusable` references a local confidential preview path, validation fails

#### Precedence rule

When the same `reference_family` exists in both packaged and local stores:

1. local curated version wins
2. packaged version remains available as fallback

#### Versioning rule

All resource families introduced by this spec must carry:

- `schema_version`
- `resource_version`

to support migration.

---

## 8. Full-Slide Archetype MCP

### 8.1 Why a new MCP layer is needed

Current MCP resources are strong for:

- playbooks
- charts
- slide layouts
- anti-patterns
- typography

But they do not yet express enough about full-page functional designs.

### 8.2 New resource families

Add:

- `inkline://slide_roles`
- `inkline://slide_roles/<role>`
- `inkline://archetypes/full_slide`
- `inkline://archetypes/full_slide/<archetype>`
- `inkline://reference_families`
- `inkline://reference_families/<family>`
- `inkline://reference_slides/<id>`
- `inkline://storyboard_rules`

### 8.3 Archetype schema

Each `full_slide` archetype should expose:

```yaml
id: executive_bio_cards_centered
functional_roles: [team, people]
deck_types: [investor, consulting, board]
content_schema:
  required:
    - people[]
  optional:
    - subheadline
    - footer_note
visual_intent:
  hero: centered_portraits
  supporting: role_title_text
  tone: institutional_human
layout_rules:
  columns: 4
  portrait_style: circular
  alignment: centered
  footer_strip: supported
slot_types:
  - headshot
  - name
  - role
  - descriptor
benchmark_refs:
  - ref_family: ccc_angola_focus_v1
    slide_id: ccc_angola_focus_v1_s04
anti_patterns:
  - equal_size_boxes_with_top_aligned_photos
  - excessive_body_copy
audit_checks:
  - portraits centered and same diameter
  - role styling subordinate to name
  - footer note spans width and is visually distinct
```

### 8.4 First archetype set

Initial required set for institutional decks:

- `cover_hero_photo_left_text_block`
- `cover_dark_title_page`
- `thesis_three_pillar_cards`
- `numbered_horizontal_proposition_rail`
- `executive_bio_cards_centered`
- `firepower_two_zone_summary`
- `three_bucket_opportunity_map`
- `pipeline_named_table`
- `market_map_with_side_panels`
- `six_card_atypical_structures`
- `reverse_roadshow_three_stage_programme`
- `visibility_three_phase_comms`
- `banker_vertical_process_spine`
- `execution_plan_stepped_programme`
- `appendix_divider_dark`
- `appendix_ranked_table_card`
- `appendix_stakeholder_card_table`

---

## 9. Storyboard + Key Message Contract

### 9.1 Problem

The current pipeline can generate slides without a sufficiently explicit description of what the deck is trying to accomplish at deck level.

That makes audit weak because the auditor can only ask:

- “does this slide look okay?”

instead of:

- “does this slide deliver the intended message in the intended place in the story?”

### 9.2 Required output from authoring layer

Before final slide generation, the authoring layer must output a `storyboard.json`.

### 9.3 Storyboard schema

```yaml
deck:
  title: Building a Major Angola Upstream Platform
  audience: 7GI principals
  objective: secure buy-in for Angola entry strategy and reverse roadshow
  thesis: Angola is a platform-entry market accessible through Cliveden’s network and structuring edge
  tone: institutional_confident
  reference_family: ccc_angola_focus_v1

slides:
  - index: 1
    role: cover
    key_message: 7GI can build a major Angola upstream platform with the right local access and sequencing
    evidence_type: hero_visual
    archetype: cover_hero_photo_left_text_block

  - index: 2
    role: thesis
    key_message: Angola should be approached as a platform-entry market, not a one-asset trade
    evidence_type: structured_argument
    archetype: thesis_three_pillar_cards

  - index: 3
    role: proposition
    key_message: Cliveden’s differentiated value is access, structuring, and execution
    evidence_type: capability_system
    archetype: numbered_horizontal_proposition_rail
```

### 9.4 Enforcement

The renderer need not use this directly, but the audit layer must.

The system should reject or warn if:

- storyboard missing
- key messages absent
- archetype absent on slides requiring full-slide selection
- role/archetype mismatch

### 9.5 Bridge to current Inkline spec formats

The storyboard is a parallel metadata artifact during authoring, but it must compile into today’s spec formats.

#### Markdown path

Recommended front-matter embedding:

```yaml
storyboard:
  deck:
    objective: secure buy-in for Angola entry strategy
    thesis: Angola is a platform-entry market
    reference_family: ccc_angola_focus_v1
  slides:
    s1:
      role: cover
      archetype: cover_hero_photo_left_text_block
      key_message: 7GI can build a major Angola upstream platform
```

Per-section directive bridge:

```markdown
## Building a Major Angola Upstream Platform
<!-- _layout: freeform
_slide_role: cover
_archetype: cover_hero_photo_left_text_block
_key_message: 7GI can build a major Angola upstream platform
-->
```

#### JSON/YAML fixture path

Each slide object may embed:

```yaml
slide_type: freeform
storyboard:
  role: cover
  archetype: cover_hero_photo_left_text_block
  key_message: 7GI can build a major Angola upstream platform
```

#### In-memory slide model contract

At runtime, each slide object should support these optional fields:

```yaml
slide_id: s01_cover
slide_type: freeform
data: {...}
storyboard:
  role: cover
  archetype: cover_hero_photo_left_text_block
  key_message: 7GI can build a major Angola upstream platform
  reference_family: ccc_angola_focus_v1
trace:
  authoring_trace_ref: artifacts/.../authoring_trace.json
```

Rules:

- unknown metadata is preserved and round-tripped where possible
- Execute Mode ignores unsupported metadata during render
- Draft Mode may warn on malformed metadata
- audit consumes this metadata if present

#### Stable IDs

Every authored slide must get a stable `slide_id`, separate from mutable slide index.

Reason:

- indices may change during revision
- audit findings must still map back to the same conceptual slide

Suggested pattern:

- `s01_cover`
- `s03_proposition`
- `app_a_ranked_opportunities`

#### Manual override rule

If a user explicitly sets:

- `_layout`
- `_archetype`
- `_slide_role`

those explicit fields override upstream inference.

### 9.6 Artifact ownership

Canonical artifact ownership:

- `storyboard.json` — authoring artifact
- `authoring_trace.json` — authoring artifact
- slide-embedded `storyboard` blocks — runtime metadata bridge
- audit JSON — audit artifact

Versioning:

- all authoring artifacts must declare `schema_version`
- all audit artifacts that consume them must record the schema versions seen

#### Canonical schema set

The following artifacts are versioned contracts, not ad hoc JSON blobs:

- `storyboard.json`
- `authoring_trace.json`
- `reference_family_manifest.json`
- `reference_slide_manifest.json`
- audit JSON / deck verdict JSON
- packaged MCP archetype manifests

Rules:

1. each artifact declares `schema_name` and `schema_version`
2. minor-version additions must be backward-compatible
3. major-version changes require explicit upgrader logic or hard failure
4. audit artifacts must record the exact upstream schema versions consumed

#### Minimum required fields

`storyboard.json`

```yaml
schema_name: storyboard
schema_version: 1
deck:
  title: ...
  audience: ...
  objective: ...
  thesis: ...
  reference_family: ...
slides:
  - slide_id: s01_cover
    index: 1
    role: cover
    archetype: cover_hero_photo_left_text_block
    key_message: ...
```

`authoring_trace.json`

```yaml
schema_name: authoring_trace
schema_version: 1
run_id: ...
deck_ref: ...
slides:
  - slide_id: s01_cover
    chosen_archetype: ...
    candidate_archetypes:
      - id: ...
        score: 0.0
    fallback_used: false
    resolved_metadata:
      role: cover
      reference_family: ...
```

`reference_family_manifest.json`

```yaml
schema_name: reference_family_manifest
schema_version: 1
reference_family_id: ...
source_id: ...
license_classification: ...
ingestion_method: pptx_native
style_tokens: {...}
slides:
  - reference_slide_id: ...
    role: ...
    archetype_candidate: ...
    preview_path: ...
```

`reference_slide_manifest.json`

```yaml
schema_name: reference_slide_manifest
schema_version: 1
reference_slide_id: ...
reference_family_id: ...
source_slide_index: 1
normalized_geometry: [...]
text_blocks: [...]
confidence_score: 0.0
```

`deck_audit.json`

```yaml
schema_name: deck_audit
schema_version: 1
deck_verdict: pass_with_warnings
slides_failed_hard_checks: []
slides_requiring_human_signoff: []
dimensions_not_evaluated: []
warning_budget_used: 0
slides: [...]
```

#### Metadata authority and precedence

There must be one conflict-resolution order across all write paths.

For slide-level metadata, precedence is:

1. explicit user override directives in source spec
2. explicit slide object fields in JSON/YAML fixtures
3. slide entry in embedded `storyboard` front matter
4. generated `storyboard.json`
5. inferred defaults from authoring retrieval

For reference families, precedence is:

1. explicit user-selected `reference_family`
2. local curated catalog entry
3. packaged fallback entry

Conflict policy:

- if higher-precedence and lower-precedence values disagree, the higher-precedence value wins
- the losing value must be preserved in `authoring_trace.json`
- malformed higher-precedence metadata is a hard validation error, not silent fallback
- audit must consume the resolved post-merge metadata, not raw competing sources

Validation policy:

- Draft Mode may repair only missing optional metadata
- Draft Mode may not silently rewrite explicit user overrides
- Execute Mode ignores unsupported metadata fields during render but must preserve them on round-trip where possible

#### Single validation boundary

There must be one canonical metadata validation and merge stage before render/audit handoff.

Owning component:

- `storyboard resolver` in the intelligence/authoring layer

Responsibilities:

- load all metadata sources
- apply precedence
- validate schemas
- emit resolved slide metadata
- fail fast on malformed higher-precedence data

Post-resolution rules:

- renderer consumes only resolved metadata embedded in slide specs or compiled manifests
- auditor consumes the same resolved metadata, plus rendered artifacts
- downstream components may report errors on missing required runtime fields, but may not re-merge or reinterpret metadata precedence

---

## 10. Authoring Layer Changes

### 10.1 New generation sequence

Current:

- source content → slide specs

New:

- source content → storyboard
- storyboard → archetype retrieval
- archetype retrieval → slide specs

### 10.2 New authoring responsibilities

The authoring layer must:

1. infer deck-level thesis and audience
2. draft slide sequence and key messages
3. assign functional role per slide
4. retrieve candidate full-slide archetypes
5. choose one archetype with justification
6. instantiate the archetype with content
7. only then fill slot-level exhibits and details

### 10.3 Retrieval strategy

For each slide, retrieve:

- `top_k` matching archetypes by role + content schema
- `top_k` benchmark reference slides from chosen reference family

Ranking features:

- slide role match
- content schema match
- density match
- benchmark family match
- deck type match
- audience match

### 10.4 Explainability

Save `authoring_trace.json`:

- storyboard
- candidate archetypes considered
- chosen archetype
- rejected candidates
- reason for selection

This is essential for auditing and debugging.

### 10.5 Retrieval substrate and determinism

The retrieval layer may be nondeterministic upstream, but it must be reproducible enough for debugging.

Required contract:

- all retrieval results include similarity scores
- tie-breaking is deterministic by stable key
- top-k results are cached per authoring run
- `authoring_trace.json` stores:
  - candidate set
  - scores
  - chosen item

#### MVP retrieval strategy

Phase 1 implementation may avoid embeddings and use metadata filtering + heuristic ranking only:

- role match
- schema match
- deck type match
- benchmark family match

Embedding-based retrieval is a later optimization, not a requirement for the first implementation.

#### No-match behavior

If no archetype exceeds threshold:

- fall back to an approved baseline layout family
- record the fallback in `authoring_trace.json`
- mark the audit context as `fallback_used=true`

### 10.6 Handoff points

The intended runtime handoff sequence is:

1. `DesignAdvisor` or equivalent authoring flow produces:
   - `storyboard.json`
   - slide specs with embedded storyboard metadata
   - `authoring_trace.json`
2. renderer receives slide specs only
3. renderer ignores semantic metadata it does not need
4. audit receives:
   - rendered artifact
   - slide specs
   - embedded storyboard metadata
   - optional `authoring_trace.json`

Bridge / Draft Mode may transport all three authoring artifacts together, but Execute Mode need only receive the slide specs.

---

## 11. Auditor Redesign

### 11.1 Current weakness

The visual auditor today mainly checks:

- clipping / fit
- generic quality issues
- rubric-level design standards

It does not robustly check:

- whether the slide matched the intended full-slide archetype
- whether the deck hit the intended message sequence
- whether the style stayed faithful to the reference family

### 11.2 New audit dimensions

For each slide, audit across four dimensions:

1. `visual_quality`
   - fit
   - spacing
   - hierarchy
   - clutter
   - alignment

2. `archetype_compliance`
   - did the slide actually express the selected archetype?
   - were the key geometry and emphasis rules respected?

3. `reference_family_alignment`
   - is the slide visually consistent with the intended benchmark family?
   - title scale
   - chrome
   - card language
   - imagery handling

4. `message_delivery`
   - does the slide communicate the intended key message?
   - does it do so within the expected story role?

### 11.2a Hard vs soft audit checks

The auditor must separate machine-scoreable checks from advisory judgments.

#### Hard checks

These can be enforced or scored mechanically:

- clipping / overflow
- whitespace imbalance
- title scale minimums
- card count / card alignment
- archetype geometry checks where the archetype explicitly defines measurable structure
- footer/header presence
- benchmark-family token checks where style tokens are explicit

#### Soft checks

These are reviewer-assistive unless backed by stronger evidence:

- message delivery
- editorial force
- family resemblance
- rhetorical sharpness

Soft checks should not replace the existing hard-gate client-deck audit policy.

For client-facing decks:

- a deck still fails if hard visual audit requirements fail
- soft checks may escalate a review outcome from `warn` to `needs human sign-off`
- soft checks alone should not silently auto-pass a deck

### 11.3 New audit input contract

The auditor must receive:

- rendered slide images
- storyboard
- chosen archetype per slide
- reference family metadata
- optional benchmark slide previews

### 11.4 New audit output

```json
{
  "slide_index": 4,
  "role": "team",
  "archetype": "executive_bio_cards_centered",
  "verdict": "warn",
  "scores": {
    "visual_quality": 74,
    "archetype_compliance": 62,
    "reference_family_alignment": 68,
    "message_delivery": 85
  },
  "findings": [
    "Portrait treatment and card proportions do not match the centered bio-card benchmark family.",
    "The slide communicates the team correctly, but the page still reads as a generated grid rather than an executive access slide."
  ],
  "required_fixes": [
    "Increase portrait dominance.",
    "Center hierarchy under each portrait.",
    "Convert footer support note into a full-width support strip."
  ]
}
```

### 11.5 Deck-level audit

In addition to slide-level checks:

- are action titles coherent as a storyline?
- do adjacent slides progress logically?
- does the deck over-repeat the same page structure?
- are hero moments placed where the storyboard expects them?

#### Deck verdict semantics

The audit system must emit both:

- per-slide verdicts
- one deck-level verdict

Allowed deck-level verdicts:

- `pass`
- `pass_with_warnings`
- `needs_human_signoff`
- `fail`

Aggregation rules for client-facing decks:

1. any hard-fail slide defect yields deck verdict `fail`
2. any required dimension marked `not_evaluated` yields at least `needs_human_signoff`
3. any slide with unresolved fallback on a critical slide family (`cover`, `thesis`, `process`, `team`, `economics`) yields at least `needs_human_signoff`
4. soft-check warnings alone may not produce `pass` if more than the configured warning budget is exceeded

Minimum evaluated dimensions for client-facing gate:

- `visual_quality` must be evaluated on every slide
- `archetype_compliance` must be evaluated whenever an archetype is declared
- `message_delivery` must be evaluated whenever storyboard metadata is present
- `reference_family_alignment` must be evaluated or explicitly marked advisory when a reference family is declared

Required audit artifact fields:

- `deck_verdict`
- `deck_required_fix_count`
- `slides_failed_hard_checks`
- `slides_requiring_human_signoff`
- `dimensions_not_evaluated`
- `warning_budget_used`

#### Normative aggregation model

Slide-level verdict order:

1. `fail`
2. `needs_human_signoff`
3. `pass_with_warnings`
4. `pass`

Slide verdict rules:

- any hard-check failure => slide verdict `fail`
- no hard failure, but required dimension `not_evaluated` => `needs_human_signoff`
- no hard failure, no required missing dimensions, but advisory warnings exceed slide warning budget => `pass_with_warnings`
- otherwise => `pass`

Deck verdict rules:

- if any slide verdict is `fail`, deck verdict is `fail`
- else if any slide verdict is `needs_human_signoff`, deck verdict is `needs_human_signoff`
- else if aggregate advisory warnings exceed deck warning budget, deck verdict is `pass_with_warnings`
- else deck verdict is `pass`

Partial-evaluation rule:

- advisory-only dimensions may contribute warnings but may not by themselves produce `fail`
- `not_evaluated` on a non-required dimension is recorded but does not escalate verdict
- `not_evaluated` on a required dimension escalates at least to `needs_human_signoff`

#### Default threshold table

Until overridden by archetype- or rubric-specific settings, the MVP uses these defaults:

- title scale minimum: title font box height must be at least `1.25x` median body text box height
- whitespace imbalance: any major content zone margin below `2%` of slide width/height is flagged
- slide warning budget: `2`
- deck warning budget: `8`
- archetype match fallback threshold: `0.60`
- benchmark family advisory threshold: `0.55`

These defaults must live in one versioned settings module so tests and audits share the same values.

### 11.6 Fallback behavior

If the auditor lacks enough metadata to evaluate a dimension:

- it must declare that dimension `not_evaluated`
- it must not silently infer a pass

Examples:

- no storyboard → skip `message_delivery`
- no reference family → skip `reference_family_alignment`
- no archetype → skip `archetype_compliance`

#### Operational compatibility rules

The redesigned audit path must still preserve current production requirements:

- explicit bridge URL override support
- provider trace in audit artifacts
- rendered PPTX audit where applicable
- resilient handling of provider constraints

This spec changes audit semantics, not the operational production contract.

---

## 12. Best-in-Class Slide Template Research Program

### 12.1 Purpose

Build an ongoing benchmark corpus for full-slide design, not just local charts and exhibits.

### 12.2 Sources

Use:

- curated public slide marketplaces
- internal benchmark decks
- operator-identified decks
- existing Inkline template catalog inputs

### 12.3 Curation goals

Collect benchmark slides for:

- consulting
- private equity
- investor relations
- strategy / board
- product / tech

### 12.4 Taxonomy

Each benchmark slide should be tagged by:

- deck type
- functional role
- page gesture
- density class
- brand style
- industry

### 12.5 Integration with existing work

Inkline already has:

- `template_catalog.md`
- `slide_layouts.md`
- `professional_exhibit_design.md`
- `visual_libraries.md`

The new benchmark program should extend them rather than replace them.

Specifically:

- `template_catalog` remains useful for structural archetype recipes
- the new system adds richer full-slide and benchmark-family semantics

### 12.6 MVP restriction

For implementation readiness, the ingestion MVP is narrowed to:

- `PPTX only`
- private/local catalog first
- operator-approved manifests
- no automatic packaged benchmark-family synthesis from PDF-only sources

PDF structural inference is explicitly deferred to a later phase.

---

## 13. Proposed Files and Modules

### New documentation / knowledge assets

- `src/inkline/intelligence/playbooks/full_slide_archetypes.md`
- `src/inkline/intelligence/playbooks/reference_deck_ingestion.md`
- `src/inkline/intelligence/playbooks/storyboard_and_message_design.md`

### New package modules

- `src/inkline/intelligence/reference_catalog.py`
- `src/inkline/intelligence/reference_ingest.py`
- `src/inkline/intelligence/slide_roles.py`
- `src/inkline/intelligence/full_slide_archetypes.py`
- `src/inkline/intelligence/storyboard.py`
- `src/inkline/intelligence/archetype_retriever.py`
- `src/inkline/intelligence/audit_storyboard.py`

### MCP resource updates

- `src/inkline/app/mcp_resources.py`

### Authoring / audit integration

- `src/inkline/intelligence/design_advisor.py`
- `src/inkline/intelligence/overflow_audit.py`
- `src/inkline/intelligence/vishwakarma.py`

---

## 14. Phased Delivery Plan

This spec must not be implemented as one monolithic change.

### Phase 1 — Storyboard metadata MVP

Deliver:

- `storyboard` schema
- markdown / JSON/YAML bridge
- stable slide IDs
- `authoring_trace.json` structure
- legacy-spec compatibility shim for missing storyboard metadata

Hard gate:

- no renderer contract changes
- Execute Mode still renders existing specs unchanged

### Phase 2 — Full-slide archetype vocabulary over current layouts

Deliver:

- `full_slide_archetypes` playbook
- archetype schema
- archetype-to-layout/freeform compilation mapping

Hard gate:

- no benchmark ingestion yet
- archetypes compile to existing renderer abstractions only

### Phase 3 — Reference-family ingestion MVP

Deliver:

- PPTX-first ingestion path
- private local catalog support
- provenance/governance metadata
- manual curation workflow

Hard gate:

- packaged public examples remain sanitized
- private confidential assets never enter repo

### Phase 4 — Archetype-aware audit

Deliver:

- audit input contract with storyboard/archetype/reference metadata
- hard vs soft scoring separation
- `not_evaluated` reporting

Hard gate:

- visual auditor remains usable without the new metadata

### Phase 5 — Retrieval optimization and benchmark expansion

Deliver:

- improved ranking
- optional embeddings
- broader benchmark corpus
- more archetype families

Hard gate:

- retrieval remains explainable and traceable

---

## 15. Acceptance Criteria

Inkline can be considered compliant with this spec when:

1. Given a fixture markdown or JSON/YAML deck with storyboard metadata, Inkline can persist and round-trip:
   - `slide_id`
   - `role`
   - `archetype`
   - `key_message`
2. Given an authored slide tagged `executive_bio_cards_centered`, the authoring layer can compile it into either:
   - an existing layout
   - or `freeform`
   with a recorded rationale.
3. Given a PPTX benchmark deck in local private storage, the ingestion MVP can emit a `reference_family` manifest with:
   - style tokens
   - slide previews
   - normalized geometry
   - provenance fields
4. Given a selected `reference_family`, the audit artifact explicitly reports whether `reference_family_alignment` was:
   - scored
   - advisory only
   - or `not_evaluated`
5. Given no archetype match above threshold, the authoring layer falls back to an approved baseline layout and records that fallback.
6. Given no storyboard, Execute Mode rendering still succeeds without LLM coupling.
7. A “key people” request can retrieve at least 3 candidate full-slide archetypes from MCP metadata, not just slot-level exhibit suggestions.
8. A user can inspect `authoring_trace.json` and see:
   - candidate archetypes considered
   - scores
   - chosen archetype
   - fallback if any
9. Given conflicting metadata across override directives, embedded storyboard metadata, and generated storyboard data, the system resolves values according to the canonical precedence order and records the losing values in `authoring_trace.json`.
10. Given an archetype declaration on a client-facing slide, the audit artifact reports either:
   - a scored `archetype_compliance`
   - or explicit `not_evaluated`
   but never a silent omission.
11. Given a client-facing deck with any hard-fail slide defect, the deck audit verdict is `fail`.
12. Given a client-facing deck with required dimensions not evaluated on one or more slides, the deck audit verdict is at least `needs_human_signoff`.
13. The MVP ingestion implementation accepts `PPTX` and rejects `PDF` as unsupported for initial reference-family creation.
14. All first-phase artifacts expose `schema_name` and `schema_version`, and the audit artifact records the upstream schema versions it consumed.

---

## 16. Risks

1. `Overfitting to one benchmark deck`
   Mitigation: support reference families, not single-deck cloning only.

2. `Token/context explosion`
   Mitigation: summarize reference slides into structured manifests and preview snippets.

3. `Auditor subjectivity`
   Mitigation: tie critique to declared archetype rules and storyboard objectives.

4. `Too many archetypes too early`
   Mitigation: start with the highest-value institutional set.

5. `False precision`
   Mitigation: keep archetype selection explainable and operator-overridable.

---

## 17. Implementation Philosophy

The correct build order is:

1. storyboard metadata
2. archetype library
3. reference ingestion MVP
4. authoring retrieval
5. archetype-aware auditor
6. refinement loops and self-learning

This ordering intentionally matches the phased delivery plan above.

### 17.1 Legacy migration policy

Existing decks, MCP resources, and audit consumers must continue to work during rollout.

Rules:

- legacy specs without storyboard metadata remain valid inputs
- legacy slides receive generated ephemeral `slide_id` values only at runtime unless explicitly persisted by an upgrade command
- existing MCP resources remain unchanged; new full-slide resources are additive
- existing audit consumers may ignore new dimensions, but the new audit artifact format must preserve backward-compatible core fields for one major version
- any breaking migration requires an explicit upgrader and release note

Do **not** begin by simply adding more slide templates to the renderer.

That would solve the wrong problem.

The primary missing capability is not more shapes.
It is better design abstraction and better alignment between:

- benchmark examples
- authoring decisions
- slide structure
- visual audit
- message intent

---

## 18. Final Recommendation

Inkline should move from:

> `playbooks + layouts + renderer + generic audit`

to:

> `reference families + full-slide archetypes + storyboard contract + aligned audit + deterministic renderer`

That is the most credible path to producing decks that feel less defensive, less generic, and more like they were designed by a competent analyst or presentation designer.
