"""Template catalog — searchable index of 771 real slide templates.

Provides metadata-only access to a snapshot of the SlideModel and Genspark AI
Slides catalogues that the DesignAdvisor and end users can query for design
inspiration. Image previews are not bundled (~236 MB), but the manifests
contain CDN URLs you can fetch on demand.

The catalogue ships as static JSON inside the package (~1 MB total). Set the
environment variable ``INKLINE_TEMPLATE_CATALOG_DIR`` to point at a local copy
of the full image catalog (with ``slidemodel_thumbs/``, ``genspark/`` etc.) if
you want offline image-grounded design — the helpers will resolve image paths
against that directory when present.

Source
------
- SlideModel: 328 templates from the ``infographics`` and ``data-visualization``
  tags. Each entry has a hex palette (from the page meta), tag list, item ID,
  slide count, supported PowerPoint versions, and gallery image URLs.
- Genspark Professional: 128 multi-slide decks with 12-20 page screenshot URLs
  each. No palette/tags — only title + UUID + URLs.
- Genspark Creative: 315 single-thumbnail templates with prompt-driven titles.

Manifests are static snapshots from 2026-04-09. Re-scrape via the
``scripts/scrape_templates.py`` workflow if you need to refresh.

Usage
-----
    from inkline.intelligence.template_catalog import (
        find_templates,
        load_manifest,
        list_archetypes,
        get_archetype_recipe,
    )

    # Find a navy dashboard template
    hits = find_templates(tags=["dashboard"], color="#003366", limit=5)
    for t in hits:
        print(t["title"], t["palette"][:5])

    # Get the structured recipe for an archetype
    recipe = get_archetype_recipe("iceberg")
    print(recipe["palette_rule"])
    print(recipe["recipe"])
"""

from __future__ import annotations

import json
import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

log = logging.getLogger(__name__)

# Directory where the JSON manifests live (inside the package)
_CATALOG_DIR = Path(__file__).parent

# Optional local image catalog directory (for offline image grounding)
LOCAL_IMAGE_DIR_ENV = "INKLINE_TEMPLATE_CATALOG_DIR"

# Manifest registry — name -> filename
MANIFEST_REGISTRY: dict[str, str] = {
    "slidemodel":           "slidemodel_manifest.json",
    "genspark_professional": "genspark_professional_manifest.json",
    "genspark_creative":    "genspark_manifest.json",
}


# ─── Manifest loading ────────────────────────────────────────────────────────


@lru_cache(maxsize=8)
def load_manifest(name: str) -> dict[str, Any]:
    """Return the parsed JSON manifest for the named source.

    Parameters
    ----------
    name : str
        One of ``"slidemodel"``, ``"genspark_professional"``, ``"genspark_creative"``.

    Returns
    -------
    dict
        The parsed manifest. Schema varies per source — see ``MANIFEST_REGISTRY``.

    Raises
    ------
    ValueError
        If the manifest name is not recognised.
    FileNotFoundError
        If the JSON file is missing from the package install.
    """
    if name not in MANIFEST_REGISTRY:
        raise ValueError(
            f"Unknown manifest '{name}'. "
            f"Available: {', '.join(MANIFEST_REGISTRY)}"
        )
    path = _CATALOG_DIR / MANIFEST_REGISTRY[name]
    if not path.exists():
        raise FileNotFoundError(f"Manifest not found: {path}")
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    log.debug("Loaded manifest '%s' (%d entries)", name, _entry_count(data))
    return data


def _entry_count(manifest: dict[str, Any]) -> int:
    """Return the number of templates in a manifest regardless of schema."""
    if "results" in manifest:
        return len(manifest["results"])
    if "groups" in manifest:
        return len(manifest["groups"])
    return 0


# ─── Search ──────────────────────────────────────────────────────────────────


