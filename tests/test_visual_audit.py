"""Unit tests for the visual audit pipeline (overflow_audit.py).

Tests cover:
- AuditWarning dataclass: __str__, severity validation
- audit_rendered_pdf: overflow, underflow, exact match, missing file
- audit_chart_image: clipping detection (pixel-level), clean image, missing file
- audit_slide_with_llm: bridge success path, bridge 400 fallback, no-api-key skip,
  missing image file, JSON findings parsing, malformed JSON from bridge
- audit_deck_with_llm: page→slide mapping with and without overflow_slide_indices,
  empty PDF (no pages), partial audit (fewer pages than slides)
"""
from __future__ import annotations

import base64
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from inkline.intelligence.overflow_audit import (
    AuditWarning,
    audit_chart_image,
    audit_deck_with_llm,
    audit_rendered_pdf,
    audit_slide_with_llm,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _white_png(w: int = 100, h: int = 100) -> bytes:
    """Return minimal solid-white PNG bytes."""
    try:
        from PIL import Image
        import io
        img = Image.new("RGB", (w, h), color=(255, 255, 255))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except ImportError:
        # Fallback: 1×1 PNG
        return (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00"
            b"\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
        )


def _png_with_edge_content(w: int = 100, h: int = 100) -> bytes:
    """Return PNG with a non-background pixel on the top edge (simulates chart clipping)."""
    try:
        from PIL import Image
        import io
        img = Image.new("RGB", (w, h), color=(255, 255, 255))
        # Draw a dark pixel in the top-left corner (edge content)
        img.putpixel((2, 2), (0, 0, 0))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except ImportError:
        pytest.skip("PIL not available")


# ---------------------------------------------------------------------------
# AuditWarning
# ---------------------------------------------------------------------------

class TestAuditWarning:
    def test_str_format(self):
        w = AuditWarning(slide_index=3, slide_type="chart_caption",
                         severity="error", message="overflow detected")
        s = str(w)
        assert "[ERROR]" in s
        assert "slide 3" in s
        assert "chart_caption" in s
        assert "overflow detected" in s

    def test_severity_info_uppercase(self):
        w = AuditWarning(slide_index=1, slide_type="content",
                         severity="info", message="ok")
        assert "[INFO]" in str(w)

    def test_severity_warn_uppercase(self):
        w = AuditWarning(slide_index=2, slide_type="table",
                         severity="warn", message="dense")
        assert "[WARN]" in str(w)

    def test_deck_level_index(self):
        w = AuditWarning(slide_index=-1, slide_type="deck",
                         severity="error", message="24 pages rendered, 18 expected")
        assert "slide -1" in str(w)


# ---------------------------------------------------------------------------
# audit_rendered_pdf
# ---------------------------------------------------------------------------

class TestAuditRenderedPdf:
    def test_missing_pdf_returns_empty(self, tmp_path):
        result = audit_rendered_pdf(tmp_path / "nonexistent.pdf", expected_slides=5)
        assert result == []

    def test_exact_match_returns_empty(self, tmp_path):
        """When page count equals slide count, no warnings."""
        pdf = tmp_path / "deck.pdf"
        with patch(
            "inkline.intelligence.overflow_audit._count_pdf_pages",
            return_value=5,
        ):
            pdf.write_bytes(b"%PDF-1.4 fake")
            result = audit_rendered_pdf(pdf, expected_slides=5)
        assert result == []

    def test_overflow_returns_error(self, tmp_path):
        pdf = tmp_path / "deck.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake")
        with patch(
            "inkline.intelligence.overflow_audit._count_pdf_pages",
            return_value=20,
        ):
            result = audit_rendered_pdf(pdf, expected_slides=18)
        assert len(result) == 1
        w = result[0]
        assert w.severity == "error"
        assert "18 slides" in w.message
        assert "20 pages" in w.message
        assert w.slide_type == "deck"
        assert w.slide_index == -1

    def test_underflow_returns_warn(self, tmp_path):
        pdf = tmp_path / "deck.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake")
        with patch(
            "inkline.intelligence.overflow_audit._count_pdf_pages",
            return_value=15,
        ):
            result = audit_rendered_pdf(pdf, expected_slides=18)
        assert len(result) == 1
        assert result[0].severity == "warn"

    def test_no_pdf_reader_returns_empty(self, tmp_path):
        """When _count_pdf_pages returns None (no PDF library), skip audit."""
        pdf = tmp_path / "deck.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake")
        with patch(
            "inkline.intelligence.overflow_audit._count_pdf_pages",
            return_value=None,
        ):
            result = audit_rendered_pdf(pdf, expected_slides=5)
        assert result == []


