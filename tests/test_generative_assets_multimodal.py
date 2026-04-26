"""Tests for multimodal Gemini image generation via n8n.

Covers:
- generate_background_image_multimodal: base64 encode, POST shape, decode, disk write, return path
- Auto-routing in generate_background_image when reference_image_path is set vs unset
- Warning + fallback when caller's endpoint doesn't end in 'inkblot-icon'
- Error paths: missing reference file, response missing imageBase64
"""
from __future__ import annotations

import base64
import json
import warnings
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def dummy_png(tmp_path: Path) -> Path:
    """Write a minimal 1-byte PNG-ish file for reference image tests."""
    p = tmp_path / "ref.png"
    p.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 8)  # 16-byte stub
    return p


@pytest.fixture()
def output_dir(tmp_path: Path) -> Path:
    d = tmp_path / "backgrounds"
    d.mkdir()
    return d


def _fake_b64_png() -> str:
    """Return valid base64 for a tiny PNG-like binary blob."""
    return base64.b64encode(b"FAKEPNGBYTES").decode("utf-8")


def _mock_response(image_b64: str, filename: str = "result.png") -> MagicMock:
    """Build a mock requests.Response with imageBase64 in the JSON body."""
    mock = MagicMock()
    mock.raise_for_status.return_value = None
    mock.json.return_value = {
        "imageBase64": image_b64,
        "filename": filename,
        "image_path": "/n8n-sandbox/tmp/result.png",  # container-local — must be ignored
        "mimeType": "image/png",
    }
    return mock


# ---------------------------------------------------------------------------
# generate_background_image_multimodal
# ---------------------------------------------------------------------------

class TestGenerateBackgroundImageMultimodal:
    def test_base64_encodes_reference_and_posts_correct_shape(self, dummy_png, output_dir):
        """Reference image must be base64-encoded and sent as reference_image_b64."""
        from inkline.generative_assets import generate_background_image_multimodal

        image_b64 = _fake_b64_png()
        mock_resp = _mock_response(image_b64)

        with patch("requests.post", return_value=mock_resp) as mock_post:
            generate_background_image_multimodal(
                n8n_endpoint="http://localhost:5678/webhook/gemini-multimodal-icon",
                prompt="blue geometric background",
                reference_image_path=dummy_png,
                output_dir=output_dir,
            )

        mock_post.assert_called_once()
        _, kwargs = mock_post.call_args
        payload = kwargs.get("json") or mock_post.call_args[0][1] if len(mock_post.call_args[0]) > 1 else kwargs["json"]
        # Reconstruct from the actual call
        call_kwargs = mock_post.call_args.kwargs if hasattr(mock_post.call_args, "kwargs") else {}
        if not call_kwargs:
            call_kwargs = mock_post.call_args[1]
        sent_payload = call_kwargs.get("json", {})

        assert "prompt" in sent_payload
        assert sent_payload["prompt"] == "blue geometric background"
        assert "reference_image_b64" in sent_payload
        assert "mime_type" in sent_payload
        assert sent_payload["mime_type"] == "image/png"

        # Verify the encoded bytes match the original file contents
        decoded = base64.b64decode(sent_payload["reference_image_b64"])
        assert decoded == dummy_png.read_bytes()

    def test_decodes_imageBase64_and_writes_to_disk(self, dummy_png, output_dir):
        """imageBase64 must be decoded and saved; image_path from response must be ignored."""
        from inkline.generative_assets import generate_background_image_multimodal

        image_b64 = _fake_b64_png()
        mock_resp = _mock_response(image_b64, filename="generated.png")

        with patch("requests.post", return_value=mock_resp):
            result_path = generate_background_image_multimodal(
                n8n_endpoint="http://localhost:5678/webhook/gemini-multimodal-icon",
                prompt="test",
                reference_image_path=dummy_png,
                output_dir=output_dir,
            )

        # File must exist on disk
        saved = Path(result_path)
        assert saved.exists(), f"Saved file not found at {result_path}"
        assert saved.read_bytes() == base64.b64decode(image_b64)

        # Must NOT have used the container-local image_path
        assert "/n8n-sandbox" not in result_path

    def test_returns_absolute_path(self, dummy_png, output_dir):
        from inkline.generative_assets import generate_background_image_multimodal

        with patch("requests.post", return_value=_mock_response(_fake_b64_png())):
            result_path = generate_background_image_multimodal(
                n8n_endpoint="http://localhost:5678/webhook/gemini-multimodal-icon",
                prompt="test",
                reference_image_path=dummy_png,
                output_dir=output_dir,
            )

        assert Path(result_path).is_absolute(), f"Expected absolute path, got: {result_path}"

    def test_missing_reference_file_raises_file_not_found(self, output_dir, tmp_path):
        from inkline.generative_assets import generate_background_image_multimodal

        with pytest.raises(FileNotFoundError, match="reference_image_path does not exist"):
            generate_background_image_multimodal(
                n8n_endpoint="http://localhost:5678/webhook/gemini-multimodal-icon",
                prompt="test",
                reference_image_path=tmp_path / "does_not_exist.png",
                output_dir=output_dir,
            )

    def test_missing_imageBase64_raises_value_error(self, dummy_png, output_dir):
        """When the n8n response doesn't include imageBase64, raise ValueError."""
        from inkline.generative_assets import generate_background_image_multimodal

        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {"image_path": "/sandbox/tmp/foo.png"}  # no imageBase64

        with patch("requests.post", return_value=mock_resp):
            with pytest.raises(ValueError, match="imageBase64"):
                generate_background_image_multimodal(
                    n8n_endpoint="http://localhost:5678/webhook/gemini-multimodal-icon",
                    prompt="test",
                    reference_image_path=dummy_png,
                    output_dir=output_dir,
                )

    def test_default_output_dir_is_backgrounds(self, dummy_png):
        """When output_dir is None, defaults to ~/.local/share/inkline/output/backgrounds/."""
        from inkline.generative_assets import generate_background_image_multimodal

        image_b64 = _fake_b64_png()
        mock_resp = _mock_response(image_b64, filename="auto_dir_test.png")

        with patch("requests.post", return_value=mock_resp):
            result_path = generate_background_image_multimodal(
                n8n_endpoint="http://localhost:5678/webhook/gemini-multimodal-icon",
                prompt="test",
                reference_image_path=dummy_png,
                output_dir=None,
            )

        assert "backgrounds" in result_path
        # Clean up
        p = Path(result_path)
        if p.exists():
            p.unlink()


