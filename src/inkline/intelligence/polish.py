"""Auto-Polish Pass — deterministic post-processing for slide specs.

Fixes minor quality issues without re-running the LLM. Runs after anti-pattern
detection and scoring, before Typst compilation. Think of it as "auto-format
for slide specs".

Pure Python, no dependencies beyond stdlib + dataclasses + re.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class PolishResult:
    """Result of a polish pass over a deck."""

    slides: list[dict]  # polished slides (mutated in-place, also returned)
    applied: list[dict] = field(default_factory=list)  # [{rule_id, slide_index, description, before, after}]
    advisories: list[str] = field(default_factory=list)  # suggestions not auto-applied


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

# Words to keep lowercase in title case (PL-09)
_TITLE_CASE_SKIP = frozenset({
    "a", "an", "the", "and", "or", "but", "nor", "in", "of", "to", "for",
    "at", "by", "on", "up", "as", "is", "it", "so", "no", "vs",
})


def _title_case(text: str) -> str:
    """Convert text to title case, skipping minor words (except first/last)."""
    words = text.split()
    if not words:
        return text
    result = []
    for i, word in enumerate(words):
        lower = word.lower()
        if i == 0 or i == len(words) - 1 or lower not in _TITLE_CASE_SKIP:
            result.append(word[0].upper() + word[1:].lower() if len(word) > 1 else word.upper())
        else:
            result.append(lower)
    return " ".join(result)


def _is_all_caps(text: str) -> bool:
    """Check if text is ALL CAPS (has at least 2 alpha chars, all uppercase)."""
    alpha = [c for c in text if c.isalpha()]
    return len(alpha) >= 2 and all(c.isupper() for c in alpha)


def _smart_truncate(title: str, max_len: int = 50) -> str:
    """Smart truncation: remove articles/filler, then truncate at word boundary."""
    # First try removing filler words (never remove the first word)
    filler = {"the", "a", "an", "our", "this", "that", "these", "those",
              "very", "really", "basically", "essentially", "actually"}
    words = title.split()
    if len(title) > max_len:
        shortened = [w for i, w in enumerate(words) if i == 0 or w.lower() not in filler]
        candidate = " ".join(shortened)
        if len(candidate) <= max_len:
            return candidate
        words = shortened

    # Abbreviate common long words
    abbrevs = {
        "performance": "Perf.",
        "indicators": "Ind.",
        "dashboard": "Dash.",
        "management": "Mgmt.",
        "development": "Dev.",
        "information": "Info.",
        "technology": "Tech.",
        "organization": "Org.",
        "international": "Intl.",
        "approximately": "Approx.",
    }
    abbreviated = []
    for w in words:
        abbreviated.append(abbrevs.get(w.lower(), w))
    candidate = " ".join(abbreviated)
    if len(candidate) <= max_len:
        return candidate

    # Hard truncate at word boundary + "..."
    if len(candidate) > max_len:
        truncated = candidate[: max_len - 3].rsplit(" ", 1)[0]
        return truncated + "..."
    return candidate


def _normalise_number(raw: str) -> str:
    """Normalise large numbers: $4,200,000 -> $4.2M, 15000 -> 15K, etc."""
    # Extract prefix (currency symbol), digits, and suffix
    m = re.match(r'^([£$€¥]?)[\s]*([\d,]+(?:\.\d+)?)\s*(%?)$', raw.strip())
    if not m:
        return raw
    prefix = m.group(1)
    num_str = m.group(2).replace(",", "")
    suffix = m.group(3)
    if suffix == "%":
        return raw  # Don't normalise percentages

    try:
        num = float(num_str)
    except ValueError:
        return raw

    if num >= 1_000_000_000:
        formatted = f"{num / 1_000_000_000:.1f}".rstrip("0").rstrip(".")
        return f"{prefix}{formatted}B"
    elif num >= 1_000_000:
        formatted = f"{num / 1_000_000:.1f}".rstrip("0").rstrip(".")
        return f"{prefix}{formatted}M"
    elif num >= 10_000:
        formatted = f"{num / 1_000:.1f}".rstrip("0").rstrip(".")
        return f"{prefix}{formatted}K"
    return raw


def _strip_trailing_period(text: str) -> str:
    """Remove trailing period from text (but not ellipsis or other punctuation)."""
    if text.endswith(".") and not text.endswith(".."):
        return text[:-1]
    return text


# ---------------------------------------------------------------------------
# Individual polish rules
# ---------------------------------------------------------------------------

def _pl01_trim_long_titles(slide: dict, idx: int, brand: Optional[dict]) -> list[dict]:
    """PL-01: Trim long titles. 46-60 chars: smart truncation. >60: hard truncate."""
    applied = []
    data = slide.get("data", {})
    title = data.get("title", "")
    if not title or len(title) <= 45:
        return applied

    before = title
    if len(title) > 60:
        # Hard truncate at word boundary
        new_title = title[:47].rsplit(" ", 1)[0] + "..."
    else:
        # Smart truncation (46-60 chars)
        new_title = _smart_truncate(title, 50)

    if new_title != before:
        data["title"] = new_title
        applied.append({
            "rule_id": "PL-01",
            "slide_index": idx,
            "description": f"Trimmed title from {len(before)} to {len(new_title)} chars",
            "before": before,
            "after": new_title,
        })
    return applied


_CHART_CONTEXT_TYPES = frozenset({"chart", "chart_caption", "dashboard", "multi_chart"})


def _pl02_trim_verbose_bullets(slide: dict, idx: int, brand: Optional[dict]) -> list[dict]:
    """PL-02: Trim verbose bullets. Items >100 chars: keep first sentence.

    For chart-context slides (chart_caption, dashboard, chart, multi_chart):
    further trim to ≤8 words (fragment style) and strip trailing punctuation.
    """
    applied = []
    data = slide.get("data", {})
    items = data.get("items", [])
    is_chart_context = slide.get("slide_type") in _CHART_CONTEXT_TYPES

    for i, item in enumerate(items):
        if not isinstance(item, str):
            continue
        original = item
        changed = False

        if len(item) > 100:
            # Split at sentence boundary
            sentences = re.split(r'(?<=[.!?])\s+', item)
            if len(sentences) > 1:
                item = sentences[0]
            else:
                item = item[:97].rsplit(" ", 1)[0] + "..."
            changed = True

        if is_chart_context:
            # Trim to ≤8 words (label/fragment style)
            words = item.split()
            if len(words) > 8:
                item = " ".join(words[:8])
                changed = True
            # Strip trailing punctuation
            stripped = item.rstrip(".,;:!?")
            if stripped != item:
                item = stripped
                changed = True

        if changed and item != original:
            items[i] = item
            applied.append({
                "rule_id": "PL-02",
                "slide_index": idx,
                "description": f"Trimmed bullet {i} from {len(original)} to {len(item)} chars",
                "before": original,
                "after": item,
            })
    return applied


def _pl03_balance_card_heights(slide: dict, idx: int, brand: Optional[dict]) -> list[dict]:
    """PL-03: Balance card heights. If one card body is 3x longer than shortest, trim."""
    applied = []
    if slide.get("slide_type") not in ("three_card", "four_card"):
        return applied
    data = slide.get("data", {})
    cards = data.get("cards", [])
    if len(cards) < 2:
        return applied

    lengths = [len(c.get("body", "")) for c in cards]
    min_len = max(min(lengths), 1)  # avoid division by zero

    for i, card in enumerate(cards):
        body = card.get("body", "")
        if len(body) > min_len * 3 and len(body) > 60:
            before = body
            # Trim to ~2x the shortest, at sentence boundary (floor of 40 chars)
            target = max(min_len * 2, 40)
            sentences = re.split(r'(?<=[.!?])\s+', body)
            trimmed = ""
            for s in sentences:
                if len(trimmed) + len(s) + 1 <= target + 20:
                    trimmed = (trimmed + " " + s).strip() if trimmed else s
                else:
                    break
            if not trimmed:
                trimmed = body[:target].rsplit(" ", 1)[0]
            if trimmed != before:
                card["body"] = trimmed
                applied.append({
                    "rule_id": "PL-03",
                    "slide_index": idx,
                    "description": f"Balanced card {i} body from {len(before)} to {len(trimmed)} chars",
                    "before": before,
                    "after": trimmed,
                })
    return applied


def _pl04_remove_empty_cards(slide: dict, idx: int, brand: Optional[dict]) -> list[dict]:
    """PL-04: Remove empty cards. Cards with empty body get body set to title."""
    applied = []
    if slide.get("slide_type") not in ("three_card", "four_card"):
        return applied
    data = slide.get("data", {})
    cards = data.get("cards", [])
    for i, card in enumerate(cards):
        body = card.get("body", "").strip()
        if not body and card.get("title", "").strip():
            before = body
            card["body"] = card["title"]
            applied.append({
                "rule_id": "PL-04",
                "slide_index": idx,
                "description": f"Filled empty card {i} body with its title",
                "before": before,
                "after": card["body"],
            })
    return applied


def _pl05_normalise_stat_values(slide: dict, idx: int, brand: Optional[dict]) -> list[dict]:
    """PL-05: Normalise stat values. $4,200,000 -> $4.2M, 15000 -> 15K."""
    applied = []
    data = slide.get("data", {})

    # Check various stat-holding fields
    stat_fields = []
    for key in ("kpis", "stats"):
        if key in data and isinstance(data[key], list):
            stat_fields.extend(data[key])

    for stat in stat_fields:
        for value_key in ("value",):
            val = stat.get(value_key, "")
            if not isinstance(val, str):
                continue
            new_val = _normalise_number(val)
            if new_val != val:
                before = val
                stat[value_key] = new_val
                applied.append({
                    "rule_id": "PL-05",
                    "slide_index": idx,
                    "description": f"Normalised stat value: {before} -> {new_val}",
                    "before": before,
                    "after": new_val,
                })
    return applied


def _pl06_fix_orphaned_footnotes(slide: dict, idx: int, brand: Optional[dict]) -> list[dict]:
    """PL-06: Fix orphaned footnotes. Body starting with 'Source:' -> move to footnote."""
    applied = []
    data = slide.get("data", {})

    # Check items for "Source: ..." patterns
    items = data.get("items", [])
    source_indices = []
    for i, item in enumerate(items):
        if isinstance(item, str) and re.match(r'^(Source|Note|Ref):\s', item, re.IGNORECASE):
            source_indices.append(i)

    for i in reversed(source_indices):
        source_text = items.pop(i)
        existing_fn = data.get("footnote", "")
        if existing_fn:
            data["footnote"] = f"{existing_fn}; {source_text}"
        else:
            data["footnote"] = source_text
        applied.append({
            "rule_id": "PL-06",
            "slide_index": idx,
            "description": f"Moved orphaned source to footnote field",
            "before": source_text,
            "after": data["footnote"],
        })

    return applied


def _pl07_deduplicate_section_labels(slides: list[dict], idx: int) -> list[dict]:
    """PL-07: Deduplicate section labels on adjacent slides.

    NOTE: This rule operates on the full slide list, not a single slide.
    It's called specially — idx is ignored, we process all slides.
    """
    applied = []
    prev_section = None
    for i, slide in enumerate(slides):
        data = slide.get("data", {})
        section = data.get("section", "")
        if section and section == prev_section:
            before = section
            data["section"] = ""
            applied.append({
                "rule_id": "PL-07",
                "slide_index": i,
                "description": f"Cleared duplicate section label '{before}'",
                "before": before,
                "after": "",
            })
        if section:
            prev_section = section
    return applied


def _pl08_chart_accent_inference(slide: dict, idx: int, brand: Optional[dict]) -> list[dict]:
    """PL-08: Chart accent inference. Missing accent_index -> infer from highest value."""
    applied = []
    data = slide.get("data", {})
    chart_req = data.get("chart_request", {})
    if not chart_req:
        return applied

    # Only apply if accent_index is missing
    if "accent_index" in chart_req:
        return applied

    chart_data = chart_req.get("chart_data", {})
    series = chart_data.get("series", [])

    # For bar-type charts, find the highest value index
    chart_type = chart_req.get("chart_type", "")
    if chart_type in ("bar_chart", "grouped_bar", "stacked_bar", "horizontal_stacked_bar"):
        if series:
            # Use first series to find max value index
            values = series[0].get("values", [])
            if values:
                max_idx = max(range(len(values)), key=lambda i: values[i] if isinstance(values[i], (int, float)) else 0)
                chart_req["accent_index"] = max_idx
                applied.append({
                    "rule_id": "PL-08",
                    "slide_index": idx,
                    "description": f"Inferred accent_index={max_idx} from highest value",
                    "before": "None",
                    "after": str(max_idx),
                })
    elif chart_type in ("donut", "pie"):
        # For pie/donut, accent the largest segment
        values = chart_data.get("values", [])
        if not values and series:
            values = series[0].get("values", [])
        if values:
            max_idx = max(range(len(values)), key=lambda i: values[i] if isinstance(values[i], (int, float)) else 0)
            chart_req["accent_index"] = max_idx
            applied.append({
                "rule_id": "PL-08",
                "slide_index": idx,
                "description": f"Inferred accent_index={max_idx} for {chart_type}",
                "before": "None",
                "after": str(max_idx),
            })
    return applied


def _pl09_sentence_case_titles(slide: dict, idx: int, brand: Optional[dict]) -> list[dict]:
    """PL-09: Sentence-case titles. ALL CAPS -> Title Case. Skip if brand override."""
    applied = []
    data = slide.get("data", {})
    title = data.get("title", "")

    if not title or not _is_all_caps(title):
        return applied

    # Skip if brand has a title_case override
    if brand and brand.get("title_case_override"):
        return applied

    before = title
    new_title = _title_case(title)
    if new_title != before:
        data["title"] = new_title
        applied.append({
            "rule_id": "PL-09",
            "slide_index": idx,
            "description": f"Converted ALL CAPS title to title case",
            "before": before,
            "after": new_title,
        })
    return applied


def _pl10_strip_trailing_periods(slide: dict, idx: int, brand: Optional[dict]) -> list[dict]:
    """PL-10: Strip trailing periods from bullet items, card bodies, and KPI/stat labels."""
    applied = []
    data = slide.get("data", {})

    # Bullet items
    items = data.get("items", [])
    for i, item in enumerate(items):
        if isinstance(item, str) and item.endswith(".") and not item.endswith(".."):
            before = item
            items[i] = item[:-1]
            applied.append({
                "rule_id": "PL-10",
                "slide_index": idx,
                "description": f"Stripped trailing period from bullet {i}",
                "before": before,
                "after": items[i],
            })

    # Card bodies
    cards = data.get("cards", [])
    for i, card in enumerate(cards):
        body = card.get("body", "")
        if body.endswith(".") and not body.endswith(".."):
            before = body
            card["body"] = body[:-1]
            applied.append({
                "rule_id": "PL-10",
                "slide_index": idx,
                "description": f"Stripped trailing period from card {i} body",
                "before": before,
                "after": card["body"],
            })

    # KPI/stat labels
    for key in ("kpis", "stats"):
        stat_list = data.get(key, [])
        if not isinstance(stat_list, list):
            continue
        for i, stat in enumerate(stat_list):
            label = stat.get("label", "")
            if label.endswith(".") and not label.endswith(".."):
                before = label
                stat["label"] = label[:-1]
                applied.append({
                    "rule_id": "PL-10",
                    "slide_index": idx,
                    "description": f"Stripped trailing period from {key}[{i}] label",
                    "before": before,
                    "after": stat["label"],
                })

    return applied


def _pl11_ensure_closing_contact(slide: dict, idx: int, brand: Optional[dict]) -> list[dict]:
    """PL-11: Ensure closing slide has contact info from brand config."""
    applied = []
    if slide.get("slide_type") != "closing":
        return applied
    if not brand:
        return applied

    data = slide.get("data", {})
    brand_contact = brand.get("contact", {})
    if not brand_contact:
        return applied

    for field_name in ("email", "role", "name", "company"):
        current = data.get(field_name, "").strip()
        brand_val = brand_contact.get(field_name, "").strip()
        if not current and brand_val:
            before = current
            data[field_name] = brand_val
            applied.append({
                "rule_id": "PL-11",
                "slide_index": idx,
                "description": f"Filled closing {field_name} from brand config",
                "before": before,
                "after": brand_val,
            })
    return applied


def _pl13_financial_abbreviations(slide: dict, idx: int, brand: Optional[dict]) -> list[dict]:
    """PL-13: Normalise financial abbreviations in titles, bullets, captions, table cells."""
    applied = []
    data = slide.get("data", {})

    def _apply_abbrevs(text: str) -> str:
        """Apply financial abbreviation substitutions."""
        if not text:
            return text

        # Year + suffix patterns (e.g. "2025 Forecast" → "2025F")
        text = re.sub(r'\b(\d{4})\s+Forecast\b', r'\1F', text, flags=re.IGNORECASE)
        text = re.sub(r'\b(\d{4})\s+Actuals?\b', r'\1A', text, flags=re.IGNORECASE)
        text = re.sub(r'\b(\d{4})\s+Budget\b', r'\1B', text, flags=re.IGNORECASE)
        text = re.sub(r'\b(\d{4})\s+Estimate\b', r'\1E', text, flags=re.IGNORECASE)

        # Currency denomination patterns
        text = re.sub(r'\bUSD\s+billion\b', 'USDbn', text, flags=re.IGNORECASE)
        text = re.sub(r'\bUS\$\s+billion\b', 'USDbn', text, flags=re.IGNORECASE)
        text = re.sub(r'\$\s+billion\b', 'USDbn', text, flags=re.IGNORECASE)
        text = re.sub(r'\bUSD\s+million\b', 'USDm', text, flags=re.IGNORECASE)
        text = re.sub(r'\bUS\$\s+million\b', 'USDm', text, flags=re.IGNORECASE)
        text = re.sub(r'\$\s+million\b', 'USDm', text, flags=re.IGNORECASE)
        text = re.sub(r'\bUSD\s+thousand\b', 'USDk', text, flags=re.IGNORECASE)

        # Rate/metric abbreviations
        text = re.sub(r'\bbasis points\b', 'bps', text, flags=re.IGNORECASE)
        text = re.sub(r'\byear[-\s]on[-\s]year\b', 'YoY', text, flags=re.IGNORECASE)
        text = re.sub(r'\bquarter[-\s]on[-\s]quarter\b', 'QoQ', text, flags=re.IGNORECASE)
        text = re.sub(r'\bcompound annual growth rate\b', 'CAGR', text, flags=re.IGNORECASE)
        text = re.sub(
            r'\bearnings before interest,?\s+taxes,?\s+depreciation\s+and\s+amortis[ae]tion\b',
            'EBITDA', text, flags=re.IGNORECASE
        )
        return text

    changes: list[tuple[str, str, str]] = []  # (field_desc, before, after)

    # Slide title
    if "title" in data:
        before = data["title"]
        after = _apply_abbrevs(before)
        if after != before:
            data["title"] = after
            changes.append(("title", before, after))

    # Bullet items (both "items" and "bullets" fields)
    for field_key in ("items", "bullets"):
        item_list = data.get(field_key, [])
        if not isinstance(item_list, list):
            continue
        for i_idx, item in enumerate(item_list):
            if isinstance(item, str):
                after = _apply_abbrevs(item)
                if after != item:
                    item_list[i_idx] = after
                    changes.append((f"{field_key}[{i_idx}]", item, after))

    # Caption
    if "caption" in data:
        before = data["caption"]
        after = _apply_abbrevs(before)
        if after != before:
            data["caption"] = after
            changes.append(("caption", before, after))

    # Table headers and cells
    headers = data.get("headers", [])
    for i_idx, h in enumerate(headers):
        if isinstance(h, str):
            after = _apply_abbrevs(h)
            if after != h:
                headers[i_idx] = after
                changes.append((f"headers[{i_idx}]", h, after))

    rows = data.get("rows", [])
    for r_idx, row in enumerate(rows):
        if isinstance(row, list):
            for c_idx, cell in enumerate(row):
                if isinstance(cell, str):
                    after = _apply_abbrevs(cell)
                    if after != cell:
                        row[c_idx] = after
                        changes.append((f"rows[{r_idx}][{c_idx}]", cell, after))

    # Chart labels (chart_data fields)
    cr = data.get("chart_request", {})
    cd = cr.get("chart_data", {})
    for field_name in ("x", "y_label", "x_label"):
        val = cd.get(field_name)
        if isinstance(val, str):
            after = _apply_abbrevs(val)
            if after != val:
                cd[field_name] = after
                changes.append((f"chart_data.{field_name}", val, after))
        elif isinstance(val, list):
            for i_idx, v in enumerate(val):
                if isinstance(v, str):
                    after = _apply_abbrevs(v)
                    if after != v:
                        val[i_idx] = after
                        changes.append((f"chart_data.{field_name}[{i_idx}]", v, after))

    for change in changes:
        applied.append({
            "rule_id": "PL-13",
            "slide_index": idx,
            "description": f"Financial abbreviation: {change[0]} '{change[1][:40]}' → '{change[2][:40]}'",
            "before": change[1],
            "after": change[2],
        })
    return applied


def _pl12_compact_sparse_tables(slide: dict, idx: int, brand: Optional[dict]) -> list[str]:
    """PL-12: Advisory only. Table with 1-2 columns and <3 rows -> suggest kpi_strip."""
    advisories = []
    if slide.get("slide_type") != "table":
        return advisories

    data = slide.get("data", {})
    headers = data.get("headers", [])
    rows = data.get("rows", [])

    if len(headers) <= 2 and len(rows) < 3:
        advisories.append(
            f"Slide {idx}: Table has only {len(headers)} column(s) and {len(rows)} row(s). "
            f"Consider converting to kpi_strip or icon_stat for better visual impact."
        )
    return advisories


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def polish_deck(slides: list[dict], brand: Any = None) -> PolishResult:
    """Run all polish rules over a deck. Mutates slides in-place AND returns them.

    Args:
        slides: List of slide spec dicts.
        brand: Optional brand config dict (for PL-11 closing contact, PL-09 override).

    Returns:
        PolishResult with polished slides, list of applied fixes, and advisories.
    """
    all_applied: list[dict] = []
    all_advisories: list[str] = []

    # Per-slide rules (order matters: PL-09 before PL-01 so title case runs first)
    per_slide_rules = [
        _pl09_sentence_case_titles,
        _pl13_financial_abbreviations,  # PL-13 before PL-01 so abbrevs run before title trim
        _pl01_trim_long_titles,
        _pl02_trim_verbose_bullets,
        _pl03_balance_card_heights,
        _pl04_remove_empty_cards,
        _pl05_normalise_stat_values,
        _pl06_fix_orphaned_footnotes,
        _pl08_chart_accent_inference,
        _pl10_strip_trailing_periods,
        _pl11_ensure_closing_contact,
    ]

    for idx, slide in enumerate(slides):
        for rule_fn in per_slide_rules:
            all_applied.extend(rule_fn(slide, idx, brand))

        # PL-12 is advisory only
        all_advisories.extend(_pl12_compact_sparse_tables(slide, idx, brand))

    # Cross-slide rules
    all_applied.extend(_pl07_deduplicate_section_labels(slides, 0))

    return PolishResult(
        slides=slides,
        applied=all_applied,
        advisories=all_advisories,
    )
