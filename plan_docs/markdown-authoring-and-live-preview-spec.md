# Markdown Authoring & Live Preview — Specification

**Date:** 26 April 2026
**Status:** Proposed
**Author model:** Opus
**Depends on:** `inkline-standalone-app-spec.md` (bridge + MCP + CLI), `two-agent-design-loop-spec.md` (per-slide design hook), `design-system-spec.md` (brand registry)
**Inspired by:** Marpit directive grammar + marp-cli watch architecture (see Appendix A for source citations)

---

## 1. Problem

Inkline today has two authoring surfaces and neither is ergonomic for a human editor:

1. **Bridge `/prompt`** — the user uploads a markdown file and writes a natural-language prompt; Claude agentic mode does the rest. Excellent for cold-start drafting, but every change re-runs the full 4-phase Archon pipeline (parse → design → save → export+audit), and the user has no way to *override* a slide-type decision short of asking Claude in chat.
2. **MCP `inkline_render_slides`** — accepts a hand-built JSON spec list. Full control, but the user is editing JSON dicts of `{"slide_type": ..., "data": {...}}` — a hostile authoring surface for anyone who is not Claude.

Concretely, the gaps the codebase review surfaced:

- **No YAML front-matter parsing anywhere.** `mcp_server._text_to_sections()` (`src/inkline/app/mcp_server.py:244`) splits on `##`/`###` headings only — front-matter blocks survive as narrative text.
- **No per-section directive parser.** Inkline's `slide_mode` field (`auto` / `guided` / `exact` — `design_advisor.py:766`) is wired and works, but it is unreachable from markdown. Authors can only set it via the JSON path.
- **Bridge cannot be told brand/template via API.** `claude_bridge.py:491` accepts `{prompt, system?, mode?}` — brand/template default in DesignAdvisor, with no way to pin them per-deck without writing them into prose.
- **No live editor.** The WebUI (`src/inkline/app/static/index.html`, 672 lines) is a chat panel + pipeline tracker + PDF iframe. There is no markdown editor pane and no file watcher. The PDF refresh trigger (`checkForPdf()`, line 514) reloads the iframe when stdout emits `PDF ready: <path>`, but the path from "I edited a heading" → "I see the new PDF" still routes through chat.
- **Every change is a full-deck rebuild.** The Archon pipeline has no notion of patching a single slide.

Marp (see the comparison memo immediately preceding this spec) solves the first three of these for HTML/CSS-rendered tech-talk decks via three mechanisms: a tiered front-matter / HTML-comment **directive grammar**, an image-alt-text **layout shorthand**, and a chokidar + WebSocket **watch server**. None of those mechanisms requires Marp's HTML/CSS rendering model — they are authoring ergonomics, transferable to Inkline's typed-Typst pipeline as-is.

This spec defines those ports.

---

## 2. Goals & Non-goals

### Goals

- **Single-file deck source.** A `.md` file with optional YAML front-matter and inline HTML-comment directives is sufficient to fully specify a deck — brand, template, slide-type per section, layout overrides, audit strictness, **output targets (PDF and/or PPTX and/or Google Slides)** — with no JSON, no chat, no extra config flags.
- **Live preview loop under 5s for incremental edits** on a typical 12-slide deck (target P95).
- **Per-slide directive override** that bypasses LLM slide-type selection deterministically (maps to existing `slide_mode="exact"`).
- **Custom directive plugin API** so brand packages (`aigis`, `tvf`, …) can register their own author-facing directives without forking the parser.
- **Backwards-compatible.** A markdown file with no front-matter and no directives behaves exactly as today.

### Non-goals

- **Replacing the Archon agentic path.** Marp-style authoring is for the *human editor* path. Cold-start "give me a deck from this transcript" continues to route through `/prompt`.
- **Real-time collaborative editing.** Single-user editor only. Out of scope.
- **A new HTML renderer.** This spec does not introduce a new HTML renderer; HTML is listed in the `output:` directive only because Inkline already declares it as a backend (`typst/__init__.py:1044`). Live-preview rendering stays Typst → PDF. (See `gap-closure-spec.md` if a richer HTML preview becomes a goal later.)
- **Rebuilding only changed slides.** Full-deck recompile on every edit, same as marp-cli. Typst is fast enough; the per-slide vision audit is the dominant cost and is addressed separately in §7.
- **Marp markdown compatibility.** We borrow the *grammar shape*; we do not promise a `.marp.md` file can compile through Inkline.

---

## 3. Architecture overview

Three new modules + four touched files. The core insight is that the existing two-phase design loop and `slide_mode` field are the right hook points — directive parsing is a thin pre-processor that lowers markdown into the canonical sections-with-overrides shape DesignAdvisor already accepts.