# ---------------------------------------------------------------------------
# Auto-routing in generate_background_image
# ---------------------------------------------------------------------------

class TestAutoRouting:
    def test_routes_to_multimodal_when_reference_set_and_endpoint_ends_inkblot_icon(
        self, dummy_png, output_dir
    ):
        """When reference_image_path is set and endpoint ends in inkblot-icon, call multimodal."""
        from inkline import generative_assets

        image_b64 = _fake_b64_png()
        mock_resp = _mock_response(image_b64, filename="multimodal_out.png")

        with patch("requests.post", return_value=mock_resp) as mock_post:
            generative_assets.generate_background_image(
                n8n_endpoint="http://localhost:5678/webhook/inkblot-icon",
                prompt="styled background",
                output_dir=output_dir,
                reference_image_path=dummy_png,
            )

        # The actual POST must go to the multimodal endpoint
        mock_post.assert_called_once()
        actual_url = mock_post.call_args[0][0]
        assert actual_url.endswith("gemini-multimodal-icon"), (
            f"Expected multimodal endpoint but got: {actual_url}"
        )
        # Payload must include reference_image_b64
        sent_json = mock_post.call_args.kwargs.get("json") or mock_post.call_args[1].get("json", {})
        assert "reference_image_b64" in sent_json

    def test_text_only_when_no_reference_image(self, output_dir):
        """When reference_image_path is None, use the text-only path."""
        from inkline import generative_assets

        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {"image_path": "/tmp/text_only.png"}

        with patch("requests.post", return_value=mock_resp) as mock_post:
            result = generative_assets.generate_background_image(
                n8n_endpoint="http://localhost:5678/webhook/inkblot-icon",
                prompt="no reference",
                output_dir=output_dir,
            )

        # Must have called the text-only endpoint
        mock_post.assert_called_once()
        actual_url = mock_post.call_args[0][0]
        assert actual_url.endswith("inkblot-icon"), (
            f"Expected text-only endpoint but got: {actual_url}"
        )
        assert result == "/tmp/text_only.png"

    def test_warning_and_text_only_when_endpoint_custom(self, dummy_png, output_dir):
        """When endpoint doesn't end in inkblot-icon and reference_image_path is set,
        emit UserWarning and proceed text-only (no multimodal call)."""
        from inkline import generative_assets

        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {"image_path": "/tmp/custom_result.png"}

        with patch("requests.post", return_value=mock_resp) as mock_post:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                result = generative_assets.generate_background_image(
                    n8n_endpoint="http://localhost:5678/webhook/my-custom-endpoint",
                    prompt="custom endpoint test",
                    output_dir=output_dir,
                    reference_image_path=dummy_png,
                )

        # Must have emitted a UserWarning
        user_warnings = [w for w in caught if issubclass(w.category, UserWarning)]
        assert len(user_warnings) >= 1
        assert "inkblot-icon" in str(user_warnings[0].message).lower()

        # Must still have called the original (custom) endpoint text-only
        mock_post.assert_called_once()
        actual_url = mock_post.call_args[0][0]
        assert "my-custom-endpoint" in actual_url

        # No reference_image_b64 should have been sent (text-only payload)
        sent_json = mock_post.call_args.kwargs.get("json") or mock_post.call_args[1].get("json", {})
        assert "reference_image_b64" not in sent_json


# ---------------------------------------------------------------------------
# generate_icon multimodal routing
# ---------------------------------------------------------------------------

class TestGenerateIconAutoRouting:
    def test_routes_to_multimodal_when_reference_set(self, dummy_png, output_dir):
        from inkline import generative_assets

        image_b64 = _fake_b64_png()
        mock_resp = _mock_response(image_b64, filename="icon_out.png")

        with patch("requests.post", return_value=mock_resp) as mock_post:
            generative_assets.generate_icon(
                n8n_endpoint="http://localhost:5678/webhook/inkblot-icon",
                prompt="brand icon",
                output_dir=output_dir,
                reference_image_path=dummy_png,
            )

        actual_url = mock_post.call_args[0][0]
        assert actual_url.endswith("gemini-multimodal-icon")

    def test_text_only_when_no_reference_image(self, output_dir):
        from inkline import generative_assets

        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {"image_path": "/tmp/icon.png"}

        with patch("requests.post", return_value=mock_resp) as mock_post:
            generative_assets.generate_icon(
                n8n_endpoint="http://localhost:5678/webhook/inkblot-icon",
                prompt="brand icon",
                output_dir=output_dir,
            )

        actual_url = mock_post.call_args[0][0]
        assert actual_url.endswith("inkblot-icon")
