# Open Source Chart & Template Libraries Playbook

> **Purpose**: Guide the DesignAdvisor in understanding available open-source
> visualisation resources, libraries, and design systems that Inkline can
> reference or integrate with.
>
> **Authority sources**: Library documentation, GitHub repositories, government
> design system specifications.

---

## 1. JavaScript Charting Libraries

### 1.1 D3.js (Data-Driven Documents)

| Attribute | Detail |
|-----------|--------|
| **URL** | [https://d3js.org](https://d3js.org) |
| **License** | BSD 3-Clause |
| **GitHub stars** | 108k+ |
| **Approach** | Low-level; binds data to DOM elements for full control |
| **Rendering** | SVG (default), Canvas optional |
| **Learning curve** | Steep |
| **Best for** | Custom, bespoke visualisations; interactive explorations |

**Gallery**: [Observable D3 Gallery](https://observablehq.com/@d3/gallery) —
hundreds of categorised examples including:
- Bar charts, histograms, line charts
- Scatter plots, bubble charts
- Sankey diagrams, chord diagrams, network graphs
- Geographic maps (choropleth, bubble, projection)
- Treemaps, sunbursts, circle packing
- Ridgeline, violin, density plots

**When to reference D3**:
- When Inkline needs inspiration for unusual or custom chart types.
- When the target output is interactive SVG for web.
- As a source of chart layout algorithms (force simulation, treemap tiling, etc.).

**Key sub-libraries**:
- `d3-scale` — mapping data to visual encodings
- `d3-shape` — generating SVG path data for arcs, areas, lines
- `d3-geo` — geographic projections
- `d3-hierarchy` — treemaps, dendrograms, circle packing
- `d3-sankey` — Sankey diagram layout
- `d3-force` — force-directed graph layout

---

### 1.2 Chart.js

| Attribute | Detail |
|-----------|--------|
| **URL** | [https://www.chartjs.org](https://www.chartjs.org) |
| **License** | MIT |
| **GitHub stars** | 64k+ |
| **Approach** | High-level; declarative config objects |
| **Rendering** | HTML5 Canvas |
| **Learning curve** | Low |
| **Best for** | Quick, attractive charts with minimal code |

**Built-in chart types** (8 core):
1. Line
2. Bar
3. Radar
4. Doughnut
5. Pie
6. Polar Area
7. Bubble
8. Scatter

**When to reference Chart.js**:
- Default configurations and design patterns for standard chart types.
- Animation and interaction patterns (hover tooltips, click handlers).
- As a benchmark for "good defaults" — Chart.js ships with sensible styling.

---

### 1.3 Apache ECharts

| Attribute | Detail |
|-----------|--------|
| **URL** | [https://echarts.apache.org](https://echarts.apache.org) |
| **License** | Apache 2.0 |
| **GitHub stars** | 60k+ |
| **Approach** | Declarative JSON options; rich built-in types |
| **Rendering** | Canvas (default), SVG optional |
| **Learning curve** | Medium |
| **Best for** | Data-dense dashboards, large datasets, rich interactivity |

**Chart types** (30+):
- Line, bar, scatter, pie, radar
- Candlestick, boxplot, heatmap
- Treemap, sunburst, Sankey, graph/network
- Funnel, gauge, parallel coordinates
- Geographic maps, globe (3D)
- Calendar heatmap, themeRiver
- **New in 6.0**: Chord series, matrix coordinate system

**When to reference ECharts**:
- When designing dashboards with many interrelated charts.
- When targeting very large datasets (ECharts handles 100k+ points).
- Rich tooltip and drill-down interaction patterns.
- Examples gallery: [https://echarts.apache.org/examples](https://echarts.apache.org/examples)

---

### 1.4 Observable Plot

| Attribute | Detail |
|-----------|--------|
| **URL** | [https://observablehq.com/plot](https://observablehq.com/plot) |
| **License** | ISC |
| **Approach** | Concise, grammar-of-graphics inspired |
| **Rendering** | SVG |
| **Best for** | Exploratory data analysis, quick prototyping |

**Key marks**: Bar, Cell, Dot, Line, Area, Rule, Text, Tick, Rect, Link, Arrow,
Image, Hexbin, Contour, Density.

---

### 1.5 Vega / Vega-Lite

| Attribute | Detail |
|-----------|--------|
| **URL** | [https://vega.github.io/vega-lite/](https://vega.github.io/vega-lite/) |
| **License** | BSD 3-Clause |
| **Approach** | Declarative JSON grammar of graphics |
| **Rendering** | SVG, Canvas |
| **Best for** | Specification-driven charts; integration with Python (Altair) |

**When to reference Vega-Lite**:
- As a model for declarative chart specification.
- Composable views: concatenation, faceting, layering, repeating.
- The Vega-Lite schema is a good template for Inkline's own chart DSL.

---

### 1.6 Recharts (React)

| Attribute | Detail |
|-----------|--------|
| **URL** | [https://recharts.org](https://recharts.org) |
| **License** | MIT |
| **Best for** | React-based dashboards |

Built on D3 sub-modules with React components. Includes: Line, Area, Bar,
Scatter, Pie, Radar, Treemap, Funnel, Sankey.

---

### 1.7 Plotly.js

| Attribute | Detail |
|-----------|--------|
| **URL** | [https://plotly.com/javascript/](https://plotly.com/javascript/) |
| **License** | MIT |
| **Best for** | Scientific/analytical visualisation; 3D charts |

40+ chart types including 3D scatter, surface plots, contour, parallel
coordinates, and statistical charts.

---

## 2. Typst Community Templates

### Typst Overview

[Typst](https://typst.app) is a modern typesetting system designed as a faster,
more ergonomic alternative to LaTeX. It is relevant to Inkline because it can
generate high-quality PDF documents and presentations programmatically.

### Typst Universe (Package Registry)

URL: [https://typst.app/universe](https://typst.app/universe)

### Key Presentation Packages

| Package | Description | Themes |
|---------|-------------|--------|
| **Touying** | Full-featured slide framework | Simple, Metropolis, Dewdrop, University, Aqua, Stargazer |
| **Polylux** | Slide creation package | Customisable |
| **Typslides** | Minimalist presentation slides | Clean, fast |
| **Diatypst** | Easy slide creation with delimiters | Adjustable colour themes |
| **Slydst** | Simple slide template | Basic |

### Key Document Templates

Available on Typst Universe for various document types:
- Academic papers and theses
- Letters and invoices
- CVs and resumes
- Reports and technical documentation
- Posters

### When to reference Typst

- When Inkline generates PDF documents or presentations via Typst.
- For layout algorithms and page composition patterns.
- Touying themes provide good defaults for slide structure.

---

## 3. Government Design Systems

### 3.1 UK Government Analysis Function

**URL**: [https://analysisfunction.civilservice.gov.uk/area_of_work/data-visualisation/](https://analysisfunction.civilservice.gov.uk/area_of_work/data-visualisation/)

**Key resources**:
- **Data Visualisation: Charts** — guidance on chart design for public sector.
- **Colour guidance** — accessible colour palettes for government publications.
- **Dashboard testing** — usability and accessibility testing for dashboards.

**Key principles**:
1. Charts must meet WCAG 2.2 Level AA success criteria.
2. Use SVG format for published charts (resolution-independent).
3. Horizontal bar charts are native HTML on GOV.UK.
4. Provide text descriptions for all charts.
5. Avoid dual axes, 3D effects, and decorative elements.

### 3.2 UK ONS Service Manual — Data Visualisation

**URL**: [https://service-manual.ons.gov.uk/data-visualisation](https://service-manual.ons.gov.uk/data-visualisation)

**Principles**:
1. **Visualise data, not decorations** — every pixel should encode data.
2. **Accessibility first** — colour is never the sole encoding.
3. **Progressive disclosure** — summary view first, detail on demand.
4. **Appropriate precision** — don't show more decimal places than the data warrants.

### 3.3 US Web Design System (USWDS)

**URL**: [https://designsystem.digital.gov](https://designsystem.digital.gov)

**Data visualisation guidance**:
- Stick to well-known chart types (line, bar) for general audiences.
- Provide a screen-reader-accessible data table using `usa-sr-only` class.
- Use `aria-hidden="true"` on the visualisation when an accessible equivalent is provided.
- Test with screen readers (NVDA, JAWS, VoiceOver).

**Design tokens** relevant to data viz:
- Typography: Public Sans (designed for government use)
- Colour: Token-based system with accessible colour grades
- Spacing: 8px base unit

### 3.4 City of London Intelligence Data Design Guidelines

**URL**: [https://data.london.gov.uk/blog/city-intelligence-data-design-guidelines/](https://data.london.gov.uk/blog/city-intelligence-data-design-guidelines/)

Comprehensive guide covering chart selection, colour, typography, and layout
specifically for city data publications.

### 3.5 Department for Education (DfE) Design Manual — Charts

**URL**: [https://design.education.gov.uk/design-system/patterns/charts](https://design.education.gov.uk/design-system/patterns/charts)

Patterns for embedding accessible charts in government services.

---

## 4. Curated Resource Lists

### 4.1 Awesome Data Visualization (GitHub)

**URL**: [https://github.com/hal9ai/awesome-dataviz](https://github.com/hal9ai/awesome-dataviz)

A curated list of data visualisation libraries and resources, organised by
language (JavaScript, Python, R, etc.) and type.

### 4.2 Awesome Typst (GitHub)

**URL**: [https://github.com/qjcg/awesome-typst](https://github.com/qjcg/awesome-typst)

Comprehensive list of Typst packages, templates, and tools.

### 4.3 Front-End Data Tools — The Awesome List

**URL**: [https://awesome.cube.dev](https://awesome.cube.dev)

Curated list of front-end data tools including charting libraries, dashboards,
and data exploration tools.

---

## 5. Chart Gallery References for Inspiration

| Gallery | URL | What it offers |
|---------|-----|---------------|
| **D3 Gallery** (Observable) | [observablehq.com/@d3/gallery](https://observablehq.com/@d3/gallery) | 100s of interactive examples, fork and modify |
| **D3 Graph Gallery** | [d3-graph-gallery.com](https://d3-graph-gallery.com/) | Step-by-step tutorials for each chart type |
| **ECharts Examples** | [echarts.apache.org/examples](https://echarts.apache.org/examples) | Comprehensive examples with live editor |
| **Chart.js Samples** | [chartjs.org/docs](https://www.chartjs.org/docs/latest/) | Inline demos for all chart types |
| **The R Graph Gallery** | [r-graph-gallery.com](https://r-graph-gallery.com/) | 400+ chart examples in R (transferable design patterns) |
| **Python Graph Gallery** | [python-graph-gallery.com](https://python-graph-gallery.com/) | Python/matplotlib/seaborn examples |
| **From Data to Viz** | [data-to-viz.com](https://www.data-to-viz.com/) | Decision tree + caveats for each chart type |
| **Dataviz Catalogue** | [datavizcatalogue.com](https://datavizcatalogue.com/) | Searchable catalogue of chart types with descriptions |
| **FT Visual Vocabulary** | [ft-interactive.github.io/visual-vocabulary](https://ft-interactive.github.io/visual-vocabulary/) | The FT's canonical chart selection poster |
| **Xenographics** | [xeno.graphics](https://xeno.graphics) | Unusual and exotic chart types |
| **Flourish** | [flourish.studio](https://flourish.studio/) | Interactive chart templates (free tier) |
| **Datawrapper** | [datawrapper.de](https://www.datawrapper.de/) | Simple chart creation tool (free tier) |

---

## 6. Design System Colour Palettes (Open Source)

| System | Palette URL | Tokens |
|--------|------------|--------|
| **USWDS** | [designsystem.digital.gov/design-tokens/color](https://designsystem.digital.gov/design-tokens/color/) | Grade-based (5-90); accessible by design |
| **IBM Carbon** | [carbondesignsystem.com/data-visualization/color-palettes](https://carbondesignsystem.com/data-visualization/color-palettes/) | Sequential, categorical, diverging; WCAG AA |
| **Material Design** | [m3.material.io/styles/color](https://m3.material.io/styles/color/) | Dynamic colour system with tonal palettes |
| **Tableau Public** | Built into Tableau | Tableau 10, Tableau 20, colourblind-safe |
| **ColorBrewer** | [colorbrewer2.org](https://colorbrewer2.org/) | The gold standard for cartographic colour |

---

## 7. Accessibility Testing Tools

| Tool | URL | What it tests |
|------|-----|---------------|
| **WebAIM Contrast Checker** | [webaim.org/resources/contrastchecker](https://webaim.org/resources/contrastchecker/) | WCAG AA/AAA contrast ratios |
| **Coblis Color Blindness Simulator** | [color-blindness.com/coblis](https://www.color-blindness.com/coblis-color-blindness-simulator/) | Simulates all types of CVD |
| **Color Oracle** | [colororacle.org](https://colororacle.org/) | Desktop colour blindness simulator |
| **axe DevTools** | [deque.com/axe](https://www.deque.com/axe/) | Comprehensive accessibility audit |
| **Stark** (Figma plugin) | [getstark.co](https://www.getstark.co/) | Contrast, colour blindness, alt text |

---

## 8. Library Selection Decision Table

| Need | Recommended library | Why |
|------|-------------------|-----|
| Quick standard chart | Chart.js | Simple API, sensible defaults, 8 chart types |
| Custom / bespoke visual | D3.js | Total control, any visual encodable |
| Data-dense dashboard | Apache ECharts | 30+ types, handles large data, rich interaction |
| Declarative specification | Vega-Lite | JSON grammar, composable, Python-friendly (Altair) |
| React application | Recharts | React components built on D3 |
| Scientific / 3D charts | Plotly.js | 40+ types including 3D, statistical |
| PDF document generation | Typst + Touying | Modern typesetting, programmatic |
| Accessible government site | USWDS + Chart.js | Government-grade accessibility |

---

## References

- [D3.js](https://d3js.org/) | [D3 Gallery](https://observablehq.com/@d3/gallery)
- [Chart.js](https://www.chartjs.org/)
- [Apache ECharts](https://echarts.apache.org/)
- [Observable Plot](https://observablehq.com/plot)
- [Vega-Lite](https://vega.github.io/vega-lite/)
- [Typst Universe](https://typst.app/universe/)
- [Touying Slides](https://touying-typ.github.io/docs/intro)
- [UK Government Analysis Function — Data Visualisation](https://analysisfunction.civilservice.gov.uk/area_of_work/data-visualisation/)
- [ONS Data Visualisation Manual](https://service-manual.ons.gov.uk/data-visualisation)
- [USWDS — Data Visualizations](https://designsystem.digital.gov/components/data-visualizations/)
- [Metabase — Comparing Open Source Chart Libraries](https://www.metabase.com/blog/best-open-source-chart-library)
- [Awesome Data Viz — GitHub](https://github.com/hal9ai/awesome-dataviz)
- [From Data to Viz](https://www.data-to-viz.com/)