```
            ┌──────────────────────────────────────────────────────┐
            │                  inkline/authoring/                  │  NEW
            │  ┌────────────────────┐   ┌────────────────────┐     │
            │  │  directives.py     │   │  preprocessor.py   │     │
            │  │  ─ grammar         │   │  ─ md → (meta,     │     │
            │  │  ─ scopes          │   │      sections[])   │     │
            │  │  ─ plugin registry │   │  ─ asset shorthand │     │
            │  └─────────┬──────────┘   └────────┬───────────┘     │
            └────────────┼───────────────────────┼─────────────────┘
                         │                       │
                         ▼                       ▼
       ┌──────────────────────────────────────────────────────────────┐
       │  DesignAdvisor.design_deck(sections=…, deck_meta=…)          │  TOUCHED
       │  ─ honours per-section slide_type + slide_mode (already done)│
       │  ─ accepts deck_meta {brand, template, audit_strictness…}    │
       └────────────────────────────┬─────────────────────────────────┘
                                    │
                                    ▼
       ┌──────────────────────────────────────────────────────────────┐
       │                       claude_bridge.py                       │  TOUCHED
       │  POST /render        — non-agentic: md text → PDF            │
       │  WS   /watch         — file-change → "reload" push           │
       │  POST /prompt        — unchanged, agentic path               │
       └────────────────────────────┬─────────────────────────────────┘
                                    │
                                    ▼
       ┌──────────────────────────────────────────────────────────────┐
       │              static/index.html (+ editor.js)                 │  TOUCHED
       │   Tab strip:  [ Chat ]  [ Editor ]                           │
       │   Editor tab: split-pane CodeMirror | iframe (live reload)   │
       └──────────────────────────────────────────────────────────────┘
```

Two CLI additions:
- `inkline render <file.md> [--watch] [--serve]` — non-agentic; pure preprocessor → DesignAdvisor → exporter. Used standalone or by the editor.
- `inkline watch <file.md>` — alias of `render --watch --serve`.

---

## 4. Directive grammar

### 4.1 Two surface syntaxes (pick one per file)

Front-matter, head of file only:
```markdown
---
brand: aigis
template: dmd_stripe
title: Q4 Strategy Review
audience: investors
audit: strict
---
```

HTML-comment, anywhere a markdown comment is legal:
```markdown
<!--
brand: aigis
template: dmd_stripe
-->
```

Both parse as YAML. Front-matter is preferred when the directive applies deck-wide; HTML-comment is preferred for mid-deck local/spot scope.

### 4.2 Three scopes

Following Marpit's underscore-prefix convention:

| Scope | Prefix | Where it can appear | Effect |
|---|---|---|---|
| **Global** | none | Front-matter, or HTML-comment **before any heading** | Whole-deck setting; last value wins |
| **Local** | none | HTML-comment after any heading | Cascades from this slide forward |
| **Spot** | `_` | HTML-comment inside a single section | Applies to *this* slide only |

Example:
```markdown
---
brand: aigis
template: consulting
footer: 'Confidential — Internal Only'
---

# Q4 Strategy Review

## Market opportunity
<!-- _layout: kpi_strip -->
TAM is $40B, growing 32% YoY. We hold 0.4% share today.

## Three problems we solve
<!-- _layout: three_card -->
- Fragmented data: analysts spend 80% of their week formatting.
- Manual reporting: a board pack takes two weeks.
- Stale insights: by the time it ships, the question has moved on.

## Section break
<!-- footer: '' -->     ← local: clears footer for the rest of the deck
<!-- _layout: section_divider -->
```

### 4.3 Built-in directive set

Names are deliberately Inkline-native, not Marp-aliased.

#### Global (deck-wide)
| Directive | Type | Default | Maps to |
|---|---|---|---|
| `brand` | string | `minimal` | `DesignAdvisor(brand=…)` |
| `template` | string | `consulting` | `DesignAdvisor(template=…)` |
| `mode` | `llm`\|`rules`\|`advised` | `llm` | `DesignAdvisor(mode=…)` |
| `title` / `subtitle` / `date` | string | — | Title-slide data |
| `audience` | string | — | DesignAdvisor heuristic input |
| `goal` | string | — | DesignAdvisor heuristic input |
| `paper` | `a4`\|`letter`\|`16:9`\|`4:3` | `16:9` | Typst page geometry |
| `audit` | `off`\|`structural`\|`strict` | `structural` | Audit strictness (see §7) |
| `headingDivider` | int 1–6 | `2` | Heading level that splits slides |
| `theme_overrides` | dict | `{}` | Inline brand-palette tweaks |
| `output` | list of `pdf`\|`pptx`\|`html`\|`google_slides`\|`png_thumbs` | `[pdf]` | Render targets (see §10 D4 — backend-coverage matrix governs downgrades) |

