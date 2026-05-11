---
domain: document_design
audience: [founders, executives, partnerships, customers]
slide_type_relevance: [content, split, stat, three_card, process_flow]
last_updated: 2026-05-11
version: 1.0.0
---

# One-Pager Design Playbook

> **Purpose**: Guide production of professional single-page documents — for product/pitch
> one-pagers, company profiles, strategic summaries, and capability sheets.
>
> **Authority sources**: Aigis one-pager production (Apr 2026), RadarSeq booklet (Apr 2026),
> Soph Gen Z Career Coach Instagram reel (Apr 2026), and consulting document conventions.

---

## 1. What is a One-Pager?

A one-pager is a **single-page document** (portrait or landscape) that communicates a
complete, self-contained narrative to a reader who will spend 60–90 seconds on it.
It is NOT a slide (no presenter required) and NOT a brochure (no decoration for its own sake).

**Core constraint**: Every element must earn its place. If removing it doesn't weaken
the argument, remove it.

### Standard canvas sizes

| Format | Pixel dimensions | Use case |
|--------|-----------------|----------|
| Portrait A4 | 1024 × 1536 px | Company profiles, product sheets, pitch materials |
| Landscape A4 | 1536 × 1024 px | Architecture diagrams, process overviews, technical specs |
| US Letter portrait | 1056 × 1368 px | North America distribution |
| Square social | 1080 × 1080 px | LinkedIn / Instagram shareable |

**Render at 2× DPI** (Playwright `device_scale_factor=2`) to produce print-ready output.

---

## 2. The Soph Framework — 6 Zones of a Professional One-Pager

Derived from career-coach and consulting best practice for single-page documents.
Every zone must be present; none can be omitted without weakening the whole.

```
┌──────────────────────────────────────────────────────┐
│  ZONE 1: HEADER / IDENTITY                           │
│  Logo · Name · Tagline · Date                        │
├──────────────────────────────────────────────────────┤
│  ZONE 2: HOOK / PROBLEM STATEMENT                    │
│  One sentence or KPI strip that earns the reader's   │
│  attention in the first 3 seconds                    │
├──────────────────────────────────────────────────────┤
│  ZONE 3: CONTEXT / SITUATION                         │
│  Why this matters now. Market, data, or credibility  │
│  evidence. Typically 2-col: stat callouts + text     │
├──────────────────────────────────────────────────────┤
│  ZONE 4: SOLUTION / CORE OFFER                       │
│  What you do / how it works. Process steps,          │
│  architecture diagram, or capability grid            │
├──────────────────────────────────────────────────────┤
│  ZONE 5: PROOF / VALIDATION                          │
│  Evidence it works: client logos, deal stats,        │
│  testimonials, results grid, regional coverage map   │
├──────────────────────────────────────────────────────┤
│  ZONE 6: CTA / FOOTER                                │
│  One clear ask. Contact. QR code optional.           │
│  Team strip if credibility is needed                 │
└──────────────────────────────────────────────────────┘
```

### Zone proportions (portrait 1024 × 1536)

| Zone | Approx height | Notes |
|------|--------------|-------|
| Header | 80–100 px | Logo left, tagline right or centre |
| Hook | 100–160 px | Hero stat or bold single sentence |
| Context | 200–280 px | 2–3 KPI callouts + 1 short paragraph |
| Solution | 280–360 px | 3–5 step process OR 2×3 capability grid |
| Proof | 200–280 px | Logos + 2–4 stat cards OR map + side cards |
| Footer/CTA | 80–120 px | Horizontal layout: QR + contact inline |

**Equal-margin rule**: `padding: 16px 28px 16px 28px` — top and bottom margins must be
equal. Asymmetric padding (e.g. 14px top / 10px bottom) looks unfinished and is the
most common amateur layout error.

---

## 3. 12-Column Grid Applied to One-Pagers

Use a **12-column grid** with a consistent gutter (12–16px) for all multi-column layouts
within a one-pager section.

### Column allocations

