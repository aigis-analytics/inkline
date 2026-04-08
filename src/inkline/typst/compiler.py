"""Typst compiler wrapper — .typ source to PDF bytes.

Uses the ``typst`` PyPI package (Rust-based, millisecond compilation).
Falls back to subprocess ``typst compile`` if the Python binding is unavailable.
"""

from __future__ import annotations

import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Detect typst availability
# ---------------------------------------------------------------------------

try:
    import typst as _typst_lib

    _HAS_TYPST_PY = True
except ImportError:
    _typst_lib = None
    _HAS_TYPST_PY = False


def compile_typst(
    source: str,
    *,
    output_path: Optional[str | Path] = None,
    root: Optional[str | Path] = None,
    font_paths: Optional[list[str | Path]] = None,
) -> bytes:
    """Compile a Typst source string to PDF bytes.

    Parameters
    ----------
    source : str
        Full Typst markup source.
    output_path : Path, optional
        If given, also write PDF to this file.
    root : Path, optional
        Root directory for relative ``#image()`` paths.
    font_paths : list[Path], optional
        Additional directories to search for fonts.

    Returns
    -------
    bytes
        PDF file contents.
    """
    if _HAS_TYPST_PY:
        return _compile_python(source, output_path=output_path, root=root, font_paths=font_paths)
    return _compile_subprocess(source, output_path=output_path, root=root, font_paths=font_paths)


def _compile_python(
    source: str,
    *,
    output_path: Optional[str | Path] = None,
    root: Optional[str | Path] = None,
    font_paths: Optional[list[str | Path]] = None,
) -> bytes:
    """Compile via the ``typst`` Python package.

    Note: typst.compile() takes a file path (not a source string),
    so we write the source to a temp file first. When root is provided,
    the source file must be inside that root directory.
    """
    # Re-import typst to avoid state corruption from prior compilations
    # (known issue in typst-py Rust binding with many sequential compiles)
    import importlib
    import typst as _fresh_typst
    importlib.reload(_fresh_typst)

    # If root is provided, write source file inside it so Typst can find images
    if root:
        root_path = Path(root)
        root_path.mkdir(parents=True, exist_ok=True)
        src_path = root_path / "_inkline_temp.typ"
        src_path.write_text(source, encoding="utf-8")
        cleanup_src = src_path
    else:
        cleanup_src = None

    try:
        if not root:
            tmp_ctx = tempfile.TemporaryDirectory()
            tmp_dir_path = Path(tmp_ctx.__enter__())
            src_path = tmp_dir_path / "input.typ"
            src_path.write_text(source, encoding="utf-8")
        else:
            tmp_ctx = None

        kwargs: dict = {}
        if root:
            kwargs["root"] = str(root)
        elif tmp_ctx:
            kwargs["root"] = str(tmp_dir_path)
        if font_paths:
            kwargs["font_paths"] = [str(p) for p in font_paths]

        pdf_bytes = _fresh_typst.compile(str(src_path), **kwargs)

        if tmp_ctx:
            tmp_ctx.__exit__(None, None, None)
    finally:
        if cleanup_src and cleanup_src.exists():
            cleanup_src.unlink(missing_ok=True)

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(pdf_bytes)
        log.info("Typst PDF written to %s (%d bytes)", output_path, len(pdf_bytes))

    return pdf_bytes


def _compile_subprocess(
    source: str,
    *,
    output_path: Optional[str | Path] = None,
    root: Optional[str | Path] = None,
    font_paths: Optional[list[str | Path]] = None,
) -> bytes:
    """Compile via ``typst compile`` CLI as fallback."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        src_path = tmp / "input.typ"
        pdf_path = tmp / "output.pdf"

        src_path.write_text(source, encoding="utf-8")

        cmd = ["typst", "compile", str(src_path), str(pdf_path)]
        if root:
            cmd.extend(["--root", str(root)])
        if font_paths:
            for fp in font_paths:
                cmd.extend(["--font-path", str(fp)])

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            raise RuntimeError(f"typst compile failed:\n{result.stderr}")

        pdf_bytes = pdf_path.read_bytes()

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(pdf_bytes)
        log.info("Typst PDF written to %s (%d bytes)", output_path, len(pdf_bytes))

    return pdf_bytes
