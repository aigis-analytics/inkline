"""Tests for inkline.authoring.classes — class registry + Typst fragment composition."""

from __future__ import annotations

import pytest

from inkline.authoring.classes import register, lookup, list_classes, _REGISTRY


class TestRegister:
    def setup_method(self):
        # Clean up test registrations
        _REGISTRY.pop("test_cls_a", None)
        _REGISTRY.pop("test_cls_b", None)
        _REGISTRY.pop("test_cls_multi", None)

    def test_register_and_lookup(self):
        register("test_cls_a", "// fragment A\n")
        result = lookup("test_cls_a")
        assert "fragment A" in result

    def test_register_multiple_and_lookup_combined(self):
        register("test_cls_a", "// fragment A\n")
        register("test_cls_b", "// fragment B\n")
        result = lookup("test_cls_a test_cls_b")
        assert "fragment A" in result
        assert "fragment B" in result

    def test_lookup_unknown_class_returns_empty(self):
        result = lookup("totally_unknown_class_xyz")
        assert result == ""

    def test_lookup_empty_string_returns_empty(self):
        result = lookup("")
        assert result == ""

    def test_lookup_whitespace_only_returns_empty(self):
        result = lookup("   ")
        assert result == ""

    def test_register_strips_whitespace_from_name(self):
        register("  test_cls_multi  ", "// fragment multi\n")
        result = lookup("test_cls_multi")
        assert "fragment multi" in result

    def test_overwrite_existing_class(self):
        register("test_cls_a", "// original\n")
        register("test_cls_a", "// overwritten\n")
        result = lookup("test_cls_a")
        assert "overwritten" in result
        assert "original" not in result


class TestBuiltinClasses:
    """Test built-in classes registered at import time."""

    def test_lead_is_registered(self):
        assert "lead" in _REGISTRY

    def test_invert_is_registered(self):
        assert "invert" in _REGISTRY

    def test_dark_is_registered(self):
        assert "dark" in _REGISTRY

    def test_lead_has_typst_fragment(self):
        result = lookup("lead")
        assert len(result) > 0

    def test_list_classes_contains_builtins(self):
        classes = list_classes()
        assert "lead" in classes
        assert "invert" in classes
        assert "dark" in classes


class TestTypstFragmentComposition:
    """Test that class fragments compose correctly for Typst rendering."""

    def test_single_class_fragment_is_valid_typst_comment(self):
        register("test_cls_a", "// Test fragment for Typst\n#show text: set text(color: red)\n")
        result = lookup("test_cls_a")
        assert "#show" in result

    def test_multiple_classes_joined_by_newline(self):
        register("test_cls_a", "// A\n")
        register("test_cls_b", "// B\n")
        result = lookup("test_cls_a test_cls_b")
        # Both fragments should be present; they're joined by \n
        lines = result.splitlines()
        assert len(lines) >= 2
