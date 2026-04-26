# Execution Engine + Knowledge Base — Architectural Pivot Specification

**Date:** 26 April 2026
**Status:** Proposed — major architectural pivot
**Author model:** Opus
**Backup reference:** Tag `pre-execution-engine-pivot` (commit `1f7688c`); archive branch `archive/pre-execution-engine-pivot-2026-04-26`. Both pushed to origin. To restore: `git checkout pre-execution-engine-pivot`.
**Supersedes (in default behaviour):** `plan_docs/two-agent-design-loop-spec.md`, `plan_docs/vfep-visual-first-exhaustion-spec.md`, the LLM-design portions of `plan_docs/design-system-spec.md` and `plan_docs/impeccable-design-intelligence-spec.md`. Those specs remain valid for the **opt-in** agentic path (see §11).
**Builds on:** `plan_docs/markdown-authoring-and-live-preview-spec.md` (directive grammar, `_mode: exact`, `/render` endpoint, backend-coverage matrix). The pivot makes that spec's path the default rather than an alternative.

---

## 1. Problem

Inkline today is implicitly a Claude Code plugin — every documented entry point (`/prompt`, `/vision`, `inkline mcp`, the agentic 4-phase pipeline) routes through `claude -p` or another Claude/Anthropic call. Yet inside Inkline, a **second** LLM (DesignAdvisor in `mode="llm"`) is asked to perform the design work. This second Claude has strictly less context than the user's outer Claude Code session — no source-material access, no conversation history, no domain knowledge beyond a 35K-char system prompt.

The empirical consequence, demonstrated by the RadarSeq pitch deck on 2026-04-25–26:

- A direct python-pptx + matplotlib build piloted by Claude Code produced a faithful, polished 16-slide deck matching a benchmark Verisk reference, with bespoke hero exhibits, multimodal style anchoring, and accurate text in every image.
- Inkline's `/prompt` agentic path on the same source markdown produced a deck with no images (silent fallback when n8n was unavailable), arbitrary teal-filled cards, 60% empty space on multiple slides, comparison tables flattened to bullet lists, and the spec's explicit `slide_type` annotations ignored.

The same content + the same brief + the same model family — but the version where Inkline's internal LLM owned design decisions was materially worse than the version where Claude Code owned them.

The root cause is architectural, not a tuning issue: **Inkline's design intelligence is positioned where the weakest informed LLM sits, not where the strongest one does**. The 33K characters of accumulated playbooks, the 22-layout catalogue, the anti-pattern library, the brand system, the per-brand pattern memory — all of this is locked inside DesignAdvisor's prompt rather than exposed as referenceable knowledge that the user's Claude Code can consume during design.

This spec proposes inverting that relationship.

---

## 2. The pivot, named

**Inkline becomes two products that share a name and a codebase:**

1. **Execution Engine.** A deterministic, fast, no-LLM renderer. Given a structured slide spec (typed layouts plus a new `freeform` primitive), it produces a PDF, PPTX, Google Slides deck, or HTML. Image strategy is first-class: each image is either a path on disk, a multimodal-anchored generation request, or an explicit placeholder. Brand, theme, font, and typography systems are pure-Python and applied at render time. No Claude required — the rendering engine works as a standalone library, CLI, or MCP tool.

2. **Design Knowledge Base.** The accumulated playbooks, slide-type catalogue with capacity rules, anti-pattern library, infographic archetype index, design-inspiration corpus, and per-brand pattern memory — all surfaced as **machine-readable references** that Claude Code can pull into its context when authoring a deck. These are exposed primarily as MCP resources, secondarily as a versioned `inkline-knowledge` Python package, and tertiarily as raw markdown files on disk.

**Claude Code (driven by the user) becomes the design intelligence.** It reads the knowledge base, considers the user's source materials and brief, writes a precise spec, hands it to the execution engine, and (optionally) calls the execution engine's post-render audit tool to critique the output.

DesignAdvisor `mode="llm"`, the agentic `/prompt` flow, the two-phase plan+per-slide loop, and the Vishwakarma in-loop audit do not disappear — they become **opt-in**, labelled as the *Draft Mode* path for users who don't have Claude Code or who explicitly want Inkline to take design decisions.

---

## 3. Goals & non-goals

### Goals

