from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

import pytest

pytest.importorskip("pptx")

from inkline.app import cli as cli_module
from inkline.app.institutional import audit_pdf_artifact, audit_pptx, load_spec_file, inspect_pptx
from inkline.pptx import export_pptx_slides
from inkline.pptx.__init__ import _table_rows
from inkline.intelligence.vishwakarma import CritiqueResult, SlideCritique


def test_load_fixture_spec():
    spec_path = Path("examples/institutional/fixture_deck_7gi_v1/fixture_deck_7gi_v1.json")
    spec = load_spec_file(spec_path)
    assert spec["title"] == "7GI Fixture Deck v1"
    assert len(spec["slides"]) == 10
    assert spec["storyboard"]["schema_name"] == "storyboard"
    assert spec["slides"][0]["slide_id"]
    assert spec["storyboard"]["deck"]["execution_contract"]["execution_mode"] == "explicit_spec"


def test_export_writes_metadata(tmp_path: Path):
    slides = [
        {
            "slide_type": "title",
            "data": {
                "company": "Fixture Co",
                "tagline": "Fixture Tagline",
                "subtitle": "Fixture Subtitle",
            },
        },
        {
            "slide_type": "content",
            "data": {
                "section": "Overview",
                "title": "Overview",
                "items": ["A", "B"],
            },
        },
    ]
    pptx_path = tmp_path / "fixture.pptx"
    meta_path = tmp_path / "fixture.export_metadata.json"

    export_pptx_slides(
        slides,
        pptx_path,
        metadata_path=meta_path,
        editable_institutional=True,
    )

    payload = json.loads(meta_path.read_text(encoding="utf-8"))
    assert payload["editable_institutional"] is True
    assert payload["editable_native_ratio"] == 1.0
    assert payload["fully_native_ratio"] == 1.0
    assert payload["slide_statuses"]["1"] == "native"
    assert payload["slides"][0]["slide_id"] == ""


