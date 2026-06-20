"""Full-slide archetype registry and compiler for reference-driven authoring.

This module introduces semantic full-slide archetypes that compile down to
renderer-native slide payloads. The renderer never interprets archetypes
directly; it only receives compiled manifests with native slide specs.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any

SCHEMA_NAME = "full_slide_archetype"
SCHEMA_VERSION = 1
COMPILED_SCHEMA_NAME = "compiled_slide_manifest"
COMPILED_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class FullSlideArchetype:
    id: str
    functional_roles: tuple[str, ...]
    deck_types: tuple[str, ...]
    content_schema_required: tuple[str, ...]
    content_schema_optional: tuple[str, ...]
    visual_intent: dict[str, str]
    compile_target_kind: str
    compile_layout_id: str
    compile_template_id: str | None
    benchmark_refs: tuple[dict[str, str], ...]
    anti_patterns: tuple[str, ...]
    audit_checks: tuple[str, ...]

    def to_manifest(self) -> dict[str, Any]:
        return {
            "schema_name": SCHEMA_NAME,
            "schema_version": SCHEMA_VERSION,
            "id": self.id,
            "functional_roles": list(self.functional_roles),
            "deck_types": list(self.deck_types),
            "content_schema": {
                "required": list(self.content_schema_required),
                "optional": list(self.content_schema_optional),
            },
            "visual_intent": deepcopy(self.visual_intent),
            "compile_targets": {
                "kind": self.compile_target_kind,
                "layout_id": self.compile_layout_id,
                "template_id": self.compile_template_id,
            },
            "benchmark_refs": [dict(item) for item in self.benchmark_refs],
            "anti_patterns": list(self.anti_patterns),
            "audit_checks": list(self.audit_checks),
        }


_ARCHETYPES: dict[str, FullSlideArchetype] = {
    "cover_hero_photo_left_text_block": FullSlideArchetype(
        id="cover_hero_photo_left_text_block",
        functional_roles=("cover",),
        deck_types=("investor", "consulting", "board"),
        content_schema_required=("company",),
        content_schema_optional=("tagline", "subtitle", "date", "background_image"),
        visual_intent={"hero": "photo", "supporting": "title_block", "tone": "institutional_confident"},
        compile_target_kind="layout",
        compile_layout_id="title",
        compile_template_id=None,
        benchmark_refs=(),
        anti_patterns=("plain_title_without_hero", "small_cover_title"),
        audit_checks=("hero presence", "large title block"),
    ),
    "thesis_three_pillar_cards": FullSlideArchetype(
        id="thesis_three_pillar_cards",
        functional_roles=("thesis", "proposition"),
        deck_types=("investor", "consulting", "board"),
        content_schema_required=("cards",),
        content_schema_optional=("section", "footnote"),
        visual_intent={"hero": "three pillars", "supporting": "short evidence", "tone": "strategic"},
        compile_target_kind="layout",
        compile_layout_id="three_card",
        compile_template_id=None,
        benchmark_refs=(),
        anti_patterns=("equal_weight_bullet_blocks",),
        audit_checks=("three cards", "message-led titles"),
    ),
    "numbered_horizontal_proposition_rail": FullSlideArchetype(
        id="numbered_horizontal_proposition_rail",
        functional_roles=("proposition", "process"),
        deck_types=("investor", "consulting"),
        content_schema_required=("steps",),
        content_schema_optional=("section", "footnote"),
        visual_intent={"hero": "numbered rail", "supporting": "support notes", "tone": "assertive"},
        compile_target_kind="layout",
        compile_layout_id="process_flow",
        compile_template_id=None,
        benchmark_refs=(),
        anti_patterns=("plain_bullets_for_steps",),
        audit_checks=("numbered steps", "sequential emphasis"),
    ),
    "executive_bio_cards_centered": FullSlideArchetype(
        id="executive_bio_cards_centered",
        functional_roles=("team", "people"),
        deck_types=("investor", "consulting", "board"),
        content_schema_required=("members",),
        content_schema_optional=("subheadline", "footer_note"),
        visual_intent={"hero": "centered portraits", "supporting": "name_role", "tone": "institutional_human"},
        compile_target_kind="layout",
        compile_layout_id="team_grid",
        compile_template_id=None,
        benchmark_refs=(),
        anti_patterns=("generic_staff_grid", "small_headshots"),
        audit_checks=("portrait dominance", "name hierarchy", "consistent card sizing"),
    ),
    "firepower_two_zone_summary": FullSlideArchetype(
        id="firepower_two_zone_summary",
        functional_roles=("economics", "capital", "size_of_prize"),
        deck_types=("investor", "consulting"),
        content_schema_required=("stats",),
        content_schema_optional=("bullets", "footnote"),
        visual_intent={"hero": "two zone", "supporting": "support bullets", "tone": "commercial"},
        compile_target_kind="layout",
        compile_layout_id="kpi_strip",
        compile_template_id=None,
        benchmark_refs=(),
        anti_patterns=("dense_numbers_without_hierarchy",),
        audit_checks=("hero metrics", "clear two-zone split"),
    ),
    "banker_vertical_process_spine": FullSlideArchetype(
        id="banker_vertical_process_spine",
        functional_roles=("timeline", "process", "execution_plan"),
        deck_types=("investor", "consulting", "board"),
        content_schema_required=("milestones",),
        content_schema_optional=("footnote",),
        visual_intent={"hero": "vertical spine", "supporting": "milestone cards", "tone": "transactional"},
        compile_target_kind="layout",
        compile_layout_id="timeline",
        compile_template_id=None,
        benchmark_refs=(),
        anti_patterns=("text_wall_process_slide",),
        audit_checks=("milestone clarity", "chronological rhythm"),
    ),
    "appendix_ranked_table_card": FullSlideArchetype(
        id="appendix_ranked_table_card",
        functional_roles=("appendix_ranked_table", "pipeline", "matrix"),
        deck_types=("investor", "consulting", "board"),
        content_schema_required=("rows",),
        content_schema_optional=("headers", "footnote"),
        visual_intent={"hero": "structured evidence", "supporting": "ranked details", "tone": "institutional_dense"},
        compile_target_kind="layout",
        compile_layout_id="table",
        compile_template_id=None,
        benchmark_refs=(),
        anti_patterns=("unstyled_data_dump",),
        audit_checks=("header hierarchy", "row consistency"),
    ),
    "market_map_reference_exhibit": FullSlideArchetype(
        id="market_map_reference_exhibit",
        functional_roles=("market_map", "map", "asset_overview"),
        deck_types=("investor", "consulting"),
        content_schema_required=("image_path",),
        content_schema_optional=("caption", "footnote"),
        visual_intent={"hero": "map exhibit", "supporting": "light framing", "tone": "evidence_led"},
        compile_target_kind="layout",
        compile_layout_id="chart_caption",
        compile_template_id=None,
        benchmark_refs=(),
        anti_patterns=("rebuilding_strong_reference_map_badly",),
        audit_checks=("map dominance", "minimal clutter"),
    ),
}

_FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "stats": ("stats", "kpis"),
    "stats[]": ("stats", "kpis"),
    "image_path": ("image_path", "chart_path", "graphic_path", "figure_path", "chart_request"),
}

ROLE_TO_DEFAULT_ARCHETYPE: dict[str, str] = {
    "cover": "cover_hero_photo_left_text_block",
    "thesis": "thesis_three_pillar_cards",
    "proposition": "numbered_horizontal_proposition_rail",
    "team": "executive_bio_cards_centered",
    "people": "executive_bio_cards_centered",
    "economics": "firepower_two_zone_summary",
    "size_of_prize": "firepower_two_zone_summary",
    "timeline": "banker_vertical_process_spine",
    "process": "banker_vertical_process_spine",
    "execution_plan": "banker_vertical_process_spine",
    "appendix_ranked_table": "appendix_ranked_table_card",
    "pipeline": "appendix_ranked_table_card",
    "market_map": "market_map_reference_exhibit",
    "map": "market_map_reference_exhibit",
    "content": "",
}
KNOWN_SLIDE_ROLES = frozenset(ROLE_TO_DEFAULT_ARCHETYPE) | frozenset(
    role for archetype in _ARCHETYPES.values() for role in archetype.functional_roles
)


def list_full_slide_archetypes() -> list[dict[str, Any]]:
    return [item.to_manifest() for item in _ARCHETYPES.values()]


def get_full_slide_archetype(archetype_id: str) -> dict[str, Any]:
    archetype = _ARCHETYPES.get(archetype_id)
    if not archetype:
        raise KeyError(archetype_id)
    return archetype.to_manifest()


def infer_slide_role(slide_spec: dict[str, Any]) -> str:
    storyboard = slide_spec.get("storyboard", {}) or {}
    if isinstance(storyboard, dict) and storyboard.get("role"):
        return str(storyboard["role"])
    slide_type = str(slide_spec.get("slide_type", "content"))
    return {
        "title": "cover",
        "team_grid": "team",
        "timeline": "timeline",
        "process_flow": "process",
        "table": "appendix_ranked_table",
        "chart_caption": "market_map",
        "chart": "market_map",
        "dashboard": "economics",
        "kpi_strip": "economics",
        "stat": "economics",
        "three_card": "thesis",
        "four_card": "proposition",
    }.get(slide_type, "content")


def _has_required_fields(slide_spec: dict[str, Any], archetype: FullSlideArchetype) -> bool:
    data = slide_spec.get("data", {}) or {}
    slide_type = str(slide_spec.get("slide_type", ""))
    for field in archetype.content_schema_required:
        if field == "image_path" and slide_type in {"chart", "chart_caption"}:
            continue
        aliases = _FIELD_ALIASES.get(field, (field[:-2],) if field.endswith("[]") else (field,))
        if not any(data.get(alias) for alias in aliases):
            return False
    return True


def _missing_required_fields(slide_spec: dict[str, Any], archetype: FullSlideArchetype) -> list[str]:
    data = slide_spec.get("data", {}) or {}
    slide_type = str(slide_spec.get("slide_type", ""))
    missing: list[str] = []
    for field in archetype.content_schema_required:
        if field == "image_path" and slide_type in {"chart", "chart_caption"}:
            continue
        aliases = _FIELD_ALIASES.get(field, (field[:-2],) if field.endswith("[]") else (field,))
        if not any(data.get(alias) for alias in aliases):
            missing.append(field)
    return missing


def retrieve_full_slide_candidates(
    *,
    role: str,
    slide_spec: dict[str, Any],
    deck_type: str = "investor",
    reference_family: str = "",
    top_k: int = 3,
) -> list[dict[str, Any]]:
    """Return ranked archetype candidates using simple metadata heuristics."""
    resolved_role = role or infer_slide_role(slide_spec)
    reference_family_declared = bool(reference_family)
    candidates: list[dict[str, Any]] = []
    for archetype in _ARCHETYPES.values():
        score = 0.0
        if role in archetype.functional_roles:
            score += 0.55
        elif resolved_role in archetype.functional_roles:
            score += 0.35
        if deck_type in archetype.deck_types:
            score += 0.15
        schema_match = _has_required_fields(slide_spec, archetype)
        if schema_match:
            score += 0.20
        else:
            score -= 0.15
        benchmark_family_match = bool(
            reference_family
            and any(ref.get("ref_family") == reference_family for ref in archetype.benchmark_refs)
        )
        if benchmark_family_match:
            score += 0.10
        elif reference_family_declared and role in archetype.functional_roles and schema_match:
            # A declared reference family should still bias ranking toward
            # archetypes that can express the requested role cleanly, even
            # when the archetype is built-in and has no explicit benchmark tags.
            score += 0.08
        if score > 0:
            candidates.append(
                {
                    "id": archetype.id,
                    "score": round(score, 4),
                    "role_match": role in archetype.functional_roles,
                    "content_schema_match": schema_match,
                    "reference_family_bonus_applied": benchmark_family_match
                    or (
                        reference_family_declared
                        and role in archetype.functional_roles
                        and schema_match
                    ),
                }
            )
    candidates.sort(key=lambda item: (-item["score"], item["id"]))
    return candidates[:top_k]


def compile_slide_manifest(
    slide_spec: dict[str, Any],
    *,
    slide_id: str,
    resolved_role: str,
    archetype_id: str,
) -> dict[str, Any]:
    archetype = _ARCHETYPES.get(archetype_id) if archetype_id else None
    requested_slide_type = str(slide_spec.get("slide_type") or "")
    if archetype_id and not archetype:
        raise ValueError(f"Unknown archetype '{archetype_id}'")
    if not archetype:
        return {
            "schema_name": COMPILED_SCHEMA_NAME,
            "schema_version": COMPILED_SCHEMA_VERSION,
            "slide_id": slide_id,
            "source_archetype": "",
            "resolved_role": resolved_role,
            "requested_slide_type": requested_slide_type,
            "compile_target": {
                "kind": "layout",
                "layout_id": requested_slide_type or "content",
                "template_id": None,
            },
            "render_payload": {
                "slide_type": requested_slide_type or "content",
                "data": deepcopy(slide_spec.get("data", {})),
            },
            "parity_requirements": {
                "pdf_visual_parity": "required",
                "pptx_visual_parity": "required",
                "pptx_native_editability": "required",
            },
            "pptx_editability_exceptions": [],
        }
    missing_required = _missing_required_fields(slide_spec, archetype)
    if missing_required:
        raise ValueError(
            f"Archetype '{archetype_id}' missing required fields: {', '.join(missing_required)}"
        )
    if resolved_role and resolved_role not in archetype.functional_roles:
        raise ValueError(
            f"Archetype '{archetype_id}' is incompatible with resolved role '{resolved_role}'"
        )
    render_payload = {
        "slide_type": archetype.compile_layout_id,
        "data": deepcopy(slide_spec.get("data", {})),
    }
    compile_target = {
        "kind": archetype.compile_target_kind,
        "layout_id": archetype.compile_layout_id,
        "template_id": archetype.compile_template_id,
    }
    exceptions: list[str] = []
    data = render_payload["data"]
    if any(data.get(k) for k in ("image_path", "background_image", "logo_path")):
        exceptions.append("intentional_raster_asset")
    manifest = {
        "schema_name": COMPILED_SCHEMA_NAME,
        "schema_version": COMPILED_SCHEMA_VERSION,
        "slide_id": slide_id,
        "source_archetype": archetype_id,
        "resolved_role": resolved_role,
        "requested_slide_type": requested_slide_type,
        "compile_target": compile_target,
        "render_payload": render_payload,
        "parity_requirements": {
            "pdf_visual_parity": "required",
            "pptx_visual_parity": "required",
            "pptx_native_editability": "required" if not exceptions else "required_with_exceptions",
        },
        "pptx_editability_exceptions": exceptions,
    }
    return manifest


def materialize_compiled_slide_spec(slide_spec: dict[str, Any]) -> dict[str, Any]:
    """Return the effective slide spec that downstream renderers should consume."""
    materialized = deepcopy(slide_spec)
    manifest = materialized.get("compiled_manifest", {}) or {}
    render_payload = manifest.get("render_payload", {}) if isinstance(manifest, dict) else {}
    if isinstance(render_payload, dict):
        slide_type = render_payload.get("slide_type")
        data = render_payload.get("data")
        if slide_type:
            materialized["slide_type"] = slide_type
        if isinstance(data, dict):
            materialized["data"] = deepcopy(data)
    return materialized


__all__ = [
    "SCHEMA_NAME",
    "SCHEMA_VERSION",
    "COMPILED_SCHEMA_NAME",
    "COMPILED_SCHEMA_VERSION",
    "KNOWN_SLIDE_ROLES",
    "ROLE_TO_DEFAULT_ARCHETYPE",
    "compile_slide_manifest",
    "get_full_slide_archetype",
    "infer_slide_role",
    "list_full_slide_archetypes",
    "materialize_compiled_slide_spec",
    "retrieve_full_slide_candidates",
]
