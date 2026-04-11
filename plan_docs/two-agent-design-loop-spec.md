# Two-Agent Design Loop — Specification

**Date:** 11 April 2026
**Depends on:** Visual Auditor Self-Learning Spec (plan_docs/visual-auditor-self-learning-spec.md)

---

## 1. Problem

The DesignAdvisor and Visual Auditor are currently **sequential and unequal**:

- **DesignAdvisor** receives 83K chars of context (full playbooks, slide catalogue, capacity limits, template catalog) and makes all design decisions upfront
- **Visual Auditor** receives 14K chars (truncated playbooks, no slide catalogue) and can only flag problems after rendering — it cannot propose specific redesigns
- The connection between them is **crude keyword matching** in `fix_from_llm_findings()` — "table should be infographic" gets pattern-matched to "reduce_content", which is the wrong fix

The result: the Auditor correctly identifies design problems but the system cannot act on them intelligently. Tables that should be infographics stay as tables. Charts that should highlight key data points don't get fixed. Layout choices that violate consulting design principles persist across iterations.

## 2. Architecture: Adversarial Design Dialogue

```
ROUND 1:
  DesignAdvisor → slide specs (with full context)
  Renderer → PDF
  Visual Auditor → structured critique (with full context + rendered images)
  
ROUND 2 (if Auditor has design objections):
  Auditor's critique → DesignAdvisor (as "reviewer feedback")
  DesignAdvisor → revised slide specs (addressing each objection)
  Renderer → PDF
  Visual Auditor → re-review (did the revision work?)
  
ROUND 3+ (until consensus or max iterations):
  Repeat until Auditor approves OR no further improvement possible
```

The key change: **the Auditor's output feeds back into the DesignAdvisor as structured design feedback**, not into a keyword matcher. The DesignAdvisor can then make informed design decisions about whether to accept or reject the suggestion, and how to implement it.

## 3. What Changes

### 3.1 Visual Auditor gets full design context

The Auditor's system prompt is upgraded to include:
- **Full SLIDE_TYPE_GUIDE** (not truncated) — knows all 22 slide types and their data schemas
- **Full playbooks** (all 83K) — same design knowledge as DesignAdvisor
- **Available alternatives** — when flagging a table, can propose "use icon_stat with data: {stats: [{value: '£11K', label: 'ANALYST'}, ...]}"
- **Original section data** — sees what content the DesignAdvisor was working with

### 3.2 Auditor returns structured redesign proposals

Current output:
```json
[{"severity": "warn", "message": "INFOGRAPHIC > TABLE: This 4-row pricing table would be more effective as an icon_stat layout"}]
```

New output:
```json
[{
  "severity": "warn",
  "category": "layout_change",
  "slide_index": 12,
  "message": "Pricing table with 4 tiers is better as icon_stat — hero numbers are more impactful for investors",
  "proposed_redesign": {
    "slide_type": "icon_stat",
    "data": {
      "section": "Business Model",
      "title": ">99% gross margin at any price point",
      "stats": [
        {"value": "£11K", "icon": "💼", "label": "ANALYST", "desc": "Per-deal, self-service"},
        {"value": "£175K", "icon": "📊", "label": "PROFESSIONAL", "desc": "Annual, 5-15 deals"},
        {"value": "£350K", "icon": "🏢", "label": "ENTERPRISE", "desc": "On-premise, unlimited"},
        {"value": "£10K", "icon": "🔗", "label": "WHITE-LABEL", "desc": "API/embedded per deal"}
      ]
    }
  }
}]
```

The Auditor proposes a **complete slide spec** as an alternative, not just a text complaint.

### 3.3 DesignAdvisor receives review feedback

New function: `revise_slides_from_review()`

```python
def revise_slides_from_review(
    self,
    slides: list[dict],
    review_findings: list[dict],  # structured Auditor output
    original_sections: list[dict],
) -> list[dict]:
    """
    Receive Visual Auditor's review and decide how to respond.
    
    For each finding:
    - If Auditor proposes a redesign: evaluate it, accept or modify
    - If Auditor flags a mechanical issue: apply the fix
    - If Auditor makes a subjective suggestion: use LLM to decide
    
    The DesignAdvisor gets the Auditor's critique as "reviewer feedback"
    in a second LLM call, similar to how a designer responds to
    a creative director's markup.
    """
```

This is a second LLM call to the DesignAdvisor, but with additional context:
```
SYSTEM: [same playbooks + slide catalogue]

USER: 
You previously designed these slides: [current specs]
The Visual Auditor has reviewed the rendered deck and has these objections:
[structured findings with proposed redesigns]

For each objection:
1. If the Auditor proposes a specific redesign, evaluate it:
   - Accept if the redesign genuinely improves the slide
   - Modify if the concept is right but the execution needs adjustment
   - Reject with reasoning if the current design is actually better
2. Return the revised slide specs

Original section data for reference: [sections]
```

### 3.4 The dialogue loop

