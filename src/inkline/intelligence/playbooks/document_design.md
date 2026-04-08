# Document Design Patterns Playbook

> **Purpose**: Guide the DesignAdvisor in designing professional reports,
> memos, white papers, and board-level documents with appropriate layout,
> formatting, and structural patterns.
>
> **Authority sources**: Venngage, Jirav, FASB formatting standards,
> UK Government Analysis Function, BCG/McKinsey document conventions.

---

## 1. Document Type Matrix

Different document types demand different design approaches:

| Document type | Pages | Density | Visual style | Audience |
|--------------|-------|---------|-------------|----------|
| **Executive summary** | 1-2 | Low | KPI callouts, bullet list | C-suite |
| **Board memo** | 2-5 | Medium | Structured sections, tables | Board / NED |
| **Investor deck** | 10-15 | Medium | Charts, clean layout | Investors / LPs |
| **White paper** | 5-30 | High | Long-form, figures, pullquotes | Industry / technical |
| **Strategy report** | 20-50 | High | Charts, frameworks, tables | Management team |
| **Dashboard report** | 1-4 | Very high | KPIs, mini-charts, RAG status | Operations / PMO |
| **Financial model memo** | 3-10 | High | Tables, sensitivity grids | Finance team / lenders |

---

## 2. Executive Summary Layout

The executive summary must stand alone — decisions may be made based on it without
reading the full document.

### Structure

```
┌──────────────────────────────────────────┐
│  TITLE / DOCUMENT HEADER                  │
│  Date | Author | Classification           │
├──────────────────────────────────────────┤
│                                          │
│  SITUATION (1-2 sentences)               │
│  Context and background                  │
│                                          │
│  COMPLICATION (1-2 sentences)            │
│  The problem or change                   │
│                                          │
│  RESOLUTION / RECOMMENDATION             │
│  • Key recommendation 1                  │
│  • Key recommendation 2                  │
│  • Key recommendation 3                  │
│                                          │
├──────────────────────────────────────────┤
│  KEY METRICS                             │
│  ┌────┐  ┌────┐  ┌────┐  ┌────┐        │
│  │$12M│  │ 23%│  │ 4.2│  │ A+ │        │
│  │Rev │  │Grow│  │NPS │  │Cred│        │
│  └────┘  └────┘  └────┘  └────┘        │
├──────────────────────────────────────────┤
│  CRITICAL RISKS / ASSUMPTIONS            │
│  Red flag items that require attention    │
└──────────────────────────────────────────┘
```

### Rules

- **Length**: Proportional to full report — typically 10-15% of total length.
  Most executive summaries are 1-2 pages.
- **Standalone**: Must include conclusions and recommendations, not just preview
  what follows.
- **Findings**: Limit to 3-5 findings. Each finding should be a complete sentence
  with a specific number or fact.
- **Metrics**: Display 3-5 KPIs as "big number" callouts — not buried in text.
- **Follow SCR**: Situation-Complication-Resolution in that order.

---

## 3. Financial Table Formatting

### Standard Formatting Rules

| Element | Rule | Rationale |
|---------|------|-----------|
| **Alignment** | Right-align numbers, left-align row labels | Aligns decimal places for easy scanning |
| **Number format** | Use thousands separator (1,234,567) | Readability |
| **Units** | State in column header ("$M", "000s") not in every cell | Reduces clutter |
| **Negatives** | Use parentheses (1,234) not minus sign -1,234 | Financial convention |
| **Decimals** | One decimal for percentages, zero for large currencies | Appropriate precision |
| **Row shading** | Alternate row backgrounds (zebra striping) | Reduces reading errors |
| **Totals** | Bold, with top border (single line) and bottom border (double line) | Clearly separates totals |
| **Sub-totals** | Bold, with single top border | Distinguishes from line items |
| **Headers** | Bold, bottom-border, centre-aligned (or right-aligned matching data) | Anchors the column |
| **Column width** | Consistent across similar columns | Professional appearance |

### Financial Statement Layout

