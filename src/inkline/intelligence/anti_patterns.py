"""Anti-Pattern Library for Inkline slide decks.

Codified rules that flag known bad design patterns in slide specs before rendering.
Runs after DesignAdvisor Phase 2 output, before Typst compilation.

Pure Python, no dependencies beyond stdlib + dataclasses.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class AntiPatternResult:
    """A single anti-pattern detection result."""
    rule_id: str
    category: str
    severity: str  # "error" | "warning" | "info"
    message: str
    slide_indices: list[int] = field(default_factory=list)
    suggestion: str = ""


# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------

TEXT_HEAVY_TYPES = {"content", "narrative"}

VISUAL_TYPES = {
    "chart", "chart_caption", "dashboard", "multi_chart",
    "kpi_strip", "icon_stat", "stat", "progress_bars",
    "bar_chart", "feature_grid",
}

WEAK_TITLES = {
    "overview", "summary", "introduction", "background",
    "the problem", "the solution", "agenda", "next steps",
    "q&a", "questions", "thank you", "appendix", "details",
    "update", "status", "progress", "recap", "review",
    "discussion", "analysis",
}

# ---------------------------------------------------------------------------
# Layout Patterns (LP-*)
# ---------------------------------------------------------------------------


def _check_lp01(slides: list[dict]) -> list[AntiPatternResult]:
    """LP-01: 3+ consecutive text-heavy slides (content, narrative)."""
    results: list[AntiPatternResult] = []
    run_start = -1
    run_len = 0
    for i, s in enumerate(slides):
        if s.get("slide_type") in TEXT_HEAVY_TYPES:
            if run_len == 0:
                run_start = i
            run_len += 1
        else:
            if run_len >= 3:
                indices = list(range(run_start, run_start + run_len))
                results.append(AntiPatternResult(
                    rule_id="LP-01",
                    category="layout",
                    severity="error",
                    message=f"{run_len} consecutive text-heavy slides at indices {indices}",
                    slide_indices=indices,
                    suggestion="Break up with a visual slide (chart, kpi_strip, icon_stat, dashboard)",
                ))
            run_len = 0
    # Check trailing run
    if run_len >= 3:
        indices = list(range(run_start, run_start + run_len))
        results.append(AntiPatternResult(
            rule_id="LP-01",
            category="layout",
            severity="error",
            message=f"{run_len} consecutive text-heavy slides at indices {indices}",
            slide_indices=indices,
            suggestion="Break up with a visual slide (chart, kpi_strip, icon_stat, dashboard)",
        ))
    return results


def _check_lp02(slides: list[dict]) -> list[AntiPatternResult]:
    """LP-02: No visual slide in first 3 slides after title."""
    if len(slides) < 2:
        return []
    # Find slides[1:4] (first 3 after title)
    check_range = slides[1:4]
    for s in check_range:
        if s.get("slide_type") in VISUAL_TYPES:
            return []
    return [AntiPatternResult(
        rule_id="LP-02",
        category="layout",
        severity="warning",
        message="No visual slide in the first 3 slides after the title",
        slide_indices=list(range(1, min(4, len(slides)))),
        suggestion="Add a chart, kpi_strip, icon_stat, or dashboard in the opening slides",
    )]


def _check_lp03(slides: list[dict]) -> list[AntiPatternResult]:
    """LP-03: Cards-in-cards nesting (split containing cards)."""
    results: list[AntiPatternResult] = []
    for i, s in enumerate(slides):
        if s.get("slide_type") == "split":
            data = s.get("data", {})
            # Check if left/right items contain nested card-like structures
            for side in ("left_items", "right_items"):
                items = data.get(side, [])
                if isinstance(items, list):
                    for item in items:
                        if isinstance(item, dict) and ("cards" in item or "title" in item and "body" in item):
                            results.append(AntiPatternResult(
                                rule_id="LP-03",
                                category="layout",
                                severity="warning",
                                message=f"Slide {i}: split slide contains nested card-like structures",
                                slide_indices=[i],
                                suggestion="Flatten the hierarchy — use separate card slides instead of nesting",
                            ))
                            break
    return results


def _check_lp04(slides: list[dict]) -> list[AntiPatternResult]:
    """LP-04: Missing section_divider between topic changes."""
    results: list[AntiPatternResult] = []
    prev_section = None
    for i, s in enumerate(slides):
        st = s.get("slide_type", "")
        if st in ("title", "closing"):
            prev_section = None
            continue
        section = s.get("data", {}).get("section", "")
        if not section:
            prev_section = None
            continue
        if prev_section is not None and section != prev_section:
            # Topic changed — check if this slide or the previous one is a section_divider
            if st != "section_divider" and (i > 0 and slides[i - 1].get("slide_type") != "section_divider"):
                results.append(AntiPatternResult(
                    rule_id="LP-04",
                    category="layout",
                    severity="info",
                    message=f"Slide {i}: section changed from '{prev_section}' to '{section}' without a divider",
                    slide_indices=[i],
                    suggestion="Add a section_divider slide between topic changes",
                ))
        prev_section = section
    return results


def _check_lp05(slides: list[dict]) -> list[AntiPatternResult]:
    """LP-05: >60% of slides are content/narrative type."""
    if not slides:
        return []
    text_count = sum(1 for s in slides if s.get("slide_type") in TEXT_HEAVY_TYPES)
    ratio = text_count / len(slides)
    if ratio > 0.6:
        return [AntiPatternResult(
            rule_id="LP-05",
            category="layout",
            severity="error",
            message=f"{text_count}/{len(slides)} slides ({ratio:.0%}) are text-heavy (content/narrative)",
            slide_indices=list(range(len(slides))),
            suggestion="Replace some content slides with visual types (charts, kpi_strip, icon_stat)",
        )]
    return []


def _check_lp06(slides: list[dict]) -> list[AntiPatternResult]:
    """LP-06: Deck has no closing slide."""
    if not slides:
        return []
    if slides[-1].get("slide_type") != "closing":
        return [AntiPatternResult(
            rule_id="LP-06",
            category="layout",
            severity="warning",
            message="Deck has no closing slide",
            slide_indices=[len(slides) - 1],
            suggestion="Add a closing slide with contact information",
        )]
    return []


def _check_lp07(slides: list[dict]) -> list[AntiPatternResult]:
    """LP-07: Identical slide types used 3+ times consecutively."""
    results: list[AntiPatternResult] = []
    if len(slides) < 3:
        return results
    run_start = 0
    run_type = slides[0].get("slide_type")
    run_len = 1
    for i in range(1, len(slides)):
        st = slides[i].get("slide_type")
        if st == run_type:
            run_len += 1
        else:
            if run_len >= 3:
                indices = list(range(run_start, run_start + run_len))
                results.append(AntiPatternResult(
                    rule_id="LP-07",
                    category="layout",
                    severity="warning",
                    message=f"{run_len} consecutive '{run_type}' slides at indices {indices}",
                    slide_indices=indices,
                    suggestion=f"Vary the slide types — convert some '{run_type}' slides to other formats",
                ))
            run_start = i
            run_type = st
            run_len = 1
    if run_len >= 3:
        indices = list(range(run_start, run_start + run_len))
        results.append(AntiPatternResult(
            rule_id="LP-07",
            category="layout",
            severity="warning",
            message=f"{run_len} consecutive '{run_type}' slides at indices {indices}",
            slide_indices=indices,
            suggestion=f"Vary the slide types — convert some '{run_type}' slides to other formats",
        ))
    return results


# ---------------------------------------------------------------------------
# Typography Patterns (TP-*)
# ---------------------------------------------------------------------------


def _get_title(slide: dict) -> str:
    """Extract the title from a slide's data."""
    return slide.get("data", {}).get("title", "")