# ---------------------------------------------------------------------------
# audit_chart_image
# ---------------------------------------------------------------------------

class TestAuditChartImage:
    def test_missing_file_returns_empty(self, tmp_path):
        result = audit_chart_image(tmp_path / "missing.png")
        assert result == []

    def test_clean_white_image_no_warnings(self, tmp_path):
        try:
            import PIL  # noqa: F401
            import numpy  # noqa: F401
        except ImportError:
            pytest.skip("PIL/numpy not available")
        png = tmp_path / "clean.png"
        png.write_bytes(_white_png(200, 100))
        result = audit_chart_image(png)
        assert result == [], f"Expected no warnings, got: {result}"

    def test_edge_content_triggers_warn(self, tmp_path):
        try:
            import PIL  # noqa: F401
            import numpy  # noqa: F401
        except ImportError:
            pytest.skip("PIL/numpy not available")
        png = tmp_path / "clipped.png"
        png.write_bytes(_png_with_edge_content(100, 100))
        result = audit_chart_image(png)
        assert len(result) == 1
        assert result[0].severity == "warn"
        assert "CHART CLIPPING" in result[0].message
        assert "top" in result[0].message  # the top edge has content

    def test_too_small_image_skipped(self, tmp_path):
        """Images smaller than 20×20 are skipped to avoid false positives."""
        try:
            import PIL  # noqa: F401
            import numpy  # noqa: F401
        except ImportError:
            pytest.skip("PIL/numpy not available")
        # Create tiny 5×5 black image
        from PIL import Image
        import io
        img = Image.new("RGB", (5, 5), color=(0, 0, 0))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        png = tmp_path / "tiny.png"
        png.write_bytes(buf.getvalue())
        result = audit_chart_image(png)
        assert result == []


# ---------------------------------------------------------------------------
# audit_slide_with_llm
# ---------------------------------------------------------------------------

class TestAuditSlideWithLlm:
    def test_missing_image_returns_empty(self, tmp_path):
        result = audit_slide_with_llm(tmp_path / "missing.png")
        assert result == []

    def test_bridge_success_returns_parsed_findings(self, tmp_path):
        """Bridge returns valid JSON findings → parsed into AuditWarning list."""
        png = tmp_path / "slide.png"
        png.write_bytes(_white_png())

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "response": json.dumps([
                {"severity": "error", "message": "Legend is cut off"},
                {"severity": "warn", "message": "Axis labels overlap"},
            ])
        }

        with patch("requests.post", return_value=mock_resp):
            result = audit_slide_with_llm(png, slide_index=3, slide_type="chart_caption")

        assert len(result) == 2
        assert result[0].severity == "error"
        assert "Legend" in result[0].message
        assert result[0].slide_index == 3
        assert result[0].slide_type == "chart_caption"
        assert result[1].severity == "warn"

    def test_bridge_empty_findings_returns_empty_list(self, tmp_path):
        """Bridge returns [] JSON → no warnings."""
        png = tmp_path / "slide.png"
        png.write_bytes(_white_png())

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"response": "[]"}

        with patch("requests.post", return_value=mock_resp):
            result = audit_slide_with_llm(png)
        assert result == []

    def test_bridge_non_200_no_api_key_returns_skip_warning(self, tmp_path):
        """Bridge returns 400, no api_key supplied → clean skip info message."""
        png = tmp_path / "slide.png"
        png.write_bytes(_white_png())

        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.json.return_value = {"error": "bad request"}

        with patch("requests.post", return_value=mock_resp):
            result = audit_slide_with_llm(png, slide_index=5, slide_type="table")

        assert len(result) == 1
        assert result[0].severity == "info"
        assert "skipped" in result[0].message.lower()
        assert result[0].slide_index == 5

    def test_bridge_unavailable_no_api_key_returns_skip_warning(self, tmp_path):
        """Bridge connection error, no api_key → clean skip."""
        import requests as _req
        png = tmp_path / "slide.png"
        png.write_bytes(_white_png())

        with patch("requests.post", side_effect=_req.exceptions.ConnectionError("refused")):
            result = audit_slide_with_llm(png, slide_index=2)

        assert len(result) == 1
        assert result[0].severity == "info"
        assert "skipped" in result[0].message.lower()

    def test_bridge_malformed_json_returns_empty(self, tmp_path):
        """Bridge returns 200 but non-JSON response → parse fails, return []."""
        png = tmp_path / "slide.png"
        png.write_bytes(_white_png())

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"response": "I cannot audit this slide."}

        with patch("requests.post", return_value=mock_resp):
            result = audit_slide_with_llm(png)
        assert result == []

    def test_bridge_empty_response_field_falls_through(self, tmp_path):
        """Bridge returns 200 but response="" → falls to API-key check → skip."""
        png = tmp_path / "slide.png"
        png.write_bytes(_white_png())

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"response": ""}

        with patch("requests.post", return_value=mock_resp):
            result = audit_slide_with_llm(png, slide_index=7, api_key=None)

        assert len(result) == 1
        assert result[0].severity == "info"

    def test_severity_normalised_for_unknown_value(self, tmp_path):
        """Findings with unrecognised severity get normalised to 'warn'."""
        png = tmp_path / "slide.png"
        png.write_bytes(_white_png())

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "response": json.dumps([
                {"severity": "critical", "message": "Very bad"},
            ])
        }

        with patch("requests.post", return_value=mock_resp):
            result = audit_slide_with_llm(png)

        assert len(result) == 1
        assert result[0].severity == "warn"  # normalised from "critical"

    def test_findings_without_message_are_skipped(self, tmp_path):
        """Findings with empty message are excluded."""
        png = tmp_path / "slide.png"
        png.write_bytes(_white_png())

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "response": json.dumps([
                {"severity": "warn", "message": ""},
                {"severity": "error", "message": "Real issue"},
            ])
        }

        with patch("requests.post", return_value=mock_resp):
            result = audit_slide_with_llm(png)

        assert len(result) == 1
        assert result[0].message == "Real issue"