- **Deterministic default path.** Same spec → same output, every time. No LLM in the layout-decision loop unless explicitly opted in.
- **Faithful execution.** When the spec says `_layout: split` with explicit content + image, the renderer produces exactly that. No reinterpretation, no silent layout substitution, no content reduction.
- **First-class image strategy.** Every slide that needs an image declares it explicitly: `path` (REUSE), `generate` (Gemini multimodal with reference anchor + region dimensions), or `placeholder` (deterministic, *visibly* a placeholder). Failures are loud, not silent.
- **Bespoke heroes supported.** A `freeform` slide_type accepts a positioned-shapes manifest, covering hero exhibits that don't match any of the 22 typed layouts (e.g., the RadarSeq workflow brainmap).
- **Knowledge base is a first-class product surface.** Playbooks, slide-type catalogue, anti-patterns, archetypes are exposed via MCP resources, queryable by domain / use-case / slide intent.
- **Backwards compatibility.** Every existing test passes. Existing markdown files render. Existing decks rebuild. The agentic `/prompt` path remains functional as opt-in Draft Mode.

### Non-goals

- **Replacing Claude Code.** Inkline does not implement its own CLI for talking to Anthropic's API. CC handles that. Inkline cooperates with whatever LLM the user has.
- **Becoming a designer's tool.** Inkline is for Claude Code piloting on behalf of a domain expert. Designers should use Figma. The audience is "engineer + analyst + AI agent producing institutional decks."
- **Maintaining the LLM-as-designer paradigm as default.** The pivot deliberately downgrades it.
- **Mass deletion.** The accumulated design knowledge is the moat — it is preserved, repositioned, and (where useful) extended. Code paths are kept and labelled as opt-in, not deleted.
- **Self-learning loop in default mode.** The pattern-memory feedback cycle was tied to the LLM-design path. It moves to the opt-in Draft Mode and partial-loss is accepted (see §10 D5).

---

## 4. Architecture overview

```
                            ┌──────────────────────────────────────────────┐
                            │  Claude Code (the user's session)            │
                            │  ─ has source materials + conversation       │
                            │  ─ pulls design knowledge from MCP           │
                            │  ─ writes spec.md (markdown + directives)    │
                            └────────────────────┬─────────────────────────┘
                                                 │
                ┌────────────────────────────────┼─────────────────────────────────┐
                │                                │                                 │
                ▼                                ▼                                 ▼
       ┌────────────────┐                ┌──────────────────┐               ┌──────────────────┐
       │  MCP server    │                │  Execution       │               │  Audit tool      │
       │  (knowledge)   │                │  Engine          │               │  (post-render,   │
       │  ─ playbooks   │                │  ─ preprocessor  │               │   opt-in)        │
       │  ─ layouts     │                │  ─ Typst render  │               │  ─ vision call   │
       │  ─ anti-       │                │  ─ PPTX render   │               │  ─ critique JSON │
       │    patterns    │                │  ─ image strategy│               │                  │
       │  ─ brands      │                │  ─ brand applier │               │                  │
       │  ─ archetypes  │                │  ─ no LLM        │               │                  │
       └────────────────┘                └──────────────────┘               └──────────────────┘
                                                 │
                                                 ▼
                                       ┌────────────────────┐
                                       │  PDF / PPTX /      │
                                       │  HTML / GSlides    │
                                       └────────────────────┘
                            ┌──────────────────────────────────────────────┐
                            │  OPT-IN: Draft Mode                          │
                            │  /prompt → claude -p → DesignAdvisor LLM     │
                            │  → Vishwakarma audit → render                │
                            │  Used when CC isn't available or user wants  │
                            │  Inkline to take design decisions            │
                            └──────────────────────────────────────────────┘
```

The default flow is left-to-right across the top: CC reads knowledge, writes spec, calls execution engine, optionally critiques output. The bottom box is the legacy agentic path, kept and labelled.

---

## 5. The Execution Engine

### 5.1 Public API surface

The engine is exposed three ways, all of which call the same core:

**Python library:**
```python
from inkline.execute import render_spec
result = render_spec(spec_path="deck.md", outputs=["pdf", "pptx"], brand="aigis")
```

**CLI:**
```bash
inkline render deck.md --output pdf,pptx --brand aigis
```

**MCP tool:**
```json
{"name": "inkline_render_spec",
 "args": {"spec_path": "deck.md", "outputs": ["pdf", "pptx"], "brand": "aigis"}}
```

All three paths are deterministic. No LLM call, no network call (except for image generation when `generate:` is present in the spec).

### 5.2 Spec format

Markdown with directive grammar (already shipped in `markdown-authoring-and-live-preview-spec.md`). Default mode for execute path is `_mode: exact` — the renderer honours the spec as written. Example:

