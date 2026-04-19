# Inkline Document Renderer Improvements Spec

## Status: Implemented

## Context

`TypstDocumentRenderer` in `src/inkline/typst/document_renderer.py` generates
branded A4/Letter reports. The renderer was originally prototyped for a single
deal note and carries several hardcoded assumptions from that origin.
As Inkline is used for a broader range of documents — board packs, investment
memos, advisory reports — these assumptions must be removed and the typographic
and layout quality must be brought up to professional publication standards.

This spec covers eight targeted improvements, prioritised into Phase 1
(correctness/usability blockers) and Phase 2 (quality enhancements). There are
no changes to the public `export_typst_document()` API surface; all changes are
internal to the renderer and `DocumentSpec`.

---

## Motivation

### Phase 1 blockers

1. **The cover page cannot be reused across document types.** The "Deal at a
   Glance" panel contains hardcoded GBP figures, market labels, and tranche data.
   Any brand or document using the renderer inherits these artefacts verbatim.

2. **Tables and figures are not numbered.** Finance documents are cross-
   referenced by exhibit number ("see Figure 3", "per Table 2"). Without auto-
   numbering, these references must be managed manually and break on any
   reorder.

3. **Line height `0.8em` is tighter than a printed newspaper.** The current
   default produces documents that feel dense and difficult to scan. Minimum
   acceptable value for body copy is `1.5`.

### Phase 2 enhancements

4. **The running header shows the document title but not the current section.**
   In a 30-page report, readers cannot determine their location without checking
   the TOC.

5. **OpenType figure variants are not applied.** Tabular figures (fixed-width)
   are required for columns of numbers to align correctly. Old-style figures
   improve readability in body copy. Neither is set anywhere in the renderer.

6. **Uppercase labels have no letter-spacing (tracking).** Untracked uppercase
   text is a typographic anti-pattern; it produces crowded, legibility-reduced
   labels.

7. **No section divider pages.** Long documents benefit from full-bleed section
   breaks that reset the reader's attention. Currently unsupported.

8. **Zero test coverage for `document_renderer.py`.** The renderer has no unit
   tests. Changes are verified only by end-to-end visual audit, which is slow
   and catches only gross failures.

---

## Implementation Plan

### Phase 1

#### Step 1 — Parameterise the cover panel

**Problem.** `_cover_page()` hard-codes a "DEAL AT A GLANCE" block with four
metric cells containing prototype-specific values. This block is unconditional.

**Change to `DocumentSpec`.**

Add a single optional field:

```python
@dataclass
class DocumentSpec:
    title: str = ""
    subtitle: str = ""
    date: str = ""
    author: str = ""
    sections: list[dict[str, Any]] = field(default_factory=list)
    paper: str = "a4"
    cover_panel: dict[str, str] | None = None  # NEW — key/value pairs for cover metrics
```

`cover_panel` accepts an ordered dict of up to six key-value pairs. Keys are
short labels; values are metric strings. Example:

```python
cover_panel={
    "Total debt target": "£80m",
    "Blended cost": "~9.5%",
    "Bullet saving vs offer": "£14–15m",
    "Markets": "UK, KSA, UAE",
}
```

**Change to `_cover_page()`.** Replace the hardcoded block with a conditional:

```python
if spec.cover_panel:
    panel_cells = "\n    ".join(
        f"""[
      #text(fill: {_rgb(secondary)}, weight: "bold", size: 22pt)[{_esc(v)}]
      #v(3pt)
      #text(fill: rgb("#c0d0c0"), size: 8pt)[{_esc(k)}]
    ]"""
        for k, v in list(spec.cover_panel.items())[:6]
    )
    n_cols = min(len(spec.cover_panel), 4)
    cover_panel_block = f"""#block(
  width: 100%,
  inset: (x: 22pt, y: 18pt),
  fill: {_rgb(accent)},
  radius: 4pt,
)[
  #text(fill: white, weight: "bold", size: 7.5pt, tracking: 2pt)[HIGHLIGHTS]
  #v(14pt)
  #grid(
    columns: {"(1fr, " * n_cols}),
    gutter: 6pt,
    {panel_cells}
  )
]

#v(1.2cm)"""
else:
    cover_panel_block = "#v(1.2cm)"
```

