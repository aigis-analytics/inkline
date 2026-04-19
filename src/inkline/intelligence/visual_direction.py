"""Visual Direction Agent — LLM-driven visual direction for decks.

Uses Claude (via bridge or API) to reason about visual design choices using
playbooks and templates. Falls back to rules-based engine if LLM unavailable.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Callable, Optional

from inkline.intelligence.design_brief import DesignBrief
from inkline.intelligence.design_context import DesignContext
from inkline.intelligence.visual_brief import VisualBrief

log = logging.getLogger(__name__)

# Type alias for LLM caller
LLMCaller = Callable[[str, str], str]


def generate_visual_brief(
    deck_outline: list[dict[str, Any]],
    design_brief: DesignBrief,
    brand: str,
    n8n_endpoint: str = "",
    design_context: Optional[DesignContext] = None,
    llm_caller: Optional[LLMCaller] = None,
    bridge_url: Optional[str] = None,
) -> VisualBrief:
    """Generate visual direction for a deck using LLM reasoning.

    Args:
        deck_outline: Slide plan from DesignAdvisor Phase 1 (list of {slide_type, title, notes})
        design_brief: DesignBrief (audience, tone, purpose)
        brand: Brand name ("minimal", etc.)
        n8n_endpoint: Optional n8n webhook URL for background generation
        design_context: Explicit user intent (audience, tone, focus, industry)
        llm_caller: Optional injected LLM callable for testing
        bridge_url: Optional Claude Code bridge URL

    Returns:
        VisualBrief with all visual decisions locked in
    """
    log.info(
        "Visual Direction Agent: LLM reasoning for %s (outline=%d slides, context=%s)",
        design_brief.deck_purpose[:40],
        len(deck_outline),
        "explicit" if design_context else "inferred",
    )

    try:
        # Try LLM-driven reasoning first
        brief = _generate_via_llm(
            deck_outline=deck_outline,
            design_brief=design_brief,
            brand=brand,
            design_context=design_context,
            llm_caller=llm_caller,
            bridge_url=bridge_url,
        )

        if brief:
            # Generate background images if requested
            if n8n_endpoint and brief.background_requests:
                _generate_backgrounds(brief, n8n_endpoint)

            log.info(
                "Visual Brief ready (LLM): %s + %d backgrounds",
                brief.template,
                len(brief.background_paths),
            )
            return brief
    except Exception as e:
        log.warning("LLM visual direction failed: %s — falling back to rules", e)

    # Fall back to rules-based engine
    return _generate_via_rules(deck_outline, design_brief, brand, n8n_endpoint)


# ─────────────────────────────────────────────────────────────────────────────
# LLM-Driven Path
# ─────────────────────────────────────────────────────────────────────────────


def _generate_via_llm(
    deck_outline: list[dict[str, Any]],
    design_brief: DesignBrief,
    brand: str,
    design_context: Optional[DesignContext],
    llm_caller: Optional[LLMCaller],
    bridge_url: Optional[str],
) -> Optional[VisualBrief]:
    """Generate visual brief via LLM reasoning. Returns None on failure."""

    system_prompt = _build_vda_system_prompt()
    user_prompt = _build_vda_user_prompt(
        deck_outline, design_brief, brand, design_context
    )

    # Call LLM (bridge-first routing, then SDK, then fail)
    response = _call_llm_vda(
        system_prompt, user_prompt, llm_caller=llm_caller, bridge_url=bridge_url
    )

    if not response:
        return None

    # Parse JSON response
    try:
        data = json.loads(response)
        brief = _parse_vda_response(data, design_context)
        log.info("Parsed VisualBrief from LLM: register=%s, template=%s", brief.register, brief.template)
        return brief
    except Exception as e:
        log.warning("Failed to parse LLM response as JSON: %s", e)
        return None


def _build_vda_system_prompt() -> str:
    """System prompt for visual direction reasoning."""
    from inkline.intelligence.playbooks import load_playbook_summary
    from inkline.intelligence.template_catalog import ARCHETYPES, load_manifest

    parts = [
        "You are a visual design director for presentation decks. "
        "Your decisions are consumed directly by a rendering pipeline — output must be valid JSON only.",
        "",
        "## DESIGN KNOWLEDGE",
        "",
        "### Colour Theory & Palette Design",
        load_playbook_summary("color_theory", max_chars=6000) or "",
        "",
        "### Template Catalogue",
        load_playbook_summary("template_catalog", max_chars=4000) or "",
        "",
        "### Typography",
        load_playbook_summary("typography", max_chars=3000) or "",
        "",
        "### Available Templates",
        _format_template_list(),
        "",
        "### Available Archetypes",
        _format_archetype_list(),
        "",
        "## OUTPUT SCHEMA (REQUIRED JSON FORMAT)",
        _format_output_schema(),
    ]

    return "\n".join(filter(None, parts))


def _format_template_list() -> str:
    """List all available templates for the LLM."""
    from inkline.intelligence.template_catalog import load_manifest

    try:
        manifest = load_manifest("minimal")
    except Exception:
        manifest = None
    if not manifest:
        return "- pitch, consulting, editorial, dmd_stripe, dmd_apple, dmd_framer, banking, boardroom, investor, executive, dmd_vercel, dmd_cursor, dmd_warp, brand (default)"

    lines = []
    for name, meta in manifest.items():
        best_for = meta.get("best_for", "")
        lines.append(f"- {name}: {best_for}")

    return "\n".join(lines) if lines else ""


def _format_archetype_list() -> str:
    """List archetypes with their purposes."""
    from inkline.intelligence.template_catalog import ARCHETYPES

    lines = []
    for name, arch in ARCHETYPES.items():
        best_for = arch.get("best_for", "")
        lines.append(f"- {name}: {best_for}")

    return "\n".join(lines) if lines else ""


def _format_output_schema() -> str:
    """JSON schema for VisualBrief output."""
    return """
{
  "register": "investor_pitch" | "executive_report" | "brand_editorial" | "consulting_proposal" | "technical_doc",
  "template": "pitch" | "consulting" | "editorial" | ... (from available templates list),
  "palette": {
    "dominant_bg": "#RRGGBB",
    "secondary_bg": "#RRGGBB",
    "accent": "#RRGGBB",
    "text_primary": "#RRGGBB",
    "text_secondary": "#RRGGBB",
    "divider_bg": "#RRGGBB"
  },
  "image_style": "abstract_geometric" | "organic_ink" | "editorial_photo" | "icon_only" | "none",
  "image_color_grade": "cool" | "warm" | "monochrome" | "native",
  "overlay_opacity": 0.0 to 0.6,
  "interstitial_frequency": 6 | 8 | 999,
  "cover_treatment": "full_bleed_dark" | "full_bleed_brand" | "light_editorial",
  "avg_density": "low" | "medium" | "high",
  "chart_gridlines": true | false,
  "chart_borders": true | false,
  "chart_accent_protocol": "one_per_slide" | "series_color",
  "chart_data_labels": true | false,
  "chart_legend_position": "top" | "bottom" | "right" | "off",
  "background_requests": []
}