```
┌──────────────────────────────────────────────────────┐
│                        FY2024    FY2025    FY2026E   │
│ Revenue                                              │
│   Product revenue       12,345    14,567    16,200   │
│   Service revenue        3,456     4,123     4,800   │
│                        ───────   ───────   ───────   │
│ Total Revenue           15,801    18,690    21,000   │
│                                                      │
│ Cost of Revenue         (9,480)  (11,214)  (12,390)  │
│                        ───────   ───────   ───────   │
│ Gross Profit             6,321     7,476     8,610   │
│ Gross Margin             40.0%     40.0%     41.0%   │
│                                                      │
│ Operating Expenses                                   │
│   SG&A                  (2,844)   (3,178)   (3,360)  │
│   R&D                   (1,580)   (1,869)   (2,100)  │
│                        ───────   ───────   ───────   │
│ Total OpEx              (4,424)   (5,047)   (5,460)  │
│                                                      │
│                        ═══════   ═══════   ═══════   │
│ EBITDA                   1,897     2,429     3,150   │
│ EBITDA Margin            12.0%     13.0%     15.0%   │
└──────────────────────────────────────────────────────┘
```

### Table Design Do's and Don'ts

- DO use consistent table numbering (Table 1, Table 2, ...) for cross-reference.
- DO include a descriptive caption above each table.
- DO highlight variance or delta columns with shading or colour.
- DO use footnotes for assumptions and adjustments.
- DON'T use gridlines on every cell — minimal lines (header border + total borders) are cleaner.
- DON'T merge cells unless absolutely necessary — it breaks copy-paste and accessibility.
- DON'T use colour as the only way to encode information — always pair with text.

---

## 4. Risk Assessment Displays

### RAG Status (Red / Amber / Green)

| Colour | Meaning | Threshold example |
|--------|---------|-------------------|
| **Green** | On track, no issues | Within 5% of plan |
| **Amber** | At risk, needs attention | 5-15% deviation from plan |
| **Red** | Critical, requires immediate action | >15% deviation from plan |

**Rules for RAG displays**:
- Define thresholds explicitly — RAG without defined criteria is subjective and unreliable.
- Use filled circles (●) or squares (■) rather than just background colour — supports colourblind users.
- Always include a text explanation alongside RAG colour.
- In a dashboard, group all Red items at the top for immediate visibility.

### Risk Heatmap / Matrix

```
              IMPACT
              Low    Medium   High    Critical
   Likely    │  ■A  │   ■A   │  ■R   │   ■R   │
LIKELIHOOD   │      │        │       │        │
   Possible  │  ■G  │   ■A   │  ■A   │   ■R   │
             │      │        │       │        │
   Unlikely  │  ■G  │   ■G   │  ■A   │   ■A   │
             │      │        │       │        │
   Rare      │  ■G  │   ■G   │  ■G   │   ■A   │
```

**Rules**:
- Impact on X-axis (left-to-right, increasing severity).
- Likelihood on Y-axis (bottom-to-top, increasing probability).
- Plot individual risks as labelled dots on the matrix.
- Include a risk register table alongside with mitigation actions.

---

## 5. Callout Boxes and Pull Quotes

### Callout Box Types

| Type | Visual treatment | Use case |
|------|-----------------|----------|
| **Key insight** | Coloured left border + light background | Highlighting the "so what" of a section |
| **Warning / risk** | Red or amber border + icon | Flagging critical assumptions or risks |
| **Definition** | Grey background, italic | Defining technical terms |
| **Pull quote** | Large text, thin borders top/bottom | Emphasising a key statement |
| **Case study** | Full box with background | Real-world example or testimonial |
| **Calculation note** | Monospace font, grey background | Methodology or formula detail |

### Rules

- Maximum 1-2 callouts per page — more dilutes their impact.
- Callouts should be scannable independently of surrounding text.
- Pull quotes should be exact quotes with attribution.
- Use consistent styling for each callout type throughout the document.

---

## 6. Dashboard-Style Report Pages

### Layout Principles

A dashboard page compresses maximum information into a single view:

```
┌──────────────────────────────────────────────┐
│  REPORT TITLE                   Period: Q3   │
├──────────────────────────────────────────────┤
│ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐        │
│ │ KPI1 │ │ KPI2 │ │ KPI3 │ │ KPI4 │        │
│ │ $12M │ │ +23% │ │ 4.2  │ │  ●G  │        │
│ └──────┘ └──────┘ └──────┘ └──────┘        │
├─────────────────────┬────────────────────────┤
│                     │                        │
│   TREND CHART       │   COMPOSITION CHART    │
│   (line/area)       │   (bar/donut)          │
│                     │                        │
├─────────────────────┴────────────────────────┤
│                                              │
│   TABLE / DETAIL VIEW                        │
│   (top issues, ranked items, or register)    │
│                                              │
├──────────────────────────────────────────────┤
│  Commentary / key observations               │
│  Source | Period | Prepared by                │
└──────────────────────────────────────────────┘
```

