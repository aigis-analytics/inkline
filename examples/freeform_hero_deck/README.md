# Example: Freeform Hero Deck

A 4-slide technical architecture deck demonstrating the `freeform` slide_type
for a bespoke hero exhibit alongside typed layouts.

## What this demonstrates

- `_layout: freeform` + `_shapes_file:` directive for a custom architecture diagram
- Shapes manifest with 8 shape types (rect, rounded_rect, text, arrow, circle, etc.)
- Mixing typed layouts (content, process_flow, stat) with a freeform hero exhibit

## Files

- `spec.md` — the deck spec with directives
- `shapes/architecture_diagram.json` — positioned shapes manifest for slide 2

## How to render

```bash
inkline render examples/freeform_hero_deck/spec.md --output pdf --brand minimal
```

## Shapes manifest format

```json
{
  "shapes": [
    {"type": "rounded_rect", "x": 5, "y": 15, "w": 18, "h": 12,
     "fill": "#1A2B4A", "radius": 0.2, "units": "pct"},
    {"type": "text", "x": 6, "y": 17, "w": 16, "h": 8,
     "text": "Label", "font": "Inter", "size": 11, "color": "#FFFFFF",
     "anchor": "mc", "units": "pct"},
    {"type": "arrow", "x1": 23, "y1": 21, "x2": 38, "y2": 30,
     "color": "#4A6FA5", "thickness": 1.5, "units": "pct"}
  ]
}
```

All coordinates are in percentage units (0-100 of slide width/height).
Valid shape types: `image`, `rounded_rect`, `rect`, `text`, `line`, `arrow`, `circle`, `polygon`.

## When to use freeform

Use `_layout: freeform` when:
- The slide needs custom positioning that no typed layout supports
- You have a complex workflow diagram, org chart, or architecture diagram
- You're adapting a design from a reference image (Figma, PowerPoint, etc.)

For most slides, prefer a typed layout — it's faster and more maintainable.