def _check_tp01(slides: list[dict]) -> list[AntiPatternResult]:
    """TP-01: Title >50 chars (hard limit)."""
    results: list[AntiPatternResult] = []
    for i, s in enumerate(slides):
        title = _get_title(s)
        if len(title) > 50:
            results.append(AntiPatternResult(
                rule_id="TP-01",
                category="typography",
                severity="error",
                message=f"Slide {i}: title is {len(title)} chars (max 50): '{title[:60]}...'",
                slide_indices=[i],
                suggestion="Shorten the title to 50 characters or fewer",
            ))
    return results


def _check_tp02(slides: list[dict]) -> list[AntiPatternResult]:
    """TP-02: Title is generic/non-actionable."""
    results: list[AntiPatternResult] = []
    for i, s in enumerate(slides):
        st = s.get("slide_type", "")
        if st in ("title", "closing", "section_divider"):
            continue
        title = _get_title(s).strip().lower()
        if title in WEAK_TITLES:
            results.append(AntiPatternResult(
                rule_id="TP-02",
                category="typography",
                severity="warning",
                message=f"Slide {i}: generic title '{_get_title(s)}'",
                slide_indices=[i],
                suggestion="Use an action title that states the conclusion (e.g. '98% gross margin at scale')",
            ))
    return results


