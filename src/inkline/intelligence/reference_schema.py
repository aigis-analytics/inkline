"""Shared manifest schemas and validators for reference-driven slide systems."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

REFERENCE_SLIDE_SCHEMA_NAME = "reference_slide_manifest"
REFERENCE_SLIDE_SCHEMA_VERSION = 2
FULL_SLIDE_ARCHETYPE_SCHEMA_NAME = "full_slide_archetype"
FULL_SLIDE_ARCHETYPE_SCHEMA_VERSION = 2
COMPILED_SLIDE_SCHEMA_NAME = "compiled_slide_manifest"
COMPILED_SLIDE_SCHEMA_VERSION = 2
BENCHMARK_AUDIT_SCHEMA_NAME = "benchmark_audit"
BENCHMARK_AUDIT_SCHEMA_VERSION = 1


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _as_str_list(value: Any) -> list[str]:
    return [str(item) for item in _as_list(value) if str(item).strip()]


def _as_dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _normalized_content_slots(value: Any) -> list[dict[str, Any]]:
    slots: list[dict[str, Any]] = []
    for item in _as_list(value):
        if isinstance(item, dict):
            slot = {
                "name": str(item.get("name", "")).strip(),
                "kind": str(item.get("kind", "")).strip(),
                "required": bool(item.get("required", False)),
                "count": int(item.get("count", 0) or 0),
            }
            if slot["name"]:
                slots.append(slot)
        elif str(item).strip():
            slots.append({"name": str(item).strip(), "kind": "", "required": False, "count": 0})
    return slots


def validate_reference_slide_manifest(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize legacy reference-slide manifests to the v2 schema."""
    raw = deepcopy(payload)
    role = str(raw.get("role") or raw.get("slide_role") or "").strip()
    composition_family = str(raw.get("composition_family") or "").strip() or "generic_canvas"
    style_tokens = _as_dict(raw.get("style_tokens"))
    normalized_geometry = _as_list(raw.get("normalized_geometry"))
    text_blocks = _as_list(raw.get("text_blocks"))
    zone_map = _as_dict(raw.get("zone_map"))
    content_slots = _normalized_content_slots(raw.get("content_slots"))
    if not content_slots and text_blocks:
        content_slots = [{"name": "text_blocks", "kind": "text", "required": False, "count": len(text_blocks)}]
    return {
        "schema_name": REFERENCE_SLIDE_SCHEMA_NAME,
        "schema_version": REFERENCE_SLIDE_SCHEMA_VERSION,
        "reference_slide_id": str(raw.get("reference_slide_id", "")).strip(),
        "reference_family_id": str(raw.get("reference_family_id", raw.get("_reference_family_manifest", ""))).strip(),
        "source_slide_index": int(raw.get("source_slide_index", 0) or 0),
        "role": role,
        "composition_family": composition_family,
        "density_class": str(raw.get("density_class") or "medium").strip(),
        "style_tokens": style_tokens,
        "zone_map": zone_map,
        "content_slots": content_slots,
        "usable_for_retrieval": bool(raw.get("usable_for_retrieval", True)),
        "archetype_tag": str(raw.get("archetype_tag") or raw.get("archetype_candidate") or "").strip(),
        "hero_kind": str(raw.get("hero_kind") or "").strip(),
        "evidence_kind": str(raw.get("evidence_kind") or "").strip(),
        "benchmark_quality_weight": float(raw.get("benchmark_quality_weight", raw.get("confidence_score", 1.0)) or 0.0),
        "strong_exemplar": bool(raw.get("strong_exemplar", False)),
        "do_not_imitate": bool(raw.get("do_not_imitate", False)),
        "preview_path": str(raw.get("preview_path", "")).strip(),
        "curation_notes": _as_str_list(raw.get("curation_notes") or raw.get("notes")),
        "normalized_geometry": normalized_geometry,
        "text_blocks": text_blocks,
    }