### Rules

- KPI row at the top — 3-5 metrics with trend arrows.
- Each KPI shows: metric name, current value, comparison (vs. target or prior period), RAG indicator.
- Mid-section: 1-2 charts providing context behind the KPIs.
- Bottom section: Detail table or risk register.
- Include a brief commentary section — numbers without narrative are incomplete.

---

## 7. Document Type-Specific Formatting

### White Paper

| Element | Standard |
|---------|----------|
| Page size | A4 or US Letter |
| Margins | 1 inch (2.54cm) all sides |
| Columns | Single column (not multi-column — poor on mobile) |
| Font size | 11-12pt body, 16-24pt headings |
| Figures | Numbered, captioned, centred |
| Header/footer | Page number + document title |
| Table of contents | Required for 5+ pages |
| Abstract | 150-250 words |
| Citations | Numbered endnotes or author-date |

### Board Memo

| Element | Standard |
|---------|----------|
| Length | 2-5 pages maximum |
| Structure | Purpose → Background → Analysis → Recommendation → Decision Required |
| Tone | Formal, third person |
| Tables | Summary only — detail in appendix |
| Decision box | Clearly framed "The Board is asked to approve..." |
| Appendices | Reference only — board members may not read them |

### Investor Deck

| Element | Standard |
|---------|----------|
| Slides | 10-15 (Guy Kawasaki's 10/20/30 rule) |
| Font size | Minimum 24pt body, 36pt titles |
| Content per slide | One key message |
| Financials | 3-year projections, high-level (detail in data room) |
| Design | Clean, modern, strong brand presence |
| Call to action | Clear ask on final slide (amount, terms, timeline) |

---

## 8. Page Layout Principles

### Grid System

- Use a consistent grid (12-column for complex layouts, 6-column for simple).
- All elements should snap to grid boundaries.
- Margins create breathing room — never crowd content to the edges.

### Visual Hierarchy

1. **Primary**: Headline / title / key metric (largest, boldest).
2. **Secondary**: Sub-headings, chart titles, callout boxes.
3. **Tertiary**: Body text, table data, captions.
4. **Quaternary**: Footnotes, source lines, metadata.

### White Space

- White space is not wasted space — it directs attention and reduces cognitive load.
- Minimum 20% of any page should be white space.
- Group related elements with tight spacing; separate unrelated elements with generous spacing.

---

## 9. Anti-Patterns

| Anti-pattern | Problem | Fix |
|-------------|---------|-----|
| Wall of text | No visual entry point; readers skip | Break into sections with headings, callouts, and charts |
| Inconsistent formatting | Different styles per section | Use document template with defined styles |
| Overuse of colour | Visual noise, unprofessional | Limit to brand palette; use colour with purpose |
| Missing page numbers | Hard to reference in meetings | Always include page/slide numbers |
| Buried recommendations | Reader must hunt for the ask | Put recommendations in exec summary AND a dedicated section |
| Decimal overload | False precision (12.3456%) | Round to meaningful precision (12.3% or 12%) |
| Missing units | "Revenue: 45" — 45 what? | Always label units ($M, %, headcount) |

---

## References

- [Venngage — Executive Summary Report Format](https://venngage.com/blog/executive-summary-report-format/)
- [Jirav — Executive Summary Report Best Practices](https://www.jirav.com/blog/executive-summary-report-financial-reporting-best-practices)
- [AccountingWare — Financial Statement Formatting Best Practices](https://accountingware.com/activreporter/blog/formatting-best-practices-for-financial-statements)
- [ClearPoint Strategy — RAG Status Guide](https://www.clearpointstrategy.com/blog/establish-rag-statuses-for-kpis)
- [BestOutcome — RAG Status Best Practice](https://bestoutcome.com/knowledge-centre/how-many-rags/)
- [Uplift Content — White Paper Design Best Practices](https://www.upliftcontent.com/blog/white-paper-design-best-practices/)
- [Venngage — White Paper Examples](https://venngage.com/blog/white-paper-examples/)
- [UK ONS — Data Visualisation Service Manual](https://service-manual.ons.gov.uk/data-visualisation)
- [Devine Consulting — Finance Report Template Guide](https://devineconsultingllc.com/create-a-finance-report-template-in-word-step-by-step-guide/)
