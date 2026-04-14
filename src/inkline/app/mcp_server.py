"""Inkline MCP Server — exposes Inkline as tools for Claude.ai and Claude Desktop.

Usage
-----
Start the server (stdio transport — required for Claude Desktop MCP config):

    inkline mcp

Or directly:

    python -m inkline.app.mcp_server

Claude Desktop config (add to ~/Library/Application Support/Claude/claude_desktop_config.json):

    {
      "mcpServers": {
        "inkline": {
          "command": "inkline",
          "args": ["mcp"]
        }
      }
    }

Tools exposed
-------------
- inkline_generate_deck    — content text + intent → PDF
- inkline_render_slides    — JSON slide specs → PDF
- inkline_list_templates   — list available templates
- inkline_list_themes      — list themes, optionally filtered by category
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

try:
    from fastmcp import FastMCP
except ImportError:
    raise ImportError(
        "fastmcp is required for the Inkline MCP server. "
        "Install it with: pip install \"inkline[mcp]\""
    )

log = logging.getLogger(__name__)

OUTPUT_DIR = Path("~/.local/share/inkline/output").expanduser()
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

mcp = FastMCP(
    "Inkline",
    instructions=(
        "Inkline generates branded, publication-quality PDF slide decks and documents. "
        "Use inkline_generate_deck to turn content into a deck, "
        "inkline_render_slides to render a specific slide spec, "
        "inkline_list_templates to see available templates, and "
        "inkline_list_themes to browse themes."
    ),
)


@mcp.tool()
def inkline_generate_deck(
    content: str,
    intent: str,
    template: str = "consulting",
    brand: str = "minimal",
    audience: str = "",
    goal: str = "",
    title: str = "",
    date: str = "",
    output_filename: str = "deck.pdf",
) -> dict[str, Any]:
    """Generate a slide deck from content text.

    Args:
        content: The source content — markdown text, pasted document, or bullet points.
        intent: What kind of deck to make, e.g. "10-slide investor pitch" or "board update".
        template: Slide template name. Default "consulting". See inkline_list_templates().
        brand: Brand name. Default "minimal". Run list_brands() if you have custom brands.
        audience: Who the deck is for, e.g. "investors", "board", "customers".
        goal: The desired outcome, e.g. "secure term sheet", "get approval".
        title: Deck title. Extracted from content if not provided.
        date: Date string for the deck, e.g. "April 2026".
        output_filename: Output filename within the output directory.
    """
    try:
        from inkline.intelligence import DesignAdvisor
        from inkline.typst import export_typst_slides

        output_path = OUTPUT_DIR / output_filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Build sections from the content text
        sections = _text_to_sections(content, intent)

        # Determine mode — use llm if API key available, else rules
        mode = "llm" if os.environ.get("ANTHROPIC_API_KEY") else "rules"

        advisor = DesignAdvisor(brand=brand, template=template, mode=mode)
        slides = advisor.design_deck(
            title=title or _extract_title(content),
            sections=sections,
            audience=audience or "",
            goal=goal or intent,
            date=date,
        )

        export_typst_slides(
            slides=slides,
            output_path=str(output_path),
            brand=brand,
            template=template,
            title=title or _extract_title(content),
            date=date,
        )

        slide_summary = [
            {"index": i + 1, "type": s["slide_type"],
             "title": s["data"].get("title", s["data"].get("company", ""))}
            for i, s in enumerate(slides)
        ]

        return {
            "success": True,
            "pdf_path": str(output_path),
            "slide_count": len(slides),
            "slides": slide_summary,
            "template": template,
            "brand": brand,
            "mode": mode,
        }

    except Exception as exc:
        log.exception("inkline_generate_deck failed")
        return {"success": False, "error": str(exc)}


@mcp.tool()
def inkline_render_slides(
    slides_json: str,
    template: str = "consulting",
    brand: str = "minimal",
    title: str = "",
    date: str = "",
    output_filename: str = "deck.pdf",
) -> dict[str, Any]:
    """Render a JSON slide spec list to a PDF.

    Use this when you already have the slide specs (e.g. after amending a deck).
    The slides_json must be a JSON array of slide spec dicts following the
    Inkline slide spec format: [{slide_type, data}, ...].

    Args:
        slides_json: JSON string — array of slide spec dicts.
        template: Template name. Default "consulting".
        brand: Brand name. Default "minimal".
        title: Deck title for the PDF metadata.
        date: Date string.
        output_filename: Output filename within the output directory.
    """
    try:
        from inkline.typst import export_typst_slides

        slides = json.loads(slides_json)
        if not isinstance(slides, list):
            return {"success": False, "error": "slides_json must be a JSON array"}

        output_path = OUTPUT_DIR / output_filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        export_typst_slides(
            slides=slides,
            output_path=str(output_path),
            brand=brand,
            template=template,
            title=title,
            date=date,
        )

        return {
            "success": True,
            "pdf_path": str(output_path),
            "slide_count": len(slides),
        }

    except Exception as exc:
        log.exception("inkline_render_slides failed")
        return {"success": False, "error": str(exc)}


@mcp.tool()
def inkline_list_templates() -> list[str]:
    """List all available Inkline slide templates."""
    try:
        from inkline.typst.theme_registry import list_templates
        return list_templates()
    except Exception:
        # Return the known static list as fallback
        return [
            "consulting", "executive", "minimalism", "newspaper", "investor",
            "pitch", "dark", "editorial", "boardroom", "brand",
            "dmd_stripe", "dmd_vercel", "dmd_notion", "dmd_apple", "dmd_spotify",
            "dmd_tesla", "dmd_airbnb", "dmd_coinbase", "dmd_shopify", "dmd_figma",
            "dmd_framer", "dmd_cursor", "dmd_warp", "dmd_supabase", "dmd_uber",
            "dmd_ferrari", "dmd_bmw", "dmd_mongodb", "dmd_intercom", "dmd_webflow",
            "dmd_miro", "dmd_posthog", "dmd_raycast", "dmd_revolut",
            "dmd_superhuman", "dmd_zapier", "dmd_claude",
        ]


@mcp.tool()
def inkline_list_themes(category: str = "") -> list[str]:
    """List available Inkline themes.

    Args:
        category: Optional filter. One of: consulting, corporate, tech, dark,
                  warm, cool, nature, creative, editorial, pastel, luxury, minimal, industry.
    """
    try:
        from inkline.typst.themes import list_themes
        return list_themes(category=category) if category else list_themes()
    except Exception as exc:
        return [f"Error listing themes: {exc}"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _extract_title(content: str) -> str:
    """Extract document title from the first heading or first non-empty line."""
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line.lstrip("# ").strip()
        if line and not line.startswith("#"):
            return line[:60]
    return "Presentation"


def _text_to_sections(content: str, intent: str) -> list[dict]:
    """Convert raw text into a minimal sections[] list for DesignAdvisor.

    Splits on markdown headings. Each heading becomes one section.
    The LLM advisor will assign appropriate types.
    """
    sections = []
    current: dict = {}

    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("## ") or stripped.startswith("### "):
            if current.get("narrative", "").strip():
                sections.append(current)
            heading = stripped.lstrip("# ").strip()
            current = {"type": "narrative", "title": heading[:50], "narrative": ""}
        elif stripped.startswith("# "):
            pass  # Document title — handled separately
        else:
            if current:
                current["narrative"] = (current.get("narrative", "") + "\n" + line).strip()
            elif stripped:
                current = {"type": "narrative", "title": intent[:50], "narrative": stripped}

    if current and current.get("narrative", "").strip():
        sections.append(current)

    # If no structure found, treat whole content as one section
    if not sections:
        sections = [{"type": "narrative", "title": intent[:50], "narrative": content}]

    return sections


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main() -> None:
    """Start the MCP server with stdio transport (required for Claude Desktop)."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
