"""Per-brand pattern memory — persists learned design patterns across decks.

Patterns are stored as YAML files at ~/.config/inkline/patterns/{brand}.yaml
and injected into both DesignAdvisor and Visual Auditor prompts so that
learned preferences compound over time.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

log = logging.getLogger(__name__)

_PATTERNS_DIR: Optional[Path] = None


def _get_patterns_dir() -> Path:
    """Return the patterns directory, creating it if needed."""
    global _PATTERNS_DIR
    if _PATTERNS_DIR is None:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        _PATTERNS_DIR = base / "inkline" / "patterns"
        _PATTERNS_DIR.mkdir(parents=True, exist_ok=True)
    return _PATTERNS_DIR


def _load_yaml(path: Path) -> dict:
    """Load a YAML file. Returns empty dict if file doesn't exist."""
    if not path.exists():
        return {}
    try:
        import yaml
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except ImportError:
        # Fallback: basic YAML-like parsing for simple key-value patterns
        import json
        # Try JSON as fallback
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}


def _save_yaml(path: Path, data: dict) -> None:
    """Save data as YAML (or JSON fallback)."""
    try:
        import yaml
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    except ImportError:
        import json
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


# =========================================================================
# Pattern CRUD
# =========================================================================

def load_brand_patterns(brand: str) -> list[dict]:
    """Load all patterns for a brand. Returns empty list if none exist."""
    path = _get_patterns_dir() / f"{brand}.yaml"
    data = _load_yaml(path)
    return data.get("patterns", [])


def save_brand_patterns(brand: str, patterns: list[dict]) -> None:
    """Save patterns for a brand."""
    path = _get_patterns_dir() / f"{brand}.yaml"
    data = {
        "brand": brand,
        "version": _load_yaml(path).get("version", 0) + 1,
        "last_updated": datetime.now().isoformat(),
        "patterns": patterns,
    }
    _save_yaml(path, data)
    log.info("Saved %d patterns for brand '%s'", len(patterns), brand)


def add_pattern(
    brand: str,
    category: str,
    rule: str,
    *,
    confidence: float = 0.5,
    source: str = "auditor_suggestion",
) -> str:
    """Add a new pattern. Returns the pattern ID."""
    patterns = load_brand_patterns(brand)

    # Check for duplicates (same category + similar rule)
    for p in patterns:
        if p.get("category") == category and _similar(p.get("rule", ""), rule):
            # Update existing pattern's confidence
            p["confidence"] = max(p.get("confidence", 0), confidence)
            p["applied_count"] = p.get("applied_count", 0) + 1
            save_brand_patterns(brand, patterns)
            return p["id"]

    # Create new pattern
    pid = f"p{len(patterns) + 1:03d}"
    patterns.append({
        "id": pid,
        "category": category,
        "rule": rule,
        "confidence": confidence,
        "source": source,
        "approved_by_user": False,
        "applied_count": 0,
        "created": datetime.now().isoformat(),
    })
    save_brand_patterns(brand, patterns)
    log.info("Added pattern %s for brand '%s': %s", pid, brand, rule[:60])
    return pid


def update_pattern_confidence(brand: str, pattern_id: str, confidence: float) -> None:
    """Update a pattern's confidence score."""
    patterns = load_brand_patterns(brand)
    for p in patterns:
        if p.get("id") == pattern_id:
            p["confidence"] = confidence
            save_brand_patterns(brand, patterns)
            return


def approve_pattern(brand: str, pattern_id: str) -> None:
    """Mark a pattern as user-approved (bumps confidence to 0.85)."""
    patterns = load_brand_patterns(brand)
    for p in patterns:
        if p.get("id") == pattern_id:
            p["approved_by_user"] = True
            p["confidence"] = max(p.get("confidence", 0), 0.85)
            save_brand_patterns(brand, patterns)
            return


def reject_pattern(brand: str, pattern_id: str) -> None:
    """Mark a pattern as rejected (confidence set to 0, won't be applied)."""
    patterns = load_brand_patterns(brand)
    for p in patterns:
        if p.get("id") == pattern_id:
            p["confidence"] = 0.0
            p["rejected"] = True
            save_brand_patterns(brand, patterns)
            return


def increment_applied(brand: str, pattern_id: str) -> None:
    """Increment a pattern's applied count. Auto-promotes at 3+ applications."""
    patterns = load_brand_patterns(brand)
    for p in patterns:
        if p.get("id") == pattern_id:
            p["applied_count"] = p.get("applied_count", 0) + 1
            # Auto-promote: 3+ successful applications → high confidence
            if p["applied_count"] >= 3 and p.get("confidence", 0) < 0.95:
                p["confidence"] = 0.95
            save_brand_patterns(brand, patterns)
            return


# =========================================================================
# Pattern filtering and prompt injection
# =========================================================================

def get_applicable_patterns(brand: str, min_confidence: float = 0.3) -> list[dict]:
    """Get patterns above the minimum confidence threshold (not rejected)."""
    patterns = load_brand_patterns(brand)
    return [
        p for p in patterns
        if p.get("confidence", 0) >= min_confidence
        and not p.get("rejected", False)
    ]


def get_auto_apply_patterns(brand: str) -> list[dict]:
    """Get patterns with confidence >= 0.8 (auto-apply without asking)."""
    return [p for p in get_applicable_patterns(brand) if p.get("confidence", 0) >= 0.8]


def format_patterns_for_prompt(brand: str) -> str:
    """Format applicable patterns as text for injection into LLM prompts."""
    patterns = get_applicable_patterns(brand)
    if not patterns:
        return ""

    lines = [
        "=" * 60,
        "LEARNED PATTERNS FOR THIS BRAND",
        "=" * 60,
        "",
        "These patterns have been learned from previous decks and user feedback.",
        "Apply them unless the current context specifically conflicts.",
        "",
    ]

    for p in patterns:
        conf = p.get("confidence", 0)
        status = "AUTO-APPLY" if conf >= 0.8 else "SUGGESTED"
        lines.append(f"- [{status}] {p['rule']} (confidence: {conf:.0%})")

    return "\n".join(lines)