#### Local & spot (per-slide or cascading)
| Directive | Spot form | Effect |
|---|---|---|
| `layout` | `_layout` | Force `slide_type` (e.g. `three_card`, `kpi_strip`); implies `slide_mode="exact"` if all required data fields are derivable, else `"guided"` |
| `class` | `_class` | Space-separated class list applied as Typst show-rule keys (`lead`, `invert`, `dark`, `metric-hero`, …) — see §4.5 |
| `paginate` | `_paginate` | `true`\|`false`\|`hold`\|`skip` (four-state, mirrors Marp) |
| `header` / `footer` | `_header`/`_footer` | Override chrome strings |
| `accent` | `_accent` | Override per-slide accent colour from the brand palette |
| `bg` | `_bg` | Background image path or palette key |
| `notes` | `_notes` | Speaker notes — written to `<basename>.notes.txt` AND to PPTX `notes_slide` when PPTX is in `output:` (see §10 D2) |
| `mode` | `_mode` | Override `slide_mode` explicitly (`auto`/`guided`/`exact`) |
| `layout_<backend>` | `_layout_<backend>` | Backend-specific layout override (e.g. `_layout_pptx: table` — see §10 D4) |

### 4.4 Image / asset shorthand

The Marp `![bg left:40%](image.png)` shorthand is genuinely useful — it lets authors address layout slots declaratively without naming a slide type. Port it as:

```markdown
## Revenue trend
![bg left:40%](charts/revenue.png)
ARR compounding at 34% per quarter. Net revenue retention >120%.
```

The preprocessor sees `![bg left:40%](...)` in a section's body, infers `_layout: chart_caption` with `image_path` slot filled and the trailing prose as `caption + bullets`. Recognised tokens (whitespace-separated inside the alt-text):

| Token | Effect |
|---|---|
| `bg` | Switches alt-text into background mode (consumes remaining tokens) |
| `left[:N%]` / `right[:N%]` | Side and width hint; selects `chart_caption`, `dashboard`, or split-style layout |
| `cover` / `contain` / `fit` | Sizing |
| `w:Npx` / `h:Npx` | Explicit pixel hints (passed to Typst image function) |
| `blur:Npx` / `brightness:N` | CSS-style filters → Typst image processing |

Multiple consecutive `![bg ...]` images on one slide → `multi_chart` layout (`equal_2`/`equal_3`/`hero_left` chosen by count + width hints).

### 4.5 Class system (`_class` / `class`)

Inkline does not have CSS, but Typst supports `show` rules keyed off arbitrary metadata. The renderer reads the `class` field on each slide context and applies registered show-rule fragments:

```python
# In a brand plugin or theme registry
inkline.classes.register("lead", typst_fragment=r"""
  #show heading.where(level: 1): set text(size: 88pt, weight: 900)
  #show heading: set align(center)
""")
```

Authors then opt in with `_class: lead` or `_class: "lead invert"`. This gives lightweight slide variants (`lead`, `dark`, `metric-hero`, `quote-only`) without minting a new layout — the 22-layout count stays stable.

### 4.6 Custom directive plugin API

Brand packages register additional directives via:

```python
from inkline.authoring.directives import register

@register(scope="global", name="confidentiality_band")
def confidentiality_band(value, ctx):
    # value: string from front-matter
    # ctx: parsing context (brand, template, …)
    return {
        "header_overrides": {"text": value, "style": "ribbon-amber"},
        "footer_overrides": {"text": f"{value} — Do Not Distribute"},
    }

@register(scope="local", name="risk")
def risk(value, ctx):
    if value not in ("low", "medium", "high"):
        raise DirectiveError(f"risk must be low|medium|high, got {value}")
    return {"accent": {"low": "#2e7d32", "medium": "#ef6c00", "high": "#c62828"}[value]}
```

The callback returns a partial directive dict that is merged into the slide's resolved directive set. Local directives auto-honour the spot-prefix (`_risk: high` works for free).

This is a direct port of Marpit's `customDirectives` registry.

---

## 5. Preprocessor — markdown → (deck_meta, sections[])

New module: `src/inkline/authoring/preprocessor.py`.

### 5.1 Pipeline

