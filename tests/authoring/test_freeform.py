"""Tests for inkline.authoring.freeform — shapes manifest schema, units, types."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from inkline.authoring.freeform import (
    parse_shapes_manifest,
    shapes_to_px,
    pct_to_px,
    ShapeSpec,
    FreeformError,
    SLIDE_W_PX,
    SLIDE_H_PX,
    VALID_SHAPE_TYPES,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_manifest(tmp_path):
    """Write a shapes manifest JSON file and return its path."""
    def _write(shapes: list[dict]) -> Path:
        p = tmp_path / "shapes.json"
        p.write_text(json.dumps({"shapes": shapes}), encoding="utf-8")
        return p
    return _write


@pytest.fixture
def tmp_image(tmp_path):
    """Create a minimal PNG for shape tests."""
    png_data = (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
        b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xff\xff'
        b'\x3f\x00\x05\xfe\x02\xfe\xdc\xccY\xe7\x00\x00\x00\x00IEND\xaeB`\x82'
    )
    img = tmp_path / "test.png"
    img.write_bytes(png_data)
    return img


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------

class TestManifestSchema:
    def test_valid_manifest_parses(self, tmp_manifest):
        p = tmp_manifest([
            {"type": "rect", "x": 0, "y": 0, "w": 100, "h": 100, "fill": "#FFFFFF"}
        ])
        shapes = parse_shapes_manifest(p)
        assert len(shapes) == 1
        assert shapes[0].type == "rect"

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            parse_shapes_manifest(tmp_path / "nonexistent.json")

    def test_invalid_json_raises(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("not json", encoding="utf-8")
        with pytest.raises(FreeformError, match="not valid JSON"):
            parse_shapes_manifest(bad)

    def test_missing_shapes_key_raises(self, tmp_path):
        p = tmp_path / "no_shapes.json"
        p.write_text(json.dumps({"other_key": []}), encoding="utf-8")
        with pytest.raises(FreeformError, match="missing 'shapes'"):
            parse_shapes_manifest(p)

    def test_unknown_shape_type_raises(self, tmp_manifest):
        p = tmp_manifest([{"type": "triangle", "x": 0, "y": 0, "w": 10, "h": 10}])
        with pytest.raises(FreeformError, match="unknown type"):
            parse_shapes_manifest(p)

    def test_invalid_units_raises(self, tmp_manifest):
        p = tmp_manifest([{"type": "rect", "x": 0, "y": 0, "w": 10, "h": 10, "units": "em"}])
        with pytest.raises(FreeformError, match="units must be"):
            parse_shapes_manifest(p)


# ---------------------------------------------------------------------------
# All valid shape types
# ---------------------------------------------------------------------------

class TestShapeTypes:
    def test_all_valid_types_parse(self, tmp_manifest, tmp_image):
        shapes = [
            {"type": "rect",         "x": 0, "y": 0, "w": 10, "h": 10},
            {"type": "rounded_rect", "x": 10, "y": 0, "w": 10, "h": 10, "radius": 0.2},
            {"type": "text",         "x": 20, "y": 0, "w": 20, "h": 5, "text": "Hello"},
            {"type": "line",         "x1": 0, "y1": 0, "x2": 100, "y2": 0},
            {"type": "arrow",        "x1": 0, "y1": 10, "x2": 100, "y2": 10},
            {"type": "circle",       "cx": 50, "cy": 50, "r": 10},
            {"type": "polygon",      "points": [[0, 0], [100, 0], [50, 100]]},
            {"type": "image",        "x": 0, "y": 0, "w": 100, "h": 100, "path": str(tmp_image)},
        ]
        p = tmp_manifest(shapes)
        result = parse_shapes_manifest(p)
        assert len(result) == 8
        types_found = {s.type for s in result}
        assert types_found == VALID_SHAPE_TYPES

    def test_polygon_requires_points(self, tmp_manifest):
        p = tmp_manifest([{"type": "polygon", "x": 0, "y": 0, "w": 10, "h": 10}])
        with pytest.raises(FreeformError, match="must have 'points'"):
            parse_shapes_manifest(p)

    def test_image_missing_path_accepted_as_empty(self, tmp_manifest):
        """Image shape with no path is valid — renderer will emit a placeholder rect."""
        p = tmp_manifest([{"type": "image", "x": 0, "y": 0, "w": 100, "h": 100}])
        shapes = parse_shapes_manifest(p)
        assert shapes[0].type == "image"
        assert shapes[0].path == ""

    def test_image_nonexistent_path_raises(self, tmp_manifest, tmp_path):
        p = tmp_manifest([{"type": "image", "x": 0, "y": 0, "w": 10, "h": 10, "path": "missing.png"}])
        with pytest.raises(FileNotFoundError):
            parse_shapes_manifest(p, base_dir=tmp_path)


# ---------------------------------------------------------------------------
# Units conversion
# ---------------------------------------------------------------------------

class TestUnitsConversion:
    def test_pct_to_px_horizontal(self):
        assert pct_to_px(100.0, "x") == pytest.approx(SLIDE_W_PX)
        assert pct_to_px(50.0, "w") == pytest.approx(SLIDE_W_PX / 2)

    def test_pct_to_px_vertical(self):
        assert pct_to_px(100.0, "y") == pytest.approx(SLIDE_H_PX)
        assert pct_to_px(50.0, "h") == pytest.approx(SLIDE_H_PX / 2)

    def test_shapes_to_px_converts_all(self, tmp_manifest):
        p = tmp_manifest([
            {"type": "rect", "x": 50, "y": 50, "w": 50, "h": 50, "units": "pct"}
        ])
        shapes = parse_shapes_manifest(p)
        px_shapes = shapes_to_px(shapes)
        assert px_shapes[0].units == "px"
        assert px_shapes[0].x == pytest.approx(SLIDE_W_PX * 0.5)
        assert px_shapes[0].y == pytest.approx(SLIDE_H_PX * 0.5)

    def test_shapes_to_px_passthrough_for_px_units(self, tmp_manifest):
        p = tmp_manifest([
            {"type": "rect", "x": 100, "y": 100, "w": 200, "h": 200, "units": "px"}
        ])
        shapes = parse_shapes_manifest(p)
        px_shapes = shapes_to_px(shapes)
        assert px_shapes[0].x == pytest.approx(100.0)  # unchanged


# ---------------------------------------------------------------------------
# Style fields
# ---------------------------------------------------------------------------

class TestStyleFields:
    def test_default_fill_is_white(self, tmp_manifest):
        p = tmp_manifest([{"type": "rect", "x": 0, "y": 0, "w": 10, "h": 10}])
        shapes = parse_shapes_manifest(p)
        assert shapes[0].fill == "#FFFFFF"

    def test_explicit_fill_parsed(self, tmp_manifest):
        p = tmp_manifest([{"type": "rect", "x": 0, "y": 0, "w": 10, "h": 10, "fill": "#1A2B4A"}])
        shapes = parse_shapes_manifest(p)
        assert shapes[0].fill == "#1A2B4A"

    def test_opacity_default(self, tmp_manifest):
        p = tmp_manifest([{"type": "rect", "x": 0, "y": 0, "w": 10, "h": 10}])
        shapes = parse_shapes_manifest(p)
        assert shapes[0].opacity == pytest.approx(1.0)

    def test_opacity_custom(self, tmp_manifest):
        p = tmp_manifest([{"type": "rect", "x": 0, "y": 0, "w": 10, "h": 10, "opacity": 0.7}])
        shapes = parse_shapes_manifest(p)
        assert shapes[0].opacity == pytest.approx(0.7)
