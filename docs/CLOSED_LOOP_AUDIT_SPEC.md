# Inkline Closed-Loop Audit-Fix-Rerender System

## Context

Inkline's current pipeline is **open-loop**: the LLM generates slides, the renderer produces a PDF, the audit flags issues (overflow, clipping, brand violations), but the warnings are printed to stderr and ignored. Broken PDFs ship. The user has to manually identify and fix every issue — font mismatches, content overflow, unequal card heights, chart clipping — through repeated trial-and-error cycles.

The goal is a **fully closed-loop system** where audit findings — including LLM visual audit findings — automatically trigger corrections and re-rendering until the deck receives a clean sign-off from the visual auditor. Cost is not a constraint; quality of the final output is.

## Architecture: Two Nested Loops

```
CHART AUDIT (one-time, after chart rendering)
├─ Size/fit: verify chart PNG fits slide container, re-render if oversized
├─ Brand colours: verify chart palette matches brand, warn if off-palette  
├─ Factual data: verify chart values exist in source sections, warn if ungrounded
│
OUTER LOOP (visual quality — LLM auditor driven, max 5 iterations)
├─ INNER LOOP (structural overflow — deterministic, max 3 iterations)
│   ├─ Pre-render validate & fix slides (capacity, text length, card heights)
│   ├─ Render Typst source → Compile PDF
│   ├─ Check page count
│   ├─ If overflow: identify slides → graduated fix → recompile
│   └─ Exit inner loop when page count matches
│
├─ LLM Visual Audit (Claude vision reviews every slide)
│   ├─ If ALL CLEAR (no errors): exit outer loop → ship PDF ✓
│   ├─ If ERRORS found: parse findings → apply targeted fixes → re-enter inner loop
│   └─ Continue until visual auditor signs off or max iterations reached
│
└─ Final audit report emitted
```

The key change from the previous plan: **the LLM visual audit is inside the outer loop**, not a one-shot gate at the end. The auditor's ERROR findings feed back into the fixer, which corrects slides and re-renders. The auditor reviews again. This continues until the auditor gives a clean pass or the max iteration count is reached.

## Implementation Plan

### New file: `src/inkline/intelligence/slide_fixer.py`

Contains all auto-fix logic. Five main functions:

#### 1. `validate_and_fix_slides(slides) → (fixed_slides, warnings)`
Pre-render validation that ACTS on violations:
- Truncate items exceeding SLIDE_CAPACITY (from `layout_selector.py`)
- Shorten text fields > 200 chars at word boundary + "..."
- Shorten titles > 75 chars
- Remove footnotes on slides near capacity
- Fill missing required fields with safe defaults

#### 2. `identify_overflow_slides(pdf_path, slides, source) → list[int]`
Determine WHICH slides overflowed:
- **Stage A (deterministic):** Extract text from each PDF page via PyMuPDF. Walk pages matching slide titles. When a slide's title appears on two consecutive pages, or the next slide's title is pushed forward, that slide overflowed.
- **Stage B (heuristic fallback):** Score each slide by overflow risk (content count, char count, title length, slide type weight). Top N by score are likely culprits.

#### 3. `apply_graduated_fixes(slides, source, overflow_indices, attempt, theme) → (slides, source, needs_rerender)`
Three escalating fix levels:
- **Attempt 1 — Content reduction:** Reduce items by 20%, truncate text to 150 chars, shorten titles to 60 chars, remove footnotes. Modifies slide specs → requires re-render.
- **Attempt 2 — Typst source micro-adjustments:** Reduce spacing (`v(14pt)` → `v(6pt)`), body font (`12pt` → `10pt`), card padding (`14pt` → `10pt`), chart height. Modifies source string only → recompile without re-render.
- **Attempt 3 — Slide splitting:** Split overflowing slides into two. Modifies slide list → requires re-render.

#### 4. `fix_from_llm_findings(slides, findings) → (fixed_slides, applied_fixes)`
Parse LLM visual audit findings and apply targeted fixes:

| LLM Finding Pattern | Auto-Fix Action |
|---------------------|-----------------|
| "clipped" / "cut off" / "truncated" | Reduce content count by 1, shorten longest text field |
| "overflow" / "extra page" | Trigger inner overflow loop |
| "overlap" / "overlapping" | Reduce item count, increase spacing between elements |
| "brand" / "colour" / "color" inconsistency | No auto-fix (cosmetic — logged as warning) |
| "alignment" / "misaligned" | No auto-fix (template-level — logged as warning) |
| "illegible" / "too small" | Increase font size in Typst source |
| "missing content" / "empty" | Re-check slide data, warn if genuinely empty |
| "equal height" / "card height" / "inconsistent" | Equalise card body text lengths by padding shorter cards |

