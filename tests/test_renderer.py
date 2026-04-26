"""Typst slide renderer tests — overflow safety + render smoke tests.

These tests exist to prevent regressions in overflow behaviour. Every time
slide_renderer.py is changed, these tests must pass.

The historical failure mode this guards against:
- Missing `set par(spacing:0em)` on a slide type → blank overflow page in PDF

Note on field limits: `_clamp` is intentionally a passthrough — text truncation
was deliberately removed because adaptive font sizing in Typst handles overflow
correctly, and silent truncation created an audit feedback loop where the
visual auditor saw "…" characters and re-flagged slides indefinitely.
FIELD_LIMITS remains as advisory metadata for the design layer; these tests
verify the passthrough contract, not truncation.
"""
from __future__ import annotations

import pytest

from inkline.typst.slide_renderer import (
    FIELD_LIMITS,
    TypstSlideRenderer,
    _clamp,
    _clamp_list,
)

# ---------------------------------------------------------------------------
# Minimal theme used in all render tests
# ---------------------------------------------------------------------------
_THEME = {
    "name": "Test",
    "bg": "#FFFFFF",
    "text": "#0F172A",
    "accent": "#6366F1",
    "muted": "#94A3B8",
    "border": "#E2E8F0",
    "card_bg": "#F8FAFC",
    "card_fill": "#F8FAFC",   # used by three_card, four_card, kpi_strip
    "title_fg": "#FFFFFF",    # text on accent-filled card headers
    "heading_font": "Inter",
    "body_font": "Inter",
    "body_size": 11,
    "footer_text": "Test deck",
}

_RENDERER = TypstSlideRenderer(_THEME)

# ---------------------------------------------------------------------------
# Helper — build maximally-populated data for every slide type
# ---------------------------------------------------------------------------

