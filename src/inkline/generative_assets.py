"""
Helper module for Gemini AI image generation via n8n.

Handles:
- Calling n8n workflows for background/icon generation
- Text-only workflow (inkblot-icon): returns image_path (file on n8n host) or imageBase64
- Multimodal workflow (gemini-multimodal-icon): reference image attachment, returns imageBase64
- Saving to disk
- Path management for generated assets

Primary n8n workflows
---------------------
Text-only (inkblot-icon):
    Endpoint: <base>/webhook/inkblot-icon
    Request:  {"prompt": "..."}
    Response: {"image_path": "/tmp/...", ...}  OR  {"imageBase64": "...", ...}

Multimodal (gemini-multimodal-icon):
    Endpoint: <base>/webhook/gemini-multimodal-icon
    Request:  {"prompt": "...", "reference_image_b64": "<base64>", "mime_type": "image/png"}
    Response: {"imageBase64": "<base64>", "filename": "...", "image_path": "...", "mimeType": "..."}
    NOTE: image_path in the multimodal response is container-local (n8n sandbox blocks fs).
          ALWAYS decode imageBase64 — never rely on image_path for this workflow.

Model: gemini-2.5-flash-image (no -preview suffix)
"""

import base64
import json
import logging
import warnings
from pathlib import Path
from typing import Optional, Union

import requests

log = logging.getLogger(__name__)

# Type alias for path-like args
_PathLike = Union[str, Path]


def generate_background_image(
    n8n_endpoint: str,
    prompt: str,
    output_dir: Optional[Path] = None,
    timeout: int = 180,
    reference_image_path: Optional[_PathLike] = None,
) -> str:
    """
    Call n8n Gemini workflow to generate a background image.

    When ``reference_image_path`` is supplied, this function automatically
    routes to the multimodal endpoint by replacing the ``inkblot-icon`` suffix
    in ``n8n_endpoint`` with ``gemini-multimodal-icon``.  If ``n8n_endpoint``
    does not end in ``inkblot-icon`` (i.e. the caller passed a fully-custom URL)
    a warning is logged and the function proceeds text-only — no multimodal
    fallback is attempted in that case, because we cannot safely guess the
    correct multimodal URL.

    Args:
        n8n_endpoint: Webhook URL (e.g., http://localhost:5678/webhook/inkblot-icon)
        prompt: Natural language prompt for image generation
        output_dir: Where to save PNG (defaults to ~/.local/share/inkline/output/backgrounds/)
        timeout: Request timeout in seconds (Gemini can take 30-60s)
        reference_image_path: Optional path to a reference image for multimodal routing.
            When set, the function calls the gemini-multimodal-icon workflow instead
            of the text-only inkblot-icon workflow.  The reference image is
            base64-encoded and sent alongside the prompt.

    Returns:
        Path to the generated PNG file.  For text-only workflows that return
        ``image_path`` the value is returned directly (file already exists on
        the n8n host).  For all other cases (base64 response, multimodal) the
        image is decoded, saved to ``output_dir``, and the saved path returned.

    Raises:
        FileNotFoundError: If ``reference_image_path`` is provided but does not exist
        ValueError: If n8n response is malformed or image decode fails
        requests.RequestException: If n8n webhook is unreachable
    """
    # Multimodal routing
    if reference_image_path is not None:
        ref_path = Path(reference_image_path)
        if not ref_path.exists():
            raise FileNotFoundError(
                f"reference_image_path does not exist: {ref_path}"
            )
        if n8n_endpoint.endswith("inkblot-icon"):
            multimodal_endpoint = n8n_endpoint[:-len("inkblot-icon")] + "gemini-multimodal-icon"
            log.debug(
                "reference_image_path supplied — routing to multimodal endpoint: %s",
                multimodal_endpoint,
            )
            return generate_background_image_multimodal(
                n8n_endpoint=multimodal_endpoint,
                prompt=prompt,
                reference_image_path=ref_path,
                output_dir=output_dir,
                timeout=timeout,
            )
        else:
            warnings.warn(
                f"reference_image_path was supplied but n8n_endpoint "
                f"'{n8n_endpoint}' does not end in 'inkblot-icon' — cannot "
                f"auto-derive multimodal URL.  Proceeding text-only.",
                UserWarning,
                stacklevel=2,
            )
            log.warning(
                "Cannot auto-route to multimodal: endpoint '%s' does not end in "
                "'inkblot-icon'.  Falling back to text-only call.",
                n8n_endpoint,
            )

    if not output_dir:
        output_dir = Path("~/.local/share/inkline/output/backgrounds").expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Call n8n workflow
    log.debug("Calling n8n at %s with prompt: %s", n8n_endpoint, prompt[:100])
    resp = requests.post(
        n8n_endpoint,
        json={"prompt": prompt},
        timeout=timeout,
    )
    resp.raise_for_status()

    # Parse response
    data = resp.json()
    log.debug("n8n response: %s", json.dumps(data, indent=2)[:500])

    # Extract image data - support both workflow formats.
    # Primary format (inkblot-icon-generator-workflow.json):
    #   {"image_path": "/tmp/generated_bg_<uuid>.png"}
    # Fallback format (future workflows that return inline base64):
    #   {"imageBase64": "...", "filename": "...", "mimeType": "image/png"}

    # --- Primary: file path returned by the workflow ---
    file_path = data.get("image_path") or data.get("file_path")
    if file_path:
        log.info("n8n returned file path: %s", file_path)
        return file_path

    # --- Fallback: base64-encoded image ---
    image_base64 = data.get("imageBase64")
    if not image_base64:
        raise ValueError(
            f"n8n response missing image_path and imageBase64. Got: {list(data.keys())}"
        )

    filename = data.get("filename", "generated_bg.png")

    # Decode base64 to binary
    try:
        image_binary = base64.b64decode(image_base64)
    except Exception as e:
        raise ValueError(f"Failed to decode base64 image data: {e}")

    # Save to disk
    output_path = output_dir / filename
    with open(output_path, "wb") as f:
        f.write(image_binary)

    log.info("Saved background image: %s (%d bytes)", output_path, len(image_binary))

    # Return relative path for use in slides
    # E.g., "backgrounds/generated_bg_xyz.png" if output_dir is ~/.local/share/inkline/output/
    try:
        rel_path = output_path.relative_to(output_dir.parent)
        return str(rel_path)
    except ValueError:
        # Fallback to absolute path if relative path fails
        return str(output_path)