def _check_tp03(slides: list[dict]) -> list[AntiPatternResult]:
    """TP-03: Bullet text >120 chars."""
    results: list[AntiPatternResult] = []
    for i, s in enumerate(slides):
        data = s.get("data", {})
        items = data.get("items", [])
        if not isinstance(items, list):
            continue
        for item in items:
            text = item if isinstance(item, str) else str(item)
            if len(text) > 120:
                results.append(AntiPatternResult(
                    rule_id="TP-03",
                    category="typography",
                    severity="warning",
                    message=f"Slide {i}: bullet text is {len(text)} chars (max 120)",
                    slide_indices=[i],
                    suggestion="Shorten bullet points to 120 characters or fewer",
                ))
                break  # One warning per slide is enough
    return results


def _check_tp04(slides: list[dict]) -> list[AntiPatternResult]:
    """TP-04: >6 bullet items on any slide."""
    results: list[AntiPatternResult] = []
    for i, s in enumerate(slides):
        data = s.get("data", {})
        items = data.get("items", [])
        if isinstance(items, list) and len(items) > 6:
            results.append(AntiPatternResult(
                rule_id="TP-04",
                category="typography",
                severity="error",
                message=f"Slide {i}: {len(items)} bullet items (max 6)",
                slide_indices=[i],
                suggestion="Reduce to 6 items or split across multiple slides",
            ))
    return results


def _check_tp05(slides: list[dict]) -> list[AntiPatternResult]:
    """TP-05: ALL CAPS in body text (not titles)."""
    results: list[AntiPatternResult] = []
    all_caps_re = re.compile(r"\b[A-Z]{4,}\b")  # Words >3 chars in all caps
    for i, s in enumerate(slides):
        data = s.get("data", {})
        # Check items, narrative, card bodies
        texts: list[str] = []
        for key in ("items", "narrative"):
            val = data.get(key, [])
            if isinstance(val, list):
                texts.extend(str(v) for v in val)
            elif isinstance(val, str):
                texts.append(val)
        # Card bodies
        for card in data.get("cards", []):
            if isinstance(card, dict):
                body = card.get("body", "")
                if body:
                    texts.append(str(body))
        for text in texts:
            if all_caps_re.search(text):
                results.append(AntiPatternResult(
                    rule_id="TP-05",
                    category="typography",
                    severity="info",
                    message=f"Slide {i}: ALL CAPS text found in body content",
                    slide_indices=[i],
                    suggestion="Use sentence case or title case instead of ALL CAPS in body text",
                ))
                break
    return results


def _check_tp06(slides: list[dict]) -> list[AntiPatternResult]:
    """TP-06: Stat value >16 chars (won't fit in kpi_strip)."""
    results: list[AntiPatternResult] = []
    for i, s in enumerate(slides):
        st = s.get("slide_type", "")
        if st not in ("kpi_strip", "icon_stat", "stat"):
            continue
        data = s.get("data", {})
        for key in ("stats", "kpis"):
            items = data.get(key, [])
            if not isinstance(items, list):
                continue
            for item in items:
                if isinstance(item, dict):
                    val = str(item.get("value", ""))
                    if len(val) > 16:
                        results.append(AntiPatternResult(
                            rule_id="TP-06",
                            category="typography",
                            severity="error",
                            message=f"Slide {i}: stat value '{val}' is {len(val)} chars (max 16)",
                            slide_indices=[i],
                            suggestion="Abbreviate the value (e.g. '$4.2M' instead of '$4,200,000')",
                        ))
    return results


# ---------------------------------------------------------------------------
# Colour & Visual Patterns (CP-*)
# ---------------------------------------------------------------------------


def _get_chart_request(slide: dict) -> dict | None:
    """Extract chart_request from a slide's data."""
    return slide.get("data", {}).get("chart_request")


def _check_cp01(slides: list[dict]) -> list[AntiPatternResult]:
    """CP-01: Chart missing accent_index (no emphasis)."""
    results: list[AntiPatternResult] = []
    for i, s in enumerate(slides):
        cr = _get_chart_request(s)
        if cr and "accent_index" not in cr:
            results.append(AntiPatternResult(
                rule_id="CP-01",
                category="colour",
                severity="warning",
                message=f"Slide {i}: chart missing accent_index — no data emphasis",
                slide_indices=[i],
                suggestion="Add accent_index to highlight the most important data point",
            ))
    return results


def _check_cp02(slides: list[dict]) -> list[AntiPatternResult]:
    """CP-02: >6 segments in donut/pie without direct labels."""
    results: list[AntiPatternResult] = []
    for i, s in enumerate(slides):
        cr = _get_chart_request(s)
        if not cr:
            continue
        ct = cr.get("chart_type", "")
        if ct not in ("donut", "pie"):
            continue
        cd = cr.get("chart_data", {})
        # Count segments from series or data
        segments = 0
        series = cd.get("series", [])
        if isinstance(series, list) and series:
            first = series[0] if series else {}
            if isinstance(first, dict):
                segments = len(first.get("values", []))
        # Also check x-axis labels as proxy
        x = cd.get("x", [])
        if isinstance(x, list):
            segments = max(segments, len(x))
        if segments > 6:
            label_strategy = cr.get("label_strategy", "")
            if label_strategy != "direct":
                results.append(AntiPatternResult(
                    rule_id="CP-02",
                    category="colour",
                    severity="warning",
                    message=f"Slide {i}: {ct} chart has {segments} segments without direct labels",
                    slide_indices=[i],
                    suggestion="Use direct labels instead of a legend for charts with >6 segments",
                ))
    return results


