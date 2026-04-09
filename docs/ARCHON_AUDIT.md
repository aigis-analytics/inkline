# Archon Audit Workflow for Inkline Output

**Purpose:** Ensure every deck and exhibit Inkline produces fits cleanly on the
slide frame, uses brand-consistent chart sizing, and doesn't silently truncate
content.

**Applies to:** Any caller that invokes `inkline.typst.export_typst_slides()`,
`inkline.typst.export_typst_document()`, or `inkline.typst.chart_renderer.render_chart_for_brand()`.

---

## 1. Why this exists

Early test decks had two recurring issues:

1. **Exhibit PNGs were oversized.** Matplotlib defaulted to 10″×5.5″ which,
   when scaled to 90% of the slide width (20.7 cm), pushed the image beyond the
   usable body area (8.5 cm) and either overflowed the next slide or got
   clipped by Typst's page fill.

2. **Slide content overflowed silently.** The design advisor would happily
   return a `content` slide with 15 bullets; the renderer had no hard cap and
   everything after bullet 10 or so ran off the bottom.

Both failures were invisible in logs — they only showed up when a human opened
the PDF. The Archon audit workflow catches both classes of problem *before*
the PDF is compiled and flags them for correction.

---

## 2. The built-in audit

`inkline.intelligence.overflow_audit` ships with three audit primitives:

```python
from inkline.intelligence import audit_deck, audit_slide, audit_image, format_report
```

### `audit_deck(slides: list[dict]) -> list[AuditWarning]`
Walks every slide, looks up its layout in `SLIDE_CAPACITY`, and compares actual
content length to the capacity. Also checks bullet/label text length for
wrap-risk (>220 chars), and calls `audit_image()` on any referenced chart PNG.

### `audit_image(path, *, max_width_cm=20.7, max_height_cm=8.5, dpi=200)`
Opens the PNG with Pillow, converts pixels to cm at the target DPI, and
computes what its height would be when scaled to slide width. Flags:
- Images that would exceed `max_height_cm` when fit to width.
- Aspect ratios under 1.2 (nearly square / tall → poor for 16:9 slides).
- Missing files.

### `format_report(warnings)`
Renders the list of `AuditWarning` objects as a human-readable block, grouped
by severity (error / warn / info).

---

## 3. When it runs automatically

`export_typst_slides(..., audit=True)` (default) runs `audit_deck()` *before*
invoking the Typst compiler. Warnings are logged at `WARNING` level via the
`inkline.typst` logger. Example:

```
WARNING inkline.typst: Inkline overflow audit:
OVERFLOW AUDIT: 0 errors, 2 warnings, 0 info
-----------------------------------------
[WARN] slide 3 (content): field 'items' has 14 items but slide capacity is 8.
       Excess items will be truncated by the renderer. Consider splitting into
       multiple slides.
[WARN] slide 5 (chart): image exhibit_1.png is 2000x1100px (25.4x14.0cm @ 200dpi);
       when fit to slide width it would be 11.3cm tall (max 8.5cm). Re-render
       with smaller matplotlib figsize (e.g. 8x4 inches) or use height constraint.
```

The renderer *also* applies hard caps at render time as a safety net
(`TypstSlideRenderer.MAX_BULLETS=8`, `MAX_TABLE_ROWS=12`, etc.), so nothing
actually overflows even if the audit is ignored — but the warnings tell the
caller to reshape the input next time.

---

## 4. How Archon integrates

The Archon review loop (in Aria's codebase, but the pattern applies to any
orchestrator) should add Inkline audit results to its evidence trail:

### 4.1 Before generation
```python
from inkline.intelligence import audit_deck, format_report

warnings = audit_deck(proposed_slides)
if any(w.severity == "error" for w in warnings):
    # Block generation — send back to the advisor to replan
    return replan_deck(proposed_slides, warnings)
```

### 4.2 During generation
Capture the audit log from `export_typst_slides()`:

```python
import logging
log_capture = logging.handlers.MemoryHandler(capacity=1024)
logging.getLogger("inkline.typst").addHandler(log_capture)

export_typst_slides(slides, output_path, brand=brand)

audit_records = [r.getMessage() for r in log_capture.buffer
                 if "overflow audit" in r.getMessage()]
```