def validate_full_slide_archetype(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize full-slide archetype manifests to the v2 schema."""
    raw = deepcopy(payload)
    content_schema = _as_dict(raw.get("content_schema"))
    compile_targets = _as_dict(raw.get("compile_targets"))
    variants = _as_list(raw.get("compile_variants"))
    if not variants:
        variants = [
            {
                "variant_id": str(compile_targets.get("layout_id") or compile_targets.get("kind") or "default"),
                "compile_target": deepcopy(compile_targets),
                "builder_recipe_id": "",
                "benchmark_tokens": {},
                "editable_pptx_supported": True,
                "fallback_policy": "fail_fast",
            }
        ]
    normalized_variants: list[dict[str, Any]] = []
    for item in variants:
        if not isinstance(item, dict):
            continue
        normalized_variants.append(
            {
                "variant_id": str(item.get("variant_id") or item.get("id") or "default").strip(),
                "compile_target": _as_dict(item.get("compile_target") or compile_targets),
                "builder_recipe_id": str(item.get("builder_recipe_id", "")).strip(),
                "benchmark_tokens": _as_dict(item.get("benchmark_tokens")),
                "editable_pptx_supported": bool(item.get("editable_pptx_supported", True)),
                "fallback_policy": str(item.get("fallback_policy") or "fail_fast").strip(),
            }
        )
    return {
        "schema_name": FULL_SLIDE_ARCHETYPE_SCHEMA_NAME,
        "schema_version": FULL_SLIDE_ARCHETYPE_SCHEMA_VERSION,
        "id": str(raw.get("id", "")).strip(),
        "functional_roles": _as_str_list(raw.get("functional_roles")),
        "deck_types": _as_str_list(raw.get("deck_types")),
        "content_schema": {
            "required": _as_str_list(content_schema.get("required")),
            "optional": _as_str_list(content_schema.get("optional")),
        },
        "visual_intent": _as_dict(raw.get("visual_intent")),
        "compile_targets": compile_targets,
        "compile_variants": normalized_variants,
        "density_class": str(raw.get("density_class") or "medium").strip(),
        "allowed_primitives": _as_str_list(raw.get("allowed_primitives")),
        "audit_checks": _as_str_list(raw.get("audit_checks")),
        "benchmark_refs": _as_list(raw.get("benchmark_refs")),
        "pptx_editability_policy": str(raw.get("pptx_editability_policy") or "native_required").strip(),
        "anti_patterns": _as_str_list(raw.get("anti_patterns")),
    }


def validate_compiled_slide_manifest(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize compiled slide manifests to the v2 schema."""
    raw = deepcopy(payload)
    return {
        "schema_name": COMPILED_SLIDE_SCHEMA_NAME,
        "schema_version": COMPILED_SLIDE_SCHEMA_VERSION,
        "slide_id": str(raw.get("slide_id", "")).strip(),
        "source_archetype": str(raw.get("source_archetype", "")).strip(),
        "source_reference_family": str(raw.get("source_reference_family", "")).strip(),
        "source_reference_slide_ids": _as_str_list(raw.get("source_reference_slide_ids")),
        "compile_target": _as_dict(raw.get("compile_target")),
        "variant_id": str(raw.get("variant_id") or "default").strip(),
        "builder_recipe_id": str(raw.get("builder_recipe_id", "")).strip(),
        "benchmark_tokens_applied": _as_dict(raw.get("benchmark_tokens_applied")),
        "render_payload": _as_dict(raw.get("render_payload")),
        "parity_requirements": _as_dict(raw.get("parity_requirements")),
        "pptx_editability_exceptions": _as_str_list(raw.get("pptx_editability_exceptions")),
        "resolved_role": str(raw.get("resolved_role", "")).strip(),
        "requested_slide_type": str(raw.get("requested_slide_type", "")).strip(),
    }


def validate_benchmark_audit(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize benchmark-aware deck audit payloads."""
    raw = deepcopy(payload)
    slides: list[dict[str, Any]] = []
    for item in _as_list(raw.get("slides")):
        if not isinstance(item, dict):
            continue
        slides.append(
            {
                "slide_id": str(item.get("slide_id", "")).strip(),
                "slide_index": int(item.get("slide_index", item.get("index", 0)) or 0),
                "hard_render": _as_dict(item.get("hard_render")),
                "archetype_compliance": _as_dict(item.get("archetype_compliance")),
                "benchmark_alignment": _as_dict(item.get("benchmark_alignment")),
                "message_delivery": _as_dict(item.get("message_delivery")),
                "required_fix": str(item.get("required_fix", "")).strip(),
                "verdict": str(item.get("verdict", "")).strip(),
            }
        )
    return {
        "schema_name": BENCHMARK_AUDIT_SCHEMA_NAME,
        "schema_version": BENCHMARK_AUDIT_SCHEMA_VERSION,
        "engineering_pass": bool(raw.get("engineering_pass", False)),
        "design_pass": bool(raw.get("design_pass", False)),
        "benchmark_alignment_pass": bool(raw.get("benchmark_alignment_pass", False)),
        "message_pass": bool(raw.get("message_pass", False)),
        "ship_recommendation": str(raw.get("ship_recommendation", "")).strip(),
        "slides": slides,
    }


__all__ = [
    "BENCHMARK_AUDIT_SCHEMA_NAME",
    "BENCHMARK_AUDIT_SCHEMA_VERSION",
    "COMPILED_SLIDE_SCHEMA_NAME",
    "COMPILED_SLIDE_SCHEMA_VERSION",
    "FULL_SLIDE_ARCHETYPE_SCHEMA_NAME",
    "FULL_SLIDE_ARCHETYPE_SCHEMA_VERSION",
    "REFERENCE_SLIDE_SCHEMA_NAME",
    "REFERENCE_SLIDE_SCHEMA_VERSION",
    "validate_benchmark_audit",
    "validate_compiled_slide_manifest",
    "validate_full_slide_archetype",
    "validate_reference_slide_manifest",
]
