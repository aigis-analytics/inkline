"""Inkline class system — Typst show-rule fragment registry.

Authors use ``_class: lead`` or ``_class: "lead invert"`` in directives.
Brand packages register Typst show-rule fragments via ``register()``.

The Typst slide renderer reads the ``class`` field on each slide context
and prepends registered fragments before the slide body.

Example registration (in a brand plugin)::

    from inkline.authoring.classes import register

    register("lead", r'''
      #show heading.where(level: 1): set text(size: 88pt, weight: 900)
      #show heading: set align(center)
    ''')

Example authoring::

    ## Big moment
    <!-- _class: lead -->
    We are the category leader.
"""

from __future__ import annotations

import logging

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_REGISTRY: dict[str, str] = {}


def register(name: str, typst_fragment: str) -> None:
    """Register a named class with a Typst show-rule fragment.

    Parameters
    ----------
    name : str
        Class name (e.g. ``"lead"``, ``"invert"``, ``"dark"``).
    typst_fragment : str
        Typst source that will be prepended before the slide content
        when this class is active.
    """
    _REGISTRY[name.strip()] = typst_fragment


def lookup(class_string: str) -> str:
    """Return the combined Typst fragment for a space-separated class string.

    Skips unknown class names with a warning.
    Returns an empty string if no classes are found.
    """
    if not class_string:
        return ""
    fragments: list[str] = []
    for cls in class_string.split():
        cls = cls.strip()
        if not cls:
            continue
        if cls in _REGISTRY:
            fragments.append(_REGISTRY[cls])
        else:
            log.debug("Class '%s' not registered — skipping", cls)
    return "\n".join(fragments)


def list_classes() -> list[str]:
    """Return all registered class names."""
    return list(_REGISTRY.keys())


# ---------------------------------------------------------------------------
# Built-in classes (minimal defaults — brands can override)
# ---------------------------------------------------------------------------

register("lead", r"""
// lead class: large centred heading
#show heading.where(level: 1): set text(size: 52pt, weight: 900)
#show heading: set align(center)
""")

register("invert", r"""
// invert class: swap foreground/background
// (actual colour swap depends on brand palette — this is a placeholder)
""")

register("dark", r"""
// dark class: force dark background regardless of template
""")