```
raw markdown
  │
  ├─► 1. extract front-matter           → deck_meta_yaml
  ├─► 2. walk markdown AST              → blocks
  ├─► 3. for each block, classify scope → global / local / spot directives + content
  ├─► 4. apply headingDivider           → split into section list
  ├─► 5. parse asset shorthand          → infer _layout where omitted
  ├─► 6. apply spot/local cascades      → resolved per-section directives
  ├─► 7. run plugin directive callbacks → merged directive dicts
  └─► 8. emit (deck_meta, sections[])
```

Output shape — each section is the same dict DesignAdvisor already consumes today, with three new optional fields:

```python
{
  "type": "narrative",          # legacy field; still ignored by LLM, used by rules fallback
  "title": "Three problems we solve",
  "narrative": "...",
  "metrics": {"TAM": "$40B", ...},
  # NEW from directives:
  "slide_type": "three_card",   # from _layout
  "slide_mode": "guided",       # implied by _layout when fields incomplete
  "directives": {               # everything else: class, accent, bg, notes, paginate, …
    "class": "lead",
    "accent": "#0a8f5c",
    "notes": "Emphasise that 80% number — this is the wedge.",
  },
}
```

### 5.2 Markdown engine

`markdown-it-py` (already a transitive dep via several existing tools). Two reasons over alternatives:

- AST exposes HTML-comment tokens distinctly from prose, making directive extraction a clean filter step.
- The `front_matter` plugin is a one-line addition.

### 5.3 Validation

Each directive is validated at parse time against a JSON-schema-like spec. Unknown directive → warning printed to stderr, value preserved in `directives.unknown` for plugin authors to consume. Unknown directive does **not** fail the build.

A `--strict-directives` CLI flag promotes warnings to errors.

---

## 6. Bridge API additions

Touched file: `src/inkline/app/claude_bridge.py`.

### 6.1 New endpoint: `POST /render` (non-agentic)

```
POST /render
Content-Type: application/json
{
  "markdown": "<full md text>",       # OR "path": "/uploads/foo.md"
  "deck_meta_overrides": {...},       # optional: CLI flags equivalent
  "skip_audit": false                 # optional
}

→ 200 OK
{
  "pdf_path": "/output/deck.pdf",
  "spec_path": "/output/deck_spec.json",
  "warnings": [...],
  "audit": {"pass": 11, "fail": 1, "details": [...]}
}
```

Synchronous — runs the preprocessor → DesignAdvisor → exporter → audit chain in-process. **Does not** spawn `claude -p`. Intended for the editor pane and CI use.

Reuses the existing `/status` and `/progress` SSE streams for progress.

### 6.2 New endpoint: `WebSocket /watch?file=<path>`

Long-lived WebSocket. The bridge holds a `watchdog.Observer` per active connection, listens for changes on the named file (and any `import:`-referenced files — see §6.4), debounces 250ms, triggers `/render`, and pushes:

```json
{"event": "render_start"}
{"event": "render_done", "pdf_path": "/output/deck.pdf", "audit": {...}}
{"event": "render_error", "message": "..."}
```

Mirrors marp-cli's `WatchNotifier` design (chokidar → watchdog, `ws` → `websockets` library, single `"reload"` push → richer event envelope).

### 6.3 `/prompt` extensions (backwards-compatible)

Add three optional body fields:

```python
{"prompt": ..., "mode": ..., 
 "brand": "aigis",         # NEW
 "template": "dmd_stripe", # NEW
 "deck_meta": {...}}       # NEW: free-form overrides merged into front-matter
```

If any of these are present, they are injected into the system prompt Claude sees, AND into the eventual `DesignAdvisor.__init__` call. Today's calls without these fields keep working.

### 6.4 Multi-file imports

Front-matter directive `import: [shared_brand.md, shared_intro.md]` pulls in additional markdown blocks before parsing. The watcher follows imports and rebuilds when any imported file changes.

---

## 7. Live preview UX — WebUI editor pane

Touched file: `src/inkline/app/static/index.html` (+ a new `static/editor.js`).

### 7.1 Layout

Add a tab strip above the existing chat / pipeline / preview grid:

```
┌── Tabs ────────────────────────────────────────────────────────┐
│  [ Chat ]  [ Editor ]                                          │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  Chat tab: existing 3-col grid (chat | pipeline | iframe)      │
│                                                                │
│  Editor tab: 2-col grid (CodeMirror | iframe)                  │
│    ┌─────────────────────┬─────────────────────┐              │
│    │ # My deck           │                     │              │
│    │                     │   [PDF iframe]      │              │
│    │ ## First section    │                     │              │
│    │ <!-- _layout: ... → │                     │              │
│    │                     │                     │              │
│    └─────────────────────┴─────────────────────┘              │
│       │ status bar: ⬤ idle | rendering 8/12 | ✓ 3.4s  ⚠ 1     │
└────────────────────────────────────────────────────────────────┘
```

