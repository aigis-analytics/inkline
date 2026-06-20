---
domain: workflow
audience: [institutional, authoring]
slide_type_relevance: []
brand_affinity: [institutional_finance]
version: 1.0.0
last_updated: 2026-06-20
description: Storyboard and key-message rules for aligned authoring and audit.
---

# Storyboard And Message Design

Every client-facing deck should have:

- deck objective
- audience
- thesis
- stable `slide_id` per slide
- slide role
- full-slide archetype
- key message
- optional `reference_family`

Metadata precedence:

1. explicit user override directives
2. slide object storyboard fields
3. top-level storyboard fields
4. inferred defaults

The resolver is the single merge/validation boundary. Render and audit should
consume the resolved result rather than re-merging metadata independently.