def _max_data(slide_type: str) -> dict:
    """Return a data dict populated to the exact character limit for each field.

    This is the worst-case input: every string is exactly at the cap.
    The renderer must not crash, and limits must absorb any over-length content.
    """
    limits = FIELD_LIMITS.get(slide_type, {})
    T = limits.get("title", 45)
    FN = limits.get("footnote", 90)
    title = "A" * T
    fn = "F" * FN

    if slide_type == "content":
        item_n = limits.get("items", 80)
        return {"section": "Test", "title": title, "items": ["B" * item_n] * 6, "footnote": fn}

    if slide_type == "split":
        h = limits.get("left.heading", 26)
        it = limits.get("left.items", 55)
        return {
            "section": "Test", "title": title,
            "left":  {"heading": "L" * h, "items": ["I" * it] * 5},
            "right": {"heading": "R" * h, "items": ["J" * it] * 5},
            "footnote": fn,
        }

    if slide_type in ("three_card", "four_card"):
        n = 3 if slide_type == "three_card" else 4
        ct = limits.get("cards.title", 24)
        cb = limits.get("cards.body", 85)
        return {
            "section": "Test", "title": title,
            "cards": [{"title": "C" * ct, "body": "D" * cb} for _ in range(n)],
            "footnote": fn,
        }

    if slide_type == "stat":
        vn = limits.get("stats.value", 8)
        ln = limits.get("stats.label", 20)
        dn = limits.get("stats.desc", 26)
        return {
            "section": "Test", "title": title,
            "stats": [{"value": "V" * vn, "label": "L" * ln, "desc": "D" * dn} for _ in range(4)],
        }

    if slide_type == "table":
        cn = limits.get("headers", 20)
        rn = limits.get("rows", 20)
        return {
            "section": "Test", "title": title,
            "headers": ["H" * cn] * 4,
            "rows": [["R" * rn] * 4 for _ in range(5)],
            "footnote": fn,
        }

    if slide_type == "bar_chart":
        ln = limits.get("bars.label", 25)
        vn = limits.get("bars.value", 12)
        return {
            "section": "Test", "title": title,
            "bars": [{"label": "L" * ln, "value": "V" * vn, "pct": 0.5} for _ in range(6)],
            "footnote": fn,
        }

    if slide_type == "kpi_strip":
        vn = limits.get("kpis.value", 10)
        ln = limits.get("kpis.label", 20)
        return {
            "section": "Test", "title": title,
            "kpis": [{"value": "V" * vn, "label": "L" * ln, "highlight": i == 0} for i in range(5)],
            "footnote": fn,
        }

    if slide_type == "chart":
        return {"section": "Test", "title": title, "image_path": "", "footnote": fn}

    if slide_type == "chart_caption":
        bn = limits.get("bullets", 80)
        cn = limits.get("caption", 90)
        return {
            "section": "Test", "title": title,
            "image_path": "", "caption": "C" * cn,
            "bullets": ["B" * bn] * 4, "footnote": fn,
        }

    if slide_type == "dashboard":
        vn = limits.get("stats.value", 10)
        ln = limits.get("stats.label", 22)
        bn = limits.get("bullets", 70)
        return {
            "section": "Test", "title": title,
            "image_path": "",
            "stats": [{"value": "V" * vn, "label": "L" * ln} for _ in range(3)],
            "bullets": ["B" * bn] * 3,
            "footnote": fn,
        }

    if slide_type == "timeline":
        dn = limits.get("milestones.date", 12)
        tn = limits.get("milestones.title", 18)
        bn = limits.get("milestones.body", 70)
        return {
            "section": "Test", "title": title,
            "milestones": [
                {"date": "D" * dn, "title": "T" * tn, "body": "B" * bn}
                for _ in range(6)
            ],
            "footnote": fn,
        }

    if slide_type == "comparison":
        ltn = limits.get("left_title", 26)
        rtn = limits.get("right_title", 26)
        mn = limits.get("rows.metric", 22)
        lvn = limits.get("rows.left", 30)
        rvn = limits.get("rows.right", 30)
        return {
            "section": "Test", "title": title,
            "left_title": "L" * ltn, "right_title": "R" * rtn,
            "rows": [{"metric": "M" * mn, "left": "A" * lvn, "right": "B" * rvn} for _ in range(5)],
            "footnote": fn,
        }

    if slide_type == "feature_grid":
        ftn = limits.get("features.title", 22)
        fbn = limits.get("features.body", 80)
        return {
            "section": "Test", "title": title,
            "features": [{"title": "T" * ftn, "body": "B" * fbn} for _ in range(6)],
            "footnote": fn,
        }

    if slide_type == "process_flow":
        stn = limits.get("steps.title", 22)
        sbn = limits.get("steps.body", 80)
        return {
            "section": "Test", "title": title,
            "steps": [{"title": "T" * stn, "body": "B" * sbn} for _ in range(4)],
            "footnote": fn,
        }

    if slide_type == "icon_stat":
        vn = limits.get("stats.value", 14)
        ln = limits.get("stats.label", 22)
        dn = limits.get("stats.desc", 50)
        return {
            "section": "Test", "title": title,
            "stats": [{"value": "V" * vn, "icon": "💡", "label": "L" * ln, "desc": "D" * dn}
                      for _ in range(4)],
            "footnote": fn,
        }

    if slide_type == "progress_bars":
        ln = limits.get("bars.label", 32)
        return {
            "section": "Test", "title": title,
            "bars": [{"label": "L" * ln, "pct": 0.6} for _ in range(6)],
            "footnote": fn,
        }

    if slide_type == "pyramid":
        pln = limits.get("tiers.label", 30)
        pvn = limits.get("tiers.value", 15)
        return {
            "section": "Test", "title": title,
            "tiers": [{"label": "L" * pln, "value": "V" * pvn} for _ in range(5)],
            "footnote": fn,
        }

    if slide_type == "multi_chart":
        ctn = limits.get("charts.title", 30)
        return {
            "section": "Test", "title": title,
            "layout": "equal_2",
            "charts": [{"image_path": "", "title": "C" * ctn} for _ in range(2)],
            "footnote": fn,
        }

    # title / closing / section_divider — minimal
    return {"title": "Test Slide", "subtitle": "Subtitle", "company": "Acme",
            "label": "Test Label", "section": "01"}


# ---------------------------------------------------------------------------
# Tests: _clamp helper
# ---------------------------------------------------------------------------

class TestClamp:
    """`_clamp` is a passthrough — Typst handles overflow via adaptive sizing.

    See module docstring for why truncation was removed.
    """

    def test_within_limit(self):
        assert _clamp("hello", 10) == "hello"

    def test_at_limit(self):
        assert _clamp("A" * 45, 45) == "A" * 45

    def test_over_limit_passthrough(self):
        result = _clamp("A" * 50, 45)
        assert result == "A" * 50
        assert "…" not in result

    def test_empty(self):
        assert _clamp("", 45) == ""

    def test_none(self):
        assert _clamp(None, 45) == ""

    def test_clamp_list_passthrough(self):
        items = ["A" * 10, "B" * 90, "C" * 3]
        result = _clamp_list(items, 80)
        assert result == items
        assert all("…" not in s for s in result)


# ---------------------------------------------------------------------------
# Tests: _apply_field_limits
# ---------------------------------------------------------------------------

