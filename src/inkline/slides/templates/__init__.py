"""Slide templates — pre-built styling and layout functions.

Each template is a function that takes (slide_id, brand, slide_index, total_slides)
and returns a list of batchUpdate requests for base styling (background, decorative
shapes, section headers, etc.). User-defined elements are layered on top.
"""

from __future__ import annotations

from typing import Callable

_TEMPLATES: dict[str, Callable] = {}


def register_template(name: str, func: Callable) -> None:
    """Register a template function."""
    _TEMPLATES[name] = func


def get_template(name: str) -> Callable:
    """Get a template function by name."""
    if name not in _TEMPLATES:
        available = ", ".join(_TEMPLATES.keys()) or "(none)"
        raise KeyError(f"Unknown template '{name}'. Available: {available}")
    return _TEMPLATES[name]


def list_templates() -> list[str]:
    """List all registered template names."""
    return list(_TEMPLATES.keys())


DEFAULT_TEMPLATE = "aigis"

# Auto-register built-in templates on import
from inkline.slides.templates.aigis import template_aigis                  # noqa: E402
from inkline.slides.templates.newspaper import template_newspaper          # noqa: E402
from inkline.slides.templates.minimalism import template_minimalism        # noqa: E402
from inkline.slides.templates.executive import template_executive          # noqa: E402
from inkline.slides.templates.neo_retro import template_neo_retro          # noqa: E402
from inkline.slides.templates.sports import template_sports                # noqa: E402
from inkline.slides.templates.antigravity import template_antigravity      # noqa: E402
from inkline.slides.templates.mckinsey import template_mckinsey            # noqa: E402
from inkline.slides.templates.infotainment import template_infotainment    # noqa: E402
from inkline.slides.templates.neon_tech import template_neon_tech          # noqa: E402
from inkline.slides.templates.sculpture_pop import template_sculpture_pop  # noqa: E402

register_template("aigis", template_aigis)
register_template("newspaper", template_newspaper)
register_template("minimalism", template_minimalism)
register_template("executive", template_executive)
register_template("neo_retro", template_neo_retro)
register_template("sports", template_sports)
register_template("antigravity", template_antigravity)
register_template("mckinsey", template_mckinsey)
register_template("infotainment", template_infotainment)
register_template("neon_tech", template_neon_tech)
register_template("sculpture_pop", template_sculpture_pop)
