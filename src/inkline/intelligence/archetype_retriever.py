"""Heuristic retrieval helpers for full-slide archetypes and references."""

from __future__ import annotations

from typing import Any

from inkline.intelligence.full_slide_archetypes import retrieve_full_slide_candidates
from inkline.intelligence.reference_catalog import find_reference_slides


def retrieve_archetypes_and_references(
    *,
    role: str,
    slide_spec: dict[str, Any],
    deck_type: str = "investor",
    reference_family: str = "",
    top_k: int = 3,
) -> dict[str, Any]:
    data = slide_spec.get("data", {}) if isinstance(slide_spec.get("data"), dict) else {}
    desired_density_class = "high" if data.get("rows") else "medium" if any(data.get(key) for key in ("cards", "members", "stats", "steps")) else "low"
    desired_composition_family = "people_profiles" if role in {"team", "people", "key_people"} else "timeline_spine" if role in {"timeline", "process", "roadshow"} else "dense_table" if role in {"pipeline", "appendix_ranked_table"} else "two_zone_summary" if role in {"economics", "size_of_prize"} else ""
    references = find_reference_slides(
        role=role,
        reference_family=reference_family,
        deck_type=deck_type,
        desired_density_class=desired_density_class,
        desired_composition_family=desired_composition_family,
        style_tokens={"typography_treatment_class": str((slide_spec.get("storyboard", {}) or {}).get("hero_kind", ""))},
        top_k=top_k,
    )
    reference_signals = next((item for item in references if not item.get("do_not_use")), {})
    archetypes = retrieve_full_slide_candidates(
        role=role,
        slide_spec=slide_spec,
        deck_type=deck_type,
        reference_family=reference_family,
        reference_signals=reference_signals,
        top_k=top_k,
    )
    return {
        "archetypes": archetypes,
        "reference_slides": references,
        "reference_signals": reference_signals,
    }


__all__ = ["retrieve_archetypes_and_references"]