CRITICAL: Output valid JSON only. No markdown, no explanations, no preamble.
"""


def _build_vda_user_prompt(
    deck_outline: list[dict[str, Any]],
    design_brief: DesignBrief,
    brand: str,
    design_context: Optional[DesignContext],
) -> str:
    """User prompt for visual direction reasoning."""

    parts = ["Design the visual direction for this presentation.", ""]

    # Explicit user intent
    if design_context:
        parts.extend(
            [
                "EXPLICIT USER INTENT (do not override these):",
                design_context.to_prompt_fragment(),
                "",
            ]
        )

    # Content brief
    parts.extend(
        [
            "CONTENT BRIEF:",
            f"- Deck purpose: {design_brief.deck_purpose}",
            f"- Story arc: {design_brief.story_arc}",
            f"- Key message: {design_brief.key_message}",
            f"- Tone: {design_brief.tone}",
            f"- Anti-goals: {', '.join(design_brief.anti_goals) if design_brief.anti_goals else 'none'}",
            f"- Visual strategy hint: {design_brief.visual_strategy}",
            "",
        ]
    )

    # Deck outline
    if deck_outline:
        parts.append(f"DECK OUTLINE ({len(deck_outline)} slides):")
        for entry in deck_outline[:30]:  # Limit to first 30 for token budget
            slide_type = entry.get("slide_type", "unknown")
            title = entry.get("title", "")[:50]
            parts.append(f"  - {slide_type}: {title}")
        if len(deck_outline) > 30:
            parts.append(f"  ... and {len(deck_outline) - 30} more slides")
        parts.append("")
    else:
        parts.append("DECK OUTLINE: Not yet generated (will be filled by design phase)")
        parts.append("")

    # Brand
    parts.extend([f"BRAND: {brand}", "", "Reason step by step about the visual direction.", ""])

    return "\n".join(parts)


def _call_llm_vda(
    system_prompt: str,
    user_prompt: str,
    llm_caller: Optional[LLMCaller] = None,
    bridge_url: Optional[str] = None,
) -> Optional[str]:
    """Call LLM with bridge-first routing. Returns response text or None on failure."""

    # Priority 1: Injected caller (for testing)
    if llm_caller:
        try:
            return llm_caller(system_prompt, user_prompt)
        except Exception as e:
            log.warning("Injected LLM caller failed: %s", e)
            return None

    # Priority 2: Bridge
    if bridge_url:
        try:
            from inkline.intelligence.claude_code import ensure_bridge_running

            ensure_bridge_running(bridge_url)

            import requests

            resp = requests.post(
                f"{bridge_url}/prompt",
                json={
                    "prompt": user_prompt,
                    "system": system_prompt,
                    "max_tokens": 8000,
                },
                timeout=(5, None),
            )
            resp.raise_for_status()
            return resp.json().get("response", "")
        except Exception as e:
            log.warning("Bridge LLM call failed: %s", e)
            return None

    # Priority 3: Anthropic SDK
    try:
        import anthropic

        client = anthropic.Anthropic()
        msg = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=8000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return msg.content[0].text
    except Exception as e:
        log.warning("Anthropic SDK LLM call failed: %s", e)
        return None


def _parse_vda_response(
    data: dict, design_context: Optional[DesignContext]
) -> VisualBrief:
    """Parse LLM JSON response into VisualBrief."""

    palette = data.get("palette", {})

    return VisualBrief(
        register=data.get("register", "consulting_proposal"),
        tone=data.get("tone", "formal"),
        template=data.get("template", "consulting"),
        dominant_bg=palette.get("dominant_bg", "#FFFFFF"),
        secondary_bg=palette.get("secondary_bg", "#1A2332"),
        accent=palette.get("accent", "#2563EB"),
        text_primary=palette.get("text_primary", "#0F172A"),
        text_secondary=palette.get("text_secondary", "#64748B"),
        divider_bg=palette.get("divider_bg", "#1A2332"),
        image_style=data.get("image_style", "none"),
        image_color_grade=data.get("image_color_grade", "native"),
        overlay_opacity=float(data.get("overlay_opacity", 0.35)),
        interstitial_frequency=int(data.get("interstitial_frequency", 999)),
        cover_treatment=data.get("cover_treatment", "full_bleed_brand"),
        avg_density=data.get("avg_density", "medium"),
        chart_gridlines=bool(data.get("chart_gridlines", False)),
        chart_borders=bool(data.get("chart_borders", False)),
        chart_accent_protocol=data.get("chart_accent_protocol", "one_per_slide"),
        chart_data_labels=bool(data.get("chart_data_labels", True)),
        chart_legend_position=data.get("chart_legend_position", "top"),
        background_requests=data.get("background_requests", []),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Rules-Based Fallback (Legacy VDA)
# ─────────────────────────────────────────────────────────────────────────────


def _generate_via_rules(
    deck_outline: list[dict[str, Any]],
    design_brief: DesignBrief,
    brand: str,
    n8n_endpoint: str = "",
) -> VisualBrief:
    """Fallback rules-based visual brief generation."""

    log.info("Using rules-based Visual Direction (deterministic fallback)")

    register = _determine_register(design_brief)
    template = _select_template(register, brand)
    palette = _select_palette(register, brand)
    image_style, image_color_grade = _select_image_treatment(register, n8n_endpoint, deck_outline)
    interstitial_freq, cover_treatment, avg_density = _determine_pacing(
        len(deck_outline), design_brief
    )
    chart_style = _select_chart_style(register)

    background_reqs = []
    if n8n_endpoint and image_style != "none":
        background_reqs = _generate_background_requests(
            register, image_style, palette, deck_outline, design_brief
        )

    brief = VisualBrief(
        register=register,
        tone=design_brief.tone,
        template=template,
        dominant_bg=palette["dominant_bg"],
        secondary_bg=palette["secondary_bg"],
        accent=palette["accent"],
        text_primary=palette["text_primary"],
        text_secondary=palette["text_secondary"],
        divider_bg=palette["divider_bg"],
        image_style=image_style,
        image_color_grade=image_color_grade,
        overlay_opacity=0.35 if image_style in ("abstract_geometric", "editorial_photo") else 0.0,
        interstitial_frequency=interstitial_freq,
        cover_treatment=cover_treatment,
        avg_density=avg_density,
        chart_gridlines=chart_style["gridlines"],
        chart_borders=chart_style["borders"],
        chart_accent_protocol=chart_style["accent_protocol"],
        chart_data_labels=chart_style["data_labels"],
        chart_legend_position=chart_style["legend_position"],
        background_requests=background_reqs,
    )

    # Generate backgrounds if n8n available
    if n8n_endpoint and background_reqs:
        _generate_backgrounds(brief, n8n_endpoint)

    log.info("Visual Brief ready (rules): %s + %d backgrounds", brief.template, len(brief.background_paths))
    return brief


# ─────────────────────────────────────────────────────────────────────────────
# Rules-Based Decision Functions (preserved from original VDA)
# ─────────────────────────────────────────────────────────────────────────────


def _determine_register(brief: DesignBrief) -> str:
    """Determine deck register from tone + purpose keywords."""
    purpose_lower = brief.deck_purpose.lower()
    audience_lower = brief.audience_profile.lower()

    if any(k in purpose_lower + audience_lower for k in ("investor", "pitch", "fundraise", "venture", "fund", "vc")):
        return "investor_pitch"

    if any(k in purpose_lower for k in ("brand", "guidelines", "identity", "editorial")):
        return "brand_editorial"

    if any(k in purpose_lower + audience_lower for k in ("executive", "board", "c-suite", "report", "review")):
        return "executive_report"

    if any(k in purpose_lower + audience_lower for k in ("proposal", "consulting", "engagement", "strategy")):
        return "consulting_proposal"

    if any(k in purpose_lower + audience_lower for k in ("technical", "engineering", "architecture", "docs")):
        return "technical_doc"

    return "consulting_proposal"


TEMPLATE_PREFERENCES = {
    "investor_pitch": ["pitch", "dmd_stripe", "investor"],
    "executive_report": ["consulting", "executive", "boardroom"],
    "brand_editorial": ["editorial", "dmd_apple", "dmd_framer"],
    "consulting_proposal": ["consulting", "banking", "boardroom"],
    "technical_doc": ["dmd_vercel", "dmd_cursor", "dmd_warp"],
}


def _select_template(register: str, brand: str) -> str:
    """Select template from register-preferred list."""
    if brand != "minimal":
        return "brand"

    prefs = TEMPLATE_PREFERENCES.get(register, ["brand"])
    return prefs[0] if prefs else "brand"


PALETTES = {
    "investor_pitch": {
        "dominant_bg": "#FFFFFF",
        "secondary_bg": "#1E293B",
        "accent": "#2563EB",
        "text_primary": "#0F172A",
        "text_secondary": "#64748B",
        "divider_bg": "#1E293B",
    },
    "executive_report": {
        "dominant_bg": "#FFFFFF",
        "secondary_bg": "#1F2937",
        "accent": "#1F2937",
        "text_primary": "#111827",
        "text_secondary": "#6B7280",
        "divider_bg": "#1F2937",
    },
    "brand_editorial": {
        "dominant_bg": "#F7F6F2",
        "secondary_bg": "#0A0A0A",
        "accent": "#3D2BE8",
        "text_primary": "#0A0A0A",
        "text_secondary": "#64748B",
        "divider_bg": "#3D2BE8",
    },
    "consulting_proposal": {
        "dominant_bg": "#FFFFFF",
        "secondary_bg": "#1A2332",
        "accent": "#1A2332",
        "text_primary": "#1A2332",
        "text_secondary": "#6B7280",
        "divider_bg": "#1A2332",
    },
    "technical_doc": {
        "dominant_bg": "#FFFFFF",
        "secondary_bg": "#0D1117",
        "accent": "#1F6FEB",
        "text_primary": "#0D1117",
        "text_secondary": "#57606A",
        "divider_bg": "#0D1117",
    },
}


def _select_palette(register: str, brand: str) -> dict[str, str]:
    """Select colour palette from register defaults."""
    return PALETTES.get(register, PALETTES["consulting_proposal"])


IMAGE_TREATMENTS = {
    "investor_pitch": ("abstract_geometric", "cool"),
    "brand_editorial": ("organic_ink", "cool"),
    "executive_report": ("none", "native"),
    "consulting_proposal": ("abstract_geometric", "cool"),
    "technical_doc": ("abstract_geometric", "cool"),
}


def _select_image_treatment(
    register: str, n8n_endpoint: str, deck_outline: list[dict[str, Any]]
) -> tuple[str, str]:
    """Select image treatment style."""
    if not n8n_endpoint:
        return "none", "native"

    style, grade = IMAGE_TREATMENTS.get(register, ("none", "native"))
    return style, grade


def _determine_pacing(
    slide_count: int, brief: DesignBrief
) -> tuple[int, str, str]:
    """Determine pacing: interstitial frequency, cover treatment, average density."""

    if slide_count <= 15:
        interstitial_freq = 999
        cover_treatment = "full_bleed_brand"
    elif slide_count <= 30:
        interstitial_freq = 8
        cover_treatment = "full_bleed_dark"
    else:
        interstitial_freq = 6
        cover_treatment = "full_bleed_dark"

    if "sparse" in brief.visual_strategy.lower() or "narrative" in brief.visual_strategy.lower():
        avg_density = "low"
    elif "dense" in brief.visual_strategy.lower() or "data-heavy" in brief.visual_strategy.lower():
        avg_density = "high"
    else:
        avg_density = "medium"

    return interstitial_freq, cover_treatment, avg_density


def _select_chart_style(register: str) -> dict[str, Any]:
    """Select chart formatting rules."""

    if register in ("consulting_proposal", "executive_report"):
        return {
            "gridlines": False,
            "borders": False,
            "accent_protocol": "one_per_slide",
            "data_labels": True,
            "legend_position": "top",
        }

    if register == "brand_editorial":
        return {
            "gridlines": True,
            "borders": False,
            "accent_protocol": "one_per_slide",
            "data_labels": True,
            "legend_position": "bottom",
        }

    return {
        "gridlines": False,
        "borders": False,
        "accent_protocol": "one_per_slide",
        "data_labels": True,
        "legend_position": "top",
    }


def _generate_background_requests(
    register: str,
    image_style: str,
    palette: dict[str, str],
    deck_outline: list[dict[str, Any]],
    brief: DesignBrief,
) -> list[dict[str, str]]:
    """Generate n8n background image requests for cover + divider slots."""

    reqs = []

    if register == "investor_pitch":
        prompt = (
            f"Generate a 16:9 background for a venture capital pitch deck cover slide. "
            f"Style: geometric abstractions, bold and minimal. "
            f"Colors: dominant blue {palette['accent']} (60%), secondary {palette['secondary_bg']} (20%), white (20%). "
            f"Elements: angular shapes, clean lines, suggesting upward trajectory and growth. "
            f"Composition: leave center-right 40% clear for text overlay. "
            f"No text, pure vector illustration, high contrast."
        )
    elif register == "brand_editorial":
        prompt = (
            f"Generate a 16:9 background for a brand identity/editorial cover slide. "
            f"Style: organic ink-blot forms, inspired by hand-crafted letterpress. "
            f"Colors: indigo {palette['accent']} blot forms (40%), vellum {palette['dominant_bg']} base (60%). "
            f"Elements: 2-3 organic irregular shapes, asymmetric (heavier lower-left), subtle satellite dots. "
            f"Composition: heavier on left side, lighter upper-right, leaves 50% clear for text. "
            f"No text, flat design, organic and artistic."
        )
    elif register == "consulting_proposal":
        prompt = (
            f"Generate a 16:9 background for a consulting proposal/financial deck cover. "
            f"Style: minimalist grid with accent highlights. "
            f"Colors: subtle grid in {palette['text_secondary']} (very light), accent {palette['accent']} lines (10%). "
            f"Elements: Fine grid pattern (nearly invisible), 2-3 accent color bars/lines for visual structure. "
            f"Composition: balanced, professional, suggests precision and structure. "
            f"No text, extremely minimal, corporate premium feel."
        )
    else:
        prompt = (
            f"Generate a 16:9 background for a presentation cover slide. "
            f"Style: clean geometric design. "
            f"Colors: primary {palette['dominant_bg']}, secondary {palette['secondary_bg']}, accent {palette['accent']}. "
            f"Elements: simple geometric shapes, minimal text area reserved. "
            f"No text, high quality, professional."
        )

    reqs.append({"slot": "cover", "prompt": prompt, "style": image_style})

    divider_prompt = (
        f"Generate a 16:9 background for a section divider slide. "
        f"Style: full-bleed solid color with subtle texture or minimal pattern. "
        f"Color: {palette['divider_bg']} dominant. "
        f"Elements: very minimal; mostly solid fill with barely-visible texture or 1-2 accent lines. "
        f"Composition: entire slide, high impact, minimal content. "
        f"No text, texture only."
    )
    reqs.append({"slot": "divider", "prompt": divider_prompt, "style": image_style})

    return reqs


def _generate_backgrounds(brief: VisualBrief, n8n_endpoint: str) -> None:
    """Call n8n to generate background images."""
    import requests

    for req in brief.background_requests:
        slot = req["slot"]
        prompt = req["prompt"]
        try:
            log.info("Generating background for slot '%s' via n8n...", slot)
            resp = requests.post(
                n8n_endpoint,
                json={"prompt": prompt},
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()
            image_path = data.get("image_path") or data.get("file_path", "")
            if image_path:
                brief.background_paths[slot] = image_path
                log.info("  ✓ Background %s: %s", slot, image_path)
            else:
                log.warning("  ✗ n8n returned no image_path for slot %s", slot)
        except Exception as e:
            log.warning("  ✗ Background generation failed for slot %s: %s", slot, e)
