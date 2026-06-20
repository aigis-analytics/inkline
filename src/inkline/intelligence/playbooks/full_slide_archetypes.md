---
domain: layout
audience: [institutional, investor_decks]
slide_type_relevance: [title, three_card, process_flow, team_grid, dashboard, table, chart_caption]
brand_affinity: [institutional_finance]
version: 1.1.0
last_updated: 2026-06-20
description: Full-slide archetype catalogue for storyboard-aware institutional decks.
---

# Full-Slide Archetypes

## 1. Why full-slide archetypes exist

Inkline distinguishes between three different layers:

- renderer-native `slide_type`
- semantic `full-slide archetype`
- deck-level `slide role`

The authoring layer should choose a full-slide archetype first, then compile it
down to an existing slide type or freeform manifest. This follows the strongest
current pattern in presentation-generation systems: choose the function of the
page, then choose the visual family, then populate the slots.

## 2. Core rule: one dominant gesture per slide

Every archetype should produce one dominant visual gesture, not a pile of equal
weight boxes.

Examples of dominant gestures:

- hero cover with one image + one title block
- three-pillar frame with three equal proof cards
- vertical transaction/process spine with milestone cards
- ranked table card with one evidence grid
- centered executive biographies with portrait-first hierarchy

Reject:

- five unrelated cards with identical importance
- a title, a chart, a matrix, and a quote all competing on one page
- dense bullet-led content pretending to be a process or infographic page

## 3. What each archetype must define

Every archetype should specify:

- `functional role`
- `message shape`
- `content schema`
- `preferred evidence type`
- `visual hierarchy`
- `compile target`
- `anti-patterns`
- `audit expectations`

Minimum schema fields:

- required data slots
- optional data slots
- whether the page is proof-led, narrative-led, or hybrid
- whether raster/reference embeds are acceptable in editable PPTX output

## 4. Slide families for institutional decks

### 4.1 Cover / opening family

Purpose:
- establish tone, topic, and confidence immediately

Use when:
- the slide opens the deck or a major section

Rules:
- headline must read like the conclusion or framing statement, not a file name
- image treatment must be deliberate: full-bleed, banded, or abstract backdrop
- subtitle/date/logo should be subordinate

Recommended archetype:
- `cover_hero_photo_left_text_block`

### 4.2 Thesis / proposition family

Purpose:
- make the strategic case in 3 to 5 points

Use when:
- the slide explains why the opportunity, market, or strategy matters

Rules:
- each card or pillar must have a short action title
- proof belongs inside cards, not in a separate note dump below
- equal columns are acceptable only if the points are genuinely parallel

Recommended archetypes:
- `thesis_three_pillar_cards`
- `numbered_horizontal_proposition_rail`

### 4.3 People / credibility family

Purpose:
- show why this team can execute

Use when:
- the page is about leadership, access, local operating capability, or advisory bench

Rules:
- 2 to 4 people is the default strong range
- portraits dominate; biographies stay short
- each person needs one credibility line, not a CV paragraph
- logos or transaction badges are allowed when they speed up credibility transfer

Recommended archetype:
- `executive_bio_cards_centered`

### 4.4 Economics / firepower family

Purpose:
- show capital, capacity, value creation, or quantified prize

Use when:
- the page needs to make numerical ambition legible fast

Rules:
- one hero metric cluster should dominate
- support bullets exist only to explain how the number works
- avoid dense valuation tables in the main body unless the page is explicitly an appendix

Recommended archetype:
- `firepower_two_zone_summary`

### 4.5 Process / timeline family

Purpose:
- show progression, workstreams, or transaction stages

Use when:
- the slide communicates sequence and dependency rather than merely a list of activities

Rules:
- group by phase, not just date
- a timeline must read directionally in under 5 seconds
- every milestone card needs a label, not a paragraph

Recommended archetype:
- `banker_vertical_process_spine`

### 4.6 Dense evidence family

Purpose:
- present ranked pipeline, diligence evidence, or appendix support

Use when:
- density is part of the slide’s job and the audience expects a banking-style appendix page

Rules:
- preserve a strong header band and row hierarchy
- density is allowed, but not visual collapse
- use clear zoning for rank, item, value, timing, and note

Recommended archetype:
- `appendix_ranked_table_card`

### 4.7 Reference exhibit family

Purpose:
- preserve a strong existing map, diagram, or reference image rather than rebuilding it badly

Use when:
- the original exhibit is already better than a quick reconstruction

Rules:
- the image must dominate the page
- surrounding annotation must stay light
- this is the cleanest acceptable use of a declared editability exception in PPTX

Recommended archetype:
- `market_map_reference_exhibit`

## 5. Archetype selection rules

Choose archetypes by function, not by superficial shape.

Selection order:

1. determine the slide role
2. determine the key message
3. determine the dominant evidence type
4. choose the narrowest archetype that fits all three

Examples:

- key message: "Our Angola edge is access, not just screening"
  - role: proposition
  - evidence: 3 parallel strategic reasons
  - archetype: `thesis_three_pillar_cards`

- key message: "7GI needs local access plus execution credibility"
  - role: team
  - evidence: named people and short credentials
  - archetype: `executive_bio_cards_centered`

- key message: "A typical Angola M&A process takes 6 to 12 months with visible gating points"
  - role: timeline / process
  - evidence: phased milestones
  - archetype: `banker_vertical_process_spine`

## 6. Common anti-patterns

- using a generic content slide when the message is clearly a process, people, or thesis page
- treating an appendix table as though it should obey sparse infographic density
- forcing every slide into a card grid
- inventing a new one-off layout when an existing institutional family already fits
- allowing the headline to restate the topic instead of delivering the message

