# Design Tokens Enhancement — Colour Ramps, Typography Scale, Spacing System

**Status:** Proposed
**Date:** 2026-04-16
**Inspired by:** Untitled UI design system (320K users, 10K components, 4px grid)
**Scope:** 3 enhancements to BaseBrand and theme token pipeline

---

## Problem Statement

Inkline's BaseBrand defines 8 flat colours (`primary`, `secondary`, `background`, etc.),
2 raw font sizes (`heading_size=28`, `body_size=14`), and no spacing tokens at all.
Templates hardcode pt values throughout.

This causes:

1. **Colour poverty** — templates only have 8 colours. When a slide needs a tinted
   background, a subtle border, a hover-like emphasis, or a secondary accent shade,
   the template author picks an arbitrary hex value. Across 37 templates and 7 brands,
   these ad-hoc values drift.

2. **Typography inconsistency** — `heading_size=28` is used for slide headings, but
   section labels, stat values, KPI numbers, footnotes, and captions all need different
   sizes. Each template hardcodes its own scale, leading to inconsistency across templates.

3. **Spacing drift** — padding, margins, and gaps are hardcoded as raw pt values in
   Typst templates. No shared vocabulary means card padding in `three_card` might be
   16pt while `four_card` uses 14pt — visually inconsistent.

Untitled UI solves all three with: 12-shade colour ramps per palette colour, a named
typography scale (display-xl through caption), and a 4px spacing grid with named tokens.

---

## Design Principles

- **Backwards compatible** — all new fields have defaults computed from existing values.
  Zero changes to existing brand definitions or templates until they opt in.
- **Computed, not declared** — brands declare `primary="#6366F1"` and the ramp is
  auto-generated. No need to manually specify 12 shades.
- **Progressive adoption** — templates can use `brand.type_scale["body_md"]` or fall
  back to `brand.body_size`. Both work.
- **No new dependencies** — colour math uses stdlib `colorsys`. No numpy/colormath.

---

## Feature 1: Colour Ramp Generator

### Purpose
Auto-generate a 12-shade ramp from any hex colour. Given `primary="#6366F1"`, produce
shades from near-white (25) to near-black (950) that are optically consistent.

