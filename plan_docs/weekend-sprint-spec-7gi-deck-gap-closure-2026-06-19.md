# Weekend Sprint Specification — 7GI Deck Gap Closure

**Date:** 19 June 2026
**Status:** Approved for weekend execution after independent audit
**Scope:** Close the highest-value Inkline gaps exposed while producing the AGEH / 7GI Angola investor deck, with emphasis on native editable PPTX quality, PDF/PPTX parity, rendered-artifact audit, institutional-layout support, and reference-deck style retention.
**Driver:** Real production pain from the `AGEH_7GI_Tuesday_Second_Pass_2026-06-19` deck workflow.
**Primary repo:** `/home/k1mini/inkline`
**Related output context:** `/home/k1mini/disk2/DOCS/TVF/AGEH_Consulting/7GI_Tuesday_Materials_2026-06-18/second_pass/`

---

## 1. Problem Statement

The 7GI deck process showed that Inkline can help produce a visually acceptable PDF, but it is not yet reliable enough as a full institutional deck-production system when the deliverable must also be an editable, sign-off-ready `.pptx`.

The critical failures were not theoretical. They occurred during real deck production:

- The first workable PPTX export path was effectively flattened slide images rather than editable PowerPoint elements.
- After introducing native PowerPoint shapes, text layout diverged materially from the stable PDF/raster output, causing overlap, clipping, and misalignment.
- There is no first-class rendered-PPTX audit loop. We had to render the PPTX through `soffice` and inspect that derived artifact manually.
- Vishwakarma and the institutional critique path currently treat many legitimate consulting/investor patterns as failures because the rubric is over-optimized for low-density infographic decks.
- Reference style inheritance from an existing source deck remains largely manual.
- Bridge routing for vision is not resilient enough: on `18083`, the default provider may be `antigravity_cli`, which is not vision-capable, so visual critique can hang or silently become unreliable.
- Institutional slides that are common in real work, such as pipeline tables, people/headshot slides, stakeholder strips, process bars, and appendix matrices, are not sufficiently represented as first-class layout primitives.

The result is a split system:

- PDF path: visually stronger, but raster-heavy and less editable.
- PPTX path: editable, but not reliable enough out of the box.

This sprint closes that split for the highest-value institutional use cases.

---

## 2. Goals

### Primary goals

1. Deliver a first-class native editable PPTX path that produces usable institutional decks without slide-wide image flattening.
2. Reduce visual divergence between PDF and PPTX outputs, especially for text-heavy institutional slides.
3. Add a formal PPTX render-and-audit loop so editable output is audited on the rendered artifact, not assumed correct from the shape tree.
4. Split critique logic into:
   - hard visual/render defects
   - layout-quality warnings
   - Vishwakarma preference warnings
5. Add or strengthen institutional layout primitives for the exact slide families that were painful on the 7GI deck.
6. Make bridge routing for vision deterministic and vision-safe under the Aria multi-LLM bridge.
7. Add a reference-deck style-extraction workflow sufficient to retain the visual language of an example `.pptx` without full manual recreation.

### Secondary goals

8. Keep the Typst/PDF path stable while improving PPTX.
9. Keep implementation grounded in current local CLI/bridge tooling, not API-key dependencies.
10. Leave behind clear tests, CLI entry points, and acceptance criteria so this work becomes maintainable, not a one-off patch pile.

---

## 3. Non-Goals

- Full generic “convert any PowerPoint to an Inkline brand/theme” intelligence. This sprint only targets a practical first version of style extraction and reuse.
- Perfect semantic parity for every existing slide type across Typst, PPTX, Google Slides, and HTML.
- Elimination of dense tables from institutional decks. The goal is better support and more honest auditing, not forcing all slides into infographic sparsity.
- Replacing the existing Vishwakarma philosophy entirely. This sprint narrows it and separates it from defect detection.
- Building a complete WYSIWYG PowerPoint editor inside Inkline.
- Re-architecting the entire bridge stack. Only the parts affecting Inkline reliability are in scope.

---

## 4. Design Principles

1. **Rendered artifact is truth.** For PPTX sign-off, the rendered PowerPoint/LibreOffice output is authoritative, not the slide object model.
2. **Editable by default when PPTX is requested.** A PPTX output containing one full-slide image is a fallback, not a successful institutional export.
3. **Hard defects outrank taste.** Overlap, clipping, missing chrome, and broken layout are errors. Vishwakarma ideology belongs in a separate warning layer.
4. **Institutional density is legitimate.** Tables, matrices, bios, and pipeline slides are not anti-patterns by default.
5. **One implementation, multiple audits.** The same spec should support PDF and PPTX, but each backend must be audited through its own rendered artifact.
6. **Reference style should be reusable.** When a client wants a new deck to look like an existing deck, Inkline should have a structured path for extracting and reusing that language.
7. **No hidden fallbacks.** Missing vision capability, unsupported PPTX layouts, and downgraded exports must surface explicitly.

---

## 5. Scope Summary

## Status Table

