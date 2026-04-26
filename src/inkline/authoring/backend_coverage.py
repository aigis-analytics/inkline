"""Inkline backend-coverage matrix — slide-type × backend implementations + downgrade chains.

This module is the load-bearing contract for "backend-agnostic grammar":
- every slide_type declared in ``slide_renderer.py`` must appear here
- each type must either be implemented by the backend OR have a downgrade chain
- the CI test ``tests/authoring/test_backend_coverage.py`` asserts this

Usage::

    from inkline.authoring.backend_coverage import (
        COVERAGE, DOWNGRADE, get_downgraded_type, get_warnings
    )
    typ = get_downgraded_type("kpi_strip", backend="pptx")
    # returns "stat"

CLI::

    inkline backend-coverage
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Coverage matrix
# ---------------------------------------------------------------------------
# Each entry: slide_type → {backend: bool}
# True  = natively implemented
# False = not implemented (downgrade chain applies)

COVERAGE: dict[str, dict[str, bool]] = {
    # ── Structural ────────────────────────────────────────────────────────────
    "title":             {"typst": True,  "pptx": True,  "google_slides": True,  "html": True},
    "closing":           {"typst": True,  "pptx": True,  "google_slides": True,  "html": True},
    "section_divider":   {"typst": True,  "pptx": True,  "google_slides": False, "html": True},
    "content":           {"typst": True,  "pptx": True,  "google_slides": True,  "html": True},

    # ── Narrative ─────────────────────────────────────────────────────────────
    "three_card":        {"typst": True,  "pptx": True,  "google_slides": True,  "html": True},
    "four_card":         {"typst": True,  "pptx": True,  "google_slides": False, "html": True},
    "split":             {"typst": True,  "pptx": True,  "google_slides": False, "html": True},
    "comparison":        {"typst": True,  "pptx": False, "google_slides": False, "html": True},
    "timeline":          {"typst": True,  "pptx": False, "google_slides": False, "html": True},
    "process_flow":      {"typst": True,  "pptx": False, "google_slides": False, "html": True},
    "pyramid":           {"typst": True,  "pptx": False, "google_slides": False, "html": True},
    "testimonial":       {"typst": True,  "pptx": False, "google_slides": False, "html": True},
    "before_after":      {"typst": True,  "pptx": False, "google_slides": False, "html": True},

    # ── Visual heroes ─────────────────────────────────────────────────────────
    "stat":              {"typst": True,  "pptx": True,  "google_slides": False, "html": True},
    "kpi_strip":         {"typst": True,  "pptx": False, "google_slides": False, "html": True},
    "icon_stat":         {"typst": True,  "pptx": False, "google_slides": False, "html": True},
    "feature_grid":      {"typst": True,  "pptx": False, "google_slides": False, "html": True},
    "progress_bars":     {"typst": True,  "pptx": False, "google_slides": False, "html": True},
    "dashboard":         {"typst": True,  "pptx": False, "google_slides": False, "html": True},
    "team_grid":         {"typst": True,  "pptx": False, "google_slides": False, "html": True},
    "credentials":       {"typst": True,  "pptx": False, "google_slides": False, "html": True},

    # ── Data exhibits ─────────────────────────────────────────────────────────
    "table":             {"typst": True,  "pptx": True,  "google_slides": False, "html": True},
    "chart":             {"typst": True,  "pptx": True,  "google_slides": False, "html": True},
    "bar_chart":         {"typst": True,  "pptx": False, "google_slides": False, "html": True},
    "chart_caption":     {"typst": True,  "pptx": False, "google_slides": False, "html": True},
    "multi_chart":       {"typst": True,  "pptx": False, "google_slides": False, "html": True},
}

# ---------------------------------------------------------------------------
# Downgrade chains
# ---------------------------------------------------------------------------
# Ordered fallback list: first supported entry wins.
# Content is the final catch-all — always supported by PPTX and Google Slides.

DOWNGRADE: dict[str, list[str]] = {
    # Narrative layouts not in PPTX
    "comparison":        ["split", "content"],
    "timeline":          ["content"],
    "process_flow":      ["content"],
    "pyramid":           ["three_card", "content"],
    "testimonial":       ["content"],
    "before_after":      ["split", "content"],

    # Visual heroes not in PPTX
    "kpi_strip":         ["stat", "content"],
    "icon_stat":         ["stat", "content"],
    "feature_grid":      ["four_card", "content"],
    "progress_bars":     ["content"],
    "dashboard":         ["chart_caption", "content"],
    "team_grid":         ["content"],
    "credentials":       ["content"],

    # Data exhibits not in PPTX
    "bar_chart":         ["chart", "content"],
    "chart_caption":     ["chart", "content"],
    "multi_chart":       ["chart", "content"],

    # Google Slides additional downgrades
    "section_divider":   ["content"],
    "four_card":         ["three_card", "content"],
    "split":             ["content"],
    "stat":              ["content"],
    "table":             ["content"],
    "chart":             ["content"],
}


# ---------------------------------------------------------------------------
# Runtime helpers
# ---------------------------------------------------------------------------

def get_downgraded_type(slide_type: str, backend: str) -> str:
    """Return the best supported slide_type for a given backend.

    If ``slide_type`` is natively supported, returns it unchanged.
    Walks the downgrade chain until a supported type is found.
    Falls back to ``"content"`` if the chain is exhausted.

    Parameters
    ----------
    slide_type : str
        Requested slide type (e.g. ``"kpi_strip"``).
    backend : str
        One of ``"typst"``, ``"pptx"``, ``"google_slides"``, ``"html"``.
    """
    entry = COVERAGE.get(slide_type)
    if entry is None:
        # Unknown type — let the renderer handle it
        return slide_type

    if entry.get(backend, False):
        return slide_type

    # Walk downgrade chain
    for candidate in DOWNGRADE.get(slide_type, []):
        candidate_entry = COVERAGE.get(candidate, {})
        if candidate_entry.get(backend, False):
            return candidate

    return "content"


def get_warnings(slides: list[dict], backend: str) -> list[dict]:
    """Return a list of downgrade warnings for a slide list.

    Each warning is:
        {
          "slide_index": int,   # 0-based
          "original": str,
          "downgraded_to": str,
          "warning": str,
        }
    """
    warnings: list[dict] = []
    for i, slide in enumerate(slides):
        original = slide.get("slide_type", "")
        downgraded = get_downgraded_type(original, backend)
        if downgraded != original:
            warnings.append({
                "slide_index": i,
                "original": original,
                "downgraded_to": downgraded,
                "warning": f"Slide {i + 1} downgraded {original} → {downgraded} for {backend} backend",
            })
    return warnings


def print_coverage_table() -> str:
    """Return a formatted coverage table string for ``inkline backend-coverage``."""
    backends = ["typst", "pptx", "google_slides", "html"]
    header = f"{'Slide type':<22}" + "".join(f"  {b:<14}" for b in backends)
    divider = "-" * len(header)
    lines = [header, divider]

    for slide_type, entry in sorted(COVERAGE.items()):
        row = f"{slide_type:<22}"
        for b in backends:
            supported = entry.get(b, False)
            if supported:
                mark = "  ok            "
            else:
                chain = DOWNGRADE.get(slide_type, [])
                downgrade_b = get_downgraded_type(slide_type, b)
                if downgrade_b != slide_type:
                    mark = f"  ->  {downgrade_b:<8}"
                else:
                    mark = "  --            "
            row += mark[:16]
        lines.append(row)

    lines.append(divider)
    lines.append(f"Total: {len(COVERAGE)} slide types across {len(backends)} backends")
    return "\n".join(lines)
