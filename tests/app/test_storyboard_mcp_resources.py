from __future__ import annotations

from argparse import Namespace
from pathlib import Path

from inkline.app import cli as cli_module
from inkline.app.mcp_resources import ResourceNotFoundError, list_resources, read_resource
import json
import pytest


def test_mcp_resources_expose_storyboard_system():
    uris = {item["uri"] for item in list_resources()}
    assert "inkline://slide_roles" in uris
    assert "inkline://slide_roles/team" in uris
    assert "inkline://archetypes/full_slide" in uris
    assert "inkline://reference_families" in uris
    assert "inkline://reference_slides" in uris
    assert "inkline://storyboard_rules" in uris


def test_can_read_full_slide_archetype_and_storyboard_rules():
    archetypes = read_resource("inkline://archetypes/full_slide")
    assert "executive_bio_cards_centered" in archetypes
    detail = read_resource("inkline://archetypes/full_slide/executive_bio_cards_centered")
    assert "compiled_slide_manifest" not in detail
    rules = read_resource("inkline://storyboard_rules")
    assert "Metadata precedence" in rules


def test_brand_detail_resource_returns_serialized_brand():
    detail = read_resource("inkline://brands/minimal")
    assert '"name": "minimal"' in detail
    assert '"heading_font"' in detail


def test_can_read_single_slide_role_resource():
    detail = read_resource("inkline://slide_roles/team")
    assert '"role": "team"' in detail
    assert '"default_archetype": "executive_bio_cards_centered"' in detail


def test_can_read_content_slide_role_resource():
    detail = read_resource("inkline://slide_roles/content")
    assert '"role": "content"' in detail
    assert '"default_archetype": ""' in detail


def test_knowledge_search_matches_resource_content(capsys):
    args = Namespace(knowledge_cmd="search", query="portrait dominance")
    cli_module.cmd_knowledge(args)
    out = capsys.readouterr().out
    assert "inkline://archetypes/full_slide/executive_bio_cards_centered" in out