def _check_cp03(slides: list[dict]) -> list[AntiPatternResult]:
    """CP-03: Bar chart with >12 categories (horizontal not set)."""
    results: list[AntiPatternResult] = []
    for i, s in enumerate(slides):
        cr = _get_chart_request(s)
        if not cr:
            continue
        ct = cr.get("chart_type", "")
        if "bar" not in ct:
            continue
        cd = cr.get("chart_data", {})
        x = cd.get("x", [])
        if isinstance(x, list) and len(x) > 12:
            orientation = cr.get("orientation", "")
            if orientation != "horizontal":
                results.append(AntiPatternResult(
                    rule_id="CP-03",
                    category="colour",
                    severity="warning",
                    message=f"Slide {i}: bar chart has {len(x)} categories but orientation is not horizontal",
                    slide_indices=[i],
                    suggestion="Set orientation to 'horizontal' for bar charts with >12 categories",
                ))
    return results


def _check_cp04(slides: list[dict]) -> list[AntiPatternResult]:
    """CP-04: Chart using legend when direct labels would work."""
    results: list[AntiPatternResult] = []
    for i, s in enumerate(slides):
        cr = _get_chart_request(s)
        if not cr:
            continue
        legend = cr.get("legend_position")
        if not legend:
            continue
        cd = cr.get("chart_data", {})
        series = cd.get("series", [])
        if isinstance(series, list) and len(series) <= 6:
            results.append(AntiPatternResult(
                rule_id="CP-04",
                category="colour",
                severity="info",
                message=f"Slide {i}: chart uses legend with only {len(series)} series — direct labels may work better",
                slide_indices=[i],
                suggestion="Consider using direct labels instead of a legend for <=6 series",
            ))
    return results


# ---------------------------------------------------------------------------
# Data Patterns (DP-*)
# ---------------------------------------------------------------------------


def _check_dp01(slides: list[dict]) -> list[AntiPatternResult]:
    """DP-01: Table with <4 rows (should be icon_stat or kpi_strip)."""
    results: list[AntiPatternResult] = []
    for i, s in enumerate(slides):
        if s.get("slide_type") != "table":
            continue
        rows = s.get("data", {}).get("rows", [])
        if isinstance(rows, list) and len(rows) < 4:
            results.append(AntiPatternResult(
                rule_id="DP-01",
                category="data",
                severity="info",
                message=f"Slide {i}: table has only {len(rows)} rows — consider icon_stat or kpi_strip",
                slide_indices=[i],
                suggestion="Convert small tables to icon_stat or kpi_strip for better visual impact",
            ))
    return results


def _check_dp02(slides: list[dict]) -> list[AntiPatternResult]:
    """DP-02: Single-series bar chart (could be progress_bars)."""
    results: list[AntiPatternResult] = []
    for i, s in enumerate(slides):
        cr = _get_chart_request(s)
        if not cr:
            continue
        ct = cr.get("chart_type", "")
        if "bar" not in ct:
            continue
        cd = cr.get("chart_data", {})
        series = cd.get("series", [])
        if isinstance(series, list) and len(series) == 1:
            results.append(AntiPatternResult(
                rule_id="DP-02",
                category="data",
                severity="info",
                message=f"Slide {i}: single-series bar chart — could use native progress_bars",
                slide_indices=[i],
                suggestion="Consider using progress_bars slide type for single-series bar data",
            ))
    return results


def _check_dp03(slides: list[dict]) -> list[AntiPatternResult]:
    """DP-03: Metrics in narrative text, not extracted to stats."""
    results: list[AntiPatternResult] = []
    metric_re = re.compile(
        r"(?:\$[\d,.]+[MBKmk]?|[\d,.]+%|\d+(?:,\d{3})+|\d+\.\d+[MBKmk])"
    )
    for i, s in enumerate(slides):
        st = s.get("slide_type", "")
        if st not in ("content", "narrative"):
            continue
        data = s.get("data", {})
        narrative = data.get("narrative", "")
        items = data.get("items", [])
        text_parts: list[str] = []
        if narrative:
            text_parts.append(str(narrative))
        if isinstance(items, list):
            text_parts.extend(str(it) for it in items)
        full_text = " ".join(text_parts)
        matches = metric_re.findall(full_text)
        if len(matches) >= 2:
            results.append(AntiPatternResult(
                rule_id="DP-03",
                category="data",
                severity="warning",
                message=f"Slide {i}: {len(matches)} metrics found in narrative text — extract to stats",
                slide_indices=[i],
                suggestion="Extract metrics into a kpi_strip, icon_stat, or stat slide",
            ))
    return results


