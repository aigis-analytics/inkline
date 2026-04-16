"""Design Brief Generation — structured brief from input sections + metadata.

Before DesignAdvisor runs, generate a structured design brief that captures
the story arc, key message per section, and visual strategy. Gives
DesignAdvisor Phase 1 (plan) much better context.

Uses an LLM call when available, with rules-based fallback.
"""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass, field
from typing import Any, Optional

log = logging.getLogger(__name__)

# Default bridge URL — mirrors DesignAdvisor
DEFAULT_BRIDGE_URL = "http://localhost:8082"


@dataclass
class DesignBrief:
    """Structured design brief for a deck."""

    deck_purpose: str  # 1-2 sentence summary of what this deck achieves
    audience_profile: str  # Who will see this and what they care about
    story_arc: str  # 3-act structure: setup -> evidence -> ask
    key_message: str  # The single takeaway the audience should remember
    visual_strategy: str  # e.g. "data-heavy with charts", "narrative with infographics"
    section_briefs: list[dict] = field(default_factory=list)  # [{title, intent, suggested_exhibit, key_metric}]
    tone: str = "formal"  # "formal", "conversational", "urgent", "celebratory"
    constraints: list[str] = field(default_factory=list)  # e.g. "max 15 slides"
    anti_goals: list[str] = field(default_factory=list)  # What this deck should NOT do


# ---------------------------------------------------------------------------
# LLM routing — mirrors DesignAdvisor._call_llm() pattern
# ---------------------------------------------------------------------------

def _call_llm(system_prompt: str, user_prompt: str, bridge_url: str | None = None) -> str | None:
    """Route an LLM call: bridge -> Anthropic SDK. Returns None on failure.

    Priority:
    1. LLM bridge at bridge_url (Claude Max subscription)
    2. Anthropic SDK with ANTHROPIC_API_KEY
    Returns None if neither is available (triggers rules fallback).
    """
    url = bridge_url or os.environ.get("INKLINE_BRIDGE_URL", "") or DEFAULT_BRIDGE_URL

    # Ensure bridge is running
    try:
        from inkline.intelligence.claude_code import ensure_bridge_running
        ensure_bridge_running(url)
    except Exception:
        pass

    # Try bridge
    try:
        import requests as _req
        log.info(
            "DesignBrief LLM bridge %s (%d sys / %d user chars)...",
            url, len(system_prompt), len(user_prompt),
        )
        # Poll /status until bridge is idle (bail quickly if unreachable)
        for _attempt in range(60):
            try:
                _st = _req.get(f"{url}/status", timeout=3).json()
                if not _st.get("active", True):
                    break
            except Exception:
                if _attempt == 0:
                    break  # Bridge unreachable on first try — skip polling
            import time as _time
            _time.sleep(5)

        for _bridge_attempt in range(3):
            resp = _req.post(
                f"{url}/prompt",
                json={"prompt": user_prompt, "system": system_prompt, "max_tokens": 8000},
                timeout=(5, None),
            )
            resp.raise_for_status()
            if not resp.content:
                log.warning("Bridge returned empty body (attempt %d/3), retrying...", _bridge_attempt + 1)
                import time as _time2
                _time2.sleep(2)
                continue
            data = resp.json()
            if data.get("response"):
                log.info(
                    "DesignBrief LLM bridge OK -- %d chars (source=%s)",
                    len(data["response"]), data.get("source", "?"),
                )
                return data["response"]
            break
    except Exception as e:
        log.info("DesignBrief LLM bridge unavailable (%s) -- falling back to Anthropic API", e)

    # Anthropic SDK fallback
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        log.info("No LLM available for design brief -- using rules fallback")
        return None

    try:
        import anthropic
    except ImportError:
        log.info("anthropic package not installed -- using rules fallback")
        return None

    try:
        client = anthropic.Anthropic(api_key=api_key)
        log.info("DesignBrief Anthropic API: %d sys / %d user chars", len(system_prompt), len(user_prompt))
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=8000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return response.content[0].text
    except Exception as e:
        log.warning("Anthropic API call failed (%s) -- using rules fallback", e)
        return None


# ---------------------------------------------------------------------------
# LLM prompt construction
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """You are a presentation strategist. Given input sections and context,
produce a design brief that will guide slide deck creation.

Output ONLY a JSON object with these exact keys:
- deck_purpose (string): 1-2 sentence summary of what this deck achieves
- audience_profile (string): Who will see this and what they care about
- story_arc (string): 3-act structure: setup -> evidence -> ask
- key_message (string): The single takeaway the audience should remember
- visual_strategy (string): e.g. "data-heavy with charts", "narrative with infographics"
- section_briefs (array of objects): Per-section [{title, intent, suggested_exhibit, key_metric}]
- tone (string): "formal", "conversational", "urgent", or "celebratory"
- constraints (array of strings): e.g. ["max 15 slides"]
- anti_goals (array of strings): What this deck should NOT do

Output valid JSON only. No markdown fences, no commentary."""


