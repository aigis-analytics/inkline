"""Tests for inkline.authoring.directives — grammar, scopes, plugin registry."""

from __future__ import annotations

import warnings
import pytest


# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from inkline.authoring.directives import (
    resolve_directive,
    list_directives,
    register,
    DirectiveError,
    _PLUGIN_GLOBAL,
    _PLUGIN_LOCAL,
)


# ---------------------------------------------------------------------------
# resolve_directive — built-ins
# ---------------------------------------------------------------------------

class TestResolveBuiltins:
    def test_global_brand(self):
        name, val = resolve_directive("brand", "aigis", {})
        assert name == "brand"
        assert val == "aigis"

    def test_global_mode_valid(self):
        name, val = resolve_directive("mode", "rules", {})
        assert val == "rules"

    def test_global_mode_invalid_warns(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            name, val = resolve_directive("mode", "bogus", {})
        assert any("bogus" in str(warning.message) for warning in w)

    def test_global_mode_invalid_strict_raises(self):
        with pytest.raises(DirectiveError, match="bogus"):
            resolve_directive("mode", "bogus", {}, strict=True)

    def test_global_heading_divider_coercion(self):
        _, val = resolve_directive("headingDivider", "3", {})
        assert val == 3

    def test_global_output_string_to_list(self):
        _, val = resolve_directive("output", "pdf,pptx", {})
        assert val == ["pdf", "pptx"]

    def test_local_layout_no_prefix(self):
        name, val = resolve_directive("layout", "kpi_strip", {})
        assert name == "layout"
        assert val == "kpi_strip"

    def test_spot_layout_underscore(self):
        name, val = resolve_directive("_layout", "three_card", {})
        assert name == "_layout"
        assert val == "three_card"

    def test_local_notes(self):
        name, val = resolve_directive("notes", "Important context here.", {})
        assert name == "notes"
        assert val == "Important context here."

    def test_spot_notes_underscore(self):
        name, val = resolve_directive("_notes", "Spot notes.", {})
        assert name == "_notes"

    def test_unknown_directive_warns(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            name, val = resolve_directive("totally_unknown", "value", {})
        assert any("totally_unknown" in str(warning.message) for warning in w)
        assert name == "unknown.totally_unknown"

    def test_unknown_directive_strict_raises(self):
        with pytest.raises(DirectiveError, match="totally_unknown"):
            resolve_directive("totally_unknown", "value", {}, strict=True)

    def test_backend_specific_layout_passthrough(self):
        # _layout_pptx should pass through unchanged
        name, val = resolve_directive("_layout_pptx", "table", {})
        assert name == "_layout_pptx"
        assert val == "table"


# ---------------------------------------------------------------------------
# resolve_directive — spot prefix stripping
# ---------------------------------------------------------------------------

class TestSpotPrefix:
    def test_spot_mode(self):
        name, val = resolve_directive("_mode", "exact", {})
        assert name == "_mode"
        assert val == "exact"

    def test_spot_accent(self):
        name, val = resolve_directive("_accent", "#ff0000", {})
        assert name == "_accent"

    def test_spot_class(self):
        name, val = resolve_directive("_class", "lead invert", {})
        assert name == "_class"


# ---------------------------------------------------------------------------
# Plugin registry
# ---------------------------------------------------------------------------

class TestPluginRegistry:
    def setup_method(self):
        # Clean up any test registrations
        _PLUGIN_GLOBAL.pop("test_global_dir", None)
        _PLUGIN_LOCAL.pop("test_local_dir", None)

    def test_register_global(self):
        @register(scope="global", name="test_global_dir")
        def my_dir(value, ctx):
            return {"brand_extra": value}

        assert "test_global_dir" in _PLUGIN_GLOBAL

        name, val = resolve_directive("test_global_dir", "foo", {})
        assert name == "test_global_dir"
        assert isinstance(val, dict)
        assert val["brand_extra"] == "foo"

    def test_register_local(self):
        @register(scope="local", name="test_local_dir")
        def my_local(value, ctx):
            return {"risk_level": value}

        assert "test_local_dir" in _PLUGIN_LOCAL

    def test_register_invalid_scope_raises(self):
        with pytest.raises(ValueError, match="scope must be"):
            @register(scope="invalid", name="x")
            def fn(v, c):
                return {}

    def test_plugin_raises_directive_error(self):
        @register(scope="local", name="test_strict_dir")
        def strict_dir(value, ctx):
            if value not in ("low", "medium", "high"):
                raise DirectiveError(f"invalid: {value}")
            return {"level": value}

        with pytest.raises(DirectiveError, match="invalid: bad"):
            resolve_directive("test_strict_dir", "bad", {})


# ---------------------------------------------------------------------------
# list_directives
# ---------------------------------------------------------------------------

class TestListDirectives:
    def test_returns_dict_with_three_keys(self):
        d = list_directives()
        assert "global" in d
        assert "local" in d
        assert "spot" in d

    def test_global_contains_brand(self):
        d = list_directives()
        assert "brand" in d["global"]

    def test_spot_forms_have_underscore_prefix(self):
        d = list_directives()
        for name in d["spot"]:
            assert name.startswith("_"), f"Expected spot directive to start with '_': {name}"