def _check_dp04(slides: list[dict]) -> list[AntiPatternResult]:
    """DP-04: Time series with <3 data points."""
    results: list[AntiPatternResult] = []
    for i, s in enumerate(slides):
        cr = _get_chart_request(s)
        if not cr:
            continue
        ct = cr.get("chart_type", "")
        if ct not in ("line_chart", "area_chart"):
            continue
        cd = cr.get("chart_data", {})
        x = cd.get("x", [])
        if isinstance(x, list) and len(x) < 3:
            results.append(AntiPatternResult(
                rule_id="DP-04",
                category="data",
                severity="warning",
                message=f"Slide {i}: time series has only {len(x)} data points (need at least 3)",
                slide_indices=[i],
                suggestion="Add more data points or use a different visualization for sparse data",
            ))
    return results


# ---------------------------------------------------------------------------
# Structural Patterns (SP-*)
# ---------------------------------------------------------------------------


def _check_sp01(slides: list[dict]) -> list[AntiPatternResult]:
    """SP-01: Deck <5 slides (too thin) or >25 slides (too long)."""
    n = len(slides)
    if n < 5:
        return [AntiPatternResult(
            rule_id="SP-01",
            category="structural",
            severity="warning",
            message=f"Deck has only {n} slides — may be too thin",
            slide_indices=list(range(n)),
            suggestion="Consider adding more content slides for a complete presentation",
        )]
    if n > 25:
        return [AntiPatternResult(
            rule_id="SP-01",
            category="structural",
            severity="warning",
            message=f"Deck has {n} slides — may be too long",
            slide_indices=list(range(n)),
            suggestion="Consider condensing or splitting into multiple decks",
        )]
    return []


def _check_sp02(slides: list[dict]) -> list[AntiPatternResult]:
    """SP-02: No chart/dashboard/multi_chart in entire deck."""
    chart_types = {"chart", "chart_caption", "dashboard", "multi_chart"}
    for s in slides:
        if s.get("slide_type") in chart_types:
            return []
    return [AntiPatternResult(
        rule_id="SP-02",
        category="structural",
        severity="error",
        message="Deck has no chart, dashboard, or multi_chart slides",
        slide_indices=list(range(len(slides))),
        suggestion="Add data visualizations to support your narrative with evidence",
    )]


def _check_sp03(slides: list[dict]) -> list[AntiPatternResult]:
    """SP-03: Duplicate slide titles."""
    results: list[AntiPatternResult] = []
    seen: dict[str, int] = {}
    for i, s in enumerate(slides):
        st = s.get("slide_type", "")
        if st in ("title", "closing"):
            continue
        title = _get_title(s).strip().lower()
        if not title:
            continue
        if title in seen:
            results.append(AntiPatternResult(
                rule_id="SP-03",
                category="structural",
                severity="warning",
                message=f"Slide {i}: duplicate title '{_get_title(s)}' (same as slide {seen[title]})",
                slide_indices=[seen[title], i],
                suggestion="Use unique, descriptive titles for each slide",
            ))
        else:
            seen[title] = i
    return results


def _check_sp04(slides: list[dict]) -> list[AntiPatternResult]:
    """SP-04: footnote on >50% of slides (overuse)."""
    if not slides:
        return []
    footnote_count = 0
    for s in slides:
        st = s.get("slide_type", "")
        if st in ("title", "closing"):
            continue
        if s.get("data", {}).get("footnote"):
            footnote_count += 1
    # Count content slides (excluding title/closing)
    content_slides = sum(1 for s in slides if s.get("slide_type") not in ("title", "closing"))
    if content_slides > 0 and footnote_count / content_slides > 0.5:
        return [AntiPatternResult(
            rule_id="SP-04",
            category="structural",
            severity="info",
            message=f"Footnotes on {footnote_count}/{content_slides} content slides (>50%) — overuse",
            slide_indices=list(range(len(slides))),
            suggestion="Reserve footnotes for slides that truly need source attribution",
        )]
    return []


# ---------------------------------------------------------------------------
# Typography Patterns (TP-07) — Action title verification
# ---------------------------------------------------------------------------

_COMPARISON_WORDS = frozenset({
    "more", "fewer", "higher", "lower", "faster", "slower",
    "better", "worse", "greater", "less", "above", "below",
})