```markdown
---
brand: radarseq
template: consulting
title: Q4 Strategy Review
output: [pdf, pptx]
audit: post-render-only
---

## What is RadarSeq
<!-- _layout: split
     _image:
       strategy: reuse
       path: assets/radar_morph.png
       slot: right
       width: 50%
-->
RadarSeq detects risk trajectories over time...

| Traditional | RadarSeq |
|---|---|
| Point-in-time scoring | Continuous temporal modelling |
| ... | ... |
```

Multiple things to note:
- `_layout: split` — explicit, no LLM picks for me.
- `_image:` is a structured directive (not just `![bg ...]` shorthand) — supports the three strategies plus per-image region dimensions.
- The markdown table is parsed into the split's right-side data structure; capacity limits are advisory warnings, not silent reductions.
- `audit: post-render-only` — no in-loop LLM critique; user can call `inkline_critique_pdf` later if they want.

### 5.3 New: `freeform` slide_type

The 22 typed layouts cover ~80% of slides in any institutional deck. The remaining ~20% are bespoke hero exhibits — RadarSeq slide 11's workflow infographic is canonical. `freeform` accepts a positioned-shapes manifest:

```python
{
  "slide_type": "freeform",
  "data": {
    "section": "Workflow",
    "title": "Predictive Risk Intelligence Workflow",
    "shapes": [
      {"type": "image", "path": "assets/verisk_slide3_overlay.png",
       "x": 0, "y": 0, "w": 100, "h": 100, "units": "pct"},
      {"type": "rounded_rect", "x": 5, "y": 80, "w": 90, "h": 8,
       "fill": "#1A2B4A", "radius": 0.5, "units": "pct"},
      {"type": "text", "x": 50, "y": 84, "w": 90, "h": 4,
       "text": "RadarSeq shifts risk management from reactive to proactive.",
       "font": "Calibri", "size": 14, "color": "#FFFFFF",
       "anchor": "mc", "units": "pct"}
    ]
  }
}
```

In markdown directive form:
```markdown
## Workflow
<!-- _layout: freeform
     _shapes_file: shapes/slide11_workflow.json
-->
```

