"""Closed-loop slide fixer — auto-corrects slides until quality gates pass.

This module provides:
- Pre-render validation and auto-fix (content capacity, text length, card heights)
- Overflow slide identification (which slides caused page overflow)
- Graduated overflow fixes (content reduction → spacing tweaks → slide splitting)
- LLM visual audit response fixes (clipped → reduce, overlap → space, etc.)
- Chart audit (fit, brand colours, factual grounding)
"""

from __future__ import annotations

import logging
import math
import re
from pathlib import Path
from typing import Any, Optional

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Content field mappings (which fields to check per slide type)
# ---------------------------------------------------------------------------

_CONTENT_FIELDS: dict[str, list[str]] = {
    "content": ["items"],
    "table": ["rows"],
    "three_card": ["cards"],
    "four_card": ["cards"],
    "bar_chart": ["bars"],
    "kpi_strip": ["kpis"],
    "timeline": ["milestones"],
    "process_flow": ["steps"],
    "progress_bars": ["bars"],
    "pyramid": ["tiers"],
    "icon_stat": ["stats"],
    "feature_grid": ["features"],
    "dashboard": ["bullets"],
    "chart_caption": ["bullets"],
    "split": ["left_items", "right_items"],
    "comparison": ["left.items", "right.items"],
}

# Import capacity limits
try:
    from inkline.intelligence.layout_selector import SLIDE_CAPACITY
except ImportError:
    SLIDE_CAPACITY: dict[str, int] = {
        "content": 6, "table": 10, "bar_chart": 8, "three_card": 3,
        "four_card": 4, "stat": 4, "kpi_strip": 5, "split": 6,
        "timeline": 6, "process_flow": 4, "progress_bars": 6,
        "pyramid": 5, "comparison": 6, "feature_grid": 6,
        "dashboard": 3, "chart_caption": 4,
    }

# Chart container heights (cm) by slide type
CHART_CONTAINER_CM: dict[str, float] = {
    "chart_caption": 6.5,
    "dashboard": 6.5,
    "chart": 8.5,
}

# Max text lengths — must stay in sync with SLIDE_TYPE_GUIDE hard caps
MAX_TITLE_CHARS = 45    # titles >45 chars risk wrapping to 2 lines (Source Sans 3 22pt, 22.6cm width)
MAX_BULLET_CHARS = 200
MAX_CELL_CHARS = 50
MAX_CARD_BODY_CHARS = 280  # card body text: adaptive font sizing handles overflow; full prose allowed

# Table hard limits (independent of SLIDE_CAPACITY which may be set higher
# for content-allocation purposes in layout_selector)
TABLE_MAX_ROWS = 6
TABLE_MAX_COLS = 6


# =========================================================================
# 1. PRE-RENDER VALIDATION & AUTO-FIX
# =========================================================================

def validate_and_fix_slides(
    slides: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict]]:
    """Validate slide specs and auto-fix violations.

    Returns (fixed_slides, fix_log) where fix_log documents every change.
    """
    fixes: list[dict] = []

    for i, slide in enumerate(slides):
        # Skip exact-mode slides — user controls these entirely
        if slide.get("slide_mode") == "exact":
            continue

        stype = slide.get("slide_type", "")
        data = slide.get("data", {})
        if not data:
            continue

        # --- Title length ---
        title = data.get("title", "")
        if len(title) > MAX_TITLE_CHARS:
            truncated = _truncate_at_word(title, MAX_TITLE_CHARS, ellipsis=False)
            data["title"] = truncated
            fixes.append({
                "slide": i, "field": "title", "action": "truncated",
                "from": len(title), "to": len(truncated),
            })

        # --- Card body length (three_card, four_card, feature_grid) ---
        # Long card bodies cause overflow because all cards render at the same
        # height and the tallest card determines the container height.
        if stype in ("three_card", "four_card"):
            field = "cards"
            for j, card in enumerate(data.get(field, [])):
                if isinstance(card, dict):
                    body = card.get("body", "")
                    if len(body) > MAX_CARD_BODY_CHARS:
                        card["body"] = _truncate_at_word(body, MAX_CARD_BODY_CHARS)
                        fixes.append({
                            "slide": i, "field": f"{field}[{j}].body",
                            "action": "card_body_truncated",
                            "from": len(body), "to": MAX_CARD_BODY_CHARS,
                        })
        if stype == "feature_grid":
            for j, feat in enumerate(data.get("features", [])):
                if isinstance(feat, dict):
                    body = feat.get("body", "")
                    if len(body) > MAX_CARD_BODY_CHARS:
                        feat["body"] = _truncate_at_word(body, MAX_CARD_BODY_CHARS)
                        fixes.append({
                            "slide": i, "field": f"features[{j}].body",
                            "action": "card_body_truncated",
                            "from": len(body), "to": MAX_CARD_BODY_CHARS,
                        })

        # --- Content capacity ---
        capacity = SLIDE_CAPACITY.get(stype)
        if capacity:
            for field_name in _CONTENT_FIELDS.get(stype, []):
                items = _get_nested(data, field_name)
                if items and isinstance(items, list) and len(items) > capacity:
                    _set_nested(data, field_name, items[:capacity])
                    fixes.append({
                        "slide": i, "field": field_name,
                        "action": "truncated_items",
                        "from": len(items), "to": capacity,
                    })

        # --- Table-specific hard limits (visual cap, independent of SLIDE_CAPACITY) ---
        if stype == "table":
            rows = data.get("rows", [])
            if len(rows) > TABLE_MAX_ROWS:
                data["rows"] = rows[:TABLE_MAX_ROWS]
                fixes.append({
                    "slide": i, "field": "rows",
                    "action": "table_rows_capped",
                    "from": len(rows), "to": TABLE_MAX_ROWS,
                })
            # Enforce column limit on headers + every row
            headers = data.get("headers", [])
            if len(headers) > TABLE_MAX_COLS:
                data["headers"] = headers[:TABLE_MAX_COLS]
                fixes.append({
                    "slide": i, "field": "headers",
                    "action": "table_cols_capped",
                    "from": len(headers), "to": TABLE_MAX_COLS,
                })
                # Trim every row to match
                for j, row in enumerate(data.get("rows", [])):
                    if isinstance(row, (list, tuple)) and len(row) > TABLE_MAX_COLS:
                        data["rows"][j] = list(row)[:TABLE_MAX_COLS]

        # --- Text length per item ---
        for field_name in _CONTENT_FIELDS.get(stype, []):
            items = _get_nested(data, field_name)
            if not items or not isinstance(items, list):
                continue
            for j, item in enumerate(items):
                if isinstance(item, str) and len(item) > MAX_BULLET_CHARS:
                    items[j] = _truncate_at_word(item, MAX_BULLET_CHARS)
                    fixes.append({
                        "slide": i, "field": f"{field_name}[{j}]",
                        "action": "truncated_text",
                    })
                elif isinstance(item, dict):
                    # card-type "body" fields are handled by the card-specific check above
                    _is_card_type = stype in ("three_card", "four_card", "feature_grid")
                    for key in ("body", "desc", "label"):
                        if key == "body" and _is_card_type:
                            continue
                        val = item.get(key, "")
                        if isinstance(val, str) and len(val) > MAX_BULLET_CHARS:
                            item[key] = _truncate_at_word(val, MAX_BULLET_CHARS)
                            fixes.append({
                                "slide": i, "field": f"{field_name}[{j}].{key}",
                                "action": "truncated_text",
                            })

    if fixes:
        log.info("Pre-render fixer applied %d fixes", len(fixes))

    return slides, fixes