| ID | Workstream | Priority | Effort | Weekend Scope |
|---|---|---:|---:|---|
| W1 | Native editable PPTX renderer hardening | P1 | M | Narrow to fixture-backed slide families only |
| W2 | PDF/PPTX parity and text-fit system | P1 | M | Narrow to fixture-backed slide families only |
| W3 | Rendered PPTX audit loop | P1 | M | Must do |
| W4 | Vision routing and bridge reliability | P1 | S | Must do |
| W5 | Audit-model split: defects vs ideology | P1 | M | Must do |
| W6 | Institutional layout primitives | P1 | M | Must do for exactly 5 slide families |
| W7 | Reference deck style extraction v1 | P2 | S | Optional stretch only |
| W8 | CLI / docs / regression fixtures | P1 | M | Must do |
| W9 | Full automated style imitation from source PPTX | P3 | XL | Defer |

### Weekend vertical slice

This sprint is now explicitly scoped as a vertical slice around one canonical institutional fixture deck and one sanitized real-deck reproduction, not a broad renderer rewrite.

**In-scope fixture-backed slide families**

1. `cover`
2. `team_grid`
3. `institutional_timeline`
4. `institutional_kpi_cards`
5. `appendix_matrix`

**Out-of-scope for mandatory completion this weekend**

- generalized support for every historical institutional slide archetype
- full pipeline matrix primitive
- full stakeholder-strip family unless needed as a light variant of `appendix_matrix`
- fully automated reference-style cloning

### Canonical fixture and sign-off corpus

The sprint must validate against these exact artifacts:

1. **Canonical synthetic fixture deck**
   - source spec path: `examples/institutional/fixture_deck_7gi_v1/fixture_deck_7gi_v1.yaml`
   - required output count: `10` slides
   - required slide families:
     - cover
     - section divider
     - three-card strategy
     - team grid
     - KPI bridge / capital deployment
     - institutional timeline
     - appendix matrix
     - rendered reference exhibit embed
     - two appendix/support slides
2. **Sanitized real-deck reproduction fixture**
   - source spec path: `examples/institutional/fixture_deck_7gi_v1/fixture_deck_7gi_v1_sanitized_real.yaml`
   - required output count: `5` slides
   - required slide families:
     - cover
     - team grid
     - KPI bridge
     - institutional timeline
     - appendix matrix

No alternative or reduced corpus counts as weekend sign-off.

### Corpus classification matrix

Every slide in both fixtures must be classified explicitly:

| Fixture slide | Family | Weekend rule | Parity gate | Notes |
|---|---|---|---|---|
| synthetic-01 | cover | must be native | yes | ship-blocking |
| synthetic-02 | section_divider | may use existing implementation | no | must render cleanly |
| synthetic-03 | three-card strategy | may use existing implementation | no | allowed to reuse current logic if editable |
| synthetic-04 | team_grid | must be native | yes | ship-blocking |
| synthetic-05 | institutional_kpi_cards | must be native | yes | ship-blocking |
| synthetic-06 | institutional_timeline | must be native | yes | ship-blocking |
| synthetic-07 | appendix_matrix | must be native | yes | ship-blocking |
| synthetic-08 | reference exhibit embed | allowed exempt fallback | no | only `reference_figure_embed` or `map_embed` |
| synthetic-09 | appendix support | may use existing implementation | no | must remain editable where practical |
| synthetic-10 | appendix support | may use existing implementation | no | must remain editable where practical |
| real-01 | cover | must be native | yes | ship-blocking |
| real-02 | team_grid | must be native | yes | ship-blocking |
| real-03 | institutional_kpi_cards | must be native | yes | ship-blocking |
| real-04 | institutional_timeline | must be native | yes | ship-blocking |
| real-05 | appendix_matrix | must be native | yes | ship-blocking |

For all slides marked `may use existing implementation`:

- they must render cleanly
- they are excluded from parity and manual-editability gates
- defects on these slides are warnings unless they break deck-wide rendering or chrome

### Numeric sign-off gates

The sprint is not approved unless all of the following hold on the canonical corpus:

1. `editable_native_ratio >= 0.90` on the synthetic fixture deck.
2. `editable_native_ratio >= 0.85` on the sanitized real-deck reproduction.
3. `ship_blocking_render_defects = 0` on both rendered PPTX audit outputs.
4. `allowed_image_fallback_slides <= 1` and only for a declared `reference_figure_embed` or `map_embed` exemption.
5. `max_text_shrink_pct <= 18` for headings/body boxes and `<= 22` for matrix/table cells.
6. `parity_diff_score <= 0.12` on the five in-scope slide families, measured as normalized rendered-image delta between Typst PDF and rendered PPTX PDF using the same page extraction pipeline.
7. `audit_provider = codex_cli`; non-vision audit runs do not count.
8. `manual_editability_pass = true` for at least one representative slide from each in-scope family.

### Metric definitions

| Metric | Formula | Producer | JSON field | Enforced at | Evidence artifact |
|---|---|---|---|---|---|
| `editable_native_ratio` | `native_editable_slide_count / total_slide_count` | PPTX export metadata builder | `editable_native_ratio` | export step and final sign-off | `export_metadata.json` |
| `ship_blocking_render_defects` | count of findings with class `render_defect` and severity `ship_blocking` | rendered PPTX audit | `render_defect_counts.ship_blocking` | audit step | `audit.json` |
| `parity_diff_score` | normalized mean visual delta across in-scope parity slides | parity diff harness | `parity_diff_score` | local-system parity test | `parity_report.json` |
| `max_text_shrink_pct` | largest percentage reduction from requested font size to emitted size on targeted text classes | PPTX export instrumentation | `max_text_shrink_pct` | export step and regression check | `export_metadata.json` |
| `manual_editability_pass` | boolean pass only if one representative slide per in-scope family is edited and saved without layout break | manual QA checklist | `manual_editability_pass` | final human sign-off | `manual_qa_checklist.md` |

