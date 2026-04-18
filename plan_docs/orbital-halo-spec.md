# Orbital / Halo Slide Layout Spec

## Problem
Circular and shaped exhibits (donut, radar, waffle, gauge, entity_flow, hexagonal_honeycomb)
leave 30–50% of slide area as empty whitespace around the shape. Currently wasted.

## Solution
`orbital` slide type: hero exhibit fills full content area, overlay boxes use
Typst `place()` to sit in whitespace without disturbing the flow layout.

`halo` variant: same as orbital + thin leader lines (0.5pt, muted colour) from
each overlay's inner corner toward the slide centre, visually connecting to the exhibit.

## Slide spec format

### orbital
```json
{
  "slide_type": "orbital",
  "data": {
    "section": "...",
    "title": "...",
    "hero": {
      "image_path": "donut.png",
      "chart_request": {}
    },
    "overlays": [
      {
        "position": "tl",
        "type": "stat",
        "value": "$124M",
        "label": "ARR",
        "desc": "Annual recurring revenue",
        "title": "Key drivers",
        "items": ["Item 1", "Item 2"],
        "body": "Free-form text...",
        "image_path": "mini.png",
        "chart_request": {},
        "caption": "optional label"
      }
    ],
    "footnote": ""
  }
}
```

### halo
Same as orbital, plus:
```json
"leader_lines": true
```

## Position codes

| Code | Description              |
|------|--------------------------|
| tl   | top-left corner          |
| tr   | top-right corner         |
| bl   | bottom-left corner       |
| br   | bottom-right corner      |
| tc   | top centre (wide strip)  |
| bc   | bottom centre (wide strip)|
| ml   | left edge, vertically centred |
| mr   | right edge, vertically centred |

## Overlay box sizing by type and position

| Type   | Corner (tl/tr/bl/br) | Edge-centre (tc/bc) | Mid-edge (ml/mr) |
|--------|----------------------|---------------------|------------------|
| stat   | 3.8cm × 2.4cm        | 6.0cm × 2.0cm       | 3.2cm × 3.5cm    |
| bullets| 4.5cm × 3.5cm        | 7.0cm × 3.0cm       | 3.5cm × 5.0cm    |
| text   | 4.5cm × 3.0cm        | 7.0cm × 2.5cm       | 3.5cm × 4.5cm    |
| chart  | 4.5cm × 3.5cm        | 7.5cm × 3.5cm       | 3.5cm × 5.5cm    |

## Leader line geometry (halo only)
- 0.5pt stroke, muted colour, 60% opacity
- From: inner corner of the overlay box
- To: slide content centre (approx 12.7cm from left edge, 7.15cm from top edge of full page)
- Rendered as a Typst `line()` call inside a `place()`

## Acceptance criteria
- Hero image fills 100% of content area (between title bar and footer)
- Overlays don't consume flow space (pure place() overlay)
- Stat overlay: value prominent (18-20pt bold accent), label small (8pt muted uppercase)
- Bullet overlay: title 10pt bold, items 8.5pt with disc bullets, max 4 items
- Chart overlay: image fills the box, optional caption below at 7pt
- Leader lines (halo): thin, subtle, don't compete with exhibit
- All overlays respect brand colours (card_fill, border, text, accent)

## Implementation notes
- `orbital` and `halo` are registered in the `_render_slide` dispatcher
- Overlay `chart_request` entries are pre-rendered in `_auto_render_charts` by
  scanning the `overlays` list inside the slide data
- Hero `chart_request` is also pre-rendered via the same scan (uses full-size
  dimensions: width_inches=9.0, height_inches=5.0)
- `halo` passes `leader_lines=True` to the shared `_orbital_slide()` implementation
- If leader lines cause Typst compile errors they are silently skipped (non-blocking)

## Status
Implemented 2026-04-18