`shapes_file` resolves a JSON file with the shape list. Renderable by both Typst (via `place()` calls) and PPTX (via PptxBuilder's existing positioned-shape methods). Bridges the gap between "use a typed layout" and "drop into python-pptx for one slide."

### 5.4 Image strategy as first-class concept

Each `_image:` directive carries a `strategy` field with one of three values, and the renderer enforces validation at parse time, not at compile time:

| Strategy | Behaviour |
|---|---|
| `reuse` | Path on disk. Validated at parse time — `FileNotFoundError` raised if missing. Resized to slot dimensions with explicit `fit` policy (`cover`/`contain`/`stretch`). |
| `generate` | Calls the multimodal Gemini endpoint shipped in `feat(generative-assets): wire multimodal Gemini endpoint with reference-image attachment` (commit `817a580`). Required: `prompt`, `reference_image_path` (optional but recommended), `region_width_px`, `region_height_px`. The region dims are passed *into* the Gemini prompt so the output is generated at native size, not resized. Cached by content hash so re-renders are free. |
| `placeholder` | Deterministic neutral box with a clear "[ Placeholder: <description> ]" label. Visibly a placeholder — not a fake-chart that might be mistaken for real content. |

Critically: **failure is loud**. If `reuse` points at a missing file, parse fails. If `generate` fails (network down, Gemini error), the slide spec is rejected with the actual error message — no silent PIL fallback, no "[Chart not available]" grey box that might be mistaken for completion.

### 5.5 Brand & theme application

Pure-Python, render-time. The brand registry, theme registry, font library, capacity-limit hints, and anti-pattern advisories all remain in the codebase exactly as today — but applied during rendering, not during a previous LLM-design pass.

Capacity limits become **warnings** rather than silent truncations or LLM-time constraints. If a `three_card` slide has 4 cards in the spec, the renderer warns and renders the first 3. This warning surfaces in the render result for CC to act on (either via spec correction or via accepting the truncation explicitly with `_capacity_override: true`).

### 5.6 Backend selection

`output: [pdf, pptx]` in front-matter (or `--output pdf,pptx` on CLI) drives multi-backend rendering. The backend-coverage matrix shipped earlier (`src/inkline/authoring/backend_coverage.py`) handles per-layout downgrades for backends that don't implement every layout. PptxBuilder gets equal status with the Typst renderer — both consume the same canonical spec.

---

## 6. The Knowledge Base

### 6.1 What it contains

Existing assets, repositioned:

| Asset | Today's role | Pivoted role |
|---|---|---|
| `intelligence/playbooks/*.md` | DesignAdvisor system prompt content | MCP resources + queryable knowledge corpus |
| `intelligence/template_catalog/*.md` | DesignAdvisor template-picker prompt | MCP resources, browsable by industry/audience |
| `intelligence/playbooks/slide_layouts.md` | Slide-type catalogue inside DesignAdvisor | MCP resource: `inkline://layouts` |
| `intelligence/playbooks/typography.md` | Typography rules for DesignAdvisor | MCP resource: `inkline://typography` |
| Brand registry (`brands/`) | Loaded at render time | MCP resource: `inkline://brands/<name>` |
| Theme registry (`typst/themes`) | Render-time | MCP resource: `inkline://themes/<name>` |
| Anti-pattern library | DesignAdvisor's mental constraints | MCP resource: `inkline://anti-patterns` |
| Infographic archetype index (16 types) | Renderer-internal | MCP resource: `inkline://archetypes` |
| Per-brand pattern memory | Self-learning loop input | MCP resource: `inkline://brands/<name>/patterns` |

The data does not move. Only the consumption pattern changes.

### 6.2 MCP resources & tools

The MCP server (`src/inkline/app/mcp_server.py`) gains a layer of resources alongside its existing tools. Resources are CC's preferred surface for "give me this knowledge" — they're cached at the protocol level and can be embedded directly into a CC context window without a tool round-trip.

**New MCP resources:**

| URI | Returns |
|---|---|
| `inkline://playbooks/index` | List of all playbooks with descriptions |
| `inkline://playbooks/<name>` | Full playbook markdown |
| `inkline://layouts` | Slide-type catalogue with data shapes + capacity limits |
| `inkline://layouts/<slide_type>` | Single slide-type spec with examples |
| `inkline://anti-patterns` | Anti-pattern library |
| `inkline://archetypes` | Infographic archetype index |
| `inkline://brands` | Available brands |
| `inkline://brands/<name>` | Brand palette + typography + asset paths |
| `inkline://themes` | Theme list |
| `inkline://themes/<name>` | Theme palette |
| `inkline://typography` | Type-scale + capacity rules |
| `inkline://templates` | Template catalogue |
| `inkline://templates/<name>` | Template detail |

**Refactored MCP tools** (the imperative-action surface):

| Tool | Purpose | Replaces / vs today |
|---|---|---|
| `inkline_render_spec` | Render a spec.md to one or more outputs | NEW — primary tool in pivot |
| `inkline_critique_pdf` | Post-render visual audit using vision API | NEW — repositioned Vishwakarma |
| `inkline_validate_spec` | Pre-render validation: image paths, capacity, schema | NEW — fail-loud at parse |
| `inkline_get_capacity` | Return capacity rules for a given slide_type (also via resource) | Convenience |
| `inkline_list_brands` | List registered brands (also via resource) | Convenience |
| `inkline_generate_deck` | EXISTING — kept, marked as Draft Mode | Opt-in agentic path |
| `inkline_render_slides` | EXISTING — JSON spec → PDF | Kept, becomes thin wrapper around `inkline_render_spec` |
| `inkline_submit_feedback` | EXISTING — feedback to learning loop | Kept, less central |
| `inkline_ingest_reference_deck` | EXISTING — analyse PDF for patterns | Kept, exposes results as MCP resource |
| `inkline_learn` | EXISTING — aggregate feedback | Kept, opt-in |

### 6.3 Knowledge corpus structure

The playbooks live as markdown today (`src/inkline/intelligence/playbooks/`). They stay there but gain:

- **Front-matter metadata** identifying domain, audience, slide-type relevance, brand affinity, last-updated date, contributors.
- **A central index** at `src/inkline/intelligence/playbooks/index.json` (generated, not hand-edited) that the MCP `inkline://playbooks/index` resource serves directly.
- **A versioned schema** for each playbook so future updates can be detected by the MCP layer and CC can refresh its context.

The core content is unchanged — the work to write 33K characters of design wisdom is preserved verbatim.

### 6.4 Inkline Standalone Knowledge Library (optional, future)

An exportable `inkline-knowledge` Python package containing only the corpus + a thin MCP-resource server, deliverable to users who want the knowledge but not the renderer. Out of scope for this spec but called out as a clean future product split.

---

## 7. Bridge changes

Touched file: `src/inkline/app/claude_bridge.py`.

### 7.1 New default front door: `/render`

Already shipped (Phase 2 of the markdown-authoring spec). Pivoted to be the **documented primary entry point** in CLAUDE.md and README.md.

### 7.2 `/prompt` becomes "Draft Mode"

Functionally unchanged — still spawns `claude -p` for the agentic 4-phase pipeline. But the response shape gains a `mode: "draft"` flag, the WebUI labels it clearly, and CLAUDE.md repositions it as "for cold-start drafting when CC isn't available or when you want Inkline to take design decisions."

### 7.3 New: `POST /critique` endpoint

Wraps the existing `/vision` per-slide audit into a deck-level post-render critique:

```
POST /critique
{
  "pdf_path": "/path/to/deck.pdf",
  "rubric": "institutional",      // or "tech_pitch", "internal_review"
  "brand": "aigis"
}
→ 200 OK
{
  "overall_score": 87,
  "slide_critiques": [
    {"slide_index": 1, "verdict": "PASS", "comment": "Strong action title."},
    {"slide_index": 7, "verdict": "WARN", "comment": "Wall of bullets — consider chart_caption.", "fix_hint": "_layout: chart_caption"}
  ]
}
```

This is the post-render audit moved from "in-loop and mandatory" to "explicit and opt-in." CC calls it after rendering, decides whether to act on critiques, and either accepts or iterates the spec.

### 7.4 New: `GET /knowledge/<resource>` proxies

For users without MCP, the bridge exposes the same knowledge resources over HTTP:

```
GET /knowledge/playbooks/institutional_finance
GET /knowledge/layouts/three_card
GET /knowledge/brands/radarseq
```

Returns the same content as the MCP resource. Convenient for tooling, scripts, and the WebUI editor's auto-completion.

### 7.5 Health check expansion

`GET /health` extended with `mode` field reporting which paths are available:

```json
{
  "status": "ok",
  "modes": {
    "execute": true,
    "draft": true,
    "critique": true
  },
  "cli_available": true,
  "cli_version": "2.1.119 (Claude Code)"
}
```

When `cli_available` is false, `draft` and `critique` are reported as false too — execute mode keeps working without Claude Code.

---

## 8. CLI changes

Touched file: `src/inkline/app/cli.py`.

| Subcommand | Status |
|---|---|
| `inkline render` | Already exists (markdown-authoring spec). Pivoted to be **the** documented primary command. |
| `inkline serve` / `inkline bridge` | Unchanged. |
| `inkline mcp` | Unchanged signature; gains the new resource layer. |
| `inkline critique <pdf>` | NEW — calls `/critique` or runs locally if CC available. |
| `inkline knowledge` | NEW — browse the knowledge corpus from CLI. Subcommands: `list`, `get <resource>`, `search <query>`. |
| `inkline validate <spec>` | NEW — pre-render schema + asset validation. |
| `inkline draft <input>` | NEW — explicit alias for `inkline serve` Draft Mode flow; makes the opt-in path discoverable. |

---

## 9. Phasing

Five phases. Each phase ships independently and the suite stays green throughout. Phase 1 alone delivers ~70% of the user-visible value.

### Phase 1 — Make execute-mode the documented default (1–2 days)

- Update `CLAUDE.md` to lead with `inkline render` / `/render` as the primary path; reposition `/prompt` as Draft Mode.
- Update `README.md` with the new framing.
- Add `mode` field to `/health` response.
- Add `audit: off|structural|post-render|strict` directive (extends the `audit:` directive shipped in markdown-authoring spec).
- Default `_mode` for `/render` is `exact` when `_layout` is specified; falls back to `auto` only when no layout is given (preserves the "rules can pick" path for sparse specs).

**Deliverable:** without writing new code, the documentation says "use `/render` first." This alone redirects CC's behaviour because CLAUDE.md is the system prompt.

### Phase 2 — `freeform` slide_type + image strategy (3–4 days)

- New file `src/inkline/typst/slide_types/freeform.py` — Typst renderer for the positioned-shapes manifest.
- Extension of `src/inkline/pptx/builder.py` — corresponding PPTX renderer.
- New file `src/inkline/authoring/image_strategy.py` — parses `_image:` directives, validates paths, calls multimodal Gemini for `generate`, emits placeholder for `placeholder`. Caches by content hash.
- Schema validation extension in `src/inkline/authoring/preprocessor.py`.
- Tests for both backends + image strategies.

**Deliverable:** a markdown spec like the RadarSeq one renders correctly via `inkline render` with all images in the right places.

### Phase 3 — Knowledge base as MCP resources (2–3 days)

- New file `src/inkline/app/mcp_resources.py` — resource registry + URI dispatch.
- Extend `src/inkline/app/mcp_server.py` to register all resources from the table in §6.2.
- Generate `src/inkline/intelligence/playbooks/index.json` from playbook front-matter (build step, not runtime).
- Add front-matter to existing playbooks (one-shot migration).
- New tools: `inkline_render_spec`, `inkline_critique_pdf`, `inkline_validate_spec`.
- Add `GET /knowledge/<resource>` HTTP proxies on the bridge.
- New CLI: `inkline knowledge`, `inkline validate`, `inkline critique`.
- Tests for resource enumeration + content fetch.

**Deliverable:** CC can ask for `inkline://playbooks/institutional_finance` and get the full playbook in its context. CC writes specs informed by the actual knowledge.

### Phase 4 — Repositioning Vishwakarma (1–2 days)

- Move Vishwakarma audit from in-loop (inside `/prompt`'s 4-phase pipeline) to post-render (called via `/critique` or `inkline critique`).
- Output structure changes from "warnings to retry the LLM with" to "verdicts CC can interpret."
- Per-slide `fix_hint` field in the response — gives CC actionable suggestions like `_layout: chart_caption` rather than free-form advice.
- The Vishwakarma agent code stays — only its position in the pipeline changes.

**Deliverable:** post-render critique is an explicit user/CC action. No silent LLM retries.

### Phase 5 — Documentation, examples, opt-in labelling (1 day)

- Update CLAUDE.md to describe Draft Mode as opt-in clearly.
- New `examples/` directory with three reference specs: a typed-layout deck, a freeform hero deck, a hybrid deck with both.
- Migration note: existing decks built via the agentic path keep working; users wanting to repivot rebuild via `inkline render`.
- Mark `intelligence/two_phase_*`, `intelligence/vfep_*`, and similar LLM-loop-specific modules with module-level docstrings noting "used only in Draft Mode."

**Deliverable:** clear, opinionated documentation. New users reach for `inkline render` first.

**Total estimate:** 8–12 working days for one engineer.

---

## 10. Risks & resolved decisions

### D1. Self-learning loop atrophies
**Risk.** The pattern-memory feedback mechanism is keyed on "user accepted/rejected/modified slide N" signals from the LLM-design path. Less signal in execute-mode.
**Resolution.** Accept partial loss. Add a lightweight `_user_overrode_layout: original→corrected` annotation that CC can append to specs after iteration; the existing learning aggregator picks these up. Not a full replacement but preserves the signal.

### D2. CC-less users have a degraded product
**Risk.** Without Claude Code, the user has Inkline as a renderer with no design guidance.
**Resolution.** Three mitigations:
- (a) Draft Mode (the agentic `/prompt`) remains fully functional, just opt-in; CC-less users have it.
- (b) `inkline knowledge` CLI lets a human browse the corpus directly without CC.
- (c) Rules-mode DesignAdvisor (existing, deterministic) continues to handle the "I have no spec, just sections" path.

### D3. The 22-layout investment becomes "advisory primitives"
**Risk.** Capacity-limit work, slide-type catalogue, anti-pattern library — all built to constrain the LLM. In execute-mode they're warnings, not enforced.
**Resolution.** The work is preserved and *more* exposed. Capacity limits become per-layout schema validators (parse-time errors when violated) plus advisory hints in the MCP resources. The anti-pattern library moves from "DesignAdvisor avoids these" to "MCP resource CC consults" — same content, broader audience.

### D4. The "AI deck designer" market positioning shifts
**Risk.** Inkline-as-execution-engine looks less impressive in a 30-second demo than Inkline-as-AI-designer.
**Resolution.** The pivot trades demo-wow for production-reliability. The empirical evidence (RadarSeq v1 vs the matplotlib build) makes the case. Demo narrative becomes "Claude Code + Inkline produces decks that look like McKinsey made them" — that's stronger, not weaker, than "Inkline alone produces… something."

### D5. Vishwakarma in-loop retry was catching real problems
**Risk.** Today, when a slide fails audit, the LLM re-tries with critique — sometimes producing better output.
**Resolution.** The same critique now reaches CC, which has more context and tooling than DesignAdvisor's internal retry loop. Empirically, CC's iteration is better than DesignAdvisor's. The two-phase loop's value was in the loop existing, not in *who* was iterating.

### D6. Existing decks built via agentic path will diverge from any rebuild
**Risk.** If a user rebuilds an old deck with `inkline render`, output may differ from the original.
**Resolution.** Acceptable — output divergence in execute-mode is *better* output. The original agentic-mode files are preserved on disk; the rebuild is an explicit user action.

### D7. Scope is large; partial deployment risks confusion
**Risk.** If only Phase 1 ships, users see new docs but old behaviour.
**Resolution.** Phase 1 changes default behaviour (via the `_mode` defaulting + audit defaulting changes), so even Phase-1-only delivers concrete behaviour change. Phases 2–5 each ship independently with clear deliverables.

### Open questions

- **Draft Mode discoverability.** Should `inkline serve` open the Editor tab by default and chat as a smaller pane, signalling that execute is primary? Probably yes; defer to Phase 5.
- **Knowledge corpus versioning.** Should playbook updates trigger a version bump in MCP resources so CC can detect staleness in long-running sessions? Yes, but defer the cache-invalidation work to a follow-up.
- **External knowledge contribution.** Should the knowledge corpus accept third-party playbooks (e.g., a user contributing an "industrial-products" playbook)? Out of scope for this spec; revisit once the resource layer is shipped.

---

## 11. What is preserved, what is repositioned, what is dormant

### Preserved (no change)

- Brand system (`src/inkline/brands/`)
- Theme registry (`src/inkline/typst/themes/`)
- Font library (`src/inkline/typst/fonts/`)
- Typst slide renderer (`src/inkline/typst/slide_renderer.py`)
- Document renderer (`src/inkline/typst/document_renderer.py`)
- Chart renderer (`src/inkline/typst/chart_renderer.py`)
- PptxBuilder (`src/inkline/pptx/builder.py`)
- Authoring layer (`src/inkline/authoring/`) — directive grammar, preprocessor, classes, backend coverage, notes writer
- All 22 typed slide layouts and their capacity rules
- The 16 infographic archetypes
- Audit-deck overflow checks (`src/inkline/intelligence/audit_*`)

### Repositioned (same code, different default role)

- DesignAdvisor `mode="llm"` → Draft Mode opt-in
- Vishwakarma audit → post-render `/critique` (called explicitly)
- `/prompt` agentic path → Draft Mode endpoint, kept fully functional
- Two-phase plan + per-slide design loop → only runs in Draft Mode
- VFEP plan auditor with retries → only runs in Draft Mode
- Self-learning feedback aggregator → optional, with reduced signal
- Playbooks → MCP resources for CC, plus DesignAdvisor system-prompt content for Draft Mode

### Dormant but kept (in case the LLM-as-designer paradigm comes back)

- The 4-phase Archon pipeline structure
- Plan auditor retry policies
- The `archon_bypassed` detection logic in the bridge
- The Implicit feedback detection (`claude_bridge.py:327-441`)

Each of these gets a module-level docstring noting "Draft Mode only — execute-mode does not invoke this."

---

## 12. Migration

### For users

1. Existing markdown source files render via `inkline render` without modification — they fall back to rules-mode for unannotated sections.
2. To get the full benefit of execute-mode, users add `<!-- _layout: ... -->` directives explicitly. CC can do this automatically by reading the source + relevant playbook.
3. Existing `/prompt` calls keep working, marked Draft Mode.
4. The WebUI auto-detects and surfaces both paths with clear labelling.

### For the codebase

1. Phase 1 documentation update is purely additive — no code deleted.
2. Phases 2–4 add new files and extend existing ones; no existing modules are rewritten.
3. Phase 5 adds module-level "Draft Mode only" docstrings — purely informational.

### For external integrations

The MCP server resource layer is additive. Existing tools (`inkline_generate_deck`, etc.) keep working. New tools are added alongside.

---

## 13. Backwards compatibility commitments

- **Test suite.** All 385 currently-passing tests must continue to pass at every commit. The new test files added by each phase bring the count to 450+ but don't replace any existing tests.
- **Public Python API.** `from inkline.intelligence import DesignAdvisor` keeps working with the same constructor signature. `from inkline.typst import export_typst_slides` keeps working.
- **CLI commands.** Every existing `inkline …` subcommand keeps its current signature and behaviour. New subcommands are added alongside.
- **MCP tool surface.** Every existing MCP tool name remains — no renames. New tools are added.
- **Bridge endpoints.** Every existing endpoint remains. New endpoints (`/critique`, `/knowledge/<resource>`) are added.
- **Markdown source files.** A markdown file that rendered through `/prompt` today renders through `inkline render` after the pivot, possibly with different output but never with errors. Existing front-matter and HTML-comment directives are honoured exactly as today.

---

## 14. Why this is the right pivot now

Three converging factors:

1. **Claude Code's session-context handling matured.** A year ago, asking CC to read 33K of playbook content and write a structured spec would have blown its context. Today it doesn't. The "let CC do the design" path is operationally viable.
2. **MCP became the right delivery surface.** The resource model (cacheable, addressable, versioned) is exactly what CC wants for design-knowledge consumption. A year ago, MCP didn't exist.
3. **Direct empirical evidence.** The RadarSeq build proved the gap concretely. We have a side-by-side comparison: same content, two paradigms, vastly different outcomes. The decision is not speculative.

The pivot does not concede that the LLM-as-designer paradigm was wrong. It concedes that **the right LLM** to do the design isn't the one inside Inkline — it's the one the user is already talking to. Inkline's job is to be the most useful tool *that LLM* can call.

---

## Appendix A — Codebase touch list

| File | Change | Phase |
|---|---|---|
| `CLAUDE.md` | Reposition `/render` as primary; label `/prompt` as Draft Mode | 1 |
| `README.md` | Same | 1 |
| `src/inkline/app/claude_bridge.py` | Extend `/health`; add `/critique`, `/knowledge/*`; update routing docstrings | 1, 3, 4 |
| `src/inkline/app/cli.py` | Add `inkline critique`, `inkline knowledge`, `inkline validate`, `inkline draft` | 3, 4 |
| `src/inkline/app/mcp_server.py` | Add new tools (`render_spec`, `critique_pdf`, `validate_spec`); register resources | 3 |
| `src/inkline/app/mcp_resources.py` | NEW — resource registry + URI dispatch | 3 |
| `src/inkline/typst/slide_types/freeform.py` | NEW — Typst renderer for positioned-shapes manifest | 2 |
| `src/inkline/typst/slide_renderer.py` | Dispatch `freeform` slide_type | 2 |
| `src/inkline/pptx/builder.py` | Add `freeform` rendering method | 2 |
| `src/inkline/authoring/preprocessor.py` | Schema validation for `_image:`, `_shapes_file:`; capacity warnings | 2 |
| `src/inkline/authoring/image_strategy.py` | NEW — parse, validate, fetch/generate, cache images | 2 |
| `src/inkline/authoring/freeform.py` | NEW — parse `_shapes_file:` JSON, validate against schema | 2 |
| `src/inkline/intelligence/playbooks/*.md` | Add front-matter metadata | 3 |
| `src/inkline/intelligence/playbooks/index.json` | NEW — generated index | 3 |
| `src/inkline/intelligence/vishwakarma.py` | Refactor for post-render usage; output `fix_hint` field | 4 |
| Module docstrings on `intelligence/two_phase_*`, `intelligence/vfep_*` | Add "Draft Mode only" note | 5 |
| `examples/` | NEW — three reference specs | 5 |
| `tests/test_freeform.py` | NEW | 2 |
| `tests/test_image_strategy.py` | NEW | 2 |
| `tests/test_mcp_resources.py` | NEW | 3 |
| `tests/test_critique_endpoint.py` | NEW | 4 |
| `tests/test_knowledge_cli.py` | NEW | 3 |

---

## Appendix B — Spec relationships

This spec sits above several existing specs. The hierarchy:

```
execution-engine-and-knowledge-base-pivot-spec.md  (this)
  ├── builds on:
  │     └── markdown-authoring-and-live-preview-spec.md  (directive grammar, /render, freeform foundation)
  ├── repositions as opt-in:
  │     ├── two-agent-design-loop-spec.md
  │     ├── vfep-visual-first-exhaustion-spec.md
  │     ├── design-system-spec.md (the LLM-design portions)
  │     └── impeccable-design-intelligence-spec.md (the LLM-design portions)
  ├── elevates / extends:
  │     ├── inkline-standalone-app-spec.md (bridge + MCP + CLI become primary product surface)
  │     ├── claude-plugin-spec.md (MCP resources are now the main offering)
  │     └── n8n-integration-generative-assets.md (image strategy formalises this work)
  └── leaves untouched:
        ├── design-tokens-spec.md
        ├── structural-fixes-v0.4-spec.md
        ├── ARCHON_AUDIT.md
        ├── CLOSED_LOOP_AUDIT_SPEC.md (still describes the audit machinery, just repositioned)
        ├── document-renderer-spec.md
        ├── orbital-halo-spec.md
        ├── branding-deck-and-assets-spec.md
        ├── inkline-self-learning-spec.md (loss of in-loop signal documented in §10 D1)
        └── visual-auditor-self-learning-spec.md
```

---

*End of spec. Ready for review and implementation. Total estimate 8–12 days. Backup tag `pre-execution-engine-pivot` is in place.*