### Minimum fixture schemas and asset policy

The fixture specs must use stable placeholder-safe schemas so engineers do not invent the shape of the test deck during implementation.

- `cover`
  - fields: `title`, `subtitle`, `logo_path`, `confidentiality_label`
- `team_grid`
  - fields: `people[]` with `name`, `role`, `headshot_path`, `proof_point`
- `institutional_kpi_cards`
  - fields: `section_title`, `assumptions[]`, `kpis[]`, `outcomes[]`
- `institutional_timeline`
  - fields: `phases[]` with `title`, `date_range`, `body_lines[]`
- `appendix_matrix`
  - fields: `title`, `columns[]`, `rows[]`, `footnote`

Placeholder asset policy:

- headshots must come from sanitized local placeholder assets committed under `examples/institutional/fixture_deck_7gi_v1/assets/`
- reference exhibits must be neutralized or synthetic unless explicitly marked as exempt embeds
- no external network fetches are allowed during fixture generation

---

## 6. Workstream Breakdown

## W1. Native Editable PPTX Renderer Hardening

### Problem

Inkline’s current PPTX path is not yet a trustworthy institutional export path. It either falls back too aggressively or requires one-off slide composition logic outside the normal engine.

### Target outcome

- A standard Inkline PPTX pipeline that emits native text boxes, tables, shapes, connectors, and pictures for common institutional slide families.
- Slide-wide raster fallback only when explicitly unavoidable, and always flagged.

### Implementation targets

**Primary modules**
- `src/inkline/pptx/__init__.py`
- `src/inkline/pptx/builder.py`
- `src/inkline/authoring/backend_coverage.py`
- `tests/pptx/`

### Required changes

1. Introduce a formal “editable institutional mode” in the PPTX builder.
2. Expand native support for the following slide families:
   - cover
   - people/headshot grid (`team_grid`)
   - process/timeline cards (`institutional_timeline`)
   - appendix tables (`appendix_matrix`)
   - KPI + callout hybrid slides (`institutional_kpi_cards`)
3. Add explicit export metadata on each slide:
   - `native_editable: true|false`
   - `fallback_reason`
   - `layout_downgrade`
4. Make fallback to slide-wide image export explicit and opt-in, not silent.
5. Add grouped shape helpers and reusable card constructors in the PPTX builder so institutional slides are not manually reassembled per deck.

### Acceptance criteria

- No slide-wide image fallback on the five in-scope slide families.
- At most one full-slide or major-region image fallback is permitted across the `10`-slide synthetic fixture deck, and only if tagged `reference_figure_embed` or `map_embed`.
- PPTX export report clearly lists native/fallback status per slide.
- Generated PPTX is editable in PowerPoint/LibreOffice with separate objects for text, image, and core containers on every in-scope slide family.

---

## W2. PDF/PPTX Parity and Text-Fit System

### Problem

The same slide design can look acceptable in PDF/Typst and fail in PPTX because text reflows differently. This is the biggest practical reliability gap.

### Target outcome

- Shared layout-safe text rules for PPTX generation.
- Predictable fitting behavior for headings, body text, callout bars, and table cells.

### Implementation targets

**Primary modules**
- `src/inkline/pptx/builder.py`
- `src/inkline/typst/slide_renderer.py`
- `src/inkline/intelligence/overflow_audit.py`
- `tests/pptx/`

### Required changes

1. Add a text-fit utility layer for PPTX:
   - heading fit
   - body fit
   - table cell fit
   - callout-strip fit
2. Add configurable text policies:
   - `fit_text`
   - `shrink_to_fit`
   - `fixed_size`
   - `truncate_with_warning`
3. Add spacing presets for institutional content:
   - card title spacing
   - body bullet spacing
   - table row padding
   - footer strip padding
4. Add parity tests for representative slides:
   - compare rendered PPTX PDF images vs baseline rendered PDF images
   - use tolerance-based diff checks rather than exact pixel identity
5. Introduce explicit “fragile slide” markers in regression fixtures for layouts known to stress reflow.

### Acceptance criteria

- `0` ship-blocking overlap/clipping findings on rendered PPTX for both canonical fixtures.
- PPTX text-fit choices are deterministic and test-covered.
- `max_text_shrink_pct <= 18` for headings/body and `<= 22` for matrix/table cells.
- `parity_diff_score <= 0.12` is documented and enforced on the five in-scope families.

---

## W3. Rendered PPTX Audit Loop

### Problem

Editable PPTX output can look wrong even when the object model seems valid. Inkline currently does not treat rendered PPTX audit as a first-class path.

### Target outcome

- One command to export PPTX, render it, and audit the rendered artifact.

### Implementation targets