def _build_user_prompt(
    sections: list[dict],
    audience: str,
    goal: str,
    brand: str | None,
    constraints: list[str] | None,
) -> str:
    """Build the user prompt summarising input sections and context."""
    # Summarise each section: title + first 200 chars
    section_summaries = []
    for i, sec in enumerate(sections):
        title = sec.get("title", f"Section {i + 1}")
        # Grab the first 200 chars of narrative/body content
        content = ""
        for key in ("narrative", "body", "text"):
            if key in sec and sec[key]:
                content = str(sec[key])[:200]
                break
        if not content:
            # Try metrics or items
            metrics = sec.get("metrics", {})
            if metrics:
                content = ", ".join(f"{k}: {v}" for k, v in list(metrics.items())[:5])
            items = sec.get("items", [])
            if items:
                content = "; ".join(str(x)[:50] for x in items[:4])
        section_summaries.append(f"- {title}: {content}" if content else f"- {title}")

    sections_text = "\n".join(section_summaries)
    constraints_text = "\n".join(f"- {c}" for c in (constraints or []))

    return f"""Input sections:
{sections_text}

Context:
- Audience: {audience}
- Goal: {goal}
- Brand: {brand or 'minimal'}
- Constraints:
{constraints_text or '  (none)'}

Focus on:
1. What is the story arc? (What problem -> what evidence -> what ask)
2. For each section, what exhibit type best serves the message?
3. What visual strategy matches this audience? (investors want data, boards want summaries)
4. What should this deck explicitly NOT do?"""


# ---------------------------------------------------------------------------
# LLM response parsing
# ---------------------------------------------------------------------------

def _parse_llm_response(text: str) -> DesignBrief | None:
    """Parse an LLM JSON response into a DesignBrief. Returns None on failure."""
    # Strip markdown fences if present
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r'^```(?:json)?\s*', '', text)
        text = re.sub(r'\s*```$', '', text)

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON object in the text
        m = re.search(r'\{[\s\S]*\}', text)
        if not m:
            log.warning("Could not parse LLM response as JSON")
            return None
        try:
            data = json.loads(m.group())
        except json.JSONDecodeError:
            log.warning("Could not parse extracted JSON from LLM response")
            return None

    if not isinstance(data, dict):
        return None

    try:
        return DesignBrief(
            deck_purpose=data.get("deck_purpose", ""),
            audience_profile=data.get("audience_profile", ""),
            story_arc=data.get("story_arc", ""),
            key_message=data.get("key_message", ""),
            visual_strategy=data.get("visual_strategy", ""),
            section_briefs=data.get("section_briefs", []),
            tone=data.get("tone", "formal"),
            constraints=data.get("constraints", []),
            anti_goals=data.get("anti_goals", []),
        )
    except Exception as e:
        log.warning("Failed to construct DesignBrief from parsed JSON: %s", e)
        return None


# ---------------------------------------------------------------------------
# Rules-based fallback
# ---------------------------------------------------------------------------