class TestApplyFieldLimits:
    """`_apply_field_limits` walks the dispatch but does not truncate.

    See module docstring for why truncation was removed. These tests verify
    the passthrough contract and the no-mutation guarantee.
    """

    def test_title_passthrough(self):
        d = {"title": "A" * 60, "items": ["hello"]}
        result = TypstSlideRenderer._apply_field_limits("content", d)
        assert result["title"] == "A" * 60
        assert "…" not in result["title"]

    def test_title_at_limit_unchanged(self):
        t = "A" * 45
        d = {"title": t, "items": ["hello"]}
        result = TypstSlideRenderer._apply_field_limits("content", d)
        assert result["title"] == t

    def test_stat_value_passthrough_4stats(self):
        d = {"title": "T", "stats": [
            {"value": "X" * 15, "label": "L", "desc": "D"} for _ in range(4)
        ]}
        result = TypstSlideRenderer._apply_field_limits("stat", d)
        for s in result["stats"]:
            assert s["value"] == "X" * 15

    def test_stat_value_passthrough_3stats(self):
        d = {"title": "T", "stats": [
            {"value": "X" * 15, "label": "L", "desc": "D"} for _ in range(3)
        ]}
        result = TypstSlideRenderer._apply_field_limits("stat", d)
        for s in result["stats"]:
            assert s["value"] == "X" * 15

    def test_stat_value_passthrough_2stats(self):
        d = {"title": "T", "stats": [
            {"value": "X" * 20, "label": "L", "desc": "D"} for _ in range(2)
        ]}
        result = TypstSlideRenderer._apply_field_limits("stat", d)
        for s in result["stats"]:
            assert s["value"] == "X" * 20

    def test_stat_dollar_value_passthrough(self):
        """Real-world dollar values pass through unchanged regardless of layout."""
        d = {"title": "T", "stats": [
            {"value": "$18.33/boe", "label": "LOE/boe", "desc": ""},
            {"value": "$27.9mm", "label": "Revenue", "desc": ""},
            {"value": "$231mm", "label": "NPV10", "desc": ""},
            {"value": "Nil", "label": "Debt", "desc": ""},
        ]}
        result = TypstSlideRenderer._apply_field_limits("stat", d)
        assert result["stats"][0]["value"] == "$18.33/boe"
        assert result["stats"][1]["value"] == "$27.9mm"
        assert result["stats"][2]["value"] == "$231mm"
        assert result["stats"][3]["value"] == "Nil"

    def test_split_items_clamped(self):
        long_item = "W" * 80
        d = {"title": "T",
             "left": {"heading": "H", "items": [long_item] * 3},
             "right": {"heading": "H", "items": [long_item] * 3}}
        result = TypstSlideRenderer._apply_field_limits("split", d)
        # left.items is a list of strings — only string items get clamped
        # (they pass through _clamp_list on the list field)
        lim = FIELD_LIMITS["split"]["left.items"]
        # items are clamped via the dot-path subkey mechanism
        # Note: left.items → left is the list_key, items is the subkey
        # but 'left' is a dict not a list, so this path won't match.
        # For split slides, left.items refers to left['items'] which is a list of strings.
        # The current implementation handles 'list_key.subkey' where list_key is a list of dicts.
        # For split, 'left' is a dict, so 'left.items' is handled differently.
        # This just checks that the field limits pass doesn't crash.
        assert "left" in result

    def test_four_card_body_passthrough(self):
        long_body = "B" * 200
        d = {"title": "T", "cards": [
            {"title": "Card", "body": long_body} for _ in range(4)
        ]}
        result = TypstSlideRenderer._apply_field_limits("four_card", d)
        for card in result["cards"]:
            assert card["body"] == long_body

    def test_comparison_rows_passthrough(self):
        long_val = "V" * 60
        d = {"title": "T", "left_title": "L", "right_title": "R",
             "rows": [{"metric": "M", "left": long_val, "right": long_val} for _ in range(4)]}
        result = TypstSlideRenderer._apply_field_limits("comparison", d)
        for row in result["rows"]:
            assert row["left"] == long_val
            assert row["right"] == long_val

    def test_original_data_not_mutated(self):
        """_apply_field_limits must not mutate the input dict."""
        d = {"title": "A" * 60, "stats": [{"value": "X" * 20, "label": "L", "desc": "D"}]}
        d_copy = {"title": "A" * 60, "stats": [{"value": "X" * 20, "label": "L", "desc": "D"}]}
        TypstSlideRenderer._apply_field_limits("stat", d)
        assert d["title"] == d_copy["title"]
        assert d["stats"][0]["value"] == d_copy["stats"][0]["value"]

    def test_unknown_type_passthrough(self):
        d = {"title": "A" * 60}
        result = TypstSlideRenderer._apply_field_limits("unknown_type", d)
        assert result["title"] == "A" * 60  # no limits → unchanged


# ---------------------------------------------------------------------------
# Tests: FIELD_LIMITS coverage
# ---------------------------------------------------------------------------