def equalise_card_heights(slides: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Pad card body text so all cards in a slide have similar length.

    For three_card, four_card, and feature_grid: find the longest card body,
    pad shorter ones with trailing non-breaking spaces so Typst renders
    them at the same height.
    """
    card_types = {"three_card", "four_card", "feature_grid"}

    for slide in slides:
        stype = slide.get("slide_type", "")
        if stype not in card_types:
            continue

        data = slide.get("data", {})
        field = "cards" if stype in ("three_card", "four_card") else "features"
        items = data.get(field, [])
        if not items:
            continue

        # Find max body length
        max_len = 0
        for item in items:
            body = item.get("body", "")
            max_len = max(max_len, len(body))

        # Pad shorter bodies with non-breaking spaces
        if max_len > 0:
            for item in items:
                body = item.get("body", "")
                if len(body) < max_len:
                    # Pad with regular spaces — Typst will preserve them in block context
                    pad = " " * (max_len - len(body))
                    item["body"] = body + pad

    return slides


# =========================================================================
# 2. OVERFLOW SLIDE IDENTIFICATION
# =========================================================================

def identify_overflow_slides(
    pdf_path: Path,
    slides: list[dict[str, Any]],
    source: str,
) -> list[int]:
    """Determine which slides caused page overflow.

    Returns 0-based slide indices that likely overflowed.
    """
    from inkline.intelligence.overflow_audit import extract_page_texts

    page_texts = extract_page_texts(pdf_path)
    actual_pages = len(page_texts)
    expected_slides = len(slides)

    if actual_pages <= expected_slides:
        return []

    overflow_count = actual_pages - expected_slides

    # Stage A: text matching
    overflowed = _identify_by_text(page_texts, slides)
    if len(overflowed) >= overflow_count:
        return overflowed[:overflow_count]

    # Stage B: heuristic scoring
    return _identify_by_heuristic(slides, overflow_count)


def _identify_by_text(
    page_texts: list[str],
    slides: list[dict[str, Any]],
) -> list[int]:
    """Match slide titles to PDF pages to find which slides span multiple pages."""
    overflowed: list[int] = []

    # Extract expected title for each slide
    slide_titles: list[str] = []
    for s in slides:
        d = s.get("data", {})
        title = d.get("title", d.get("company", "")).upper()[:30]
        slide_titles.append(title)

    # Walk through pages, matching to slides
    slide_idx = 0
    for page_idx in range(len(page_texts)):
        if slide_idx >= len(slide_titles):
            break

        page_upper = page_texts[page_idx].upper()
        title = slide_titles[slide_idx]

        if title and title in page_upper:
            # Check if next page also has this title (overflow)
            if page_idx + 1 < len(page_texts):
                next_upper = page_texts[page_idx + 1].upper()
                # Next page has content from this slide but not next slide's title
                next_title = slide_titles[slide_idx + 1] if slide_idx + 1 < len(slide_titles) else ""
                if next_title and next_title not in next_upper:
                    overflowed.append(slide_idx)

            slide_idx += 1

    return overflowed


def _identify_by_heuristic(
    slides: list[dict[str, Any]],
    overflow_count: int,
) -> list[int]:
    """Score slides by overflow risk and return the top N."""
    # Risk weights by slide type
    type_risk = {
        "dashboard": 1.5, "chart_caption": 1.3, "feature_grid": 1.2,
        "four_card": 1.1, "three_card": 1.1, "table": 1.0,
        "split": 0.9, "content": 0.8, "icon_stat": 0.7,
        "process_flow": 0.6, "timeline": 0.6, "stat": 0.4,
        "title": 0.1, "closing": 0.1,
    }

    scores: list[tuple[int, float]] = []
    for i, s in enumerate(slides):
        stype = s.get("slide_type", "")
        data = s.get("data", {})
        score = type_risk.get(stype, 0.5)

        # Title length risk
        title = data.get("title", "")
        if len(title) > MAX_TITLE_CHARS:
            score += 0.5

        # Content volume risk
        total_chars = sum(
            len(str(v)) for v in _flatten_values(data) if isinstance(v, str)
        )
        score += min(total_chars / 500, 1.0)

        # Capacity utilisation
        capacity = SLIDE_CAPACITY.get(stype, 10)
        for field in _CONTENT_FIELDS.get(stype, []):
            items = _get_nested(data, field)
            if items and isinstance(items, list):
                score += len(items) / capacity * 0.5

        scores.append((i, score))

    scores.sort(key=lambda x: x[1], reverse=True)
    return [idx for idx, _ in scores[:overflow_count]]


# =========================================================================
# 3. GRADUATED OVERFLOW FIXES
# =========================================================================

def apply_graduated_fixes(
    slides: list[dict[str, Any]],
    source: str,
    overflow_indices: list[int],
    attempt: int,
    theme: dict,
) -> tuple[list[dict[str, Any]], str, bool]:
    """Apply escalating fixes to overflowing slides.

    Returns (slides, source, needs_rerender).
    - needs_rerender=True: slides were modified, must regenerate Typst source
    - needs_rerender=False: only source was modified, can recompile directly

    Attempt order (deliberately conservative — never adds slides early):
    1. Content reduction  — trim text, drop footnote, remove last item
    2. Spacing/font       — shrink font size, reduce padding in Typst source
    3. Type downgrade     — replace complex layout with simpler one (no new slides)
    4. Selective split    — ONLY content/table slides with many items get split
    5+ Aggressive combo   — content reduction + type downgrade together
    """
    if attempt == 1:
        # Font/spacing first — non-destructive, preserves all content.
        # Wide tables (many columns) and dense slides often fit after shrinking.
        return _fix_source_spacing(slides, source, overflow_indices)
    elif attempt == 2:
        return _fix_content_reduction(slides, source, overflow_indices)
    elif attempt == 3:
        # Type downgrade before split: converts chart_caption/split/dashboard etc.
        # to a simpler layout WITHOUT adding slides. Always safer than splitting.
        return _fix_type_downgrade(slides, source, overflow_indices)
    elif attempt == 4:
        # Selective split: ONLY content/table slides. Chart/card/split slides
        # overflow due to layout constraints, not item count — splitting them
        # creates two identically-overflowing slides and makes things worse.
        return _fix_slide_splitting(slides, source, overflow_indices)
    elif attempt == 5:
        # Attempt 5: aggressive combo — content reduction + another downgrade pass
        slides, source, changed = _fix_content_reduction(slides, source, overflow_indices)
        slides2, source2, changed2 = _fix_type_downgrade(slides, source, overflow_indices)
        return slides2, source2, changed or changed2
    elif attempt >= 6:
        # Attempt 6+: nuclear — force any remaining overflowing slide to content/split
        # regardless of type. Guarantees convergence; visual quality is secondary here.
        return _fix_nuclear_downgrade(slides, source, overflow_indices)
    else:
        return slides, source, False


def _fix_content_reduction(
    slides: list[dict[str, Any]],
    source: str,
    indices: list[int],
) -> tuple[list[dict[str, Any]], str, bool]:
    """Attempt 1: reduce content on overflowing slides."""
    modified = False
    for idx in indices:
        if idx >= len(slides):
            continue
        slide = slides[idx]
        stype = slide.get("slide_type", "")
        data = slide.get("data", {})

        # Remove footnote
        if "footnote" in data:
            del data["footnote"]
            modified = True

        # Shorten title to hard cap (MAX_TITLE_CHARS)
        title = data.get("title", "")
        if len(title) > MAX_TITLE_CHARS:
            data["title"] = _truncate_at_word(title, MAX_TITLE_CHARS, ellipsis=False)
            modified = True

        # Reduce item count by ~20%
        for field in _CONTENT_FIELDS.get(stype, []):
            items = _get_nested(data, field)
            if items and isinstance(items, list) and len(items) > 2:
                reduced = max(len(items) - max(1, len(items) // 5), 2)
                _set_nested(data, field, items[:reduced])
                modified = True

        # Truncate text to 300 chars (overflow fix — adaptive font sizing handles rest)
        for field in _CONTENT_FIELDS.get(stype, []):
            items = _get_nested(data, field)
            if not items or not isinstance(items, list):
                continue
            for j, item in enumerate(items):
                if isinstance(item, str) and len(item) > 300:
                    items[j] = _truncate_at_word(item, 280)
                    modified = True
                elif isinstance(item, dict):
                    for key in ("body", "desc"):
                        val = item.get(key, "")
                        if isinstance(val, str) and len(val) > 300:
                            item[key] = _truncate_at_word(val, 280)
                            modified = True

    if modified:
        log.info("Overflow fix attempt 1: content reduction on slides %s", indices)
    return slides, source, modified


def _fix_source_spacing(
    slides: list[dict[str, Any]],
    source: str,
    indices: list[int],
) -> tuple[list[dict[str, Any]], str, bool]:
    """Attempt 2: reduce spacing/font in Typst source for overflowing slides."""
    # Split source into per-slide sections
    sections = _split_source_sections(source)

    modified = False
    for idx in indices:
        if idx >= len(sections):
            continue
        start, end = sections[idx]
        slide_src = source[start:end]

        # Reduce spacing
        new_src = re.sub(r'v\(14pt\)', 'v(6pt)', slide_src)
        new_src = re.sub(r'v\(10pt\)', 'v(4pt)', new_src)
        # Reduce body text size (two-step: first pass 12→10→9, second pass 9.5→8)
        new_src = re.sub(r'size: 12pt', 'size: 10pt', new_src)
        new_src = re.sub(r'size: 11pt', 'size: 9.5pt', new_src)
        new_src = re.sub(r'size: 10\.5pt', 'size: 9pt', new_src)
        new_src = re.sub(r'size: 10pt', 'size: 9pt', new_src)
        new_src = re.sub(r'size: 9\.5pt', 'size: 8pt', new_src)
        new_src = re.sub(r'size: 9pt', 'size: 7.5pt', new_src)
        # Reduce card padding
        new_src = re.sub(r'inset: 14pt', 'inset: 10pt', new_src)
        new_src = re.sub(r'inset: 12pt', 'inset: 8pt', new_src)
        new_src = re.sub(r'inset: 10pt', 'inset: 7pt', new_src)
        # Reduce chart height
        new_src = re.sub(r'height: 8\.5cm', 'height: 7cm', new_src)
        new_src = re.sub(r'height: 7\.2cm', 'height: 6cm', new_src)
        new_src = re.sub(r'height: 6\.5cm', 'height: 5.5cm', new_src)

        if new_src != slide_src:
            source = source[:start] + new_src + source[end:]
            modified = True

    if modified:
        log.info("Overflow fix attempt 2: spacing/font reduction on slides %s", indices)
    return slides, source, False  # needs_rerender=False (source modified directly)


def _fix_slide_splitting(
    slides: list[dict[str, Any]],
    source: str,
    indices: list[int],
) -> tuple[list[dict[str, Any]], str, bool]:
    """Attempt 4: split content/table slides that have too many items.

    ONLY applies to ``content`` and ``table`` slide types. All other types
    (chart_caption, split, dashboard, three_card, four_card, comparison, etc.)
    overflow due to layout constraints, not item count. Splitting them creates
    two identically-overflowing slides and causes the total page count to grow.
    Those types must be handled by type downgrade (attempt 3) instead.

    A minimum of 4 items is required before splitting; splitting a slide with
    2-3 items produces degenerate single-item slides.
    """
    # Only these types benefit from content splitting
    _SPLITTABLE_TYPES = {"content", "table"}

    new_slides = list(slides)
    for idx in sorted(indices, reverse=True):
        if idx >= len(new_slides):
            continue
        slide = new_slides[idx]
        stype = slide.get("slide_type", "")

        if stype not in _SPLITTABLE_TYPES:
            log.info(
                "Overflow fix attempt 4: skipping split of slide %d (%s) — "
                "layout type, not content overflow; type downgrade handles this",
                idx, stype,
            )
            continue

        data = slide.get("data", {})
        split_pair = _split_one_slide(stype, data)
        if split_pair:
            a, b = split_pair
            new_slides[idx] = {"slide_type": stype, "data": a}
            new_slides.insert(idx + 1, {"slide_type": stype, "data": b})
            log.info("Overflow fix attempt 4: split slide %d (%s) into two", idx, stype)

    if len(new_slides) != len(slides):
        return new_slides, source, True  # needs_rerender=True
    return slides, source, False


def _split_one_slide(
    stype: str,
    data: dict[str, Any],
) -> Optional[tuple[dict, dict]]:
    """Split a single slide's data into two halves.

    Requires at least 4 items so each half gets at least 2 — splitting a 3-item
    slide into 1+2 produces a degenerate near-empty slide.
    """
    for field in _CONTENT_FIELDS.get(stype, []):
        items = _get_nested(data, field)
        if items and isinstance(items, list) and len(items) >= 4:
            mid = len(items) // 2
            a = dict(data)
            b = dict(data)
            _set_nested(a, field, items[:mid])
            _set_nested(b, field, items[mid:])
            base = _truncate_at_word(data.get("title", ""), MAX_TITLE_CHARS - 8, ellipsis=False)
            b["title"] = base + " (cont.)"
            return a, b
    return None


def _fix_type_downgrade(
    slides: list[dict[str, Any]],
    source: str,
    indices: list[int],
) -> tuple[list[dict[str, Any]], str, bool]:
    """Attempt 4: downgrade complex overflow-prone slide types to simpler ones.

    Complex types that frequently overflow are replaced by simpler equivalents
    that reliably fit on one page regardless of content volume.

    Downgrade map:
      feature_grid  → content (flat bullet list)
      comparison    → split   (two-column with bullets, not header+cards)
      dashboard     → chart_caption (drop stat boxes)
      four_card     → three_card   (remove last card)
      table         → content (if many rows, convert to bullet list)
    """
    # Types ordered by overflow risk (most → least).
    # Each type is downgraded to a simpler equivalent that fits on one page.
    # chart_caption was previously absent — it overflows when chart height + title
    # + bullets exceed the slide content area. Downgrade removes the chart image
    # and converts to a plain split/content layout.
    _DOWNGRADE_MAP = {
        "chart_caption": "split",    # drop chart image; keep title + bullets as two-col
        "dashboard":     "chart_caption",  # drop stat boxes; keep chart + bullets
        "feature_grid":  "content",
        "comparison":    "split",
        "split":         "content",  # split with heavy content → flat list
        "four_card":     "three_card",
        "three_card":    "content",  # if three_card still overflows → list
        "table":         "content",
        "timeline":      "content",  # timeline with many items → list
        "icon_stat":     "kpi_strip",  # icon_stat → compact strip (no desc text)
        "kpi_strip":     "content",  # last resort for kpi_strip overflow
        "progress_bars": "content",
    }
    modified = False
    for idx in indices:
        if idx >= len(slides):
            continue
        slide = slides[idx]
        stype = slide.get("slide_type", "")
        target = _DOWNGRADE_MAP.get(stype)
        if not target:
            continue

        data = dict(slide.get("data", {}))
        new_data: dict[str, Any] = {}

        if stype == "chart_caption" and target == "split":
            # Drop the chart image; preserve title + bullets as a two-column layout.
            # The caption becomes the left column heading; bullets go to the right.
            new_data["title"] = data.get("title", "")
            new_data["section"] = data.get("section", "")
            caption = data.get("caption", "Key findings")
            bullets = data.get("bullets", [])
            new_data["left_title"] = caption or "Analysis"
            new_data["left_items"] = bullets[:3]
            new_data["right_title"] = "Implications"
            new_data["right_items"] = bullets[3:6] if len(bullets) > 3 else []

        elif stype == "icon_stat" and target == "kpi_strip":
            # icon_stat with desc text overflows; kpi_strip is more compact.
            new_data["title"] = data.get("title", "")
            new_data["section"] = data.get("section", "")
            stats = data.get("stats", [])
            kpis = []
            for s in stats[:5]:
                if isinstance(s, dict):
                    kpis.append({
                        "value": s.get("value", ""),
                        "label": s.get("label", ""),
                        "highlight": False,
                    })
            new_data["kpis"] = kpis

        elif stype in ("kpi_strip", "progress_bars") and target == "content":
            new_data["title"] = data.get("title", "")
            new_data["section"] = data.get("section", "")
            items_raw = data.get("kpis", data.get("bars", []))
            items = []
            for item in items_raw[:6]:
                if isinstance(item, dict):
                    label = item.get("label") or item.get("title") or ""
                    value = item.get("value") or item.get("pct", "")
                    items.append(f"{label}: {value}".strip(": ") if value else label)
                else:
                    items.append(str(item))
            new_data["items"] = items

        elif stype == "feature_grid" and target == "content":
            # Convert feature cards to bullet strings
            new_data["title"] = data.get("title", "")
            new_data["section"] = data.get("section", "")
            features = data.get("features", [])
            items = []
            for feat in features:
                if isinstance(feat, dict):
                    label = feat.get("title") or feat.get("label") or ""
                    body = feat.get("body") or feat.get("desc") or ""
                    items.append(f"{label}: {body}".strip(": ") if body else label)
                else:
                    items.append(str(feat))
            new_data["items"] = items[:6]

        elif stype == "comparison" and target == "split":
            new_data["title"] = data.get("title", "")
            new_data["section"] = data.get("section", "")
            left = data.get("left", {})
            right = data.get("right", {})
            left_items = left.get("items", []) if isinstance(left, dict) else []
            right_items = right.get("items", []) if isinstance(right, dict) else []
            new_data["left_title"] = (left.get("title", "Option A") if isinstance(left, dict) else "Option A")
            new_data["right_title"] = (right.get("title", "Option B") if isinstance(right, dict) else "Option B")
            new_data["left_items"] = [
                (i if isinstance(i, str) else i.get("body", str(i))) for i in left_items[:4]
            ]
            new_data["right_items"] = [
                (i if isinstance(i, str) else i.get("body", str(i))) for i in right_items[:4]
            ]

        elif stype == "dashboard" and target == "chart_caption":
            new_data["title"] = data.get("title", "")
            new_data["section"] = data.get("section", "")
            new_data["image_path"] = data.get("image_path", "")
            new_data["chart_request"] = data.get("chart_request")
            new_data["caption"] = data.get("insight", data.get("caption", ""))
            bullets = data.get("bullets", [])
            new_data["bullets"] = bullets[:3]

        elif stype == "four_card" and target == "three_card":
            new_data = dict(data)
            cards = new_data.get("cards", [])
            new_data["cards"] = cards[:3]

        elif stype == "split" and target == "content":
            new_data["title"] = data.get("title", "")
            new_data["section"] = data.get("section", "")
            left_title = data.get("left_title", "")
            right_title = data.get("right_title", "")
            left_items = data.get("left_items", [])
            right_items = data.get("right_items", [])
            items = []
            if left_title:
                items.append(f"{left_title}:")
            items.extend(
                (i if isinstance(i, str) else i.get("body", str(i))) for i in left_items[:3]
            )
            if right_title:
                items.append(f"{right_title}:")
            items.extend(
                (i if isinstance(i, str) else i.get("body", str(i))) for i in right_items[:3]
            )
            new_data["items"] = items[:6]

        elif stype == "three_card" and target == "content":
            new_data["title"] = data.get("title", "")
            new_data["section"] = data.get("section", "")
            cards = data.get("cards", [])
            items = []
            for card in cards:
                if isinstance(card, dict):
                    title = card.get("title") or card.get("label") or ""
                    body = card.get("body") or card.get("desc") or ""
                    items.append(f"{title}: {body}".strip(": ") if body else title)
                else:
                    items.append(str(card))
            new_data["items"] = items[:6]

        elif stype == "timeline" and target == "content":
            new_data["title"] = data.get("title", "")
            new_data["section"] = data.get("section", "")
            field = "milestones"
            items_raw = data.get(field, [])
            items = []
            for item in items_raw[:6]:
                if isinstance(item, dict):
                    label = item.get("label") or item.get("title") or item.get("date") or ""
                    body = item.get("body") or item.get("desc") or item.get("event") or ""
                    items.append(f"{label}: {body}".strip(": ") if body else label)
                else:
                    items.append(str(item))
            new_data["items"] = items

        elif stype == "table" and target == "content":
            new_data["title"] = data.get("title", "")
            new_data["section"] = data.get("section", "")
            headers = data.get("headers", [])
            rows = data.get("rows", [])
            items = []
            for row in rows[:6]:
                if isinstance(row, (list, tuple)) and len(row) > 0:
                    label = str(row[0])
                    rest = " | ".join(str(c) for c in row[1:] if c)
                    items.append(f"{label}: {rest}" if rest else label)
                elif isinstance(row, str):
                    items.append(row)
            new_data["items"] = items

        else:
            # Unhandled downgrade — keep original
            continue

        # Clean up None values
        new_data = {k: v for k, v in new_data.items() if v is not None}

        # Always enforce title cap on downgraded slides
        t = new_data.get("title", "")
        if len(t) > MAX_TITLE_CHARS:
            new_data["title"] = _truncate_at_word(t, MAX_TITLE_CHARS, ellipsis=False)

        slides[idx] = {"slide_type": target, "data": new_data}
        log.info(
            "Overflow fix attempt (type downgrade): slide %d %s → %s",
            idx, stype, target,
        )
        modified = True

    return slides, source, modified


def _fix_nuclear_downgrade(
    slides: list[dict[str, Any]],
    source: str,
    indices: list[int],
) -> tuple[list[dict[str, Any]], str, bool]:
    """Attempt 6+: nuclear — force any remaining overflowing slide to content.

    All graduated fixes (content reduction, spacing, type downgrade, selective
    split) have been exhausted.  Any slide still overflowing here is converted
    directly to a plain ``content`` (bullet) slide regardless of its current
    type.  Visual quality is secondary — the goal is a rendered PDF with the
    right page count.

    The CRITICAL_OVERFLOW note in the next LLM visual audit round will prompt
    the advisor to produce a better redesign of these slides.
    """
    _NUCLEAR_SKIP = {"title", "closing", "content"}  # already at floor; skip

    modified = False
    for idx in indices:
        if idx >= len(slides):
            continue
        slide = slides[idx]
        stype = slide.get("slide_type", "")
        if stype in _NUCLEAR_SKIP:
            continue
        data = slide.get("data", {})

        # Extract the most important text fields as bullet items
        new_data: dict[str, Any] = {
            "title":   data.get("title", ""),
            "section": data.get("section", ""),
        }
        # Collect any list-like fields and flatten to strings
        items: list[str] = []
        for field in ("items", "bullets", "rows", "stats", "kpis", "bars",
                      "cards", "milestones", "steps", "tiers", "features",
                      "left_items", "right_items"):
            raw = data.get(field, [])
            if isinstance(raw, list):
                for item in raw[:6]:
                    if isinstance(item, dict):
                        label = (item.get("label") or item.get("title")
                                 or item.get("value") or "")
                        body  = (item.get("body") or item.get("text")
                                 or item.get("description") or "")
                        items.append(f"{label}: {body}".strip(": ") if body else label)
                    elif isinstance(item, (list, tuple)):
                        items.append(" | ".join(str(c) for c in item if c))
                    else:
                        items.append(str(item))
                break  # first matching field wins

        new_data["items"] = items[:6]

        # Enforce title cap
        t = new_data.get("title", "")
        if len(t) > MAX_TITLE_CHARS:
            new_data["title"] = _truncate_at_word(t, MAX_TITLE_CHARS, ellipsis=False)

        slides[idx] = {"slide_type": "content", "data": new_data}
        log.info(
            "Overflow fix attempt 6 (nuclear): slide %d %s → content (last resort)",
            idx, stype,
        )
        modified = True

    return slides, source, modified


# =========================================================================
# 4. LLM VISUAL AUDIT RESPONSE FIXES
# =========================================================================

# Patterns that map LLM findings to fix actions
_FIX_PATTERNS: list[tuple[list[str], str]] = [
    (["clipped", "cut off", "truncated", "extends beyond"], "reduce_content"),
    (["overflow", "extra page"], "reduce_content"),
    (["overlap", "overlapping", "stacked on top"], "reduce_items"),
    (["illegible", "too small", "hard to read"], "increase_font"),
    (["missing content", "empty", "no content"], "warn_empty"),
    (["equal height", "card height", "misaligned", "inconsistent height"], "equalise_cards"),
]


def fix_from_llm_findings(
    slides: list[dict[str, Any]],
    findings: list,  # list of AuditWarning
) -> tuple[list[dict[str, Any]], list[dict]]:
    """Apply targeted fixes based on LLM visual audit ERROR findings.

    Returns (fixed_slides, applied_fixes). applied_fixes is empty if
    no actionable fixes could be determined.
    """
    applied: list[dict] = []

    for finding in findings:
        msg = finding.message.lower() if hasattr(finding, "message") else str(finding).lower()
        slide_idx = getattr(finding, "slide_index", -1)

        if slide_idx < 0 or slide_idx >= len(slides):
            continue

        action = _match_finding_to_action(msg)
        if not action:
            continue

        slide = slides[slide_idx]
        stype = slide.get("slide_type", "")
        data = slide.get("data", {})

        if action == "reduce_content":
            # Remove footnote + shorten longest text
            data.pop("footnote", None)
            _shorten_longest_field(data, stype)
            applied.append({"slide": slide_idx, "action": action, "finding": msg[:60]})

        elif action == "reduce_items":
            # Remove one item from each content field
            for field in _CONTENT_FIELDS.get(stype, []):
                items = _get_nested(data, field)
                if items and isinstance(items, list) and len(items) > 2:
                    _set_nested(data, field, items[:-1])
                    applied.append({"slide": slide_idx, "action": action, "field": field})

        elif action == "equalise_cards":
            slides = equalise_card_heights(slides)
            applied.append({"slide": slide_idx, "action": action})

        # "increase_font" and "warn_empty" are logged but not auto-fixed
        # (they require source-level changes or are genuinely empty)

    if applied:
        log.info("LLM finding fixer applied %d fixes", len(applied))
    return slides, applied


def _match_finding_to_action(msg: str) -> Optional[str]:
    """Match an LLM finding message to a fix action."""
    for keywords, action in _FIX_PATTERNS:
        if any(kw in msg for kw in keywords):
            return action
    return None


# =========================================================================
# 5. CHART AUDIT
# =========================================================================

def audit_charts(
    slides: list[dict[str, Any]],
    root: str,
    brand_name: str,
    source_sections: Optional[list[dict]] = None,
) -> list[dict]:
    """Audit all chart images and auto-fix where possible.

    Returns list of warnings/fixes applied.
    """
    warnings: list[dict] = []

    try:
        from inkline.brands import get_brand
        brand = get_brand(brand_name)
    except Exception:
        return warnings

    for i, slide in enumerate(slides):
        data = slide.get("data", {})
        image_path = data.get("image_path")
        if not image_path:
            continue

        stype = slide.get("slide_type", "")
        full_path = Path(root) / image_path

        if not full_path.exists():
            continue

        # --- Size/fit check ---
        container_cm = CHART_CONTAINER_CM.get(stype, 8.5)
        fit_warnings = _audit_chart_fit(full_path, container_cm, image_path)
        if fit_warnings:
            # Auto-fix: re-render at correct size
            chart_req = data.get("chart_request")
            if chart_req:
                try:
                    from inkline.typst.chart_renderer import render_chart_for_brand
                    target_h = container_cm / 2.54  # cm to inches
                    target_w = target_h * 1.6  # landscape aspect ratio
                    render_chart_for_brand(
                        chart_req["chart_type"],
                        chart_req["chart_data"],
                        str(full_path),
                        brand_name=brand_name,
                        width=target_w,
                        height=target_h,
                    )
                    warnings.append({
                        "slide": i, "action": "chart_resized",
                        "image": image_path,
                        "new_height_cm": container_cm * 0.9,
                    })
                except Exception as e:
                    log.warning("Chart resize failed for %s: %s", image_path, e)

        # --- Brand colour check ---
        brand_warnings = _audit_chart_brand(full_path, brand)
        warnings.extend(brand_warnings)

        # --- Factual data check ---
        if source_sections:
            section_data = source_sections[i] if i < len(source_sections) else None
            if section_data:
                chart_req = data.get("chart_request", {})
                chart_data = chart_req.get("chart_data", {})
                if chart_data and not chart_data.get("illustrative"):
                    data_warnings = _audit_chart_data(chart_data, section_data)
                    warnings.extend(data_warnings)

    return warnings


def _audit_chart_fit(
    image_path: Path,
    container_cm: float,
    image_name: str,
) -> list[dict]:
    """Check if chart image fits within the slide container."""
    warnings = []
    try:
        from PIL import Image
        img = Image.open(str(image_path))
        w, h = img.size
        # Assume 150 DPI rendering
        height_cm = h / 150 * 2.54
        if height_cm > container_cm * 1.1:
            warnings.append({
                "image": image_name,
                "issue": f"Chart height {height_cm:.1f}cm exceeds container {container_cm}cm",
                "severity": "warn",
            })
    except ImportError:
        pass
    return warnings


def _audit_chart_brand(image_path: Path, brand) -> list[dict]:
    """Check if chart colours align with brand palette."""
    warnings = []
    try:
        from PIL import Image
        import numpy as np

        img = Image.open(str(image_path)).convert("RGB")
        pixels = np.array(img)

        # Sample background from corner
        bg = pixels[2, 2].tolist()

        # Get non-background pixels
        mask = np.any(np.abs(pixels.astype(int) - bg) > 25, axis=2)
        content_pixels = pixels[mask]

        if len(content_pixels) == 0:
            return warnings

        # Simple dominant colour extraction: sample 1000 random pixels
        rng = np.random.default_rng(42)
        sample_size = min(1000, len(content_pixels))
        sample = content_pixels[rng.choice(len(content_pixels), sample_size, replace=False)]

        # Get brand colours as RGB tuples
        brand_colors_rgb = []
        for hex_color in (brand.chart_colors or []) + [brand.primary, brand.secondary]:
            if hex_color:
                h = hex_color.lstrip("#")
                brand_colors_rgb.append((int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)))

        if not brand_colors_rgb:
            return warnings

        # Check each sampled pixel against brand colours
        off_brand_count = 0
        for px in sample:
            r, g, b = int(px[0]), int(px[1]), int(px[2])
            # Skip greys (axes, labels)
            if abs(r - g) < 20 and abs(g - b) < 20:
                continue
            # Find closest brand colour
            min_dist = float("inf")
            for br, bg_, bb in brand_colors_rgb:
                dist = math.sqrt((r - br) ** 2 + (g - bg_) ** 2 + (b - bb) ** 2)
                min_dist = min(min_dist, dist)
            if min_dist > 50:  # More than 50 RGB distance from nearest brand colour
                off_brand_count += 1

        if off_brand_count > sample_size * 0.1:  # >10% of coloured pixels off-brand
            warnings.append({
                "issue": f"Chart has {off_brand_count}/{sample_size} sampled pixels off-brand palette",
                "severity": "warn",
            })

    except ImportError:
        pass
    return warnings


def _audit_chart_data(
    chart_data: dict[str, Any],
    source_section: dict[str, Any],
) -> list[dict]:
    """Check if chart data values appear in the source section content."""
    warnings = []

    # Extract all numeric values from chart data
    chart_values = set()
    for v in _flatten_values(chart_data):
        if isinstance(v, (int, float)):
            chart_values.add(v)

    if not chart_values:
        return warnings

    # Extract all text from source section
    source_text = " ".join(str(v) for v in _flatten_values(source_section))

    # Check each chart value
    for val in chart_values:
        val_str = str(val)
        # Check for exact match or close match (e.g., "4.8" in "$4.8 trillion")
        if val_str not in source_text:
            # Try integer version
            if isinstance(val, float) and str(int(val)) in source_text:
                continue
            warnings.append({
                "issue": f"Chart value {val} not found in source section data",
                "severity": "info",
            })

    return warnings


# =========================================================================
# HELPERS
# =========================================================================

def _truncate_at_word(text: str, max_chars: int, ellipsis: bool = True) -> str:
    """Truncate text at the last word boundary before max_chars.

    ellipsis=False: used for slide titles (action titles should end cleanly,
    not with '...' which implies a sentence continuation that doesn't exist).
    ellipsis=True (default): used for body text/bullets where truncation is expected.
    """
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    last_space = truncated.rfind(" ")
    if last_space > max_chars * 0.6:
        truncated = truncated[:last_space]
    return truncated.rstrip() + ("..." if ellipsis else "")


def _get_nested(data: dict, dotted_key: str) -> Any:
    """Get a value from a dict using dotted notation (e.g., 'left.items')."""
    parts = dotted_key.split(".")
    current = data
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current


def _set_nested(data: dict, dotted_key: str, value: Any) -> None:
    """Set a value in a dict using dotted notation."""
    parts = dotted_key.split(".")
    current = data
    for part in parts[:-1]:
        if isinstance(current, dict):
            current = current.get(part, {})
    if isinstance(current, dict):
        current[parts[-1]] = value


def _flatten_values(data: Any) -> list[Any]:
    """Recursively flatten all values from a nested dict/list structure."""
    values = []
    if isinstance(data, dict):
        for v in data.values():
            values.extend(_flatten_values(v))
    elif isinstance(data, list):
        for item in data:
            values.extend(_flatten_values(item))
    else:
        values.append(data)
    return values


_CARD_TYPES = {"three_card", "four_card", "feature_grid"}


def _shorten_longest_field(data: dict, stype: str) -> None:
    """Find and shorten the longest text field on a slide.

    Card types (three_card, four_card, feature_grid) are skipped — they use
    adaptive font sizing to handle overflow, so shortening body text here only
    creates a truncation loop when the visual audit reports clipping.
    """
    if stype in _CARD_TYPES:
        return
    for field in _CONTENT_FIELDS.get(stype, []):
        items = _get_nested(data, field)
        if not items or not isinstance(items, list):
            continue
        # Find longest item
        longest_idx = -1
        longest_len = 0
        for j, item in enumerate(items):
            text = item if isinstance(item, str) else item.get("body", "") if isinstance(item, dict) else ""
            if len(text) > longest_len:
                longest_len = len(text)
                longest_idx = j
        if longest_idx >= 0 and longest_len > 80:
            item = items[longest_idx]
            if isinstance(item, str):
                items[longest_idx] = _truncate_at_word(item, int(longest_len * 0.7))
            elif isinstance(item, dict) and "body" in item:
                item["body"] = _truncate_at_word(item["body"], int(longest_len * 0.7))


def _split_source_sections(source: str) -> list[tuple[int, int]]:
    """Split Typst source into per-slide (start, end) byte ranges.

    Slides are separated by #pagebreak() or #page( function calls.
    """
    sections: list[tuple[int, int]] = []
    # Find all pagebreak and page markers
    markers = []
    for match in re.finditer(r'#pagebreak\(\)', source):
        markers.append(match.start())
    for match in re.finditer(r'#page\(', source):
        markers.append(match.start())

    markers.sort()

    if not markers:
        return [(0, len(source))]

    # First section: from start to first marker
    sections.append((0, markers[0]))
    # Middle sections: between markers
    for i in range(len(markers) - 1):
        sections.append((markers[i], markers[i + 1]))
    # Last section: from last marker to end
    sections.append((markers[-1], len(source)))

    return sections
