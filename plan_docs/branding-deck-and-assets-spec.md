# Inkline Branding Deck + Asset Regeneration Spec

**Status:** Approved for implementation  
**Version:** 1.0  
**Date:** April 2026

---

## Overview

This spec covers three interconnected deliverables:

1. **Brand Guidelines Deck** (12–15 slides) — comprehensive identity system for internal + external stakeholders
2. **Product Pitch Deck** (10–12 slides) — investor/customer facing; showcases Inkline's capabilities
3. **Brand Asset Kit** — regenerated backgrounds, icon variations, hero illustrations

All materials use **Inkline Indigo (#3D2BE8)** as the primary accent with **Vellum (#F7F6F2)** backgrounds, paired with imaginative AI-generated visual treatments that feel premium and intentional.

---

## Visual Aesthetic Direction

### Color Palette
- **Primary:** Inkline Indigo (#3D2BE8) + gradient to Light Indigo (#5B4FFF)
- **Background:** Vellum off-white (#F7F6F2)
- **Text:** Ink Black (#0A0A0A) + Slate secondary (#64748B)
- **Accents:** Violet (#7C3AED), Cobalt (#1E40AF), Sage (#16A34A)

### Typography
- **Display:** Plus Jakarta Sans 200 (ExtraLight) — refined, minimal
- **Serif accent:** Cormorant Garamond 600 Italic — for "ink" wordmark, editorial moments
- **Body:** Plus Jakarta Sans 400

### Design Principles
1. **Minimal, not minimal-ist** — generous whitespace, intentional composition
2. **Organic + precise** — blend geometric precision with ink-blot organic forms
3. **Editorial quality** — every slide should feel like a premium publication
4. **Data-forward** — charts and exhibits drive narrative, not decorative flourishes

---

## DELIVERABLE 1: Brand Guidelines Deck (12–15 slides)

**Audience:** Internal team, partners, licensees  
**Tone:** Authoritative, educational, inspiring  
**Format:** PDF via Inkline (Typst backend)

### Slide-by-slide outline

| # | Slide Type | Title | Content |
|---|---|---|---|
| 1 | `title` | Inkline Brand Identity | Subtitle: "The craft of ink, the precision of a line" |
| 2 | `chart_caption` | The Mark (v2) | Organic ink-blot with italic serif "i"; explain the split concept (ink = serif/craft, line = sans/geometry) |
| 3 | `three_card` | The Wordmark Split | Three cards: "Ink" (black, serif), "Line" (indigo, sans), Compound meaning (craft + geometry) |
| 4 | `feature_grid` | Logo Variants | 6 grid: mark-only, wordmark, horizontal lockup, stacked, white variant, favicon |
| 5 | `dashboard` | Colour System | Hero color swatch + breakdown: Primary (Indigo), Secondary (Ink), Background (Vellum), Accents (5 colors) |
| 6 | `kpi_strip` | Typography Scale | 5 KPIs: Logo (200 ExtraLight), Heading (300), Subheading (400), Body (400 16px), Caption (300 12px) |
| 7 | `chart_caption` | Typeface Pairing | Plus Jakarta Sans (sans) + Cormorant Garamond Italic (serif); explain the brand voice |
| 8 | `before_after` | Light vs Dark Modes | Left: light mode (Vellum bg), Right: dark mode (dark surface); show contrast/readability |
| 9 | `timeline` | Clear Space Rules | Visual timeline showing minimum clearance (= cap-height of wordmark) around lockups |
| 10 | `three_card` | Do's | Do: Use 3-color max, apply gradient to mark only, tighten letter-spacing, speak like a designer |
| 11 | `three_card` | Don'ts | Don't: Alter mark proportions, recolour "ink", use gradient on type, bold the wordmark |
| 12 | `closing` | Questions? | Contact info, link to brand assets (GitHub), tagline |

### Key visuals needed
- **Slide 2:** Generated background showing organic ink-blot pattern (indigo on vellum)
- **Slide 4:** Grid of logo variations rendered cleanly (use existing brand/logo/ files)
- **Slide 5:** Color palette swatch (use existing colors.svg as reference)
- **Slide 7:** Typography specimen showing Plus Jakarta vs Cormorant side-by-side
- **Slide 8:** Two-column layout with light/dark theme application examples

---

## DELIVERABLE 2: Product Pitch Deck (10–12 slides)

**Audience:** Investors, prospective users, partners  
**Tone:** Confident, narrative-driven, outcome-focused  
**Format:** PDF via Inkline (Typst backend) + optional Google Slides export

### Slide-by-slide outline

| # | Slide Type | Title | Content | Background |
|---|---|---|---|---|
| 1 | `title` | Inkline | Subtitle: "Publication-quality decks, designed by AI" | Geometric indigo pattern |
| 2 | `chart_caption` | The Problem | Chart: manual slide design takes 40% of analysis work; nobody has time | Abstract indigo/vellum |
| 3 | `three_card` | The Solution | Three pillars: Code-first, LLM-designed, Visually audited | Clean indigo accent |
| 4 | `dashboard` | How It Works | 4-step flow: Upload file → DesignAdvisor → Visual audit → PDF ready | Diagram-style background |
| 5 | `feature_grid` | 6 Capabilities | Code-first, Per-slide audit, Self-learning, 90 themes, AI images, Self-hosted | Hero indigo section |
| 6 | `kpi_strip` | Competitive Position | 4 KPIs: Speed (5min to deck), Cost (self-hosted = free), Quality (>95% audit pass), Coverage (22 slide types) | Subtle grid background |
| 7 | `chart_caption` | n8n Integration | Show: custom backgrounds, icons, hero illustrations auto-generated | AI-generated background demo |
| 8 | `timeline` | Roadmap | Q2 2026: Desktop app, Q3: Multi-format export, Q4: Marketplace | Timeline with milestones |
| 9 | `chart_caption` | Open Source | GitHub stars, community contributions, public brand registry | Code/OSS aesthetic |
| 10 | `kpi_strip` | Traction | 3 KPIs: Users, decks generated, avg time saved | Growth indicators |
| 11 | `three_card` | Use Cases | Investor pitches, Board presentations, Product docs | Use-case cards |
| 12 | `closing` | Let's build | Contact, tagline "Because your output should be as good as your analysis" | Indigo gradient |

### Key visuals needed
- **Slide 1:** Bold hero background (geometric indigo abstractions)
- **Slide 2:** Waterfall or bar chart showing time allocation
- **Slide 4:** Process flow diagram (generated or hand-drawn)
- **Slide 5:** 6-item feature grid with icons
- **Slide 7:** Showcase 3 AI-generated background examples
- **Slide 10:** Growth chart (line or area chart)

---

## DELIVERABLE 3: Brand Asset Kit

### New Assets to Generate (via n8n + Gemini)

| Asset | Purpose | Dimensions | Style |
|---|---|---|---|
| `bg-hero-geometric.png` | Slide 1 / marketing hero | 1920×1080 | Geometric indigo abstractions; angular, bold |
| `bg-chart-grid.png` | Data slide background | 1920×1080 | Minimalist grid in slate; accent lines in indigo |
| `bg-editorial-organic.png` | Editorial/brand slide background | 1920×1080 | Organic ink-blot inspired; asymmetric, flowing |
| `bg-gradient-abstract.png` | Gradient slide background | 1920×1080 | Indigo #3D2BE8 → Light Indigo #5B4FFF; soft gradient |
| `icon-chart.svg` | Chart icon / UI element | 64×64 | Minimalist bar chart in indigo |
| `icon-code.svg` | Code/API icon | 64×64 | Code brackets in indigo |
| `icon-audit.svg` | Audit/check icon | 64×64 | Checkmark in sage green |

### Gemini Prompts (for n8n workflow)

**Prompt 1: Hero geometric background**
```
Generate a 16:9 background image for a SaaS product hero slide.
Style: Geometric abstractions, bold and minimal.
Colors: Dominant indigo #3D2BE8 (60%), light indigo #5B4FFF highlights (20%), vellum #F7F6F2 negative space (20%).
Elements: Angular shapes, clean lines, no curves. Suggest movement/upward trajectory.
Composition: Leave clear space in center-right for text overlay (40% of slide width).
No text, no photographic textures, pure vector illustration.
```

**Prompt 2: Chart grid background**
```
Generate a minimalist background for a financial/data slide.
Style: Subtle grid pattern with accent highlighting.
Colors: Vellum #F7F6F2 base (90%), indigo #3D2BE8 grid lines and accent (10%).
Elements: Fine grid lines (very subtle), 2-3 accent bars/lines in indigo positioned at strategic points.
Composition: Balanced, not too busy. Should feel like premium financial design.
No text, flat design, high contrast.
```

**Prompt 3: Organic ink-blot inspired background**
```
Generate a 16:9 background inspired by organic ink-blot shapes for an editorial/brand slide.
Style: Fluid, asymmetric organic forms; feels like ink dropped on paper.
Colors: Vellum #F7F6F2 background (primary), indigo #3D2BE8 blot forms (40% coverage).
Elements: 2-3 organic ink-blot shapes (asymmetric, heavier on one side), subtle satellite spatter dots.
Composition: Heavier on left-bottom, lighter upper-right; leaves room for text.
No text, flat design, high-quality rendering.
```

**Prompt 4: Gradient abstract background**
```
Generate a smooth gradient background for a feature/capability slide.
Style: Minimalist gradient transition, abstract shapes.
Colors: Start indigo #3D2BE8 (bottom-left), transition to light indigo #5B4FFF (top-right), vellum highlights.
Elements: Subtle abstract shapes suggesting motion; very minimal and refined.
Composition: Should feel premium and sophisticated; suitable for SaaS product deck.
No text, smooth gradients, no hard edges.
```

---

## Implementation Timeline

### Phase 1: Asset Generation (2–3 hours)
1. Trigger n8n workflows to generate 4 backgrounds + SVG icons
2. Review outputs; regenerate any that don't match aesthetic
3. Save to `brand/backgrounds/` and `brand/icons/`

### Phase 2: Brand Guidelines Deck (2–3 hours)
1. Build sections[] Python objects with spec outline
2. Use DesignAdvisor(brand="minimal", mode="llm") to design slides
3. Export via Archon pipeline; audit visually
4. Iterate on any failed slides

### Phase 3: Product Pitch Deck (2–3 hours)
1. Build sections[] for pitch outline
2. Generate charts (revenue, time-savings, feature grid)
3. Use DesignAdvisor to layout
4. Embed background images + charts
5. Export and audit

### Phase 4: Asset Kit Organization (30–45 min)
1. Organize all assets into `brand/backgrounds/`, `brand/icons/`, `brand/charts/`
2. Update `BRAND_GUIDELINES.md` with asset file list
3. Commit and push to main

---

## Success Criteria

- [ ] All 4 backgrounds generated and visually coherent with brand
- [ ] Brand Guidelines deck: 12–15 slides, all audit-passing
- [ ] Product Pitch deck: 10–12 slides, all audit-passing
- [ ] Icon set: 7 icons, consistent style, ready for use
- [ ] All assets organized and documented in `BRAND_GUIDELINES.md`
- [ ] Decks push to `brand/decks/` directory
- [ ] Commit message references both decks + asset kit

---

## References

- Brand Guidelines: `brand/BRAND_GUIDELINES.md` (comprehensive identity spec)
- Logo files: `brand/logo/` (v1 geometric + v2 ink-blot)
- Color palette: `brand/colors.svg`
- n8n workflow: `inkblot-icon-generator-workflow.json` (template)
- Inkline bridge: Running on localhost:8082 for deck generation
