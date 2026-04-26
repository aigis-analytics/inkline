"""Inkline directive grammar — scopes, validation, and plugin registry.

Directive grammar follows Marpit's underscore-prefix convention:
  - Global: no prefix, in front-matter or HTML-comment before any heading
  - Local:  no prefix, in HTML-comment after a heading (cascades forward)
  - Spot:   ``_`` prefix, HTML-comment inside a single section (this slide only)

Plugin API::

    from inkline.authoring.directives import register

    @register(scope="global", name="confidentiality_band")
    def confidentiality_band(value, ctx):
        return {"header_overrides": {"text": value}}
"""

from __future__ import annotations

import logging
import sys
import warnings
from typing import Any, Callable

log = logging.getLogger(__name__)


class DirectiveError(ValueError):
    """Raised when a directive value fails validation (e.g. with --strict-directives)."""


# ---------------------------------------------------------------------------
# Built-in directive schemas
# ---------------------------------------------------------------------------

_GLOBAL_DIRECTIVES: dict[str, dict] = {
    "brand":           {"type": str,  "default": "minimal"},
    "template":        {"type": str,  "default": "consulting"},
    "mode":            {"type": str,  "default": "llm",     "choices": ["llm", "rules", "advised"]},
    "title":           {"type": str,  "default": ""},
    "subtitle":        {"type": str,  "default": ""},
    "date":            {"type": str,  "default": ""},
    "audience":        {"type": str,  "default": ""},
    "goal":            {"type": str,  "default": ""},
    "paper":           {"type": str,  "default": "16:9",    "choices": ["a4", "letter", "16:9", "4:3"]},
    "audit":           {"type": str,  "default": "structural", "choices": ["off", "structural", "strict"]},
    "headingDivider":  {"type": int,  "default": 2},
    "theme_overrides": {"type": dict, "default": {}},
    "output":          {"type": list, "default": ["pdf"]},
    "import":          {"type": list, "default": []},
    "footer":          {"type": str,  "default": ""},
    "header":          {"type": str,  "default": ""},
}

_LOCAL_DIRECTIVES: dict[str, dict] = {
    "layout":       {"type": str},
    "class":        {"type": str},
    "paginate":     {"type": (str, bool), "choices": ["true", "false", "hold", "skip", True, False]},
    "header":       {"type": str},
    "footer":       {"type": str},
    "accent":       {"type": str},
    "bg":           {"type": str},
    "notes":        {"type": str},
    "mode":         {"type": str, "choices": ["auto", "guided", "exact", "llm", "rules", "advised"]},
}

# Local directives that also have spot forms (``_name``)
_SPOT_DIRECTIVES = set(_LOCAL_DIRECTIVES.keys())

# ---------------------------------------------------------------------------
# Plugin registry
# ---------------------------------------------------------------------------

_PLUGIN_GLOBAL: dict[str, Callable] = {}
_PLUGIN_LOCAL:  dict[str, Callable] = {}


