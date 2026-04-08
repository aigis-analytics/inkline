# Color Theory for Data Playbook

> **Purpose**: Guide the DesignAdvisor in selecting effective, accessible, and
> aesthetically sound colour palettes for charts, slides, and documents.
>
> **Authority sources**: ColorBrewer (Cynthia Brewer), WCAG 2.1, Datawrapper,
> Datylon, Atlassian Data Visualization Guide, Vision Australia.

---

## 1. The Three Palette Types

### 1.1 Sequential Palette

**What**: A single hue that progresses from light (low) to dark (high).

**When to use**:
- Data with a natural order from low to high (temperature, revenue, population).
- Heatmaps, choropleths, and any single-variable intensity display.
- When there is no meaningful midpoint.

**How to construct**:
- Choose one hue (e.g., blue).
- Vary lightness from ~95% (lightest) to ~20% (darkest).
- 5-7 steps is optimal; more steps become hard to distinguish.

**ColorBrewer examples**: Blues, Greens, Oranges, Purples, YlOrRd, BuGn.

```
Light ░░░░▒▒▒▒▓▓▓▓████ Dark
 Low                    High
```

---

### 1.2 Diverging Palette

**What**: Two contrasting hues meeting at a neutral midpoint.

**When to use**:
- Data with a meaningful centre point (zero, mean, target, break-even).
- Showing positive vs. negative deviation.
- Sentiment scales (disagree ↔ agree).
- Financial variance (above/below budget).

**How to construct**:
- Choose two contrasting hues (e.g., blue and red, green and brown).
- Both hues darken away from centre.
- Centre is light/neutral (white or light grey).
- Ensure the centre break represents a meaningful value.

**ColorBrewer examples**: RdBu, BrBG, PiYG, PRGn, RdYlGn.

```
Dark Blue ████▓▓▓▒▒▒░░░▒▒▒▓▓▓████ Dark Red
 Negative        Zero         Positive
```

**Special guidance**: If your data is asymmetric (more classes on one side), you
may shift the midpoint. For example, if most values are positive with a few
negatives, use more steps on the positive side.

---

### 1.3 Categorical (Qualitative) Palette

**What**: Distinct hues with no implied order — each colour represents a different
category.

**When to use**:
- Nominal data (product lines, regions, departments).
- Multi-series line charts, grouped bars, pie/donut segments.
- Any comparison where categories are unordered.

**How to construct**:
- Choose hues that are maximally distinct from each other.
- Keep saturation and lightness roughly equal so no category visually dominates.
- Limit to 6-8 colours maximum. Beyond 8, humans cannot reliably distinguish.

**ColorBrewer examples**: Set1, Set2, Set3, Pastel1, Dark2, Paired, Accent.

**Rules**:
- If there is a "highlight" category, make it saturated and bright; grey out the rest.
- If categories have cultural associations (e.g., political parties), respect them.
- The "Paired" scheme provides light/dark pairs — useful for related sub-categories.

---

## 2. The 60-30-10 Rule for Presentations

A balanced colour composition for slides and documents:

| Proportion | Role | Typical choice |
|------------|------|---------------|
| **60%** | Dominant / background | White, light grey, or off-white |
| **30%** | Secondary / supporting elements | Dark text, chart bodies, section headers |
| **10%** | Accent / emphasis | Brand colour, highlight, CTA |

### Application to Slides

- **Background** (60%): Clean, neutral. White or very light grey.
- **Text and chart frames** (30%): Dark grey or navy. All body copy, axis labels, gridlines.
- **Highlights** (10%): One strong brand colour for the key data point, callout
  box, or recommended option. This is what the eye is drawn to.

### Application to Charts

- Use grey for all "context" data series.
- Use the accent colour for the "hero" data series — the one the title references.
- This creates immediate visual focus without needing to read the legend.

```
Chart example:
  ████  Series A (grey — context)
  ████  Series B (grey — context)
  ████  Series C (BLUE — hero, matches action title)
```

---

## 3. Accessibility Requirements

### WCAG Contrast Ratios

