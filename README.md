# Inkline

Branded document generation toolkit — HTML, PDF, and Google Slides.

## Installation

```bash
pip install inkline              # HTML only (core)
pip install inkline[pdf]         # + WeasyPrint PDF
pip install inkline[slides]      # + Google Slides API
pip install inkline[all]         # Everything
```

## Quick Start

```python
from inkline import export_html, export_pdf

# Aigis-branded HTML report
export_html("# My Report\n\nContent...", "report.html", brand="aigis")

# TVF-branded PDF
export_pdf("# Quarterly Review\n\n...", "review.pdf", brand="tvf")
```

## Brands

- **aigis** — Aigis Analytics (navy/teal)
- **tvf** — Tamarind Village Foundation (olive/gold)
- **minimal** — Clean, unbranded

## CLI

```bash
inkline-html report.md --brand aigis --title "My Report"
inkline-pdf  report.md --brand tvf --title "TVF Review"
```
