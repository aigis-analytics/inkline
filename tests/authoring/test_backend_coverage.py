"""Tests for inkline.authoring.backend_coverage — coverage matrix + downgrade chains."""

from __future__ import annotations

import pytest

from inkline.authoring.backend_coverage import (
    COVERAGE,
    DOWNGRADE,
    get_downgraded_type,
    get_warnings,
    print_coverage_table,
)


# ---------------------------------------------------------------------------
# Matrix completeness — every slide_type in slide_renderer.py must be here
# ---------------------------------------------------------------------------

# All slide types declared in slide_renderer.py FIELD_LIMITS dict + known types
KNOWN_SLIDE_TYPES = {
    "title", "content", "three_card", "four_card", "stat", "table", "split",
    "chart", "closing", "section_divider", "bar_chart", "kpi_strip",
    "chart_caption", "dashboard", "timeline", "comparison", "feature_grid",
    "process_flow", "icon_stat", "progress_bars", "pyramid", "multi_chart",
    "team_grid", "credentials", "testimonial", "before_after",
}


class TestCoverageCompleteness:
    def test_all_known_types_in_matrix(self):
        missing = KNOWN_SLIDE_TYPES - set(COVERAGE.keys())
        assert not missing, f"Slide types missing from COVERAGE matrix: {missing}"

    def test_typst_covers_all(self):
        """Typst is the primary backend — must support everything."""
        not_typst = [t for t, entry in COVERAGE.items() if not entry.get("typst", False)]
        assert not not_typst, f"Typst missing implementations for: {not_typst}"

    def test_downgrade_chain_or_pptx_coverage(self):
        """Every type not natively in PPTX must have a downgrade chain."""
        for slide_type, entry in COVERAGE.items():
            if not entry.get("pptx", False):
                assert (
                    slide_type in DOWNGRADE
                    or get_downgraded_type(slide_type, "pptx") == "content"
                ), f"{slide_type}: not in PPTX and no downgrade chain"

    def test_downgrade_chain_targets_must_be_valid(self):
        """All targets in downgrade chains must themselves be valid slide types."""
        for source, chain in DOWNGRADE.items():
            for target in chain:
                assert target in COVERAGE, f"DOWNGRADE[{source!r}] target {target!r} not in COVERAGE"


# ---------------------------------------------------------------------------
# get_downgraded_type
# ---------------------------------------------------------------------------

class TestGetDowngradedType:
    def test_typst_always_returns_same(self):
        for slide_type in KNOWN_SLIDE_TYPES:
            result = get_downgraded_type(slide_type, "typst")
            assert result == slide_type, f"Typst should not downgrade {slide_type}"

    def test_kpi_strip_pptx_becomes_stat(self):
        result = get_downgraded_type("kpi_strip", "pptx")
        assert result == "stat"

    def test_pyramid_pptx_becomes_three_card(self):
        result = get_downgraded_type("pyramid", "pptx")
        assert result == "three_card"

    def test_multi_chart_pptx_becomes_chart(self):
        result = get_downgraded_type("multi_chart", "pptx")
        assert result == "chart"

    def test_title_pptx_unchanged(self):
        assert get_downgraded_type("title", "pptx") == "title"

    def test_content_pptx_unchanged(self):
        assert get_downgraded_type("content", "pptx") == "content"

    def test_unknown_type_passthrough(self):
        result = get_downgraded_type("totally_new_type", "pptx")
        assert result == "totally_new_type"


# ---------------------------------------------------------------------------
# get_warnings
# ---------------------------------------------------------------------------

class TestGetWarnings:
    def test_all_typst_no_warnings(self):
        slides = [{"slide_type": t} for t in KNOWN_SLIDE_TYPES]
        warnings = get_warnings(slides, "typst")
        assert warnings == []

    def test_pptx_kpi_strip_produces_warning(self):
        slides = [{"slide_type": "kpi_strip"}]
        warnings = get_warnings(slides, "pptx")
        assert len(warnings) == 1
        w = warnings[0]
        assert w["original"] == "kpi_strip"
        assert w["downgraded_to"] == "stat"
        assert "0" in w["warning"] or "1" in w["warning"]

    def test_pptx_mixed_slides(self):
        slides = [
            {"slide_type": "title"},        # supported
            {"slide_type": "kpi_strip"},    # not supported → warn
            {"slide_type": "three_card"},   # supported
            {"slide_type": "pyramid"},      # not supported → warn
        ]
        warnings = get_warnings(slides, "pptx")
        assert len(warnings) == 2
        original_types = {w["original"] for w in warnings}
        assert "kpi_strip" in original_types
        assert "pyramid" in original_types

    def test_warning_has_required_keys(self):
        slides = [{"slide_type": "kpi_strip"}]
        warnings = get_warnings(slides, "pptx")
        w = warnings[0]
        assert "slide_index" in w
        assert "original" in w
        assert "downgraded_to" in w
        assert "warning" in w


# ---------------------------------------------------------------------------
# print_coverage_table
# ---------------------------------------------------------------------------

class TestPrintCoverageTable:
    def test_returns_string(self):
        table = print_coverage_table()
        assert isinstance(table, str)
        assert len(table) > 100

    def test_contains_typst_header(self):
        table = print_coverage_table()
        assert "typst" in table

    def test_contains_pptx_header(self):
        table = print_coverage_table()
        assert "pptx" in table

    def test_contains_all_slide_types(self):
        table = print_coverage_table()
        for slide_type in KNOWN_SLIDE_TYPES:
            assert slide_type in table, f"{slide_type} missing from coverage table"


# ---------------------------------------------------------------------------
# Downgrade-chain integration test: kpi_strip → stat for PPTX
# ---------------------------------------------------------------------------

class TestDowngradeIntegration:
    def test_kpi_strip_pptx_downgrade_chain(self):
        """kpi_strip PPTX export should actually produce a stat slide."""
        from inkline.authoring.backend_coverage import get_downgraded_type
        result = get_downgraded_type("kpi_strip", "pptx")
        assert result == "stat", (
            f"Expected kpi_strip → stat for PPTX, got {result}"
        )