Insert `cover_panel_block` in place of the current hardcoded block. If
`cover_panel` is `None`, the visual gap is filled by the `#v(1.2cm)` spacer
so the metadata table position is stable.

**The TOC page is also affected.** The current `_toc_page()` contains a
hardcoded "RECOMMENDED CAPITAL STRUCTURE" grid, a "HOW TO READ THIS NOTE"
callout, and a hardcoded confidentiality footer. These are as document-specific
as the cover panel.

Add a parallel `toc_panel` field to `DocumentSpec`:

```python
toc_panel: dict[str, Any] | None = None
# Keys: "title" (str), "cards" (list of {"heading": str, "body": str}),
#       "how_to_read" (str | None), "confidentiality_notice" (str | None)
```

When `toc_panel` is `None`, `_toc_page()` renders a minimal page: just the
outline, a spacer, and the confidentiality notice from the theme's
`confidentiality` key (no hardcoded boilerplate text).

**Files to modify:**
- `src/inkline/typst/document_renderer.py` — `DocumentSpec`, `_cover_page()`,
  `_toc_page()`

---

#### Step 2 — Exhibit numbering and captioning

**Problem.** There is no `Figure N` / `Table N` numbering. No caption
conventions. No source attribution.

**Design.** Use Typst's native `counter` API so numbering is automatic and
survives section reorders.

**New Typst counter definitions** (emit in `_component_defs()`):

```typst
#let figure-counter = counter("figures")
#let table-counter = counter("tables")

// Figure: caption BELOW, incrementing Figure counter
#let fig(image-content, caption: none, source: none) = {
  figure-counter.step()
  block(width: 100%)[
    #image-content
    #v(4pt)
    #text(size: 9pt, weight: "bold")[Figure #figure-counter.display()]
    #if caption != none [ — #text(size: 9pt)[#caption]]
    #if source != none [
      #v(2pt)
      #text(size: 8pt, fill: rgb("#64748B"), style: "italic")[Source: #source]
    ]
  ]
}

// Table: caption ABOVE, incrementing Table counter
#let tbl(table-content, caption: none, source: none) = {
  table-counter.step()
  block(width: 100%)[
    #text(size: 9pt, weight: "bold")[Table #table-counter.display()]
    #if caption != none [ — #text(size: 9pt)[#caption]]
    #v(4pt)
    #table-content
    #if source != none [
      #v(2pt)
      #text(size: 8pt, fill: rgb("#64748B"), style: "italic")[Source: #source]
    ]
  ]
}
```

The `slate` colour `#64748B` is used for source attribution. If the theme
defines a `slate` key, use `{_rgb(t.get("slate", "#64748B"))}` instead of the
literal.

**API change to `_render_section()`.** Sections can now specify exhibits:

```python
# Section dict extended schema:
{
    "heading": "Revenue Analysis",
    "level": 1,
    "content": "...",        # raw Typst — may call #fig() or #tbl()
    "exhibits": [            # NEW — pre-declared exhibits for this section
        {
            "type": "figure",           # "figure" | "table"
            "content": "...",           # Typst content expression (chart image etc.)
            "caption": "...",           # optional
            "source": "...",            # optional
        }
    ],
    "pagebreak": False,
}
```

When `exhibits` is present, `_render_section()` emits each exhibit wrapped
in the appropriate `#fig()` or `#tbl()` call immediately after the section
body content.

**No change is required to `_flush_table()`** in the Markdown path — Markdown
tables are auto-rendered and should not be numbered unless the caller
explicitly wraps them. (Automatic numbering of all Markdown tables is Phase 2
scope only, if desired.)

**Files to modify:**
- `src/inkline/typst/document_renderer.py` — `_component_defs()`,
  `_render_section()`

---

#### Step 3 — Line height and paragraph spacing

**Problem.** `#set par(leading: 0.8em, justify: true)` is too tight for
professional print. No inter-paragraph spacing is set.

**Change in `_preamble()`.** Replace the single `#set par` call:

```typst
// Before:
#set par(leading: 0.8em, justify: true)

// After:
#set par(leading: 1.5em, justify: true, spacing: 0.65em)
```

