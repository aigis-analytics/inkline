from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("pptx")

from inkline.intelligence import reference_catalog as catalog_module
from inkline.intelligence.reference_catalog import (
    find_reference_slides,
    load_reference_slide,
    load_reference_family,
    sanitize_reference_family_for_mcp,
)
from inkline.intelligence.reference_ingest import apply_curation_overrides, ingest_reference_pptx
from inkline.pptx import export_pptx_slides


def test_ingest_reference_pptx_and_apply_curation(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(catalog_module, "LOCAL_ROOT", tmp_path / "catalog")
    import inkline.intelligence.reference_ingest as ingest_module

    monkeypatch.setattr(ingest_module, "LOCAL_ROOT", tmp_path / "catalog")

    pptx_path = tmp_path / "fixture.pptx"
    export_pptx_slides(
        [
            {"slide_type": "title", "data": {"company": "Fixture", "tagline": "Tag"}},
            {"slide_type": "team_grid", "data": {"title": "Team", "members": [{"name": "A", "role": "B"}]}},
        ],
        pptx_path,
    )

    payload = ingest_reference_pptx(pptx_path, family_id="family_v1")
    assert payload["reference_family_id"] == "family_v1"
    assert payload["style_tokens"]["source_mode"] == "pptx_native_mvp"
    family_dir = (tmp_path / "catalog" / "family_v1")
    manifest_path = family_dir / "reference_family_manifest.json"
    assert manifest_path.exists()
    assert payload["slides"][0]["role"] == "cover"
    assert payload["slides"][0]["archetype_candidate"] == "cover_hero_photo_left_text_block"
    assert payload["slides"][1]["role"] == "team"
    assert payload["slides"][1]["archetype_candidate"] == "executive_bio_cards_centered"
    assert payload["slides"][0]["preview_path"] == "family_v1_s01.png"
    assert payload["slides"][0]["manifest_path"] == "family_v1_s01.json"
    refs = find_reference_slides(role="team", reference_family="family_v1")
    assert refs
    assert refs[0]["reference_slide_id"] == "family_v1_s02"
    slide_manifest = load_reference_slide("family_v1_s02")
    assert slide_manifest["reference_slide_id"] == "family_v1_s02"
    overrides_path = family_dir / "curation_overrides.yaml"
    overrides_path.write_text(
        "\n".join(
            [
                "reference_family_id: family_v1",
                "slides:",
                "  - reference_slide_id: family_v1_s02",
                "    role_override: team",
                "    archetype_override: executive_bio_cards_centered",
                "    exemplar_strength: strong",
            ]
        ),
        encoding="utf-8",
    )
    curated = apply_curation_overrides("family_v1", catalog_root=tmp_path / "catalog")
    slide = next(item for item in curated["slides"] if item["reference_slide_id"] == "family_v1_s02")
    assert slide["role"] == "team"
    assert slide["archetype_candidate"] == "executive_bio_cards_centered"


def test_reference_catalog_precedence_prefers_local(tmp_path: Path, monkeypatch):
    local = tmp_path / "local"
    packaged = tmp_path / "packaged"
    (local / "family_x").mkdir(parents=True)
    (packaged / "family_x").mkdir(parents=True)
    local_payload = {
        "reference_family_id": "family_x",
        "source_path": "local.pptx",
        "license_classification": "private_internal",
        "slides": [],
    }
    packaged_payload = {
        "reference_family_id": "family_x",
        "source_path": "packaged.pptx",
        "license_classification": "public_reusable",
        "slides": [],
    }
    (local / "family_x" / "reference_family_manifest.json").write_text(json.dumps(local_payload), encoding="utf-8")
    (packaged / "family_x" / "reference_family_manifest.json").write_text(json.dumps(packaged_payload), encoding="utf-8")
    monkeypatch.setattr(catalog_module, "LOCAL_ROOT", local)
    monkeypatch.setattr(catalog_module, "PACKAGE_ROOT", packaged)
    families = catalog_module.list_reference_families()
    assert len(families) == 1
    assert families[0]["source_path"] == "local.pptx"


def test_sanitize_reference_family_for_mcp_redacts_paths():
    payload = {
        "schema_name": "reference_family_manifest",
        "schema_version": 1,
        "reference_family_id": "family_x",
        "license_classification": "client_confidential",
        "ingestion_method": "pptx_native",
        "confidence_score": 1.0,
        "version": 1,
        "style_tokens": {"source_mode": "pptx_native_mvp"},
        "notes": [],
        "source_path": "/secret/client/deck.pptx",
        "_catalog_root": "/secret/catalog",
        "slides": [
            {
                "reference_slide_id": "family_x_s01",
                "role": "cover",
                "archetype_candidate": "cover_hero_photo_left_text_block",
                "preview_path": "/secret/catalog/family_x_s01.png",
                "manifest_path": "/secret/catalog/family_x_s01.json",
            }
        ],
    }
    safe = sanitize_reference_family_for_mcp(payload)
    assert "source_path" not in safe
    assert "_catalog_root" not in safe
    assert "preview_path" not in safe["slides"][0]
    assert "manifest_path" not in safe["slides"][0]


def test_reference_family_id_rejects_path_traversal(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(catalog_module, "LOCAL_ROOT", tmp_path / "catalog")
    import inkline.intelligence.reference_ingest as ingest_module

    monkeypatch.setattr(ingest_module, "LOCAL_ROOT", tmp_path / "catalog")
    pptx_path = tmp_path / "fixture.pptx"
    export_pptx_slides(
        [{"slide_type": "title", "data": {"company": "Fixture", "tagline": "Tag"}}],
        pptx_path,
    )
    with pytest.raises(ValueError, match="Invalid reference family id"):
        ingest_reference_pptx(pptx_path, family_id="../escape")
    with pytest.raises(ValueError, match="Invalid reference family id"):
        load_reference_family("../escape")


def test_load_reference_slide_rejects_absolute_or_escaping_manifest_paths(tmp_path: Path, monkeypatch):
    local = tmp_path / "catalog"
    family_dir = local / "family_x"
    family_dir.mkdir(parents=True)
    manifest = {
        "reference_family_id": "family_x",
        "license_classification": "private_internal",
        "slides": [
            {
                "reference_slide_id": "family_x_s01",
                "role": "cover",
                "archetype_candidate": "cover_hero_photo_left_text_block",
                "manifest_path": "/tmp/evil.json",
            }
        ],
    }
    (family_dir / "reference_family_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setattr(catalog_module, "LOCAL_ROOT", local)
    monkeypatch.setattr(catalog_module, "PACKAGE_ROOT", tmp_path / "packaged")
    with pytest.raises(ValueError, match="Absolute reference family paths"):
        load_reference_slide("family_x_s01")

    manifest["slides"][0]["manifest_path"] = "../escape.json"
    (family_dir / "reference_family_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="escapes catalog root"):
        load_reference_slide("family_x_s01")


def test_apply_curation_overrides_validates_role_and_archetype(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(catalog_module, "LOCAL_ROOT", tmp_path / "catalog")
    import inkline.intelligence.reference_ingest as ingest_module

    monkeypatch.setattr(ingest_module, "LOCAL_ROOT", tmp_path / "catalog")
    pptx_path = tmp_path / "fixture.pptx"
    export_pptx_slides(
        [{"slide_type": "title", "data": {"company": "Fixture", "tagline": "Tag"}}],
        pptx_path,
    )
    ingest_reference_pptx(pptx_path, family_id="family_v1")
    overrides_path = tmp_path / "catalog" / "family_v1" / "curation_overrides.yaml"
    overrides_path.write_text(
        "\n".join(
            [
                "reference_family_id: family_v1",
                "slides:",
                "  - reference_slide_id: family_v1_s01",
                "    role_override: teem",
            ]
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Unknown role_override"):
        apply_curation_overrides("family_v1", catalog_root=tmp_path / "catalog")

    overrides_path.write_text(
        "\n".join(
            [
                "reference_family_id: family_v1",
                "slides:",
                "  - reference_slide_id: family_v1_s01",
                "    archetype_override: not_a_real_archetype",
            ]
        ),
        encoding="utf-8",
    )
    with pytest.raises(KeyError):
        apply_curation_overrides("family_v1", catalog_root=tmp_path / "catalog")


def test_reference_ingest_rejects_non_local_catalog_root(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(catalog_module, "LOCAL_ROOT", tmp_path / "catalog")
    import inkline.intelligence.reference_ingest as ingest_module

    monkeypatch.setattr(ingest_module, "LOCAL_ROOT", tmp_path / "catalog")
    pptx_path = tmp_path / "fixture.pptx"
    export_pptx_slides(
        [{"slide_type": "title", "data": {"company": "Fixture", "tagline": "Tag"}}],
        pptx_path,
    )
    with pytest.raises(ValueError, match="local private catalog root"):
        ingest_reference_pptx(pptx_path, family_id="family_v1", catalog_root=tmp_path / "elsewhere")


def test_reference_curation_rejects_non_local_catalog_root(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(catalog_module, "LOCAL_ROOT", tmp_path / "catalog")
    import inkline.intelligence.reference_ingest as ingest_module

    monkeypatch.setattr(ingest_module, "LOCAL_ROOT", tmp_path / "catalog")
    pptx_path = tmp_path / "fixture.pptx"
    export_pptx_slides(
        [{"slide_type": "title", "data": {"company": "Fixture", "tagline": "Tag"}}],
        pptx_path,
    )
    ingest_reference_pptx(pptx_path, family_id="family_v1")
    with pytest.raises(ValueError, match="local private catalog root"):
        apply_curation_overrides("family_v1", catalog_root=tmp_path / "elsewhere")
