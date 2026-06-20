"""Storyboard resolution, validation, and trace emission."""

from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

from inkline.intelligence.archetype_retriever import retrieve_archetypes_and_references
from inkline.intelligence.reference_catalog import load_reference_family
from inkline.intelligence.full_slide_archetypes import (
    KNOWN_SLIDE_ROLES,
    compile_slide_manifest,
    infer_slide_role,
)

STORYBOARD_SCHEMA_NAME = "storyboard"
STORYBOARD_SCHEMA_VERSION = 1
AUTHORING_TRACE_SCHEMA_NAME = "authoring_trace"
AUTHORING_TRACE_SCHEMA_VERSION = 1
DEFAULT_AUDIT_SETTINGS = {
    "title_scale_min_ratio": 1.25,
    "whitespace_margin_min_ratio": 0.02,
    "slide_warning_budget": 2,
    "deck_warning_budget": 8,
    "archetype_match_threshold": 0.60,
    "reference_family_advisory_threshold": 0.55,
}


def generate_slide_id(index: int, title: str, role: str) -> str:
    stem = re.sub(r"[^a-z0-9]+", "_", f"{role}_{title}".lower()).strip("_")
    stem = stem or f"slide_{index+1}"
    return f"s{index + 1:02d}_{stem[:40]}"


def _normalize_storyboard_slides(raw: Any) -> dict[str, dict[str, Any]]:
    if isinstance(raw, dict):
        return {str(k): dict(v) for k, v in raw.items() if isinstance(v, dict)}
    if isinstance(raw, list):
        normalized: dict[str, dict[str, Any]] = {}
        for idx, item in enumerate(raw):
            if isinstance(item, dict):
                key = str(item.get("slide_id") or item.get("index") or f"s{idx+1}")
                normalized[key] = dict(item)
        return normalized
    return {}


def _lookup_storyboard_entry(
    storyboard_slides: dict[str, dict[str, Any]],
    *,
    slide_index: int,
    explicit_slide_id: str = "",
    generated_slide_id: str = "",
) -> dict[str, Any]:
    candidates = [
        explicit_slide_id,
        generated_slide_id,
        str(slide_index + 1),
        f"s{slide_index+1}",
    ]
    for key in candidates:
        if key and key in storyboard_slides:
            return dict(storyboard_slides[key])
    prefix = f"s{slide_index + 1:02d}_"
    prefixed = [dict(value) for key, value in storyboard_slides.items() if key.startswith(prefix)]
    if len(prefixed) == 1:
        return prefixed[0]
    return {}


def _infer_key_message(slide: dict[str, Any], role: str) -> str:
    data = slide.get("data", {}) or {}
    for key in ("title", "headline", "tagline", "section"):
        if data.get(key):
            return str(data[key])
    return f"{role.replace('_', ' ').title()} message"


def _extract_explicit_overrides(slide: dict[str, Any]) -> dict[str, Any]:
    return {
        "role": slide.get("_slide_role") or slide.get("role"),
        "archetype": slide.get("_archetype") or slide.get("archetype"),
        "key_message": slide.get("_key_message") or slide.get("key_message"),
        "reference_family": slide.get("_reference_family") or slide.get("reference_family"),
    }


def _validate_declared_role(role: Any, *, source: str) -> str:
    value = str(role or "").strip()
    if value and value not in KNOWN_SLIDE_ROLES:
        allowed = ", ".join(sorted(KNOWN_SLIDE_ROLES))
        raise ValueError(f"Unknown slide role '{value}' from {source}. Allowed roles: {allowed}")
    return value


def _validate_reference_family(reference_family: Any, *, source: str) -> str:
    value = str(reference_family or "").strip()
    if not value:
        return ""
    try:
        load_reference_family(value)
    except FileNotFoundError as exc:
        raise ValueError(f"Unknown reference family '{value}' from {source}") from exc
    return value


