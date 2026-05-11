"""Safe path validation for bridge multimodal files."""

from __future__ import annotations

import os
import struct
from dataclasses import dataclass
from pathlib import Path


MAX_IMAGE_BYTES = 10 * 1024 * 1024
MAX_IMAGE_DIMENSION = 4000
ALLOWED_MIME_TYPES = {"image/png", "image/jpeg"}


class SafePathError(ValueError):
    """Raised when a user-supplied path is unsafe for backend invocation."""


@dataclass(frozen=True)
class SafeImage:
    path: Path
    mime_type: str
    width: int
    height: int
    size_bytes: int


def default_output_dir() -> Path:
    return Path(os.environ.get(
        "INKLINE_OUTPUT_DIR",
        "~/.local/share/inkline/output",
    )).expanduser().resolve()


def default_assets_dir() -> Path:
    return Path(os.environ.get(
        "INKLINE_ASSETS_DIR",
        "~/.config/inkline/assets",
    )).expanduser().resolve()


def allowed_image_roots() -> tuple[Path, ...]:
    roots = [default_output_dir(), default_assets_dir()]
    extra = os.environ.get("INKLINE_SAFE_IMAGE_ROOTS", "")
    for item in extra.split(os.pathsep):
        if item.strip():
            roots.append(Path(item).expanduser().resolve())
    return tuple(dict.fromkeys(roots))


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _png_dimensions(data: bytes) -> tuple[int, int]:
    if len(data) < 24 or not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise SafePathError("not a PNG image")
    if data[12:16] != b"IHDR":
        raise SafePathError("PNG missing IHDR")
    width, height = struct.unpack(">II", data[16:24])
    return int(width), int(height)


def _jpeg_dimensions(data: bytes) -> tuple[int, int]:
    if len(data) < 4 or not data.startswith(b"\xff\xd8"):
        raise SafePathError("not a JPEG image")
    offset = 2
    while offset + 9 < len(data):
        if data[offset] != 0xFF:
            offset += 1
            continue
        marker = data[offset + 1]
        offset += 2
        if marker in {0xD8, 0xD9}:
            continue
        if offset + 2 > len(data):
            break
        segment_len = struct.unpack(">H", data[offset:offset + 2])[0]
        if segment_len < 2:
            break
        if marker in {
            0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
            0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF,
        }:
            if offset + 7 > len(data):
                break
            height, width = struct.unpack(">HH", data[offset + 3:offset + 7])
            return int(width), int(height)
        offset += segment_len
    raise SafePathError("JPEG dimensions not found")


def sniff_image(data: bytes) -> tuple[str, int, int]:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        width, height = _png_dimensions(data)
        return "image/png", width, height
    if data.startswith(b"\xff\xd8"):
        width, height = _jpeg_dimensions(data)
        return "image/jpeg", width, height
    raise SafePathError("unsupported image MIME type")


def validate_image_path(path: str | os.PathLike[str], *, roots: tuple[Path, ...] | None = None) -> SafeImage:
    """Validate an existing image path before handing it to an LLM CLI.

    The check resolves symlinks, enforces the configured Inkline roots, sniffs
    magic bytes instead of trusting extensions, checks size, and verifies pixel
    dimensions.
    """
    candidate = Path(path).expanduser()
    resolved = candidate.resolve(strict=True)
    safe_roots = roots or allowed_image_roots()
    if not any(_is_relative_to(resolved, root) for root in safe_roots):
        raise SafePathError(f"path escapes allowed roots: {resolved}")
    size = resolved.stat().st_size
    if size > MAX_IMAGE_BYTES:
        raise SafePathError(f"image exceeds {MAX_IMAGE_BYTES} byte limit")
    data = resolved.read_bytes()
    mime_type, width, height = sniff_image(data)
    if mime_type not in ALLOWED_MIME_TYPES:
        raise SafePathError(f"unsupported image MIME type: {mime_type}")
    if width < 1 or height < 1:
        raise SafePathError("image dimensions must be positive")
    if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
        raise SafePathError(
            f"image dimensions exceed {MAX_IMAGE_DIMENSION}px limit: {width}x{height}"
        )
    return SafeImage(
        path=resolved,
        mime_type=mime_type,
        width=width,
        height=height,
        size_bytes=size,
    )
