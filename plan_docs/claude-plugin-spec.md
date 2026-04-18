# Inkline Claude Code Plugin — Specification

**Status:** Proposed
**Model policy:** Opus (architecture/design)
**Date:** April 2026

---

## 1. Problem Statement

When a new user installs Inkline (`pip install inkline`) and opens Claude Code,
they face a cold-start problem: Claude has no awareness of the Archon pipeline
constraint, the bridge workflow, the slide type catalogue, or the "never call
export functions directly" rule. Without this context, Claude will:

- Call `export_typst_slides()` directly, bypassing the visual audit
- Skip the bridge upload/prompt pattern entirely
- Hallucinate slide types that don't exist
- Produce overflow-prone decks (wrong item counts, titles over 50 chars)
- Be unable to diagnose bridge-down situations

CLAUDE.md in the repo root solves this for developers working inside the repo.
But it does not help a user who has only `pip install`-ed the package, or who
is working in a different project directory where CLAUDE.md is not in scope.

The Claude Code plugin system solves exactly this problem: a user can run
`claude plugin add https://github.com/u3126117/inkline` once, and from that
point every Claude Code session has the Inkline workflow baked in — regardless
of working directory.

### What the plugin adds (user experience goal)

- Claude already knows the Archon pipeline constraint before the user says anything
- `/inkline:deck <file>` kicks off a deck generation in one command
- `/inkline:doc <file>` kicks off a document generation in one command
- `/inkline:setup` walks the user through prerequisites and bridge health
- Users who do not have the bridge running get a clear error and fix path, not
  a silent bypass

---

## 2. Scope

### In scope

- `.claude-plugin/plugin.json` — plugin manifest
- `skills/inkline/SKILL.md` — workflow/mental model skill (always injected)
- `skills/setup/SKILL.md` — bridge health check + fix skill
- `commands/deck.md` — `/inkline:deck` command
- `commands/doc.md` — `/inkline:doc` command
- `commands/setup.md` — `/inkline:setup` command

### Out of scope

- No changes to the Inkline Python package itself
- No MCP server (see Section 12 — What NOT to Build)
- No agent.md file (not needed until there is an autonomous background task)
- No changes to CLAUDE.md (it remains the full developer reference)
- No CI/CD or test changes
- No new Python code of any kind

---

## 3. File Structure

Add the following to the inkline repo root. Nothing else changes.

```
inkline/                          ← repo root (existing)
├── .claude-plugin/
│   └── plugin.json               ← plugin manifest
├── skills/
│   ├── inkline/
│   │   └── SKILL.md              ← workflow skill (always active)
│   └── setup/
│       └── SKILL.md              ← setup/health-check skill
├── commands/
│   ├── deck.md                   ← /inkline:deck command
│   ├── doc.md                    ← /inkline:doc command
│   └── setup.md                  ← /inkline:setup command
├── inkline/                      ← existing Python package (unchanged)
├── CLAUDE.md                     ← existing full reference (unchanged)
└── ...
```

No existing file is modified. All new files are plain Markdown or JSON.

---

## 4. `.claude-plugin/plugin.json` — Exact Content

```json
{
  "name": "inkline",
  "description": "Branded document and slide deck generation via the Inkline Archon pipeline. Teaches Claude the bridge workflow, slide type catalogue, and generation constraints. Provides /inkline:deck, /inkline:doc, and /inkline:setup commands.",
  "version": "0.1.0",
  "keywords": [
    "slides",
    "documents",
    "pdf",
    "presentation",
    "typst",
    "branded"
  ],
  "author": {
    "name": "u3126117",
    "url": "https://github.com/u3126117/inkline"
  }
}
```

### Notes on the manifest

- `name` must be lowercase, no spaces — `inkline` is correct
- `description` must be ≤200 chars for marketplace display truncation (this one
  is 199 chars — measure before finalising)
- `version` follows semver; increment when skill content changes meaningfully
- `keywords` aid discoverability in the marketplace browser
- No `mcp` key — this plugin has no MCP server component

---

## 5. `skills/inkline/SKILL.md` — Content Outline

### Purpose

This skill is the always-active context injection. It loads every session once
the plugin is installed, regardless of whether the user invokes a command. It
gives Claude the mental model needed to handle any Inkline-related request
correctly.

### Frontmatter

