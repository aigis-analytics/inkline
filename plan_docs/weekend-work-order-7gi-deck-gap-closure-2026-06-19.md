# Weekend Work Order — 7GI Deck Gap Closure

**Date:** 19 June 2026
**Status:** Approved for execution
**Parent spec:** `plan_docs/weekend-sprint-spec-7gi-deck-gap-closure-2026-06-19.md`
**Objective:** Turn the approved sprint spec into a granular, execution-ready implementation order for the Inkline repo.

---

## 1. Execution Rule

Execute in the order below unless a blocker requires resequencing.

---

## 2. Work Packages

## WP1 — Vision Routing Preflight

**Goal:** Make visual audit provider selection deterministic and fail-fast.

### Tasks

1. Add preflight helper in `src/inkline/intelligence/vishwakarma.py`:
   - inspect `INKLINE_BRIDGE_URL`
   - inspect provider capabilities
   - force `codex_cli` when vision is required and default provider is non-vision
2. Mirror the same routing logic in:
   - `src/inkline/intelligence/overflow_audit.py`
   - `src/inkline/typst/chart_auditor.py`
3. Emit structured failure on:
   - non-vision provider
   - unavailable bridge
   - timed-out audit
4. Add tests for:
   - non-vision default provider
   - successful `codex_cli` override
   - “audit incomplete” treated as failure

### Acceptance check

- `inkline` audit paths do not hang when `antigravity_cli` is the default provider.

---

## WP2 — PPTX Native Export Metadata

**Goal:** Make native vs fallback export behavior explicit.

### Tasks

1. Extend `src/inkline/pptx/__init__.py` export path to return metadata.
2. Add fields:
   - `editable_native_ratio`
   - `slides_with_image_fallback`
   - `fallback_reasons`
3. Thread these through CLI and tests.
4. Update any current PPTX helper assumptions that treat picture-only slides as acceptable success.

### Acceptance check

- Export log/report states exactly which slides, if any, are not native-editable.

---

## WP3 — PPTX Text-Fit Utilities

**Goal:** Stop native PPTX text overlap/clipping on institutional slides.

### Tasks

1. Add or refactor helper layer in `src/inkline/pptx/builder.py` for:
   - heading fit
   - body fit
   - table cell fit
   - callout strip fit
2. Add fit policies:
   - `fit_text`
   - `shrink_to_fit`
   - `fixed_size`
   - `truncate_with_warning`
3. Add spacing presets:
   - card title spacing
   - bullet spacing
   - matrix row padding
   - footer strip padding
4. Create tests with intentionally tight text to confirm deterministic behavior.

### Acceptance check

- Regression fixture slides no longer show visible text collision in rendered PPTX output.

---

## WP4 — Institutional Primitive Layouts

**Goal:** Replace ad hoc slide composition with reusable institutional primitives.

### Tasks

1. Implement `cover`
2. Implement `team_grid`
3. Implement `institutional_timeline`
4. Implement `institutional_kpi_cards`
5. Implement `appendix_matrix`

### Files

- `src/inkline/pptx/builder.py`
- `src/inkline/typst/slide_renderer.py`
- `src/inkline/authoring/backend_coverage.py`

### Required outputs

- one example per primitive
- one regression fixture per primitive
- explicit downgrade path if a backend lacks exact support

### Acceptance check

- 7GI-like fixture deck can be assembled without one-off procedural slide code.

---

## WP5 — Rendered PPTX Audit Command

**Goal:** Make editable-deck sign-off a standard command.

### Tasks

1. Add `inkline audit-pptx` CLI entry point.
2. Render PPTX to PDF via `soffice`.
3. Extract pages.
4. Run critique on the rendered artifact.
5. Save audit JSON next to the source PPTX when requested.
6. Add test coverage for:
   - missing `soffice`
   - successful audit
   - audit failure surfaced correctly

### Acceptance check

- A single command audits the rendered editable deck artifact end to end.

---

## WP6 — Audit Model Split

**Goal:** Separate broken decks from merely non-preferred decks.

### Tasks

1. Refactor critique schema in `src/inkline/intelligence/vishwakarma.py`.
2. Add categories:
   - `render_defect`
   - `layout_quality`
   - `style_preference`
