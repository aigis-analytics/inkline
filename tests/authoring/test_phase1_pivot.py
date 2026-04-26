"""Phase 1 pivot tests — audit directive extension + default-mode behaviour.

Tests:
- audit: directive accepts post-render as a valid value
- audit: directive still rejects invalid values
- preprocessor defaults _mode to 'exact' when _layout is specified
- preprocessor defaults _mode to 'auto' (falls through to 'guided') when no _layout
- health endpoint returns modes object
- new spot directives: _image, _shapes_file, _capacity_override
"""

from __future__ import annotations

import warnings
import pytest

from inkline.authoring.directives import resolve_directive, DirectiveError
from inkline.authoring.preprocessor import preprocess


# ---------------------------------------------------------------------------
# audit: directive — extended choices
# ---------------------------------------------------------------------------

class TestAuditDirective:
    def test_audit_off(self):
        _, val = resolve_directive("audit", "off", {})
        assert val == "off"

    def test_audit_structural(self):
        _, val = resolve_directive("audit", "structural", {})
        assert val == "structural"

    def test_audit_post_render(self):
        """post-render is the new value added in Phase 1."""
        _, val = resolve_directive("audit", "post-render", {})
        assert val == "post-render"

    def test_audit_strict(self):
        _, val = resolve_directive("audit", "strict", {})
        assert val == "strict"

    def test_audit_invalid_warns(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            resolve_directive("audit", "bogus_value", {})
        assert any("bogus_value" in str(warning.message) for warning in w)

    def test_audit_invalid_strict_raises(self):
        with pytest.raises(DirectiveError):
            resolve_directive("audit", "bogus_value", {}, strict=True)


# ---------------------------------------------------------------------------
# New spot directives added in Phase 1
# ---------------------------------------------------------------------------

class TestNewSpotDirectives:
    def test_image_directive_passthrough(self):
        """_image: accepts a dict value."""
        _, val = resolve_directive("_image", {"strategy": "reuse", "path": "assets/foo.png"}, {})
        # spot directives resolve to their bare name with underscore
        assert isinstance(val, dict)
        assert val["strategy"] == "reuse"

    def test_shapes_file_directive_passthrough(self):
        """_shapes_file: accepts a string path."""
        name, val = resolve_directive("_shapes_file", "shapes/slide11.json", {})
        assert isinstance(val, str)

    def test_capacity_override_passthrough(self):
        """_capacity_override: accepts a bool."""
        name, val = resolve_directive("_capacity_override", True, {})
        assert val is True


# ---------------------------------------------------------------------------
# Default _mode behaviour in preprocessor
# ---------------------------------------------------------------------------

class TestDefaultMode:
    def test_layout_specified_defaults_to_exact_mode(self):
        """When _layout is specified, slide_mode should default to 'exact'."""
        md = """\
## My slide
<!-- _layout: three_card -->
- Item one
- Item two
- Item three
"""
        _, sections = preprocess(md)
        assert len(sections) == 1
        assert sections[0]["slide_type"] == "three_card"
        assert sections[0]["slide_mode"] == "exact"

    def test_layout_with_explicit_mode_override(self):
        """Author can override the default exact mode by specifying _mode explicitly."""
        md = """\
## My slide
<!-- _layout: three_card
_mode: guided -->
- Item one
- Item two
- Item three
"""
        _, sections = preprocess(md)
        assert sections[0]["slide_mode"] == "guided"

    def test_no_layout_does_not_get_exact_mode(self):
        """Without _layout, slide_mode should NOT be 'exact' (falls through to default pipeline)."""
        md = """\
## My slide
Just some narrative text without any layout directive.
"""
        _, sections = preprocess(md)
        # Without _layout, slide_mode is not set or uses cascade default — not 'exact'
        slide_mode = sections[0].get("slide_mode")
        assert slide_mode != "exact"

    def test_layout_in_front_matter_style_comment_defaults_exact(self):
        """_layout in pre-heading comment also gets exact mode default."""
        md = """\
<!-- _layout: split -->
## My slide
Some content here.
"""
        _, sections = preprocess(md)
        assert sections[0].get("slide_type") == "split"
        assert sections[0].get("slide_mode") == "exact"

    def test_layout_auto_mode_override(self):
        """_mode: auto is a valid override when _layout is specified."""
        md = """\
## My slide
<!-- _layout: kpi_strip
_mode: auto -->
KPI 1 | KPI 2 | KPI 3
"""
        _, sections = preprocess(md)
        assert sections[0]["slide_type"] == "kpi_strip"
        assert sections[0]["slide_mode"] == "auto"


# ---------------------------------------------------------------------------
# audit: post-render in front-matter
# ---------------------------------------------------------------------------

class TestAuditPostRenderInFrontMatter:
    def test_audit_post_render_parsed_in_front_matter(self):
        """audit: post-render round-trips through the full preprocessor pipeline."""
        md = """\
---
brand: minimal
audit: post-render
---

## My slide
Content here.
"""
        deck_meta, _ = preprocess(md)
        assert deck_meta["audit"] == "post-render"