| Element | Minimum ratio | WCAG level |
|---------|--------------|------------|
| Normal text (< 18pt) | 4.5 : 1 | AA |
| Large text (≥ 18pt or 14pt bold) | 3 : 1 | AA |
| Non-text elements (chart elements, icons) | 3 : 1 | AA (WCAG 2.1 SC 1.4.11) |
| Normal text (enhanced) | 7 : 1 | AAA |

### Colourblind-Safe Design

Approximately 8% of men and 0.5% of women have colour vision deficiency.
The most common form is red-green (deuteranopia/protanopia).

**Rules**:
1. **Never rely on colour alone** to convey meaning. Always pair colour with:
   - Shape (circles vs. squares vs. triangles)
   - Pattern (solid vs. hatched vs. dotted)
   - Text labels
   - Position
2. **Avoid red-green only** colour schemes. If you must use red and green (e.g.,
   RAG status), also use icons (checkmark, warning triangle, X mark).
3. **Test with a simulator**: Use tools like Coblis, Color Oracle, or the
   colourblind simulation in Figma/Adobe.
4. **Safe colourblind palettes**:
   - Blue + Orange (universally distinguishable)
   - Blue + Yellow
   - Purple + Green (better than red + green)
   - Viridis, Cividis, and Inferno colour maps (perceptually uniform)

### Adjacent Colour Contrast in Charts

WCAG 2.1 SC 1.4.11 requires a 3:1 contrast ratio between adjacent meaningful
elements. In charts, this means:
- Adjacent bars must contrast 3:1 with each other.
- Adjacent pie slices must contrast 3:1 with neighbours.
- Lines in a multi-series chart must be distinguishable by more than colour
  (add different dash patterns or marker shapes).

---

## 4. Colour for Meaning — Semantic Colour Conventions

Some colours carry inherent meaning in business contexts:

| Colour | Common meaning | Use in |
|--------|---------------|--------|
| **Red** | Negative, danger, loss, stop, below target | Financial losses, critical risk, declining metrics |
| **Green** | Positive, success, profit, go, on target | Financial gains, on-track status, growth |
| **Amber/Yellow** | Caution, warning, at risk | Moderate risk, approaching threshold |
| **Blue** | Neutral, professional, trust | Primary brand, default chart colour |
| **Grey** | Inactive, context, secondary | Benchmark data, gridlines, supporting series |

**Rules**:
- Respect semantic conventions — using green for losses confuses everyone.
- In financial contexts, use blue for actuals and grey for forecasts/projections.
- For RAG status, always define thresholds explicitly (not subjective judgment).
- Cultural awareness: red means luck/prosperity in Chinese culture — context
  matters for global audiences.

---

## 5. Constructing a Data Palette from a Brand Palette

Most organisations have a brand palette that was NOT designed for data
visualisation. Here is how to derive a data palette:

### Step 1: Start with the Brand Primary

- Use the brand's primary colour as the chart "hero" colour.

### Step 2: Create Tints and Shades

- Generate 5 lighter tints (add white) and 3 darker shades (add black).
- This gives you a sequential palette from one brand hue.

### Step 3: Select 2-3 Supporting Hues

- Choose colours that contrast with the primary and with each other.
- Use the colour wheel: analogous (adjacent) for harmony, complementary (opposite) for contrast.

### Step 4: Define a Grey Ramp

- Create 5-step grey scale (white → light grey → medium grey → dark grey → near-black).
- Used for: backgrounds, gridlines, secondary data, disabled states.

### Step 5: Validate Accessibility

- Check every foreground/background pair against WCAG ratios.
- Test the full palette through a colourblind simulator.
- Ensure adjacent chart colours pass the 3:1 test.

### Standard Data Palette Structure

```
Primary:     ■ Brand Blue (#1A73E8)
Sequential:  ░ ▒ ▓ █ ■  (5 steps of Primary, light to dark)
Categorical: ■ ■ ■ ■ ■ ■  (6-8 distinct hues)
Diverging:   ■■■ ░░░ ■■■  (Negative hue ← neutral → Positive hue)
Semantic:    ■ Red  ■ Amber  ■ Green  (RAG)
Grey ramp:   ░ ▒ ▓ █ ■  (5 steps, white to dark)
Accent:      ■ Bright accent for callouts / highlights
```

