"""Example brand package showing how to register custom directives and classes.

This is a public example — replace "_example_brand" with your actual brand name
and supply real values for colors, fonts, and footers.

To activate this brand:
    inkline render deck.md --brand _example_brand

Or in front-matter:
    ---
    brand: _example_brand
    ---
"""

from inkline.authoring.directives import register, DirectiveError
from inkline.authoring.classes import register as register_class

# ── Example 1: global directive — document classification banner ──────────────

@register(scope="global", name="classification")
def classification(value: str, ctx: dict) -> dict:
    """Set a document classification banner in the header.

    Usage in front-matter::

        ---
        brand: _example_brand
        classification: CONFIDENTIAL
        ---

    Valid values: PUBLIC, INTERNAL, CONFIDENTIAL, RESTRICTED
    """
    valid = ("PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED")
    value = value.upper().strip()
    if value not in valid:
        raise DirectiveError(
            f"classification must be one of {valid}, got {value!r}"
        )

    color_map = {
        "PUBLIC":       "#2e7d32",  # green
        "INTERNAL":     "#1565c0",  # blue
        "CONFIDENTIAL": "#ef6c00",  # amber
        "RESTRICTED":   "#c62828",  # red
    }
    return {
        "header_overrides": {
            "text":  f"{value} — Do Not Distribute",
            "style": "ribbon",
            "color": color_map[value],
        },
        "footer_overrides": {
            "text": f"Document Classification: {value}",
        },
    }


# ── Example 2: local directive — risk indicator ───────────────────────────────

@register(scope="local", name="risk")
def risk(value: str, ctx: dict) -> dict:
    """Set a per-slide risk accent colour.

    Usage::

        ## Revenue Forecast
        <!-- _risk: high -->
        Revenue is down 40% quarter-on-quarter.

    Valid values: low, medium, high
    """
    valid = ("low", "medium", "high")
    value = value.lower().strip()
    if value not in valid:
        raise DirectiveError(f"risk must be one of {valid}, got {value!r}")

    accent_map = {
        "low":    "#2e7d32",
        "medium": "#ef6c00",
        "high":   "#c62828",
    }
    return {"accent": accent_map[value]}


# ── Example 3: class registration — hero slide variant ───────────────────────

register_class("hero", r"""
// hero class: large centred hero text for impact slides
#show heading.where(level: 2): set text(size: 48pt, weight: 900)
#show heading.where(level: 2): set align(center)
""")

register_class("brand-dark", r"""
// brand-dark class: force dark background (brand-specific colours)
""")
