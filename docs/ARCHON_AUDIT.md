# Inkline Archon Audit Pipeline

**Purpose:** Every Inkline pipeline run is supervised by an `Archon` instance
that intercepts all log records, tracks named phases, and writes a structured
Markdown issues report at completion. This gives every pipeline run a single
point of contact and a machine-readable audit trail.

**Module:** `inkline.intelligence.archon`

---

## 1. Why Archon exists

Production Inkline pipelines have 4–6 phases (parse → design → render → audit →
copy output). Failures happen in any phase. Without a supervisor:
- Errors from the Typst compiler, LLM bridge, chart renderer, and overflow fixer
  all go to different log streams with different formats.
- There is no single file to read when something goes wrong.
- Phase timing is invisible.

Archon solves all three: it attaches once to the root `inkline` logger and
captures everything, tagged by phase, written to a predictable Markdown file.

---

## 2. Core API

```python
from inkline.intelligence.archon import Archon, Issue, PhaseResult

@dataclass
class Issue:
    phase: str
    severity: str   # "INFO" | "WARNING" | "ERROR"
    message: str
    detail: str = ""   # optional traceback or extended context

@dataclass
class PhaseResult:
    name: str
    started: datetime
    ended: datetime | None
    ok: bool
    issues: list[Issue]

class Archon:
    def __init__(
        self,
        report_path: Path | str,
        title: str = "",
        verbose: bool = True,
    ) -> None: ...

    def start_phase(self, name: str) -> PhaseResult: ...
    def end_phase(self, phase: PhaseResult, ok: bool) -> None: ...
    def record(self, issue: Issue) -> None: ...
    def write_report(self) -> None: ...
    def detach(self) -> None: ...
```

**Logging integration:** Archon attaches `_ArchonHandler` to the **root `inkline`
logger only** (all child loggers — `inkline.typst`, `inkline.intelligence`, etc. —
propagate up). DEBUG records are skipped (too noisy). This means you never need
to wire up multiple loggers; Archon sees everything automatically.

---

## 3. Usage pattern

```python
from pathlib import Path
import traceback, sys
from inkline.intelligence.archon import Archon, Issue

archon = Archon(Path("work_dir/run_issues.md"), title="My Pipeline Run")

# Phase 1
phase = archon.start_phase("design_advisor_llm")
try:
    slides = advisor.design_deck(...)
    archon.record(Issue(
        phase="design_advisor_llm", severity="INFO",
        message=f"DesignAdvisor produced {len(slides)} slides",
    ))
    archon.end_phase(phase, ok=True)
except Exception as e:
    archon.record(Issue(
        phase="design_advisor_llm", severity="ERROR",
        message=str(e), detail=traceback.format_exc(),
    ))
    archon.end_phase(phase, ok=False)
    archon.write_report()
    archon.detach()
    sys.exit(1)

# Phase 2 ...

# Done
archon.write_report()
archon.detach()
```

---

## 4. The overflow audit — what Archon captures

The closed-loop QA pipeline in `export_typst_slides()` emits detailed logs for
every fix attempt. Archon captures all of them:

```
Phase: export_pdf_with_audit
  INFO  Pre-render fixer applied 4 fixes to 18 slides
  INFO  Overflow inner loop: attempt 1 on slides [3, 7, 12]
  INFO  Overflow fix attempt 1: content_reduction on slide 3
  INFO  Overflow inner loop: attempt 2 on slides [7, 12]
  INFO  Overflow fix attempt 3: type_downgrade on slide 7 (chart_caption → split)
  INFO  Overflow fix attempt 3: type_downgrade on slide 12 (icon_stat → kpi_strip)
  INFO  Inner loop converged: 18 slides → 18 pages
  INFO  Visual audit: 2 errors, 1 warning — re-rendering (attempt 1/3)
  INFO  Visual audit attempt 1: fixed 2 issues, re-rendering
  INFO  Visual audit: 0 errors → clean pass
  INFO  PDF rendered: output.pdf (2,847,301 bytes)
```

---

## 5. Report format

`write_report()` produces a Markdown file:

```markdown
# Archon Issues Report — My Pipeline Run
Generated: 2026-04-13 14:32:17

## Summary
| Phase | Status | Errors | Warnings | Info |
|-------|--------|--------|----------|------|
| parse_markdown | ✅ OK | 0 | 0 | 1 |
| design_advisor_llm | ✅ OK | 0 | 1 | 2 |
| export_pdf_with_audit | ✅ OK | 0 | 0 | 8 |
| copy_final_pdf | ✅ OK | 0 | 0 | 1 |

## Phase: design_advisor_llm (12.4s)
...
```

---

## 6. Integration with gen scripts

Archon is importable directly from `inkline.intelligence`:

```python
from inkline.intelligence import Archon, Issue
# or
from inkline.intelligence.archon import Archon, Issue, PhaseResult
```

The Corsair gen script (`gen_corsair_deck.py`) is the reference implementation:
five phases, all wrapped with `start_phase`/`end_phase`, fatal phases call
`write_report()` + `detach()` + `sys.exit(1)`.

---

## 7. Structural overflow audit functions

The following remain available as standalone functions in
`inkline.intelligence.overflow_audit`:

```python
from inkline.intelligence import audit_deck, audit_slide, audit_image, format_report

# Structural (no API)
warnings = audit_deck(slides)
warnings = audit_slide(slide_index, slide_type, data)
warnings = audit_image(path, max_width_cm=20.7, max_height_cm=8.5)
warnings = audit_rendered_pdf(pdf_path, expected_slides)
print(format_report(warnings))

# Visual (bridge /vision or explicit api_key)
warnings = audit_deck_with_llm(pdf_path, slides, bridge_url="http://localhost:8082")
```

**`AuditWarning` dataclass:**
```python
@dataclass
class AuditWarning:
    slide_index: int
    slide_type: str
    severity: str   # "info" | "warn" | "error"
    message: str
```

---

## 8. Failure modes the audit catches

| Symptom in PDF | Audit source | Warning |
|----------------|-------------|---------|
| Bullets cut off at bottom | Structural | `field 'items' has N > capacity` |
| Table runs onto second page | Structural | `field 'rows' has N > 6` |
| Chart PNG clipped | `audit_image` | `image would be N cm tall (max 8.5 cm)` |
| Page count > slide count | `audit_rendered_pdf` | `actual=N pages > expected=M slides` |
| Text visually overflowing | LLM vision | ERROR finding → triggers revision |
| Off-brand colour | LLM vision | WARN finding → logged, not auto-fixed |

---

## 9. Guarantees

With `audit=True` (default in `export_typst_slides`):

- **No silent overflow.** Any content exceeding layout capacity generates a
  `WARN`-level log line (captured by Archon).
- **No missing images.** Referenced `image_path` values that don't exist
  generate `ERROR`-level warnings before compile.
- **Auto-fix convergence.** The inner loop runs up to `max_overflow_attempts`
  (default 6) fix attempts; the outer loop runs up to `max_visual_attempts`
  (default 3) vision-dialogue rounds. Exit on: clean pass, no actionable
  fixes, or max rounds reached — never infinite loop.
- **Zero API spend by default.** Visual audit routes through the bridge
  (`/vision` endpoint). `ANTHROPIC_API_KEY` is never read from the environment
  automatically; pass `api_key=` explicitly to opt in to SDK fallback.
