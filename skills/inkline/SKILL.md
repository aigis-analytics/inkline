---
name: inkline
description: >
  Inkline workflow — bridge-first document and slide generation via the
  Archon 4-phase pipeline. Use when the user asks to generate slides, a
  deck, a presentation, a PDF report, or a branded document, or mentions
  creating a deck, building a presentation, making a PDF, chart generation,
  branded output, or using typst.
argument-hint: "[topic or file path]"
---

# Inkline Workflow Primer

## The one rule that overrides everything else

Never call `export_typst_slides()` or `export_typst_document()` directly. These functions exist in the Python package but must never be invoked outside the Archon pipeline. Calling them directly bypasses the per-page visual audit — the only gate that catches rendering failures, overflow, and brand violations. The bridge is not optional.

## The four-step mental model

Every generation job — slides or documents — follows exactly this sequence:

**Step 1 — Confirm the bridge is running.**
```bash
curl -s --max-time 3 http://localhost:8082/ | head -1
```
If the bridge does not respond, stop. Do not attempt to generate output. Tell the user to run `/inkline:setup` to diagnose and start the bridge.

**Step 2 — Upload the source file.**
```bash
curl -X POST http://localhost:8082/upload -F "file=@/absolute/path/to/file"
```
The response is JSON with a `path` field. Store that path — it is what you send in the prompt.

**Step 3 — Send the generation prompt.**
```bash
curl -X POST http://localhost:8082/prompt \
  -H "Content-Type: application/json" \
  -d '{"prompt": "I have uploaded a file at: <path>. Generate ...", "mode": "slides"}'
```
Use `"mode": "slides"` for decks and presentations. Use `"mode": "document"` for reports and PDFs.

**Step 4 — Wait. Do not intervene.**
The bridge runs Claude in agentic mode, executing the 4-phase Archon pipeline. This takes 60–120 seconds for a full deck. When it finishes, the bridge prints `PDF ready:` and the output appears at `~/.local/share/inkline/output/deck.pdf`. Do not send follow-up requests or attempt to monitor the process — the bridge owns the job from the moment the prompt is sent.

## Mode selection

- `"slides"` — for decks, presentations, pitch decks, investor materials
- `"document"` — for reports, memos, briefs, any branded PDF that is not a slide deck

## Output location

The session PDF is always written to `~/.local/share/inkline/output/deck.pdf`. After render the bridge prints `PDF ready: <path>`, which triggers the WebUI iframe to refresh automatically. Do not look for the file anywhere else.

## Slide title rule

Slide titles must be 50 characters or fewer. This is a hard limit — the renderer silently drops content that overflows when a title is too long. Count characters before writing. Titles should state a conclusion, not a topic label:

- Wrong: "Business Model Overview"
- Right: "98% gross margin at scale"
- Wrong: "The Problem"
- Right: "Analysts spend 80% of their week on formatting"

## Capacity limits

Every slide type has hard capacity limits — items beyond the limit are silently dropped by the renderer. When you are unsure how many items a slide type accepts, trust the DesignAdvisor to pick the right type for the content. If you are constructing slides manually, check the slide type catalogue in CLAUDE.md before specifying item counts.

## Brand selection

`minimal` ships with the package and is always available. Additional brands may be installed. To check what is available on the current machine:
```bash
python3 -c "from inkline.brands import list_brands; print(list_brands())"
```
Private brands (aigis, tvf, aria, statler, exmachina, sparkdcs) are available if the brands repo has been cloned to `~/.config/inkline/`. If only `minimal` appears, the user has a public install — that is fine for most use cases.

## When the bridge is not running

Do not attempt to generate anything. Do not call export functions directly as a workaround. The bridge is not an optimisation — it is a requirement. Tell the user to run `/inkline:setup`, which will attempt to start the bridge automatically. If the bridge cannot be started, the user must run `inkline serve` in a separate terminal and keep it running.

## When in doubt

If you are unsure which slide type to use, provide structured sections to the DesignAdvisor via the bridge prompt and let it decide. The DesignAdvisor is designed to pick the optimal layout from natural language descriptions. You do not need to specify slide types explicitly — only do so when the user has a strong preference or when amending an existing deck.
