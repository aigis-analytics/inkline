"""
Helper module for Gemini AI image generation via n8n.

Handles:
- Calling n8n workflows for background/icon generation
- Reading image_path responses (primary format from inkblot-icon-generator-workflow.json)
- Decoding base64 image responses (fallback for future workflows)
- Saving to disk
- Path management for generated assets

Primary n8n response format (inkblot-icon-generator-workflow.json):
    {"image_path": "/tmp/generated_bg_<uuid>.png"}

Fallback n8n response format (future workflows):
    {"imageBase64": "<base64-encoded-png>", "filename": "...", "mimeType": "image/png"}
"""

import base64
import json
import logging
from pathlib import Path
from typing import Optional

import requests

log = logging.getLogger(__name__)


def generate_background_image(
    n8n_endpoint: str,
    prompt: str,
    output_dir: Optional[Path] = None,
    timeout: int = 180,
) -> str:
    """
    Call n8n Gemini workflow to generate a background image.

    Args:
        n8n_endpoint: Webhook URL (e.g., http://localhost:5678/webhook/inkblot-icon)
        prompt: Natural language prompt for image generation
        output_dir: Where to save PNG (defaults to ~/.local/share/inkline/output/backgrounds/)
        timeout: Request timeout in seconds (Gemini can take 30-60s)

    Returns:
        Path to the generated PNG file.  When the workflow returns ``image_path``
        the value is returned directly (file already exists on the n8n host).
        When the workflow returns ``imageBase64`` the image is decoded, saved to
        ``output_dir``, and the saved path is returned.

    Raises:
        ValueError: If n8n response is malformed or image decode fails
        requests.RequestException: If n8n webhook is unreachable
    """

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


def generate_icon(
    n8n_endpoint: str,
    prompt: str,
    output_dir: Optional[Path] = None,
) -> str:
    """
    Generate a brand icon via n8n Gemini.

    Args:
        n8n_endpoint: n8n webhook URL for icon generation
        prompt: Icon design prompt
        output_dir: Output directory (defaults to ~/.local/share/inkline/output/icons/)

    Returns:
        Path to saved PNG icon
    """
    if not output_dir:
        output_dir = Path("~/.local/share/inkline/output/icons").expanduser()

    return generate_background_image(n8n_endpoint, prompt, output_dir)


# Example usage for Inkline's visual_direction.py
# This integrates directly with _generate_backgrounds() in visual_direction.py