```yaml
---
name: inkline
description: >
  Inkline workflow — bridge-first document and slide generation via the
  Archon 4-phase pipeline. Use when the user asks to generate slides, a
  deck, a presentation, a PDF report, or a branded document.
---
```

### What goes in the skill (include)

**The constraint rule** (highest priority — must be first):
- Never call `export_typst_slides()` or `export_typst_document()` directly
- All output must flow through the bridge at `http://localhost:8082`
- Why: bypassing the bridge skips the per-page visual audit; the bridge
  is the only gate that catches rendering failures, overflow, and brand
  violations

**The four-step workflow** (the mental model, not the code):
1. Check bridge is running: `curl -s http://localhost:8082/ | head -1`
2. Upload source file: `curl -X POST http://localhost:8082/upload -F "file=@/path/to/file"`
3. Send generation prompt: `curl -X POST http://localhost:8082/prompt` with
   JSON body containing `prompt` and `mode` (`"slides"` or `"document"`)
4. Monitor logs — do not intervene; wait for `PDF ready:` announcement

**Mode selection**:
- `"slides"` — for decks, presentations, pitch decks
- `"document"` — for reports, memos, branded PDF documents

**Output location**:
- Session PDF always at `~/.local/share/inkline/output/deck.pdf`
- After render, `PDF ready: <path>` is printed — this triggers WebUI refresh

**Slide title rule**:
- Titles must be ≤50 characters — hard limit, longer titles push content off
- Write action titles that state the conclusion, not topic labels

**Capacity limits are hard** (brief mention to prime awareness):
- The renderer silently drops content beyond per-type limits
- When in doubt, use `/inkline:setup` to check the environment first

**Brand selection**:
- `minimal` ships with the package
- Additional brands may be available: check with
  `python3 -c "from inkline.brands import list_brands; print(list_brands())"`

**When the bridge is not running**:
- Do not attempt to generate output without the bridge
- Tell the user to run `inkline serve` or `inkline bridge` and wait for it
  to start on port 8082
- Offer to run `/inkline:setup` to diagnose the full environment

### What stays in CLAUDE.md (do not duplicate in skill)

- Complete slide type catalogue (22 types with full data shapes and limits)
- Chart type list (15 types + infographic archetypes)
- Template list (37 templates)
- Full Archon pipeline code patterns (Python code blocks)
- Input file handling (pandoc, python-docx, pymupdf, pptx extraction)
- Section building patterns
- DesignAdvisor option A and option B full examples
- Amending deck patterns
- Common patterns (quick deck from docx, add chart slide, change template)
- Troubleshooting table
- Theme system (90 themes, list/search API)
- Overflow audit API

### What to omit from the skill entirely

- Python code blocks (they belong in CLAUDE.md, not the always-on skill)
- The full 22-slide type catalogue (too long for injection; Claude will ask
  CLAUDE.md or the user when needed)
- Internal package implementation details
- Private brand names or configuration paths
- The spec table from CLAUDE.md

### Length target

The skill should be 400-600 words. It is a workflow primer, not a reference
manual. Users who need the full reference have CLAUDE.md.

---

## 6. `skills/setup/SKILL.md` — Content Outline

### Purpose

This skill is invoked by the `/inkline:setup` command and also loads as
context when a user mentions "setup", "install", "configure", or "bridge
not working". It walks through a deterministic checklist and gives concrete
fix commands for each failure mode.

### Frontmatter

```yaml
---
name: setup
description: >
  Inkline environment health check. Use when the user asks how to set up
  Inkline, reports the bridge is not running, or wants to verify the
  installation before generating output.
user-invocable: true
allowed-tools:
  - Bash(curl *)
  - Bash(python3 *)
  - Bash(pip *)
  - Bash(which *)
  - Bash(inkline *)
---
```

### Content: the checklist (what to check, in order)

**Check 1 — inkline installed**
Run: `python3 -c "import inkline; print(inkline.__version__)"`
- Pass: print version, continue
- Fail (`ModuleNotFoundError`): tell user to run `pip install inkline`; stop
  further checks until they confirm it's installed

**Check 2 — ANTHROPIC_API_KEY set**
Run: `python3 -c "import os; print('SET' if os.environ.get('ANTHROPIC_API_KEY') else 'MISSING')"`
- Pass: continue
- Missing: print the consequence (LLM mode will fail; `mode="rules"` is the
  fallback for deterministic output without an API key). Do not reveal or
  suggest storing the key in the skill — just tell the user to set it in
  their shell environment or `.env` file

