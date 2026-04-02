"""Tests for Inkline Slides module.

These tests validate the element builders and builder API without
hitting the Google Slides API (no credentials needed).
"""

import pytest
from inkline.slides.elements import (
    create_slide,
    create_text_box,
    create_shape,
    create_image,
    create_table,
    create_line,
    set_slide_background,
    _rgb_color,
    _text_style,
)
from inkline.slides.builder import SlideBuilder, SlideContext
from inkline.slides.templates import list_templates, get_template
from inkline.utils import inches_to_emu


# ── Element tests ───────────────────────────────────────────────────────


class TestElements:
    def test_rgb_color(self):
        c = _rgb_color("#FF8000")
        assert abs(c["red"] - 1.0) < 0.01
        assert abs(c["green"] - 0.502) < 0.01
        assert abs(c["blue"] - 0.0) < 0.01

    def test_rgb_color_black(self):
        c = _rgb_color("#000000")
        assert c == {"red": 0.0, "green": 0.0, "blue": 0.0}

    def test_text_style_full(self):
        style, fields = _text_style(
            font="Inter", size_pt=14, bold=True, color="#FF0000",
        )
        assert style["fontFamily"] == "Inter"
        assert style["fontSize"]["magnitude"] == 14
        assert style["bold"] is True
        assert "foregroundColor" in style
        assert "fontFamily" in fields
        assert "bold" in fields

    def test_text_style_empty(self):
        style, fields = _text_style()
        assert style == {}
        assert fields == ""

    def test_create_slide(self):
        slide_id, req = create_slide(insertion_index=2)
        assert slide_id.startswith("inkline_")
        assert req["createSlide"]["slideLayoutReference"]["predefinedLayout"] == "BLANK"
        assert req["createSlide"]["insertionIndex"] == 2

    def test_create_text_box(self):
        elem_id, reqs = create_text_box(
            "slide_1", "Hello World",
            x=1.0, y=2.0, w=5.0, h=1.0,
            font="Inter", size_pt=24, bold=True,
        )
        assert elem_id.startswith("inkline_")
        # Should have: createShape, insertText, updateTextStyle
        assert len(reqs) >= 3
        assert reqs[0]["createShape"]["shapeType"] == "TEXT_BOX"
        assert reqs[1]["insertText"]["text"] == "Hello World"

    def test_create_text_box_with_alignment(self):
        _, reqs = create_text_box(
            "slide_1", "Centered",
            alignment="CENTER",
        )
        alignment_reqs = [r for r in reqs if "updateParagraphStyle" in r]
        assert len(alignment_reqs) == 1
        assert alignment_reqs[0]["updateParagraphStyle"]["style"]["alignment"] == "CENTER"

    def test_create_shape(self):
        elem_id, reqs = create_shape(
            "slide_1", "RECTANGLE",
            x=0, y=0, w=10.0, h=1.0,
            fill_color="#1B283B",
        )
        assert len(reqs) == 2  # createShape + updateShapeProperties
        assert "shapeBackgroundFill" in reqs[1]["updateShapeProperties"]["shapeProperties"]

    def test_create_image(self):
        elem_id, req = create_image(
            "slide_1", "https://example.com/img.png",
            x=1.0, y=1.0, w=4.0, h=3.0,
        )
        assert req["createImage"]["url"] == "https://example.com/img.png"
        assert req["createImage"]["elementProperties"]["pageObjectId"] == "slide_1"

    def test_create_table(self):
        table_id, reqs = create_table(
            "slide_1",
            headers=["Name", "Value"],
            rows=[["NPV", "$32M"], ["IRR", "18%"]],
            header_bg="#1B283B",
        )
        # createTable + 2 header insertText + 2 header styles + 2 header bg + 4 data cells + 4 data styles
        assert reqs[0]["createTable"]["rows"] == 3  # 1 header + 2 data
        assert reqs[0]["createTable"]["columns"] == 2

    def test_create_line(self):
        line_id, reqs = create_line(
            "slide_1",
            x1=0.5, y1=1.0, x2=9.5, y2=1.0,
            color="#D1D5DB", weight_pt=1.0,
        )
        assert reqs[0]["createLine"]["lineCategory"] == "STRAIGHT"

    def test_set_slide_background(self):
        req = set_slide_background("slide_1", "#0D1117")
        assert req["updatePageProperties"]["objectId"] == "slide_1"
        assert "pageBackgroundFill" in req["updatePageProperties"]["pageProperties"]


