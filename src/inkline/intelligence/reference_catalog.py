"""Reference-family catalog helpers for local and packaged benchmark decks."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from inkline.intelligence.reference_schema import validate_reference_slide_manifest

PACKAGE_ROOT = Path(__file__).resolve().parent / "reference_catalog"
LOCAL_ROOT = Path("~/.config/inkline/reference_catalog").expanduser()
_FAMILY_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,127}$")


def get_catalog_roots() -> list[Path]:
    return [LOCAL_ROOT, PACKAGE_ROOT]


def validate_reference_family_id(family_id: str) -> str:
    value = str(family_id or "").strip()
    if not _FAMILY_ID_RE.fullmatch(value):
        raise ValueError(f"Invalid reference family id: {family_id!r}")
    return value


def _family_manifest_path(root: Path, family_id: str) -> Path:
    return root / validate_reference_family_id(family_id) / "reference_family_manifest.json"


def _family_dir(payload: dict[str, Any]) -> Path:
    root = Path(payload.get("_catalog_root", "")).expanduser().resolve()
    family_id = validate_reference_family_id(str(payload.get("reference_family_id", "")))
    return (root / family_id).resolve()


def _resolve_family_file(family_payload: dict[str, Any], rel_path: str) -> Path:
    candidate = Path(rel_path)
    if candidate.is_absolute():
        raise ValueError("Absolute reference family paths are not allowed")
    family_dir = _family_dir(family_payload)
    resolved = (family_dir / candidate).resolve()
    try:
        resolved.relative_to(family_dir)
    except ValueError as exc:
        raise ValueError(f"Reference family path escapes catalog root: {rel_path!r}") from exc
    return resolved


def sanitize_reference_family_for_mcp(payload: dict[str, Any]) -> dict[str, Any]:
    safe = {
        "schema_name": payload.get("schema_name", ""),
        "schema_version": payload.get("schema_version", 0),
        "reference_family_id": payload.get("reference_family_id", ""),
        "license_classification": payload.get("license_classification", ""),
        "ingestion_method": payload.get("ingestion_method", ""),
        "confidence_score": payload.get("confidence_score", 0),
        "version": payload.get("version", 0),
        "style_tokens": payload.get("style_tokens", {}),
        "notes": list(payload.get("notes", [])),
        "slides": [],
    }
    for slide in payload.get("slides", []):
        safe["slides"].append(
            {
                "reference_slide_id": slide.get("reference_slide_id", ""),
                "role": slide.get("role", ""),
                "archetype_candidate": slide.get("archetype_candidate", ""),
            }
        )
    return safe


def sanitize_reference_slide_for_mcp(payload: dict[str, Any]) -> dict[str, Any]:
    payload = validate_reference_slide_manifest(payload)
    safe = {
        "reference_slide_id": payload.get("reference_slide_id", ""),
        "reference_family_id": payload.get("reference_family_id", payload.get("_reference_family_manifest", "")),
        "source_slide_index": payload.get("source_slide_index", 0),
        "role": payload.get("role", ""),
        "composition_family": payload.get("composition_family", ""),
        "density_class": payload.get("density_class", ""),
        "style_tokens": payload.get("style_tokens", {}),
        "text_blocks": payload.get("text_blocks", []),
        "normalized_geometry": payload.get("normalized_geometry", []),
    }
    for key in ("preview_path", "manifest_path", "_catalog_root", "source_path"):
        safe.pop(key, None)
    return safe


def list_reference_families() -> list[dict[str, Any]]:
    seen: dict[str, dict[str, Any]] = {}
    for root in get_catalog_roots():
        if not root.exists():
            continue
        for manifest in sorted(root.glob("*/reference_family_manifest.json")):
            try:
                payload = json.loads(manifest.read_text(encoding="utf-8"))
            except Exception:
                continue
            family_id = str(payload.get("reference_family_id", manifest.parent.name))
            try:
                family_id = validate_reference_family_id(family_id)
            except ValueError:
                continue
            payload.setdefault("reference_family_id", family_id)
            payload["_catalog_root"] = str(root)
            if family_id not in seen or root == LOCAL_ROOT:
                seen[family_id] = payload
    return [seen[key] for key in sorted(seen)]


def load_reference_family(reference_family_id: str) -> dict[str, Any]:
    reference_family_id = validate_reference_family_id(reference_family_id)
    for root in get_catalog_roots():
        path = _family_manifest_path(root, reference_family_id)
        if path.exists():
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["_catalog_root"] = str(root)
            return payload
    raise FileNotFoundError(reference_family_id)


def load_reference_slide(reference_slide_id: str) -> dict[str, Any]:
    for family in list_reference_families():
        for slide in family.get("slides", []):
            if slide.get("reference_slide_id") == reference_slide_id:
                manifest_path = slide.get("manifest_path", "")
                if manifest_path:
                    payload = json.loads(
                        _resolve_family_file(family, manifest_path).read_text(encoding="utf-8")
                    )
                    payload["reference_family_id"] = family.get("reference_family_id", "")
                    payload["_reference_family_manifest"] = family.get("reference_family_id", "")
                    return validate_reference_slide_manifest(payload)
                payload = dict(slide)
                payload["reference_family_id"] = family.get("reference_family_id", "")
                payload["_reference_family_manifest"] = family.get("reference_family_id", "")
                return validate_reference_slide_manifest(payload)
    raise FileNotFoundError(reference_slide_id)


def find_reference_slides(
    *,
    role: str,
    reference_family: str = "",
    deck_type: str = "investor",
    desired_density_class: str = "",
    desired_composition_family: str = "",
    style_tokens: dict[str, Any] | None = None,
    top_k: int = 3,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    if reference_family:
        try:
            families = [load_reference_family(reference_family)]
        except FileNotFoundError:
            families = []
    else:
        families = list_reference_families()
    desired_style_tokens = style_tokens or {}
    for family in families:
        for slide in family.get("slides", []):
            slide_role = slide.get("role") or slide.get("role_override") or ""
            role_score = 1.0 if slide_role == role else 0.0
            if role_score <= 0:
                continue
            archetype_candidate = str(slide.get("archetype_candidate", ""))
            density_class = str(slide.get("density_class", "")).strip()
            composition_family = str(slide.get("composition_family", "")).strip()
            benchmark_quality = float(slide.get("benchmark_quality_weight", family.get("confidence_score", 0.0)) or 0.0)
            curator_confidence = 1.0 if slide.get("strong_exemplar") else 0.5 if slide.get("usable_for_retrieval", True) else 0.0
            style_match = 0.0
            family_style_tokens = family.get("style_tokens", {}) if isinstance(family.get("style_tokens"), dict) else {}
            if desired_style_tokens:
                style_match = 1.0 if desired_style_tokens.get("typography_treatment_class") == family_style_tokens.get("typography_treatment_class") else 0.5
            else:
                style_match = 0.5
            density_match = 1.0 if desired_density_class and density_class == desired_density_class else 0.6 if not desired_density_class else 0.0
            composition_match = 1.0 if desired_composition_family and composition_family == desired_composition_family else 0.6 if not desired_composition_family else 0.0
            deck_match = 1.0 if deck_type in {"investor", "consulting", "board"} else 0.0
            score_components = {
                "role_match": role_score,
                "content_schema_match": 1.0 if archetype_candidate else 0.0,
                "deck_type_match": deck_match,
                "density_match": density_match,
                "composition_family_match": composition_match,
                "style_token_match": style_match,
                "benchmark_quality": benchmark_quality,
                "curator_confidence": curator_confidence,
            }
            score = round(
                (0.28 * role_score)
                + (0.18 * score_components["content_schema_match"])
                + (0.10 * deck_match)
                + (0.08 * density_match)
                + (0.14 * composition_match)
                + (0.10 * style_match)
                + (0.07 * benchmark_quality)
                + (0.05 * curator_confidence),
                4,
            )
            if slide.get("do_not_imitate"):
                score = min(score, 0.29)
            if not slide.get("usable_for_retrieval", True):
                score = min(score, 0.39)
            results.append(
                {
                    "reference_family_id": family.get("reference_family_id", ""),
                    "reference_slide_id": slide.get("reference_slide_id", ""),
                    "role": slide_role,
                    "archetype_candidate": archetype_candidate,
                    "composition_family": composition_family,
                    "density_class": density_class,
                    "benchmark_quality_weight": benchmark_quality,
                    "curator_confidence": curator_confidence,
                    "score_components": score_components,
                    "score": score,
                    "qualified": score >= 0.62,
                    "advisory_only": 0.45 <= score < 0.62,
                    "do_not_use": score < 0.45,
                }
            )
    results.sort(key=lambda item: (-item["score"], item["do_not_use"], item["reference_slide_id"]))
    return results[:top_k]


__all__ = [
    "LOCAL_ROOT",
    "PACKAGE_ROOT",
    "find_reference_slides",
    "get_catalog_roots",
    "list_reference_families",
    "load_reference_family",
    "load_reference_slide",
    "sanitize_reference_family_for_mcp",
    "sanitize_reference_slide_for_mcp",
    "validate_reference_family_id",
]
