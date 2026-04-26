---
domain: typography
audience: [claude-code, design-advisor]
slide_type_relevance: [all]
brand_affinity: []
last_updated: "2026-04-26"
version: "1.0.0"
description: "Font selection, type hierarchies, and typographic best practices for slides and documents."
---

# Typography for Presentations Playbook

> **Purpose**: Guide the DesignAdvisor in selecting fonts, establishing type
> hierarchies, and applying typographic best practices for slides, reports, and
> documents.
>
> **Authority sources**: Slidor, Whitepage Studio, Figma resource library, Canva
> font pairing guide, TypeType, Monotype type styles guide.

---

## 1. Font Classification Reference

Understanding font anatomy helps the DesignAdvisor make informed pairing decisions.

### Major Font Categories

| Category | Characteristics | Personality | Best for |
|----------|----------------|------------|----------|
| **Serif** | Small strokes (serifs) at letter endpoints | Traditional, authoritative, elegant | Long-form reading, formal documents, headings |
| **Sans-serif** | No serifs; clean endpoints | Modern, clean, neutral | Slides, dashboards, UI, body text on screen |
| **Slab serif** | Thick, blocky serifs | Bold, confident, contemporary | Headlines, callouts, posters |
| **Monospace** | Equal character width | Technical, code-like | Code snippets, data tables, financial figures |
| **Display/Script** | Decorative, stylised | Creative, unique, expressive | Titles only (NEVER for body text) |

### Sub-categories That Matter for Pairing

| Sub-category | Examples | Key trait |
|-------------|----------|-----------|
| **Humanist sans** | Gill Sans, Frutiger, Lucida Grande, Open Sans | Calligraphic warmth; most readable sans-serif |
| **Geometric sans** | Futura, Avenir, Century Gothic, Montserrat | Circle-based; modern and clean |
| **Grotesque/Neo-grotesque** | Helvetica, Arial, Roboto, Inter | Neutral, ubiquitous, workmanlike |
| **Old-style serif** | Garamond, Bembo, Caslon, Palatino | Diagonal stress; classic elegance |
| **Transitional serif** | Times New Roman, Georgia, Baskerville | Vertical stress; professional |
| **Modern serif** | Didot, Bodoni, Playfair Display | High contrast; dramatic |

---

## 2. Font Pairing Rules

### The Golden Rule

**Pair fonts that contrast in style but share proportions.** Two fonts should look
different enough to establish hierarchy, but their x-height and letter width
should be similar enough that they feel cohesive.

### Proven Pairing Strategies

| Strategy | How it works | Example |
|----------|-------------|---------|
| **Serif heading + Sans body** | Classic contrast | Playfair Display + Source Sans Pro |
| **Sans heading + Serif body** | Modern contrast | Montserrat + Lora |
| **Geometric + Humanist** | Structural contrast | Futura + Open Sans |
| **Bold weight + Light weight** | Weight contrast within one family | Roboto Bold + Roboto Light |
| **Superfamily** | Use one type family with multiple optical sizes | IBM Plex Sans + IBM Plex Serif |

### Historical Pairing Compatibility

| Serif sub-category | Pairs well with | Examples |
|-------------------|----------------|----------|
| Old-style (Garamond, Caslon) | Humanist sans (Gill Sans, Open Sans) | Garamond heading + Open Sans body |
| Transitional (Times, Georgia) | Geometric sans (Futura, Avenir) | Georgia heading + Avenir body |
| Modern (Bodoni, Didot) | Grotesque sans (Helvetica, Inter) | Bodoni heading + Inter body |
| Slab (Rockwell, Clarendon) | Geometric sans (Montserrat, Poppins) | Rockwell heading + Poppins body |

### What NOT to Pair

- Two serif fonts from the same sub-category (too similar; no contrast).
- Two decorative/display fonts (visual chaos).
- Fonts with clashing x-heights (one tall, one squat).
- More than 2 font families in a single document (3 in rare cases with a monospace).

---

## 3. Type Scale for Presentations

### Recommended Size Hierarchy (16:9 slides at 1920x1080)

| Element | Size range | Weight | Notes |
|---------|-----------|--------|-------|
| **Slide title** | 28-36pt | Bold | The primary visual anchor |
| **Action title** | 18-24pt | Bold | Consulting-style insight statement |
| **Section heading** | 20-28pt | Bold or Semi-bold | Section divider slides |
| **Sub-heading** | 16-20pt | Semi-bold | Within-slide section labels |
| **Body text / bullets** | 14-18pt | Regular | Never smaller than 14pt on slides |
| **Chart title** | 14-16pt | Bold | Describes the exhibit |
| **Chart labels / axis** | 10-12pt | Regular | Readable at projection distance |
| **Footnote / source** | 8-10pt | Light | Bottom of slide, de-emphasized |
| **KPI / big number** | 36-72pt | Bold | Hero metric callouts |