def test_reference_family_resource_is_sanitized(monkeypatch):
    fake_family = {
        "reference_family_id": "family_x",
        "license_classification": "public_reference_only",
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
    monkeypatch.setattr(
        "inkline.intelligence.reference_catalog.list_reference_families",
        lambda: [fake_family],
    )
    monkeypatch.setattr(
        "inkline.intelligence.reference_catalog.load_reference_family",
        lambda _family_id: fake_family,
    )
    listing = read_resource("inkline://reference_families")
    assert "/secret" not in listing
    detail = read_resource("inkline://reference_families/family_x")
    assert "/secret" not in detail
    payload = json.loads(detail.split("```json\n", 1)[1].rsplit("\n```", 1)[0])
    assert "source_path" not in payload


def test_reference_slide_resource_is_sanitized(monkeypatch):
    fake_slide = {
        "reference_slide_id": "family_x_s01",
        "reference_family_id": "family_x",
        "source_slide_index": 1,
        "confidence_score": 1.0,
        "text_blocks": [{"text": "Cover"}],
        "normalized_geometry": [],
        "preview_path": "/secret/catalog/family_x_s01.png",
        "manifest_path": "/secret/catalog/family_x_s01.json",
        "_catalog_root": "/secret/catalog",
    }
    monkeypatch.setattr(
        "inkline.intelligence.reference_catalog.load_reference_slide",
        lambda _slide_id: fake_slide,
    )
    monkeypatch.setattr(
        "inkline.intelligence.reference_catalog.load_reference_family",
        lambda _family_id: {"reference_family_id": "family_x", "license_classification": "public_reference_only"},
    )
    detail = read_resource("inkline://reference_slides/family_x_s01")
    assert "/secret" not in detail
    payload = json.loads(detail.split("```json\n", 1)[1].rsplit("\n```", 1)[0])
    assert "preview_path" not in payload
    assert "manifest_path" not in payload


def test_confidential_reference_slide_detail_is_blocked_even_without_slide_family_id(monkeypatch):
    monkeypatch.setattr(
        "inkline.intelligence.reference_catalog.load_reference_slide",
        lambda _slide_id: {
            "reference_slide_id": "family_secret_s01",
            "source_slide_index": 1,
            "confidence_score": 1.0,
            "text_blocks": [{"text": "Secret"}],
            "normalized_geometry": [],
        },
    )
    monkeypatch.setattr(
        "inkline.intelligence.reference_catalog.list_reference_families",
        lambda: [
            {
                "reference_family_id": "family_secret",
                "license_classification": "client_confidential",
                "slides": [{"reference_slide_id": "family_secret_s01", "role": "cover"}],
            }
        ],
    )
    monkeypatch.setattr(
        "inkline.intelligence.reference_catalog.load_reference_family",
        lambda _family_id: {
            "reference_family_id": "family_secret",
            "license_classification": "client_confidential",
        },
    )
    with pytest.raises(ResourceNotFoundError):
        read_resource("inkline://reference_slides/family_secret_s01")


def test_confidential_reference_resources_are_not_exposed(monkeypatch):
    fake_family = {
        "reference_family_id": "family_secret",
        "license_classification": "client_confidential",
        "slides": [
            {
                "reference_slide_id": "family_secret_s01",
                "role": "cover",
            }
        ],
    }
    monkeypatch.setattr(
        "inkline.intelligence.reference_catalog.list_reference_families",
        lambda: [fake_family],
    )
    listing = read_resource("inkline://reference_families")
    assert "family_secret" not in listing
    slides = read_resource("inkline://reference_slides")
    assert "family_secret_s01" not in slides



def test_cmd_render_markdown_hard_fails_storyboard_validation(tmp_path: Path, monkeypatch):
    md_path = tmp_path / "deck.md"
    md_path.write_text("## Slide\nBody\n", encoding="utf-8")

    monkeypatch.setattr(
        "inkline.authoring.preprocessor.preprocess",
        lambda *_args, **_kwargs: (
            {"title": "Deck", "audience": "IC"},
            [{"heading": "Slide", "body": "Body"}],
        ),
    )

    class FakeAdvisor:
        def __init__(self, **_kwargs):
            pass

        def design_deck(self, **_kwargs):
            return [{"slide_type": "content", "archetype": "not_a_real_archetype", "data": {"title": "Slide"}}]

    monkeypatch.setattr("inkline.intelligence.DesignAdvisor", FakeAdvisor)
    monkeypatch.setattr("inkline.typst.export_typst_slides", lambda **_kwargs: None)
    monkeypatch.setattr("inkline.intelligence.audit_deck", lambda _slides: [])
    monkeypatch.setattr("inkline.intelligence.format_report", lambda _warnings: "")

    args = Namespace(
        file=str(md_path),
        output="pdf",
        output_dir=str(tmp_path / "out"),
        editable_institutional=False,
        watch=False,
        serve=False,
        strict_directives=False,
        brand="",
        template="",
    )
    with pytest.raises(ValueError, match="Unknown archetype"):
        cli_module.cmd_render(args)


def test_cmd_render_markdown_forwards_editable_institutional_to_pptx(tmp_path: Path, monkeypatch):
    md_path = tmp_path / "deck.md"
    md_path.write_text("## Slide\nBody\n", encoding="utf-8")
    monkeypatch.setattr(
        "inkline.authoring.preprocessor.preprocess",
        lambda *_args, **_kwargs: (
            {"title": "Deck", "audience": "IC"},
            [{"heading": "Slide", "body": "Body"}],
        ),
    )

    class FakeAdvisor:
        def __init__(self, **_kwargs):
            pass

        def design_deck(self, **_kwargs):
            return [{"slide_type": "content", "data": {"title": "Slide", "items": ["Body"]}}]

    monkeypatch.setattr("inkline.intelligence.DesignAdvisor", FakeAdvisor)
    monkeypatch.setattr(
        "inkline.intelligence.storyboard.resolve_storyboard_spec",
        lambda spec, **_kwargs: {
            **spec,
            "slides": spec["slides"],
            "_resolved_storyboard": {"schema_version": 1, "slides": []},
            "_authoring_trace": {"schema_name": "authoring_trace", "slides": []},
        },
    )
    monkeypatch.setattr("inkline.intelligence.storyboard.write_storyboard_artifacts", lambda *_args, **_kwargs: {})
    monkeypatch.setattr("inkline.typst.export_typst_slides", lambda **_kwargs: None)
    monkeypatch.setattr("inkline.intelligence.audit_deck", lambda _slides: [])
    monkeypatch.setattr("inkline.intelligence.format_report", lambda _warnings: "")
    calls: dict[str, object] = {}
    monkeypatch.setattr(
        "inkline.pptx.export_pptx_slides",
        lambda **kwargs: calls.update(kwargs) or (tmp_path / "out" / "deck.pptx"),
    )

    args = Namespace(
        file=str(md_path),
        output="pptx",
        output_dir=str(tmp_path / "out"),
        editable_institutional=True,
        watch=False,
        serve=False,
        strict_directives=False,
        brand="",
        template="",
    )
    cli_module.cmd_render(args)
    assert calls["editable_institutional"] is True


def test_cmd_critique_uses_pdf_storyboard_audit(capsys, tmp_path: Path, monkeypatch):
    pdf_path = tmp_path / "deck.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n%%EOF\n")
    monkeypatch.setattr(
        "inkline.app.institutional.audit_pdf_artifact",
        lambda **_kwargs: {"storyboard_audit": {"deck_verdict": "pass"}, "slide_critiques": []},
    )
    args = Namespace(pdf=str(pdf_path), rubric="institutional", brand="")
    cli_module.cmd_critique(args)
    out = capsys.readouterr().out
    assert '"deck_verdict": "pass"' in out


def test_cmd_render_fails_when_storyboard_artifact_write_fails(tmp_path: Path, monkeypatch, capsys):
    md_path = tmp_path / "deck.md"
    md_path.write_text("## Slide\nBody\n", encoding="utf-8")
    monkeypatch.setattr(
        "inkline.authoring.preprocessor.preprocess",
        lambda *_args, **_kwargs: (
            {"title": "Deck", "audience": "IC"},
            [{"heading": "Slide", "body": "Body"}],
        ),
    )

    class FakeAdvisor:
        def __init__(self, **_kwargs):
            pass

        def design_deck(self, **_kwargs):
            return [{"slide_type": "content", "data": {"title": "Slide", "items": ["Body"]}}]

    monkeypatch.setattr("inkline.intelligence.DesignAdvisor", FakeAdvisor)
    monkeypatch.setattr("inkline.typst.export_typst_slides", lambda **_kwargs: None)
    monkeypatch.setattr("inkline.intelligence.audit_deck", lambda _slides: [])
    monkeypatch.setattr("inkline.intelligence.format_report", lambda _warnings: "")
    monkeypatch.setattr(
        "inkline.intelligence.storyboard.write_storyboard_artifacts",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("disk full")),
    )

    args = Namespace(
        file=str(md_path),
        output="pdf",
        output_dir=str(tmp_path / "out"),
        editable_institutional=False,
        watch=False,
        serve=False,
        strict_directives=False,
        brand="",
        template="",
    )
    with pytest.raises(RuntimeError, match="disk full"):
        cli_module.cmd_render(args)
    err = capsys.readouterr().err
    assert "could not write storyboard artifacts" in err.lower()