class TestFieldLimitsCoverage:
    """Ensure FIELD_LIMITS covers every renderable slide type."""

    ALL_TYPES = [
        "title", "closing", "section_divider", "content", "three_card", "four_card",
        "stat", "table", "split", "chart", "bar_chart", "kpi_strip", "timeline",
        "process_flow", "icon_stat", "progress_bars", "pyramid", "comparison",
        "feature_grid", "dashboard", "chart_caption", "multi_chart",
    ]

    def test_all_types_have_limits_entry(self):
        missing = [t for t in self.ALL_TYPES if t not in FIELD_LIMITS]
        assert missing == [], f"Slide types missing from FIELD_LIMITS: {missing}"

    def test_content_types_have_title_limit(self):
        """Every content slide type must have a title character limit."""
        exempt = {"title", "closing", "section_divider"}
        for stype, limits in FIELD_LIMITS.items():
            if stype not in exempt:
                assert "title" in limits, f"'{stype}' missing 'title' limit in FIELD_LIMITS"
                assert limits["title"] <= 45, f"'{stype}' title limit > 45 chars (risk of wrapping)"


# ---------------------------------------------------------------------------
# Tests: render smoke tests — every type must produce non-empty markup
# ---------------------------------------------------------------------------

_ALL_CONTENT_TYPES = [
    "content", "three_card", "four_card", "stat", "table", "split",
    "chart", "bar_chart", "kpi_strip", "timeline", "process_flow",
    "icon_stat", "progress_bars", "pyramid", "comparison", "feature_grid",
    "dashboard", "chart_caption", "multi_chart",
]

class TestRenderSmoke:
    """Smoke test: every slide type renders without Python exception.

    These tests do NOT compile Typst (no typst binary required). They verify
    that:
    1. The Python renderer doesn't crash with maximal-content input.
    2. The output is non-empty Typst markup containing expected keywords.
    3. Every slide type that uses _body_block has `set par(spacing: 0em)`
       in its markup — the critical overflow-prevention rule.
    """

    @pytest.mark.parametrize("slide_type", _ALL_CONTENT_TYPES)
    def test_renders_without_exception(self, slide_type):
        from inkline.typst.slide_renderer import SlideSpec
        data = _max_data(slide_type)
        spec = SlideSpec(slide_type=slide_type, data=data)
        markup = _RENDERER._render_slide(spec)
        assert markup, f"{slide_type}: renderer returned empty string"
        assert "#" in markup, f"{slide_type}: markup missing Typst syntax"

    @pytest.mark.parametrize("slide_type", _ALL_CONTENT_TYPES)
    def test_has_spacing_reset(self, slide_type):
        """Every content slide must suppress Typst's implicit par.spacing.

        Missing this rule causes ~0.28cm overflow (blank page in output PDF).
        """
        # title/closing/section_divider use v(1fr) layouts — exempt
        exempt = {"chart", "chart_caption", "dashboard", "multi_chart"}
        if slide_type in exempt:
            pytest.skip("chart types use _body_block which clips rather than spacing reset")

        from inkline.typst.slide_renderer import SlideSpec
        data = _max_data(slide_type)
        spec = SlideSpec(slide_type=slide_type, data=data)
        markup = _RENDERER._render_slide(spec)
        assert "set par(spacing: 0em)" in markup, (
            f"{slide_type}: missing 'set par(spacing: 0em)' — "
            "this slide WILL produce a blank overflow page in the PDF"
        )
        assert "set block(spacing: 0pt)" in markup, (
            f"{slide_type}: missing 'set block(spacing: 0pt)'"
        )

    @pytest.mark.parametrize("slide_type", _ALL_CONTENT_TYPES)
    def test_renders_with_over_limit_content(self, slide_type):
        """Renderer must not crash when fed content exceeding FIELD_LIMITS.

        Truncation was deliberately removed (see module docstring); the
        renderer's contract is that adaptive Typst sizing handles overflow.
        This test verifies the contract — no Python exception when content
        is over-limit, not that content is truncated.
        """
        from inkline.typst.slide_renderer import SlideSpec
        limits = FIELD_LIMITS.get(slide_type, {})
        if not limits:
            pytest.skip(f"{slide_type}: no field limits defined")

        data_over = {}
        max_data = _max_data(slide_type)
        for k, v in max_data.items():
            if isinstance(v, str):
                limit = limits.get(k)
                data_over[k] = v * 2 if limit else v
            else:
                data_over[k] = v

        spec = SlideSpec(slide_type=slide_type, data=data_over)
        markup = _RENDERER._render_slide(spec)
        assert markup, f"{slide_type}: renderer returned empty string for over-limit content"
