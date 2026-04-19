# Inkline — Brand Guidelines

**Version:** 1.0
**Date:** April 2026

---

## 1. The Mark

The Inkline mark is a stylised lowercase **i** in which the tittle (dot) is replaced by an
ink drop — a teardrop form that tapers to a cusp at the base, as if a drop of ink has just
fallen from a nib. The stem is a clean, rounded-end bar below the drop.

The mark is intentionally simple: two elements, one colour.

### Construction

The ink drop is a circular arc (`r = 22`) over the top half, tapering via two mirrored
cubic Bézier curves to a sharp cusp at the bottom. The overall drop spans 54 units from
peak to point. The stem is 12 units wide with a 6-unit corner radius, separated from the
drop by a 10-unit gap. Total mark height: 128 units; width: 100 units.

### SVG paths

```svg
<!-- Ink drop -->
<path d="M 28,28 A 22,22 0 1,1 72,28 Q 72,48 50,60 Q 28,48 28,28 Z"/>
<!-- Stem -->
<rect x="44" y="70" width="12" height="52" rx="6"/>
```

### Colour on the mark

| Context | Drop fill | Stem fill |
|---|---|---|
| Light background | Gradient #5B4FFF → #3D2BE8 | #3D2BE8 flat |
| Dark / indigo background | #FFFFFF | #FFFFFF |
| Single-colour print | #3D2BE8 (or 100% K) | Same |

Never apply the brand colour gradient to the full wordmark — gradient is exclusive to the
mark/icon only.

---

## 2. The Wordmark

The wordmark is **inkline** set entirely in lowercase. It uses a two-colour split:

- **ink** — Ink Black (#0A0A0A)
- **line** — Inkline Indigo (#3D2BE8)

The split reinforces the compound meaning:
> *ink* — the medium, craft, precision
> *line* — structure, geometry, the slide canvas
> *incline* — upward trajectory (phonetic Easter egg)

### Typeface

**Primary:** Plus Jakarta Sans, weight 200 (ExtraLight)
Google Fonts CDN: `https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@200`

**Fallback stack:** `'Plus Jakarta Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif`

**Premium alternative:** Söhne by Klim Type Foundry (for print / high-end collateral)

Letter-spacing: **−0.02em** (tightened for refinement; do not loosen beyond 0em)

### Scaling

The wordmark is SVG vector and infinitely scalable. Minimum legible size: **80px wide**
in digital contexts; 25mm wide in print.

---

## 3. Lockups

Three approved lockup configurations:

| File | Use case |
|---|---|
| `logo/lockup-horizontal.svg` | Header navigation, email signatures, social banners |
| `logo/lockup-stacked.svg` | Document covers, app splash, square crops |
| `logo/mark.svg` | Favicon, app icon, watermark, embossed use |
| `logo/wordmark.svg` | Where the mark has already been established in context |

### Clear space

Minimum clear space around any lockup = height of the ink drop (top circle of the mark).
In the horizontal lockup, this equals approximately 1× the cap-height of the wordmark.

---

## 4. Colour System

### Primary palette

| Token | Hex | Usage |
|---|---|---|
| `--inkline-ink` | `#0A0A0A` | Primary text, Ink half of wordmark |
| `--inkline-indigo` | `#3D2BE8` | Brand primary, Line half of wordmark, CTAs |
| `--inkline-indigo-light` | `#5B4FFF` | Gradient start, hover states, selected |
| `--inkline-vellum` | `#F7F6F2` | Page background, card fills |
| `--inkline-slate` | `#64748B` | Secondary text, captions, metadata |
| `--inkline-rule` | `#E2E1DC` | Dividers, borders, table rules |

### Dark mode palette

| Token | Hex | Usage |
|---|---|---|
| `--inkline-surface-dark` | `#0F0F14` | Dark page background |
| `--inkline-surface-raised` | `#1A1A24` | Cards, panels on dark bg |
| `--inkline-indigo-dim` | `#4A3FF0` | Indigo adjusted for dark bg contrast |
| `--inkline-text-dark` | `#F0EFEB` | Primary text on dark |
| `--inkline-text-secondary-dark` | `#8B8FA8` | Secondary text on dark |

### Accent palette (data and status)

| Token | Hex | Usage |
|---|---|---|
| `--inkline-violet` | `#7C3AED` | Extended brand, charts (complement) |
| `--inkline-cobalt` | `#1E40AF` | Links, informational |
| `--inkline-vermilion` | `#DC2626` | Errors, FAIL states, alerts |
| `--inkline-sage` | `#16A34A` | Success, PASS states |
| `--inkline-amber` | `#D97706` | Warnings, caution |

### Colour rules

1. **Three-colour maximum** in any single composition: Ink + Indigo + one accent.
2. The gradient (#5B4FFF → #3D2BE8) is **exclusive to the mark**. Never apply it to type.
3. Indigo backgrounds are high-impact; use sparingly (hero sections, full-bleed slides).
4. Never place Indigo text on an Indigo background — switch to white or Vellum.

---

## 5. Typography

### Type scale

| Role | Family | Weight | Size |
|---|---|---|---|
| Logo / display | Plus Jakarta Sans | 200 | 48–96px |
| Section heading | Plus Jakarta Sans | 300 | 32–48px |
| Subheading | Plus Jakarta Sans | 400 | 20–28px |
| Body | Plus Jakarta Sans | 400 | 14–16px |
| Caption / footnote | Plus Jakarta Sans | 300 | 11–13px |
| Code / monospace | Geist Mono | 400 | 13–14px |

### Typeface download

- **Plus Jakarta Sans:** https://fonts.google.com/specimen/Plus+Jakarta+Sans
- **Geist Mono:** https://vercel.com/font
- **Print / premium:** Söhne (Klim Type Foundry) — purchase separately

### Type rules

1. **Never bold the wordmark.** The ExtraLight (200) weight is a core design decision.
2. Letter-spacing in display headings: −0.01em to −0.03em (always tighten, never loosen).
3. Line height for body copy: 1.6.
4. Line height for headings: 1.15.
5. Set captions in Slate (#64748B); never use pure grey (#808080 or similar).

---

## 6. Motion (if animated)

When the logo animates (e.g. app loading screen):

1. The ink drop appears first — fades + drops in from y−8 to y=0 over 300ms (ease-out).
2. The stem draws in upward from 0 height to full height over 200ms after the drop settles.
3. The wordmark fades in at 0ms delay relative to the stem, over 250ms (ease-in-out).
4. Total animation: ≤800ms. Never loop.

Suggested CSS easing: `cubic-bezier(0.16, 1, 0.3, 1)` (expo-out feel).

---

## 7. Tone of Voice

Inkline's brand language mirrors the product: precise, confident, minimal.

**Do:**
- Use active voice and short sentences
- Lead with the outcome, not the process
- Speak like a senior designer explaining a decision

**Don't:**
- Use superlatives ("amazing", "powerful", "beautiful") — let the output speak
- Use filler phrases ("essentially", "basically", "in order to")
- Over-explain technical choices in marketing copy

**Examples:**

> ✓ "Inkline turns structured data into institutional-quality slides."
> ✗ "Inkline is an amazing tool that uses powerful AI to beautifully transform your data."

---

## 8. Don'ts

| Rule | Why |
|---|---|
| Don't alter the mark proportions | The 100:128 aspect ratio is precise |
| Don't recolour "ink" to anything but black | It destroys the split-word concept |
| Don't use the gradient on type | Gradient is mark-exclusive — applied to type it looks generic |
| Don't set the wordmark in bold or medium weight | ExtraLight is the brand voice |
| Don't add drop shadows to the mark | The mark is designed for flat rendering |
| Don't use the mark at below 20px width | Use text-only below that threshold |
| Don't place the mark on a cluttered background | Use a solid or very simple background |

---

## 9. Files

```
brand/
├── logo/
│   ├── mark.svg                   # Icon only — gradient, on light
│   ├── mark-white.svg             # Icon only — white, on dark
│   ├── wordmark.svg               # Text only — ink+indigo split
│   ├── wordmark-white.svg         # Text only — white
│   ├── lockup-horizontal.svg      # Mark + text, side by side
│   ├── lockup-horizontal-white.svg
│   └── lockup-stacked.svg         # Mark above text
├── colors.svg                     # Colour palette reference
├── favicon.svg                    # 32×32 optimised mark
└── BRAND_GUIDELINES.md            # This file
```

---

*Inkline brand identity. All assets are SVG vector; infinitely scalable.*