Returns the modified slides and a list of what was changed, so the outer loop can track progress.

#### 5. `equalise_card_heights(slides) → slides`
For three_card, four_card, and feature_grid slides: measure the longest card body text, pad shorter cards to match by adding trailing whitespace or a non-breaking space filler. This ensures Typst renders all cards at the same height.

### Modified file: `src/inkline/typst/__init__.py`

`export_typst_slides()` implements the two nested loops:

```python
def export_typst_slides(
    slides, output_path, *,
    brand, template, title, date, subtitle,
    font_paths=None, image_root=None,
    audit=True, audit_visual=True,
    auto_fix=True,
    max_overflow_attempts=3,   # inner loop max
    max_visual_attempts=5,     # outer loop max
) -> Path:

    # === PHASE 0: Setup ===
    # Brand, theme, logo copy, root detection (unchanged)

    # === PHASE 1: Chart rendering (ONE TIME) ===
    _auto_render_charts(slides, brand, root)

    # === PHASE 2: Pre-render validation & auto-fix ===
    if auto_fix:
        slides, pre_warnings = validate_and_fix_slides(slides)
        slides = equalise_card_heights(slides)

    # === PHASE 3: OUTER LOOP (visual quality) ===
    visual_attempt = 0
    final_warnings = []

    while visual_attempt <= max_visual_attempts:
        # --- INNER LOOP (structural overflow) ---
        overflow_attempt = 0
        source = None
        needs_rerender = True

        while overflow_attempt <= max_overflow_attempts:
            if needs_rerender:
                deck_spec = build_deck_spec(slides, title, date, subtitle)
                source = TypstSlideRenderer(theme).render_deck(deck_spec)

            compile_typst(source, output_path=output_path, ...)
            actual = _count_pages(output_path)
            expected = len(slides)

            if actual == expected:
                break  # inner loop success

            if overflow_attempt >= max_overflow_attempts or not auto_fix:
                break  # give up on overflow

            overflow_indices = identify_overflow_slides(output_path, slides, source)
            overflow_attempt += 1
            slides, source, needs_rerender = apply_graduated_fixes(
                slides, source, overflow_indices, overflow_attempt, theme,
            )

        # --- Post-overflow: run ALL audits ---
        post_warnings = []
        post_warnings += audit_rendered_pdf(output_path, expected_slides=len(slides))
        post_warnings += _audit_chart_images(slides, root, output_path)

        # --- LLM Visual Audit ---
        if audit_visual:
            llm_warnings = audit_deck_with_llm(output_path, slides)
            post_warnings += llm_warnings

            errors = [w for w in llm_warnings if w.severity == "error"]

            if not errors or not auto_fix:
                # ALL CLEAR or auto_fix disabled — exit outer loop
                final_warnings = pre_warnings + post_warnings
                break

            if visual_attempt >= max_visual_attempts:
                # Max attempts reached — ship what we have
                final_warnings = pre_warnings + post_warnings
                break

            # ERRORS FOUND — fix and retry
            visual_attempt += 1
            slides, applied = fix_from_llm_findings(slides, errors)
            if not applied:
                # No actionable fixes possible — exit
                final_warnings = pre_warnings + post_warnings
                break

            log.info("Visual audit attempt %d: fixed %d issues, re-rendering",
                     visual_attempt, len(applied))
            continue  # re-enter inner loop with fixed slides
        else:
            # No visual audit — exit after structural checks
            final_warnings = pre_warnings + post_warnings
            break

    # === PHASE 4: Final report ===
    if final_warnings:
        emit_audit_report(final_warnings)

    return output_path
```

### Chart Audit System (inside `src/inkline/intelligence/slide_fixer.py`)

Charts are currently rendered by matplotlib in isolation — no awareness of the slide they'll be embedded in, no brand colour verification, and no factual check. Three new checks:

#### `audit_chart_fit(chart_path, slide_type, theme) → list[AuditWarning]`
**Size/fit check:** Before chart is embedded in the slide, verify:
- Chart image dimensions (pixels) will fit within the slide's chart container without clipping
- Container heights by slide type: `chart_caption` = 6.5cm, `dashboard` = 6.5cm, `chart` = 8.5cm
- At 150 DPI: 6.5cm ≈ 384px. If chart PNG height > container_px × 1.1 (10% margin), flag as WARNING and re-render at a smaller `height` parameter
- Check aspect ratio: if chart is taller than wide, flag and suggest landscape orientation
- **Auto-fix:** Re-call `render_chart_for_brand()` with adjusted `width`/`height` kwargs that fit the container