**Check 3 — typst available**
Run: `python3 -c "import typst; print('ok')"` or `which typst`
- Fail: `pip install --upgrade typst`

**Check 4 — bridge health**
Run: `curl -s http://localhost:8082/ | head -1`
- Pass (returns any content): bridge is running, print "Bridge OK on port 8082"
- Fail (connection refused or empty): bridge is not running
  - Tell user to run `inkline serve` in a separate terminal (or `inkline bridge`)
  - Explain the bridge must stay running for the duration of any generation job
  - Do not attempt to start the bridge from within Claude Code

**Check 5 — available brands**
Run: `python3 -c "from inkline.brands import list_brands; print(list_brands())"`
- Print the list. If only `minimal` is present, note that private brands
  can be added by cloning the brands repo to `~/.config/inkline/`

**Summary output**
After all checks, print a one-line status table:
```
inkline: 0.x.x  |  API key: SET  |  typst: ok  |  bridge: OK  |  brands: [minimal]
```
Then print the next step: either "Ready — run /inkline:deck <file> to generate"
or a specific fix command.

---

## 7. `commands/deck.md` — Exact Content Spec

### File header (frontmatter)

```yaml
---
description: >
  Generate a branded slide deck from a document or description. Uploads
  the source file to the Inkline bridge and runs the Archon 4-phase pipeline.
user-invocable: true
allowed-tools:
  - Bash(curl *)
  - Bash(ls *)
  - Bash(python3 *)
---
```

### Command heading

```markdown
# /inkline:deck — Generate a Slide Deck
```

### Arguments

`$ARGUMENTS` — the path to the source file (required). May be:
- An absolute path: `/home/user/reports/q4.md`
- A relative path from the current working directory: `q4.md`
- Empty: if no file is provided, ask the user what content they want to turn
  into a deck, then proceed with a text prompt (no upload step)

### Workflow the command instructs Claude to follow

**Step 0 — resolve the file path**
If `$ARGUMENTS` is non-empty, expand to an absolute path:
```bash
python3 -c "import os; print(os.path.abspath('$ARGUMENTS'))"
```
Confirm the file exists: `ls "$RESOLVED_PATH"`. If not found, tell the user
and stop.

**Step 1 — check the bridge is alive**
```bash
curl -s --max-time 3 http://localhost:8082/ | head -1
```
If the bridge is not responding, print: "Bridge not running on port 8082. Start
it with `inkline serve` in another terminal, then re-run /inkline:deck."
Do not proceed without a live bridge.

**Step 2 — upload the file**
```bash
curl -X POST http://localhost:8082/upload \
  -F "file=@$RESOLVED_PATH"
```
Parse the JSON response to extract the `path` field. Store as `UPLOADED_PATH`.
Example response: `{"path": "/home/user/.local/share/inkline/uploads/q4.md", "filename": "q4.md"}`

**Step 3 — send the generation prompt**
```bash
curl -X POST http://localhost:8082/prompt \
  -H "Content-Type: application/json" \
  -d "{\"prompt\": \"I have uploaded a file at: $UPLOADED_PATH. Generate a branded slide deck from this document.\", \"mode\": \"slides\"}"
```
The bridge runs Claude agentic mode. This call will take 60-120 seconds for a
full deck. Do not send follow-up requests.

**Step 4 — wait and report**
The bridge streams output. Tell the user:
"Generation started. The Archon 4-phase pipeline is running — watch for
`PDF ready:` in the bridge logs. The output will appear at
`~/.local/share/inkline/output/deck.pdf`."

Do not attempt to monitor the bridge logs from within this command — the bridge
is an external process.

### Prompt augmentation

After the file path in the prompt, Claude may append additional context from
the user's request, for example:
- Brand: `"Use brand: minimal"`
- Template: `"Use template: dmd_stripe"`
- Audience: `"Audience: seed investors"`
- Goal: `"Goal: close the round"`

These are passed as natural language in the `prompt` field — the bridge's
Claude instance interprets them.

---

## 8. `commands/doc.md` — Exact Content Spec

### File header (frontmatter)

```yaml
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
```

### Command heading

```markdown
# /inkline:doc — Generate a PDF Document
```

### Differences from `/inkline:deck`

