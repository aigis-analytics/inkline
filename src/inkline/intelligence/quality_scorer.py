"""Quality Scorer for Inkline slide decks.

Quantitative 0-100 score broken into 6 dimensions. Pure heuristics on slide spec data,
no LLM calls. Enables tracking improvement over time.

Pure Python, no dependencies beyond stdlib + dataclasses.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class QualityScore:
    """Quantitative quality assessment of a slide deck."""
    total: int
    grade: str  # "A" (90+), "B" (75+), "C" (60+), "D" (40+), "F" (<40)
    dimensions: dict[str, int] = field(default_factory=dict)
    issues: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

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

ACTION_WORDS = re.compile(
    r"\d+%|\$[\d,.]+|grew|increased|decreased|reduced|improved|"
    r"doubled|tripled|outperformed|saved|achieved|delivered|exceeded|vs\.?|compared"
    , re.IGNORECASE
)

# Weights for each dimension
WEIGHTS = {
    "visual_variety": 0.20,
    "data_ink_ratio": 0.20,
    "typography": 0.15,
    "colour_discipline": 0.15,
    "flow": 0.15,
    "density": 0.15,
}

# Capacity limits per slide type (for density scoring)
CAPACITY = {
    "content": 6,
    "three_card": 3,
    "four_card": 4,
    "feature_grid": 6,
    "timeline": 6,
    "process_flow": 4,
    "split": 6,  # per side
    "table": 6,  # rows
    "kpi_strip": 5,
    "icon_stat": 4,
    "stat": 4,
    "progress_bars": 6,
    "bar_chart": 12,
    "comparison": 6,
    "pyramid": 5,
}


# ---------------------------------------------------------------------------
# Dimension scorers — each returns (score: int, issues: list[str])
# ---------------------------------------------------------------------------


def _score_visual_variety(slides: list[dict]) -> tuple[int, list[str]]:
    """Visual Variety: slide type distribution."""
    if not slides:
        return 0, ["No slides"]

    issues: list[str] = []
    types = [s.get("slide_type", "unknown") for s in slides]
    unique = len(set(types))
    ratio = unique / len(types)

    # Base score: 100 if ratio >= 0.6, linear down to 0 at ratio 0
    if ratio >= 0.6:
        score = 100
    else:
        score = int(100 * ratio / 0.6)

    if ratio < 0.3:
        issues.append(f"Low variety: only {unique} unique types across {len(types)} slides")

    # Penalty for 3+ consecutive same type
    run_len = 1
    for i in range(1, len(types)):
        if types[i] == types[i - 1]:
            run_len += 1
            if run_len >= 3:
                score = max(0, score - 15)
                issues.append(f"3+ consecutive '{types[i]}' slides reduce variety")
                break
        else:
            run_len = 1

    return max(0, min(100, score)), issues


def _score_data_ink_ratio(slides: list[dict]) -> tuple[int, list[str]]:
    """Data-Ink Ratio: % of slides that are visual vs text."""
    if not slides:
        return 0, ["No slides"]

    issues: list[str] = []
    # Exclude title and closing from denominator
    content_slides = [s for s in slides if s.get("slide_type") not in ("title", "closing")]
    denom = max(len(content_slides), 1)
    visual_count = sum(1 for s in content_slides if s.get("slide_type") in VISUAL_TYPES)
    visual_pct = visual_count / denom

    # Score: 100 if >= 0.7, 0 if < 0.2, linear between
    if visual_pct >= 0.7:
        score = 100
    elif visual_pct < 0.2:
        score = 0
        issues.append(f"Only {visual_pct:.0%} visual slides — deck is text-heavy")
    else:
        score = int(100 * (visual_pct - 0.2) / 0.5)

    if visual_count == 0:
        issues.append("No visual slides at all — add charts, KPIs, or data exhibits")

    return max(0, min(100, score)), issues


def _score_typography(slides: list[dict]) -> tuple[int, list[str]]:
    """Typography: title quality, bullet discipline, stat formatting."""
    score = 100
    issues: list[str] = []

    for i, s in enumerate(slides):
        st = s.get("slide_type", "")
        data = s.get("data", {})
        title = data.get("title", "")

        # Skip structural slides
        if st in ("title", "closing"):
            continue

        # Generic title: -10
        if title.strip().lower() in WEAK_TITLES:
            score -= 10
            issues.append(f"Slide {i}: generic title '{title}'")

        # Long title: -5 per
        if len(title) > 45:
            score -= 5
            issues.append(f"Slide {i}: title is {len(title)} chars (>45)")

        # Action title bonus: +5
        if ACTION_WORDS.search(title):
            score += 5

        # Bullet length: -3 per long bullet
        items = data.get("items", [])
        if isinstance(items, list):
            for item in items:
                text = item if isinstance(item, str) else str(item)
                if len(text) > 100:
                    score -= 3
                    issues.append(f"Slide {i}: bullet >100 chars")
                    break  # One penalty per slide

    return max(0, min(100, score)), issues


def _score_colour_discipline(slides: list[dict]) -> tuple[int, list[str]]:
    """Colour Discipline: accent usage, chart colour count, brand adherence."""
    score = 100
    issues: list[str] = []

    for i, s in enumerate(slides):
        cr = s.get("data", {}).get("chart_request")
        if not cr:
            continue

        # Missing accent_index: -15
        if "accent_index" not in cr:
            score -= 15
            issues.append(f"Slide {i}: chart missing accent_index")

        # >6 colours in chart: -10
        cd = cr.get("chart_data", {})
        series = cd.get("series", [])
        x = cd.get("x", [])
        ct = cr.get("chart_type", "")
        if ct in ("donut", "pie"):
            segment_count = len(x) if isinstance(x, list) else 0
            if segment_count > 6:
                score -= 10
                issues.append(f"Slide {i}: {ct} chart has {segment_count} segments (>6)")
        elif isinstance(series, list) and len(series) > 6:
            score -= 10
            issues.append(f"Slide {i}: chart has {len(series)} series (>6 colours)")

        # Legend with <=6 series: -5
        if cr.get("legend_position") and isinstance(series, list) and len(series) <= 6:
            if ct in ("donut", "pie"):
                score -= 5
                issues.append(f"Slide {i}: {ct} uses legend instead of direct labels")

    return max(0, min(100, score)), issues


def _score_flow(slides: list[dict]) -> tuple[int, list[str]]:
    """Flow: story arc, opening impact, closing, section dividers."""
    score = 50  # Start at 50, add/subtract
    issues: list[str] = []

    if not slides:
        return 0, ["No slides"]

    # +20 if first content slide (after title) is visual
    content_start = None
    for i, s in enumerate(slides):
        if s.get("slide_type") not in ("title", "section_divider"):
            content_start = s
            break
    if content_start and content_start.get("slide_type") in VISUAL_TYPES:
        score += 20
    else:
        issues.append("First content slide is not visual — consider opening with data")

    # +15 if closing slide present
    if slides[-1].get("slide_type") == "closing":
        score += 15
    else:
        score -= 5
        issues.append("No closing slide")

    # +10 if section_dividers used between topic changes
    has_dividers = any(s.get("slide_type") == "section_divider" for s in slides)
    if has_dividers:
        score += 10

    # -10 per abrupt topic change (section field changes without divider)
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
                score -= 10
                issues.append(f"Slide {i}: abrupt topic change from '{prev_section}' to '{section}'")
        prev_section = section

    return max(0, min(100, score)), issues


def _score_density(slides: list[dict]) -> tuple[int, list[str]]:
    """Density: content per slide — not too sparse, not too dense."""
    if not slides:
        return 0, ["No slides"]

    issues: list[str] = []
    slide_scores: list[int] = []

    for i, s in enumerate(slides):
        st = s.get("slide_type", "")
        if st in ("title", "closing", "section_divider"):
            continue

        data = s.get("data", {})
        cap = CAPACITY.get(st, 6)

        # Count items for the slide
        item_count = 0
        if "items" in data and isinstance(data["items"], list):
            item_count = len(data["items"])
        elif "cards" in data and isinstance(data["cards"], list):
            item_count = len(data["cards"])
        elif "stats" in data and isinstance(data["stats"], list):
            item_count = len(data["stats"])
        elif "kpis" in data and isinstance(data["kpis"], list):
            item_count = len(data["kpis"])
        elif "features" in data and isinstance(data["features"], list):
            item_count = len(data["features"])
        elif "milestones" in data and isinstance(data["milestones"], list):
            item_count = len(data["milestones"])
        elif "steps" in data and isinstance(data["steps"], list):
            item_count = len(data["steps"])
        elif "bars" in data and isinstance(data["bars"], list):
            item_count = len(data["bars"])
        elif "rows" in data and isinstance(data["rows"], list):
            item_count = len(data["rows"])
        elif "tiers" in data and isinstance(data["tiers"], list):
            item_count = len(data["tiers"])
        else:
            # For chart/dashboard slides without countable items, assume good density
            slide_scores.append(80)
            continue

        if cap == 0:
            slide_scores.append(80)
            continue

        utilisation = item_count / cap

        if utilisation < 0.5:
            ss = int(60 * utilisation / 0.5)
            issues.append(f"Slide {i}: sparse ({item_count}/{cap} capacity)")
        elif utilisation > 0.9:
            ss = max(50, 100 - int(50 * (utilisation - 0.9) / 0.1))
            if item_count > cap:
                ss = max(30, ss - 20)
                issues.append(f"Slide {i}: over capacity ({item_count}/{cap})")
        else:
            # Sweet spot: 50-90% utilisation
            ss = 100
        slide_scores.append(max(0, min(100, ss)))

    if not slide_scores:
        return 70, issues  # No scoreable slides

    avg = sum(slide_scores) // len(slide_scores)
    return max(0, min(100, avg)), issues


# ---------------------------------------------------------------------------
# Main scoring function
# ---------------------------------------------------------------------------

_DIMENSION_SCORERS = {
    "visual_variety": _score_visual_variety,
    "data_ink_ratio": _score_data_ink_ratio,
    "typography": _score_typography,
    "colour_discipline": _score_colour_discipline,
    "flow": _score_flow,
    "density": _score_density,
}

# Suggestions keyed by dimension name
_DIMENSION_SUGGESTIONS = {
    "visual_variety": "Diversify slide types — replace repeated content slides with charts, cards, or kpi_strip",
    "data_ink_ratio": "Add more visual slides (charts, dashboards, KPIs) to improve data-to-ink ratio",
    "typography": "Use action titles that state conclusions, keep bullets under 100 chars",
    "colour_discipline": "Add accent_index to charts and limit colour count to 6 or fewer",
    "flow": "Improve story arc — open with data, use section dividers, end with a closing slide",
    "density": "Balance content density — aim for 50-90% capacity utilisation per slide",
}


def _compute_grade(total: int) -> str:
    """Map total score to letter grade."""
    if total >= 90:
        return "A"
    if total >= 75:
        return "B"
    if total >= 60:
        return "C"
    if total >= 40:
        return "D"
    return "F"


def score_deck(slides: list[dict], brand: str | None = None) -> QualityScore:
    """Score a slide deck across 6 quality dimensions.

    Args:
        slides: List of slide spec dicts, each with "slide_type" and "data" keys.
        brand: Optional brand name (reserved for future brand-specific scoring).

    Returns:
        QualityScore with total (0-100), grade, per-dimension scores, issues, and suggestions.
    """
    dimensions: dict[str, int] = {}
    all_issues: list[str] = []

    for dim_name, scorer_fn in _DIMENSION_SCORERS.items():
        dim_score, dim_issues = scorer_fn(slides)
        dimensions[dim_name] = dim_score
        all_issues.extend(dim_issues)

    # Weighted total
    total = int(sum(dimensions[d] * WEIGHTS[d] for d in WEIGHTS))
    total = max(0, min(100, total))

    grade = _compute_grade(total)

    # Top 3 suggestions based on lowest-scoring dimensions
    sorted_dims = sorted(dimensions.items(), key=lambda x: x[1])
    suggestions = [_DIMENSION_SUGGESTIONS[d] for d, _ in sorted_dims[:3]]

    return QualityScore(
        total=total,
        grade=grade,
        dimensions=dimensions,
        issues=all_issues,
        suggestions=suggestions,
    )
