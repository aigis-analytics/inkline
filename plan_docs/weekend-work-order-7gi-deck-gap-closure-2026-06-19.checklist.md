# Weekend Execution Checklist — 7GI Deck Gap Closure

**Date:** 19 June 2026
**Parent work-order:** `plan_docs/weekend-work-order-7gi-deck-gap-closure-2026-06-19.md`
**Execution target:** `engineering_signoff`

## 1. Sign-off Surface

- [ ] Add `render` support for spec-driven institutional fixture decks.
- [ ] Add `inspect-pptx` command producing `export_metadata.json`.
- [ ] Add `audit-pptx` command rendering PPTX via `soffice` and writing `audit.json`.
- [ ] Add `compare-rendered` command producing `parity_report.json`.
- [ ] Record `provider_trace` and enforce `codex_cli` for weekend sign-off audits.

## 2. PPTX Path

- [ ] Add native/fallback slide metadata collection in PPTX export.
- [ ] Expose `editable_native_ratio`, slide statuses, and fallback reasons.
- [ ] Restrict flagged institutional path to the five ship-blocking families:
  - [ ] `cover`
  - [ ] `team_grid`
  - [ ] `institutional_timeline`
  - [ ] `institutional_kpi_cards`
  - [ ] `appendix_matrix`
- [ ] Keep legacy PPTX path callable and unaffected when `--editable-institutional` is not used.

## 3. Audit and Parity

- [ ] Implement PPTX -> PDF render helper with `soffice`.
- [ ] Fail hard on non-vision provider selection for sign-off audits.
- [ ] Emit structured audit result JSON with provider trace and artifact paths.
- [ ] Implement PDF-to-image parity comparison using `pdftoppm`.
- [ ] Use static fixture masks under `examples/institutional/fixture_deck_7gi_v1/masks/`.

## 4. Fixture Corpus

- [ ] Add canonical synthetic fixture spec at `examples/institutional/fixture_deck_7gi_v1/fixture_deck_7gi_v1.yaml`.
- [ ] Add sanitized real-deck fixture spec at `examples/institutional/fixture_deck_7gi_v1/fixture_deck_7gi_v1_sanitized_real.yaml`.
- [ ] Add placeholder-safe assets under `examples/institutional/fixture_deck_7gi_v1/assets/`.
- [ ] Add mask config under `examples/institutional/fixture_deck_7gi_v1/masks/`.

## 5. Tests and Docs

- [ ] Add CLI tests for new commands and failure modes.
- [ ] Add unit coverage for metadata and provider selection.
- [ ] Add docs for the weekend sign-off command sequence.
- [ ] Add manual QA checklist template at `docs/templates/manual_qa_checklist_institutional.md`.

## 6. Execution Order

1. CLI and helper scaffolding
2. PPTX metadata and inspect path
3. `audit-pptx` render/audit loop
4. `compare-rendered` parity path
5. fixture corpus and mask files
6. tests and docs
7. fixture run and artifact generation
8. independent post-code audit