### Minimum Readable Sizes

| Context | Absolute minimum | Recommended minimum |
|---------|-----------------|---------------------|
| Projected slide (large room) | 18pt body | 24pt body |
| Projected slide (meeting room) | 14pt body | 18pt body |
| Printed report (A4/Letter) | 9pt body | 11pt body |
| Screen dashboard | 12pt body | 14pt body |
| PDF document | 10pt body | 11-12pt body |

---

## 4. Type Scale for Documents

### Recommended Size Hierarchy (A4/Letter reports)

| Element | Size | Weight | Spacing |
|---------|------|--------|---------|
| **Document title** | 24-32pt | Bold | 1.0-1.2 line height |
| **H1 (Chapter)** | 18-24pt | Bold | Space before: 24pt |
| **H2 (Section)** | 14-18pt | Bold | Space before: 18pt |
| **H3 (Sub-section)** | 12-14pt | Bold or Semi-bold | Space before: 12pt |
| **Body text** | 10-12pt | Regular | 1.3-1.5 line height |
| **Table text** | 9-11pt | Regular | 1.2 line height |
| **Caption** | 9-10pt | Italic or Regular | Below figures/tables |
| **Footnote** | 8-9pt | Regular | Bottom of page |

---

## 5. Line Spacing and Readability

### Line Height (Leading)

- **Body text**: 1.3-1.5x the font size (e.g., 12pt text with 16-18pt leading).
- **Headings**: 1.0-1.2x the font size (tighter than body).
- **Bullet lists**: 1.2-1.4x with additional spacing between items.
- **Tables**: 1.1-1.3x (tighter to fit content).

### Paragraph Spacing

- Use **space-after** (not blank lines) to separate paragraphs.
- Typically 50-100% of body font size (e.g., 6-12pt after a 12pt body paragraph).
- First paragraph after a heading: no extra space before.

### Line Length

- **Optimal**: 50-75 characters per line (including spaces) for body text.
- **Too short** (< 40 chars): Choppy reading; too many line breaks.
- **Too long** (> 90 chars): Eye loses its place when returning to the next line.
- For wide pages, use wider margins or a two-column layout to control line length.

---

## 6. Text Alignment

| Alignment | When to use | When NOT to use |
|-----------|------------|-----------------|
| **Left-aligned** | Default for all body text, bullets, paragraphs | — |
| **Centre-aligned** | Title slides, section dividers, short headings, KPI numbers | Body text, paragraphs, long headings |
| **Right-aligned** | Numeric columns in tables, dates, page numbers | Body text, headings |
| **Justified** | Never in slides; rarely in reports | Almost always — it creates uneven word spacing |

---

## 7. Safe Font Recommendations

### Universally Available (System Fonts)

| Font | Category | Strengths |
|------|----------|-----------|
| **Arial / Helvetica** | Neo-grotesque sans | Ubiquitous, safe, neutral |
| **Calibri** | Humanist sans | Default in Office; clean |
| **Georgia** | Transitional serif | Excellent screen readability |
| **Times New Roman** | Transitional serif | Formal; widely available |
| **Courier New** | Monospace | Code and financial tables |
| **Segoe UI** | Humanist sans | Windows system font; modern |

### Recommended Open-Source Fonts

| Font | Category | Ideal for | Source |
|------|----------|-----------|--------|
| **Inter** | Neo-grotesque sans | UI, dashboards, slides | Google Fonts |
| **Roboto** | Neo-grotesque sans | Clean body text | Google Fonts |
| **Open Sans** | Humanist sans | Versatile body text | Google Fonts |
| **Montserrat** | Geometric sans | Modern headings | Google Fonts |
| **Lato** | Humanist sans | Professional body text | Google Fonts |
| **Source Sans Pro** | Humanist sans | Adobe's open-source workhorse | Google Fonts |
| **Poppins** | Geometric sans | Friendly headings | Google Fonts |
| **Merriweather** | Serif | Long-form reading | Google Fonts |
| **Lora** | Serif | Elegant body/heading | Google Fonts |
| **Playfair Display** | Modern serif | Dramatic headings | Google Fonts |
| **IBM Plex Sans/Serif/Mono** | Superfamily | Full system (body + code) | Google Fonts |
| **Fira Code** | Monospace | Code with ligatures | Google Fonts |
| **JetBrains Mono** | Monospace | Code and data tables | JetBrains |