### 4.3 After generation
Open the produced PDF (via `pdfinfo` or `pdf2image`) and confirm:
- Page count matches `len(slides)` — no unexpected extra pages (classic overflow symptom).
- No blank final page (happens when content bleeds past the body).
- Any embedded images stay within the safe area.

### 4.4 Audit trail
Record every audit pass in the Archon evidence database:

```python
archon.record_evidence(
    source="inkline_overflow_audit",
    outcome="OK" if not warnings else "WARN",
    details={
        "deck": output_path,
        "slide_count": len(slides),
        "warnings": [str(w) for w in warnings],
        "auto_truncated": any(w.severity == "warn" for w in warnings),
    },
)
```

---

## 5. Agent workflow

When a Claude/Aria agent is asked to "make a pitch deck":

```
1. Plan structure ──▶ DesignAdvisor.design_deck()
                     │
                     ▼
2. Pre-audit    ──▶ audit_deck(slides)
                     │ (errors → back to step 1)
                     │ (warnings → acceptable, continue)
                     ▼
3. Render       ──▶ export_typst_slides(audit=True)
                     │ (auto-runs audit_deck() again and logs)
                     ▼
4. Post-check   ──▶ verify PDF page count, open page 1 as image
                     │
                     ▼
5. Deliver      ──▶ attach PDF + audit summary to Archon evidence
```

---

## 6. Chart sizing rules for agents

When writing code that produces PNG exhibits for slide embedding:

1. **Default figsize is safe.** `render_chart()` now defaults to `width=8.0,
   height=4.0` inches, which at 200 dpi is 1600×800 px → 20.3×10.2 cm → fits
   comfortably within the 20.7×8.5 cm image budget.

2. **Don't override figsize upward.** If an agent wants a bigger chart, it
   should instead use a dedicated `chart` slide and keep figsize ≤ 8×4.

3. **Let Typst do the scaling.** The `chart` slide embed is now
   `image("...", width: 90%, height: 8.5cm)` — Typst will letterbox the image
   into that box, preserving aspect ratio.

4. **For tables of numbers, use `table` slide — not a chart PNG.**
   Tables render as native Typst, reflow correctly, and the audit knows their
   capacity.

---

## 7. Failure modes the audit catches

| Symptom in PDF                                 | Audit warning                                       |
|------------------------------------------------|-----------------------------------------------------|
| Bullets cut off at bottom of slide             | `field 'items' has N items but slide capacity is 8` |
| Table runs onto a second (blank) page          | `field 'rows' has N items but slide capacity is 12` |
| Chart PNG clipped at the bottom                | `image ... would be N cm tall (max 8.5 cm)`         |
| Chart looks tiny and square                    | `aspect ratio X is nearly square/tall`              |
| `image not found` Typst compile error          | `image_path '...' does not exist`                   |
| Process flow with 8+ steps runs off the side   | `field 'steps' has N items but slide capacity is 5` |

---

## 8. Extending the audit

To add a new slide type to the audit:

1. Add it to `SLIDE_CAPACITY` in `intelligence/layout_selector.py`.
2. Add the content field(s) to `_CONTENT_FIELDS` in
   `intelligence/overflow_audit.py` (supports dotted paths like
   `"left.items"`).
3. Add a `MAX_*` constant on `TypstSlideRenderer` and truncate the input in
   the corresponding `_*_slide()` method.

The audit will pick up the new type automatically.

---

## 9. Running the audit standalone

```bash
python -c "
from inkline.intelligence import audit_deck, format_report
import json
slides = json.load(open('my_deck.json'))
print(format_report(audit_deck(slides)))
"
```

Or from code:

```python
from inkline.intelligence import audit_deck, format_report

warnings = audit_deck(my_slides)
print(format_report(warnings))
```

---

## 10. Guarantees

With `audit=True` (default):

- **No silent overflow.** Any content that exceeds a layout's capacity will
  generate a `WARN`-level log line.
- **No missing images.** Referenced `image_path` values that don't exist
  generate `ERROR`-level warnings.
- **No oversized charts.** PNGs that would exceed 8.5 cm tall when fit to
  slide width generate a `WARN`-level recommendation.
- **No long-wrap bullets.** Individual bullets >220 characters are flagged.
- **Truncation is deterministic.** Even with the audit disabled, the renderer
  truncates to hard limits so nothing renders off-page.

The audit is cheap (microseconds), safe (never throws), and idempotent. It
should be on by default in every production Inkline pipeline.