3. Add deck-level flags:
   - `ship_blocking`
   - `quality_warnings`
   - `vishwakarma_warnings`
4. Add the minimum `institutional_consulting` rubric split needed for credible audit output.
5. Update docs and tests.

### Acceptance check

- Dense appendix tables can receive warnings without being treated as rendering failures.

---

## WP7 — Reference Style Extraction v1

**Goal:** Optional stretch only after all required gates pass.

### Tasks

1. Create `src/inkline/intelligence/reference_deck.py`.
2. Add `inkline extract-style <deck.pptx>`.
3. Extract:
   - primary colors
   - secondary accents
   - heading/body font guesses
   - logo position
   - divider/cover chrome
   - footer convention
4. Emit:
   - style report markdown/json
   - starter brand/config output
5. Document limitations clearly.

### Acceptance check

- Stretch only. Do not start until the required sign-off package is complete.

---

## WP8 — Institutional Fixture Deck and Regression Harness

**Goal:** Lock the improvements to a real institutional use case.

### Tasks

1. Build the canonical synthetic fixture deck at `examples/institutional/fixture_deck_7gi_v1/fixture_deck_7gi_v1.yaml`.
2. Build the sanitized real-deck reproduction fixture at `examples/institutional/fixture_deck_7gi_v1/fixture_deck_7gi_v1_sanitized_real.yaml`.
3. Add the artifact directory contract under `artifacts/weekend_sprint_2026-06-19/`.
4. Add CI-friendly render harness plus local-system sign-off harness.
5. Capture expected artifact outputs and thresholds.

### Acceptance check

- Both canonical fixtures become the regression baseline for institutional editable-deck work.

---

## WP9 — Documentation and Operator Workflow

**Goal:** Make the improved workflow reproducible by another engineer.

### Tasks

1. Update `README.md` or docs with:
   - render PDF
   - render editable PPTX
   - audit PDF
   - audit rendered PPTX
   - extract style
2. Add troubleshooting notes for:
   - non-vision bridge providers
   - missing `soffice`
   - fallback-heavy PPTX exports
3. Add explicit “institutional deck sign-off checklist”.

### Acceptance check

- A new operator can follow docs to reproduce the full workflow.

---

## 3. Execution Sequence

1. WP1 Vision routing preflight
2. WP5 Rendered PPTX audit command skeleton
3. WP2 PPTX native export metadata
4. WP3 PPTX text-fit utilities
5. WP4 Institutional primitives
6. WP8 Fixture deck and regression harness
7. WP6 Audit model split
8. WP7 Reference style extraction v1
9. WP9 Documentation and workflow polish

---

## 4. Concrete File Touch List

### High-probability file targets

- `src/inkline/intelligence/vishwakarma.py`
- `src/inkline/intelligence/overflow_audit.py`
- `src/inkline/typst/chart_auditor.py`
- `src/inkline/pptx/__init__.py`
- `src/inkline/pptx/builder.py`
- `src/inkline/typst/slide_renderer.py`
- `src/inkline/authoring/backend_coverage.py`
- `src/inkline/app/cli.py`
- `tests/pptx/*`
- `tests/intelligence/*`
- `examples/*`
- `docs/*`

### New likely files

- `src/inkline/intelligence/reference_deck.py`
- institutional fixture assets/spec under `examples/` or `tests/pptx/fixtures/`

---

## 5. Verification Commands

### Minimum manual verification loop

```bash
inkline render examples/<fixture>.md --output pdf,pptx
inkline audit-pptx output/<fixture>.pptx
inkline critique-pdf output/<fixture>.pdf --rubric institutional_consulting
inkline extract-style <reference>.pptx
```

### Additional local render check

```bash
soffice --headless --convert-to pdf --outdir /tmp/audit output/<fixture>.pptx
```

---

## 6. Definition of Ready for Each Work Package

- target file(s) identified
- acceptance check written
- at least one test target identified
- known dependency order understood

---

## 7. Definition of Done for the Work Order

- Parent sprint spec is audited and accepted
- All `Must do this weekend` items from parent spec are either completed or explicitly marked blocked/deferred with evidence
- Institutional fixture deck renders cleanly as both PDF and editable PPTX
- Rendered PPTX audit produces no ship-blocking overlap/clipping defects on the target slide families
- Docs and CLI are updated enough for reuse
