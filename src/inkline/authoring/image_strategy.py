"""Inkline image strategy — parse, validate, fetch/generate, and cache images.

An ``_image:`` directive carries a ``strategy`` field with one of three values:

  reuse      Path on disk. Validated at parse time — FileNotFoundError raised
             if missing. Resized to slot dimensions with an explicit fit policy.
  generate   Calls the multimodal Gemini endpoint. Requires ``prompt``; optional
             ``reference_image_path``, ``region_width_px``, ``region_height_px``.
             Result is cached by content hash so re-renders are free.
  placeholder  Deterministic neutral box with a visible label. Never mistaken
             for finished content.

Failure is loud: if ``reuse`` points at a missing file, parse raises immediately.
If ``generate`` fails (network down, Gemini error), an ImageStrategyError is raised
with the actual error message — no silent fallback.

Usage::

    from inkline.authoring.image_strategy import resolve_image_directive

    result = resolve_image_directive(
        {"strategy": "reuse", "path": "assets/diagram.png"},
        base_dir="/path/to/spec/dir",
    )
    # Returns ImageResult(strategy="reuse", path=PosixPath(...), ...)
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

# Cache directory for generated images
_CACHE_DIR = Path("~/.local/share/inkline/image_cache").expanduser()


class ImageStrategyError(ValueError):
    """Raised when image strategy validation or generation fails."""


@dataclass
class ImageResult:
    """Resolved image ready for the renderer to embed."""
    strategy: str              # reuse | generate | placeholder
    path: Path | None          # resolved absolute path (None for placeholder)
    description: str = ""      # for placeholder: visible label text
    fit: str = "cover"         # cover | contain | stretch
    slot: str = "right"        # right | left | top | bottom | full
    width_pct: float = 50.0    # slot width as percentage (for split etc.)
    region_width_px: int = 1920
    region_height_px: int = 1080
    cached: bool = False       # True if served from cache (generate strategy)
    raw: dict = field(default_factory=dict)  # original directive dict


def resolve_image_directive(
    directive: dict,
    base_dir: str | Path | None = None,
    *,
    dry_run: bool = False,
) -> ImageResult:
    """Parse and validate an ``_image:`` directive.

    Parameters
    ----------
    directive : dict
        The parsed dict from the ``_image:`` directive.
    base_dir : str | Path | None
        Directory relative to which asset paths are resolved.
        If None, paths are resolved relative to cwd.
    dry_run : bool
        If True, skip Gemini API calls (return a placeholder instead).
        Useful in tests and CI.

    Returns
    -------
    ImageResult
        Resolved image description.

    Raises
    ------
    ImageStrategyError
        If the directive is missing required fields or validation fails.
    FileNotFoundError
        If strategy == 'reuse' and the path does not exist.
    """
    if not isinstance(directive, dict):
        raise ImageStrategyError(
            f"_image: directive must be a dict, got {type(directive).__name__}"
        )

    strategy = directive.get("strategy", "placeholder")
    if strategy not in ("reuse", "generate", "placeholder"):
        raise ImageStrategyError(
            f"_image: strategy must be 'reuse', 'generate', or 'placeholder', got {strategy!r}"
        )

    base = Path(base_dir) if base_dir else Path.cwd()

    if strategy == "reuse":
        return _resolve_reuse(directive, base)
    elif strategy == "generate":
        return _resolve_generate(directive, base, dry_run=dry_run)
    else:
        return _resolve_placeholder(directive)


def _resolve_reuse(directive: dict, base: Path) -> ImageResult:
    """Validate a 'reuse' directive — path must exist at parse time."""
    path_str = directive.get("path")
    if not path_str:
        raise ImageStrategyError("_image: strategy='reuse' requires 'path'")

    candidate = Path(path_str)
    if not candidate.is_absolute():
        candidate = base / candidate

    if not candidate.exists():
        raise FileNotFoundError(
            f"_image: reuse path not found: {candidate}\n"
            f"  (resolved from: {path_str!r}, base: {base})"
        )

    return ImageResult(
        strategy="reuse",
        path=candidate.resolve(),
        fit=directive.get("fit", "cover"),
        slot=directive.get("slot", "right"),
        width_pct=float(directive.get("width", "50%").rstrip("%") if isinstance(directive.get("width"), str) else directive.get("width", 50)),
        region_width_px=int(directive.get("region_width_px", 1920)),
        region_height_px=int(directive.get("region_height_px", 1080)),
        raw=directive,
    )


def _resolve_generate(directive: dict, base: Path, *, dry_run: bool = False) -> ImageResult:
    """Call multimodal Gemini to generate an image, with content-hash caching."""
    prompt = directive.get("prompt")
    if not prompt:
        raise ImageStrategyError("_image: strategy='generate' requires 'prompt'")

    reference_path_str = directive.get("reference_image_path")
    reference_path: Path | None = None
    if reference_path_str:
        candidate = Path(reference_path_str)
        if not candidate.is_absolute():
            candidate = base / candidate
        if not candidate.exists():
            raise FileNotFoundError(
                f"_image: generate reference_image_path not found: {candidate}"
            )
        reference_path = candidate.resolve()

    region_w = int(directive.get("region_width_px", 1920))
    region_h = int(directive.get("region_height_px", 1080))

    # Build cache key from all inputs
    cache_inputs = {
        "prompt": prompt,
        "reference_image_path": str(reference_path) if reference_path else None,
        "region_width_px": region_w,
        "region_height_px": region_h,
    }
    cache_key = hashlib.sha256(
        json.dumps(cache_inputs, sort_keys=True).encode()
    ).hexdigest()[:16]

    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = _CACHE_DIR / f"{cache_key}.png"

    if cache_file.exists():
        log.debug("image_strategy: cache hit for key %s", cache_key)
        return ImageResult(
            strategy="generate",
            path=cache_file,
            fit=directive.get("fit", "cover"),
            slot=directive.get("slot", "right"),
            width_pct=float(str(directive.get("width", "50%")).rstrip("%") if isinstance(directive.get("width"), str) else directive.get("width", 50)),
            region_width_px=region_w,
            region_height_px=region_h,
            cached=True,
            raw=directive,
        )

    if dry_run:
        log.debug("image_strategy: dry_run=True, returning placeholder for generate")
        return _resolve_placeholder(directive, description=f"[Generated: {prompt[:60]}]")

    # Call Gemini
    try:
        from inkline.generative_assets import generate_background_image_multimodal
        reference_b64: str | None = None
        if reference_path:
            import base64
            reference_b64 = base64.b64encode(reference_path.read_bytes()).decode()

        result_path = generate_background_image_multimodal(
            prompt=f"{prompt} (size: {region_w}x{region_h}px)",
            reference_image_b64=reference_b64,
            output_path=str(cache_file),
        )
        return ImageResult(
            strategy="generate",
            path=Path(result_path),
            fit=directive.get("fit", "cover"),
            slot=directive.get("slot", "right"),
            width_pct=float(str(directive.get("width", "50%")).rstrip("%") if isinstance(directive.get("width"), str) else directive.get("width", 50)),
            region_width_px=region_w,
            region_height_px=region_h,
            cached=False,
            raw=directive,
        )
    except Exception as exc:
        raise ImageStrategyError(
            f"_image: generate failed: {exc}\n"
            f"  prompt: {prompt!r}\n"
            f"  If n8n/Gemini is unavailable, use strategy: placeholder instead."
        ) from exc


def _resolve_placeholder(directive: dict, description: str | None = None) -> ImageResult:
    """Return a placeholder image description — no file, just metadata."""
    desc = description or directive.get("description", directive.get("prompt", "Image placeholder"))
    return ImageResult(
        strategy="placeholder",
        path=None,
        description=desc,
        fit="cover",
        slot=directive.get("slot", "right"),
        width_pct=float(str(directive.get("width", "50%")).rstrip("%") if isinstance(directive.get("width"), str) else directive.get("width", 50)),
        raw=directive,
    )


def validate_image_directives_in_sections(
    sections: list[dict],
    base_dir: str | Path | None = None,
    *,
    dry_run: bool = False,
) -> list[dict]:
    """Validate _image: directives in all sections at parse time.

    Returns a list of warning dicts for non-fatal issues.
    Raises ImageStrategyError or FileNotFoundError for fatal issues.
    """
    warnings: list[dict] = []
    base = Path(base_dir) if base_dir else Path.cwd()

    for i, section in enumerate(sections):
        directives = section.get("directives", {})
        image_directive = directives.get("image") or directives.get("_image")
        if not image_directive:
            continue
        try:
            resolve_image_directive(image_directive, base_dir=base, dry_run=dry_run)
        except FileNotFoundError as exc:
            # FileNotFoundError is a hard stop — re-raise immediately
            raise
        except ImageStrategyError as exc:
            warnings.append({
                "slide_index": i,
                "title": section.get("title", f"slide {i}"),
                "issue": str(exc),
                "severity": "error",
            })

    return warnings