def find_templates(
    *,
    tags: Optional[list[str]] = None,
    color: Optional[str] = None,
    category: Optional[str] = None,
    title_contains: Optional[str] = None,
    min_slides: Optional[int] = None,
    max_slides: Optional[int] = None,
    source: str = "slidemodel",
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Search the SlideModel catalog by tag, color, category, title, or slide count.

    All filters are AND-combined. Filters are case-insensitive where text-based.

    Parameters
    ----------
    tags : list[str], optional
        Match templates whose ``tags`` field contains ALL of these strings
        (substring match, case-insensitive).
    color : str, optional
        Match templates whose ``palette`` contains this hex code (case-insensitive).
        E.g. ``"#003366"``.
    category : str, optional
        Substring match against the template's ``category`` field.
    title_contains : str, optional
        Substring match against the template's ``title``.
    min_slides, max_slides : int, optional
        Filter by ``slideCount``. ``None`` means unbounded.
    source : str
        Manifest to search. Currently only ``"slidemodel"`` carries the rich
        metadata needed for tag/colour search; the Genspark manifests are
        title-and-UUID only.
    limit : int
        Maximum number of results to return.

    Returns
    -------
    list[dict]
        Matching template entries from the manifest, in original order.
    """
    if source != "slidemodel":
        # Genspark manifests don't have tags/palettes; only title search applies
        manifest = load_manifest(source)
        groups = manifest.get("groups", [])
        out: list[dict[str, Any]] = []
        if title_contains:
            needle = title_contains.lower()
            out = [g for g in groups if needle in g.get("title", "").lower()]
        else:
            out = list(groups)
        return out[:limit]

    manifest = load_manifest(source)
    results = manifest.get("results", [])
    color_upper = color.upper() if color else None
    needle_title = title_contains.lower() if title_contains else None
    needle_cat = category.lower() if category else None
    tag_needles = [t.lower() for t in tags] if tags else []

    out: list[dict[str, Any]] = []
    for r in results:
        if color_upper and color_upper not in [c.upper() for c in r.get("palette", [])]:
            continue
        if needle_cat and needle_cat not in (r.get("category") or "").lower():
            continue
        if needle_title and needle_title not in r.get("title", "").lower():
            continue
        if min_slides is not None and (r.get("slideCount") or 0) < min_slides:
            continue
        if max_slides is not None and (r.get("slideCount") or 0) > max_slides:
            continue
        if tag_needles:
            r_tags_lower = [t.lower() for t in r.get("tags", [])]
            if not all(any(t in rt for rt in r_tags_lower) for t in tag_needles):
                continue
        out.append(r)
        if len(out) >= limit:
            break
    return out


# ─── Archetype recipes ───────────────────────────────────────────────────────

# The 16 archetypes documented in template_catalog.md, exposed as structured
# Python data so a programmatic caller (e.g. layout_selector) can reason about
# them without parsing the markdown.

ARCHETYPES: dict[str, dict[str, Any]] = {
    "iceberg": {
        "name": "Iceberg / hidden-vs-visible",
        "best_for": ["risk", "hidden_cost", "what_we_see_vs_dont"],
        "n_items": 2,
        "layout": "metaphor_split_horizontal",
        "palette_rule": "single_hue_monochrome",
        "example_palette": ["#003366", "#1E3A6E", "#3366CC", "#99CCFF", "#FFFFFF"],
        "inkline_slide_type": "dashboard",
        "needs_metaphor_image": True,
    },
    "sidebar_profile": {
        "name": "Sidebar profile + KPI grid",
        "best_for": ["bio", "executive_dashboard", "personal_brand"],
        "n_items": 6,
        "layout": "left_rail_22pct_plus_3x2_grid",
        "palette_rule": "mint_or_teal_primary",
        "example_palette": ["#66CCCC", "#88DDBB", "#FFFFFF", "#F4F5F7", "#2A3A4F"],
        "inkline_slide_type": "split",
        "needs_metaphor_image": False,
    },
    "funnel_kpi_strip": {
        "name": "Funnel KPI strip + chart grid",
        "best_for": ["sales", "conversion", "funnel"],
        "n_items": 6,
        "layout": "left_rail_28pct_plus_2_donuts_plus_3_rows",
        "palette_rule": "navy_to_teal_monochrome",
        "example_palette": ["#003366", "#003F5C", "#669999", "#88BBBB", "#FFFFFF"],
        "inkline_slide_type": "kpi_strip",
        "needs_metaphor_image": False,
    },
    "persona_dashboard": {
        "name": "Multi-tile customer/persona dashboard",
        "best_for": ["customer_profile", "ICP", "user_persona"],
        "n_items": 9,
        "layout": "3x3_tile_grid",
        "palette_rule": "multi_accent_rainbow",
        "example_palette": ["#993399", "#CC3399", "#663399", "#FFCC00", "#33CC99", "#3399FF"],
        "inkline_slide_type": "dashboard",
        "needs_metaphor_image": False,
    },
    "radial_pinwheel": {
        "name": "Radial framework (pinwheel)",
        "best_for": ["taxonomy", "framework", "principles"],
        "n_items": 8,
        "layout": "donut_8_segments",
        "palette_rule": "two_tone_half_circle",
        "example_palette": ["#1E5A8A", "#2E7AAA", "#3E9ACA", "#5EBA50", "#7ED070", "#9EE090"],
        "inkline_slide_type": "feature_grid",
        "needs_metaphor_image": False,
    },
    "hexagonal_honeycomb": {
        "name": "Hexagonal honeycomb",
        "best_for": ["design_thinking", "capability_map", "team_roles"],
        "n_items": 6,
        "layout": "centre_plus_6_hexagons",
        "palette_rule": "6_color_rainbow",
        "example_palette": ["#16A1CA", "#188ED6", "#7DBC2D", "#EEA720", "#EA3D15", "#9132A6"],
        "inkline_slide_type": "feature_grid",
        "needs_metaphor_image": False,
    },
    "semicircle_taxonomy": {
        "name": "Semi-circle taxonomy (large N)",
        "best_for": ["12_months", "12_dimensions", "many_items"],
        "n_items": 12,
        "layout": "dotted_arc_with_radial_callouts",
        "palette_rule": "single_brand_color",
        "example_palette": ["#0779B7", "#FFFFFF", "#999999", "#333333"],
        "inkline_slide_type": "timeline",
        "needs_metaphor_image": False,
    },
    "process_curved_arrows": {
        "name": "Linear/curved process flow",
        "best_for": ["customer_journey", "onboarding", "transformation"],
        "n_items": 4,
        "layout": "diagonal_curved_arrows",
        "palette_rule": "bright_multi_accent",
        "example_palette": ["#16A1CA", "#7DBC2D", "#EEA720", "#EA3D15"],
        "inkline_slide_type": "process_flow",
        "needs_metaphor_image": False,
    },
    "pyramid": {
        "name": "Pyramid hierarchy",
        "best_for": ["maslow", "capability_stack", "org_layers"],
        "n_items": 5,
        "layout": "5_horizontal_trapezoid_bands",
        "palette_rule": "two_hue_gradient",
        "example_palette": ["#7DBC2D", "#5EAE4D", "#3FA06D", "#20928D", "#0184AD"],
        "inkline_slide_type": "pyramid",
        "needs_metaphor_image": False,
    },
    "ladder": {
        "name": "Vertical step model (ladder)",
        "best_for": ["cognitive_model", "decision_framework", "escalation"],
        "n_items": 5,
        "layout": "central_ladder_with_side_callouts",
        "palette_rule": "blue_ladder_pastel_rungs",
        "example_palette": ["#3399CC", "#FFE5E5", "#FFE5CC", "#E5F5E5", "#E5E5FF"],
        "inkline_slide_type": "pyramid",
        "needs_metaphor_image": False,
    },
    "petal_teardrop": {
        "name": "Petal/teardrop step diagram",
        "best_for": ["soft_process", "design_workflow", "organic_growth"],
        "n_items": 7,
        "layout": "radial_teardrops_from_centre",
        "palette_rule": "saturated_rainbow_gradient",
        "example_palette": ["#9132A6", "#E13A62", "#EA3D15", "#EEA720", "#7DBC2D", "#099481", "#188ED6"],
        "inkline_slide_type": "process_flow",
        "needs_metaphor_image": False,
    },
    "funnel_ribbon": {
        "name": "Funnel/conversion ribbon",
        "best_for": ["data_integration", "M&A", "consolidation"],
        "n_items": 4,
        "layout": "4_input_ribbons_braiding_to_1_output",
        "palette_rule": "4_saturated_brand_colors",
        "example_palette": ["#EA3D15", "#EEA720", "#188ED6", "#4EB9C1"],
        "inkline_slide_type": "chart",
        "needs_metaphor_image": True,
    },
    "dual_donut": {
        "name": "Dual donut comparison",
        "best_for": ["before_after", "AB_test", "two_quarter"],
        "n_items": 2,
        "layout": "2_centred_rounded_cards",
        "palette_rule": "white_cards_colored_donuts",
        "example_palette": ["#FFFFFF", "#1E5A8A", "#7DBC2D", "#9132A6"],
        "inkline_slide_type": "comparison",
        "needs_metaphor_image": False,
    },
    "waffle": {
        "name": "Waffle / square-pie",
        "best_for": ["tight_pct_comparison", "time_allocation", "headcount_mix"],
        "n_items": 8,
        "layout": "vertical_stack_of_10x10_grids",
        "palette_rule": "single_hue_with_lighter_unfilled",
        "example_palette": ["#CC6666", "#E5A0A0"],
        "inkline_slide_type": "bar_chart",
        "needs_metaphor_image": False,
    },
    "metaphor_backdrop": {
        "name": "Visual metaphor backdrop (cover)",
        "best_for": ["cover", "section_divider", "ESG", "wellness"],
        "n_items": 1,
        "layout": "full_bleed_illustration",
        "palette_rule": "bright_cartoon",
        "example_palette": ["#A8D8FF", "#88C8EE", "#FFFFFF"],
        "inkline_slide_type": "title",
        "needs_metaphor_image": True,
    },
    "chart_row": {
        "name": "Generic chart row",
        "best_for": ["multi_chart_kpi_snapshot", "comparison_row"],
        "n_items": 4,
        "layout": "row_of_3_or_4_charts_with_caption_cards",
        "palette_rule": "2_or_3_chart_colors",
        "example_palette": ["#1E3A6E", "#EEA720", "#4EB9C1"],
        "inkline_slide_type": "chart_caption",
        "needs_metaphor_image": False,
    },
}


def list_archetypes() -> list[str]:
    """Return the names of all archetypes in this catalog."""
    return list(ARCHETYPES.keys())


def get_archetype_recipe(name: str) -> dict[str, Any]:
    """Return the structured recipe for a single archetype.

    Parameters
    ----------
    name : str
        One of the keys in ``ARCHETYPES`` (e.g., ``"iceberg"``, ``"pyramid"``).

    Returns
    -------
    dict
        The recipe with keys ``name``, ``best_for``, ``n_items``, ``layout``,
        ``palette_rule``, ``example_palette``, ``inkline_slide_type``,
        ``needs_metaphor_image``.

    Raises
    ------
    ValueError
        If the archetype name is unknown.
    """
    if name not in ARCHETYPES:
        raise ValueError(
            f"Unknown archetype '{name}'. "
            f"Available: {', '.join(ARCHETYPES)}"
        )
    return dict(ARCHETYPES[name])


def suggest_archetype(
    *,
    n_items: Optional[int] = None,
    intent: Optional[str] = None,
) -> list[str]:
    """Heuristic archetype suggestion based on item count and intent string.

    Parameters
    ----------
    n_items : int, optional
        How many peer items the user wants to show.
    intent : str, optional
        Free-form intent string. Matched against each archetype's ``best_for``
        tags via substring search.

    Returns
    -------
    list[str]
        Archetype names ordered by descending relevance. Empty if no match.
    """
    candidates = list(ARCHETYPES.items())
    if intent:
        intent_lower = intent.lower()
        candidates = [
            (k, v) for k, v in candidates
            if any(tag in intent_lower or intent_lower in tag for tag in v["best_for"])
        ]
    if n_items is not None:
        candidates = sorted(
            candidates,
            key=lambda kv: abs(kv[1]["n_items"] - n_items),
        )
    return [k for k, _ in candidates]


# ─── Local image catalog (optional) ───────────────────────────────────────────


def get_local_image_dir() -> Optional[Path]:
    """Return the local image catalog directory if configured, else None.

    Looks at the environment variable ``INKLINE_TEMPLATE_CATALOG_DIR``.
    """
    val = os.environ.get(LOCAL_IMAGE_DIR_ENV)
    if not val:
        return None
    p = Path(val)
    return p if p.is_dir() else None


def resolve_local_image(template_url: str) -> Optional[Path]:
    """Try to resolve a manifest image URL to a local file.

    The local catalog (when present) is laid out as
    ``$INKLINE_TEMPLATE_CATALOG_DIR/slidemodel_thumbs/<slug>/<filename.jpg>``
    or ``$INKLINE_TEMPLATE_CATALOG_DIR/genspark/professional/<slug>/page_NNN.png``.
    This helper performs a best-effort lookup using the URL's basename.
    """
    base = get_local_image_dir()
    if base is None:
        return None
    filename = template_url.rsplit("/", 1)[-1]
    matches = list(base.rglob(filename))
    return matches[0] if matches else None


__all__ = [
    "MANIFEST_REGISTRY",
    "ARCHETYPES",
    "LOCAL_IMAGE_DIR_ENV",
    "load_manifest",
    "find_templates",
    "list_archetypes",
    "get_archetype_recipe",
    "suggest_archetype",
    "get_local_image_dir",
    "resolve_local_image",
]
