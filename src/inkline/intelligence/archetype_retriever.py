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
    archetypes = retrieve_full_slide_candidates(
        role=role,
        slide_spec=slide_spec,
        deck_type=deck_type,
        reference_family=reference_family,
        top_k=top_k,
    )
    references = find_reference_slides(
        role=role,
        reference_family=reference_family,
        top_k=top_k,
    )
    return {
        "archetypes": archetypes,
        "reference_slides": references,
    }


__all__ = ["retrieve_archetypes_and_references"]