**Primary modules**
- `src/inkline/pptx/auditor.py`
- `src/inkline/intelligence/vishwakarma.py`
- `src/inkline/app/cli.py`
- `tests/pptx/`

### Required changes

1. Add CLI and library support for:
   - `inkline audit-pptx <file.pptx>`
   - render via `soffice --headless --convert-to pdf`
   - extract pages
   - route to critique
2. Standardize the temporary render workspace and cleanup behavior.
3. Save audit JSON next to the PPTX when requested.
5. Make audit output identify:
   - rendered-PPTX failures
   - PDF-only passes
   - divergence class

### Acceptance criteria

- PPTX audit can be invoked with one command.
- Audit artifacts are reproducible and saved predictably.
- Rendered-PPTX audit is documented as the required sign-off path for institutional editable decks.
- Default local contract is `LibreOffice 25.x` on `k1mini` via `soffice --headless`, with:
  - per-render timeout: `90s`
  - one retry on transient conversion failure
  - explicit warning if substituted fonts are detected in stdout/stderr or export logs
  - artifact retention of rendered PDF plus page images for failed audits

---

## W4. Vision Routing and Bridge Reliability

### Problem

On `18083`, the bridge may default to `antigravity_cli`, which is not vision-capable. Inkline should not hang or silently degrade in that situation.

### Target outcome

- Deterministic vision-capable provider selection for Inkline audits.
- Clear failure messages when no vision backend is available.

### Implementation targets

**Primary modules**
- `src/inkline/intelligence/vishwakarma.py`
- `src/inkline/intelligence/overflow_audit.py`
- `src/inkline/typst/chart_auditor.py`
- `src/inkline/intelligence/claude_code.py`

### Required changes

1. Add explicit provider override support in Inkline audit calls:
   - prefer `codex_cli` for vision on the Aria bridge
2. Add a preflight health probe that checks:
   - bridge reachable
   - selected provider supports vision
   - fallback chain exists
3. Fail fast with structured error if:
   - provider is non-vision
   - provider times out
   - no rendered audit was completed
4. Surface audit incompleteness as hard failure for sign-off commands.
5. Update documentation and CLI logs so the operator sees the provider path clearly.

### Acceptance criteria

- No hanging audit runs caused by non-vision default providers.
- Audit logs show selected provider and fallback behavior.
- “Audit incomplete” can no longer be mistaken for pass.
- Sign-off commands fail hard if the selected provider is not vision-capable.

---

## W5. Audit-Model Split: Hard Defects vs Ideology

### Problem

The current critique path conflates:

- hard visual/render failures
- legitimate but denser institutional slides
- Vishwakarma aesthetic preference

This makes the audit less credible for investor/consulting decks.

### Target outcome

- Separate scoring lanes so a deck can fail for clipping without being mixed up with “too table-like” preferences, and vice versa.

### Implementation targets

**Primary modules**
- `src/inkline/intelligence/vishwakarma.py`
- `src/inkline/intelligence/overflow_audit.py`
- `src/inkline/intelligence/design_advisor.py`
- `tests/intelligence/`

### Required changes

1. Split critique output into three classes:
   - `render_defect`
   - `layout_quality`
   - `style_preference`
2. Add separate deck-level rollups:
   - `ship_blocking`
   - `quality_warnings`
   - `vishwakarma_warnings`
3. Add a new `institutional_consulting` rubric tuned for:
   - dense tables where justified
   - people slides
   - stakeholder maps
   - appendix pages
   - maps / reused reference exhibits
4. Preserve the current stricter infographic-first rubric for decks that need it.
5. Update audit JSON schema and docs.

### Acceptance criteria

- A legitimate appendix table can receive a style warning without failing as a render defect.
- Ship-blocking issues are clearly separable from design preference warnings.
- New rubric is selectable from CLI and library paths.

---

## W6. Institutional Layout Primitives

### Problem

Institutional slide families were painful because Inkline lacks enough strong native primitives for them.

### Target outcome

- First-class reusable layouts for high-frequency investor/consulting slides.

### Implementation targets

**Primary modules**
- `src/inkline/pptx/builder.py`
- `src/inkline/typst/slide_renderer.py`
- `src/inkline/authoring/backend_coverage.py`
- `examples/`
- `tests/authoring/`

### Must-have primitive families this weekend

1. `cover`
   - title/subtitle/logo/confidential chrome
2. `team_grid`
   - headshot
   - name
   - role
   - short proof point
   - optional advisor strip
3. `institutional_timeline`
   - central or horizontal spine
   - alternating cards
   - footnote workstream bar
4. `institutional_kpi_cards`
   - section title
   - assumption bullets
   - KPI bridge blocks
   - outcomes list
5. `appendix_matrix`
   - dense but legible table/matrix with institutional typography and padding

### Nice-to-have if time permits

6. `section_divider`
   - full-bleed brand color
   - rule/chrome treatment
   - title/subtitle block
7. `stakeholder_strip`
   - left label panel
   - right description block
   - repeated vertical list
8. `reference_map_slide`
   - native chrome + embedded reference figure
9. `pipeline_matrix`
   - 5-6 column institutional comparison alternative

### Acceptance criteria

- Each primitive has both Typst and PPTX implementation or an explicit documented downgrade path.
- Each primitive has at least one example and one regression test.
- Only the five must-have families above are ship-blocking for this sprint.

