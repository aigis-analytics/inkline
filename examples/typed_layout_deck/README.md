# Example: Typed Layout Deck

A generic 8-slide investor pitch deck demonstrating all the common typed layouts.
Renders deterministically via execute-mode — no LLM call for layout decisions.

## Layouts demonstrated

| Slide | Layout | When to use |
|---|---|---|
| The Problem | `three_card` | 3 parallel points |
| Our Solution | `split` | Text + comparison table |
| Market Opportunity | `stat` | 1-3 hero numbers |
| Traction | `kpi_strip` | 4-8 KPI boxes in a row |
| Product Capabilities | `four_card` | 2×2 feature grid |
| The Team | `content` | Narrative + bullets |
| Financial Model | `table` | Data table |
| Ask | `split` | Text + list |

## How to render

```bash
inkline render examples/typed_layout_deck/spec.md --output pdf --brand minimal
```

## Key directives used

- `_layout: <type>` — explicit layout, defaults `_mode: exact`
- `audit: post-render` — no in-loop LLM; run `inkline critique` separately
- All layouts in this deck are supported by both Typst and PPTX backends

## How Claude Code should use this pattern

1. Read the knowledge base: `inkline knowledge get inkline://layouts/three_card`
2. Write a spec with explicit `_layout` directives based on content shape
3. Render: `inkline render spec.md --output pdf,pptx`
4. Optionally critique: `inkline critique output.pdf --rubric institutional`