---

## 6. Colour Do's and Don'ts

### Do's

- DO use one colour palette consistently throughout a document/presentation.
- DO use colour to direct attention — highlight the "hero" data, grey the rest.
- DO validate all colour choices against WCAG AA contrast standards.
- DO use a colourblind-safe palette as the default.
- DO use white or very light backgrounds — dark backgrounds are harder to print
  and read.
- DO limit chart colours to 6-8 maximum. Group smaller categories into "Other."

### Don'ts

- DON'T use a rainbow (jet/spectral) colour map — it is not perceptually uniform,
  creates false boundaries, and fails for colourblind viewers.
- DON'T use highly saturated colours for large areas — they cause visual fatigue.
- DON'T use colour as the sole encoding — always pair with shape, pattern, or text.
- DON'T mix warm and cool hues randomly — use a consistent palette.
- DON'T use red and green as the only distinction — always add a secondary cue.
- DON'T place text on patterned or photographic backgrounds without an overlay.

---

## 7. Quick-Reference Decision Table

| Data type | Palette type | Example palette |
|-----------|-------------|----------------|
| Low → High (continuous) | Sequential | Blues, YlOrRd |
| Below ↔ Above midpoint | Diverging | RdBu, BrBG |
| Unordered categories | Categorical | Set2, Dark2 |
| Status (good/warning/bad) | Semantic RAG | Green / Amber / Red |
| Highlight one series | Grey + accent | All grey, one brand colour |
| Binary (yes/no, A/B) | Two-colour | Blue + Orange |

---

## 8. Named Palette Reference

### Recommended Colourblind-Safe Palettes

| Name | Source | Type | Colours | Notes |
|------|--------|------|---------|-------|
| **Viridis** | Matplotlib | Sequential | Yellow → Green → Blue → Purple | Perceptually uniform; excellent |
| **Cividis** | Matplotlib | Sequential | Yellow → Blue | Optimised for deuteranopia |
| **Inferno** | Matplotlib | Sequential | Black → Red → Yellow → White | High contrast |
| **Okabe-Ito** | Masataka Okabe | Categorical | 8 colours | Designed for colour vision deficiency |
| **ColorBrewer Set2** | Cynthia Brewer | Categorical | 8 colours | Colourblind safe |
| **ColorBrewer Dark2** | Cynthia Brewer | Categorical | 8 colours | Colourblind safe, higher saturation |
| **Tableau 10** | Tableau | Categorical | 10 colours | Widely used, good separation |
| **IBM Design** | IBM | Categorical | 14 colours | Accessibility-first design |

---

## References

- [ColorBrewer 2.0](https://colorbrewer2.org/)
- [ColorBrewer — Scheme Types](https://colorbrewer2.org/learnmore/schemes_full.html)
- [Atlassian — How to Choose Colors for Data Visualization](https://www.atlassian.com/data/charts/how-to-choose-colors-data-visualization)
- [Datylon — Guide to Data Visualization Color Palettes](https://www.datylon.com/blog/a-guide-to-data-visualization-color-palette)
- [Datawrapper — Colors for Data Vis Style Guides](https://www.datawrapper.de/blog/colors-for-data-vis-style-guides)
- [Let Data Speak — Mastering Color in Data Visualizations](https://letdataspeak.com/mastering-color-in-data-visualizations/)
- [CleanChart — Best Color Palettes for Charts (2026)](https://www.cleanchart.app/blog/data-visualization-color-palettes)
- [WebAIM — Contrast Checker](https://webaim.org/resources/contrastchecker/)
- [WebAIM — Contrast and Color Accessibility](https://webaim.org/articles/contrast/)
- [Vision Australia — 60-30-10 Accessible Colour Rule](https://www.visionaustralia.org/business-consulting/digital-access/Creating-accessible-digital-colour-palettes-60-30-10-design-rule)
- [Venngage — Accessible Color Palettes](https://venngage.com/blog/accessible-colors/)
- [WCAG 2.1 — SC 1.4.11 Non-text Contrast](https://www.w3.org/WAI/WCAG21/Understanding/non-text-contrast.html)
