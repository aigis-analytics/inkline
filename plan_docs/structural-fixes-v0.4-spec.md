# Inkline v0.4 Structural Fixes Spec

## Context

Exposed during end-to-end testing: generating a 16-section board DD slide deck from a 60-page markdown report using `DesignAdvisor(brand="aigis", template="dmd_stripe", mode="llm")`. Four structural issues prevent reliable end-to-end PDF generation.

## Fix 1: Missing Image Graceful Handling

### Problem
When the LLM designs a `dashboard`, `chart_caption`, or `chart` slide, it specifies `image_path: "some_chart.png"`. If that image doesn't exist, Typst compilation crashes with `file not found`. There is no pre-flight validation and no fallback.

### Root Cause
- `slide_renderer.py` — `_dashboard_slide()`, `_chart_caption_slide()`, `_chart_slide()` all embed `#image("path")` directly without checking existence
- `__init__.py` — `export_typst_slides()` detects image root but never validates paths
- Post-render audit checks image existence AFTER compilation (useless since it already crashed)

### Fix
1. **Pre-flight validation in `export_typst_slides()`** (in `__init__.py`):
   - Before calling `renderer.render_deck()`, iterate slides and check each `image_path`
   - If image doesn't exist, either:
     - (a) Replace the slide type with a non-image alternative (e.g., `dashboard` → `kpi_strip` using the stats data), OR
     - (b) Generate a placeholder image (solid color rectangle with text "Chart not available")
   - Log a warning either way

2. **Renderer-level fallback** (in `slide_renderer.py`):
   - Add a `_placeholder_image()` helper that generates inline Typst markup (a colored rect with text) when image_path is missing
   - Each image-embedding slide method checks `Path(root / image_path).exists()` and uses placeholder if missing

### Files to Modify
- `src/inkline/typst/__init__.py` — add pre-flight image validation before render
- `src/inkline/typst/slide_renderer.py` — add `_placeholder_image()` fallback in `_chart_slide`, `_chart_caption_slide`, `_dashboard_slide`

---

## Fix 2: System Prompt Size Reduction

### Problem
`_build_system_prompt()` inlines complete playbook texts totalling ~85K chars (~25K tokens). This exceeds the Claude Max bridge's effective processing time (300s timeout), causing fallback to API. It also wastes tokens — most playbook content is reference material irrelevant to the specific design task.

### Root Cause
- `design_advisor.py` line 388-392: loops over ALL loaded playbooks and appends full text
- `load_playbooks_for_task("slide")` returns 4 playbooks: `slide_layouts`, `template_catalog`, `typography`, `color_theory`
- The `template_catalog` playbook alone contains a 771-entry manifest (~40K chars)
- The design.md catalog adds another ~3K

### Fix
1. **Playbook summarization** — add a `load_playbook_summary(name, max_chars=4000)` function that returns a condensed version:
   - For `template_catalog`: only include the 16 archetype recipes (skip the 771-entry manifest)
   - For `slide_layouts`: include rules and decision trees, skip examples
   - For `typography` and `color_theory`: include rules only, skip reference tables