def generate_background_image_multimodal(
    n8n_endpoint: str,
    prompt: str,
    reference_image_path: _PathLike,
    output_dir: Optional[Path] = None,
    timeout: int = 180,
    mime_type: str = "image/png",
) -> str:
    """Call the multimodal n8n Gemini workflow with a reference image attachment.

    Sends the reference image as base64 alongside the text prompt to the
    ``gemini-multimodal-icon`` n8n workflow (model: gemini-2.5-flash-image).
    The workflow returns a generated image encoded as ``imageBase64`` in the
    response JSON.

    IMPORTANT: The ``image_path`` field in the response is container-local
    (n8n sandbox blocks ``fs``).  This function ALWAYS decodes ``imageBase64``
    and writes the result to disk — ``image_path`` is never used.

    Args:
        n8n_endpoint: Full webhook URL for the multimodal workflow,
            e.g. ``http://localhost:5678/webhook/gemini-multimodal-icon``.
        prompt: Natural language generation prompt.
        reference_image_path: Path to an existing image file to use as style
            anchor.  The file is read from disk and base64-encoded before the
            POST.  Raises ``FileNotFoundError`` if the path does not exist.
        output_dir: Directory to write the generated PNG.  Defaults to
            ``~/.local/share/inkline/output/backgrounds/``.
        timeout: HTTP request timeout in seconds (default 180).
        mime_type: MIME type of the reference image (default ``"image/png"``).

    Returns:
        Absolute path (str) to the saved PNG on disk.

    Raises:
        FileNotFoundError: If ``reference_image_path`` does not exist on disk.
        ValueError: If the n8n response is missing ``imageBase64``.
        requests.RequestException: If the n8n webhook is unreachable.
    """
    ref_path = Path(reference_image_path)
    if not ref_path.exists():
        raise FileNotFoundError(
            f"reference_image_path does not exist: {ref_path}"
        )

    if not output_dir:
        output_dir = Path("~/.local/share/inkline/output/backgrounds").expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Read and encode reference image
    ref_bytes = ref_path.read_bytes()
    ref_b64 = base64.b64encode(ref_bytes).decode("utf-8")
    log.debug(
        "Calling multimodal n8n at %s — prompt: %s, reference: %s (%d bytes)",
        n8n_endpoint,
        prompt[:100],
        ref_path.name,
        len(ref_bytes),
    )

    payload = {
        "prompt": prompt,
        "reference_image_b64": ref_b64,
        "mime_type": mime_type,
    }

    resp = requests.post(n8n_endpoint, json=payload, timeout=timeout)
    resp.raise_for_status()

    data = resp.json()
    log.debug("n8n multimodal response keys: %s", list(data.keys()))

    # ALWAYS decode imageBase64 — image_path is container-local and unreliable
    image_base64 = data.get("imageBase64")
    if not image_base64:
        raise ValueError(
            f"n8n multimodal response missing 'imageBase64'. "
            f"Got keys: {list(data.keys())}"
        )

    # Decode base64 to binary
    try:
        image_binary = base64.b64decode(image_base64)
    except Exception as e:
        raise ValueError(f"Failed to decode base64 image from multimodal response: {e}")

    filename = data.get("filename", f"multimodal_{ref_path.stem}.png")
    output_path = output_dir / filename
    with open(output_path, "wb") as f:
        f.write(image_binary)

    log.info(
        "Saved multimodal background image: %s (%d bytes)",
        output_path,
        len(image_binary),
    )

    return str(output_path.resolve())


def generate_icon(
    n8n_endpoint: str,
    prompt: str,
    output_dir: Optional[Path] = None,
    reference_image_path: Optional[_PathLike] = None,
) -> str:
    """
    Generate a brand icon via n8n Gemini.

    When ``reference_image_path`` is supplied, automatically routes to the
    multimodal endpoint (same auto-derivation logic as
    ``generate_background_image``).

    Args:
        n8n_endpoint: n8n webhook URL for icon generation
        prompt: Icon design prompt
        output_dir: Output directory (defaults to ~/.local/share/inkline/output/icons/)
        reference_image_path: Optional reference image for multimodal routing.
            When set and ``n8n_endpoint`` ends in ``inkblot-icon``, the function
            replaces that suffix with ``gemini-multimodal-icon`` and calls the
            multimodal workflow.  If the endpoint does not end in ``inkblot-icon``,
            a warning is logged and the function proceeds text-only.

    Returns:
        Path to saved PNG icon
    """
    if not output_dir:
        output_dir = Path("~/.local/share/inkline/output/icons").expanduser()

    return generate_background_image(
        n8n_endpoint, prompt, output_dir, reference_image_path=reference_image_path
    )


# Example usage for Inkline's visual_direction.py
# This integrates directly with _generate_backgrounds() in visual_direction.py
