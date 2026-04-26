"""Tests for freeform slide_type Typst + PPTX rendering."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from inkline.typst.slide_renderer import TypstSlideRenderer, SlideSpec

_THEME = {
    "name": "Test",
    "bg": "#FFFFFF",
    "text": "#0F172A",
    "accent": "#6366F1",
    "muted": "#94A3B8",
    "border": "#E2E8F0",
    "card_bg": "#F8FAFC",
    "card_fill": "#F8FAFC",
    "title_fg": "#FFFFFF",
    "heading_font": "Inter",
    "body_font": "Inter",
    "body_size": 11,
    "footer_text": "Test deck",
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def renderer():
    return TypstSlideRenderer(_THEME)


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
# Typst freeform renderer
# ---------------------------------------------------------------------------

class TestTypstFreeformRenderer:
    def test_freeform_in_dispatch_table(self, renderer):
        """freeform is registered in the slide dispatch table."""
        slide = SlideSpec(slide_type="freeform", data={"title": "Test", "shapes": []})
        output = renderer._render_slide(slide)
        assert "freeform slide" in output.lower() or "no shapes" in output

    def test_rect_shape_emits_typst_rect(self, renderer):
        slide = SlideSpec(slide_type="freeform", data={
            "title": "T",
            "shapes": [
                {"type": "rect", "x": 10, "y": 20, "w": 30, "h": 10, "fill": "#FF0000"}
            ]
        })
        output = renderer._render_slide(slide)
        assert "rect(" in output
        assert "#FF0000" in output

    def test_rounded_rect_shape(self, renderer):
        slide = SlideSpec(slide_type="freeform", data={
            "title": "T",
            "shapes": [
                {"type": "rounded_rect", "x": 5, "y": 5, "w": 20, "h": 10, "fill": "#AABBCC", "radius": 0.3}
            ]
        })
        output = renderer._render_slide(slide)
        assert "rect(" in output
        assert "radius:" in output

    def test_text_shape_emits_typst_text(self, renderer):
        slide = SlideSpec(slide_type="freeform", data={
            "title": "T",
            "shapes": [
                {"type": "text", "x": 10, "y": 10, "w": 50, "h": 10,
                 "text": "Hello World", "size": 18, "color": "#FFFFFF"}
            ]
        })
        output = renderer._render_slide(slide)
        assert "Hello World" in output
        assert "18" in output  # size appears as 18pt or 18.0pt

    def test_line_shape(self, renderer):
        slide = SlideSpec(slide_type="freeform", data={
            "title": "T",
            "shapes": [
                {"type": "line", "x1": 0, "y1": 50, "x2": 100, "y2": 50, "color": "#000000"}
            ]
        })
        output = renderer._render_slide(slide)
        assert "line(" in output

    def test_arrow_shape(self, renderer):
        slide = SlideSpec(slide_type="freeform", data={
            "title": "T",
            "shapes": [
                {"type": "arrow", "x1": 0, "y1": 50, "x2": 100, "y2": 50}
            ]
        })
        output = renderer._render_slide(slide)
        assert "line(" in output

    def test_circle_shape(self, renderer):
        slide = SlideSpec(slide_type="freeform", data={
            "title": "T",
            "shapes": [{"type": "circle", "cx": 50, "cy": 50, "r": 10, "fill": "#00FF00"}]
        })
        output = renderer._render_slide(slide)
        assert "circle(" in output

    def test_image_shape_with_path(self, renderer, tmp_image):
        slide = SlideSpec(slide_type="freeform", data={
            "title": "T",
            "shapes": [
                {"type": "image", "x": 0, "y": 0, "w": 100, "h": 100, "path": str(tmp_image)}
            ]
        })
        output = renderer._render_slide(slide)
        assert "image(" in output

    def test_image_shape_without_path_emits_placeholder_rect(self, renderer):
        slide = SlideSpec(slide_type="freeform", data={
            "title": "T",
            "shapes": [
                {"type": "image", "x": 0, "y": 0, "w": 100, "h": 100}
            ]
        })
        output = renderer._render_slide(slide)
        # Empty path should emit a placeholder rect
        assert "rect(" in output

    def test_title_in_output(self, renderer):
        slide = SlideSpec(slide_type="freeform", data={
            "title": "My Hero Exhibit",
            "shapes": []
        })
        output = renderer._render_slide(slide)
        assert "My Hero Exhibit" in output

    def test_no_title_renders_without_error(self, renderer):
        slide = SlideSpec(slide_type="freeform", data={"shapes": []})
        output = renderer._render_slide(slide)
        assert output  # non-empty string


# ---------------------------------------------------------------------------
# PPTX freeform renderer
# ---------------------------------------------------------------------------

class TestPptxFreeformRenderer:
    def test_add_freeform_slide_no_shapes(self, tmp_path):
        from inkline.pptx.builder import PptxBuilder
        builder = PptxBuilder()
        builder.add_freeform_slide(title="Test Slide", shapes=[])
        out = tmp_path / "test.pptx"
        builder.save(out)
        assert out.exists()
        assert out.stat().st_size > 0

    def test_add_freeform_slide_with_rect(self, tmp_path):
        from inkline.pptx.builder import PptxBuilder
        builder = PptxBuilder()
        builder.add_freeform_slide(
            title="Freeform",
            shapes=[{"type": "rect", "x": 10, "y": 10, "w": 20, "h": 10, "fill": "#FF0000"}]
        )
        out = tmp_path / "freeform.pptx"
        builder.save(out)
        assert out.exists()

    def test_add_freeform_slide_with_text(self, tmp_path):
        from inkline.pptx.builder import PptxBuilder
        builder = PptxBuilder()
        builder.add_freeform_slide(
            title="Text Slide",
            shapes=[{"type": "text", "x": 10, "y": 50, "w": 40, "h": 10, "text": "Hello"}]
        )
        out = tmp_path / "text.pptx"
        builder.save(out)
        assert out.exists()

    def test_add_freeform_slide_with_image(self, tmp_path, tmp_image):
        from inkline.pptx.builder import PptxBuilder
        builder = PptxBuilder()
        builder.add_freeform_slide(
            title="Image Slide",
            shapes=[{"type": "image", "x": 0, "y": 0, "w": 100, "h": 100, "path": str(tmp_image)}]
        )
        out = tmp_path / "image.pptx"
        builder.save(out)
        assert out.exists()

    def test_add_freeform_slide_with_circle(self, tmp_path):
        from inkline.pptx.builder import PptxBuilder
        builder = PptxBuilder()
        builder.add_freeform_slide(
            title="Circle Slide",
            shapes=[{"type": "circle", "cx": 50, "cy": 50, "r": 10, "fill": "#0000FF"}]
        )
        out = tmp_path / "circle.pptx"
        builder.save(out)
        assert out.exists()

    def test_freeform_in_backend_coverage(self):
        from inkline.authoring.backend_coverage import COVERAGE
        assert "freeform" in COVERAGE
        assert COVERAGE["freeform"]["typst"] is True
        assert COVERAGE["freeform"]["pptx"] is True
