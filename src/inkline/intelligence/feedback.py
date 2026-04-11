"""User feedback capture and implicit change detection.

Captures explicit feedback (user comments on slides) and implicit
feedback (detecting changes between deck versions) to update the
pattern memory.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional

log = logging.getLogger(__name__)


def capture_feedback(
    slides: list[dict[str, Any]],
    feedback_items: list[dict[str, Any]],
    brand: str,
) -> list[str]:
    """Store user feedback and update pattern memory.

    Parameters
    ----------
    slides : list[dict]
        The current slide specs.
    feedback_items : list[dict]
        Each item: {"slide": int, "comment": str, "type": str}
        type: "positive" | "negative" | "layout_change" | "content"
    brand : str
        Brand name for pattern storage.

    Returns
    -------
    list[str]
        Pattern IDs created or updated.
    """
    from inkline.intelligence.pattern_memory import (
        add_pattern, record_brand_rule,
    )

    pattern_ids: list[str] = []

    for item in feedback_items:
        slide_idx = item.get("slide", -1)
        comment = item.get("comment", "")
        feedback_type = item.get("type", "content")

        if not comment:
            continue

        if feedback_type == "positive":
            # User liked something — record as a positive pattern
            if 0 <= slide_idx < len(slides):
                slide = slides[slide_idx]
                stype = slide.get("slide_type", "")
                pid = add_pattern(
                    brand, "positive_example",
                    f"User approved {stype} slide: {comment}",
                    confidence=0.85, source="user_positive",
                )
                pattern_ids.append(pid)

        elif feedback_type == "layout_change":
            # User wants a different layout
            pid = add_pattern(
                brand, "layout_preference",
                comment,
                confidence=0.9, source="user_feedback",
            )
            pattern_ids.append(pid)

        elif feedback_type == "negative":
            # User disliked something — record as a rule to avoid
            pid = add_pattern(
                brand, "avoid_pattern",
                f"Avoid: {comment}",
                confidence=0.85, source="user_negative",
            )
            pattern_ids.append(pid)

        else:
            # General brand rule
            pid = record_brand_rule(brand, comment)
            pattern_ids.append(pid)

    if pattern_ids:
        log.info("Captured %d feedback items → %d patterns for brand '%s'",
                 len(feedback_items), len(pattern_ids), brand)

    return pattern_ids


def detect_implicit_feedback(
    previous_slides: list[dict[str, Any]],
    current_slides: list[dict[str, Any]],
    brand: str,
) -> list[dict[str, Any]]:
    """Compare two versions of the same deck to detect user changes.

    When a user manually modifies slide specs between runs, the delta
    reveals design preferences that should be learned.

    Returns list of detected changes with suggested patterns.
    """
    from inkline.intelligence.pattern_memory import add_pattern

    changes: list[dict[str, Any]] = []

    # Match slides by section name
    prev_by_section: dict[str, dict] = {}
    for s in previous_slides:
        section = s.get("data", {}).get("section", "")
        if section:
            prev_by_section[section] = s

    for s in current_slides:
        section = s.get("data", {}).get("section", "")
        if not section or section not in prev_by_section:
            continue

        prev = prev_by_section[section]
        curr_type = s.get("slide_type", "")
        prev_type = prev.get("slide_type", "")

        # Detect slide type change
        if curr_type != prev_type and curr_type and prev_type:
            change = {
                "section": section,
                "change": "slide_type",
                "from": prev_type,
                "to": curr_type,
            }
            changes.append(change)
            add_pattern(
                brand, "layout_preference",
                f"For '{section}' content, prefer {curr_type} over {prev_type}",
                confidence=0.85, source="implicit_feedback",
            )
            log.info("Implicit feedback: %s → %s for section '%s'",
                     prev_type, curr_type, section)

        # Detect slide_mode change
        curr_mode = s.get("slide_mode", "auto")
        prev_mode = prev.get("slide_mode", "auto")
        if curr_mode != prev_mode:
            changes.append({
                "section": section,
                "change": "slide_mode",
                "from": prev_mode,
                "to": curr_mode,
            })

    return changes


def propose_reworks(
    slides: list[dict[str, Any]],
    suggestions: list,  # AuditWarning objects
    brand: str,
) -> list[dict[str, Any]]:
    """Generate rework proposals from auditor suggestions + pattern memory.

    Combines auditor findings with learned patterns to propose specific
    slide reworks that the user can accept or reject.

    Returns list of proposals, each with:
    - slide_index: which slide to rework
    - reason: why
    - proposed_type: suggested new slide type
    - confidence: how confident the system is
    """
    from inkline.intelligence.pattern_memory import get_applicable_patterns

    patterns = get_applicable_patterns(brand)
    proposals: list[dict] = []

    # Build pattern lookup by category
    layout_prefs = [p for p in patterns if p.get("category") == "layout_preference"]

    for suggestion in suggestions:
        msg = getattr(suggestion, "message", str(suggestion)).lower()
        slide_idx = getattr(suggestion, "slide_index", -1)

        if slide_idx < 0 or slide_idx >= len(slides):
            continue

        slide = slides[slide_idx]
        curr_type = slide.get("slide_type", "")

        # Check if any learned pattern applies
        for pref in layout_prefs:
            rule = pref.get("rule", "").lower()
            if curr_type in rule and "prefer" in rule:
                # Extract the preferred type from the rule
                # Pattern: "prefer X over Y"
                parts = rule.split("prefer ")
                if len(parts) > 1:
                    preferred = parts[1].split(" over")[0].strip()
                    proposals.append({
                        "slide_index": slide_idx,
                        "reason": pref.get("rule", ""),
                        "proposed_type": preferred,
                        "confidence": pref.get("confidence", 0.5),
                        "pattern_id": pref.get("id"),
                    })
                    break

        # Check auditor suggestion for layout_change
        if "infographic" in msg or "icon_stat" in msg or "feature_grid" in msg:
            # Extract suggested type from message
            for stype in ["icon_stat", "feature_grid", "kpi_strip", "bar_chart",
                          "process_flow", "timeline", "progress_bars"]:
                if stype in msg:
                    proposals.append({
                        "slide_index": slide_idx,
                        "reason": msg[:100],
                        "proposed_type": stype,
                        "confidence": 0.6,
                    })
                    break

    return proposals
