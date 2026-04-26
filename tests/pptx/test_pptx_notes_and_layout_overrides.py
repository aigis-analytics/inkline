"""Tests for PPTX _notes + _layout_pptx end-to-end handling."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

# Skip if python-pptx is not installed
pytest.importorskip("pptx")

from pptx import Presentation
from inkline.pptx.builder import PptxBuilder, resolve_pptx_layout


# ---------------------------------------------------------------------------
# resolve_pptx_layout
# ---------------------------------------------------------------------------

class TestResolvePptxLayout:
    def test_supported_type_unchanged(self):
        spec = {"slide_type": "title", "data": {}}
        assert resolve_pptx_layout(spec) == "title"

    def test_kpi_strip_downgrades_to_stat(self):
        spec = {"slide_type": "kpi_strip", "data": {}}
        result = resolve_pptx_layout(spec)
        assert result == "stat"

    def test_pyramid_downgrades_to_three_card(self):
        spec = {"slide_type": "pyramid", "data": {}}
        result = resolve_pptx_layout(spec)
        assert result == "three_card"

    def test_layout_pptx_overrides_downgrade(self):
        spec = {
            "slide_type": "kpi_strip",
            "data": {"_layout_pptx": "table"},
        }
        result = resolve_pptx_layout(spec)
        assert result == "table"

    def test_directives_layout_pptx_override(self):
        spec = {
            "slide_type": "kpi_strip",
            "data": {},
            "directives": {"_layout_pptx": "content"},
        }
        result = resolve_pptx_layout(spec)
        assert result == "content"

    def test_unknown_type_passthrough(self):
        spec = {"slide_type": "totally_new_type", "data": {}}
        result = resolve_pptx_layout(spec)
        assert isinstance(result, str)

    def test_no_slide_type_defaults_to_content(self):
        spec = {"data": {}}
        result = resolve_pptx_layout(spec)
        assert result == "content"


# ---------------------------------------------------------------------------
# PptxBuilder.set_slide_notes
# ---------------------------------------------------------------------------

class TestPptxNotes:
    def _make_builder(self) -> PptxBuilder:
        return PptxBuilder(brand="minimal")

    def test_set_slide_notes_writes_text(self):
        builder = self._make_builder()
        builder.add_title_slide(
            company="Test Co",
            tagline="Test tagline",
            date="2026-04-26",
        )
        # Access via _slides_list
        slide = builder._slides_list[0]
        builder.set_slide_notes(slide, "These are speaker notes.")

        notes_text = slide.notes_slide.notes_text_frame.text
        assert "speaker notes" in notes_text

    def test_set_slide_notes_empty_string_no_error(self):
        builder = self._make_builder()
        builder.add_title_slide("Test Co", "Tagline", "2026-04-26")
        slide = builder._slides_list[0]
        # Should not raise
        builder.set_slide_notes(slide, "")

    def test_set_slide_notes_at(self):
        builder = self._make_builder()
        builder.add_title_slide("Co", "Tag", "2026")
        builder.add_content_slide("S1", "Slide 2", ["bullet"])

        builder.set_slide_notes_at(0, "Notes for slide 0")
        builder.set_slide_notes_at(1, "Notes for slide 1")

        assert "Notes for slide 0" in builder._slides_list[0].notes_slide.notes_text_frame.text
        assert "Notes for slide 1" in builder._slides_list[1].notes_slide.notes_text_frame.text

    def test_apply_notes_from_slides_with_notes_key(self):
        builder = self._make_builder()
        builder.add_title_slide("Co", "Tag", "2026")
        builder.add_content_slide("S1", "Slide 2", ["bullet"])

        slide_specs = [
            {"slide_type": "title",   "data": {"company": "Co", "notes": "Title notes"}},
            {"slide_type": "content", "data": {"title": "Slide 2", "_notes": "Content notes"}},
        ]

        builder.apply_notes_from_slides(slide_specs)

        assert "Title notes" in builder._slides_list[0].notes_slide.notes_text_frame.text
        assert "Content notes" in builder._slides_list[1].notes_slide.notes_text_frame.text

    def test_apply_notes_from_directives(self):
        builder = self._make_builder()
        builder.add_title_slide("Co", "Tag", "2026")

        slide_specs = [
            {
                "slide_type": "title",
                "data": {"company": "Co"},
                "directives": {"notes": "Notes from directives"},
            },
        ]

        builder.apply_notes_from_slides(slide_specs)

        assert "Notes from directives" in builder._slides_list[0].notes_slide.notes_text_frame.text

    def test_notes_survive_save_reload(self):
        builder = self._make_builder()
        builder.add_title_slide("Co", "Tag", "2026")
        slide = builder._slides_list[0]
        builder.set_slide_notes(slide, "Persistent notes for this slide.")

        with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as f:
            tmp_path = f.name

        try:
            builder.save(tmp_path)
            prs = Presentation(tmp_path)
            first_slide = prs.slides[0]
            notes_text = first_slide.notes_slide.notes_text_frame.text
            assert "Persistent notes" in notes_text
        finally:
            Path(tmp_path).unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Downgrade chain integration: kpi_strip → stat for PPTX export
# ---------------------------------------------------------------------------

class TestDowngradeIntegration:
    def test_kpi_strip_pptx_downgrade_returns_stat(self):
        """kpi_strip export to PPTX should use stat layout (downgrade chain)."""
        spec = {
            "slide_type": "kpi_strip",
            "data": {
                "section": "KPIs",
                "title": "Key metrics",
                "kpis": [
                    {"value": "34%", "label": "Growth"},
                    {"value": "$4.2M", "label": "ARR"},
                ],
            },
        }
        # The resolved PPTX layout should be "stat"
        result = resolve_pptx_layout(spec)
        assert result == "stat", f"Expected 'stat', got {result!r}"