#### `audit_chart_brand(chart_path, brand) → list[AuditWarning]`
**Brand colour check:** Verify chart colours align with brand palette:
- Extract dominant colours from chart PNG via PIL (sample non-background pixels, cluster into top 5-8 colours)
- Compare extracted colours against `brand.chart_colors` + `brand.primary` + `brand.secondary`
- If any extracted colour is >30 colour-distance (Euclidean in RGB) from the nearest brand colour, flag as WARNING
- Exception: grey tones (for axes, grid lines, labels) are always acceptable
- **Auto-fix:** Not auto-fixable from the PNG — but the chart can be re-rendered with explicit `brand_colors` parameter (which `render_chart_for_brand` already does). Flag as warning if the chart renderer isn't using brand colours properly.

#### `audit_chart_data(chart_data, source_sections) → list[AuditWarning]`
**Factual verification:** Before rendering, verify chart data is grounded in the source content:
- Compare numerical values in `chart_data` against values found in the section's text fields (narrative, metrics, table_data)
- Flag any chart data point that doesn't appear in the source section as WARNING: "Chart value X not found in source data — verify factual accuracy"
- For `illustrative: true` charts, skip this check (they're explicitly labelled as synthetic)
- **Not auto-fixable** — flags for human review

#### Integration into the pipeline

Chart audit runs **after `_auto_render_charts()`** and **before the inner loop**:

```
Phase 1: Chart rendering
Phase 1b: Chart audit (NEW)
  ├─ For each rendered chart:
  │   ├─ audit_chart_fit() — resize if needed, re-render
  │   ├─ audit_chart_brand() — warn if off-palette
  │   └─ audit_chart_data() — warn if ungrounded values
  └─ Chart fixes applied before entering render loop
Phase 2: Pre-render validation
Phase 3: Nested loops...
```

Charts are fixed **once** before the main loops — they don't change during the overflow/visual fix iterations.

### Modified file: `src/inkline/intelligence/overflow_audit.py`

Add one function:
- `extract_page_texts(pdf_path) → list[str]` — PyMuPDF text extraction per page

### Key files
- `/mnt/d/inkline/src/inkline/typst/__init__.py` — main pipeline with nested loops
- `/mnt/d/inkline/src/inkline/intelligence/overflow_audit.py` — audit functions + new text extractor
- `/mnt/d/inkline/src/inkline/intelligence/slide_fixer.py` — **new** fix logic (slides + charts)
- `/mnt/d/inkline/src/inkline/typst/slide_renderer.py` — render patterns for source manipulation
- `/mnt/d/inkline/src/inkline/typst/chart_renderer.py` — chart rendering (read for re-render API)
- `/mnt/d/inkline/src/inkline/intelligence/layout_selector.py` — SLIDE_CAPACITY dict

### Design decisions
- **LLM visual audit is INSIDE the outer loop** — runs on every iteration until clean pass
- **Cost is not a constraint** — quality of final output is the priority
- **Inner loop is deterministic** (no LLM calls) — fast structural fixes
- **Outer loop uses LLM vision** — catches everything heuristics miss
- **Chart rendering outside both loops** — charts don't change
- **Card height equalisation** runs pre-render — structural fix, not cosmetic
- **Max 5 visual audit iterations** — safety bound, but expected to converge in 2-3
- **API backward-compatible** — `auto_fix=True` by default
- **Fix tracking** — each fix is logged so the outer loop can detect if no progress is being made (avoid infinite loops where the same error is found but no fix is applicable)

### Exit conditions for outer loop
1. **Clean pass**: LLM visual audit returns zero ERRORs → ship PDF
2. **No actionable fixes**: `fix_from_llm_findings()` returns `applied=[]` — the errors are cosmetic or template-level issues that can't be auto-fixed → ship PDF with warnings
3. **Max iterations**: `visual_attempt >= max_visual_attempts` → ship PDF with warnings
4. **No visual audit**: `audit_visual=False` → exit after structural checks only

## Verification

1. Run existing test suite: `py.exe -m pytest tests/ -q --deselect tests/test_brands.py::test_minimal_palette`
2. Create test with known-overflowing slide, verify auto-fix resolves it
3. Create test with slide that triggers LLM visual ERROR (e.g., deliberately clipped text), verify the loop fixes it
4. Regenerate Aigis investor deck with `auto_fix=True`, verify clean visual audit pass
5. Inspect final PDF visually to confirm quality