def test_render_spec_file_sidecar_omits_host_bound_artifact_paths(tmp_path: Path):
    spec_path = tmp_path / "fixture.json"
    spec_path.write_text(
        json.dumps(
            {
                "title": "Fixture",
                "slides": [
                    {
                        "slide_type": "content",
                        "data": {"title": "Overview", "items": ["A"]},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    from inkline.app.institutional import render_spec_file

    artifacts = render_spec_file(
        spec_path,
        formats=["pptx"],
        output_dir=tmp_path / "out",
        editable_institutional=True,
        execution_mode="explicit_spec",
        design_locked=True,
        use_design_advisor=False,
        authoring_mode="external_llm",
    )
    payload = json.loads(artifacts.export_metadata_path.read_text(encoding="utf-8"))
    deck_metadata = payload["deck_metadata"]
    assert payload["pptx_path"] == "fixture.pptx"
    assert "storyboard_path" not in deck_metadata
    assert "authoring_trace_path" not in deck_metadata
    assert deck_metadata["artifact_files"]["storyboard"].endswith(".storyboard.json")
    assert deck_metadata["artifact_files"]["authoring_trace"].endswith(".authoring_trace.json")
    assert deck_metadata["storyboard"]["deck"]["execution_contract"]["use_design_advisor"] is False
    assert deck_metadata["authoring_trace"]["execution_contract"]["authoring_mode"] == "external_llm"
    serialized = json.dumps(deck_metadata)
    assert str(tmp_path) not in serialized


def test_inspect_pptx_reports_shape_counts(tmp_path: Path):
    slides = [
        {
            "slide_type": "title",
            "data": {
                "company": "Fixture Co",
                "tagline": "Fixture Tagline",
                "subtitle": "Fixture Subtitle",
            },
        },
    ]
    pptx_path = tmp_path / "fixture.pptx"
    export_pptx_slides(slides, pptx_path)

    result = inspect_pptx(pptx_path)
    assert result["slide_count"] == 1
    assert result["slides"][0]["shape_count"] >= 1


def test_export_uses_spec_relative_chart_assets(tmp_path: Path):
    spec_root = tmp_path / "spec"
    spec_root.mkdir()
    asset = spec_root / "chart.png"
    asset.write_bytes(
        bytes.fromhex(
            "89504E470D0A1A0A0000000D4948445200000001000000010802000000907753DE"
            "0000000C49444154789C63606060000000040001F61738550000000049454E44AE426082"
        )
    )

    slides = [
        {
            "slide_type": "chart",
            "data": {
                "section": "Exhibit",
                "title": "Chart",
                "image_path": "chart.png",
            },
        },
    ]
    pptx_path = tmp_path / "out" / "fixture.pptx"
    meta_path = tmp_path / "out" / "fixture.export_metadata.json"

    export_pptx_slides(
        slides,
        pptx_path,
        source_root=spec_root,
        metadata_path=meta_path,
        editable_institutional=True,
        deck_metadata={"storyboard": {"schema_version": 1}},
    )

    payload = json.loads(meta_path.read_text(encoding="utf-8"))
    assert payload["slide_statuses"]["1"] == "native_with_exceptions"
    assert payload["editable_native_ratio"] == 1.0
    assert payload["fully_native_ratio"] == 0.0
    assert payload["slides_with_image_fallback"] == []
    assert payload["slides_with_editability_exceptions"] == [1]
    assert payload["deck_metadata"]["storyboard"]["schema_version"] == 1

    inspected = inspect_pptx(pptx_path)
    assert inspected["slide_statuses"]["1"] == "native_with_exceptions"
    assert inspected["editable_native_ratio"] == 1.0
    assert inspected["fully_native_ratio"] == 0.0
    assert inspected["slides_with_editability_exceptions"] == [1]
    assert inspected["inspection_mode"] == "metadata"
    assert inspected["reliability"] == "high"


def test_editable_institutional_rejects_fallback_slides(tmp_path: Path):
    pptx_path = tmp_path / "fixture.pptx"
    with pytest.raises(RuntimeError, match="Editable institutional PPTX export requires native slides"):
        export_pptx_slides(
            [
                {
                    "slide_type": "unsupported_custom_layout",
                    "data": {"title": "Unsupported"},
                }
            ],
            pptx_path,
            editable_institutional=True,
            metadata_path=tmp_path / "fixture.export_metadata.json",
        )


def test_editable_institutional_marks_freeform_raster_as_exception_not_native(tmp_path: Path):
    image_path = tmp_path / "asset.png"
    image_path.write_bytes(
        bytes.fromhex(
            "89504E470D0A1A0A0000000D4948445200000001000000010802000000907753DE"
            "0000000C49444154789C63606060000000040001F61738550000000049454E44AE426082"
        )
    )
    pptx_path = tmp_path / "fixture.pptx"
    meta_path = tmp_path / "fixture.export_metadata.json"
    export_pptx_slides(
        [
            {
                "slide_type": "freeform",
                "data": {
                    "title": "Hero",
                    "shapes": [
                        {"type": "image", "path": str(image_path), "x": 0, "y": 0, "w": 100, "h": 100}
                    ],
                },
            }
        ],
        pptx_path,
        metadata_path=meta_path,
        editable_institutional=True,
    )
    payload = json.loads(meta_path.read_text(encoding="utf-8"))
    assert payload["slide_statuses"]["1"] == "native_with_exceptions"
    assert payload["slides_with_editability_exceptions"] == [1]


def test_editable_institutional_rejects_timeline_backend_degrade(tmp_path: Path):
    pptx_path = tmp_path / "fixture.pptx"
    with pytest.raises(RuntimeError, match="timeline_backend_degraded_to_four_card"):
        export_pptx_slides(
            [
                {
                    "slide_type": "timeline",
                    "data": {
                        "_layout_pptx": "timeline",
                        "title": "Timeline",
                        "milestones": [
                            {"date": "Q1", "label": "Launch", "desc": "Start process"},
                            {"date": "Q2", "label": "Sign", "desc": "Close deal"},
                        ],
                    },
                }
            ],
            pptx_path,
            editable_institutional=True,
            metadata_path=tmp_path / "fixture.export_metadata.json",
        )


def test_table_rows_follow_header_order():
    rows = [{"Second": "B", "First": "A"}]
    headers = ["First", "Second"]
    assert _table_rows(rows, headers=headers) == [["A", "B"]]


def test_cmd_render_yaml_json_watch_enters_watch_loop(tmp_path: Path, monkeypatch):
    spec_path = tmp_path / "fixture.json"
    spec_path.write_text(json.dumps({"title": "Fixture", "slides": []}), encoding="utf-8")

    calls: dict[str, object] = {}

    def fake_render_spec_file(
        path,
        *,
        formats,
        output_dir=None,
        editable_institutional=False,
        brand_override="",
        template_override="",
        execution_mode="",
        design_locked=None,
        use_design_advisor=None,
        authoring_mode="",
    ):
        calls["render"] = {
            "path": Path(path),
            "formats": list(formats),
            "output_dir": output_dir,
            "editable": editable_institutional,
            "brand_override": brand_override,
            "template_override": template_override,
            "execution_mode": execution_mode,
            "design_locked": design_locked,
            "use_design_advisor": use_design_advisor,
            "authoring_mode": authoring_mode,
        }
        return Namespace(pdf_path=tmp_path / "fixture.pdf", pptx_path=None, export_metadata_path=None)

    def fake_watch(path, args):
        calls["watch"] = {"path": Path(path), "args_file": args.file}

    monkeypatch.setattr("inkline.app.institutional.render_spec_file", fake_render_spec_file)
    monkeypatch.setattr(cli_module, "_run_watch", fake_watch)

    args = Namespace(
        file=str(spec_path),
        output="pdf",
        output_dir="",
        editable_institutional=False,
        watch=True,
        serve=False,
        strict_directives=False,
        brand="",
        template="",
        execution_mode="explicit_spec",
        design_locked=True,
        use_design_advisor=False,
        authoring_mode="external_llm",
    )
    cli_module.cmd_render(args)

    assert calls["render"]["path"] == spec_path
    assert calls["watch"]["path"] == spec_path
    assert calls["render"]["brand_override"] == ""
    assert calls["render"]["template_override"] == ""
    assert calls["render"]["execution_mode"] == "explicit_spec"
    assert calls["render"]["design_locked"] is True
    assert calls["render"]["use_design_advisor"] is False
    assert calls["render"]["authoring_mode"] == "external_llm"


def test_args_for_watch_rerender_disables_recursive_watch():
    args = Namespace(file="deck.md", watch=True, serve=True, output="pdf")
    rerender = cli_module._args_for_watch_rerender(args)
    assert rerender.watch is False
    assert rerender.serve is False
    assert rerender.file == "deck.md"


def test_cmd_render_yaml_json_serve_opens_browser(tmp_path: Path, monkeypatch):
    spec_path = tmp_path / "fixture.json"
    spec_path.write_text(json.dumps({"title": "Fixture", "slides": []}), encoding="utf-8")

    opened: list[str] = []

    def fake_render_spec_file(
        path,
        *,
        formats,
        output_dir=None,
        editable_institutional=False,
        brand_override="",
        template_override="",
        execution_mode="",
        design_locked=None,
        use_design_advisor=None,
        authoring_mode="",
    ):
        return Namespace(pdf_path=tmp_path / "fixture.pdf", pptx_path=None, export_metadata_path=None)

    monkeypatch.setattr("inkline.app.institutional.render_spec_file", fake_render_spec_file)
    monkeypatch.setattr(cli_module.webbrowser, "open", lambda url: opened.append(url))

    args = Namespace(
        file=str(spec_path),
        output="pdf",
        output_dir="",
        editable_institutional=False,
        watch=False,
        serve=True,
        strict_directives=False,
        brand="",
        template="",
        execution_mode="",
        design_locked=None,
        use_design_advisor=None,
        authoring_mode="",
    )
    cli_module.cmd_render(args)

    assert opened == ["http://localhost:8082/"]


def test_cmd_render_yaml_json_forwards_brand_and_template_overrides(tmp_path: Path, monkeypatch):
    spec_path = tmp_path / "fixture.json"
    spec_path.write_text(json.dumps({"title": "Fixture", "slides": []}), encoding="utf-8")

    calls: dict[str, object] = {}

    def fake_render_spec_file(
        path,
        *,
        formats,
        output_dir=None,
        editable_institutional=False,
        brand_override="",
        template_override="",
        execution_mode="",
        design_locked=None,
        use_design_advisor=None,
        authoring_mode="",
    ):
        calls["brand_override"] = brand_override
        calls["template_override"] = template_override
        calls["execution_mode"] = execution_mode
        return Namespace(pdf_path=tmp_path / "fixture.pdf", pptx_path=None, export_metadata_path=None)

    monkeypatch.setattr("inkline.app.institutional.render_spec_file", fake_render_spec_file)

    args = Namespace(
        file=str(spec_path),
        output="pdf",
        output_dir="",
        editable_institutional=False,
        watch=False,
        serve=False,
        strict_directives=False,
        brand="client_brand",
        template="board",
        execution_mode="draft",
        design_locked=None,
        use_design_advisor=None,
        authoring_mode="",
    )
    cli_module.cmd_render(args)

    assert calls == {
        "brand_override": "client_brand",
        "template_override": "board",
        "execution_mode": "draft",
    }


def test_cmd_draft_delegates_to_cmd_serve(monkeypatch):
    called: dict[str, object] = {}

    def fake_cmd_serve(args):
        called["port"] = args.port
        called["backend"] = args.backend
        called["no_browser"] = args.no_browser

    monkeypatch.setattr(cli_module, "cmd_serve", fake_cmd_serve)
    monkeypatch.setattr(cli_module, "_check_backend", lambda backend: None)

    args = Namespace(port=18083, backend="auto")
    cli_module.cmd_draft(args)

    assert called == {"port": 18083, "backend": "auto", "no_browser": False}


def test_inspect_pptx_reports_best_effort_without_sidecar(tmp_path: Path):
    slides = [
        {
            "slide_type": "title",
            "data": {
                "company": "Fixture Co",
                "tagline": "Fixture Tagline",
                "subtitle": "Fixture Subtitle",
            },
        },
    ]
    pptx_path = tmp_path / "fixture.pptx"
    export_pptx_slides(slides, pptx_path)
    meta_path = tmp_path / "fixture.export_metadata.json"
    if meta_path.exists():
        meta_path.unlink()

    result = inspect_pptx(pptx_path)
    assert result["inspection_mode"] == "heuristic"
    assert result["reliability"] == "best_effort"
    assert "Best-effort PPTX inspection" in result["warning"]


def test_audit_pptx_treats_native_with_exceptions_as_non_fallback(tmp_path: Path, monkeypatch):
    spec_root = tmp_path / "spec"
    spec_root.mkdir()
    asset = spec_root / "chart.png"
    asset.write_bytes(
        bytes.fromhex(
            "89504E470D0A1A0A0000000D4948445200000001000000010802000000907753DE"
            "0000000C49444154789C63606060000000040001F61738550000000049454E44AE426082"
        )
    )
    pptx_path = tmp_path / "fixture.pptx"
    export_pptx_slides(
        [
            {
                "slide_type": "chart",
                "slide_id": "s01_map",
                "storyboard": {
                    "slide_id": "s01_map",
                    "role": "market_map",
                    "archetype": "market_map_reference_exhibit",
                    "key_message": "Map",
                    "reference_family": "",
                },
                "compiled_manifest": {
                    "source_archetype": "market_map_reference_exhibit",
                    "pptx_editability_exceptions": ["intentional_raster_asset"],
                },
                "data": {"section": "Exhibit", "title": "Map", "image_path": "chart.png"},
            }
        ],
        pptx_path,
        source_root=spec_root,
        metadata_path=tmp_path / "fixture.export_metadata.json",
        editable_institutional=True,
        deck_metadata={"storyboard": {"schema_version": 1}},
    )
    rendered_pdf = tmp_path / "fixture.rendered.pdf"
    rendered_pdf.write_bytes(b"%PDF-1.4\n%%EOF\n")

    monkeypatch.setattr(
        "inkline.app.institutional.render_pptx_via_soffice",
        lambda *_args, **_kwargs: rendered_pdf,
    )
    monkeypatch.setattr(
        "inkline.intelligence.vishwakarma.critique_pdf",
        lambda *args, **kwargs: CritiqueResult(
            overall_score=100,
            rubric="institutional",
            brand="",
            pdf_path=str(rendered_pdf),
            slide_critiques=[
                SlideCritique(
                    slide_index=1,
                    verdict="PASS",
                    comment="ok",
                    fix_hint="",
                )
            ],
        ),
    )

    result = audit_pptx(pptx_path)
    assert result["storyboard_audit"]["deck_verdict"] == "pass"
    assert result["storyboard_audit"]["slides_requiring_human_signoff"] == []


def test_audit_pptx_requires_human_signoff_without_export_metadata(tmp_path: Path, monkeypatch):
    pptx_path = tmp_path / "fixture.pptx"
    export_pptx_slides(
        [
            {
                "slide_type": "title",
                "data": {"company": "Fixture Co", "tagline": "Fixture Tagline", "subtitle": "Fixture Subtitle"},
            }
        ],
        pptx_path,
    )
    meta_path = tmp_path / "fixture.export_metadata.json"
    if meta_path.exists():
        meta_path.unlink()
    rendered_pdf = tmp_path / "fixture.rendered.pdf"
    rendered_pdf.write_bytes(b"%PDF-1.4\n%%EOF\n")

    monkeypatch.setattr(
        "inkline.app.institutional.render_pptx_via_soffice",
        lambda *_args, **_kwargs: rendered_pdf,
    )
    monkeypatch.setattr(
        "inkline.intelligence.vishwakarma.critique_pdf",
        lambda *args, **kwargs: CritiqueResult(
            overall_score=100,
            rubric="institutional",
            brand="",
            pdf_path=str(rendered_pdf),
            slide_critiques=[
                SlideCritique(
                    slide_index=1,
                    verdict="PASS",
                    comment="ok",
                    fix_hint="",
                )
            ],
        ),
    )

    result = audit_pptx(pptx_path)
    assert result["storyboard_audit"]["deck_verdict"] == "needs_human_signoff"
    assert "sidecar missing" in result["storyboard_audit"]["reason"].lower()


def test_audit_pdf_artifact_uses_sibling_storyboard_metadata(tmp_path: Path, monkeypatch):
    pdf_path = tmp_path / "deck.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n%%EOF\n")
    (tmp_path / "deck.storyboard.json").write_text(
        json.dumps(
            {
                "schema_name": "storyboard",
                "schema_version": 1,
                "slides": [
                    {
                        "slide_id": "s01_cover",
                        "index": 1,
                        "role": "cover",
                        "archetype": "cover_hero_photo_left_text_block",
                        "key_message": "Enter Angola",
                        "reference_family": "family_v1",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "inkline.intelligence.vishwakarma.critique_pdf",
        lambda *args, **kwargs: CritiqueResult(
            overall_score=100,
            rubric="institutional",
            brand="",
            pdf_path=str(pdf_path),
            slide_critiques=[
                SlideCritique(
                    slide_index=1,
                    verdict="PASS",
                    comment="ok",
                    fix_hint="",
                )
            ],
        ),
    )
    result = audit_pdf_artifact(pdf_path)
    assert result["storyboard_audit"]["deck_verdict"] == "pass"
    assert result["storyboard_schema_version"] == 1


def test_audit_pdf_artifact_requires_human_signoff_without_storyboard(tmp_path: Path, monkeypatch):
    pdf_path = tmp_path / "deck.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n%%EOF\n")
    monkeypatch.setattr(
        "inkline.intelligence.vishwakarma.critique_pdf",
        lambda *args, **kwargs: CritiqueResult(
            overall_score=100,
            rubric="institutional",
            brand="",
            pdf_path=str(pdf_path),
            slide_critiques=[
                SlideCritique(
                    slide_index=1,
                    verdict="PASS",
                    comment="ok",
                    fix_hint="",
                )
            ],
        ),
    )
    result = audit_pdf_artifact(pdf_path)
    assert result["storyboard_audit"]["deck_verdict"] == "needs_human_signoff"
    assert "storyboard metadata missing" in result["storyboard_audit"]["reason"].lower()


def test_audit_pdf_artifact_fails_when_storyboard_declares_more_slides_than_critiqued(tmp_path: Path, monkeypatch):
    pdf_path = tmp_path / "deck.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n%%EOF\n")
    (tmp_path / "deck.storyboard.json").write_text(
        json.dumps(
            {
                "schema_name": "storyboard",
                "schema_version": 1,
                "slides": [
                    {
                        "slide_id": "s01_cover",
                        "index": 1,
                        "role": "cover",
                        "archetype": "cover_hero_photo_left_text_block",
                        "key_message": "Enter Angola",
                        "reference_family": "family_v1",
                    },
                    {
                        "slide_id": "s02_team",
                        "index": 2,
                        "role": "team",
                        "archetype": "executive_bio_cards_centered",
                        "key_message": "Local access",
                        "reference_family": "family_v1",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "inkline.intelligence.vishwakarma.critique_pdf",
        lambda *args, **kwargs: CritiqueResult(
            overall_score=100,
            rubric="institutional",
            brand="",
            pdf_path=str(pdf_path),
            slide_critiques=[
                SlideCritique(
                    slide_index=1,
                    verdict="PASS",
                    comment="ok",
                    fix_hint="",
                )
            ],
        ),
    )
    result = audit_pdf_artifact(pdf_path)
    assert result["storyboard_audit"]["deck_verdict"] == "fail"
    assert result["storyboard_audit"]["slides_failed_hard_checks"] == [2]


def test_audit_pdf_artifact_fails_when_critiqued_slides_exceed_storyboard_metadata(tmp_path: Path, monkeypatch):
    pdf_path = tmp_path / "deck.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n%%EOF\n")
    (tmp_path / "deck.storyboard.json").write_text(
        json.dumps(
            {
                "schema_name": "storyboard",
                "schema_version": 1,
                "slides": [
                    {
                        "slide_id": "s01_cover",
                        "index": 1,
                        "role": "cover",
                        "archetype": "cover_hero_photo_left_text_block",
                        "key_message": "Enter Angola",
                        "reference_family": "family_v1",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "inkline.intelligence.vishwakarma.critique_pdf",
        lambda *args, **kwargs: CritiqueResult(
            overall_score=100,
            rubric="institutional",
            brand="",
            pdf_path=str(pdf_path),
            slide_critiques=[
                SlideCritique(
                    slide_index=1,
                    verdict="PASS",
                    comment="ok",
                    fix_hint="",
                ),
                SlideCritique(
                    slide_index=2,
                    verdict="PASS",
                    comment="unexpected extra slide",
                    fix_hint="",
                ),
            ],
        ),
    )
    result = audit_pdf_artifact(pdf_path)
    assert result["storyboard_audit"]["deck_verdict"] == "fail"
    assert result["storyboard_audit"]["slides_failed_hard_checks"] == [2]