### 7.2 Editor

CodeMirror 6 (smaller, faster, ESM-clean — drop-in via CDN, no build step). Markdown mode + custom directive highlighting (recognise the front-matter block and the `<!-- -->` directive blocks; show the directive keys in a distinct colour).

Auto-completion from the registered directive set (built-ins + plugin-registered).

### 7.3 Save & render trigger

Two strategies, user-toggleable in a settings popover:

1. **Manual save:** Cmd/Ctrl-S → POST `/upload` → editor establishes WebSocket `/watch?file=<uploaded path>` → bridge re-renders on every subsequent save.
2. **Auto-render-on-pause:** 1.5s debounce after last keystroke → silent POST `/render` with the current buffer contents (no upload step). Skips audit (`skip_audit=true`) for speed; audit runs only on manual save or explicit "Audit now" button.

Both routes update the iframe via the existing `showPdf(filename)` path (`index.html:523`), with the `?t=<timestamp>` cache-bust already in place.

### 7.4 Audit feedback inline

When audit results arrive, the editor decorates source lines with gutter markers:

- Green ✓ on heading lines for slides that passed
- Amber ⚠ on heading lines for `WARN`-level findings
- Red ✗ on heading lines for `FAIL`-level findings
- Hovering the marker shows the audit message

This requires the audit output to carry a section-index → source-line-number map, threaded back through the preprocessor. Add `source_line_start` and `source_line_end` to each section dict; audit results already carry slide_index.

### 7.5 Scroll-sync

Two-way:
- Editor cursor enters a heading's section → iframe scrolls to that PDF page
- Iframe page change (via PDF.js page event) → editor scrolls source line into view

Implementation: PDF.js events on the iframe; CodeMirror has a `scrollIntoView` API and exposes cursor-line via the editor state.

### 7.6 Latency budget

Target end-to-end (keystroke → updated PDF visible) for a 12-slide deck:

| Stage | Budget |
|---|---|
| Debounce | 1500ms (configurable) |
| Preprocessor | <50ms |
| DesignAdvisor (`mode: rules` for live preview) | <200ms |
| Typst export | ~800ms typical |
| Iframe reload | <300ms |
| **Total (no audit)** | **~2.9s** |
| Audit (parallel post-load) | adds 4–8s, async |

`mode: llm` lifts DesignAdvisor cost into 30–60s — too slow for the live loop. The editor pane defaults to `rules` for in-flight previews and runs `llm` only on explicit "Re-design with LLM" button or final manual save.

### 7.7 Audit strictness levels (introduced in §4.3 `audit:` directive)

| Level | Behaviour |
|---|---|
| `off` | Skip vision audit entirely |
| `structural` | Capacity-limit checks only (existing `audit_deck()` from `intelligence/__init__`); fast, deterministic |
| `strict` | Full per-slide vision audit (existing `/vision` endpoint loop) |

Default `structural`. Editor pane uses `off` during typing and `structural` on save. CI / final exports use `strict`.

---

## 8. Migration & backwards compatibility

- Markdown files with no front-matter and no directives behave exactly as today (parser falls through to `_text_to_sections()`-equivalent behaviour).
- Existing `/prompt` calls without `brand`/`template`/`deck_meta` fields work unchanged.
- The MCP tool surface is untouched. Optionally, add a thin `inkline_render_markdown` MCP tool that wraps `POST /render` for callers that prefer markdown over JSON specs.
- `inkline serve` continues to launch the bridge + WebUI; the editor tab is additive.
- Existing `pitch_deck_v2.pdf` etc. regenerate identically because the JSON spec path is unchanged.

---

## 9. Phasing

### Phase 1 — Directive parser (1–2 days)
- `inkline/authoring/directives.py` — grammar, scopes, plugin registry
- `inkline/authoring/preprocessor.py` — markdown → (deck_meta, sections[])
- Unit tests against fixtures: front-matter only, comments only, mixed, asset shorthand, plugin directives
- `inkline render <file.md>` CLI subcommand using the new path
- **Deliverable:** identical PDF output to today for an unannotated file; new override-via-directive behaviour for annotated files

### Phase 2 — Bridge endpoints (1–2 days)
- `POST /render` — non-agentic synchronous render
- `WebSocket /watch` — file-watcher push
- `/prompt` extensions: `brand`, `template`, `deck_meta`
- Audit results carry `source_line_start/end` per slide
- **Deliverable:** `inkline render --watch --serve foo.md` opens browser, edits to `foo.md` reload PDF in <5s