- `mode` is `"document"` instead of `"slides"`
- The prompt says "Generate a branded PDF document/report" instead of "slide deck"
- The user may optionally specify paper size: `a4` (default), `letter`, `a3`
- The user may optionally specify title, subtitle, date in natural language
  appended to the prompt

Everything else (file resolution, bridge health check, upload, prompt send,
wait-and-report) is identical to `commands/deck.md`. The implementation should
reference the same pattern, not duplicate the prose.

### Specific prompt template for mode: document

```bash
curl -X POST http://localhost:8082/prompt \
  -H "Content-Type: application/json" \
  -d "{\"prompt\": \"I have uploaded a file at: $UPLOADED_PATH. Generate a branded PDF document from this content.\", \"mode\": \"document\"}"
```

---

## 9. `commands/setup.md` — Exact Content Spec

### File header (frontmatter)

```yaml
---
description: >
  Check Inkline installation, API key, typst, bridge health, and available
  brands. Run this first if you encounter any errors.
user-invocable: true
allowed-tools:
  - Bash(curl *)
  - Bash(python3 *)
  - Bash(pip *)
  - Bash(which *)
  - Bash(inkline *)
---
```

### Command heading

```markdown
# /inkline:setup — Environment Check and Setup Guide
```

### Instruction to Claude

This command invokes the `setup` skill behaviour directly. Claude should:

1. Run all five checks from the `skills/setup/SKILL.md` checklist in order
2. Print results clearly after each check (pass / fail + fix command)
3. Stop at the first blocking failure (inkline not installed, bridge not up)
   and give the user a specific fix before proceeding
4. After all checks pass, print the one-line summary table and a "Ready" message

Arguments (`$ARGUMENTS`) are unused in this command — there are no sub-commands
for setup. If the user passes arguments, ignore them.

### Bridge-start note

If the bridge health check fails, Claude should print exactly:

```
Bridge not running. Start it:

    inkline serve

Keep that terminal open. Once you see "Inkline bridge running on port 8082",
re-run /inkline:setup or proceed with /inkline:deck <file>.
```

Do not attempt to start the bridge in the background from Claude Code. The
bridge is a long-running server that the user must own.

---

## 10. Integration Points

### CLAUDE.md and the plugin skill coexist without conflict

- CLAUDE.md is the full developer reference. It is in scope when Claude Code is
  opened in the inkline repo directory. It contains every detail: full slide
  type catalogue, pipeline code, templates, chart types, troubleshooting.
- The `inkline` skill is the workflow primer. It is always injected once the
  plugin is installed, regardless of working directory. It contains the mental
  model and constraints — not the implementation detail.
- When both are in scope (working inside the repo), the skill's constraints
  take precedence (they are shorter and loaded first), and CLAUDE.md provides
  the detailed reference Claude will consult as needed.
- The skill must not contradict CLAUDE.md. If a detail changes (e.g., a new
  bridge endpoint), update both CLAUDE.md and the relevant skill/command.

### What triggers which component

| User action | What activates |
|---|---|
| Asks about Inkline generally | `inkline` skill (always active) |
| Runs `/inkline:deck path/to/file` | `commands/deck.md` + `inkline` skill |
| Runs `/inkline:doc path/to/file` | `commands/doc.md` + `inkline` skill |
| Runs `/inkline:setup` | `commands/setup.md` + `setup` skill |
| Says "bridge not working" or "setup help" | `setup` skill (keyword-triggered) |
| Working inside the inkline repo | `CLAUDE.md` + `inkline` skill |

### Version drift

When Inkline adds new slide types, chart types, or templates, CLAUDE.md is the
primary update target. The skill only needs updating if the core workflow
constraint or bridge API changes. This keeps the skill stable and the
maintenance burden low.

---

## 11. Marketplace Submission

This section describes what would be needed to submit the plugin to
`claude-plugins-official` later. This is not a near-term goal — it is documented
so the plugin is built in a submission-ready way from the start.

### Repository structure requirements

- The plugin must be in its own standalone repository, or in a clearly
  delineated subdirectory of a larger repo
- For submission, a fork/copy of just the plugin files to a dedicated repo
  (e.g., `u3126117/inkline-claude-plugin`) would be the cleanest path
- Alternatively, the claude-plugins-official maintainers may accept a PR
  pointing at the plugin within the main inkline repo if the `.claude-plugin/`
  directory is at the root