def register(scope: str, name: str):
    """Decorator to register a custom directive callback.

    Parameters
    ----------
    scope : str
        ``"global"`` or ``"local"`` (local directives also auto-get a spot form).
    name : str
        Directive name as it appears in front-matter / HTML-comments.

    The decorated function receives ``(value, ctx: dict)`` and returns a
    partial directive dict that is merged into the resolved directive set.

    Example::

        @register(scope="global", name="confidentiality_band")
        def confidentiality_band(value, ctx):
            return {"header_overrides": {"text": value}}
    """
    def decorator(fn: Callable) -> Callable:
        if scope == "global":
            _PLUGIN_GLOBAL[name] = fn
        elif scope == "local":
            _PLUGIN_LOCAL[name] = fn
        else:
            raise ValueError(f"register(scope=...): scope must be 'global' or 'local', got {scope!r}")
        return fn
    return decorator


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def _validate_directive(
    name: str,
    value: Any,
    schema: dict,
    strict: bool = False,
) -> Any:
    """Validate and coerce a directive value.

    Returns the (possibly coerced) value on success.
    Warns (or raises DirectiveError when strict) on failure.
    """
    expected = schema.get("type")
    choices   = schema.get("choices")

    # Type coercion
    if expected is not None:
        if isinstance(expected, tuple):
            # Multiple allowed types — just check
            if not isinstance(value, expected):
                # Try coercion to first type
                try:
                    value = expected[0](value)
                except (TypeError, ValueError):
                    pass
        elif expected is int and not isinstance(value, int):
            try:
                value = int(value)
            except (TypeError, ValueError):
                msg = f"Directive '{name}': expected int, got {type(value).__name__}"
                if strict:
                    raise DirectiveError(msg)
                warnings.warn(msg, stacklevel=4)
        elif expected is list and not isinstance(value, list):
            # Accept comma-separated string → list
            if isinstance(value, str):
                value = [v.strip() for v in value.split(",") if v.strip()]
            else:
                value = [value]
        elif expected is dict and not isinstance(value, dict):
            msg = f"Directive '{name}': expected dict, got {type(value).__name__}"
            if strict:
                raise DirectiveError(msg)
            warnings.warn(msg, stacklevel=4)

    # Choice validation
    if choices and value not in choices:
        msg = f"Directive '{name}': value {value!r} not in allowed choices {choices}"
        if strict:
            raise DirectiveError(msg)
        warnings.warn(msg, stacklevel=4)

    return value


def resolve_directive(
    name: str,
    value: Any,
    ctx: dict,
    strict: bool = False,
) -> tuple[str, Any]:
    """Resolve a single directive key/value pair.

    Returns ``(canonical_name, resolved_value)``.
    Unknown directives return unchanged with a warning.
    Spot prefix (``_``) is stripped before lookup.
    """
    is_spot = name.startswith("_")
    bare = name.lstrip("_")

    # Backend-specific layout: _layout_pptx, _layout_google_slides, etc.
    if bare.startswith("layout_"):
        return (name, value)   # pass through as-is

    # Spot directives check local schema first (spot overrides global for same name)
    if is_spot and bare in _LOCAL_DIRECTIVES:
        schema = _LOCAL_DIRECTIVES[bare]
        value = _validate_directive(bare, value, schema, strict=strict)
        return (name, value)  # keep underscore prefix for spot form

    # Look up in schema
    if bare in _GLOBAL_DIRECTIVES:
        schema = _GLOBAL_DIRECTIVES[bare]
        value = _validate_directive(bare, value, schema, strict=strict)
        return (bare, value)

    if bare in _LOCAL_DIRECTIVES:
        schema = _LOCAL_DIRECTIVES[bare]
        value = _validate_directive(bare, value, schema, strict=strict)
        # Spot form keeps the underscore prefix for callers to detect scope
        return (name if is_spot else bare, value)

    # Check plugin registries
    if bare in _PLUGIN_GLOBAL or bare in _PLUGIN_LOCAL:
        registry = _PLUGIN_GLOBAL if bare in _PLUGIN_GLOBAL else _PLUGIN_LOCAL
        try:
            extra = registry[bare](value, ctx)
            if isinstance(extra, dict):
                return (bare, extra)
        except DirectiveError:
            raise
        except Exception as exc:
            log.warning("Plugin directive '%s' raised: %s", bare, exc)
        return (bare, value)

    # Unknown directive — warn, preserve
    msg = f"Unknown directive '{bare}' — preserved in directives.unknown"
    if strict:
        raise DirectiveError(msg)
    warnings.warn(msg, stacklevel=4)
    return (f"unknown.{bare}", value)


def list_directives() -> dict[str, list[str]]:
    """Return all registered directive names grouped by scope.

    Used by the editor pane auto-completion endpoint.
    """
    return {
        "global": list(_GLOBAL_DIRECTIVES.keys()) + list(_PLUGIN_GLOBAL.keys()),
        "local":  list(_LOCAL_DIRECTIVES.keys())  + list(_PLUGIN_LOCAL.keys()),
        "spot":   ["_" + k for k in _SPOT_DIRECTIVES] + ["_" + k for k in _PLUGIN_LOCAL.keys()],
    }