### Phase 3 — WebUI editor (4–5 days)
- Tab strip + Editor tab
- CodeMirror 6 (vendored, no CDN) with directive highlighting + auto-completion
- Auto-render-on-pause + manual save modes
- Inline audit gutter markers (✓ pass, ⚠ warn, ✗ fail, ◐ downgrade)
- "Fix this slide" gutter action → `POST /redesign_slide` → CodeMirror diff overlay (D3)
- Scroll-sync (basic: cursor → page; defer page → cursor to a follow-up)
- Speaker-notes pane below iframe, served from `<basename>.notes.txt`
- **Deliverable:** browser-based editor end-to-end with one-click slide redesign

### Phase 4 — Class system, plugin API, and backend-coverage contract (3 days)
- `inkline.classes.register(name, typst_fragment)`
- Brand-package directive registration hook
- `inkline.authoring.backend_coverage` matrix + downgrade chains (§10 D4)
- `inkline backend-coverage` CLI subcommand
- CI test asserting every `slide_type` is in the matrix with either implementation or downgrade chain
- PPTX `notes_slide` writer + `_layout_<backend>` resolver
- Document the API in `CLAUDE.md` and add example to a private brand
- **Deliverable:** `aigis` brand registers `confidentiality_band` directive end-to-end; PPTX export honours grammar with documented downgrades

Total estimate: **9–12 working days** for one engineer.

---

## 10. Risks & resolved decisions

### Risks

1. **markdown-it-py vs the existing markdown handling.** Need to confirm the existing parser usage (if any) doesn't conflict. If `markdown-it-py` is not already a runtime dep, this adds one — acceptable.
2. **CodeMirror via CDN in the WebUI.** Existing static UI is dependency-free vanilla JS. CodeMirror via ESM CDN avoids a build step, but offline use breaks. **Decision:** vendor the CodeMirror bundle into `static/vendor/codemirror/` (~200KB). No CDN dependency at runtime.
3. **Live-render correctness with `mode: rules`.** The rules-mode DesignAdvisor produces lower-quality designs. Authors might think the live preview *is* the final output. Mitigation: show a clear "Live preview — rules mode" badge in the editor; require an explicit "Re-design with LLM" click before final export.
4. **WebSocket lifecycle on bridge restarts.** The current bridge has no graceful socket draining. Mitigation: emit a `{"event": "bridge_shutdown"}` message in the SIGTERM handler and have the editor auto-reconnect.

### Resolved decisions

The four open questions raised in the original draft of this spec have been resolved:

#### D1. `_layout` precedence with partial data → **LLM invents missing fields**

When the author writes `<!-- _layout: three_card -->` but the markdown body does not enumerate three card titles/bodies, the preprocessor sets:

```python
section["slide_type"] = "three_card"
section["slide_mode"] = "guided"   # NOT "exact"
```

`slide_mode="guided"` is the existing behaviour at `src/inkline/intelligence/design_advisor.py:766` — the LLM honours the forced `slide_type` but invents the missing data fields from the surrounding narrative + uploaded source documents. This is the **default** Inkline mental model anyway: the LLM constructs the deck from user-supplied materials. Authors who want to specify exact data inline can promote to `_mode: exact` plus the literal data:

```markdown
## Three pain points
<!--
_layout: three_card
_mode: exact
_cards:
  - title: Fragmented data
    body: Analysts spend 80% of their week formatting.
  - title: Manual reporting
    body: A board pack takes two weeks.
  - title: Stale insights
    body: By the time it ships, the question has moved on.
-->
```

`_mode: exact` plus structurally-incomplete data IS an error (caught at preprocessor validation time, not at render time).

#### D2. Speaker notes destination → **separate `notes.txt`**

`_notes:` content is collected during preprocessing and written to `<output_basename>.notes.txt` alongside the PDF. Format:

```
─── Slide 1 — Title slide ───────────────────────────────────────
(no notes)

─── Slide 2 — Three pain points ─────────────────────────────────
Emphasise the 80% number — this is the wedge.
Don't dwell on the second card; it's table-stakes.

─── Slide 3 — Our solution ──────────────────────────────────────
...
```

Why this over PDF backmatter or PDF annotations:
- **PDF backmatter** mixes presenter content with the audience artefact — bad if the deck is shared.
- **PDF annotations** require Typst PDF-annotation support that is currently limited and varies by viewer.
- **Separate file** keeps notes editable, greppable, and trivially shippable to a teleprompter/presenter app.

The bridge serves the notes file at `GET /output/<basename>.notes.txt`. The editor surfaces it in a collapsible "Speaker notes" pane below the iframe.

PPTX export route adds notes natively to each slide's `notes_slide.notes_text_frame` (python-pptx supports this directly) — see D4.