---

## W7. Reference Deck Style Extraction v1

### Problem

We had to manually imitate the `CCC_Angola Focus` deck. Inkline needs a practical way to extract and reuse style from a source deck.

### Target outcome

- A v1 reference-style capture workflow for:
   - colors
   - fonts
   - logo usage
   - cover/divider chrome
   - footer conventions
   - preferred slide archetypes

### Implementation targets

**Primary modules**
- new: `src/inkline/intelligence/reference_deck.py`
- `src/inkline/app/cli.py`
- `src/inkline/intelligence/visual_direction.py`
- `~/.config/inkline/brands/` support docs

### Required changes

1. Add `inkline extract-style <deck.pptx>` command.
2. Output a style report and optional starter brand pack:
   - colors
   - font guesses
   - logo placement
   - divider/cover signatures
3. Allow spec or render invocation to point at a reference-style file.
4. Add minimal heuristics only; do not attempt full semantic slide understanding this weekend.

### Weekend cutoff

- Stretch only. This workstream is not ship-blocking for weekend approval.
- If attempted, deliver only:
  - a style token report
  - starter brand/config output
  - parser notes describing priority of theme tokens vs direct formatting
- Defer true content-aware layout imitation.

### Acceptance criteria

- If implemented this weekend, the command must extract at minimum:
  - primary and secondary colors
  - heading/body font guesses
  - logo position guess
  - divider and footer chrome descriptors
- Parsing approach must be documented, including whether it inspects `.pptx` theme XML, slide masters, or direct shape formatting.

---

## W8. CLI, Docs, Regression Fixtures

### Problem

Even if the code improves, the workflow remains fragile without standard commands and fixtures.

### Implementation targets

- `src/inkline/app/cli.py`
- `README.md`
- `docs/`
- `examples/`
- `tests/pptx/fixtures/` or equivalent

### Required changes

1. Add documented commands for:
   - render PDF
   - render editable PPTX
   - audit PDF
   - audit rendered PPTX
2. Add a “7GI-style institutional deck” example using placeholder-safe assets.
3. Add regression fixtures for:
   - cover slide
   - team grid
   - process/timeline
   - KPI bridge
   - appendix matrix
4. Document bridge routing expectations for vision.

If `W7` is attempted after required gates pass, add its command/docs as a stretch addendum only.

### Acceptance criteria

- A new developer can reproduce the full workflow from docs.
- Core institutional fixtures are present and auditable.

---

## 7. Interface and Data Model Changes

## 7.1 Audit result schema

Extend critique results to include:

```json
{
  "overall_score": 72,
  "ship_blocking": true,
  "schema_version": "2026-06-19.v1",
  "artifact_id": "fixture_deck_7gi_v1:pptx_render",
  "render_defects": [...],
  "layout_quality_warnings": [...],
  "style_preference_warnings": [...],
  "rubric": "institutional_consulting",
  "artifact_type": "pptx_render",
  "slides": [
    {
      "slide_id": "team_grid_01",
      "slide_number": 4,
      "status": "pass",
      "findings": []
    }
  ]
}
```

## 7.2 Export metadata

Each PPTX export run should return structured metadata:

```json
{
  "editable_native_ratio": 0.89,
  "slides_with_image_fallback": [8],
  "fallback_reasons": {
    "8": "reference_figure_embed"
  },
  "slide_statuses": {
    "1": "native",
    "8": "fallback"
  }
}
```

## 7.3 Style extraction output

This section is stretch-only and does not participate in weekend sign-off.

Starter output for reference style extraction:

```json
{
  "deck_title": "CCC_Angola Focus_vf_for_ac",
  "brand_tokens": {
    "primary_navy": "#222936",
    "accent_bronze": "#CD8B45",
    "secondary_teal": "#4F8F88"
  },
  "fonts": {
    "heading": "Garamond-like",
    "body": "Calibri-like"
  },
  "chrome": {
    "logo_position": "top_right",
    "footer_style": "thin_rule_plus_confidential_plus_page",
    "divider_style": "navy_full_bleed_with_bronze_rule"
  }
}
```

## 7.4 Fallback semantics

- `full_slide_fallback`: never allowed on `must be native` slides.
- `region_fallback`: allowed only for `allowed exempt fallback` slides and must still preserve surrounding slide chrome as native objects.
- `unsupported_non_exempt_slide`: export fails with non-zero status and structured downgrade metadata; it does not silently complete.
- `sanitized_real_deck_exemptions`: none. All five slides in the sanitized real-deck reproduction are `must be native`.

## 7.5 Flag and config behavior

**Source of truth**

- base config: `~/.codex/config.toml` or Inkline config equivalent already used by the repo
- CLI flag overrides config
- environment variable overrides base config only when explicitly documented

**Required controls**

- `inkline.features.editable_institutional_pptx`
  - default: `false`
- `inkline.audit.rubric`
  - default: existing rubric
  - weekend sign-off value: `institutional_consulting`
- `inkline.pptx.allow_full_slide_fallback`
  - default: `true` for legacy path
  - weekend sign-off value: `false`

**Required test coverage**

