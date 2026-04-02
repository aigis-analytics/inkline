"""Tests for the brand system."""

from inkline.brands import get_brand, list_brands, BaseBrand


def test_list_brands():
    names = list_brands()
    assert "aigis" in names
    assert "tvf" in names
    assert "minimal" in names


def test_get_brand_by_name():
    brand = get_brand("aigis")
    assert isinstance(brand, BaseBrand)
    assert brand.name == "aigis"
    assert brand.display_name == "Aigis Analytics"
    assert brand.primary == "#1A7FA0"
    assert brand.surface == "#1B283B"


def test_get_brand_passthrough():
    brand = get_brand("tvf")
    assert get_brand(brand) is brand


def test_aigis_palette():
    brand = get_brand("aigis")
    assert brand.primary == "#1A7FA0"
    assert brand.secondary == "#39D3BB"
    assert brand.surface == "#1B283B"
    assert brand.text == "#1A1A1A"


def test_tvf_palette():
    brand = get_brand("tvf")
    assert brand.primary == "#3D5A3E"
    assert brand.secondary == "#B8960C"
    assert brand.heading_font == "Cormorant Garamond"
    assert brand.body_font == "Lato"


def test_logo_paths():
    brand = get_brand("aigis")
    assert brand.logo_dark.exists(), f"Missing: {brand.logo_dark}"
    assert brand.logo_light.exists(), f"Missing: {brand.logo_light}"


def test_logo_for_dark_bg():
    brand = get_brand("aigis")
    # Dark bg should return the dark (light-text) logo
    logo = brand.logo_for_bg("#1B283B")
    assert logo == brand.logo_dark


def test_logo_for_light_bg():
    brand = get_brand("aigis")
    # Light bg should return the light (dark-text) logo
    logo = brand.logo_for_bg("#FFFFFF")
    assert logo == brand.logo_light


def test_unknown_brand_raises():
    import pytest
    with pytest.raises(KeyError):
        get_brand("nonexistent")