**Change in `_heading_styles()`.** Each heading show rule applies a
`par(leading:)` override inside the show rule to tighten heading-internal
line breaks (headings rarely wrap, but when they do, `1.15em` is appropriate):

```typst
#show heading.where(level: 1): it => {
  set par(leading: 1.15em)
  v(16pt)
  text(font: "...", weight: "bold", size: 18pt, fill: ...)[#it]
  ...
}
// Same pattern for level 2 and level 3 headings.
```

The `spacing: 0.65em` parameter requires Typst 0.11 or later. The renderer
already requires Typst for compilation, so no version guard is needed; however,
the implementation should confirm Typst version support before merging.

**Files to modify:**
- `src/inkline/typst/document_renderer.py` — `_preamble()`,
  `_heading_styles()`

---

#### Step 4 — Document-specific test coverage

**Problem.** `document_renderer.py` has zero unit tests.

**New test file:** `tests/test_document_renderer.py`

Minimum five tests required. Each test should call `render_document()` or
`render_from_markdown()` and assert on the generated Typst string — no PDF
compilation required.

```python
# tests/test_document_renderer.py

import pytest
from inkline.typst.document_renderer import DocumentSpec, TypstDocumentRenderer

MINIMAL_THEME = {
    "heading_font": "Inter",
    "body_font": "Inter",
    "body_size": 11,
    "accent": "#1a3a5c",
    "accent2": "#39d3bb",
    "muted": "#6B7280",
    "border": "#D1D5DB",
    "text": "#1A1A1A",
    "surface": "#F4F6F8",
    "secondary": "#B8960C",
    "confidentiality": "Confidential",
    "footer_text": "Test Document",
}


def make_renderer():
    return TypstDocumentRenderer(theme=MINIMAL_THEME)


# Test 1: Cover page omits panel block when cover_panel is None
def test_cover_page_no_panel():
    spec = DocumentSpec(title="Test", cover_panel=None)
    renderer = make_renderer()
    result = renderer.render_document(spec)
    assert "DEAL AT A GLANCE" not in result
    assert "HIGHLIGHTS" not in result


# Test 2: Cover page renders panel entries when cover_panel is provided
def test_cover_page_with_panel():
    spec = DocumentSpec(
        title="Test",
        cover_panel={"Total target": "£80m", "Blended cost": "~9.5%"},
    )
    renderer = make_renderer()
    result = renderer.render_document(spec)
    assert "£80m" in result
    assert "~9.5%" in result
    assert "Total target" in result


# Test 3: Exhibit counter definitions are emitted
def test_exhibit_counter_defs():
    spec = DocumentSpec(title="Test")
    renderer = make_renderer()
    result = renderer.render_document(spec)
    assert 'counter("figures")' in result
    assert 'counter("tables")' in result
    assert "#let fig(" in result
    assert "#let tbl(" in result


# Test 4: Section with exhibit emits fig/tbl wrapper
def test_section_figure_exhibit():
    spec = DocumentSpec(
        title="Test",
        sections=[
            {
                "heading": "Analysis",
                "level": 1,
                "content": "See the chart below.",
                "exhibits": [
                    {
                        "type": "figure",
                        "content": '#image("chart.png")',
                        "caption": "Revenue trend",
                        "source": "Internal",
                    }
                ],
            }
        ],
    )
    renderer = make_renderer()
    result = renderer.render_document(spec)
    assert "#fig(" in result
    assert "Revenue trend" in result
    assert "Source: Internal" in result or "source: " in result


# Test 5: par leading is 1.5em not 0.8em
def test_par_leading_not_tight():
    spec = DocumentSpec(title="Test")
    renderer = make_renderer()
    result = renderer.render_document(spec)
    assert "leading: 0.8em" not in result
    assert "leading: 1.5em" in result


# Test 6: cover_panel truncates at 6 entries
def test_cover_panel_max_six_entries():
    spec = DocumentSpec(
        title="Test",
        cover_panel={f"Key {i}": f"Val {i}" for i in range(10)},
    )
    renderer = make_renderer()
    result = renderer.render_document(spec)
    # Keys 0-5 should appear, Keys 6-9 should not
    assert "Key 0" in result
    assert "Key 5" in result
    assert "Key 6" not in result
```

