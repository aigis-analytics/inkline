# Example: Hybrid Deck

A 5-slide market intelligence report combining typed layouts and a freeform
hero exhibit (competitive positioning map).

## What this demonstrates

- Mixing typed layouts (`stat`, `split`, `timeline`, `three_card`) with a freeform exhibit
- Two-backend output: `output: [pdf, pptx]` in front-matter
- `audit: post-render` — no in-loop LLM; run `inkline critique` separately
- Competitive positioning map as a freeform positioned-shapes diagram

## How to render

```bash
# PDF + PPTX
inkline render examples/hybrid_deck/spec.md --output pdf,pptx --brand minimal

# Then critique the output
inkline critique ~/.local/share/inkline/output/spec.pdf --rubric institutional
```

## Pattern: typed layouts + freeform in the same deck

This is the recommended pattern for real-world decks:
- Use typed layouts for 80-90% of slides (faster, more maintainable, better overflow handling)
- Use `freeform` for 1-2 slides that need custom positioning (hero exhibits, diagrams)

Claude Code workflow:
1. Read `inkline://layouts` to understand what typed layouts are available
2. Map content to typed layouts where possible
3. Use `freeform` only for slides with genuinely bespoke visual requirements
4. Render with `inkline render spec.md --output pdf,pptx`
5. Critique with `inkline critique deck.pdf`