_DIRECTION_WORDS = frozenset({
    "grew", "declined", "rose", "fell", "increased", "decreased",
    "exceeded", "surpassed", "outperformed", "underperformed",
    "improved", "worsened", "gained", "lost",
})

_DIGIT_RE = re.compile(r"\d")


def _check_tp07(slides: list[dict]) -> list[AntiPatternResult]:
    """TP-07: Action title verification — title must contain a number, comparison, or direction word."""
    results: list[AntiPatternResult] = []
    for i, s in enumerate(slides):
        st = s.get("slide_type", "")
        if st in ("title", "closing", "section_divider"):
            continue
        title = _get_title(s).strip()
        if not title:
            continue
        title_lower = title.lower()
        title_words = set(title_lower.split())

        has_digit = bool(_DIGIT_RE.search(title))
        has_comparison = bool(title_words & _COMPARISON_WORDS)
        has_direction = bool(title_words & _DIRECTION_WORDS)

        if not (has_digit or has_comparison or has_direction):
            results.append(AntiPatternResult(
                rule_id="TP-07",
                category="typography",
                severity="warning",
                message=(
                    f"Slide {i}: title '{title}' appears to be a topic label, not an action title. "
                    "Add a metric, comparison, or direction word."
                ),
                slide_indices=[i],
                suggestion=(
                    "Rewrite to state the insight, e.g. 'Revenue grew 34% YoY' not 'Revenue Overview'"
                ),
            ))
    return results


# ---------------------------------------------------------------------------
# Structural Patterns (SP-05) — Appendix problem detection
# ---------------------------------------------------------------------------

def _check_sp05(slides: list[dict]) -> list[AntiPatternResult]:
    """SP-05: Too many supporting slides, not enough multi_chart exhibits."""
    if not slides:
        return []
    content_slides = [
        s for s in slides if s.get("slide_type") not in ("title", "closing", "section_divider")
    ]
    total = max(len(content_slides), 1)
    content_count = sum(
        1 for s in content_slides if s.get("slide_type") in ("content", "table")
    )
    multi_chart_count = sum(
        1 for s in content_slides if s.get("slide_type") == "multi_chart"
    )
    if content_count > 0.30 * total and multi_chart_count < 0.15 * total:
        return [AntiPatternResult(
            rule_id="SP-05",
            category="structural",
            severity="warning",
            message=(
                f"Deck has too many supporting slides: {content_count} content/table slides "
                f"({content_count/total:.0%}) with only {multi_chart_count} multi_chart slides. "
                "Consider moving detail slides to an appendix section."
            ),
            slide_indices=list(range(len(slides))),
            suggestion="Use multi_chart layouts for data-rich sections and move text/tables to appendix",
        )]
    return []


# ---------------------------------------------------------------------------
# Data Patterns (DP-05) — Apology footnote
# ---------------------------------------------------------------------------

_APOLOGY_WORDS = re.compile(
    r"\b(approximate|estimated|assumed|subject to change|indicative|not guaranteed)\b",
    re.IGNORECASE,
)


def _check_dp05(slides: list[dict]) -> list[AntiPatternResult]:
    """DP-05: Footnote contains a qualification that signals uncertainty."""
    results: list[AntiPatternResult] = []
    for i, s in enumerate(slides):
        footnote = s.get("data", {}).get("footnote", "")
        if not footnote:
            continue
        if _APOLOGY_WORDS.search(footnote):
            results.append(AntiPatternResult(
                rule_id="DP-05",
                category="data",
                severity="warning",
                message=(
                    f"Slide {i}: footnote contains a qualification that signals uncertainty: "
                    f"'{footnote[:80]}'"
                ),
                slide_indices=[i],
                suggestion="Replace with a source attribution or methodology note instead of a caveat",
            ))
    return results


# ---------------------------------------------------------------------------
# Data Patterns (DP-06) — Data dump (no dominant element)
# Note: DP-04 already exists (time series with <3 data points)
# ---------------------------------------------------------------------------

def _check_dp06(slides: list[dict]) -> list[AntiPatternResult]:
    """DP-06: Chart slide has no dominant element (no accent, stat callout, or insight bullets)."""
    results: list[AntiPatternResult] = []
    chart_slide_types = {"chart", "chart_caption", "dashboard", "multi_chart"}
    for i, s in enumerate(slides):
        if s.get("slide_type") not in chart_slide_types:
            continue
        data = s.get("data", {})
        cr = data.get("chart_request", {})

        has_accent = "accent_index" in cr
        has_stat = bool(data.get("stats"))
        has_bullets = bool(data.get("bullets")) or bool(data.get("items"))
        has_caption = bool(data.get("caption", "").strip())

        if not (has_accent or has_stat or has_bullets or has_caption):
            results.append(AntiPatternResult(
                rule_id="DP-06",
                category="data",
                severity="warning",
                message=(
                    f"Slide {i}: chart slide has no dominant element. "
                    "Add accent_index, stat callout, or insight bullets to focus audience attention."
                ),
                slide_indices=[i],
                suggestion="Add accent_index to the chart_request, or add bullets/stats to the slide data",
            ))
    return results