### Prerequisites statement (honest)

The plugin's README must clearly state:

```
Prerequisites:
- Inkline installed: pip install inkline
- Anthropic API key set in environment (for LLM mode; rules mode works without)
- Bridge running: inkline serve (must be started separately, kept running)
- typst installed: pip install typst (or system typst)
```

Do not suggest the plugin works without the bridge. The `/inkline:setup`
command is the user-facing diagnostic, but the README must set expectations
upfront.

### PR description constraints (claude-plugins-official)

Based on the superpowers repo CLAUDE.md and the rejection rate documented
there (94%), a submission PR must:

- Fill every section of the PR template with real, specific answers
- Show evidence of testing across at least one platform (macOS or Linux)
- Not claim capabilities that require the user to have done setup (the
  plugin teaches the workflow; it does not replace the bridge)
- Include a clear "what this is not" section — specifically that it is
  skill-only, no MCP, and requires a running bridge
- Be submitted only once the plugin has been tested by a real user in a
  real session, not just reviewed by the author

### Keywords for discoverability

`slides`, `documents`, `pdf`, `presentation`, `typst`, `branded`, `reports`

These appear in `plugin.json` and should also appear in the README.

---

## 12. What NOT to Build

### No MCP wrapper

The Inkline bridge already runs on HTTP (port 8082). Adding an MCP server on
top of it would mean:

1. MCP tool call → MCP server → HTTP request to bridge → Claude agentic run
   (60-120 seconds) → response back through the stack

MCP has a 60-second tool call timeout by default. A full deck generation runs
for 60-120 seconds inside the bridge's Claude agentic session. The MCP wrapper
would time out on every real-world generation request. This is not a fixable
problem — it is architectural.

The correct interface to the bridge is the `curl` pattern shown in CLAUDE.md
and in the command files. Claude Code runs the curl commands as Bash tool
calls; the bridge handles the long-running agentic work; Claude Code reports
back when the file is ready. This works today without MCP.

An MCP wrapper would be a wrapper of a wrapper that adds a timeout failure mode
and zero user-facing benefit. Do not build it.

### No agent.md

`agent.md` defines autonomous background tasks. Inkline has no background tasks
— it is a request/response tool that the user invokes explicitly. An agent.md
would be appropriate if Inkline were watching a folder and auto-generating
decks, or running nightly reports. It is not appropriate today.

If a future spec introduces an Inkline watch mode or scheduled generation, add
`agent.md` at that time.

### No changes to the Python package

The plugin is a Claude Code extension. It does not touch the Inkline Python
package, its CLI, its bridge, or its tests. The boundary is sharp: the plugin
is Markdown files that teach Claude how to use the tool that already exists.

---

## Implementation Order

When this spec is approved and implementation begins, build in this order:

1. `.claude-plugin/plugin.json` — three lines, validate JSON
2. `skills/inkline/SKILL.md` — the always-on workflow primer
3. `commands/setup.md` + `skills/setup/SKILL.md` — let users verify the
   environment before attempting generation
4. `commands/deck.md` — primary use case
5. `commands/doc.md` — secondary use case

Test each step by installing the plugin (`claude plugin add .` from the repo
root) and verifying the skill/command activates as expected in a fresh Claude
Code session outside the inkline repo directory.

---

## Open Questions

1. **Plugin install path** — confirm that `claude plugin add https://github.com/u3126117/inkline`
   resolves the `.claude-plugin/plugin.json` at repo root correctly (vs
   requiring a dedicated plugin repo). If not, a thin wrapper repo may be
   needed.

2. **Skill keyword triggers** — the `setup` skill should activate when the user
   says "bridge not working" without running `/inkline:setup`. Confirm the
   plugin system supports keyword-based skill activation or whether explicit
   invocation is the only path.

3. **Multiple brands** — should the `deck` and `doc` commands accept a `--brand`
   argument in `$ARGUMENTS`? The initial spec passes brand as natural language
   in the prompt, which works but is less explicit. Defer to implementation
   review.

4. **ANTHROPIC_API_KEY check** — the setup skill checks for the key in the
   environment. If the user runs Claude Code via the Claude Max bridge (port
   8082 already handles auth), the key may not be in the shell environment even
   though generation works. The check should note this case rather than
   treating it as a hard failure.
