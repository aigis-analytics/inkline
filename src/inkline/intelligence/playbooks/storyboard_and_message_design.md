---
domain: workflow
audience: [institutional, authoring]
slide_type_relevance: []
brand_affinity: [institutional_finance]
version: 1.1.0
last_updated: 2026-06-20
description: Storyboard and key-message rules for aligned authoring and audit.
---

# Storyboard And Message Design

## 1. Storyboard-first rule

Every client-facing deck should have a storyboard before layout generation.

Minimum deck-level fields:

- deck objective
- audience
- thesis
- optional reference family

Minimum slide-level fields:

- stable `slide_id`
- slide role
- full-slide archetype
- key message

The storyboard is the contract between:

- authoring
- rendering
- audit

## 2. One message per slide

A slide is not a page-sized container for all known facts.

Every slide should answer one primary question:

- what should the audience believe after seeing this page?

The title should normally be the takeaway, not the topic.

Strong:

- "Access, not just screening, is the scarce edge in Angola"
- "A $500m equity anchor can seed a multi-asset platform"

Weak:

- "Angola opportunity set"
- "Process"
- "Team"

## 3. Standard storyboard fields

Use these fields consistently:

- `slide_id`
- `role`
- `archetype`
- `key_message`
- `reference_family`

Recommended optional fields:

- `evidence_type`
- `phase`
- `speaker_note_intent`

## 4. Metadata precedence

Metadata precedence should be explicit and deterministic:

1. explicit user override directives
2. slide object storyboard fields
3. top-level storyboard fields
4. inferred defaults

The resolver is the single merge/validation boundary. Render and audit should
consume the resolved result rather than re-merging metadata independently.

## 5. Role selection

Choose the role before choosing the layout.

Common institutional roles:

- `cover`
- `thesis`
- `proposition`
- `team`
- `economics`
- `timeline`
- `process`
- `execution_plan`
- `pipeline`
- `market_map`
- `appendix_ranked_table`

If the role is wrong, the slide will usually be wrong even if the layout is clean.

## 6. Message design by slide family

### 6.1 Cover

Goal:
- frame the entire deck in one sentence

Message form:
- situation + implication

Example:
- "7GI can enter Angola through an access-led upstream M&A platform"

### 6.2 Thesis / proposition

Goal:
- explain why the strategy is true or attractive

Message form:
- 3 to 5 parallel reasons

Example:
- "The best opportunities are not auctioned; they emerge through access, pre-emption, and bilateral structuring"

### 6.3 People / credibility

Goal:
- explain why this team can execute

Message form:
- person + credibility transfer + relevance

Example:
- "Local operating and political access compresses time-to-conversation"

### 6.4 Economics / size of prize

Goal:
- translate capital into believable scale

Message form:
- number + mechanism + implication

Example:
- "A $500m initial equity pool can underwrite a phased multi-deal build rather than a single-asset bet"

### 6.5 Timeline / process

Goal:
- make sequence and gating visible

Message form:
- phase + action + gating point

Example:
- "Angola M&A is a staged regulatory and relationship process, not a straight auction timeline"

## 7. Storyboard to archetype mapping

The storyboard should be rich enough that layout choice becomes easier.

Examples:

- role: `team`
  - key message: "Cliveden can bring named access and on-the-ground execution support"
  - best family: portrait-first biography cards

- role: `timeline`
  - key message: "The reverse roadshow is a phased relationship-building program"
  - best family: banker/process spine

- role: `pipeline`
  - key message: "The opportunity set is broader than public auctions and can be triaged by route-to-access"
  - best family: ranked evidence table or structured pipeline card

## 8. Checklist for authoring quality

Before rendering, ask:

- does each slide have a clear role?
- does each slide have a one-sentence key message?
- is the title actually the message?
- is any page carrying two unrelated arguments?
- has appendix material been separated from core narrative?

## 9. Checklist for audit quality

During audit, ask:

- did the rendered slide still communicate the intended message?
- did the archetype match the declared role?
- did the sequence across slides still tell the intended story?
- did dense pages appear where density was intentional rather than accidental?

## 10. Example storyboard skeleton

```yaml
storyboard:
  deck:
    objective: Build investor confidence in an access-led Angola entry strategy
    audience: 7GI principals
    thesis: Access and local credibility create routes to non-public upstream deals
    reference_family: ccc_angola_focus_v1
  slides:
    s01_cover:
      role: cover
      archetype: cover_hero_photo_left_text_block
      key_message: 7GI can build an Angola platform through access-led M&A
    s02_thesis:
      role: proposition
      archetype: thesis_three_pillar_cards
      key_message: The opportunity is created by route-to-access, not just asset quality
    s03_team:
      role: team
      archetype: executive_bio_cards_centered
      key_message: Cliveden can bring named relationships and local execution support
```

## 11. What storyboarding should prevent

- descriptive but empty slide titles
- random layout switching without narrative reason
- text-heavy pages that should have been archetype-led
- audit systems checking only for clipping without checking message delivery

The storyboard layer exists to stop the deck from being merely well-rendered and
instead make it intentionally argued.

## 12. Institutional deck sequencing benchmark

For investor and advisory decks, the story should normally progress through a
deliberate page family rather than jumping between arbitrary layouts.

Common sequence:

1. `cover` — frame the deck
2. `proposition` — why this matters
3. `proposition / strategy rail` — how the idea works
4. `team` — why we can execute
5. `economics` — what the firepower can become
6. `opportunity_set` — what routes exist
7. `pipeline` — what is actionable now
8. `reference_exhibit / market_map` — where the assets or market sit
9. `programme / roadshow` — how access gets operationalised
10. `critical_path / timeline` — how execution really runs
11. `execution_plan / next_steps` — how the platform build advances
12. `appendix` — evidence, rankings, and workstreams

This is not a rigid formula, but it is a strong default. If a deck deviates,
there should be a reason grounded in audience or objective.

## 13. Main-body compression rule

Main-body slides should carry the argument, not all supporting facts.

Promote to appendix when content is:
- important, but not essential for the 5-second read
- mainly evidentiary rather than persuasive
- too detailed to preserve the dominant gesture of the page

Keep in the main body when content is:
- essential to the argument
- needed for credibility transfer
- the primary reason the page exists

## 14. Synthesis-strip rule

If a slide contains multiple cards, buckets, or phases, ask whether it needs a
bottom synthesis strip to resolve the page into one point.

Good use cases:
- proposition cards
- opportunity triage
- programme / roadshow pages
- process pages with multiple milestones
- appendix workstream pages where one practical takeaway matters

Avoid:
- repeating the title in the bar
- using the bar as a dumping ground for caveats
- stacking multiple bars

## 15. Benchmark questions for authoring and audit

Before sign-off, ask:

- does each slide have one dominant gesture?
- does the page family feel consistent across the deck?
- does the slide need fewer words and a stronger archetype?
- does the page end on a message or merely on content?
- would a human analyst keep the slide as-is, or immediately rebuild it?