- one CI-safe test for flagged institutional path
- one CI-safe test confirming legacy unflagged path remains callable
- one local-system sign-off run on flagged institutional path

Flag interaction rules:

- `--editable-institutional` is the authoritative CLI switch that enables institutional editable mode for that invocation
- config may set the same mode as a default when the CLI flag is omitted
- explicit CLI flags override config and environment
- legacy specs rendered without `--editable-institutional` must continue to use the current PPTX path
- new institutional primitives must not be auto-selected on the legacy path
- exit code `23` applies only to the flagged institutional path, never to legacy PPTX mode

## 7.6 Sign-off ownership and package

- engineering owner: current Inkline operator on `k1mini`
- acceptance owner: user / project owner reviewing the artifact bundle
- `engineering_signoff` requires:
  - both canonical fixtures generated successfully
  - local-system audit gates passing
  - manual QA checklist completed
- `production_ship_ready` requires everything in `engineering_signoff` plus one Windows PowerPoint validation pass.
- Weekend approval target for this sprint is `engineering_signoff`.
- If Windows PowerPoint validation is unavailable, the sprint may still achieve `engineering_signoff` but must mark `powerpoint_validation_pending=true` in the deferred issues list.

## 7.7 CLI and artifact contract

- `inkline render --format pptx --editable-institutional`
  - authoritative command for generating `deck.pptx`
- `inkline inspect-pptx <deck.pptx> --export-metadata-out <path>`
  - authoritative command for generating `export_metadata.json`
- `inkline audit-pptx <deck.pptx> --rubric institutional_consulting --out <path>`
  - authoritative command for generating `audit.json`
  - must also emit `deck.rendered.pdf` in the same artifact directory
- `inkline compare-rendered ... --out <path>`
  - authoritative command for generating `parity_report.json`

Exit codes:

- `0`: success and all requested artifacts produced
- `20`: export failure
- `21`: audit failure
- `22`: parity gate failure
- `23`: unsupported non-exempt fallback

Metadata embedding is optional. JSON sidecar artifacts are authoritative for sign-off.

## 7.8 Parity harness contract

- rasterization tool: `pdftoppm`
- rasterization DPI: `144`
- diff algorithm: normalized mean absolute pixel delta after masking, expressed on a `0.0-1.0` scale
- normalization:
  - convert to RGB
  - trim transparent margins
  - scale pages to identical pixel dimensions before diff
- masking rules:
  - ignore page number region
  - ignore timestamp or generated-at metadata if present
- font substitution:
  - any detected substitution adds a warning
  - parity gate is still evaluated, but `production_ship_ready` cannot be granted until substitution is resolved or explicitly accepted
- baseline policy:
  - weekend sign-off compares rendered PPTX against same-run Typst PDF baseline
  - checked-in goldens are informative only and not the gating artifact for this sprint
- aggregation:
  - compute one diff score per parity-gated slide
  - compute `parity_diff_score` as the simple arithmetic mean across those slide scores
- family-to-page mapping source:
  - use the corpus classification matrix in Section 5 as the authoritative family-to-slide mapping
- page alignment source of truth:
  - match rendered pages by the slide order emitted from the same fixture spec
  - if page count or order diverges from the fixture spec, parity run fails with exit code `22`
- masking implementation source:
  - use a checked-in static mask configuration stored with the fixture under `examples/institutional/fixture_deck_7gi_v1/masks/`

## 7.9 Vision-provider contract

- required provider for weekend sign-off: `codex_cli`
- forbidden: silent fallback to non-vision providers such as `antigravity_cli`
- any provider mismatch causes audit failure for sign-off
- selected provider and fallback history must be recorded in `audit.json` under `provider_trace`

---

## 8. Test Plan

Tests are split into CI-safe, local-system, and human sign-off tiers. Sign-off claims only count if they are attached to one of these tiers explicitly.

## 8.1 CI-safe unit tests

- PPTX text-fit helpers
- fallback-report generation
- audit result schema classification
- vision preflight provider selection

## 8.2 CI-safe integration tests

- render a fixture deck to PDF and editable PPTX
- verify export metadata and schema structure
- verify per-slide native/fallback reporting
- verify rubric classification logic
- verify feature-flag behavior for editable institutional mode and fallback policy

These tests must not require live vision providers.

## 8.3 Local-system integration tests

- render the PPTX to PDF with `soffice`
- audit both artifacts
- verify:
  - no ship-blocking render defects
  - native-editable ratio above threshold
  - no silent fallback

These tests require the local `k1mini` environment with:

- `LibreOffice 25.x`
- bridge on `18083`
- vision-capable provider override available

## 8.4 Regression tests

Create a mini institutional fixture deck covering:

1. cover
2. three-card thesis
3. capability grid
4. team/headshots
5. KPI bridge
6. opportunity cards
7. process timeline
8. appendix matrix

## 8.5 Manual QA and sign-off

Required sign-off checks:

- open PPTX in LibreOffice on `k1mini`
- open PPTX in PowerPoint on Windows if accessible during or immediately after the sprint
- edit text on a representative sample of slides
- confirm objects remain editable
- inspect for overlap, clipping, footer loss, and broken logo/chrome
- record substituted-font observations if any
- attach deferred-issues list if non-ship-blocking warnings remain
- save the edited deck copy as `manual_editability_check.pptx`
- save at least one screenshot per edited family in `manual_qa_screens/`