# ---------------------------------------------------------------------------
# Appearance Patterns (AP-05) — Symmetric deck (low visual rhythm)
# ---------------------------------------------------------------------------

def _check_ap05(slides: list[dict]) -> list[AntiPatternResult]:
    """AP-05: Deck has low visual variety rhythm (too uniform slide types)."""
    import math
    if len(slides) < 8:
        return []
    content_slides = [
        s for s in slides if s.get("slide_type") not in ("title", "closing", "section_divider")
    ]
    if len(content_slides) < 8:
        return []

    types = [s.get("slide_type", "") for s in content_slides]
    # Count transitions (type changes)
    transitions = [1 if types[i] != types[i - 1] else 0 for i in range(1, len(types))]
    if not transitions:
        return []

    # Compute std dev of local windows (measure of rhythmic variety)
    window = 4
    window_scores = []
    for start in range(0, len(transitions) - window + 1):
        w = transitions[start:start + window]
        window_scores.append(sum(w))

    if not window_scores:
        return []

    mean_val = sum(window_scores) / len(window_scores)
    variance = sum((x - mean_val) ** 2 for x in window_scores) / len(window_scores)
    std_dev = math.sqrt(variance)

    if std_dev < 1.5:
        return [AntiPatternResult(
            rule_id="AP-05",
            category="layout",
            severity="warning",
            message=(
                f"Deck has low visual variety rhythm (std dev of type changes: {std_dev:.1f}). "
                "Vary slide density: use high-impact Tier 1 slides for key points, "
                "lighter layouts for supporting detail."
            ),
            slide_indices=list(range(len(slides))),
            suggestion=(
                "Alternate between dense data exhibits (multi_chart, dashboard) and "
                "focused single-exhibit slides (icon_stat, three_card) to create visual rhythm"
            ),
        )]
    return []


# ---------------------------------------------------------------------------
# Appearance Patterns (AP-06) — Section transition without divider (warning level)
# ---------------------------------------------------------------------------

def _check_ap06(slides: list[dict]) -> list[AntiPatternResult]:
    """AP-06: Section transition without a section_divider slide (warning level upgrade of LP-04)."""
    results: list[AntiPatternResult] = []
    prev_section = None
    for i, s in enumerate(slides):
        st = s.get("slide_type", "")
        if st in ("title", "closing"):
            prev_section = None
            continue
        section = s.get("data", {}).get("section", "")
        if not section:
            prev_section = None
            continue
        if prev_section is not None and section != prev_section:
            if st != "section_divider" and (i > 0 and slides[i - 1].get("slide_type") != "section_divider"):
                results.append(AntiPatternResult(
                    rule_id="AP-06",
                    category="layout",
                    severity="warning",
                    message=(
                        f"Slide {i}: section transition from '{prev_section}' to '{section}' "
                        "without a section_divider slide. Consider adding a divider."
                    ),
                    slide_indices=[i],
                    suggestion=f"Insert a section_divider slide before slide {i} to signal the topic change",
                ))
        prev_section = section
    return results


# ---------------------------------------------------------------------------
# Capacity checks for new slide types
# ---------------------------------------------------------------------------