# =========================================================================
# Record patterns from auditor dialogue
# =========================================================================

def record_accepted_redesign(
    brand: str,
    original_type: str,
    new_type: str,
    reason: str,
) -> str:
    """Record when DesignAdvisor accepts an Auditor's redesign proposal."""
    rule = f"Prefer {new_type} over {original_type}: {reason}"
    return add_pattern(
        brand, "layout_preference", rule,
        confidence=0.5, source="auditor_accepted",
    )


def record_brand_rule(brand: str, rule: str) -> str:
    """Record a brand-specific design rule from user correction."""
    return add_pattern(
        brand, "brand_rule", rule,
        confidence=1.0, source="user_correction",
    )


# =========================================================================
# New API functions (P6.4) — slide-type approval tracking
# =========================================================================

def record_pattern(
    brand: str,
    slide_type: str,
    section_type: str,
    approved: bool = True,
) -> None:
    """Record a slide type usage for a given brand + section type.

    Appends to per-brand YAML at ~/.config/inkline/patterns/{brand}.yaml.
    Aggregates: if the (slide_type, section_type) combo exists, increments count.
    If approved is False, records a rejection that lowers approval rate.

    Args:
        brand: Brand name (e.g., "minimal").
        slide_type: The slide type used (e.g., "icon_stat").
        section_type: The section category (e.g., "financials", "executive_summary").
        approved: True if accepted by user / passed audit; False if rejected.
    """
    path = _get_patterns_dir() / f"{brand}.yaml"
    data = _load_yaml(path)
    patterns = data.get("patterns", [])

    # Find existing entry for this combo
    for p in patterns:
        if p.get("section_type") == section_type and p.get("slide_type") == slide_type:
            p["count"] = p.get("count", 0) + 1
            approvals = p.get("approvals", 0)
            if approved:
                p["approvals"] = approvals + 1
            p["approval_rate"] = p["approvals"] / p["count"]
            p["timestamp"] = datetime.now().strftime("%Y-%m-%d")
            _save_yaml(path, {"brand": brand, "patterns": patterns})
            return

    # New entry
    patterns.append({
        "section_type": section_type,
        "slide_type": slide_type,
        "approved": approved,
        "count": 1,
        "approvals": 1 if approved else 0,
        "approval_rate": 1.0 if approved else 0.0,
        "timestamp": datetime.now().strftime("%Y-%m-%d"),
    })
    _save_yaml(path, {"brand": brand, "patterns": patterns})
    log.info("record_pattern: brand=%s section=%s type=%s approved=%s",
             brand, section_type, slide_type, approved)


def get_preferred_types(brand: str, section_type: str) -> list[str]:
    """Return slide types ordered by approval rate for brand + section_type.

    Tries the SQLite learning store first (richer, includes DM rule dimension).
    Falls back to the YAML-backed implementation if the store is unavailable
    or returns fewer than 2 results.

    Only includes slide types with at least 2 observations. Returns an empty
    list if no data is available.

    Args:
        brand: Brand name.
        section_type: Section category to look up.

    Returns:
        List of slide type strings, highest approval rate first.
    """
    # Try SQLite store first
    try:
        import inkline.learning.store as _learning_store_mod
        store = _learning_store_mod.get_store()
        sqlite_prefs = store.get_section_type_preferences(brand, section_type)
        if sqlite_prefs:
            return sqlite_prefs
    except Exception:
        pass

    # Fallback: YAML-backed implementation
    path = _get_patterns_dir() / f"{brand}.yaml"
    data = _load_yaml(path)
    patterns = data.get("patterns", [])

    candidates = [
        p for p in patterns
        if p.get("section_type") == section_type and p.get("count", 0) >= 2
    ]
    candidates.sort(key=lambda p: p.get("approval_rate", 0.0), reverse=True)
    return [p["slide_type"] for p in candidates]


def get_pattern_summary(brand: str) -> dict:
    """Return a summary of all recorded patterns for a brand.

    Returns a dict with structure:
    {
        "brand": str,
        "total_patterns": int,
        "by_section": {section_type: [{slide_type, count, approval_rate}]},
    }

    Args:
        brand: Brand name.

    Returns:
        Dict with pattern summary, or an empty summary if no data.
    """
    path = _get_patterns_dir() / f"{brand}.yaml"
    data = _load_yaml(path)
    patterns = data.get("patterns", [])

    by_section: dict[str, list] = {}
    for p in patterns:
        section = p.get("section_type", "unknown")
        by_section.setdefault(section, [])
        by_section[section].append({
            "slide_type": p.get("slide_type", ""),
            "count": p.get("count", 0),
            "approval_rate": p.get("approval_rate", 0.0),
        })

    # Sort each section's entries by approval rate desc
    for entries in by_section.values():
        entries.sort(key=lambda x: x["approval_rate"], reverse=True)

    return {
        "brand": brand,
        "total_patterns": len(patterns),
        "by_section": by_section,
    }


# =========================================================================
# Helpers
# =========================================================================

def _similar(a: str, b: str, threshold: float = 0.7) -> bool:
    """Check if two strings are similar enough to be the same pattern."""
    if not a or not b:
        return False
    # Simple word overlap similarity
    words_a = set(a.lower().split())
    words_b = set(b.lower().split())
    if not words_a or not words_b:
        return False
    overlap = len(words_a & words_b)
    return overlap / max(len(words_a), len(words_b)) >= threshold