Six tests are provided; the minimum stated requirement is five. The sixth
(panel truncation) is included because the implementation silently silences
excess entries and the contract should be explicitly tested.

**Files to create:**
- `tests/test_document_renderer.py`

---

### Phase 2

#### Step 5 — Running section headers

**Problem.** The current header shows only the document title and logo.
Readers of multi-section documents cannot determine their position.

**Design.** Use Typst's `query()` API with `context` to find the last
level-1 heading that precedes the current page position.

**Replace the header block in `_preamble()`.** The current header:

```typst
header: context {
  if counter(page).get().first() > 1 {
    grid(
      columns: (1fr, auto),
      text(...)[doc_title],
      logo_or_conf_text,
    )
    v(4pt)
    line(...)
  }
},
```

Replace with:

```typst
header: context {
  let pg = counter(page).get().first()
  if pg > 2 {
    // Suppress on cover (pg 0 has no header), TOC (pg 1), and first content page
    let headings = query(heading.where(level: 1).before(here()))
    let section-name = if headings.len() > 0 {
      upper(headings.last().body)
    } else {
      ""
    }
    let page-display = [
      #counter(page).display() of #context counter(page).final().first()
    ]
    grid(
      columns: (1fr, auto),
      align: (left + horizon, right + horizon),
      text(
        font: "{heading_font}",
        size: 8pt,
        fill: {_rgb(muted)},
        tracking: 0.05em,
      )[#section-name],
      text(
        font: "{heading_font}",
        size: 8pt,
        fill: {_rgb(muted)},
      )[#section-name #sym.dot.c Page #page-display],
    )
    v(4pt)
    line(length: 100%, stroke: 0.5pt + {_rgb(border)})
  }
},
```

The condition `pg > 2` suppresses the header on the cover page (page counter
resets to 1 at TOC) and on the TOC page itself. When no level-1 heading
precedes the current position (i.e. the document has no level-1 headings yet),
the section name is empty and the header degrades gracefully to just the page
number.

Note: The right column shows `SECTION NAME · Page N of M` rather than
repeating the document title, which is already visible on the logo header on
the first content page. The left column is blank (reserved for future logo
placement in headers if themes require it).

**Files to modify:**
- `src/inkline/typst/document_renderer.py` — `_preamble()`

---

#### Step 6 — OpenType figure variants

**Problem.** Table cells require tabular figures (fixed-width) for numeric
columns to align. Body copy benefits from old-style figures (proportional,
baseline-aligned) for typographic quality. Neither is applied.

**Design.** Apply at the style/rule level, not inline.

**Add to `_preamble()`** immediately after `#set text(...)`:

```typst
// OpenType figure variants — applied at style level
// Tabular figures in all table cells (fixed-width, columns align)
#show table.cell: set text(features: ("tnum": 1))

// Old-style figures in body paragraphs (proportional, typographically correct)
// Applied only to par content, not headings or table cells.
// Headings use lining figures (OpenType default) — no override needed.
#show par: set text(features: ("onum": 1))
```

The `show table.cell` rule overrides the `show par` rule for cells that
contain paragraph-wrapped content because Typst applies show rules in
specificity order, with `table.cell` being more specific than `par`.

**Caveat for implementers.** Not all fonts support `tnum` and `onum`.
The `Inter` font (Inkline default) fully supports both. Brands using fonts
without OT figure variants will see these features silently ignored by Typst —
there is no runtime error. No fallback is needed.

**Files to modify:**
- `src/inkline/typst/document_renderer.py` — `_preamble()`

---

#### Step 7 — Letter-spacing on uppercase labels

**Problem.** `#upper()` calls in component definitions (`rag-badge`, `metric-
box`, `source-note`) produce crowded uppercase text with no tracking. The
typographic convention is `0.08em` for uppercase labels.

**Design.** Add a `#let label-text(content)` helper that combines `upper()`
with tracking, and retrofit the three affected components.

**Add to `_component_defs()`:**

```typst
// Uppercase label with standard tracking
#let label-text(content, size: 8pt, color: rgb("#6B7280")) = {
  text(size: size, tracking: 0.08em, fill: color)[#upper(content)]
}
```