### Shade Scale (Untitled UI / Tailwind standard)
```
25, 50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950
```
- **500** is the input colour (the brand's declared value)
- **25** is a barely-tinted white (for subtle backgrounds)
- **950** is a deep saturated dark (for text on coloured backgrounds)

### Algorithm

HSL-based lightness interpolation:

```python
def generate_ramp(hex_color: str) -> dict[int, str]:
    """Generate 12-shade ramp from a single hex colour.

    Returns dict mapping shade number → hex string.
    """
    h, s, l = hex_to_hsl(hex_color)

    # Target lightness for each shade (empirically tuned to match Untitled UI)
    targets = {
        25:  0.97,   # near white
        50:  0.94,
        100: 0.88,
        200: 0.78,
        300: 0.66,
        400: 0.55,
        500: l,      # preserve original lightness
        600: 0.38,
        700: 0.30,
        800: 0.23,
        900: 0.17,
        950: 0.11,   # near black
    }

    # Saturation curve: slightly desaturate at extremes for natural feel
    ramp = {}
    for shade, target_l in targets.items():
        if shade == 500:
            ramp[shade] = hex_color
        else:
            # Interpolate saturation: reduce at light/dark extremes
            sat_factor = 1.0 - 0.3 * abs(target_l - 0.5)
            adj_s = s * sat_factor
            ramp[shade] = hsl_to_hex(h, adj_s, target_l)

    return ramp
```

### Integration into BaseBrand

New computed property:

```python
@dataclass
class BaseBrand:
    # ... existing fields ...

    @property
    def primary_ramp(self) -> dict[int, str]:
        """12-shade ramp from primary colour."""
        return generate_ramp(self.primary)

    @property
    def secondary_ramp(self) -> dict[int, str]:
        """12-shade ramp from secondary colour."""
        return generate_ramp(self.secondary)

    @property
    def gray_ramp(self) -> dict[int, str]:
        """12-shade neutral ramp derived from text colour."""
        return generate_ramp(self.muted)
```

### Integration into Theme

```python
def brand_to_typst_theme(brand, template="brand") -> dict:
    theme = {
        # ... existing tokens ...

        # Colour ramps (new)
        "primary_25":  brand.primary_ramp[25],
        "primary_50":  brand.primary_ramp[50],
        "primary_100": brand.primary_ramp[100],
        "primary_200": brand.primary_ramp[200],
        "primary_500": brand.primary_ramp[500],
        "primary_700": brand.primary_ramp[700],
        "primary_900": brand.primary_ramp[900],
        "gray_50":     brand.gray_ramp[50],
        "gray_100":    brand.gray_ramp[100],
        "gray_200":    brand.gray_ramp[200],
        "gray_500":    brand.gray_ramp[500],
        "gray_700":    brand.gray_ramp[700],
        "gray_900":    brand.gray_ramp[900],
    }
```

### Use Cases

| Token | Purpose | Example |
|---|---|---|
| `primary_25` | Subtle tinted background for cards | KPI strip background, feature_grid cards |
| `primary_50` | Slightly stronger tint | Highlighted table rows, selected states |
| `primary_100` | Light accent background | Section divider backgrounds, callout boxes |
| `primary_700` | Darker accent | Heading text on light backgrounds |
| `primary_900` | Very dark accent | Body text alternatives, footer on primary bg |
| `gray_50` | Near-white neutral | Alternating row backgrounds (currently `light_bg`) |
| `gray_100` | Light neutral | Card backgrounds (currently `card_fill`) |
| `gray_200` | Border tone | Subtle borders (currently `border`) |
| `gray_700` | Secondary text | Muted text (currently `muted`) |

### Module

`inkline/brands/color_ramp.py` (~80 lines)

Functions:
- `hex_to_hsl(hex_color: str) -> tuple[float, float, float]`
- `hsl_to_hex(h: float, s: float, l: float) -> str`
- `generate_ramp(hex_color: str) -> dict[int, str]`

---

## Feature 2: Named Typography Scale

### Purpose
Replace raw `heading_size=28, body_size=14` with a structured scale that templates
reference by name. This ensures consistent hierarchy across all templates and brands.

### Scale Definition (adapted from Untitled UI)

```python
@dataclass
class TypeScale:
    """Named typography scale for consistent hierarchy."""
    display_xl: float = 44    # Hero numbers, title slide company name
    display_lg: float = 36    # Large stat values
    display_md: float = 28    # Section headings (= current heading_size)
    display_sm: float = 24    # Sub-headings, card titles in large layouts
    heading_lg: float = 20    # Card titles, chart titles
    heading_md: float = 18    # KPI labels, table headers
    heading_sm: float = 16    # Small headings, bold labels
    body_lg: float = 14       # Primary body text (= current body_size)
    body_md: float = 12       # Secondary body text, bullet points
    body_sm: float = 11       # Dense body text, footnotes
    caption: float = 10       # Footnotes, source labels, axis labels
    overline: float = 9       # Section overline labels ("FINANCIALS"), small caps
```

### Derivation from Brand

The scale is **auto-derived** from `heading_size` and `body_size` using ratios,
so existing brands get a full scale without changes:

```python
@property
def type_scale(self) -> TypeScale:
    """Derive a full typography scale from heading_size and body_size."""
    h = self.heading_size  # anchor: display_md
    b = self.body_size     # anchor: body_lg
    return TypeScale(
        display_xl=round(h * 1.57),  # 44 when h=28
        display_lg=round(h * 1.29),  # 36 when h=28
        display_md=h,                 # 28
        display_sm=round(h * 0.86),  # 24 when h=28
        heading_lg=round(h * 0.71),  # 20 when h=28
        heading_md=round(h * 0.64),  # 18 when h=28
        heading_sm=round(h * 0.57),  # 16 when h=28
        body_lg=b,                    # 14
        body_md=round(b * 0.86),     # 12 when b=14
        body_sm=round(b * 0.79),     # 11 when b=14
        caption=round(b * 0.71),     # 10 when b=14
        overline=round(b * 0.64),    # 9 when b=14
    )
```

### Integration into Theme

```python
def brand_to_typst_theme(brand, template="brand") -> dict:
    ts = brand.type_scale
    theme = {
        # ... existing tokens ...

        # Typography scale (new — supplements heading_size/body_size)
        "display_xl": ts.display_xl,
        "display_lg": ts.display_lg,
        "display_md": ts.display_md,
        "display_sm": ts.display_sm,
        "heading_lg": ts.heading_lg,
        "heading_md": ts.heading_md,
        "heading_sm": ts.heading_sm,
        "body_lg": ts.body_lg,
        "body_md": ts.body_md,
        "body_sm": ts.body_sm,
        "caption": ts.caption,
        "overline": ts.overline,
    }
```

### Use in Typst Templates

Before:
```typst
#text(size: 28pt, weight: "bold")[...heading...]
#text(size: 11pt)[...body...]
#text(size: 9pt, fill: muted)[...footnote...]
```

After:
```typst
#text(size: {display_md}pt, weight: "bold")[...heading...]
#text(size: {body_md}pt)[...body...]
#text(size: {overline}pt, fill: {muted})[...footnote...]
```

### Override Support

Brands can optionally declare a custom TypeScale:

```python
MyBrand = BaseBrand(
    ...,
    custom_type_scale=TypeScale(display_xl=48, body_lg=15, ...),
)
```

If `custom_type_scale` is set, it takes precedence over the auto-derived scale.

---

## Feature 3: Spacing Token System

### Purpose
Named spacing tokens that templates reference instead of hardcoded pt values.
Based on Untitled UI's 4px grid, adapted for print/slide context (4pt base).

### Token Scale

```python
@dataclass
class SpacingScale:
    """Named spacing tokens based on 4pt grid."""
    xxs: float = 2     # Tight gaps: between icon and label
    xs: float = 4      # Minimal padding: compact elements
    sm: float = 8      # Small gaps: between related items
    md: float = 16     # Standard padding: card insets, section gaps
    lg: float = 24     # Large gaps: between sections on a slide
    xl: float = 32     # Extra large: slide margins, major separations
    xxl: float = 48    # Maximum: hero spacing, title slide breathing room
```

### Derivation

Fixed values (not derived from brand — spacing should be consistent across brands
for optical consistency). Brands can override if needed:

```python
@property
def spacing(self) -> SpacingScale:
    """Spacing token scale."""
    if hasattr(self, 'custom_spacing') and self.custom_spacing:
        return self.custom_spacing
    return SpacingScale()
```

### Integration into Theme

```python
def brand_to_typst_theme(brand, template="brand") -> dict:
    sp = brand.spacing
    theme = {
        # ... existing tokens ...

        # Spacing tokens (new)
        "space_xxs": sp.xxs,
        "space_xs": sp.xs,
        "space_sm": sp.sm,
        "space_md": sp.md,
        "space_lg": sp.lg,
        "space_xl": sp.xl,
        "space_xxl": sp.xxl,
    }
```

### Use in Typst Templates

Before:
```typst
#pad(x: 12pt, y: 8pt)[...card content...]
#v(16pt)  // gap between sections
```

After:
```typst
#pad(x: {space_md}pt, y: {space_sm}pt)[...card content...]
#v({space_md}pt)  // gap between sections
```

---

## Implementation Summary

### Files to Create

| File | Purpose | Lines (est.) |
|---|---|---|
| `src/inkline/brands/color_ramp.py` | NEW — HSL ramp generator | ~80 |

### Files to Modify

| File | Changes | Impact |
|---|---|---|
| `src/inkline/brands/__init__.py` | Add TypeScale, SpacingScale dataclasses. Add `type_scale`, `spacing`, `primary_ramp`, `secondary_ramp`, `gray_ramp` properties to BaseBrand. Add optional `custom_type_scale` and `custom_spacing` fields. | Backwards compatible — all new fields have defaults |
| `src/inkline/typst/theme_registry.py` | Expand `brand_to_typst_theme()` to emit ramp, type scale, and spacing tokens | Backwards compatible — adds keys, doesn't change existing ones |
| `CLAUDE.md` | Document new token system in brand reference section | Docs only |

### Files NOT Changed (yet)

Typst template files (`slide_renderer.py`, `document_renderer.py`, `components.py`) are
**not modified** in this phase. They continue using existing `heading_size`, `body_size`,
and hardcoded values. A follow-up PR can migrate templates to use the new tokens
progressively — one template at a time, with visual diff testing.

---

## Implementation Order

1. `color_ramp.py` — standalone module, no dependencies
2. `brands/__init__.py` — add TypeScale, SpacingScale, computed properties on BaseBrand
3. `theme_registry.py` — emit new tokens
4. Verification: `python3 -c "from inkline.brands import get_brand; b = get_brand('minimal'); print(b.primary_ramp); print(b.type_scale); print(b.spacing)"`
5. Update CLAUDE.md

---

## Verification

```python
from inkline.brands import get_brand

b = get_brand("minimal")

# Colour ramp
assert len(b.primary_ramp) == 12
assert b.primary_ramp[500] == b.primary
assert b.primary_ramp[25].startswith("#")  # near-white tint

# Typography scale
ts = b.type_scale
assert ts.display_md == b.heading_size  # anchored to existing value
assert ts.body_lg == b.body_size        # anchored to existing value
assert ts.display_xl > ts.display_lg > ts.display_md > ts.display_sm
assert ts.body_lg > ts.body_md > ts.body_sm > ts.caption > ts.overline

# Spacing
sp = b.spacing
assert sp.xxs < sp.xs < sp.sm < sp.md < sp.lg < sp.xl < sp.xxl
assert sp.xs == 4  # 4pt base grid

# Theme integration
from inkline.typst.theme_registry import brand_to_typst_theme
theme = brand_to_typst_theme(b)
assert "primary_500" in theme
assert "display_xl" in theme
assert "space_md" in theme
```

---

## Non-Goals

- **No template migration** — templates keep using hardcoded values until a separate PR.
  This spec only adds the token infrastructure.
- **No OKLCH colour space** — HSL is good enough for our use case (print/slides, not
  perceptual uniformity). OKLCH can be a future enhancement.
- **No dark mode** — Inkline outputs are print/PDF, not screens. Dark mode is irrelevant.
- **No new brand fields required** — existing brands work unchanged. Ramps, scales, and
  spacing are all auto-derived from current `primary`, `heading_size`, `body_size`.
- **No breaking changes** — `heading_size` and `body_size` remain the source of truth.
  TypeScale is derived from them.
