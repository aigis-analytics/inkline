---
domain: workflow
audience: [institutional, operator]
slide_type_relevance: []
brand_affinity: [institutional_finance]
version: 1.1.0
last_updated: 2026-06-20
description: How benchmark PPTX decks are ingested into Inkline reference families.
---

# Reference Deck Ingestion

## 1. Purpose

Reference-deck ingestion exists to convert a strong benchmark deck into a
reusable design system, not just a screenshot archive.

The ingestion pipeline should capture:

- slide role
- full-slide archetype candidate
- content schema
- style tokens
- layout family
- editability implications

The output should be reusable by both:

- authoring systems choosing archetypes
- audit systems checking benchmark alignment

## 2. Core rule: separate structure from appearance

Do not treat a reference deck as only a visual mood board.

Extract separately:

- semantic structure
  - cover, thesis, people, timeline, appendix table, etc.
- content slots
  - title, subtitle, hero image, proof cards, footnote, source, badge strip
- visual tokens
  - palette, typography, spacing rhythm, card radius, footer behavior, divider treatment
- reference assets
  - preview images and slide manifests for benchmark lookup

## 3. What a reference family should contain

Minimum family-level metadata:

- `reference_family_id`
- license / confidentiality classification
- source deck identity
- theme / ratio / source mode
- family-level style tokens
- slide list with role and archetype candidate per slide

Minimum slide-level metadata:

- `reference_slide_id`
- source slide index
- role
- archetype candidate
- title style / text hierarchy hints
- preview and manifest references

## 4. Ingestion workflow

### 4.1 Accepted input

Current rule:

- `PPTX` only for the institutional benchmark workflow

Why:

- PowerPoint preserves editable structure, placeholder behavior, shape groups,
  notes, and slide-family recurrence better than PDF alone

### 4.2 First extraction pass

First pass should identify:

- structural slides
  - cover, divider, closing
- recurring content families
  - proposition, people, timeline, KPI, table, map
- repeated style tokens
  - palette, font pairings, footer pattern, margin rhythm

### 4.3 Family normalization

Normalize the extracted slides into:

- a family manifest
- per-slide manifests
- preview assets
- curation overrides log

### 4.4 Operator curation

The operator should then refine with `curation_overrides.yaml`.

This is where you correct:

- wrong role labels
- wrong archetype candidates
- weak exemplar flags
- slides that should not be exposed through MCP

## 5. Curation rules

Use curation to improve judgment, not to hide a broken extractor.

Operator overrides may set:

- `role_override`
- `archetype_override`
- `exemplar_strength`
- notes about why the slide matters

Good practice:

- mark only the strongest 1 to 3 slides per family as strong exemplars
- avoid over-tagging every slide as reusable
- keep explanatory notes short and operational

## 6. Confidentiality and exposure

Reference families have four practical exposure classes:

- `public_reusable`
- `public_reference_only`
- `private_internal`
- `client_confidential`

Rules:

- only public classes should be exposed through general MCP resource listing
- private and confidential decks may still drive local authoring decisions
- no host-bound private paths should leak through MCP resources
- no confidential preview/manifests should be available via public repo artifacts

## 7. Style tokens to extract

At minimum, extract:

- background mode
- dominant and accent colors
- heading/body font pair
- title scale
- card border/fill/shadow rules
- footer structure
- divider treatment
- image treatment
- density level

Examples:

- "light institutional body slides with dark cover/dividers"
- "portrait-led team cards with centered names"
- "white card on neutral canvas with muted footer strip"

## 8. Archetype cues to capture

Capture not just that a slide is a `team` page, but what family of team page it is.

Examples:

- circular portrait cards with centered labels
- left-rail biography stack
- horizontal leadership strip with logo row
- two-zone hero metric page
- phase-based banker timeline

That is what lets the retrieval layer select a *full-slide idea* rather than
just a generic element type.

## 9. Recommended validation checklist

Before a family is considered usable:

- family id resolves cleanly
- slide ids are unique and stable
- no manifest path escapes the catalog root
- confidentiality classification is present
- role labels are valid
- archetype overrides are valid
- exposed MCP views are sanitized

## 10. CLI workflow

Current commands:

```bash
inkline ingest-reference benchmark.pptx --family ccc_angola_focus_v1
inkline apply-curation --family ccc_angola_focus_v1
```

Catalog roots:

- packaged/reference-safe: `src/inkline/intelligence/reference_catalog/`
- local/private: `~/.config/inkline/reference_catalog/`

## 11. What the ingestion layer should not do

- should not pretend OCR alone is enough
- should not flatten every slide into a one-off template
- should not expose confidential references through MCP
- should not hard-bind manifests to absolute host paths
- should not treat preview images as the only durable representation

## 12. Relationship to authoring and audit

Reference families support three downstream tasks:

- retrieval bias for archetype selection
- benchmark alignment during audit
- human operator review of exemplars

The important point is consistency:

- authoring and audit should speak the same role/archetype vocabulary
- a reference family should bias generation, not silently override explicit user intent
