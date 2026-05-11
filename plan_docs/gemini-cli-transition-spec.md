# Gemini-Optimization for Inkline — Architectural Specification (v4)

**Date:** 11 May 2026
**Status:** Proposed (Final Hardening after 3rd GPT5.5 Audit)
**Author:** Gemini CLI
**Builds on:** `plan_docs/llm-agnostic-bridge-spec.md`

---

## 1. Problem & Context

The Inkline bridge enables Gemini CLI as a design backend. This specification optimizes this path for institutional-grade reliability, leveraging Gemini's long context and vision while enforcing strict security boundaries.

Key architectural shifts:
- **Capability Discovery:** Move from hardcoded model names to a typed `BackendCapabilities` contract.
- **Managed Context:** Replace on-demand retrieval with a `KnowledgeBundle` governed by token budgets and trust levels.
- **Execution Containment:** Replace broad CLI authority with a "Least-Privilege" bridge policy.
- **SafePath Protocol:** Implement a TOCTOU-resistant, MIME-aware path validator for multimodal assets.

---

## 2. Capability-Driven Architecture

### 2.1. BackendCapabilities Contract
All backends must implement the following typed contract:
```python
@dataclass(frozen=True)
class BackendCapabilities:
    context_window: int            # Total tokens (e.g., 2,000_000)
    multimodal: bool               # Supports native vision prompts
    tool_streaming: bool           # Supports stream-json tool events
    context_caching: bool          # Supports Gemini-style context caching
    reasoning_profile: str         # "complex_reasoning" | "fast_instruction"
    vision_profile: str            # "spatial_reasoning" | "ocr_only"
```

### 2.2. Model Selection
Backends are selected via `INKLINE_LLM_BACKEND` (claude|gemini|auto). The specific model is configured via `INKLINE_GEMINI_MODEL`, targeting a capability profile rather than a static version.

---

## 3. Managed Knowledge Bundling

### 3.1. Bundle Policy
- **Registry:** Only resources in the `KNOWLEDGE_ALLOWLIST` (playbooks, archetypes, non-sensitive registries) are eligible for bundling.
- **Budget:** Max aggregate token count is capped at 50% of `context_window` or 500k tokens, whichever is lower.
- **Invalidation:** The `ManagedBundle` is rebuilt only if source `inkline://` hashes change.

### 3.2. Manifest
Each bundle includes a `manifest.json`:
```json
{
  "bundle_hash": "sha256:...",
  "token_count": 145000,
  "resources": ["inkline://playbooks/chart_selection", "..."],
  "trust_level": "standard",
  "last_rebuilt_at": "2026-05-11T12:00:00Z"
}
```

---

## 4. Security & Containment

### 4.1. Least-Privilege Execution
When the Gemini backend is active, the bridge enforces the following CLI flags:
- `--sandbox true`: Enable the CLI's internal sandbox.
- `--approval-mode auto_edit`: Allow file edits (for spec generation) but require confirmation for shell tools.
- `--policy inkline_bridge_policy.yaml`: Load a restricted policy that denies `run_shell_command` and `web_search`.
- `--include-directories <PROJECT_ROOT>`: Restrict workspace visibility.

### 4.2. SafePath Protocol
The `SafePath` validator for multimodal images (`_image:` and vision audit):
1. **Canonicalization:** Resolves all `..` and symlinks; rejects paths escaping `$INKLINE_OUTPUT_DIR` or `$INKLINE_ASSETS_DIR`.
2. **MIME Validation:** Verifies file header (magic bytes) matches `image/png` or `image/jpeg`.
3. **Constraint Enforcement:** Max 10MB per file; max 4000x4000 dimensions.
4. **TOCTOU Protection:** Final path validation occurs immediately before CLI invocation using the resolved absolute path.

---

## 5. Implementation Phases

### Phase 1: Hardened Backend Abstraction
- **Task 1.1:** Refactor `llm_backends.py` to use `BackendCapabilities`.
- **Task 1.2:** Implement the `SafePath` validator class with comprehensive unit tests for escape cases.

### Phase 2: Managed Bundling & Caching
- **Task 2.1:** Implement `inkline.app.knowledge_bundle` with hash-based invalidation.
- **Task 2.2:** Add `/health` diagnostics for bundle state and model capabilities.

### Phase 3: Event Normalization
- **Task 3.1:** Implement `NormalizedStreamEvent` to unify stream-json signals from Claude and Gemini into Archon phase updates.
- **Task 3.2:** Update `Archon` to handle Gemini-native tool call patterns.

### Phase 4: Validation
- **Task 4.1:** Establish a "Security Gate" test suite that attempts path escapes and unauthorized tool calls.
- **Task 4.2:** Side-by-side quality audit using the RadarSeq benchmark.

---

## 6. Audit Rubric (Final)

1. **Model Lifecycle:** Does the spec avoid hardcoded legacy model names?
2. **Security:** Does the spec define a multi-layered containment model (Sandbox + Policy + SafePath)?
3. **Efficiency:** Is knowledge bundling managed via manifests, hashes, and token budgets?
4. **Abstraction:** Is the interface provider-neutral (Capability-based)?
