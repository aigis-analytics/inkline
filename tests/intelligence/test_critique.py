"""Tests for critique_pdf — post-render Vishwakarma audit (Phase 4)."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from inkline.intelligence.vishwakarma import (
    critique_pdf,
    CritiqueResult,
    SlideCritique,
    _parse_verdict,
    _RUBRICS,
)


# ---------------------------------------------------------------------------
# CritiqueResult dataclass
# ---------------------------------------------------------------------------

class TestCritiqueResult:
    def test_to_dict_has_required_keys(self):
        result = CritiqueResult(
            overall_score=85,
            rubric="institutional",
            brand="minimal",
            pdf_path="/path/to/deck.pdf",
        )
        d = result.to_dict()
        assert "overall_score" in d
        assert "rubric" in d
        assert "brand" in d
        assert "pdf_path" in d
        assert "slide_critiques" in d
        assert "error" in d

    def test_to_dict_slide_critiques_serialized(self):
        result = CritiqueResult(
            overall_score=80,
            rubric="tech_pitch",
            brand="",
            pdf_path="/tmp/deck.pdf",
            slide_critiques=[
                SlideCritique(
                    slide_index=1,
                    verdict="WARN",
                    comment="Wall of bullets",
                    fix_hint="_layout: three_card",
                )
            ],
        )
        d = result.to_dict()
        assert len(d["slide_critiques"]) == 1
        sc = d["slide_critiques"][0]
        assert sc["verdict"] == "WARN"
        assert sc["fix_hint"] == "_layout: three_card"
        assert sc["slide_index"] == 1


# ---------------------------------------------------------------------------
# _parse_verdict
# ---------------------------------------------------------------------------

class TestParseVerdict:
    def test_parse_json_response(self):
        raw = '{"verdict": "PASS", "comment": "Clean layout.", "fix_hint": ""}'
        result = _parse_verdict(raw)
        assert result["verdict"] == "PASS"

    def test_parse_fail_keyword(self):
        result = _parse_verdict("This slide has ERROR: text overflow")
        assert result["verdict"] == "FAIL"

    def test_parse_warn_keyword(self):
        result = _parse_verdict("WARNING: too many bullets on this slide")
        assert result["verdict"] == "WARN"

    def test_parse_default_pass(self):
        result = _parse_verdict("The slide looks clean and well-structured.")
        assert result["verdict"] == "PASS"

    def test_parse_json_embedded_in_prose(self):
        raw = 'Overall this looks good. {"verdict": "WARN", "comment": "Minor issue", "fix_hint": ""} Done.'
        result = _parse_verdict(raw)
        assert result["verdict"] == "WARN"


# ---------------------------------------------------------------------------
# critique_pdf — missing file
# ---------------------------------------------------------------------------

class TestCritiquePdfMissingFile:
    def test_missing_pdf_returns_error(self):
        result = critique_pdf("/nonexistent/path/deck.pdf")
        assert result.overall_score == 0
        assert "not found" in result.error.lower()

    def test_missing_pdf_has_correct_structure(self):
        result = critique_pdf("/nonexistent/path/deck.pdf")
        d = result.to_dict()
        assert d["overall_score"] == 0
        assert d["error"]  # non-empty error string


# ---------------------------------------------------------------------------
# critique_pdf — with mocked vision
# ---------------------------------------------------------------------------

class TestCritiquePdfWithMockedVision:
    @pytest.fixture
    def minimal_pdf(self, tmp_path):
        """Create a minimal valid PDF for testing."""
        # Create a 1-page PDF using reportlab or fallback to a raw minimal PDF
        pdf_path = tmp_path / "test.pdf"
        # Minimal PDF bytes that pymupdf can open
        minimal_pdf_bytes = (
            b"%PDF-1.4\n"
            b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
            b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
            b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n"
            b"xref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n"
            b"0000000058 00000 n\n0000000115 00000 n\n"
            b"trailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n190\n%%EOF\n"
        )
        pdf_path.write_bytes(minimal_pdf_bytes)
        return pdf_path

    def _mock_vision(self, image_b64: str, prompt: str) -> str:
        """Mock vision function returning a structured verdict."""
        return json.dumps({
            "verdict": "PASS",
            "comment": "Clean, well-structured slide.",
            "fix_hint": "",
        })

    def _mock_vision_warn(self, image_b64: str, prompt: str) -> str:
        """Mock vision function returning a WARN verdict."""
        return json.dumps({
            "verdict": "WARN",
            "comment": "Consider using a more visual layout.",
            "fix_hint": "_layout: three_card",
        })

    def test_critique_with_mocked_vision_returns_result(self, minimal_pdf):
        """critique_pdf with mocked vision returns a valid CritiqueResult."""
        try:
            result = critique_pdf(
                str(minimal_pdf),
                rubric="institutional",
                brand="minimal",
                vision_fn=self._mock_vision,
            )
        except ImportError:
            pytest.skip("pymupdf not available")
        assert isinstance(result, CritiqueResult)
        assert result.overall_score >= 0
        assert result.overall_score <= 100

    def test_critique_score_reduced_for_warns(self, minimal_pdf):
        """WARN verdicts should reduce the overall score."""
        try:
            result = critique_pdf(
                str(minimal_pdf),
                rubric="tech_pitch",
                brand="",
                vision_fn=self._mock_vision_warn,
            )
        except ImportError:
            pytest.skip("pymupdf not available")
        # Score should be less than 100 due to warns
        assert result.overall_score < 100

    def test_all_rubrics_accepted(self, minimal_pdf):
        """All three rubrics should run without error."""
        for rubric in ("institutional", "tech_pitch", "internal_review"):
            try:
                result = critique_pdf(
                    str(minimal_pdf),
                    rubric=rubric,
                    vision_fn=self._mock_vision,
                )
                assert result.rubric == rubric
            except ImportError:
                pytest.skip("pymupdf not available")


# ---------------------------------------------------------------------------
# Rubrics
# ---------------------------------------------------------------------------

class TestRubrics:
    def test_all_rubrics_present(self):
        assert "institutional" in _RUBRICS
        assert "tech_pitch" in _RUBRICS
        assert "internal_review" in _RUBRICS

    def test_each_rubric_non_empty(self):
        for name, text in _RUBRICS.items():
            assert len(text) > 50, f"Rubric {name!r} is too short"