# ---------------------------------------------------------------------------
# audit_deck_with_llm — page→slide index mapping
# ---------------------------------------------------------------------------

class TestAuditDeckWithLlm:
    """Tests for the page→slide mapping logic, not the LLM calls themselves."""

    def _make_pages(self, tmp_path: Path, n: int) -> list[Path]:
        """Create n dummy PNG files to simulate rendered PDF pages."""
        pages = []
        for i in range(n):
            p = tmp_path / f"page_{i+1:02d}.png"
            p.write_bytes(_white_png(50, 50))
            pages.append(p)
        return pages

    def test_no_pdf_returns_empty(self, tmp_path):
        slides = [{"slide_type": "content", "data": {"title": "S1"}}]
        result = audit_deck_with_llm(tmp_path / "none.pdf", slides)
        assert result == []

    def test_correct_mapping_no_overflow(self, tmp_path):
        """3 slides, 3 pages — each page audited against its slide."""
        slides = [
            {"slide_type": "title",   "data": {"title": "T1"}},
            {"slide_type": "content", "data": {"title": "T2"}},
            {"slide_type": "closing", "data": {}},
        ]
        pages = self._make_pages(tmp_path, 3)
        audited_pairs: list[tuple[int, str]] = []

        def mock_audit_slide(png, *, slide_index, slide_type, **kw):
            audited_pairs.append((slide_index, slide_type))
            return []

        with patch(
            "inkline.intelligence.overflow_audit._render_pdf_pages",
            return_value=pages,
        ), patch(
            "inkline.intelligence.overflow_audit.audit_slide_with_llm",
            side_effect=mock_audit_slide,
        ):
            pdf = tmp_path / "deck.pdf"
            pdf.write_bytes(b"fake")
            audit_deck_with_llm(pdf, slides)

        assert len(audited_pairs) == 3
        # Each slide audited with its correct 1-based index
        assert (1, "title")   in audited_pairs
        assert (2, "content") in audited_pairs
        assert (3, "closing") in audited_pairs

    def test_overflow_indices_skip_extra_pages(self, tmp_path):
        """Slide 1 overflows: 4 pages for 3 slides. With overflow_slide_indices=[0],
        page_2 is skipped; slides [0,1,2] map to pages [0,2,3]."""
        slides = [
            {"slide_type": "dashboard", "data": {"title": "overflow slide"}},
            {"slide_type": "content",   "data": {"title": "normal"}},
            {"slide_type": "closing",   "data": {}},
        ]
        pages = self._make_pages(tmp_path, 4)  # 4 pages for 3 slides
        audited_pairs: list[tuple[int, Path]] = []

        def mock_audit_slide(png, *, slide_index, slide_type, **kw):
            audited_pairs.append((slide_index, png))
            return []

        with patch(
            "inkline.intelligence.overflow_audit._render_pdf_pages",
            return_value=pages,
        ), patch(
            "inkline.intelligence.overflow_audit.audit_slide_with_llm",
            side_effect=mock_audit_slide,
        ):
            pdf = tmp_path / "deck.pdf"
            pdf.write_bytes(b"fake")
            audit_deck_with_llm(pdf, slides, overflow_slide_indices=[0])

        assert len(audited_pairs) == 3
        # Slide 1 (index=0) → page_01 (pages[0])
        assert any(idx == 1 and png == pages[0] for idx, png in audited_pairs)
        # Slide 2 (index=1) → page_03 (pages[2]) — page_02 was the overflow page
        assert any(idx == 2 and png == pages[2] for idx, png in audited_pairs)
        # Slide 3 (index=2) → page_04 (pages[3])
        assert any(idx == 3 and png == pages[3] for idx, png in audited_pairs)

    def test_no_overflow_indices_treats_all_pages_sequentially(self, tmp_path):
        """Without overflow_slide_indices, pages map 1:1 to slides (first N pages)."""
        slides = [
            {"slide_type": "content", "data": {"title": f"S{i}"}}
            for i in range(3)
        ]
        # 5 pages but only 3 slides — overflow pages at end
        pages = self._make_pages(tmp_path, 5)
        audited_pairs: list[tuple[int, Path]] = []

        def mock_audit_slide(png, *, slide_index, slide_type, **kw):
            audited_pairs.append((slide_index, png))
            return []

        with patch(
            "inkline.intelligence.overflow_audit._render_pdf_pages",
            return_value=pages,
        ), patch(
            "inkline.intelligence.overflow_audit.audit_slide_with_llm",
            side_effect=mock_audit_slide,
        ):
            pdf = tmp_path / "deck.pdf"
            pdf.write_bytes(b"fake")
            audit_deck_with_llm(pdf, slides)

        # Only 3 slides audited, using pages[0], pages[1], pages[2]
        assert len(audited_pairs) == 3
        assert all(png in pages[:3] for _, png in audited_pairs)

    def test_fewer_pages_than_slides_audits_available(self, tmp_path):
        """If PDF has fewer pages than slides (render error), audit what's available."""
        slides = [
            {"slide_type": "content", "data": {"title": f"S{i}"}}
            for i in range(5)
        ]
        pages = self._make_pages(tmp_path, 3)  # only 3 pages

        audited: list[int] = []

        def mock_audit_slide(png, *, slide_index, **kw):
            audited.append(slide_index)
            return []

        with patch(
            "inkline.intelligence.overflow_audit._render_pdf_pages",
            return_value=pages,
        ), patch(
            "inkline.intelligence.overflow_audit.audit_slide_with_llm",
            side_effect=mock_audit_slide,
        ):
            pdf = tmp_path / "deck.pdf"
            pdf.write_bytes(b"fake")
            audit_deck_with_llm(pdf, slides)

        assert len(audited) == 3  # only 3 audited, not 5

    def test_warnings_collected_in_slide_order(self, tmp_path):
        """Warnings from all slides are returned in slide-index order."""
        slides = [
            {"slide_type": "content", "data": {"title": "S1"}},
            {"slide_type": "content", "data": {"title": "S2"}},
        ]
        pages = self._make_pages(tmp_path, 2)

        def mock_audit(png, *, slide_index, slide_type, **kw):
            return [AuditWarning(
                slide_index=slide_index, slide_type=slide_type,
                severity="warn", message=f"issue on slide {slide_index}",
            )]

        with patch(
            "inkline.intelligence.overflow_audit._render_pdf_pages",
            return_value=pages,
        ), patch(
            "inkline.intelligence.overflow_audit.audit_slide_with_llm",
            side_effect=mock_audit,
        ):
            pdf = tmp_path / "deck.pdf"
            pdf.write_bytes(b"fake")
            result = audit_deck_with_llm(pdf, slides)

        assert len(result) == 2
        assert result[0].slide_index == 1
        assert result[1].slide_index == 2

    def test_failed_audit_slide_does_not_crash_deck_audit(self, tmp_path):
        """If one slide's audit raises, the rest still complete."""
        slides = [
            {"slide_type": "content", "data": {}},
            {"slide_type": "content", "data": {}},
            {"slide_type": "content", "data": {}},
        ]
        pages = self._make_pages(tmp_path, 3)

        call_count = [0]

        def mock_audit(png, *, slide_index, **kw):
            call_count[0] += 1
            if slide_index == 2:
                raise RuntimeError("simulated audit failure")
            return [AuditWarning(
                slide_index=slide_index, slide_type="content",
                severity="warn", message="ok",
            )]

        with patch(
            "inkline.intelligence.overflow_audit._render_pdf_pages",
            return_value=pages,
        ), patch(
            "inkline.intelligence.overflow_audit.audit_slide_with_llm",
            side_effect=mock_audit,
        ):
            pdf = tmp_path / "deck.pdf"
            pdf.write_bytes(b"fake")
            result = audit_deck_with_llm(pdf, slides)

        # Slide 2 failed → 0 warnings from it, but slides 1 and 3 succeeded
        assert call_count[0] == 3
        assert len(result) == 2  # warnings from slides 1 and 3
        assert all(w.slide_index != 2 for w in result)