**Update `rag-badge`:**

```typst
// Before:
text(size: 8pt, weight: "bold", fill: white)[#upper(status)]

// After:
text(size: 8pt, weight: "bold", tracking: 0.08em, fill: white)[#upper(status)]
```

**Update `metric-box`:**

```typst
// Before:
text(size: 9pt, fill: {_rgb(muted)})[#upper(label)]

// After:
text(size: 9pt, tracking: 0.08em, fill: {_rgb(muted)})[#upper(label)]
```

The `source-note` component does not use `#upper()` so no change is needed
there.

Also apply tracking to the cover panel label emission in Step 1 — the `HIGHLIGHTS`
label and the per-metric label lines should both carry `tracking: 0.08em`.

**Files to modify:**
- `src/inkline/typst/document_renderer.py` — `_component_defs()`, and the
  cover panel Typst snippets emitted by `_cover_page()`

---

#### Step 8 — Section divider pages

**Problem.** Long documents (3+ major sections) have no visual break between
sections. Readers lose context when sections run together.

**Design.** Optionally insert a full-bleed section divider page before each
level-1 section when the document has three or more level-1 sections. The
divider is off by default and enabled by a `DocumentSpec` flag.

**Add to `DocumentSpec`:**

```python
section_dividers: bool = False  # NEW — insert divider pages between major sections
```

**New helper `_section_divider_page()`:**

```python
def _section_divider_page(self, section_number: int, heading: str) -> str:
    t = self.t
    accent = t.get("accent", "#1a3a5c")
    heading_font = t.get("heading_font", "Inter")
    return f"""// Section divider — {heading}
#page(
  fill: {_rgb(accent)},
  margin: (top: 0pt, bottom: 0pt, left: 0pt, right: 0pt),
  header: none,
  footer: none,
)[
  #align(center + horizon)[
    #v(1fr)
    #text(
      font: "{heading_font}",
      size: 11pt,
      weight: "bold",
      fill: white,
      tracking: 0.15em,
    )[#upper("Section {section_number}")]
    #v(0.6cm)
    #text(
      font: "{heading_font}",
      size: 36pt,
      weight: "bold",
      fill: white,
    )[{_esc(heading)}]
    #v(1fr)
  ]
]"""
```

**Change to `render_document()`.** When `spec.section_dividers` is `True` and
the document has three or more level-1 sections, insert a divider page before
each level-1 section:

```python
def render_document(self, spec: DocumentSpec) -> str:
    parts = [
        self._preamble(spec),
        self._heading_styles(),
        self._component_defs(),
        self._cover_page(spec),
        self._toc_page(),
    ]

    # Count level-1 sections to determine if dividers are appropriate
    l1_sections = [s for s in spec.sections if s.get("level", 1) == 1]
    use_dividers = spec.section_dividers and len(l1_sections) >= 3

    l1_counter = 0
    for section in spec.sections:
        if use_dividers and section.get("level", 1) == 1:
            l1_counter += 1
            parts.append(
                self._section_divider_page(l1_counter, section.get("heading", ""))
            )
        parts.append(self._render_section(section))

    return "\n\n".join(parts)
```

The same threshold applies to `render_from_markdown()`: count `# ` headings
before deciding whether to emit dividers.

**Files to modify:**
- `src/inkline/typst/document_renderer.py` — `DocumentSpec`, `render_document()`,
  `render_from_markdown()`, add `_section_divider_page()`

---

## API Changes Summary

### `DocumentSpec` additions

| Field | Type | Default | Phase |
|---|---|---|---|
| `cover_panel` | `dict[str, str] \| None` | `None` | 1 |
| `toc_panel` | `dict[str, Any] \| None` | `None` | 1 |
| `section_dividers` | `bool` | `False` | 2 |

All new fields are keyword-only with defaults so all existing call sites are
unaffected.

### No changes to `export_typst_document()` public signature

The public function in `src/inkline/typst/__init__.py` accepts `**kwargs`
which are forwarded to `DocumentSpec`. The new fields are automatically
available to callers:

