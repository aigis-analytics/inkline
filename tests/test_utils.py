"""Tests for utility functions."""

from inkline.utils import hex_to_rgb, hex_to_rgba_str, luminance, inches_to_emu, pt_to_emu


def test_hex_to_rgb():
    assert hex_to_rgb("#1B283B") == (27, 40, 59)
    assert hex_to_rgb("#FFFFFF") == (255, 255, 255)
    assert hex_to_rgb("#000000") == (0, 0, 0)


def test_hex_to_rgba_str():
    assert hex_to_rgba_str("#3fb950", 0.85) == "rgba(63, 185, 80, 0.85)"


def test_luminance_dark():
    assert luminance("#000000") < 0.1
    assert luminance("#1B283B") < 0.05


def test_luminance_light():
    assert luminance("#FFFFFF") > 0.9
    assert luminance("#FAF8F5") > 0.9


def test_inches_to_emu():
    assert inches_to_emu(1) == 914400
    assert inches_to_emu(0.5) == 457200


def test_pt_to_emu():
    assert pt_to_emu(1) == 12700
