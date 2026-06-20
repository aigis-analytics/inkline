# Inkline Reference-Driven Slide Archetype System — Audit Note

**Date:** 20 June 2026  
**Primary spec:** `plan_docs/reference-driven-slide-archetype-system-spec-2026-06-20.md`  
**Work program:** `plan_docs/reference-driven-slide-archetype-work-program-2026-06-20.md`

## 1. Audit method

- External review was run in a separate `codex exec` process using `gpt-5.4` as the closest locally available substitute for the requested `gpt-5.5`.
- Research inputs for the spec used Perplexity MCP plus the existing Inkline repo and playbook corpus.
- Multiple review rounds were run. Each round surfaced implementation-readiness gaps, which were folded back into the spec and work program.

## 2. Main issues found across audit rounds

The independent reviewer repeatedly focused on these categories:

1. mode boundaries and deterministic-renderer preservation
2. taxonomy normalization between `full-slide archetype`, `layout`, `template`, and `freeform`
3. missing schema/versioning contracts for new artifacts
4. metadata precedence and one resolved authority order
5. incomplete deck-level audit semantics
6. ingestion MVP ambiguity between `PPTX` and `PDF`
7. missing compiler contract between archetypes and renderer-native manifests
8. missing curation workflow contract for reference-family overrides
9. missing operational guardrails for confidential reference assets
10. missing migration/backward-compatibility policy for legacy specs and audit consumers

## 3. Changes made in response

The current spec now explicitly includes:

- Execute Mode vs Draft Mode vs audit boundaries
- preservation of existing hard-gate audit policy
- normalized taxonomy and compiler ownership rule
- versioned contracts for:
  - `storyboard.json`
  - `authoring_trace.json`
  - `reference_family_manifest.json`
  - `reference_slide_manifest.json`
  - `deck_audit.json`
- one metadata precedence order and one single validation/merge boundary
- a `compiled_slide_manifest` schema with renderer-facing payload rules
- PPTX parity/editability exception classes
- `PPTX-only` ingestion MVP
- file-first curation workflow plus `curation_overrides.yaml`
- deck verdict aggregation rules and default threshold table
- confidential-asset enforcement rules for ingest/package time
- legacy migration policy

The work program was also updated so those contracts are represented as explicit deliverables rather than implicit follow-up work.

## 4. Latest external review result

**Latest explicit external verdict:** `Approved with Conditions`

Latest material findings at the time of review were:

1. one validation/merge owner was not explicit enough
2. some audit thresholds/defaults were not yet normative
3. PPTX parity/editability required an exception model
4. confidential reference governance needed ingest/package enforcement
5. rollout needed a compatibility policy for legacy specs and consumers

Those points have now been incorporated into the current spec revision after that review pass.

## 5. Current status

**Status:** `Conditionally approved package, ready for implementation planning`

Interpretation:

- The direction, architecture, and phase ordering have been independently validated.
- The remaining review comments were operational-contract items rather than a rejection of the design.
- The spec and work program are now sufficiently concrete to begin implementation in phased slices.

## 6. Remaining caveat

I did **not** obtain a fresh final external verdict after the very last patch set in this note.  
So the most accurate statement is:

- the package has undergone rigorous independent audit
- the latest explicit saved verdict is `Approved with Conditions`
- the current documents already fold in the final listed conditions

## 7. Recommendation

Proceed with implementation from the work program, starting with:

1. Phase 1 `storyboard metadata + validation boundary`
2. Phase 2 `full-slide archetype compiler contract`
3. Phase 3 `reference-family ingestion + curation enforcement`

Then run a true **post-code** external audit once those phases land.