| Layout intent | Column split | Pixel split (1024px canvas, 28px margin each side = 968px usable) |
|---|---|---|
| Full width | 12/12 | 968px |
| 2-col equal | 6+6 | 476px + 476px (16px gutter) |
| 2-col sidebar+content | 4+8 | 308px + 644px |
| 2-col content+sidebar | 8+4 | 644px + 308px |
| 3-col equal | 4+4+4 | 308px + 308px + 308px (16px gutters) |
| KPI strip (4 items) | 3+3+3+3 | 228px each (12px gutters) |
| KPI strip (3 items) | 4+4+4 | 308px each |

### When to use each split

- **12/12 (full width)**: Header, hook headline, footer CTA
- **6+6**: Context zone (stat callout + explanatory text side-by-side)
- **4+8**: Proof zone (small map / logo grid + deal card details)
- **4+4+4**: Solution zone (3-step process)
- **3+3+3+3**: KPI strip across the top of context or proof zone

**Grid alignment is non-negotiable for one-pagers.** Unlike slides (where whitespace
hides misalignment), a one-pager is read at close range and misaligned columns are
immediately visible.

---

## 4. Typography for One-Pagers

| Element | Size | Weight | Colour |
|---------|------|--------|--------|
| Document title / company name | 28–36pt | Bold | Brand primary |
| Zone section label | 9–10pt | Semibold, all caps | Brand accent or grey |
| Hook headline | 22–28pt | Bold | Dark (#1A1A1A) |
| KPI hero number | 36–48pt | Black/ExtraBold | Brand primary |
| KPI label | 9–10pt | Regular | #666666 |
| Body paragraph | 9–10pt | Regular | #333333, line-height 1.5 |
| Step title / card title | 11–12pt | Semibold | Dark |
| Step body | 9pt | Regular | #555555 |
| Footer text | 8–9pt | Regular | #888888 |

---

## 5. The Hook Zone — Three Patterns

### Pattern A: Hero stat
Single number with context label. Occupies full width. Example:
```
  ┌─────────────────────────────────────────────────┐
  │   M&A due diligence in E&P costs                │
  │   £200k      per deal — and still misses things  │
  │   (avg advisory fees, JLL/CBRE 2025 survey)      │
  └─────────────────────────────────────────────────┘
```

### Pattern B: KPI strip
3–4 stats in a horizontal row. Each stat: hero number + label. Example for Aigis:
```
  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐
  │   2,000+  │  │   £200k   │  │    6 wks  │  │    22x    │
  │ E&P deals │  │  per deal │  │  avg DD   │  │  faster   │
  │  /year    │  │  in fees  │  │  timeline │  │  w/ Aigis │
  └───────────┘  └───────────┘  └───────────┘  └───────────┘
```

### Pattern C: Bold question
One-sentence question in 24–28pt that the rest of the one-pager answers:
```
  "What if your next data room took 3 days, not 6 weeks?"
```

---

## 6. The Proof Zone — Map + Side Cards Pattern

Derived from Aigis one-pager vF (Apr 2026). Effective for showing geographic coverage
or deal validation across regions.

### Layout (6+6 column split)

```
  ┌────────────────────────┬──────────────────────────┐
  │  Regional map          │  Deal card 1              │
  │  (230×230 px square)   │  ┌──────────────────────┐ │
  │  with pin overlays     │  │ [mini map] [2×2 stats]│ │
  │                        │  │ Description text      │ │
  │                        │  └──────────────────────┘ │
  │                        │  Deal card 2              │
  │                        │  ...                      │
  └────────────────────────┴──────────────────────────┘
```

**Critical trap — square image in non-square column**:
When using `object-fit: contain` on a 1024×1024 source image inside a rectangular
column (e.g. 320×240), the rendered image fills only 240×240 — the smaller dimension.
SVG pin overlays anchored at `column_x + px% × column_width` land at the WRONG position
because `column_width ≠ rendered_image_width`.

**Fix**: Make the map column square (`width = height`), OR compute pin-x against
`min(col_w, col_h)` not `col_w`. This bug caused ~50% pin displacement until corrected
in Aigis vF build.

---

## 7. The Footer / CTA Zone

The footer must be **horizontal**, not vertical. A vertical CTA stack (QR code above
contact text) consumes 120px+ of page height and crowds the proof zone.

### Horizontal footer pattern (recommended)
```
  ┌────────────────────────────────────────────────────────┐
  │  [52×52 QR]   aaditya@aigis.ai  |  aigis.ai  |  @Aigis │
  └────────────────────────────────────────────────────────┘
```

### Footer with team grid
When credibility requires showing the team (e.g. early-stage pitch material):
```
  ┌──────────┬──────────┬──────────┬──────────┬──────────────┐
  │ [Photo]  │ [Photo]  │ [Photo]  │ [Photo]  │  QR + email  │
  │ Name     │ Name     │ Name     │ Name     │  web address │
  │ Title    │ Title    │ Title    │ Title    │              │
  └──────────┴──────────┴──────────┴──────────┴──────────────┘
```

Use a **4-column team grid** (not 2×2). The 2×2 grid clips the bottom row at standard
page height — confirmed Aigis vF bug.

---

## 8. Build Approach

One-pagers are **not generated via Inkline's Typst pipeline**. Typst is optimised for
multi-page documents and slide decks. One-pagers require pixel-precise layout control.

**Recommended stack**: Python + HTML/CSS + Playwright (headless Chromium screenshot).

### Pattern
```python
from playwright.sync_api import sync_playwright

HTML = """<!DOCTYPE html>
<html><head>
<style>
  body { margin: 0; width: 1024px; height: 1536px; font-family: 'Inter', sans-serif; }
  .page { padding: 16px 28px 16px 28px; }
  /* ... zones ... */
</style>
</head><body>
<div class="page">
  <!-- zone 1: header -->
  <!-- zone 2: hook -->
  <!-- zone 3: context -->
  <!-- zone 4: solution -->
  <!-- zone 5: proof -->
  <!-- zone 6: footer -->
</div>
</body></html>"""

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1024, "height": 1536})
    page.set_content(HTML, wait_until="networkidle")
    page.screenshot(path="output.png", full_page=False, scale="device")
    browser.close()
```

Set `device_scale_factor=2` on `new_page()` for 2048×3072 print-ready output.

**Asset embedding**: Convert all images to base64 data URIs and embed inline.
This ensures the Playwright screenshot captures assets regardless of file paths,
network access, or CORS. Example:
```python
import base64
def img_b64(path):
    return "data:image/png;base64," + base64.b64encode(open(path,"rb").read()).decode()
```

---

## 9. Quality Checklist

Before shipping a one-pager, verify:

- [ ] Equal top/bottom margin (measure in browser devtools)
- [ ] All 6 zones present and in correct order
- [ ] Hook readable in 3 seconds (print test: stand 1 metre from screen)
- [ ] KPI numbers are the largest text on the page (hierarchy enforced)
- [ ] Footer is horizontal, not vertical
- [ ] Team grid is 4-column (not 2×2)
- [ ] Map column is square if using pin overlays
- [ ] No zone bleeds into adjacent zone (use explicit height, not auto)
- [ ] CTA is unambiguous — reader knows exactly what to do next
- [ ] All images embedded as base64 (no broken image links)

---

## 10. Related Playbooks

- `document_design.md` — §8 grid system, §2 executive summary
- `template_catalog.md` — §2.4 multi-tile persona, §2.3 funnel KPI strip
- `slide_layouts.md` — KPI strip atom, action title rules

---

## References

- Aigis one-pager build: `aigis-agents-v2/docs/business/build_scripts/build_aigis_onepagers.py`
- Aigis session journal: `~/.claude/journal/aigis/2026-04-28-aigis-onepagers-vF.md`
- Soph (@sophgenzcareers) Instagram Reel `DXdIW10k3N_`, 28 Apr 2026 — project one-pager framework