## 7. Editable PPTX implications

Archetypes should declare when a slide is:

- `native`
- `native_with_exceptions`
- `fallback`

Institutional decks should normally ship with:

- native shapes and text for primary pages
- only narrow exceptions for intentional raster/reference assets
- no silent downgrade from a process/timeline archetype into a generic fallback slide

## 8. Audit expectations

The auditor should check:

- whether the slide matches its chosen archetype family
- whether the dominant gesture is obvious
- whether the page delivered one core message
- whether density level matched the declared role

Questions to ask:

- can the main point be read in under 5 seconds?
- is there one dominant gesture, or just several equal-weight boxes?
- does the slide end with a point, not just content?

## 9. Institutional investor-deck system patterns

The strongest professional investor decks behave like a page family, not a
collection of unrelated clean layouts. The analyst-reworked `7GI` Angola deck
is the current internal benchmark for this standard.

### 9.1 Cover hero with footer band

Purpose:
- open with confidence and immediate topic framing

Rules:
- use one full-bleed or near-full-bleed hero image
- keep the title block large, sparse, and anchored
- subordinate date/context to the title
- use a deliberate footer band rather than scattered footer items

Recommended archetype:
- `cover_hero_photo_left_text_block`

### 9.2 Proposition cards with numbered header badges

Purpose:
- explain 3 parallel strategic reasons without looking like a generic card grid

Rules:
- each card needs a strong top band
- use a circular number badge that overlaps the band; the badge is part of the
  card grammar, not a separate icon
- body copy should stay short enough that the card still reads as a visual unit
- add one bottom synthesis strip if the cards need to resolve into one message

Recommended archetype:
- `thesis_three_pillar_cards`

### 9.3 Numbered rail / stepped strategy page

Purpose:
- communicate a staged strategy or multi-point proposition with momentum

Rules:
- use a visible path, spine, or stepped rail so the eye reads in order
- every item should be a raised card with one short bold phrase, not a paragraph
- numbered markers should carry the rhythm of the page

Recommended archetype:
- `numbered_horizontal_proposition_rail`

### 9.4 Portrait-first executive biographies

Purpose:
- make the team or access bench feel credible and calm, not crowded

Rules:
- use 2 to 4 centered portrait cards
- portraits should dominate the upper half of each card
- role line should be short and italic or stylistically subordinate
- end the page with one access/support synthesis bar rather than extra bullets

Recommended archetype:
- `executive_bio_cards_centered`

### 9.5 Two-zone economics bridge

Purpose:
- combine assumptions, capital logic, and resulting outcome without turning the
  page into a spreadsheet

Rules:
- left side: assumptions or transaction logic
- right side: bridge, capital staircase, or outcome stack
- one bottom interpretation bar should state the implication
- avoid multiple mini-tables competing with the main bridge

Recommended archetype:
- `firepower_two_zone_summary`

### 9.6 Opportunity triage trio

Purpose:
- classify an opportunity set into 3 distinct routes without looking repetitive

Rules:
- three buckets are acceptable if the headers are visually distinct
- each bucket should feel like a route-to-entry category, not a random list
- use one bottom synthesis strip to convert the page into an argument

Recommended archetype:
- `three_route_opportunity_triage`

### 9.7 Dense pipeline with project anchor column

Purpose:
- show a ranked or triaged live pipeline while preserving readability

Rules:
- leftmost project labels should read like anchor objects, not plain text rows
- keep headers as strong bands
- zone the page clearly into project, metrics, route, and note
- use one methodology or caveat strip below instead of inline disclaimer clutter

Recommended archetype:
- `pipeline_evidence_table`

### 9.8 Programme cards with directional transitions

Purpose:
- present a roadshow, workplan, or staged programme as a designed journey

Rules:
- each day/phase should be a tabbed or ticket-like card family
- use directional arrows between phases
- keep phase lists short and numbered
- one bottom objective strip should resolve why the programme exists

Recommended archetype:
- `programme_day_cards`

### 9.9 Critical-path vertical spine

Purpose:
- communicate that process is governed by approvals, gating, and choreography

Rules:
- central spine or directional axis should dominate
- alternating left/right phase cards improve rhythm
- cards must be short enough to read as milestones, not prose boxes
- use one bottom workstream strip to show what runs throughout

Recommended archetype:
- `banker_vertical_process_spine`

### 9.10 Appendix evidence pages that still look designed

Purpose:
- keep appendix slides inside the same professional system as the main deck

Rules:
- preserve full title hierarchy and header chrome
- tables should still have strong visual anchors, such as rank badges, priority
  chips, or grouped headers
- appendix pages may be dense, but they must still show row hierarchy and a
  controlled evidence rhythm

Recommended archetypes:
- `appendix_ranked_table_card`
- `appendix_workstream_icon_cards`

## 10. Companion pattern: the synthesis strip

Many institutional slides become materially stronger when they end with a
full-width synthesis strip.

Use it when:
- the page needs to resolve multiple cards into one point
- the argument would otherwise feel like display rather than persuasion
- the deck benefits from a repeatable main-body ending device

Rules:
- one sentence only
- full-width or near-full-width
- visually subordinate to the title, but stronger than footnotes
- do not stack multiple takeaway bars on one page

- Is this clearly a people page, a process page, a thesis page, or an evidence page?
- Is there a dominant zone?
- Would a human analyst keep this slide as-is, or immediately rebuild it in PowerPoint?

## 9. Machine-readable registry

Use these MCP resources for the runtime registry:

- `inkline://slide_roles`
- `inkline://archetypes/full_slide`
- `inkline://archetypes/full_slide/<id>`

The markdown playbook should teach judgment; the registry should teach the
machine-readable contract.