2. **Tiered loading in `_build_system_prompt()`**:
   ```python
   # Core playbook (full text, always included)
   CORE_PLAYBOOK = "slide_layouts"
   # Summary-only playbooks (condensed)
   SUMMARY_PLAYBOOKS = ["template_catalog", "typography", "color_theory"]
   ```
   - Include `SLIDE_TYPE_GUIDE` in full (it's only ~4.5K and critical)
   - Include `slide_layouts` in full (layout rules are essential)
   - Include other playbooks as summaries only
   - Include design.md catalog as-is (it's compact)

3. **Target**: system prompt under 30K chars (~10K tokens)

### Files to Modify
- `src/inkline/intelligence/playbooks/__init__.py` — add `load_playbook_summary()` with per-playbook condensation
- `src/inkline/intelligence/design_advisor.py` — use tiered loading in `_build_system_prompt()`

---

## Fix 3: _esc() and Renderer Type Safety

### Problem (Partially Fixed)
The `_esc()` function in `slide_renderer.py` was updated to handle dicts and non-strings. However, the flattened dict text `"key: value, key2: value2"` can contain characters that break Typst markup in certain contexts (commas inside grid arguments, special chars in table cells).

### Current State
- `_esc()` now converts dicts to `", ".join(f"{k}: {v}" ...)` and non-strings via `str()`
- This handles the crash but produces ugly output for dict items in content slides

### Remaining Fix
1. **Smarter dict rendering** — when `_esc()` receives a dict, format it as a multi-line entry:
   - For items with `title`/`name` + `body`/`detail`/`value` keys: render as `"**{title}** — {detail}"`
   - For items with `risk`/`action` + `severity`/`priority`: render as `"{risk} [{severity}]"`
   - Fallback: `"key1: val1; key2: val2"` (semicolons instead of commas to avoid Typst grid issues)

2. **Type validation in each slide builder** — add a `_ensure_string_items(items)` helper that normalizes a list of mixed str/dict items into strings before rendering:
   ```python
   def _ensure_string_items(items: list) -> list[str]:
       result = []
       for item in items:
           if isinstance(item, str):
               result.append(item)
           elif isinstance(item, dict):
               # Extract meaningful display string
               name = item.get("title") or item.get("name") or item.get("well") or item.get("action") or item.get("risk") or ""
               detail = item.get("body") or item.get("detail") or item.get("value") or item.get("status") or ""
               if name and detail:
                   result.append(f"{name} — {detail}")
               elif name:
                   result.append(name)
               else:
                   result.append("; ".join(f"{k}: {v}" for k, v in item.items()))
           else:
               result.append(str(item))
       return result
   ```

3. **Apply in `_content_slide()`** and any other builder that iterates `items`.

### Files to Modify
- `src/inkline/typst/slide_renderer.py` — add `_ensure_string_items()`, update `_esc()` to use semicolons, apply in content/split builders

---

## Fix 4: Rules-Mode Content Analysis for Dict Items

### Problem
When the rules-based fallback is used (no LLM), sections with dict items are misclassified:
- `content_analyzer.py` counts dict items as single data points without understanding their structure
- `layout_selector.py` routes based on flat counts, not dict shapes
- Result: rich card-like data gets dumped into plain `content` slides

### Root Cause
- `analyze_content()` checks `items = section.get("items", [])` and counts `len(items)` — doesn't inspect item type
- No recognition of card patterns (`[{"title": ..., "body": ...}]`), risk patterns (`[{"risk": ..., "severity": ...}]`), or timeline patterns (`[{"date": ..., "label": ...}]`)

### Fix
1. **Pattern detection in `content_analyzer.py`**:
   ```python
   # After extracting items, classify their shape
   if items and isinstance(items[0], dict):
       item_keys = set(items[0].keys())
       if {"title", "body"} <= item_keys or {"name", "body"} <= item_keys:
           # Card-shaped items → suggest three_card/four_card/feature_grid
           content_type = ContentType.COMPARISON  # or a new CARD_LIST type
       elif {"date", "label"} <= item_keys or {"timing", "label"} <= item_keys:
           content_type = ContentType.FLOW  # timeline
       elif {"risk", "severity"} <= item_keys or {"action", "priority"} <= item_keys:
           content_type = ContentType.RISK
       elif {"label", "value"} <= item_keys or {"label", "pct"} <= item_keys:
           content_type = ContentType.RANKING  # bar_chart or progress_bars
   ```

2. **Layout selector updates** in `layout_selector.py`:
   - When `ContentType.COMPARISON` with exactly 3 dict items → `three_card`
   - When `ContentType.COMPARISON` with exactly 4 dict items → `four_card`
   - When `ContentType.COMPARISON` with 5-6 dict items → `feature_grid`
   - When `ContentType.FLOW` with dict items → `timeline` or `process_flow`
   - When `ContentType.RISK` → `comparison` or `split`

3. **Section-to-slide builder** in `design_advisor.py` `_section_to_slide()`:
   - Add builders for dict items: extract `title`/`body` from dicts to populate card/feature_grid data
   - Map dict item keys to the expected slide data schema

### Files to Modify
- `src/inkline/intelligence/content_analyzer.py` — add dict item pattern detection
- `src/inkline/intelligence/layout_selector.py` — add routing rules for dict item patterns
- `src/inkline/intelligence/design_advisor.py` — add rules-mode builders for dict-based slides

---

## Implementation Order

1. **Fix 3** (type safety) — smallest change, unblocks rendering
2. **Fix 1** (missing images) — prevents crashes during testing
3. **Fix 2** (prompt size) — enables bridge-based LLM calls
4. **Fix 4** (rules-mode analysis) — improves fallback quality

## Verification

After all four fixes:
1. `pytest tests/ -q` — all 75 tests still pass
2. Run `scripts/generate_corsair_dd_deck.py` — should produce PDF without crashes
3. Bridge call should complete within 120s (system prompt < 30K chars)
4. Rules fallback should produce visually varied deck (not all `content` slides)
