from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

import pytest

pytest.importorskip("pptx")

from inkline.app import cli as cli_module
from inkline.app.institutional import load_spec_file, inspect_pptx
from inkline.pptx import export_pptx_slides
from inkline.pptx.__init__ import _table_rows


def test_load_fixture_spec():
    spec_path = Path("examples/institutional/fixture_deck_7gi_v1/fixture_deck_7gi_v1.json")
    spec = load_spec_file(spec_path)
    assert spec["title"] == "7GI Fixture Deck v1"
    assert len(spec["slides"]) == 10


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
    assert payload["slide_statuses"]["1"] == "native"


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
    )

    payload = json.loads(meta_path.read_text(encoding="utf-8"))
    assert payload["slide_statuses"]["1"] == "native"
    assert payload["slides_with_image_fallback"] == []


def test_table_rows_follow_header_order():
    rows = [{"Second": "B", "First": "A"}]
    headers = ["First", "Second"]
    assert _table_rows(rows, headers=headers) == [["A", "B"]]


def test_cmd_render_yaml_json_watch_enters_watch_loop(tmp_path: Path, monkeypatch):
    spec_path = tmp_path / "fixture.json"
    spec_path.write_text(json.dumps({"title": "Fixture", "slides": []}), encoding="utf-8")

    calls: dict[str, object] = {}

    def fake_render_spec_file(path, *, formats, output_dir=None, editable_institutional=False):
        calls["render"] = {
            "path": Path(path),
            "formats": list(formats),
            "output_dir": output_dir,
            "editable": editable_institutional,
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
    )
    cli_module.cmd_render(args)

    assert calls["render"]["path"] == spec_path
    assert calls["watch"]["path"] == spec_path
