"""Tests for inkline.authoring.asset_shorthand — ``![bg ...]`` parser."""

from __future__ import annotations

import pytest

from inkline.authoring.asset_shorthand import (
    parse_asset_shorthand,
    infer_layout_from_assets,
    AssetShorthand,
)


class TestParseAssetShorthand:
    def test_bg_left_40(self):
        result = parse_asset_shorthand("bg left:40%", "charts/revenue.png")
        assert result is not None
        assert result.side == "left"
        assert result.width_pct == 40
        assert result.image_path == "charts/revenue.png"

    def test_bg_right_no_pct(self):
        result = parse_asset_shorthand("bg right", "img.png")
        assert result is not None
        assert result.side == "right"
        assert result.width_pct == 0

    def test_bg_full(self):
        result = parse_asset_shorthand("bg", "bg.png")
        assert result is not None
        assert result.side == "full"

    def test_cover_mode(self):
        result = parse_asset_shorthand("bg cover", "img.png")
        assert result is not None
        assert result.fill_mode == "cover"

    def test_contain_mode(self):
        result = parse_asset_shorthand("bg contain", "img.png")
        assert result.fill_mode == "contain"

    def test_fit_mode(self):
        result = parse_asset_shorthand("bg fit", "img.png")
        assert result.fill_mode == "fit"

    def test_width_px(self):
        result = parse_asset_shorthand("bg w:800px", "img.png")
        assert result.width_px == 800

    def test_height_px(self):
        result = parse_asset_shorthand("bg h:600px", "img.png")
        assert result.height_px == 600

    def test_blur(self):
        result = parse_asset_shorthand("bg blur:10px", "img.png")
        assert result.blur_px == 10

    def test_brightness(self):
        result = parse_asset_shorthand("bg brightness:0.8", "img.png")
        assert abs(result.brightness - 0.8) < 1e-9

    def test_vertical(self):
        result = parse_asset_shorthand("bg vertical", "img.png")
        assert result.vertical is True

    def test_combined_tokens(self):
        result = parse_asset_shorthand("bg left:40% cover blur:5px", "img.png")
        assert result.side == "left"
        assert result.width_pct == 40
        assert result.fill_mode == "cover"
        assert result.blur_px == 5

    def test_non_bg_returns_none(self):
        result = parse_asset_shorthand("Alt text for a normal image", "img.png")
        assert result is None

    def test_empty_alt_returns_none(self):
        result = parse_asset_shorthand("", "img.png")
        assert result is None

    def test_case_insensitive_bg(self):
        result = parse_asset_shorthand("BG LEFT:30%", "img.png")
        assert result is not None
        assert result.side == "left"
        assert result.width_pct == 30


class TestInferLayoutFromAssets:
    def test_single_left_asset_gives_chart_caption(self):
        a = parse_asset_shorthand("bg left:40%", "chart.png")
        result = infer_layout_from_assets([a])
        assert result["slide_type"] == "chart_caption"
        assert result["image_path"] == "chart.png"

    def test_single_right_asset_gives_chart_caption(self):
        a = parse_asset_shorthand("bg right:60%", "chart.png")
        result = infer_layout_from_assets([a])
        assert result["slide_type"] == "chart_caption"

    def test_single_full_bg_gives_bg_directive(self):
        a = parse_asset_shorthand("bg", "bg.png")
        result = infer_layout_from_assets([a])
        assert "_bg" in result
        assert "slide_type" not in result

    def test_two_assets_gives_multi_chart_equal_2(self):
        a1 = parse_asset_shorthand("bg left", "c1.png")
        a2 = parse_asset_shorthand("bg right", "c2.png")
        result = infer_layout_from_assets([a1, a2])
        assert result["slide_type"] == "multi_chart"
        assert result["multi_layout"] == "equal_2"

    def test_three_assets_gives_equal_3(self):
        assets = [parse_asset_shorthand("bg", f"c{i}.png") for i in range(3)]
        result = infer_layout_from_assets(assets)
        assert result["multi_layout"] == "equal_3"

    def test_four_assets_gives_equal_4(self):
        assets = [parse_asset_shorthand("bg", f"c{i}.png") for i in range(4)]
        result = infer_layout_from_assets(assets)
        assert result["multi_layout"] == "equal_4"

    def test_empty_list_gives_empty_dict(self):
        result = infer_layout_from_assets([])
        assert result == {}