#### D3. Audit-gutter "fix this" button → **in scope, ships in Phase 3**

When an audit FAIL/WARN gutter marker is shown, hovering reveals a "Fix this slide" action. Clicking it:

1. Sends `POST /redesign_slide` with `{slide_index, audit_findings, current_spec, source_section}`
2. Bridge calls `DesignAdvisor.redesign_one()` (new method) — runs the LLM on a **single slide** with the audit critique injected as reviewer feedback (this is the per-slide hook designed in `two-agent-design-loop-spec.md`)
3. Returns the new slide spec
4. The slide is patched into the existing JSON spec; renderer re-exports the **whole PDF** (no incremental render — Typst is fast enough); audit re-runs on just that one slide
5. The editor diffs the markdown body for that section and offers the change as a non-destructive suggestion the author can accept/reject (CodeMirror diff overlay)

Endpoint addition to §6:

```
POST /redesign_slide
{
  "slide_index": 7,
  "audit_findings": [{"category": "...", "message": "...", "fix": "..."}],
  "current_spec": {...},
  "source_section": {...}
}
→ 200 OK
{
  "new_spec": {...},
  "suggested_markdown": "## ... rewritten section ...",
  "rationale": "Replaced 6-bullet wall with kpi_strip per audit suggestion."
}
```

This adds ~1 day to the Phase 3 estimate (now 4–5 days).

#### D4. PPTX & multi-backend grammar → **grammar is backend-agnostic by construction; coverage matrix governs runtime fallback**

Inkline already has multiple output backends, confirmed in the codebase:

| Backend | Module | Slide-type coverage |
|---|---|---|
| **Typst → PDF** | `src/inkline/typst/` | All 22 typed slide layouts |
| **PPTX** | `src/inkline/pptx/builder.py` (`PptxBuilder`) | 9 layouts: title, content, three_card, stat, table, split, four_card, chart, closing |
| **Google Slides** | `src/inkline/core/` (`SlideBuilder`) | Subset, varies |
| **HTML / PNG** | declared in `typst/__init__.py:1044`, partial | Varies |

The directive grammar in §4 is **already backend-agnostic** — directives compile to the canonical `[{slide_type, data, slide_mode, directives}]` shape that all four backends consume. To make this explicit and bake in the right contract, two additions:

**(a) New global directive: `output`** (§4.3 amendment)

```yaml
---
output: [pdf, pptx]        # render both; default is [pdf]
---
```

Acceptable values: `pdf`, `pptx`, `html`, `google_slides`, `png_thumbs`. The bridge `/render` endpoint accepts a matching `output: [...]` field; the response carries one path per requested format:

```json
{
  "outputs": {
    "pdf": "/output/deck.pdf",
    "pptx": "/output/deck.pptx"
  },
  "warnings": [...],
  "audit": {...}
}
```

**(b) Backend-coverage matrix + downgrade policy** (new module `src/inkline/authoring/backend_coverage.py`)

Each backend declares which `slide_type` values it implements. The preprocessor cross-references requested layouts against the coverage matrix:

| `_layout` | Typst | PPTX | Google Slides |
|---|---|---|---|
| `title` | ✓ | ✓ | ✓ |
| `three_card` | ✓ | ✓ | ✓ |
| `kpi_strip` | ✓ | ✗ | ✗ |
| `pyramid` | ✓ | ✗ | ✗ |
| `multi_chart` | ✓ | ✗ | ✗ |
| `feature_grid` | ✓ | ✗ | ✗ |
| `infographic_*` (16 archetypes) | ✓ | ✗ | ✗ |
| ...etc | | | |

When a backend is asked to render a slide whose layout it does not implement, the **downgrade policy** kicks in — declared per slide_type as an ordered fallback chain:

```python
DOWNGRADE = {
    "kpi_strip":     ["stat", "content"],
    "pyramid":       ["three_card", "content"],
    "feature_grid":  ["four_card", "content"],
    "multi_chart":   ["chart", "content"],
    "icon_stat":     ["stat", "content"],
    "infographic_iceberg":  ["chart", "content"],
    # …one row per layout PPTX/GS doesn't natively render
}
```

Behaviour:
- The Typst renderer always uses the requested layout (no downgrade — full coverage).
- PPTX/Google Slides walk the downgrade chain until they hit a supported layout. If they exhaust the chain, they emit a `content` slide with the raw narrative + a "downgraded from `<layout>`" footnote.
- Each downgrade is logged as a `WARN` warning in the response (`{"warning": "Slide 8 downgraded kpi_strip → stat for PPTX backend"}`).
- The editor's audit gutter shows a distinct "downgrade" marker (blue ◐) so authors know which slides will look different per backend.

