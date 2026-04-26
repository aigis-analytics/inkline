# Inkline Migration Guide — Execute-Mode Pivot

## What changed in the pivot (April 2026)

Inkline pivoted from "LLM-as-designer" to "Execution Engine + Knowledge Base."
The key behavioural changes are:

1. **`_layout` directives now default to `_mode: exact`** instead of `_mode: guided`.
   If you have markdown files with `_layout:` directives and want the old behaviour
   (renderer makes minor adjustments), add `_mode: guided` explicitly.

2. **`audit:` directive accepts a new value `post-render`** (was `off | structural | strict`).
   The full set is now `off | structural | post-render | strict`.

3. **`/health` endpoint now includes a `modes` object** alongside `cli_available`.
   Existing code that reads only `cli_available` is unaffected.

4. **New slide type: `freeform`** — accepted in `_layout:` directives with a
   `_shapes_file:` pointing to a JSON shapes manifest.

5. **`inkline knowledge`, `inkline validate`, `inkline critique`, `inkline draft`**
   are new CLI subcommands. All existing subcommands unchanged.

## How existing decks behave

### Existing markdown files with no `_layout:` directives

No change. The preprocessor applies `_mode: auto` (existing behaviour)
for sections without a layout directive.

### Existing markdown files with `_layout:` directives

If you have `<!-- _layout: three_card -->` in an existing file:
- The slide now defaults to `_mode: exact` (was `_mode: guided`)
- This means the renderer will not make layout adjustments
- **If the slide was relying on guided-mode to fill missing data**, add `_mode: guided` explicitly:
  ```
  <!-- _layout: three_card
  _mode: guided -->
  ```

### Existing `/prompt` calls

Unchanged. The `/prompt` agentic path continues to work exactly as before.
It is now labelled as "Draft Mode" in the documentation but the code is identical.

### Existing MCP tools

All existing MCP tools (`inkline_generate_deck`, `inkline_render_slides`, etc.)
are unchanged. New tools were added alongside them.

## How to opt into execute-mode benefits for an existing deck

1. Add `<!-- _layout: <slide_type> -->` to each section that should have an explicit layout
2. Run `inkline validate deck.md` to check for issues before rendering
3. Render with `inkline render deck.md --output pdf,pptx`
4. Optionally critique: `inkline critique deck.pdf --rubric institutional`

Claude Code can add `_layout:` directives automatically by reading the source
and the layout catalogue (`inkline knowledge get inkline://layouts`).

## Execute-mode vs Draft Mode — when to use each

| Scenario | Recommended path |
|---|---|
| You have source material and CC is writing the spec | Execute mode (`inkline render`) |
| You need a first-pass spec from raw markdown | Draft Mode (`/prompt` or `inkline draft`) |
| You want to iterate with CC on layout decisions | Execute mode — CC edits the spec directly |
| You don't have Claude Code available | Draft Mode — DesignAdvisor makes decisions |
| CI/CD pipeline, deterministic output required | Execute mode only |
| Quick cold-start from meeting notes | Draft Mode to get initial spec, then edit |