Weekend sign-off requires:

1. all CI-safe unit and integration tests pass
2. local-system integration tests pass on `k1mini`
3. both canonical fixture artifact bundles are produced
4. manual QA checklist is completed
5. if Windows PowerPoint validation is unavailable, the bundle is marked `engineering_signoff_only`

Manual QA artifact contract:

- checklist template path: `docs/templates/manual_qa_checklist_institutional.md`
- screenshot directory: `manual_qa_screens/`
- edited proof deck: `manual_editability_check.pptx`
- pass/fail recorder: the engineering owner named in Section `7.6`
- one failed in-scope family blocks `engineering_signoff`

Required manual editability script per in-scope family:

1. `cover`
   - extend title text length by roughly `20%`
   - save and reopen
   - verify no overlap with subtitle or confidentiality label
2. `team_grid`
   - replace one proof point with a two-line variant
   - swap one headshot with another placeholder image of different aspect ratio
   - save and reopen
   - verify card alignment and caption integrity
3. `institutional_kpi_cards`
   - extend one assumption bullet to two lines
   - change one KPI value width materially, e.g. `500` to `500.0`
   - save and reopen
   - verify no KPI card overflow or label collision
4. `institutional_timeline`
   - extend one phase title by roughly `20%`
   - add one extra body line to one phase
   - save and reopen
   - verify timeline cards do not collide with the spine or each other
5. `appendix_matrix`
   - widen one cell value from short text to a two-line entry
   - save and reopen
   - verify row height expands cleanly without clipping or border loss

Objective manual pass/fail rule:

- pass if the edited slide preserves all intended objects and has no clipping, overlap, missing borders, or displaced chrome after save/reopen
- fail if any edited slide loses editability, clips text, collapses a container, or overlaps another object

---

## 9. Rollout Plan

### Phase 1 — Weekend implementation

- deliver code changes behind explicit controls:
  - `inkline.features.editable_institutional_pptx`
  - `inkline.audit.rubric=institutional_consulting`
  - `inkline.pptx.allow_full_slide_fallback=false`
- land fixtures, docs, CLI, and audit schema
- validate on the 7GI-style institutional fixture deck

### Phase 2 — Immediate follow-up

- re-run against a real cloned version of the AGEH / 7GI deck workflow
- compare editable PPTX output to prior PDF benchmark
- capture residual cases for follow-up sprint

### Phase 3 — Post-weekend extensions

- fuller reference-style imitation
- richer institutional slide taxonomy
- PowerPoint-specific visual-diff testing improvements

### Migration/default behavior

- Existing users remain on current PPTX behavior unless `inkline.features.editable_institutional_pptx=true`.
- New `audit-pptx` and institutional rubric flows are opt-in but documented as required for editable institutional sign-off.
- If a primitive lacks PPTX support, export must fail with structured downgrade metadata unless an explicit fallback exemption is configured.
- CLI flag precedence:
  - explicit CLI flag
  - documented environment override
  - repo/user config default

---

## 10. Risks and Edge Cases

1. **LibreOffice vs PowerPoint rendering drift**
   - Mitigation: treat `soffice` audit as baseline on `k1mini`, but keep the architecture open to PowerPoint COM/export on Windows for stronger parity checks.
2. **PPTX text-fit can over-shrink**
   - Mitigation: support fit policies and warn on excessive shrink.
3. **Institutional rubric may become too permissive**
   - Mitigation: keep hard defect separation and preserve stricter Vishwakarma mode as an explicit option.
4. **Reference-style extraction may over-promise**
   - Mitigation: scope v1 clearly to tokens/chrome/archetypes, not full content-aware recreation.
5. **Builder complexity may sprawl**
   - Mitigation: add reusable primitive constructors rather than deck-specific procedural code.
6. **Dirty working tree in Inkline repo**
   - Mitigation: keep changes localized, do not overwrite unrelated modifications in `src/inkline/intelligence/*` already present.

---

## 11. Acceptance Criteria

This sprint is successful only if all of the following are true:

1. Inkline can produce a native editable institutional PPTX for the five in-scope slide families with `editable_native_ratio >= 0.90` on the synthetic fixture deck and `>= 0.85` on the sanitized real-deck reproduction.
2. A rendered PPTX audit loop exists, is documented, and fails hard on incomplete or non-vision-backed audits.
3. Vision routing no longer hangs on a non-vision default provider and logs the selected provider path.
4. Audit output clearly distinguishes ship-blocking render defects from style-preference warnings using the `institutional_consulting` rubric.
5. Institutional primitives exist for `cover`, `team_grid`, `institutional_timeline`, `institutional_kpi_cards`, and `appendix_matrix`.
6. `ship_blocking_render_defects = 0` on both canonical corpus rendered PPTX audits.
7. `parity_diff_score <= 0.12` on the five in-scope slide families.
8. The workflow is reproducible from CLI/docs without one-off custom scripts.

---

## 12. Suggested Weekend Execution Order

Execution must follow dependency-driven slices, not parallel broad workstreams.

Thin-slice cutoff per must-do workstream:

