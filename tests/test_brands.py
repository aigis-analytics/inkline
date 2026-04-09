"""Tests for the brand system.

These tests exercise the public framework only — they do not depend on any
private user brands that may be loaded from ``~/.config/inkline/brands/``.
The only brand guaranteed to be registered in a fresh checkout is ``minimal``.
"""

import pytest

from inkline.brands import (
    BaseBrand,
    get_brand,
    list_brands,
    register_brand,
    brand_search_paths,
    asset_search_paths,
)


# ── Fixture brand: a synthetic brand registered for test isolation ─────────

_FIXTURE = BaseBrand(
    name="__test_fixture",
    display_name="Test Fixture",
    primary="#0B5FFF",
    secondary="#00C2A8",
    background="#FFFFFF",
    surface="#0A2540",
    text="#111827",
    muted="#6B7280",
    border="#E5E7EB",
    light_bg="#F8FAFC",
    heading_font="Inter",
    body_font="Inter",
    confidentiality="Test Confidential",
    footer_text="Test Footer",
    tagline="A fixture",
)
register_brand(_FIXTURE)


# ── Built-in brand (minimal) ────────────────────────────────────────────

def test_minimal_is_always_available():
    assert "minimal" in list_brands()
    brand = get_brand("minimal")
    assert isinstance(brand, BaseBrand)
    assert brand.name == "minimal"


def test_minimal_palette():
    brand = get_brand("minimal")
    assert brand.primary == "#1F2328"
    assert brand.background == "#FFFFFF"


# ── Registry API ────────────────────────────────────────────────────────

def test_list_brands_returns_sorted():
    names = list_brands()
    assert names == sorted(names)
    assert "minimal" in names
    assert "__test_fixture" in names


def test_get_brand_passthrough():
    brand = get_brand("__test_fixture")
    assert get_brand(brand) is brand


def test_get_brand_from_instance():
    assert get_brand(_FIXTURE) is _FIXTURE


def test_unknown_brand_raises():
    with pytest.raises(KeyError):
        get_brand("nonexistent_brand_xyz")


# ── BaseBrand dataclass ─────────────────────────────────────────────────

def test_fixture_palette():
    brand = get_brand("__test_fixture")
    assert brand.primary == "#0B5FFF"
    assert brand.secondary == "#00C2A8"
    assert brand.heading_font == "Inter"


def test_register_custom_brand():
    custom = BaseBrand(
        name="__custom",
        display_name="Custom",
        primary="#FF0000",
        secondary="#00FF00",
        background="#FFFFFF",
        surface="#000000",
        text="#111111",
        muted="#999999",
        border="#CCCCCC",
        light_bg="#F5F5F5",
    )
    register_brand(custom)
    assert get_brand("__custom").primary == "#FF0000"


def test_logo_missing_returns_empty_path():
    # Fixture has no logo_dark_path — should return empty Path
    brand = get_brand("__test_fixture")
    assert str(brand.logo_dark) in ("", ".")


def test_logo_for_bg_dark():
    brand = get_brand("__test_fixture")
    # No logo files, but the helper must still pick a variant without error
    brand.logo_for_bg("#1B283B")  # dark bg
    brand.logo_for_bg("#FFFFFF")  # light bg


# ── Plugin discovery ────────────────────────────────────────────────────

def test_brand_search_paths_is_list():
    assert isinstance(brand_search_paths(), list)


def test_asset_search_paths_includes_package_assets():
    paths = asset_search_paths()
    assert any("assets" in str(p) for p in paths)
