"""Reference-family catalog helpers for local and packaged benchmark decks."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

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
    safe = {
        "reference_slide_id": payload.get("reference_slide_id", ""),
        "reference_family_id": payload.get("reference_family_id", payload.get("_reference_family_manifest", "")),
        "source_slide_index": payload.get("source_slide_index", 0),
        "confidence_score": payload.get("confidence_score", 0),
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
                    return payload
                payload = dict(slide)
                payload["reference_family_id"] = family.get("reference_family_id", "")
                payload["_reference_family_manifest"] = family.get("reference_family_id", "")
                return payload
    raise FileNotFoundError(reference_slide_id)


def find_reference_slides(*, role: str, reference_family: str = "", top_k: int = 3) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    if reference_family:
        try:
            families = [load_reference_family(reference_family)]
        except FileNotFoundError:
            families = []
    else:
        families = list_reference_families()
    for family in families:
        for slide in family.get("slides", []):
            slide_role = slide.get("role") or slide.get("role_override") or ""
            score = 0.0
            if slide_role == role:
                score += 0.7
            archetype_candidate = str(slide.get("archetype_candidate", ""))
            if role and role in archetype_candidate:
                score += 0.1
            if score <= 0:
                continue
            results.append(
                {
                    "reference_family_id": family.get("reference_family_id", ""),
                    "reference_slide_id": slide.get("reference_slide_id", ""),
                    "role": slide_role,
                    "archetype_candidate": archetype_candidate,
                    "score": round(score, 4),
                }
            )
    results.sort(key=lambda item: (-item["score"], item["reference_slide_id"]))
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