**(c) Backend-specific spot directives**

For cases where the author *wants* a different layout per backend (e.g. a chart slide that becomes a table in PPTX because the chart image isn't easily editable):

```markdown
## Revenue trend
<!--
_layout: chart_caption
_layout_pptx: table          ← spot override for PPTX backend only
-->
```

`_layout_<backend>` overrides the default `_layout` when that backend is the active output target. Same pattern works for `_class_<backend>`, `_bg_<backend>`, etc.

**(d) Speaker notes are first-class in PPTX**

`_notes:` content goes to the separate `notes.txt` (D2) AND to `slide.notes_slide.notes_text_frame.text` in the PPTX export. python-pptx supports this directly — the `PptxBuilder` gains one shared helper. No grammar change.

**Coverage commitment**

To keep the contract honest, Phase 4 (newly added — see §9 amendment below) ships:
1. `inkline.authoring.backend_coverage` with the full matrix
2. `inkline backend-coverage` CLI subcommand to print the matrix as a table
3. CI test `tests/authoring/test_backend_coverage.py` that asserts every `slide_type` declared in `slide_renderer.py` appears in the matrix and either (a) is implemented by the backend or (b) has a downgrade chain
4. PPTX backend gains the `notes_slide` writer

This is the price of "backend-agnostic grammar" — the matrix is the spec's load-bearing artefact, not a nice-to-have.

---

## 11. What we are explicitly *not* taking from Marp

- **HTML/CSS rendering** — Inkline stays Typst-backed. No headless Chromium.
- **Marp theme files** — themes stay Inkline brand packages + Typst templates.
- **`@import` of CSS** — replaced by Inkline's brand-package model.
- **Inline SVG layout mode** — Typst handles layout; we don't need an inline-SVG escape hatch.
- **Marp markdown compatibility** — we share grammar shape, not a file format.

---

## Appendix A — Source citations

Marpit directive grammar:
- https://marpit.marp.app/directives
- https://marpit.marp.app/markdown
- https://raw.githubusercontent.com/marp-team/marpit/main/docs/image-syntax.md

marp-cli watch architecture (verified from source):
- `src/watcher.ts` (chokidar + WatchNotifier)
- `src/server.ts` (`http.Server` + WebSocket `upgrade` handler on path `/${WatchNotifier.webSocketEntrypoint}/<sha256>`)
- `package.json` deps (`chokidar` ^4.0.3, `ws` ^8.19.0, `portfinder`)
- Standalone-watch port 37717 default

marp-vscode preview:
- https://github.com/marp-team/marp-vscode (uses VS Code's built-in markdown-preview webview with Marp Core as the markdown-it engine)

## Appendix B — Codebase touch list

| File | Change |
|---|---|
| `src/inkline/authoring/__init__.py` | NEW package |
| `src/inkline/authoring/directives.py` | NEW — grammar + plugin registry |
| `src/inkline/authoring/preprocessor.py` | NEW — md → (deck_meta, sections[]) |
| `src/inkline/authoring/asset_shorthand.py` | NEW — `![bg ...]` parser |
| `src/inkline/authoring/classes.py` | NEW — class registry, Typst show-rule fragments |
| `src/inkline/authoring/backend_coverage.py` | NEW — slide-type × backend matrix + downgrade chains (§10 D4) |
| `src/inkline/authoring/notes_writer.py` | NEW — `<basename>.notes.txt` emitter (§10 D2) |
| `src/inkline/intelligence/design_advisor.py` | TOUCHED — accept `deck_meta`, honour pre-resolved `slide_mode`, add `redesign_one()` for D3 fix-this-slide flow |
| `src/inkline/pptx/builder.py` | TOUCHED — write `_notes` to `notes_slide.notes_text_frame`; honour `_layout_pptx` |
| `src/inkline/app/claude_bridge.py` | TOUCHED — `POST /render`, `POST /redesign_slide`, `WS /watch`, `/prompt` extensions, multi-output response shape |
| `src/inkline/app/cli.py` | TOUCHED — `inkline render` and `inkline watch` subcommands |
| `src/inkline/app/mcp_server.py` | TOUCHED (optional) — `inkline_render_markdown` tool wrapping `/render` |
| `src/inkline/app/static/index.html` | TOUCHED — tab strip |
| `src/inkline/app/static/editor.js` | NEW — CodeMirror, watch socket, scroll-sync, audit gutter |
| `src/inkline/app/static/editor.css` | NEW |
| `tests/authoring/` | NEW test package |
| `CLAUDE.md` | TOUCHED — document directive grammar + editor pane workflow |
