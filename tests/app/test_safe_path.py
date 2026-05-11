from __future__ import annotations

import struct

import pytest

from inkline.app.safe_path import SafePathError, sniff_image, validate_image_path


PNG_1X1 = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00"
    b"\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
)


def test_validate_image_path_accepts_png_inside_allowed_root(tmp_path):
    image = tmp_path / "ok.png"
    image.write_bytes(PNG_1X1)

    safe = validate_image_path(image, roots=(tmp_path.resolve(),))

    assert safe.mime_type == "image/png"
    assert safe.width == 1
    assert safe.height == 1


def test_validate_image_path_rejects_path_escape(tmp_path):
    outside = tmp_path.parent / "outside.png"
    outside.write_bytes(PNG_1X1)

    with pytest.raises(SafePathError, match="escapes"):
        validate_image_path(outside, roots=(tmp_path.resolve(),))


def test_validate_image_path_rejects_symlink_escape(tmp_path):
    outside = tmp_path.parent / "outside-link-target.png"
    outside.write_bytes(PNG_1X1)
    link = tmp_path / "link.png"
    link.symlink_to(outside)

    with pytest.raises(SafePathError, match="escapes"):
        validate_image_path(link, roots=(tmp_path.resolve(),))


def test_validate_image_path_rejects_bad_magic(tmp_path):
    bad = tmp_path / "bad.png"
    bad.write_bytes(b"not really an image")

    with pytest.raises(SafePathError, match="unsupported"):
        validate_image_path(bad, roots=(tmp_path.resolve(),))


def test_sniff_image_rejects_oversized_png_dimensions():
    data = bytearray(PNG_1X1)
    data[16:24] = struct.pack(">II", 4001, 1)

    mime, width, height = sniff_image(bytes(data))

    assert mime == "image/png"
    assert width == 4001
    assert height == 1


def test_validate_image_path_rejects_oversized_dimensions(tmp_path):
    data = bytearray(PNG_1X1)
    data[16:24] = struct.pack(">II", 4001, 1)
    image = tmp_path / "too-wide.png"
    image.write_bytes(bytes(data))

    with pytest.raises(SafePathError, match="dimensions exceed"):
        validate_image_path(image, roots=(tmp_path.resolve(),))