def _check_new_slide_capacities(slides: list[dict]) -> list[AntiPatternResult]:
    """Capacity checks for credentials, testimonial, before_after slide types."""
    results: list[AntiPatternResult] = []
    for i, s in enumerate(slides):
        st = s.get("slide_type", "")
        data = s.get("data", {})

        if st == "credentials":
            tombstones = data.get("tombstones", [])
            n = len(tombstones)
            if n < 4:
                results.append(AntiPatternResult(
                    rule_id="CAP-01",
                    category="structural",
                    severity="warning",
                    message=f"Slide {i}: credentials slide has only {n} tombstones (minimum 4)",
                    slide_indices=[i],
                    suggestion="Add more tombstones or use a different slide type for fewer items",
                ))
            elif n > 8:
                results.append(AntiPatternResult(
                    rule_id="CAP-01",
                    category="structural",
                    severity="error",
                    message=f"Slide {i}: credentials slide has {n} tombstones (maximum 8)",
                    slide_indices=[i],
                    suggestion="Reduce to 8 tombstones — move overflow to a second credentials slide",
                ))

        elif st == "testimonial":
            quote = data.get("quote", "")
            attribution = data.get("attribution", "")
            if len(quote) > 200:
                results.append(AntiPatternResult(
                    rule_id="CAP-02",
                    category="typography",
                    severity="error",
                    message=f"Slide {i}: testimonial quote is {len(quote)} chars (max 200)",
                    slide_indices=[i],
                    suggestion="Shorten the quote to 200 characters or fewer",
                ))
            if len(attribution) > 60:
                results.append(AntiPatternResult(
                    rule_id="CAP-02",
                    category="typography",
                    severity="warning",
                    message=f"Slide {i}: testimonial attribution is {len(attribution)} chars (max 60)",
                    slide_indices=[i],
                    suggestion="Shorten attribution to 60 characters or fewer",
                ))

        elif st == "before_after":
            for side_key in ("left", "right"):
                side = data.get(side_key, {})
                items = side.get("items", [])
                n = len(items)
                if n < 3:
                    results.append(AntiPatternResult(
                        rule_id="CAP-03",
                        category="structural",
                        severity="warning",
                        message=f"Slide {i}: before_after {side_key} side has only {n} items (minimum 3)",
                        slide_indices=[i],
                        suggestion="Add more items to the panel",
                    ))
                elif n > 5:
                    results.append(AntiPatternResult(
                        rule_id="CAP-03",
                        category="structural",
                        severity="error",
                        message=f"Slide {i}: before_after {side_key} side has {n} items (maximum 5)",
                        slide_indices=[i],
                        suggestion="Reduce to 5 items per side",
                    ))

        elif st == "team_grid":
            members = data.get("members", [])
            n = len(members)
            if n < 2:
                results.append(AntiPatternResult(
                    rule_id="CAP-04",
                    category="structural",
                    severity="error",
                    message=f"Slide {i}: team_grid has only {n} member(s) (minimum 2)",
                    slide_indices=[i],
                    suggestion="Need at least 2 team members",
                ))
            elif n > 4:
                results.append(AntiPatternResult(
                    rule_id="CAP-05",
                    category="structural",
                    severity="error",
                    message=f"Slide {i}: team_grid has {n} members (maximum 4)",
                    slide_indices=[i],
                    suggestion="team_grid supports max 4 members; use two slides for larger teams",
                ))
            # Warn on bios over 120 chars
            for member in members:
                bio = member.get("bio", "")
                if isinstance(bio, str) and len(bio) > 120:
                    results.append(AntiPatternResult(
                        rule_id="CAP-04",
                        category="typography",
                        severity="warning",
                        message=(
                            f"Slide {i}: team member '{member.get('name', '?')}' has a bio of "
                            f"{len(bio)} chars (recommended max 120)"
                        ),
                        slide_indices=[i],
                        suggestion="Shorten the bio to 120 characters or fewer to avoid truncation",
                    ))
                    break  # One warning per slide is enough

    return results


# ---------------------------------------------------------------------------
# Registry of all check functions
# ---------------------------------------------------------------------------

_ALL_CHECKS = [
    _check_lp01, _check_lp02, _check_lp03, _check_lp04,
    _check_lp05, _check_lp06, _check_lp07,
    _check_tp01, _check_tp02, _check_tp03, _check_tp04,
    _check_tp05, _check_tp06,
    _check_tp07,
    _check_cp01, _check_cp02, _check_cp03, _check_cp04,
    _check_dp01, _check_dp02, _check_dp03, _check_dp04,
    _check_dp05, _check_dp06,
    _check_sp01, _check_sp02, _check_sp03, _check_sp04,
    _check_sp05,
    _check_ap05, _check_ap06,
    _check_new_slide_capacities,
]


_INVESTOR_TEMPLATES = frozenset({"investor", "pitch", "boardroom"})


def check_anti_patterns(slides: list[dict], template: str = "") -> list[AntiPatternResult]:
    """Run all anti-pattern checks against a slide deck.

    Args:
        slides: List of slide spec dicts, each with "slide_type" and "data" keys.
        template: Optional template name — used to upgrade DP-03 severity for investor/pitch/boardroom.

    Returns:
        List of AntiPatternResult for every detected issue, sorted by slide index.
    """
    results: list[AntiPatternResult] = []
    for check_fn in _ALL_CHECKS:
        results.extend(check_fn(slides))

    # DP-03 severity upgrade: error for investor/pitch/boardroom templates
    if template.lower() in _INVESTOR_TEMPLATES:
        for r in results:
            if r.rule_id == "DP-03":
                r.severity = "error"
                r.message = r.message.replace("warning", "error")

    # Sort by first slide index, then by rule_id
    results.sort(key=lambda r: (r.slide_indices[0] if r.slide_indices else 0, r.rule_id))
    return results