- `W1`: native export metadata plus native output only for the five ship-blocking families
- `W2`: deterministic fit rules only for the five ship-blocking families and their fixture content
- `W3`: `audit-pptx` working on local rendered artifact with JSON output
- `W4`: deterministic provider selection with explicit failure on non-vision routes
- `W5`: schema split and minimum rubric split only to the extent required for audit output credibility
- `W6`: minimum viable primitives sufficient to render the two canonical fixtures
- `W8`: only the commands, docs, and fixtures required to execute the sign-off sequence

## Slice 1 — Preflight and audit plumbing

- W4 vision routing hardening
- W3 rendered PPTX audit loop skeleton
- audit schema scaffolding from W5

## Slice 2 — Export metadata and feature controls

- W1 export metadata / fallback reporting
- rollout flags and CLI surface from W8

## Slice 3 — One primitive end to end

- W2 text-fit utilities
- W6 `team_grid`
- fixture and rendered audit proving loop

## Slice 4 — Remaining ship-blocking primitives

- W6 `institutional_timeline`
- W6 `institutional_kpi_cards`
- W6 `appendix_matrix`
- cover / section-divider hardening

## Slice 5 — Parity tuning and rubric split

- W2 parity adjustments from fixture output
- W5 `institutional_consulting` rubric and defect split

## Slice 6 — Docs, sign-off, and optional stretch

- W8 documentation and regression harness polish
- W7 style extraction only if all ship-blocking gates already pass
- final rendered PPTX audit pass and sign-off package

---

## 13. Weekend Must-Do vs Defer

## Must do this weekend

- native editable PPTX hardening for the five in-scope slide families
- rendered PPTX audit loop
- vision routing fix for `codex_cli` vision preflight
- audit split between render defects and style ideology
- text-fit / spacing / parity improvements for the canonical corpus only
- institutional primitives for cover, team grid, KPI cards, timeline, appendix matrix
- docs, CLI, and fixtures

## Explicitly defer

- full content-aware style cloning from arbitrary reference decks
- broad PPTX support for non-fixture slide families
- stakeholder-strip as a first-class required primitive if appendix matrix already covers the need
- generalized PowerPoint round-trip editing semantics
- complete parity for every historical Inkline layout across all backends
- non-local / API-based services

---

## 14. Deliverables

1. Code changes in:
   - `src/inkline/pptx/`
   - `src/inkline/intelligence/`
   - `src/inkline/typst/`
   - `src/inkline/app/cli.py`
2. New or updated regression tests
3. New institutional fixture deck
4. Updated documentation
5. Signed-off rendered-PPTX audit result for the canonical corpus
6. Sign-off package containing:
   - generated `.pptx`
   - rendered PPTX PDF
   - audit JSON
   - export metadata JSON
   - manual QA checklist result
   - deferred issues list

Optional stretch deliverable only after all required gates pass:

7. reference-style extraction entry point (`W7`)

---

## 15. Definition of Done

The sprint is done when Inkline can produce and audit an editable institutional deck with:

- no major text overlap or clipping in the rendered PPTX artifact
- editable slide objects for core institutional slides
- explicit, reliable vision-backed sign-off
- audit output that distinguishes real breakage from aesthetic preference
- reproducible commands and tests in-repo
- a complete sign-off package saved next to the canonical fixture outputs
- `engineering_signoff` achieved even if `production_ship_ready` remains pending PowerPoint validation

## 16. Required Sign-off Command Sequence

The weekend artifact bundle is only valid if produced with the equivalent of this sequence for both canonical fixtures:

1. Render PDF baseline
   - `inkline render examples/institutional/fixture_deck_7gi_v1/<spec>.yaml --format pdf --out <artifact_dir>/baseline.pdf`
2. Render editable PPTX
   - `inkline render examples/institutional/fixture_deck_7gi_v1/<spec>.yaml --format pptx --editable-institutional --out <artifact_dir>/deck.pptx`
3. Save export metadata
   - `inkline inspect-pptx <artifact_dir>/deck.pptx --export-metadata-out <artifact_dir>/export_metadata.json`
4. Audit rendered PPTX
   - `inkline audit-pptx <artifact_dir>/deck.pptx --rubric institutional_consulting --out <artifact_dir>/audit.json`
5. Run parity comparison on in-scope slides
   - `inkline compare-rendered --baseline <artifact_dir>/baseline.pdf --pptx-render <artifact_dir>/deck.rendered.pdf --slides cover,team_grid,institutional_kpi_cards,institutional_timeline,appendix_matrix --out <artifact_dir>/parity_report.json`
6. Complete manual checklist
   - save `manual_qa_checklist.md`
7. Save deferred issues list
   - save `deferred_issues.md`

Required outputs per fixture:

- `baseline.pdf`
- `deck.pptx`
- `deck.rendered.pdf`
- `export_metadata.json`
- `audit.json`
- `parity_report.json`
- `manual_qa_checklist.md`
- `deferred_issues.md`

Artifact directory contract per fixture:

- synthetic fixture: `artifacts/weekend_sprint_2026-06-19/fixture_deck_7gi_v1/`
- sanitized real-deck fixture: `artifacts/weekend_sprint_2026-06-19/fixture_deck_7gi_v1_sanitized_real/`
- both directories must contain the full required output set and no external dependencies