def resolve_storyboard_spec(
    spec: dict[str, Any],
    *,
    source_name: str = "",
    deck_type: str = "investor",
    allow_inference: bool = False,
) -> dict[str, Any]:
    """Resolve one authoritative metadata view for a deck spec.

    This is the single validation/merge boundary. Downstream renderers and
    auditors should consume the resolved metadata only.
    """
    resolved = deepcopy(spec)
    slides = resolved.setdefault("slides", [])
    storyboard_root = resolved.get("storyboard", {}) or {}
    deck_storyboard = dict(storyboard_root.get("deck", {})) if isinstance(storyboard_root, dict) else {}
    embedded_storyboard_slides = _normalize_storyboard_slides(storyboard_root.get("slides") if isinstance(storyboard_root, dict) else {})
    reference_family = (
        resolved.get("reference_family")
        or deck_storyboard.get("reference_family")
        or ""
    )
    reference_family = _validate_reference_family(reference_family, source="deck metadata")
    storyboard_bundle = {
        "schema_name": STORYBOARD_SCHEMA_NAME,
        "schema_version": STORYBOARD_SCHEMA_VERSION,
        "deck": {
            "title": resolved.get("title", ""),
            "audience": resolved.get("audience", deck_storyboard.get("audience", "")),
            "objective": deck_storyboard.get("objective", ""),
            "thesis": deck_storyboard.get("thesis", ""),
            "reference_family": reference_family,
            "source_name": source_name,
        },
        "slides": [],
    }
    authoring_trace = {
        "schema_name": AUTHORING_TRACE_SCHEMA_NAME,
        "schema_version": AUTHORING_TRACE_SCHEMA_VERSION,
        "run_id": f"{Path(source_name).stem if source_name else 'memory'}::resolved",
        "deck_ref": source_name or resolved.get("title", ""),
        "defaults": deepcopy(DEFAULT_AUDIT_SETTINGS),
        "slides": [],
    }

    for idx, slide in enumerate(slides):
        data = slide.setdefault("data", {})
        explicit = _extract_explicit_overrides(slide)
        embedded_slide = slide.get("storyboard", {}) if isinstance(slide.get("storyboard"), dict) else {}
        embedded_slide = dict(embedded_slide)
        if explicit.get("role"):
            explicit["role"] = _validate_declared_role(explicit.get("role"), source="explicit slide metadata")
        if explicit.get("reference_family"):
            explicit["reference_family"] = _validate_reference_family(explicit.get("reference_family"), source="explicit slide metadata")
        if embedded_slide.get("role"):
            embedded_slide["role"] = _validate_declared_role(embedded_slide.get("role"), source="embedded slide storyboard")
        if embedded_slide.get("reference_family"):
            embedded_slide["reference_family"] = _validate_reference_family(embedded_slide.get("reference_family"), source="embedded slide storyboard")
        explicit_slide_id = str(
            slide.get("slide_id") or embedded_slide.get("slide_id") or ""
        )
        embedded_lookup_seed = _lookup_storyboard_entry(
            embedded_storyboard_slides,
            slide_index=idx,
            explicit_slide_id=explicit_slide_id,
        )
        provisional_role = (
            explicit.get("role")
            or embedded_slide.get("role")
            or embedded_lookup_seed.get("role")
            or infer_slide_role(slide)
        )
        slide_id = str(
            explicit_slide_id
            or generate_slide_id(
                idx,
                str(data.get("title", data.get("section", ""))),
                str(provisional_role),
            )
        )
        embedded_lookup = _lookup_storyboard_entry(
            embedded_storyboard_slides,
            slide_index=idx,
            explicit_slide_id=slide_id,
            generated_slide_id=slide_id,
        )
        if embedded_lookup.get("role"):
            embedded_lookup["role"] = _validate_declared_role(embedded_lookup.get("role"), source="deck storyboard")
        if embedded_lookup.get("reference_family"):
            embedded_lookup["reference_family"] = _validate_reference_family(embedded_lookup.get("reference_family"), source="deck storyboard")
        resolved_role = (
            explicit.get("role")
            or embedded_slide.get("role")
            or embedded_lookup.get("role")
            or provisional_role
        )
        retrieved = {"archetypes": [], "reference_slides": []}
        if allow_inference:
            retrieved = retrieve_archetypes_and_references(
                role=str(resolved_role),
                slide_spec=slide,
                deck_type=deck_type,
                reference_family=str(explicit.get("reference_family") or embedded_slide.get("reference_family") or embedded_lookup.get("reference_family") or reference_family or ""),
                top_k=3,
            )
        candidate_archetypes = retrieved["archetypes"]
        chosen_archetype = (
            explicit.get("archetype")
            or embedded_slide.get("archetype")
            or embedded_lookup.get("archetype")
            or (
                candidate_archetypes[0]["id"]
                if candidate_archetypes
                and candidate_archetypes[0]["score"] >= DEFAULT_AUDIT_SETTINGS["archetype_match_threshold"]
                else ""
            )
        )
        fallback_used = bool(candidate_archetypes) and bool(chosen_archetype) and not any(
            c["id"] == chosen_archetype
            and c["score"] >= DEFAULT_AUDIT_SETTINGS["archetype_match_threshold"]
            for c in candidate_archetypes
        )
        key_message = (
            explicit.get("key_message")
            or embedded_slide.get("key_message")
            or embedded_lookup.get("key_message")
            or _infer_key_message(slide, str(resolved_role))
        )
        slide_storyboard = {
            "slide_id": slide_id,
            "role": resolved_role,
            "archetype": chosen_archetype,
            "key_message": key_message,
            "reference_family": explicit.get("reference_family") or embedded_slide.get("reference_family") or embedded_lookup.get("reference_family") or reference_family,
        }
        compiled_manifest = compile_slide_manifest(
            slide,
            slide_id=slide_id,
            resolved_role=str(resolved_role),
            archetype_id=str(chosen_archetype),
        )
        slide["slide_id"] = slide_id
        slide["storyboard"] = slide_storyboard
        slide["compiled_manifest"] = compiled_manifest
        render_payload = compiled_manifest.get("render_payload", {})
        if isinstance(render_payload, dict):
            slide["slide_type"] = render_payload.get("slide_type", slide.get("slide_type"))
            if isinstance(render_payload.get("data"), dict):
                slide["data"] = deepcopy(render_payload["data"])
        storyboard_bundle["slides"].append(
            {
                "slide_id": slide_id,
                "index": idx + 1,
                "role": resolved_role,
                "archetype": chosen_archetype,
                "key_message": key_message,
                "reference_family": slide_storyboard["reference_family"],
                "fallback_used": fallback_used,
            }
        )
        authoring_trace["slides"].append(
            {
                "slide_id": slide_id,
                "chosen_archetype": chosen_archetype,
                "candidate_archetypes": candidate_archetypes,
                "reference_slides": retrieved["reference_slides"],
                "fallback_used": fallback_used,
                "resolved_metadata": slide_storyboard,
                "losing_values": {
                    "explicit": {k: v for k, v in explicit.items() if v and str(v) != str(slide_storyboard.get(k if k != "reference_family" else "reference_family", ""))},
                    "embedded": {k: v for k, v in embedded_slide.items() if v and str(v) != str(slide_storyboard.get(k, ""))},
                    "deck_storyboard": {k: v for k, v in embedded_lookup.items() if v and str(v) != str(slide_storyboard.get(k, ""))},
                },
            }
        )

    resolved["storyboard"] = storyboard_bundle
    resolved["_resolved_storyboard"] = storyboard_bundle
    resolved["_authoring_trace"] = authoring_trace
    resolved["_validation_settings"] = deepcopy(DEFAULT_AUDIT_SETTINGS)
    return resolved


def write_storyboard_artifacts(
    resolved_spec: dict[str, Any],
    *,
    output_dir: str | Path,
    stem: str = "deck",
) -> dict[str, Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    safe_stem = re.sub(r"[^a-zA-Z0-9._-]+", "_", stem).strip("._") or "deck"
    storyboard_path = output / f"{safe_stem}.storyboard.json"
    trace_path = output / f"{safe_stem}.authoring_trace.json"
    storyboard_path.write_text(json.dumps(resolved_spec.get("_resolved_storyboard", {}), indent=2), encoding="utf-8")
    trace_path.write_text(json.dumps(resolved_spec.get("_authoring_trace", {}), indent=2), encoding="utf-8")
    return {
        "storyboard_path": storyboard_path,
        "authoring_trace_path": trace_path,
    }


__all__ = [
    "AUTHORING_TRACE_SCHEMA_NAME",
    "AUTHORING_TRACE_SCHEMA_VERSION",
    "DEFAULT_AUDIT_SETTINGS",
    "STORYBOARD_SCHEMA_NAME",
    "STORYBOARD_SCHEMA_VERSION",
    "generate_slide_id",
    "resolve_storyboard_spec",
    "write_storyboard_artifacts",
]
