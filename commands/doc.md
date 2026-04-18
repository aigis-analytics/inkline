---
description: >
  Generate a branded PDF document or report. Uploads the source file to
  the Inkline bridge and runs the Archon document pipeline.
user-invocable: true
allowed-tools:
  - Bash(curl *)
  - Bash(ls *)
  - Bash(python3 *)
---

# /inkline:doc — Generate a PDF Document

## Arguments

`$ARGUMENTS` accepts any combination of:

- `--brand <name>` — brand to use (e.g. `--brand aigis`). If omitted, defaults to `minimal` unless the natural language context implies a specific brand.
- `--template <name>` — template to use (e.g. `--template dmd_stripe`). If omitted, the bridge picks automatically.
- A file path (first non-flag token that looks like a path) — absolute or relative to the current working directory.
- Remaining natural language — paper size (`a4`, `letter`, `a3`), document title, subtitle, date, intended audience, or any other context to pass to the bridge (e.g. "a4, title: Q1 Board Update, date: April 2026").

Parse `--brand` and `--template` out of `$ARGUMENTS` first, then identify the file path, then treat the rest as extra context.

## Workflow

### Step 0 — Resolve arguments

Extract from `$ARGUMENTS`:
- `BRAND`: value after `--brand` if present, otherwise `minimal`
- `TEMPLATE`: value after `--template` if present, otherwise empty (omit from prompt)
- `FILE_PATH`: first token that is not a flag and looks like a file path
- `EXTRA_CONTEXT`: all remaining natural language after flags and file path are removed

If no file path is present in `$ARGUMENTS`, ask the user: "What file or content do you want to turn into a PDF document?" Do not proceed until a file or description is provided. If the user provides a description rather than a file, skip the upload step and include the description directly in the generation prompt.

If a file path was provided, resolve it to an absolute path:
```bash
python3 -c "import os; print(os.path.abspath('$FILE_PATH'))"
```

Confirm the file exists:
```bash
ls "$RESOLVED_PATH"
```

If the file is not found, tell the user and stop.

### Step 1 — Check the bridge

```bash
curl -s --max-time 3 http://localhost:8082/ | head -1
```

If the bridge does not respond, print exactly:

```
Bridge not running. Run `/inkline:setup` to start it.
```

Do not proceed without a live bridge.

### Step 2 — Upload the file

```bash
curl -X POST http://localhost:8082/upload -F "file=@$RESOLVED_PATH"
```

Parse the JSON response to extract the `path` field. Store as `UPLOADED_PATH`.

Example response: `{"path": "/home/user/.local/share/inkline/uploads/report.md", "filename": "report.md"}`

### Step 3 — Build and send the generation prompt

Construct the prompt string:

- Base: `"I have uploaded a file at: <UPLOADED_PATH>. Generate a branded PDF document from this content."`
- If BRAND is set: append `" Use brand: <BRAND>."`
- If TEMPLATE is set: append `" Use template: <TEMPLATE>."`
- If EXTRA_CONTEXT is non-empty: append `" <EXTRA_CONTEXT>."` (this is where paper size, title, subtitle, and date are passed as natural language)

Send the prompt:

```bash
curl -X POST http://localhost:8082/prompt \
  -H "Content-Type: application/json" \
  -d '{"prompt": "<constructed prompt>", "mode": "document"}'
```

### Step 4 — Report and wait

Tell the user:

"Generation started. Bridge is running the Archon document pipeline — this takes 60–120 seconds. Output will be at `~/.local/share/inkline/output/deck.pdf` when complete."

Do not send any further commands while the bridge is working. Do not attempt to monitor the bridge logs. The bridge will announce `PDF ready:` when the document is finished.