# ── Builder tests (no API calls) ────────────────────────────────────────


class TestBuilder:
    def test_builder_init(self):
        builder = SlideBuilder(title="Test", brand="aigis")
        assert builder._title == "Test"
        assert builder._brand.name == "aigis"

    def test_builder_slide_chaining(self):
        builder = SlideBuilder(title="Test")
        ctx = builder.slide()
        assert isinstance(ctx, SlideContext)
        assert len(builder._slides) == 1

        ctx2 = ctx.slide()
        assert len(builder._slides) == 2

    def test_builder_element_chaining(self):
        builder = SlideBuilder(title="Test")
        ctx = (
            builder.slide()
            .title("Hello")
            .subtitle("World")
            .text("Body text", x=1, y=2, w=8, h=3)
            .bullet_list(["A", "B", "C"])
            .divider()
        )
        assert len(ctx._elements) == 5
        assert ctx._elements[0]["type"] == "title"
        assert ctx._elements[1]["type"] == "subtitle"
        assert ctx._elements[2]["type"] == "text"
        assert ctx._elements[3]["type"] == "bullets"
        assert ctx._elements[4]["type"] == "divider"

    def test_builder_table_element(self):
        builder = SlideBuilder()
        ctx = builder.slide().table(
            headers=["A", "B"],
            rows=[["1", "2"]],
        )
        assert ctx._elements[0]["type"] == "table"
        assert ctx._elements[0]["headers"] == ["A", "B"]

    def test_builder_chart_element(self):
        builder = SlideBuilder()
        ctx = builder.slide().chart(
            headers=["Year", "Revenue"],
            rows=[[2024, 100], [2025, 150]],
            chart_type="LINE",
        )
        assert ctx._elements[0]["type"] == "chart"
        assert ctx._elements[0]["chart_type"] == "LINE"

    def test_builder_background_element(self):
        builder = SlideBuilder()
        ctx = builder.slide().background("#0D1117")
        assert ctx._elements[0] == {"type": "background", "color": "#0D1117"}

    def test_builder_no_credentials_raises(self):
        builder = SlideBuilder(title="Test")
        builder.slide().title("Hello")
        with pytest.raises(RuntimeError, match="authenticate"):
            builder.build()

    def test_builder_with_template(self):
        builder = SlideBuilder(title="Test", template="newspaper")
        assert builder._template_name == "newspaper"

    def test_builder_multiple_slides(self):
        builder = SlideBuilder()
        (
            builder.slide().title("Slide 1")
            .slide().title("Slide 2")
            .slide().title("Slide 3")
        )
        assert len(builder._slides) == 3


# ── Template tests ──────────────────────────────────────────────────────


class TestTemplates:
    def test_list_templates(self):
        templates = list_templates()
        assert "newspaper" in templates
        assert "minimalism" in templates
        assert "executive" in templates

    def test_get_template_unknown(self):
        with pytest.raises(KeyError, match="Unknown template"):
            get_template("nonexistent")

    def test_newspaper_template(self):
        from inkline.brands import get_brand
        brand = get_brand("aigis")
        func = get_template("newspaper")

        # Title slide
        reqs = func("slide_0", brand, 0, 5)
        assert len(reqs) > 0
        # Should set background
        bg_reqs = [r for r in reqs if "updatePageProperties" in r]
        assert len(bg_reqs) == 1

    def test_minimalism_template(self):
        from inkline.brands import get_brand
        brand = get_brand("aigis")
        func = get_template("minimalism")

        # Content slide
        reqs = func("slide_1", brand, 1, 5)
        assert len(reqs) > 0

    def test_executive_template(self):
        from inkline.brands import get_brand
        brand = get_brand("aigis")
        func = get_template("executive")

        # Title slide (dark bg)
        reqs_title = func("slide_0", brand, 0, 5)
        # Content slide (light bg)
        reqs_content = func("slide_1", brand, 1, 5)
        # Closing slide (dark bg)
        reqs_close = func("slide_4", brand, 4, 5)

        # All should produce requests
        assert len(reqs_title) > 0
        assert len(reqs_content) > 0
        assert len(reqs_close) > 0
