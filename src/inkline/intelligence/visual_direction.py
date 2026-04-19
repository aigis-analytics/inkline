"""Visual Direction Agent — generates VisualBrief from deck context.

Single responsibility: make 7-level hierarchy of visual decisions (register → template → palette
→ image treatment → pacing → slide types → chart style) and output a typed VisualBrief
that constrains all downstream design decisions.

No LLM calls — all rules-based for speed and determinism.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from inkline.intelligence.design_brief import DesignBrief
from inkline.intelligence.visual_brief import VisualBrief

log = logging.getLogger(__name__)


def generate_visual_brief(
    deck_outline: list[dict[str, Any]],
    design_brief: DesignBrief,
    brand: str,
    n8n_endpoint: str = "",
) -> VisualBrief:
    """Generate visual direction for a deck.

    Args:
        deck_outline: Slide plan from DesignAdvisor Phase 1 (list of {slide_type, title, notes})
        design_brief: DesignBrief (audience, tone, purpose)
        brand: Brand name ("minimal", etc.)
        n8n_endpoint: Optional n8n webhook URL for background generation

    Returns:
        VisualBrief with all visual decisions locked in
    """
    log.info("Visual Direction Agent: generating brief for %s (audience=%s, tone=%s)",
             design_brief.deck_purpose[:50], design_brief.audience_profile[:30], design_brief.tone)

    # ─────────────────────────────────────────────────────────────────────
    # LEVEL 1: Deck Register (from tone + purpose keywords)
    # ─────────────────────────────────────────────────────────────────────
    register = _determine_register(design_brief)
    log.info("  Level 1 (register): %s", register)

    # ─────────────────────────────────────────────────────────────────────
    # LEVEL 2: Template Selection (from register + brand)
    # ─────────────────────────────────────────────────────────────────────
    template = _select_template(register, brand)
    log.info("  Level 2 (template): %s", template)

    # ─────────────────────────────────────────────────────────────────────
    # LEVEL 3: Palette (from register + brand primary)
    # ─────────────────────────────────────────────────────────────────────
    palette = _select_palette(register, brand)
    log.info("  Level 3 (palette): accent=%s", palette["accent"])

    # ─────────────────────────────────────────────────────────────────────
    # LEVEL 4: Image Treatment (from register + n8n availability + deck outline)
    # ─────────────────────────────────────────────────────────────────────
    image_style, image_color_grade = _select_image_treatment(register, n8n_endpoint, deck_outline)
    log.info("  Level 4 (image): %s (%s)", image_style, image_color_grade)

    # ─────────────────────────────────────────────────────────────────────
    # LEVEL 5: Layout Pacing (from slide count + density distribution)
    # ─────────────────────────────────────────────────────────────────────
    interstitial_freq, cover_treatment, avg_density = _determine_pacing(
        len(deck_outline), design_brief
    )
    log.info("  Level 5 (pacing): interstitial_freq=%d, density=%s", interstitial_freq, avg_density)

    # ─────────────────────────────────────────────────────────────────────
    # LEVEL 6: Chart Style (from register + template)
    # ─────────────────────────────────────────────────────────────────────
    chart_style = _select_chart_style(register)
    log.info("  Level 6 (chart): gridlines=%s, accent_protocol=%s",
             chart_style["gridlines"], chart_style["accent_protocol"])

    # ─────────────────────────────────────────────────────────────────────
    # LEVEL 7: Background Image Requests (for n8n generation)
    # ─────────────────────────────────────────────────────────────────────
    background_reqs = []
    if n8n_endpoint and image_style != "none":
        background_reqs = _generate_background_requests(
            register, image_style, palette, deck_outline, design_brief
        )
        log.info("  Level 7 (backgrounds): %d image requests queued", len(background_reqs))

    # ─────────────────────────────────────────────────────────────────────
    # Build VisualBrief
    # ─────────────────────────────────────────────────────────────────────
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

    log.info("Visual Brief ready: %s + %d backgrounds", brief.template, len(brief.background_paths))
    return brief


# ─────────────────────────────────────────────────────────────────────────────
# LEVEL 1: Deck Register Determination
# ─────────────────────────────────────────────────────────────────────────────

def _determine_register(brief: DesignBrief) -> str:
    """Determine deck register from tone + purpose keywords."""
    purpose_lower = brief.deck_purpose.lower()
    audience_lower = brief.audience_profile.lower()

    # Investor / pitch context
    if any(k in purpose_lower + audience_lower for k in ("investor", "pitch", "fundraise", "venture", "fund", "vc")):
        return "investor_pitch"

    # Brand / editorial context
    if any(k in purpose_lower for k in ("brand", "guidelines", "identity", "editorial")):
        return "brand_editorial"

    # Executive / report context
    if any(k in purpose_lower + audience_lower for k in ("executive", "board", "c-suite", "report", "review")):
        return "executive_report"

    # Consulting / proposal context
    if any(k in purpose_lower + audience_lower for k in ("proposal", "consulting", "engagement", "strategy")):
        return "consulting_proposal"

    # Technical / documentation
    if any(k in purpose_lower + audience_lower for k in ("technical", "engineering", "architecture", "docs")):
        return "technical_doc"

    return "consulting_proposal"  # default


# ─────────────────────────────────────────────────────────────────────────────
# LEVEL 2: Template Selection
# ─────────────────────────────────────────────────────────────────────────────

TEMPLATE_PREFERENCES = {
    "investor_pitch": ["pitch", "dmd_stripe", "investor"],
    "executive_report": ["consulting", "executive", "boardroom"],
    "brand_editorial": ["editorial", "dmd_apple", "dmd_framer"],
    "consulting_proposal": ["consulting", "banking", "boardroom"],
    "technical_doc": ["dmd_vercel", "dmd_cursor", "dmd_warp"],
}


def _select_template(register: str, brand: str) -> str:
    """Select template from register-preferred list.

    If brand is 'minimal', use preferred list. If branded client, defer to 'brand' template
    to respect their color palette.
    """
    if brand != "minimal":
        return "brand"  # Respect client's brand colors

    prefs = TEMPLATE_PREFERENCES.get(register, ["brand"])
    return prefs[0] if prefs else "brand"


# ─────────────────────────────────────────────────────────────────────────────
# LEVEL 3: Palette Selection
# ─────────────────────────────────────────────────────────────────────────────

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
    # For branded clients, preserve their primary color but apply to accent
    if brand != "minimal":
        # This would be overridden by the brand's own palette at render time
        # Just return a safe default
        return PALETTES.get(register, PALETTES["consulting_proposal"])

    return PALETTES.get(register, PALETTES["consulting_proposal"])


# ─────────────────────────────────────────────────────────────────────────────
# LEVEL 4: Image Treatment Selection
# ─────────────────────────────────────────────────────────────────────────────

IMAGE_TREATMENTS = {
    "investor_pitch": ("abstract_geometric", "cool"),
    "brand_editorial": ("organic_ink", "cool"),
    "executive_report": ("none", "native"),
    "consulting_proposal": ("abstract_geometric", "cool"),
    "technical_doc": ("abstract_geometric", "cool"),
}


def _select_image_treatment(
    register: str,
    n8n_endpoint: str,
    deck_outline: list[dict[str, Any]],
) -> tuple[str, str]:
    """Select image treatment style.

    If no n8n endpoint, fall back to 'none' (no background images).
    """
    if not n8n_endpoint:
        return "none", "native"

    style, grade = IMAGE_TREATMENTS.get(register, ("none", "native"))
    return style, grade


# ─────────────────────────────────────────────────────────────────────────────
# LEVEL 5: Layout Pacing
# ─────────────────────────────────────────────────────────────────────────────

def _determine_pacing(
    slide_count: int,
    brief: DesignBrief,
) -> tuple[int, str, str]:
    """Determine pacing: interstitial frequency, cover treatment, average density."""

    # Interstitial frequency: how often to insert dividers
    if slide_count <= 15:
        interstitial_freq = 999  # no dividers for short decks
        cover_treatment = "full_bleed_brand"
    elif slide_count <= 30:
        interstitial_freq = 8
        cover_treatment = "full_bleed_dark"
    else:
        interstitial_freq = 6
        cover_treatment = "full_bleed_dark"

    # Average density: from brief.visual_strategy
    if "sparse" in brief.visual_strategy.lower() or "narrative" in brief.visual_strategy.lower():
        avg_density = "low"
    elif "dense" in brief.visual_strategy.lower() or "data-heavy" in brief.visual_strategy.lower():
        avg_density = "high"
    else:
        avg_density = "medium"

    return interstitial_freq, cover_treatment, avg_density


# ─────────────────────────────────────────────────────────────────────────────
# LEVEL 6: Chart Style
# ─────────────────────────────────────────────────────────────────────────────

def _select_chart_style(register: str) -> dict[str, Any]:
    """Select chart formatting rules (gridlines, borders, accent protocol)."""

    # Financial/consulting: minimal, clean charts
    if register in ("consulting_proposal", "executive_report"):
        return {
            "gridlines": False,
            "borders": False,
            "accent_protocol": "one_per_slide",
            "data_labels": True,
            "legend_position": "top",
        }

    # Brand/editorial: can be more decorative
    if register == "brand_editorial":
        return {
            "gridlines": True,
            "borders": False,
            "accent_protocol": "one_per_slide",
            "data_labels": True,
            "legend_position": "bottom",
        }

    # Investor/technical: clean, high contrast
    return {
        "gridlines": False,
        "borders": False,
        "accent_protocol": "one_per_slide",
        "data_labels": True,
        "legend_position": "top",
    }


# ─────────────────────────────────────────────────────────────────────────────
# LEVEL 7: Background Image Requests
# ─────────────────────────────────────────────────────────────────────────────

def _generate_background_requests(
    register: str,
    image_style: str,
    palette: dict[str, str],
    deck_outline: list[dict[str, Any]],
    brief: DesignBrief,
) -> list[dict[str, str]]:
    """Generate n8n background image requests for cover + divider slots."""

    reqs = []

    # Cover slide background
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
            f"Elements: Fine grid pattern (nearly invisible), 2-3 accent accent color bars/lines for visual structure. "
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

    # Section divider background
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


# ─────────────────────────────────────────────────────────────────────────────
# n8n Background Generation
# ─────────────────────────────────────────────────────────────────────────────

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
            image_path = data.get("image_path", "")
            if image_path:
                brief.background_paths[slot] = image_path
                log.info("  ✓ Background %s: %s", slot, image_path)
            else:
                log.warning("  ✗ n8n returned no image_path for slot %s", slot)
        except Exception as e:
            log.warning("  ✗ Background generation failed for slot %s: %s", slot, e)