```python
export_typst_document(
    markdown=md_text,
    output_path=str(OUTPUT),
    brand="minimal",
    title="Q1 Board Pack",
    cover_panel={
        "Total AUM": "$2.4B",
        "Active deals": "7",
        "IRR (gross)": "~22%",
    },
    section_dividers=True,
)
```

---

## Typst Version Requirement

The `par(spacing:)` parameter (Step 3) and `query(heading.where(level: 1).before(here()))`
(Step 5) both require Typst 0.11+. The `features:` parameter on `text()`
(Step 6) requires Typst 0.10+.

Before merging Phase 2 items, confirm Typst version with:

```bash
python3 -c "import typst; print(typst.__version__)"
```

If the installed version is below 0.11, the `par(spacing:)` call in Step 3
should be omitted (not wrapped in a try/except — just omitted with a comment).

---

## Test Plan

### Phase 1 tests (required before merge)

1. `test_cover_page_no_panel` — cover page with `cover_panel=None` must not
   contain any hardcoded metric values or "DEAL AT A GLANCE" text.
2. `test_cover_page_with_panel` — cover page with a two-entry `cover_panel`
   must include both values and labels verbatim.
3. `test_exhibit_counter_defs` — rendered document must contain
   `counter("figures")`, `counter("tables")`, `#let fig(`, `#let tbl(`.
4. `test_section_figure_exhibit` — a section with one `"type": "figure"`
   exhibit must emit a `#fig(` call containing the caption and source text.
5. `test_par_leading_not_tight` — rendered preamble must contain
   `leading: 1.5em` and must not contain `leading: 0.8em`.
6. `test_cover_panel_max_six_entries` — `cover_panel` with 10 entries: only
   entries 0–5 appear in output.

All six tests live in `tests/test_document_renderer.py` and must pass
with `pytest tests/test_document_renderer.py -q` before the Phase 1 branch
is merged.

### Phase 2 tests (required before merge)

7. `test_running_header_suppressed_on_cover` — rendered Typst must include
   the `pg > 2` guard so the header block is not emitted on pages 1–2.
8. `test_opentype_features_in_preamble` — rendered preamble must contain
   `"tnum"` and `"onum"` in `show` rules.
9. `test_label_text_tracking` — `_component_defs()` output must contain
   `tracking: 0.08em` at least twice (rag-badge and metric-box).
10. `test_section_dividers_inserted` — a `DocumentSpec` with
    `section_dividers=True` and four level-1 sections must emit four
    `Section divider —` comments in the output.
11. `test_section_dividers_not_inserted_below_threshold` — a `DocumentSpec`
    with `section_dividers=True` and only two level-1 sections must not emit
    any divider pages.

### Regression

After all changes, run the full test suite:

```bash
pytest tests/ -q
```

The suite must continue to pass without regressions. If `test_toc_page` or
any existing test checks for hardcoded prototype strings, those tests must be
updated to reflect the new parameterised behaviour — the old hardcoded content
is by definition being removed.

---

## Implementation Order

1. **Step 4** (tests) — write the six Phase 1 tests first with `pytest.mark.xfail`
   so they fail against the current code, confirming the test harness is correct.
2. **Step 1** (cover parameterisation) — removes the hardcoded cover coupling; broadest
   impact.
3. **Step 3** (line height) — single-line change, low risk, immediately visible
   improvement.
4. **Step 2** (exhibit numbering) — adds new API; verify counter definitions
   compile in a scratch Typst file before wiring into the renderer.
5. **Step 5** (running headers) — requires Typst `query()` which can be
   sensitive to document structure; verify in isolation before integrating.
6. **Step 6** (OpenType variants) — one `show` rule per variant; low risk.
7. **Step 7** (tracking) — small string changes to existing component defs.
8. **Step 8** (section dividers) — adds new `DocumentSpec` field and a new
   private method; implement last as it touches `render_document()` control
   flow.

---

## Files to Modify

| File | Changes |
|---|---|
| `src/inkline/typst/document_renderer.py` | All eight steps |
| `tests/test_document_renderer.py` | Create new (Steps 4, Phase 2 tests) |

No other files require modification. The `export_typst_document()` function in
`src/inkline/typst/__init__.py` already forwards `**kwargs` to `DocumentSpec`,
so the new fields are automatically available to callers without any change to
the public API.