def _rules_fallback(
    sections: list[dict],
    audience: str,
    goal: str,
    brand: str | None,
    constraints: list[str] | None,
) -> DesignBrief:
    """Generate a brief using heuristics when no LLM is available."""
    audience_lower = audience.lower() if audience else ""
    goal_lower = goal.lower() if goal else ""

    # Audience-based defaults
    if any(kw in audience_lower for kw in ("investor", "vc", "fund", "lp")):
        visual_strategy = "data-heavy with charts and KPIs upfront"
        tone = "formal"
        anti_goals = ["Don't oversell", "Don't hide risks", "Don't use vague claims without data"]
    elif any(kw in audience_lower for kw in ("board", "director", "executive")):
        visual_strategy = "executive summary format with key metrics and decisions needed"
        tone = "formal"
        anti_goals = ["Don't go into operational detail", "Don't exceed 15 slides"]
    elif any(kw in audience_lower for kw in ("team", "internal", "employee")):
        visual_strategy = "narrative with infographics and process flows"
        tone = "conversational"
        anti_goals = ["Don't be overly formal", "Don't omit context"]
    elif any(kw in audience_lower for kw in ("customer", "client", "prospect")):
        visual_strategy = "benefit-focused with social proof and case studies"
        tone = "conversational"
        anti_goals = ["Don't lead with features", "Don't use internal jargon"]
    else:
        visual_strategy = "balanced mix of data exhibits and narrative"
        tone = "formal"
        anti_goals = ["Don't be monotonous", "Don't use text-heavy slides"]

    # Count sections with metrics to adjust strategy
    metric_sections = sum(
        1 for s in sections
        if s.get("metrics") or s.get("table_data") or s.get("series")
    )
    if metric_sections > len(sections) * 0.5:
        visual_strategy = "data-heavy with charts, dashboards, and KPI strips"
    elif len(sections) < 3:
        visual_strategy = "condensed executive format with high-impact exhibits"

    # Build section briefs
    section_briefs = []
    for sec in sections:
        sec_type = sec.get("type", "narrative")
        title = sec.get("title", "Untitled")

        # Suggest exhibit type based on section content
        if sec.get("metrics"):
            suggested = "kpi_strip or icon_stat"
            key_metric = next(iter(sec["metrics"].values()), None) if isinstance(sec["metrics"], dict) else None
        elif sec.get("table_data"):
            suggested = "table or chart_caption"
            key_metric = None
        elif sec.get("series"):
            suggested = "chart_caption or multi_chart"
            key_metric = None
        elif sec.get("steps") or sec_type == "process_flow":
            suggested = "process_flow"
            key_metric = None
        elif sec.get("milestones") or sec_type == "timeline":
            suggested = "timeline"
            key_metric = None
        elif sec.get("cards") or sec_type == "comparison":
            suggested = "three_card or comparison"
            key_metric = None
        else:
            suggested = "three_card or feature_grid"
            key_metric = None

        section_briefs.append({
            "title": title,
            "intent": f"Present {sec_type.replace('_', ' ')} content",
            "suggested_exhibit": suggested,
            "key_metric": str(key_metric) if key_metric else None,
        })

    # Story arc
    if "fundrais" in goal_lower or "invest" in goal_lower or "term sheet" in goal_lower:
        story_arc = "Problem/opportunity -> Traction & evidence -> Investment ask & terms"
    elif "update" in goal_lower or "review" in goal_lower or "report" in goal_lower:
        story_arc = "Context & highlights -> Detailed progress -> Next steps & decisions"
    elif "pitch" in goal_lower or "sell" in goal_lower or "proposal" in goal_lower:
        story_arc = "Pain point -> Solution & differentiation -> Call to action"
    else:
        story_arc = "Setup & context -> Evidence & analysis -> Conclusion & next steps"

    return DesignBrief(
        deck_purpose=f"A {tone} presentation for {audience or 'stakeholders'} to {goal or 'inform and persuade'}",
        audience_profile=f"{audience or 'General audience'} -- focused on clarity and impact",
        story_arc=story_arc,
        key_message=f"Key message aligned with goal: {goal}" if goal else "To be determined from content",
        visual_strategy=visual_strategy,
        section_briefs=section_briefs,
        tone=tone,
        constraints=constraints or [],
        anti_goals=anti_goals,
    )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def generate_brief(
    sections: list[dict],
    audience: str = "",
    goal: str = "",
    brand: str | None = None,
    constraints: list[str] | None = None,
    bridge_url: str | None = None,
) -> DesignBrief:
    """Generate a structured design brief for a slide deck.

    Two paths:
    1. LLM path: Single LLM call with focused prompt. Uses bridge -> Anthropic SDK.
    2. Rules fallback: If no LLM available, uses audience-based heuristics.

    Args:
        sections: List of section dicts (same format as DesignAdvisor input).
        audience: Who will see this deck (e.g. "investors", "board", "team").
        goal: What the deck should achieve (e.g. "secure Series B term sheet").
        brand: Optional brand name.
        constraints: Optional list of constraints (e.g. ["max 20 slides"]).
        bridge_url: Optional LLM bridge URL override.

    Returns:
        DesignBrief with story arc, visual strategy, section briefs, etc.
    """
    # Try LLM path first
    user_prompt = _build_user_prompt(sections, audience, goal, brand, constraints)
    llm_response = _call_llm(_SYSTEM_PROMPT, user_prompt, bridge_url=bridge_url)

    if llm_response:
        brief = _parse_llm_response(llm_response)
        if brief:
            log.info("Design brief generated via LLM (%d section briefs)", len(brief.section_briefs))
            return brief
        log.warning("LLM response could not be parsed -- falling back to rules")

    # Rules fallback
    brief = _rules_fallback(sections, audience, goal, brand, constraints)
    log.info("Design brief generated via rules fallback (%d section briefs)", len(brief.section_briefs))
    return brief
