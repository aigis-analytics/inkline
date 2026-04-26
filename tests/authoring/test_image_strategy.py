"""Tests for inkline.authoring.image_strategy — three strategies, success + failure paths."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

import pytest

from inkline.authoring.image_strategy import (
    resolve_image_directive,
    validate_image_directives_in_sections,
    ImageStrategyError,
    ImageResult,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_dir(tmp_path):
    """Temporary directory with a real image file."""
    # Create a minimal PNG (1x1 white pixel)
    png_data = (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
        b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xff\xff'
        b'\x3f\x00\x05\xfe\x02\xfe\xdc\xccY\xe7\x00\x00\x00\x00IEND\xaeB`\x82'
    )
    (tmp_path / "test.png").write_bytes(png_data)
    return tmp_path


# ---------------------------------------------------------------------------
# strategy: reuse
# ---------------------------------------------------------------------------

class TestReuseStrategy:
    def test_reuse_valid_absolute_path(self, tmp_dir):
        directive = {"strategy": "reuse", "path": str(tmp_dir / "test.png")}
        result = resolve_image_directive(directive)
        assert result.strategy == "reuse"
        assert result.path is not None
        assert result.path.exists()

    def test_reuse_valid_relative_path(self, tmp_dir):
        directive = {"strategy": "reuse", "path": "test.png"}
        result = resolve_image_directive(directive, base_dir=tmp_dir)
        assert result.strategy == "reuse"
        assert result.path.exists()

    def test_reuse_missing_path_raises_file_not_found(self, tmp_dir):
        directive = {"strategy": "reuse", "path": "nonexistent.png"}
        with pytest.raises(FileNotFoundError, match="nonexistent"):
            resolve_image_directive(directive, base_dir=tmp_dir)

    def test_reuse_missing_path_key_raises_strategy_error(self):
        directive = {"strategy": "reuse"}  # no path
        with pytest.raises(ImageStrategyError, match="requires 'path'"):
            resolve_image_directive(directive)

    def test_reuse_default_fit_is_cover(self, tmp_dir):
        directive = {"strategy": "reuse", "path": "test.png"}
        result = resolve_image_directive(directive, base_dir=tmp_dir)
        assert result.fit == "cover"

    def test_reuse_explicit_fit(self, tmp_dir):
        directive = {"strategy": "reuse", "path": "test.png", "fit": "contain"}
        result = resolve_image_directive(directive, base_dir=tmp_dir)
        assert result.fit == "contain"

    def test_reuse_slot_parsed(self, tmp_dir):
        directive = {"strategy": "reuse", "path": "test.png", "slot": "left"}
        result = resolve_image_directive(directive, base_dir=tmp_dir)
        assert result.slot == "left"

    def test_reuse_width_pct_parsed(self, tmp_dir):
        directive = {"strategy": "reuse", "path": "test.png", "width": "40%"}
        result = resolve_image_directive(directive, base_dir=tmp_dir)
        assert result.width_pct == pytest.approx(40.0)


# ---------------------------------------------------------------------------
# strategy: generate (dry_run=True to avoid actual API calls)
# ---------------------------------------------------------------------------

class TestGenerateStrategy:
    def test_generate_dry_run_returns_placeholder(self):
        directive = {
            "strategy": "generate",
            "prompt": "Abstract blue geometric background",
        }
        result = resolve_image_directive(directive, dry_run=True)
        # dry_run returns a placeholder instead of calling Gemini
        assert result.strategy == "placeholder"
        assert "Abstract blue" in result.description

    def test_generate_missing_prompt_raises(self):
        directive = {"strategy": "generate"}  # no prompt
        with pytest.raises(ImageStrategyError, match="requires 'prompt'"):
            resolve_image_directive(directive, dry_run=False)

    def test_generate_missing_reference_image_raises(self, tmp_dir):
        directive = {
            "strategy": "generate",
            "prompt": "Background",
            "reference_image_path": "nonexistent_ref.png",
        }
        with pytest.raises(FileNotFoundError):
            resolve_image_directive(directive, base_dir=tmp_dir)


# ---------------------------------------------------------------------------
# strategy: placeholder
# ---------------------------------------------------------------------------

class TestPlaceholderStrategy:
    def test_placeholder_returns_none_path(self):
        directive = {"strategy": "placeholder", "description": "Market sizing diagram"}
        result = resolve_image_directive(directive)
        assert result.strategy == "placeholder"
        assert result.path is None
        assert result.description == "Market sizing diagram"

    def test_placeholder_no_description_uses_default(self):
        directive = {"strategy": "placeholder"}
        result = resolve_image_directive(directive)
        assert result.strategy == "placeholder"
        assert len(result.description) > 0

    def test_placeholder_default_slot(self):
        directive = {"strategy": "placeholder"}
        result = resolve_image_directive(directive)
        assert result.slot == "right"


# ---------------------------------------------------------------------------
# Invalid strategy
# ---------------------------------------------------------------------------

class TestInvalidStrategy:
    def test_invalid_strategy_raises(self):
        with pytest.raises(ImageStrategyError, match="strategy must be"):
            resolve_image_directive({"strategy": "unknown"})

    def test_non_dict_raises(self):
        with pytest.raises(ImageStrategyError):
            resolve_image_directive("not_a_dict")


# ---------------------------------------------------------------------------
# validate_image_directives_in_sections
# ---------------------------------------------------------------------------

class TestValidateInSections:
    def test_no_image_directives_returns_empty(self):
        sections = [{"title": "Slide 1", "narrative": "Content", "directives": {}}]
        warnings = validate_image_directives_in_sections(sections)
        assert warnings == []

    def test_missing_file_raises_immediately(self, tmp_dir):
        sections = [
            {
                "title": "Slide 1",
                "directives": {
                    "image": {"strategy": "reuse", "path": "missing.png"}
                }
            }
        ]
        with pytest.raises(FileNotFoundError):
            validate_image_directives_in_sections(sections, base_dir=tmp_dir)