```python
# In export_typst_slides():

for visual_round in range(max_visual_attempts):
    # Inner overflow loop (unchanged)
    ...
    
    # Visual audit with structured proposals
    findings = audit_deck_with_proposals(
        output_path, slides, original_sections, brand
    )
    
    errors = [f for f in findings if f["severity"] == "error"]
    design_suggestions = [f for f in findings if f.get("proposed_redesign")]
    
    if not errors and not design_suggestions:
        break  # Consensus reached
    
    # DesignAdvisor reviews and responds
    slides = advisor.revise_slides_from_review(
        slides, findings, original_sections
    )
    
    # Re-render with revised slides
    continue
```

## 4. Auditor Prompt: Full Design Context

The `_build_visual_audit_system()` function is expanded to include:

```python
def _build_visual_audit_system(
    slide_type_guide: str,     # Full SLIDE_TYPE_GUIDE (237 lines)
    playbooks: dict,            # All design playbooks (untruncated)
    brand_patterns: list,       # Learned patterns for this brand
    original_sections: list,    # What content the DesignAdvisor was given
) -> str:
```

The Auditor's system prompt grows from 14K to ~90K chars — comparable to DesignAdvisor. This is intentional: **equal context = equal authority in the design dialogue.**

The Auditor's output format changes to structured JSON with:
```json
{
  "severity": "error|warn|info",
  "category": "layout_change|content_trim|spacing_fix|brand_fix|data_viz|structural|positive",
  "slide_index": 0,
  "message": "human-readable description",
  "proposed_redesign": { ... }  // optional: complete slide spec
}
```

## 5. Design Principles Enforcement

The Auditor checks against specific consulting design principles:

1. **Information density**: Is the slide using the right exhibit type for the data volume? (3 items → three_card, 4-6 items with values → icon_stat, 8+ items → table)
2. **Action titles**: Does the title state the insight, not the topic?
3. **60-30-10 colour rule**: 60% background, 30% surface, 10% accent
4. **Exhibit dominance**: Is the main exhibit (chart, infographic) at least 60% of the content area?
5. **Whitespace intentionality**: Is whitespace purposeful (framing content) or accidental (content too small)?
6. **Card consistency**: Equal heights, equal text density, consistent visual treatment
7. **Data highlighting**: In competitive/comparison exhibits, is the client clearly differentiated?
8. **Slide flow**: Does the deck tell a story with logical progression?

When any principle is violated, the Auditor proposes a specific fix — not just flags it.

## 6. Integration with Self-Learning

The two-agent dialogue feeds into the Pattern Memory:

1. When the Auditor proposes a redesign and the DesignAdvisor accepts → pattern recorded (confidence 0.5)
2. When the same pattern is accepted 3+ times across different decks → confidence 0.85 (auto-proposed)
3. When the user approves the pattern → confidence 0.95 (auto-applied)

This means the DesignAdvisor gradually learns to make the right choices upfront, reducing the number of dialogue rounds needed. First deck: 3-4 rounds. Fifth deck: 1 round (most patterns pre-applied).

## 7. Cost Analysis

- Each round: 1 DesignAdvisor call (~8K tokens) + 1 Auditor call per slide (~2K tokens × 18 slides = ~36K tokens) + 1 revision call (~8K tokens)
- Round 1: ~52K tokens
- Each additional round: ~44K tokens (no initial design call)
- Typical 3-round deck: ~140K tokens ≈ $0.50-$1.00 at Sonnet pricing
- Acceptable for investor-grade output quality

## 8. Files to Create/Modify

| File | Action | Key Changes |
|------|--------|-------------|
| `intelligence/design_advisor.py` | Modify | Add `revise_slides_from_review()` method |
| `intelligence/overflow_audit.py` | Modify | `audit_deck_with_proposals()` — structured output with redesign proposals |
| `intelligence/slide_fixer.py` | Modify | `rework_from_suggestions()` replaced by DesignAdvisor revision |
| `intelligence/pattern_memory.py` | Create | YAML pattern storage, confidence scoring |
| `intelligence/feedback.py` | Create | User feedback capture, implicit change detection |
| `typst/__init__.py` | Modify | Dialogue loop replaces current outer loop |

---

## Appendix: Current Implementation Status

### Fully Implemented ✓
- Closed-loop inner overflow detection and fix (3-level graduated)
- Closed-loop outer visual audit loop (LLM inside loop)
- Pre-render validation and auto-fix
- Card height equalisation
- Chart auto-rendering from chart_request
- Chart audit (fit/brand/data)
- Three slide modes (exact/guided/auto)
- Design-aware visual auditor (with truncated playbooks)
- Scatter chart highlighting
- Timeline bubble sizing
- Title slide brand customisation

### Specced But Not Implemented ❌
- **Suggestion → Action Engine**: `rework_from_suggestions()` for layout_change redesigns
- **Pattern Memory**: `pattern_memory.py` + per-brand YAML storage
- **User Feedback Loop**: `feedback.py` + CLI capture + implicit detection
- **Pattern injection into prompts**: DesignAdvisor + Auditor prompt enrichment
- **Two-Agent Design Dialogue**: DesignAdvisor revision from Auditor critique (this spec)
- **Structured Auditor output**: Proposed redesigns with complete slide specs
- **Equal-context Auditor**: Full playbooks + slide catalogue (currently truncated)