---

## 8. Typography in Data Visualization

### Chart Text Hierarchy

```
Chart Title (Bold, 14-16pt)          ← What the chart shows
  Subtitle / unit label (Regular, 11-12pt)  ← Context (units, date range)
    Axis labels (Regular, 10-11pt)    ← Category/value labels
      Data labels (Regular, 9-10pt)   ← Values on bars/points
        Source (Light, 8pt)           ← Data provenance
```

### Font Choice for Charts

- Use a **sans-serif** font for all chart text (better legibility at small sizes).
- Use **tabular (monospaced) numerals** for data labels and tables — digits
  should align vertically (compare "111" vs "111" — tabular nums line up).
- Avoid italic in charts (hard to read at small sizes).
- Bold only the chart title; everything else is regular weight.

### Number Formatting in Charts

| Format | Use for | Example |
|--------|---------|---------|
| Thousands separator | Values > 999 | 1,234 not 1234 |
| K/M/B suffix | Large axis values | $1.2M not $1,200,000 |
| One decimal % | Percentages | 12.3% not 12.34% |
| No decimals | Integer counts | 150 not 150.0 |
| Currency prefix | Money | $1,234 not 1,234$ |
| Consistent precision | All values in one chart | All to 1dp or all to 0dp |

---

## 9. Anti-Patterns

| Anti-pattern | Problem | Fix |
|-------------|---------|-----|
| More than 2 font families | Visual inconsistency, unprofessional | Pick one heading + one body font (+ optional monospace) |
| All caps body text | Slower reading (no ascender/descender cues) | Use sentence case; reserve ALL CAPS for very short labels |
| Tiny text on slides | Unreadable from the back of the room | Minimum 14pt on slides, 18pt preferred |
| Decorative fonts for body | Illegible, distracting | Display fonts for titles only |
| Inconsistent sizes | No visual hierarchy | Define a type scale and stick to it |
| Justified text | Uneven word spacing, "rivers" of white | Left-align all body text |
| Low-contrast text | Fails accessibility, hard to read | 4.5:1 minimum for body text (WCAG AA) |
| Proportional numbers in tables | Numbers don't align vertically | Use tabular/monospaced numerals |

---

## 10. Decision Table — Font Selection

| Context | Heading font | Body font | Size scale |
|---------|-------------|-----------|-----------|
| Corporate presentation | Montserrat Bold | Open Sans Regular | 28 / 18 / 14 / 10 |
| Investor deck | Playfair Display | Lato Regular | 36 / 20 / 16 / 10 |
| Technical report | IBM Plex Sans Bold | IBM Plex Sans Regular | 18 / 12 / 11 / 9 |
| Financial model memo | Inter Semi-bold | Inter Regular | 14 / 11 / 10 / 8 |
| Dashboard | Inter Bold | Inter Regular | 16 / 13 / 11 / 9 |
| White paper | Merriweather Bold | Source Sans Pro | 24 / 14 / 12 / 9 |
| Board memo | Georgia Bold | Calibri Regular | 16 / 12 / 11 / 9 |

---

## References

- [Slidor — Best Fonts for PowerPoint Presentations](https://www.slidor.agency/blog/best-fonts-powerpoint-presentations-designers-guide)
- [Whitepage Studio — Best Font for Presentations (2026)](https://www.whitepage.studio/blog/the-ultimate-guide-for-using-fonts-in-decks-presentations)
- [Figma — Font Pairings Resource Library](https://www.figma.com/resource-library/font-pairings/)
- [Canva — The Ultimate Guide to Font Pairing](https://www.canva.com/learn/the-ultimate-guide-to-font-pairing/)
- [Visme — Font Combinations for Infographics](https://visme.co/blog/font-combinations-for-infographics/)
- [InkPPT — 10 Tips for Combining Fonts in PowerPoint](https://www.inkppt.com/post/essential-tips-combining-fonts-powerpoint)
- [TypeType — 10 Best Fonts for Professional Presentations (2025)](https://typetype.org/blog/10-best-fonts-for-professional-powerpoint-presentations-in-2025/)
- [SlideModel — Best Font for PowerPoint](https://slidemodel.com/best-font-for-powerpoint/)
- [Monotype — Guide to Type Styles](https://www.monotype.com/resources/guide-type-styles)
- [Design Your Way — How to Pair Fonts](https://www.designyourway.net/blog/how-to-pair-fonts/)
