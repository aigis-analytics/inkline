# Inkline LLM-Agnostic Bridge Spec

**Status:** Proposed  
**Date:** 2026-05-06

## Goal

Make Inkline Draft Mode and bridge-driven intelligence provider-agnostic so the
same runtime can execute through either:

- Claude CLI
- Gemini CLI

without changing the higher-level Inkline API surface.

## Why

Today the repo already has a clean `LLMCaller` abstraction in `DesignAdvisor`,
but the bridge and surrounding helpers are still Claude-specific:

- `inkline serve` and `inkline bridge` hard-wire Claude checks
- `inkline.app.claude_bridge` shells out directly to `claude`
- `/prompt`, `/vision`, and `/health` assume Claude semantics
- `ensure_bridge_running()` is Claude-named and Claude-script specific
- several intelligence helpers describe the bridge as “Claude bridge”

That makes the runtime harder to operate from Codex and blocks Gemini-backed
Draft Mode even though Gemini CLI is locally available.

## Scope

This change covers:

1. A backend abstraction for bridge subprocess execution
2. Runtime selection between Claude and Gemini
3. CLI flags/env vars for backend selection
4. Health metadata that reports the active backend
5. Compatibility updates in bridge-first helper paths

This change does **not** attempt to:

- redesign the DesignAdvisor prompting system
- remove Anthropic SDK fallback in `DesignAdvisor`
- make every vision/audit path model-identical
- add API-key-based Gemini support

## Architecture

### 1. Generic bridge runner

Introduce a small provider module in `inkline.app` that exposes:

- available backend IDs
- backend-specific CLI availability checks
- prompt command construction
- vision command construction
- health metadata

Suggested shape:

```python
class LLMBackend(Protocol):
    backend_id: str
    def cli_available(self) -> bool: ...
    def cli_version_cmd(self) -> list[str]: ...
    def prompt_command(self, *, system: str, max_turns: int) -> list[str]: ...
    def vision_command(self, *, system: str) -> list[str]: ...
    def prepare_env(self, env: dict[str, str]) -> dict[str, str]: ...
```

Concrete implementations:

- `ClaudeCLIBackend`
- `GeminiCLIBackend`

### 2. Backend selection

Support:

- CLI flag: `inkline serve --backend {claude,gemini,auto}`
- CLI flag: `inkline bridge --backend {claude,gemini,auto}`
- env var: `INKLINE_LLM_BACKEND`

Resolution order:

1. explicit CLI flag
2. env var
3. `auto`

`auto` should prefer:

1. Claude if available
2. Gemini if available

This preserves existing behaviour for current users.

### 3. Bridge module compatibility

Keep `inkline.app.claude_bridge` as an import-compatible entrypoint for now, but
make it backend-agnostic internally. That avoids breaking existing references.

Optional later cleanup can rename the file to `bridge.py` and leave a thin
compat shim.

### 4. Health endpoint

Extend `/health` and related responses to report:

- active backend
- available backends
- whether prompt mode is usable
- whether vision mode is usable

Example:

```json
{
  "status": "ok",
  "backend": "gemini",
  "available_backends": ["claude", "gemini"],
  "draft": true,
  "critique": true
}
```

## Backend Behaviour

### Claude

Keep current behaviour:

- `claude -p`
- `--output-format stream-json`
- `--dangerously-skip-permissions`
- `--system-prompt`

### Gemini

Use Gemini CLI in headless mode:

- `gemini --prompt`
- `--output-format stream-json`
- `--model <model>`
- `--approval-mode yolo`
- `--sandbox false`
- `--include-directories` if needed later

The bridge prompt contract should stay the same from Inkline’s perspective:

- system prompt text
- user prompt text
- structured response extraction from streamed output

If Gemini needs a different system-injection pattern, handle that inside the
backend adapter rather than in bridge call sites.

## Intelligence Helper Updates

Update bridge helpers to refer to a generic Inkline bridge rather than Claude:

- `inkline.intelligence.claude_code.ensure_bridge_running()` should remain for
  compatibility but delegate to a generic implementation
- long term we should expose a neutral helper such as
  `inkline.intelligence.bridge_runtime.ensure_bridge_running()`

This pass only needs enough neutralisation so bridge-first routing works
regardless of whether the running bridge uses Claude or Gemini.

## Testing

Minimum coverage:

- backend selection logic
- health endpoint reports backend correctly
- CLI parser accepts `--backend`
- prompt command building for Claude and Gemini

Mock subprocess execution where possible. No live model invocation required.

## Acceptance Criteria

1. `inkline bridge --backend claude` starts the current Draft Mode path
2. `inkline bridge --backend gemini` starts the same HTTP bridge on Gemini CLI
3. `inkline serve --backend auto` works without code changes by the caller
4. `DesignAdvisor` bridge-first routing still works against the same `/prompt`
   endpoint regardless of backend
5. existing Claude users are not broken by default
