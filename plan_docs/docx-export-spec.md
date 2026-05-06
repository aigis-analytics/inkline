# Inkline DOCX Export Spec

**Status:** Proposed  
**Date:** 2026-05-06

## Goal

Add native `.docx` document export to Inkline so Markdown or report-style
content can be rendered to Microsoft Word format in addition to existing PDF,
HTML, and PPTX-related outputs.

## Current State

Inkline currently supports:

- `.docx` as an input format in Draft Mode and upload UX
- PDF output for documents
- PDF and PPTX output for decks
- HTML output for documents

Inkline does **not** currently have a native `.docx` export path.

## Scope

This feature adds native Word export for **documents**.

It does not attempt to:

- serialize slide decks into editable `.docx` slide-like layouts
- preserve every visual attribute from Typst/PDF output
- replace Typst as the publication-quality document backend

The target is structurally correct, editable, branded-enough Word output.

## Public Surface

### Python API

Add:

```python
from inkline import export_docx
```

and:

```python
path = export_docx(markdown, output_path="report.docx", brand="minimal")
```

### CLI

Add a dedicated CLI:

```bash
inkline-docx report.md --brand minimal --title "My Report"
```

This mirrors `inkline-pdf` and `inkline-html`.

### Capability Manifest

Add `docx` to exported capabilities for document output discovery.

## Implementation

### Module

Create:

`src/inkline/docx/__init__.py`

with:

- `export_docx(...)`
- a small Markdown-to-Word renderer

### Dependency

Use `python-docx`.

This should be a declared package dependency rather than an undocumented local
assumption.

### Rendering Model

Support these Markdown/document structures:

- H1/H2/H3 headings
- normal paragraphs
- bullet lists
- numbered lists
- inline bold / italic / code
- fenced code blocks
- blockquotes
- horizontal rules
- tables

### Brand / document chrome

Apply light document styling:

- title metadata
- default margins
- body font
- heading hierarchy
- optional footer line containing brand/confidentiality/date

This should be simpler than Typst output, but consistent and usable.

## Tests

Add tests that verify:

1. a `.docx` file is created
2. title extraction works
3. headings and list items are preserved
4. table export creates Word tables

## Documentation

Update:

- `README.md`
- package docstrings
- capability descriptions

to distinguish clearly between:

- `.docx` input
- `.docx` native output

## Acceptance Criteria

1. `export_docx()` exists and writes a readable `.docx`
2. `inkline-docx` works from the CLI
3. tests cover core structure export
4. README no longer implies `.docx` support ambiguously
