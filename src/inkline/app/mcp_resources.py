"""Inkline MCP resource registry — URI dispatch for the knowledge base.

Exposes accumulated design knowledge as machine-readable resources that
Claude Code can pull into context when authoring specs.

Resource URIs follow the ``inkline://`` scheme:

    inkline://playbooks/index               — list of all playbooks with metadata
    inkline://playbooks/<name>              — full playbook markdown
    inkline://layouts                       — slide-type catalogue with capacity rules
    inkline://layouts/<slide_type>          — single slide-type spec
    inkline://anti-patterns                 — anti-pattern library
    inkline://archetypes                    — infographic archetype index
    inkline://brands                        — available brands list
    inkline://brands/<name>                 — brand palette + typography
    inkline://themes                        — theme list
    inkline://themes/<name>                 — theme palette
    inkline://typography                    — type-scale + capacity rules
    inkline://templates                     — template catalogue
    inkline://templates/<name>              — template detail

Usage (from mcp_server.py)::

    from inkline.app.mcp_resources import list_resources, read_resource

    resources = list_resources()
    content = read_resource("inkline://layouts/three_card")
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)
_MCP_REFERENCE_LICENSES = {"public_reusable", "public_reference_only"}

# Root of the inkline source tree
_SRC_ROOT = Path(__file__).parent.parent
_PLAYBOOKS_DIR = _SRC_ROOT / "intelligence" / "playbooks"
_TEMPLATE_CATALOG_DIR = _SRC_ROOT / "intelligence" / "template_catalog"
_BRANDS_DIR = _SRC_ROOT / "brands"
_THEMES_DIR = _SRC_ROOT / "typst" / "themes"
_ANTI_PATTERNS_MODULE = _SRC_ROOT / "intelligence" / "anti_patterns.py"


class ResourceNotFoundError(KeyError):
    """Raised when a resource URI is not found in the registry."""


_SAFE_RESOURCE_NAME = re.compile(r"^[A-Za-z0-9._-]+$")


# ---------------------------------------------------------------------------
# Playbook index (generated at runtime from front-matter, cached)
# ---------------------------------------------------------------------------

_playbook_index_cache: dict | None = None


def _parse_front_matter(content: str) -> dict:
    """Extract YAML front-matter from a markdown file."""
    if not content.startswith("---"):
        return {}
    end = content.find("---", 3)
    if end == -1:
        return {}
    fm_text = content[3:end].strip()
    result = {}
    for line in fm_text.splitlines():
        if ":" in line and not line.startswith(" ") and not line.startswith("-"):
            k, _, v = line.partition(":")
            k = k.strip()
            v = v.strip()
            # Handle list values like [a, b, c]
            if v.startswith("[") and v.endswith("]"):
                items = v[1:-1].split(",")
                result[k] = [i.strip().strip('"\'') for i in items if i.strip()]
            elif v.startswith('"') and v.endswith('"'):
                result[k] = v[1:-1]
            elif v.startswith("'") and v.endswith("'"):
                result[k] = v[1:-1]
            else:
                result[k] = v
    return result


def _build_playbook_index() -> dict:
    """Scan all playbooks and build a metadata index."""
    global _playbook_index_cache
    if _playbook_index_cache is not None:
        return _playbook_index_cache

    index: dict[str, dict] = {}
    if not _PLAYBOOKS_DIR.exists():
        return index

    for md_file in sorted(_PLAYBOOKS_DIR.glob("*.md")):
        name = md_file.stem
        if name.startswith("_") or name == "__init__":
            continue
        content = md_file.read_text(encoding="utf-8")
        fm = _parse_front_matter(content)
        index[name] = {
            "name": name,
            "uri": f"inkline://playbooks/{name}",
            "domain": fm.get("domain", "general"),
            "audience": fm.get("audience", []),
            "slide_type_relevance": fm.get("slide_type_relevance", []),
            "brand_affinity": fm.get("brand_affinity", []),
            "last_updated": fm.get("last_updated", ""),
            "version": fm.get("version", "1.0.0"),
            "description": fm.get("description", ""),
        }

    _playbook_index_cache = index
    return index


# ---------------------------------------------------------------------------
# Slide type catalogue
# ---------------------------------------------------------------------------

_SLIDE_TYPE_DESCRIPTIONS: dict[str, dict] = {
    "title": {
        "description": "Cover / title slide with company name, tagline, date.",
        "capacity": {"max_bullet_chars": None},
        "data_fields": ["company", "tagline", "date", "subtitle", "background_image"],
    },
    "content": {
        "description": "Section header with bullets and narrative. Default for unannotated sections.",
        "capacity": {"max_bullets": 6, "max_bullet_chars": 80},
        "data_fields": ["section", "title", "items"],
    },
    "three_card": {
        "description": "Three side-by-side cards. Classic for 3 problems / 3 solutions / 3 features.",
        "capacity": {"max_cards": 3, "max_title_chars": 40, "max_body_chars": 200},
        "data_fields": ["section", "title", "cards: [{title, body}]"],
    },
    "four_card": {
        "description": "2×2 card grid. For quadrant comparisons or 4 features.",
        "capacity": {"max_cards": 4, "max_title_chars": 35, "max_body_chars": 150},
        "data_fields": ["section", "title", "cards: [{title, body}]"],
    },
    "split": {
        "description": "Left narrative + right image/chart. Classic for 'what is X' slides.",
        "capacity": {"max_bullet_chars": 70, "max_bullets": 5},
        "data_fields": ["section", "title", "body", "image_path"],
    },
    "stat": {
        "description": "Large hero stat with supporting context. For 1-3 key numbers.",
        "capacity": {"max_stats": 3, "max_value_chars": 20, "max_label_chars": 60},
        "data_fields": ["section", "title", "stats: [{value, label, delta}]"],
    },
    "kpi_strip": {
        "description": "Horizontal strip of 4-8 KPI boxes. For scorecards and dashboards.",
        "capacity": {"max_kpis": 8, "max_label_chars": 40},
        "data_fields": ["section", "title", "kpis: [{value, label, delta}]"],
    },
    "table": {
        "description": "Data table with header row. Auto-shrinks font for >6 rows.",
        "capacity": {"max_rows": 12, "max_cols": 8},
        "data_fields": ["section", "title", "headers", "rows"],
    },
    "chart": {
        "description": "Full-bleed chart with title and optional caption.",
        "capacity": {"chart_height_hint": "8-9cm"},
        "data_fields": ["section", "title", "chart_type", "chart_data"],
    },
    "freeform": {
        "description": "Bespoke hero exhibit with positioned shapes. For complex hero slides that don't fit typed layouts.",
        "capacity": {},
        "data_fields": ["title", "section", "shapes: [{type, x, y, w, h, ...}]"],
        "directive": "_shapes_file: path/to/shapes.json",
    },
    "comparison": {
        "description": "Side-by-side comparison table. Classic for before/after or vendor comparison.",
        "capacity": {"max_rows": 8, "max_cols": 3},
        "data_fields": ["section", "title", "headers", "rows"],
    },
    "timeline": {
        "description": "Horizontal timeline with milestones.",
        "capacity": {"max_milestones": 6},
        "data_fields": ["section", "title", "milestones: [{date, label, description}]"],
    },
    "process_flow": {
        "description": "Left-to-right process steps with arrows.",
        "capacity": {"max_steps": 5},
        "data_fields": ["section", "title", "steps: [{title, description}]"],
    },
}


def _get_layouts_catalogue() -> str:
    """Generate the layouts catalogue as markdown."""
    from inkline.authoring.backend_coverage import COVERAGE, DOWNGRADE

    lines = ["# Inkline Slide Type Catalogue\n"]
    lines.append("All 22+ typed layouts with capacity rules and data shapes.\n")

    for slide_type, entry in sorted(COVERAGE.items()):
        desc = _SLIDE_TYPE_DESCRIPTIONS.get(slide_type, {})
        backends = ", ".join(k for k, v in entry.items() if v)
        lines.append(f"## {slide_type}")
        if desc.get("description"):
            lines.append(f"{desc['description']}\n")
        lines.append(f"**Backends:** {backends}")
        downgrade = DOWNGRADE.get(slide_type)
        if downgrade:
            lines.append(f"**Downgrade chain:** {' → '.join(downgrade)}")
        cap = desc.get("capacity", {})
        if cap:
            lines.append(f"**Capacity:** {cap}")
        fields = desc.get("data_fields", [])
        if fields:
            lines.append(f"**Data fields:** `{', '.join(fields)}`")
        directive = desc.get("directive")
        if directive:
            lines.append(f"**Directive example:** `{directive}`")
        lines.append("")

    return "\n".join(lines)


def _get_single_layout(slide_type: str) -> str:
    """Get spec for a single slide type."""
    from inkline.authoring.backend_coverage import COVERAGE, DOWNGRADE

    if slide_type not in COVERAGE:
        raise ResourceNotFoundError(f"Unknown slide_type: {slide_type!r}")

    entry = COVERAGE[slide_type]
    desc = _SLIDE_TYPE_DESCRIPTIONS.get(slide_type, {})
    backends = ", ".join(k for k, v in entry.items() if v)
    downgrade = DOWNGRADE.get(slide_type, [])

    lines = [
        f"# Layout: {slide_type}",
        "",
        desc.get("description", "No description available."),
        "",
        f"**Backends:** {backends}",
    ]
    if downgrade:
        lines.append(f"**Downgrade chain:** {' → '.join(downgrade)}")
    cap = desc.get("capacity", {})
    if cap:
        lines.append(f"**Capacity rules:** `{cap}`")
    fields = desc.get("data_fields", [])
    if fields:
        lines.append(f"\n**Required data fields:**")
        for f in fields:
            lines.append(f"- `{f}`")
    directive = desc.get("directive")
    if directive:
        lines.append(f"\n**Markdown directive:**\n```\n{directive}\n```")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Anti-patterns
# ---------------------------------------------------------------------------

def _get_anti_patterns() -> str:
    """Return anti-patterns content from the intelligence module."""
    try:
        from inkline.intelligence.anti_patterns import AntiPatternLibrary
        lib = AntiPatternLibrary()
        patterns = lib.patterns
        lines = ["# Inkline Anti-Pattern Library\n"]
        lines.append("Patterns to avoid in institutional presentations.\n")
        for i, p in enumerate(patterns):
            name = p.get("name", f"Pattern {i+1}")
            desc = p.get("description", "")
            fix = p.get("fix", "")
            lines.append(f"## {name}")
            if desc:
                lines.append(desc)
            if fix:
                lines.append(f"**Fix:** {fix}")
            lines.append("")
        return "\n".join(lines)
    except Exception as exc:
        log.debug("Could not load anti-patterns module: %s", exc)
        return (
            "# Inkline Anti-Pattern Library\n\n"
            "Anti-patterns are loaded from `intelligence/anti_patterns.py`.\n"
            "See that module for the full list of patterns to avoid.\n"
        )


# ---------------------------------------------------------------------------
# Brand registry
# ---------------------------------------------------------------------------

def _get_brands_list() -> str:
    """List all available brands."""
    try:
        from inkline.brands import list_brands
        brands = list_brands()
    except Exception:
        brands = []
    if not brands:
        brands = ["minimal"]

    lines = ["# Available Inkline Brands\n"]
    for b in brands:
        lines.append(f"- {b}")
    lines.append("\nGet brand details: `inkline://brands/<name>`")
    return "\n".join(lines)


def _get_brand_detail(name: str) -> str:
    """Get palette and typography for a specific brand."""
    try:
        from inkline.brands import get_brand
        brand = get_brand(name)
        if brand is None:
            raise ResourceNotFoundError(f"Brand not found: {name!r}")
        if is_dataclass(brand):
            payload = asdict(brand)
        elif hasattr(brand, "__dict__"):
            payload = {
                key: value
                for key, value in vars(brand).items()
                if not key.startswith("_")
            }
        else:
            payload = {"name": str(brand)}
        return f"# Brand: {name}\n\n```json\n{json.dumps(payload, indent=2)}\n```"
    except ResourceNotFoundError:
        raise
    except Exception as exc:
        return f"# Brand: {name}\n\nCould not load brand details: {exc}"


# ---------------------------------------------------------------------------
# Theme registry
# ---------------------------------------------------------------------------

def _get_themes_list() -> str:
    """List all available themes."""
    try:
        from inkline.typst.theme_registry import list_themes
        themes = list_themes()
        lines = ["# Available Inkline Themes\n"]
        for t in sorted(themes):
            lines.append(f"- {t}")
        return "\n".join(lines)
    except Exception as exc:
        return f"# Inkline Themes\n\nCould not load themes: {exc}"


def _get_theme_detail(name: str) -> str:
    """Get palette for a specific theme."""
    try:
        from inkline.typst.theme_registry import get_theme
        theme = get_theme(name)
        if theme is None:
            raise ResourceNotFoundError(f"Theme not found: {name!r}")
        return f"# Theme: {name}\n\n```json\n{json.dumps(theme, indent=2)}\n```"
    except ResourceNotFoundError:
        raise
    except Exception as exc:
        return f"# Theme: {name}\n\nCould not load theme: {exc}"


# ---------------------------------------------------------------------------
# Archetypes
# ---------------------------------------------------------------------------

def _get_archetypes() -> str:
    """Return the infographic archetype index."""
    try:
        from inkline.intelligence.playbooks.infographic_styles import _ARCHETYPES
        lines = ["# Inkline Infographic Archetypes\n"]
        for arch in _ARCHETYPES:
            lines.append(f"## {arch['name']}")
            lines.append(arch.get("description", ""))
            lines.append("")
        return "\n".join(lines)
    except Exception:
        pass
    # Fallback: read from the playbook file
    p = _PLAYBOOKS_DIR / "infographic_styles.md"
    if p.exists():
        return p.read_text(encoding="utf-8")
    return "# Infographic Archetypes\n\nSee `intelligence/playbooks/infographic_styles.md`."


def _get_slide_roles() -> str:
    from inkline.intelligence.full_slide_archetypes import ROLE_TO_DEFAULT_ARCHETYPE

    lines = ["# Inkline Slide Roles\n"]
    for role, archetype in sorted(ROLE_TO_DEFAULT_ARCHETYPE.items()):
        lines.append(f"- `{role}` → `{archetype}`")
    return "\n".join(lines)


def _get_single_slide_role(role: str) -> str:
    from inkline.intelligence.full_slide_archetypes import (
        ROLE_TO_DEFAULT_ARCHETYPE,
        get_full_slide_archetype,
    )

    if role not in ROLE_TO_DEFAULT_ARCHETYPE:
        raise ResourceNotFoundError(f"Unknown slide role: {role!r}")
    archetype_id = ROLE_TO_DEFAULT_ARCHETYPE.get(role, "")
    if not archetype_id:
        payload = {
            "role": role,
            "default_archetype": "",
            "functional_roles": [role],
            "visual_intent": {},
            "compile_targets": {},
        }
        return f"# Slide Role: {role}\n\n```json\n{json.dumps(payload, indent=2)}\n```"
    archetype = get_full_slide_archetype(archetype_id)
    payload = {
        "role": role,
        "default_archetype": archetype_id,
        "functional_roles": archetype.get("functional_roles", []),
        "visual_intent": archetype.get("visual_intent", {}),
        "compile_targets": archetype.get("compile_targets", {}),
    }
    return f"# Slide Role: {role}\n\n```json\n{json.dumps(payload, indent=2)}\n```"


def _get_full_slide_archetypes() -> str:
    from inkline.intelligence.full_slide_archetypes import list_full_slide_archetypes

    lines = ["# Inkline Full-Slide Archetypes\n"]
    for item in list_full_slide_archetypes():
        lines.append(f"## {item['id']}")
        lines.append(f"- roles: {', '.join(item.get('functional_roles', []))}")
        lines.append(f"- compile target: {item.get('compile_targets', {}).get('layout_id', '')}")
        lines.append(f"- tone: {item.get('visual_intent', {}).get('tone', '')}")
        lines.append("")
    return "\n".join(lines)


def _get_single_full_slide_archetype(archetype_id: str) -> str:
    from inkline.intelligence.full_slide_archetypes import get_full_slide_archetype

    item = get_full_slide_archetype(archetype_id)
    return f"# Full-Slide Archetype: {archetype_id}\n\n```json\n{json.dumps(item, indent=2)}\n```"


def _get_reference_families() -> str:
    from inkline.intelligence.reference_catalog import (
        list_reference_families,
        sanitize_reference_family_for_mcp,
    )

    lines = ["# Inkline Reference Families\n"]
    families = [
        item
        for item in list_reference_families()
        if item.get("license_classification") in _MCP_REFERENCE_LICENSES
    ]
    if not families:
        lines.append("No reference families currently installed.")
    for item in families:
        safe = sanitize_reference_family_for_mcp(item)
        lines.append(f"## {item.get('reference_family_id', '')}")
        lines.append(f"- license: {safe.get('license_classification', '')}")
        lines.append(f"- slide_count: {len(safe.get('slides', []))}")
        lines.append("")
    return "\n".join(lines)


def _get_single_reference_family(reference_family_id: str) -> str:
    from inkline.intelligence.reference_catalog import (
        load_reference_family,
        sanitize_reference_family_for_mcp,
    )

    loaded = load_reference_family(reference_family_id)
    if loaded.get("license_classification") not in _MCP_REFERENCE_LICENSES:
        raise ResourceNotFoundError(f"Reference family not exposed via MCP: {reference_family_id!r}")
    item = sanitize_reference_family_for_mcp(loaded)
    return f"# Reference Family: {reference_family_id}\n\n```json\n{json.dumps(item, indent=2)}\n```"


def _get_reference_slides() -> str:
    from inkline.intelligence.reference_catalog import list_reference_families

    lines = ["# Inkline Reference Slides\n"]
    found = False
    for family in list_reference_families():
        if family.get("license_classification") not in _MCP_REFERENCE_LICENSES:
            continue
        for slide in family.get("slides", []):
            slide_id = slide.get("reference_slide_id", "")
            if not slide_id:
                continue
            found = True
            lines.append(f"- `{slide_id}` ({family.get('reference_family_id', '')})")
    if not found:
        lines.append("No reference slides currently installed.")
    return "\n".join(lines)


def _get_single_reference_slide(reference_slide_id: str) -> str:
    from inkline.intelligence.reference_catalog import (
        list_reference_families,
        load_reference_family,
        load_reference_slide,
        sanitize_reference_slide_for_mcp,
    )

    loaded = load_reference_slide(reference_slide_id)
    family_id = str(loaded.get("reference_family_id") or "").strip()
    if not family_id:
        for family in list_reference_families():
            for slide in family.get("slides", []):
                if slide.get("reference_slide_id") == reference_slide_id:
                    family_id = str(family.get("reference_family_id", "")).strip()
                    break
            if family_id:
                break
    if family_id:
        family = load_reference_family(family_id)
        if family.get("license_classification") not in _MCP_REFERENCE_LICENSES:
            raise ResourceNotFoundError(f"Reference slide not exposed via MCP: {reference_slide_id!r}")
    item = sanitize_reference_slide_for_mcp(loaded)
    return f"# Reference Slide: {reference_slide_id}\n\n```json\n{json.dumps(item, indent=2)}\n```"


def _get_storyboard_rules() -> str:
    return (
        "# Inkline Storyboard Rules\n\n"
        "- Every slide gets a stable `slide_id`.\n"
        "- Metadata precedence: explicit overrides > slide object storyboard > top-level storyboard > inferred defaults.\n"
        "- Execute Mode renders resolved metadata only.\n"
        "- Audit consumes the same resolved metadata plus rendered artifacts.\n"
        "- Missing required evaluated dimensions escalate client-facing decks to human sign-off.\n"
    )


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

def _get_templates_list() -> str:
    """List all available slide templates."""
    try:
        from inkline.typst.theme_registry import list_templates
        templates = list_templates()
        lines = ["# Available Inkline Slide Templates\n"]
        for t in sorted(templates):
            lines.append(f"- {t}")
        lines.append("\nGet template details: `inkline://templates/<name>`")
        return "\n".join(lines)
    except Exception as exc:
        return f"# Inkline Templates\n\nCould not load templates: {exc}"


def _get_template_detail(name: str) -> str:
    """Get detail for a specific template."""
    catalog_files = list(_TEMPLATE_CATALOG_DIR.glob("*.json")) if _TEMPLATE_CATALOG_DIR.exists() else []
    for f in catalog_files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            entries = data if isinstance(data, list) else data.get("templates", [data])
            for entry in entries:
                if entry.get("id") == name or entry.get("name") == name:
                    return f"# Template: {name}\n\n```json\n{json.dumps(entry, indent=2)}\n```"
        except Exception:
            continue
    return f"# Template: {name}\n\nTemplate detail not found in catalog."


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def list_resources() -> list[dict]:
    """Return all available MCP resources.

    Returns
    -------
    list[dict]
        Each dict has: uri, name, description, mimeType.
    """
    index = _build_playbook_index()
    resources = [
        {
            "uri": "inkline://playbooks/index",
            "name": "Playbook Index",
            "description": "Index of all design playbooks with metadata",
            "mimeType": "text/markdown",
        },
        {
            "uri": "inkline://layouts",
            "name": "Slide Layout Catalogue",
            "description": "All 22+ typed layouts with capacity rules and data shapes",
            "mimeType": "text/markdown",
        },
        {
            "uri": "inkline://anti-patterns",
            "name": "Anti-Pattern Library",
            "description": "Design patterns to avoid in institutional presentations",
            "mimeType": "text/markdown",
        },
        {
            "uri": "inkline://archetypes",
            "name": "Infographic Archetypes",
            "description": "16 infographic archetype types with descriptions",
            "mimeType": "text/markdown",
        },
        {
            "uri": "inkline://slide_roles",
            "name": "Slide Roles",
            "description": "Functional page roles mapped to default full-slide archetypes",
            "mimeType": "text/markdown",
        },
        {
            "uri": "inkline://archetypes/full_slide",
            "name": "Full-Slide Archetypes",
            "description": "Reference-driven full-slide design archetypes",
            "mimeType": "text/markdown",
        },
        {
            "uri": "inkline://reference_families",
            "name": "Reference Families",
            "description": "Installed benchmark/reference deck families",
            "mimeType": "text/markdown",
        },
        {
            "uri": "inkline://reference_slides",
            "name": "Reference Slides",
            "description": "Installed reference slide manifests and exemplars",
            "mimeType": "text/markdown",
        },
        {
            "uri": "inkline://storyboard_rules",
            "name": "Storyboard Rules",
            "description": "Shared authoring/audit rules for storyboard-aware decks",
            "mimeType": "text/markdown",
        },
        {
            "uri": "inkline://brands",
            "name": "Brand Registry",
            "description": "List of available brands",
            "mimeType": "text/markdown",
        },
        {
            "uri": "inkline://themes",
            "name": "Theme Registry",
            "description": "List of available themes",
            "mimeType": "text/markdown",
        },
        {
            "uri": "inkline://typography",
            "name": "Typography Guide",
            "description": "Type-scale and capacity rules for presentations",
            "mimeType": "text/markdown",
        },
        {
            "uri": "inkline://templates",
            "name": "Template Catalogue",
            "description": "Available slide templates",
            "mimeType": "text/markdown",
        },
    ]
    # Add per-playbook resources
    for name, meta in index.items():
        resources.append({
            "uri": f"inkline://playbooks/{name}",
            "name": f"Playbook: {name}",
            "description": meta.get("description", ""),
            "mimeType": "text/markdown",
        })

    try:
        from inkline.intelligence.full_slide_archetypes import ROLE_TO_DEFAULT_ARCHETYPE
        for role in sorted(ROLE_TO_DEFAULT_ARCHETYPE):
            resources.append({
                "uri": f"inkline://slide_roles/{role}",
                "name": f"Slide Role: {role}",
                "description": f"Detail for slide role {role}",
                "mimeType": "text/markdown",
            })
    except Exception:
        pass

    try:
        from inkline.intelligence.full_slide_archetypes import list_full_slide_archetypes
        for item in list_full_slide_archetypes():
            resources.append({
                "uri": f"inkline://archetypes/full_slide/{item['id']}",
                "name": f"Full-Slide Archetype: {item['id']}",
                "description": f"Roles: {', '.join(item.get('functional_roles', []))}",
                "mimeType": "text/markdown",
            })
    except Exception:
        pass

    try:
        from inkline.intelligence.reference_catalog import list_reference_families
        for item in list_reference_families():
            if item.get("license_classification") not in _MCP_REFERENCE_LICENSES:
                continue
            family_id = item.get("reference_family_id", "")
            resources.append({
                "uri": f"inkline://reference_families/{family_id}",
                "name": f"Reference Family: {family_id}",
                "description": item.get("license_classification", ""),
                "mimeType": "text/markdown",
            })
            for slide in item.get("slides", []):
                slide_id = slide.get("reference_slide_id", "")
                if not slide_id:
                    continue
                resources.append({
                    "uri": f"inkline://reference_slides/{slide_id}",
                    "name": f"Reference Slide: {slide_id}",
                    "description": slide.get("role", "") or family_id,
                    "mimeType": "text/markdown",
                })
    except Exception:
        pass

    return resources


def read_resource(uri: str) -> str:
    """Read the content of a resource by URI.

    Parameters
    ----------
    uri : str
        Resource URI following the ``inkline://`` scheme.

    Returns
    -------
    str
        Resource content as a string (usually markdown).

    Raises
    ------
    ResourceNotFoundError
        If the URI does not match any known resource.
    """
    uri = uri.strip()

    # inkline://playbooks/index
    if uri == "inkline://playbooks/index":
        index = _build_playbook_index()
        lines = ["# Inkline Playbook Index\n"]
        for name, meta in sorted(index.items()):
            lines.append(f"## {name}")
            lines.append(f"- URI: `inkline://playbooks/{name}`")
            lines.append(f"- Domain: {meta['domain']}")
            lines.append(f"- Description: {meta.get('description', '')}")
            lines.append(f"- Slide types: {meta.get('slide_type_relevance', [])}")
            lines.append(f"- Version: {meta.get('version', '1.0.0')}")
            lines.append("")
        return "\n".join(lines)

    # inkline://playbooks/<name>
    if uri.startswith("inkline://playbooks/"):
        name = uri[len("inkline://playbooks/"):]
        index = _build_playbook_index()
        if not name or not _SAFE_RESOURCE_NAME.fullmatch(name) or name not in index:
            raise ResourceNotFoundError(f"Playbook not found: {name!r}")
        p = _PLAYBOOKS_DIR / f"{name}.md"
        if not p.exists():
            raise ResourceNotFoundError(f"Playbook not found: {name!r}")
        return p.read_text(encoding="utf-8")

    # inkline://layouts (catalogue)
    if uri == "inkline://layouts":
        return _get_layouts_catalogue()

    # inkline://layouts/<slide_type>
    if uri.startswith("inkline://layouts/"):
        slide_type = uri[len("inkline://layouts/"):]
        return _get_single_layout(slide_type)

    # inkline://anti-patterns
    if uri == "inkline://anti-patterns":
        return _get_anti_patterns()

    # inkline://archetypes
    if uri == "inkline://archetypes":
        return _get_archetypes()

    if uri == "inkline://slide_roles":
        return _get_slide_roles()

    if uri.startswith("inkline://slide_roles/"):
        role = uri[len("inkline://slide_roles/"):]
        return _get_single_slide_role(role)

    if uri == "inkline://archetypes/full_slide":
        return _get_full_slide_archetypes()

    if uri.startswith("inkline://archetypes/full_slide/"):
        archetype_id = uri[len("inkline://archetypes/full_slide/"):]
        return _get_single_full_slide_archetype(archetype_id)

    if uri == "inkline://reference_families":
        return _get_reference_families()

    if uri.startswith("inkline://reference_families/"):
        family_id = uri[len("inkline://reference_families/"):]
        return _get_single_reference_family(family_id)

    if uri == "inkline://reference_slides":
        return _get_reference_slides()

    if uri.startswith("inkline://reference_slides/"):
        slide_id = uri[len("inkline://reference_slides/"):]
        return _get_single_reference_slide(slide_id)

    if uri == "inkline://storyboard_rules":
        return _get_storyboard_rules()

    # inkline://brands
    if uri == "inkline://brands":
        return _get_brands_list()

    # inkline://brands/<name>
    if uri.startswith("inkline://brands/"):
        name = uri[len("inkline://brands/"):]
        return _get_brand_detail(name)

    # inkline://themes
    if uri == "inkline://themes":
        return _get_themes_list()

    # inkline://themes/<name>
    if uri.startswith("inkline://themes/"):
        name = uri[len("inkline://themes/"):]
        return _get_theme_detail(name)

    # inkline://typography
    if uri == "inkline://typography":
        p = _PLAYBOOKS_DIR / "typography.md"
        if p.exists():
            return p.read_text(encoding="utf-8")
        return "# Typography\n\nSee `intelligence/playbooks/typography.md`."

    # inkline://templates
    if uri == "inkline://templates":
        return _get_templates_list()

    # inkline://templates/<name>
    if uri.startswith("inkline://templates/"):
        name = uri[len("inkline://templates/"):]
        return _get_template_detail(name)

    raise ResourceNotFoundError(f"Unknown resource URI: {uri!r}")
