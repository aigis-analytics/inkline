"""Tests for inkline.authoring.preprocessor — md → (deck_meta, sections[])."""

from __future__ import annotations

import pytest

from inkline.authoring.preprocessor import preprocess


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

PLAIN_MD = """\
# My Deck

## First section
Some narrative about the first topic.

## Second section
More content here.
"""

FRONT_MATTER_MD = """\
---
brand: minimal
template: consulting
title: Q4 Review
audience: investors
---

## Market overview
TAM is $40B growing 32% YoY.

## Three problems we solve
- Fragmented data
- Manual reporting
- Stale insights
"""

COMMENTS_MD = """\
## Market opportunity
<!-- _layout: kpi_strip -->
TAM is $40B, growing 32% YoY.

## Three problems
<!-- _layout: three_card -->
- Problem 1
- Problem 2
- Problem 3
"""

MIXED_MD = """\
---
brand: minimal
template: consulting
title: Test Deck
---

## Market opportunity
<!-- _layout: kpi_strip -->
<!-- _notes: Emphasise the TAM number. -->
TAM is $40B, growing 32% YoY.

## Section break
<!-- footer: '' -->
<!-- _layout: section_divider -->
"""

ASSET_SHORTHAND_MD = """\
## Revenue trend
![bg left:40%](charts/revenue.png)
ARR compounding at 34% per quarter.
"""


# ---------------------------------------------------------------------------
# Plain markdown (backwards compat)
# ---------------------------------------------------------------------------

class TestPlainMarkdown:
    def test_returns_two_sections(self):
        deck_meta, sections = preprocess(PLAIN_MD)
        assert len(sections) == 2

    def test_section_titles(self):
        _, sections = preprocess(PLAIN_MD)
        assert sections[0]["title"] == "First section"
        assert sections[1]["title"] == "Second section"

    def test_section_narratives_contain_content(self):
        _, sections = preprocess(PLAIN_MD)
        assert "first topic" in sections[0]["narrative"]
        assert "More content" in sections[1]["narrative"]

    def test_no_slide_type_set(self):
        _, sections = preprocess(PLAIN_MD)
        for sec in sections:
            assert "slide_type" not in sec

    def test_deck_meta_defaults(self):
        deck_meta, _ = preprocess(PLAIN_MD)
        assert deck_meta.get("brand") == "minimal"
        assert deck_meta.get("template") == "consulting"

    def test_source_lines_present(self):
        _, sections = preprocess(PLAIN_MD)
        for sec in sections:
            assert "source_line_start" in sec
            assert "source_line_end" in sec


# ---------------------------------------------------------------------------
# Front-matter only
# ---------------------------------------------------------------------------

class TestFrontMatter:
    def test_brand_extracted(self):
        deck_meta, _ = preprocess(FRONT_MATTER_MD)
        assert deck_meta["brand"] == "minimal"

    def test_title_extracted(self):
        deck_meta, _ = preprocess(FRONT_MATTER_MD)
        assert deck_meta["title"] == "Q4 Review"

    def test_audience_extracted(self):
        deck_meta, _ = preprocess(FRONT_MATTER_MD)
        assert deck_meta["audience"] == "investors"

    def test_sections_correct_count(self):
        _, sections = preprocess(FRONT_MATTER_MD)
        assert len(sections) == 2


# ---------------------------------------------------------------------------
# HTML-comment directives only
# ---------------------------------------------------------------------------

class TestHTMLCommentDirectives:
    def test_layout_becomes_slide_type(self):
        _, sections = preprocess(COMMENTS_MD)
        assert sections[0].get("slide_type") == "kpi_strip"
        assert sections[1].get("slide_type") == "three_card"

    def test_layout_implies_guided_mode(self):
        _, sections = preprocess(COMMENTS_MD)
        assert sections[0].get("slide_mode") == "guided"

    def test_narrative_still_extracted(self):
        _, sections = preprocess(COMMENTS_MD)
        assert "TAM" in sections[0]["narrative"]


# ---------------------------------------------------------------------------
# Mixed (front-matter + comments)
# ---------------------------------------------------------------------------

class TestMixed:
    def test_brand_from_front_matter(self):
        deck_meta, _ = preprocess(MIXED_MD)
        assert deck_meta["brand"] == "minimal"

    def test_layout_from_comment(self):
        _, sections = preprocess(MIXED_MD)
        assert sections[0].get("slide_type") == "kpi_strip"

    def test_notes_in_directives(self):
        _, sections = preprocess(MIXED_MD)
        directives = sections[0].get("directives", {})
        assert "notes" in directives
        assert "TAM" in directives["notes"]


# ---------------------------------------------------------------------------
# Asset shorthand
# ---------------------------------------------------------------------------

class TestAssetShorthand:
    def test_bg_left_infers_chart_caption(self):
        _, sections = preprocess(ASSET_SHORTHAND_MD)
        assert len(sections) == 1
        sec = sections[0]
        # Asset shorthand should set slide_type to chart_caption
        assert sec.get("slide_type") == "chart_caption"

    def test_image_path_captured(self):
        _, sections = preprocess(ASSET_SHORTHAND_MD)
        directives = sections[0].get("directives", {})
        # image path should be available somewhere
        assert (
            "charts/revenue.png" in str(sections[0])
            or any("revenue" in str(v) for v in directives.values())
        )


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_empty_markdown(self):
        deck_meta, sections = preprocess("")
        assert sections == []

    def test_only_heading(self):
        _, sections = preprocess("## Just a heading\n")
        assert len(sections) == 1
        assert sections[0]["title"] == "Just a heading"

    def test_strict_unknown_directive_raises(self):
        from inkline.authoring.directives import DirectiveError
        md = "## Slide\n<!-- _unknown_xyz: foo -->\nContent."
        with pytest.raises(DirectiveError):
            preprocess(md, strict_directives=True)

    def test_custom_heading_level(self):
        md = "---\nheadingDivider: 3\n---\n\n### Slide A\nContent A.\n\n### Slide B\nContent B.\n"
        _, sections = preprocess(md)
        assert len(sections) == 2
        assert sections[0]["title"] == "Slide A"
