"""Design playbooks for the DesignAdvisor intelligence layer.

Each playbook is a Markdown file containing rules, heuristics, decision trees,
and reference material that an LLM-based DesignAdvisor can use to make smart
design decisions about charts, layouts, colours, typography, and more.

Usage
-----
    from inkline.intelligence.playbooks import load_playbook, load_all_playbooks

    # Load a single playbook by name
    chart_rules = load_playbook("chart_selection")

    # Load all playbooks as a dict
    all_playbooks = load_all_playbooks()

    # Get the list of available playbook names
    from inkline.intelligence.playbooks import PLAYBOOK_NAMES
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional

log = logging.getLogger(__name__)

# Directory containing the .md playbook files
PLAYBOOKS_DIR = Path(__file__).parent

# Registry of all available playbooks (name -> filename)
PLAYBOOK_REGISTRY: Dict[str, str] = {
    "chart_selection": "chart_selection.md",
    "infographic_styles": "infographic_styles.md",
    "slide_layouts": "slide_layouts.md",
    "document_design": "document_design.md",
    "color_theory": "color_theory.md",
    "typography": "typography.md",
    "visual_libraries": "visual_libraries.md",
    "template_catalog": "template_catalog.md",
    "professional_exhibit_design": "professional_exhibit_design.md",
    "design_md_styles": "__generated__",  # Dynamic: loaded from design_md_styles module
}

# Convenience list of playbook names
PLAYBOOK_NAMES: List[str] = list(PLAYBOOK_REGISTRY.keys())


def load_playbook(name: str) -> str:
    """Load a single playbook by name and return its Markdown content.

    Parameters
    ----------
    name : str
        The playbook name (e.g., "chart_selection", "color_theory").
        Must be one of the keys in ``PLAYBOOK_REGISTRY``.

    Returns
    -------
    str
        The full Markdown text of the playbook.

    Raises
    ------
    ValueError
        If the playbook name is not recognised.
    FileNotFoundError
        If the .md file is missing from disk.
    """
    if name not in PLAYBOOK_REGISTRY:
        raise ValueError(
            f"Unknown playbook '{name}'. "
            f"Available playbooks: {', '.join(PLAYBOOK_NAMES)}"
        )

    # Dynamic playbook: design_md_styles catalog
    if PLAYBOOK_REGISTRY[name] == "__generated__":
        try:
            from inkline.intelligence.design_md_styles import get_playbook_text
            content = get_playbook_text()
            log.debug("Loaded dynamic playbook '%s' (%d chars)", name, len(content))
            return content
        except Exception as exc:
            log.warning("Failed to generate dynamic playbook '%s': %s", name, exc)
            return ""

    filepath = PLAYBOOKS_DIR / PLAYBOOK_REGISTRY[name]
    if not filepath.exists():
        raise FileNotFoundError(f"Playbook file not found: {filepath}")

    content = filepath.read_text(encoding="utf-8")
    log.debug("Loaded playbook '%s' (%d chars)", name, len(content))
    return content


def load_all_playbooks() -> Dict[str, str]:
    """Load all playbooks and return them as a name -> content dict.

    Returns
    -------
    dict[str, str]
        Mapping of playbook name to its Markdown content.
    """
    playbooks = {}
    for name in PLAYBOOK_NAMES:
        try:
            playbooks[name] = load_playbook(name)
        except (ValueError, FileNotFoundError) as exc:
            log.warning("Failed to load playbook '%s': %s", name, exc)
    return playbooks


def load_playbooks_for_task(task_type: str) -> Dict[str, str]:
    """Load a subset of playbooks relevant to a specific design task.

    This is useful when the full set of playbooks would exceed token limits
    and only a subset is needed for the current task.

    Parameters
    ----------
    task_type : str
        The type of design task. Supported values:
        - "chart" — chart selection + color theory
        - "slide" — slide layouts + typography + color theory
        - "document" — document design + typography + color theory
        - "infographic" — infographic styles + color theory + typography
        - "full" — all playbooks

    Returns
    -------
    dict[str, str]
        Mapping of playbook name to its Markdown content.
    """
    task_playbooks = {
        "chart": ["chart_selection", "color_theory", "professional_exhibit_design"],
        "slide": ["slide_layouts", "template_catalog", "typography", "color_theory", "professional_exhibit_design"],
        "document": ["document_design", "typography", "color_theory"],
        "infographic": ["infographic_styles", "template_catalog", "color_theory", "typography", "professional_exhibit_design"],
        "full": PLAYBOOK_NAMES,
    }

    names = task_playbooks.get(task_type, PLAYBOOK_NAMES)
    result = {}
    for name in names:
        try:
            result[name] = load_playbook(name)
        except (ValueError, FileNotFoundError) as exc:
            log.warning("Failed to load playbook '%s': %s", name, exc)
    return result


def load_playbook_summary(name: str, max_chars: int = 4000) -> str:
    """Load a condensed version of a playbook, trimming bulk reference material.

    For ``template_catalog``: strips the 771-entry manifest (section 6+),
    keeping only the 16 archetype recipes, decision matrix, and rules.
    For ``slide_layouts``: includes rules and decision trees, skips the
    verbose formatting reference tables (section 5+).
    For other playbooks: truncates to ``max_chars``.

    Parameters
    ----------
    name : str
        Playbook name.
    max_chars : int
        Maximum character length for the returned text.

    Returns
    -------
    str
        Condensed playbook text.
    """
    text = load_playbook(name)

    if name == "template_catalog":
        # Drop section 6 "Catalog manifests" (the 771-entry bulk index) onward
        cutoff = text.find("\n## 6. Catalog manifests")
        if cutoff > 0:
            text = text[:cutoff].rstrip()
    elif name == "slide_layouts":
        # Drop section 5 "Formatting Standards" onward (verbose reference tables)
        cutoff = text.find("\n## 5. Formatting Standards")
        if cutoff > 0:
            text = text[:cutoff].rstrip()

    if len(text) > max_chars:
        text = text[:max_chars].rstrip()
        text += "\n\n... [condensed — full playbook available via load_playbook()]"

    return text


def get_playbook_summary() -> str:
    """Return a brief summary of all available playbooks.

    Useful for including in an LLM system prompt to let the model know
    what design knowledge is available.

    Returns
    -------
    str
        A formatted string listing each playbook with a one-line description.
    """
    descriptions = {
        "chart_selection": "Rules for choosing the right chart type based on data shape and communication goal",
        "infographic_styles": "Visual formats beyond charts: timelines, comparisons, icon grids, flowcharts",
        "slide_layouts": "Consulting-grade slide structures, the Pyramid Principle, and layout patterns",
        "document_design": "Report formatting: executive summaries, financial tables, RAG displays, callouts",
        "color_theory": "Colour palette selection, accessibility (WCAG), and the 60-30-10 rule",
        "typography": "Font selection, pairing rules, type scales for slides and documents",
        "visual_libraries": "Reference catalogue of open-source chart libraries and design systems",
        "template_catalog": "16 named slide archetype recipes (iceberg, pinwheel, hexagonal, ladder, waffle, etc.) with structural coordinates, plus a queryable index of 771 curated templates",
        "professional_exhibit_design": "Institutional-grade exhibit design patterns: axis elimination, legend embedding, 3-color discipline, insight headlines, Marimekko/entity-flow/divergent-bar, and 11 density techniques",
        "design_md_styles": "27 curated design systems (Stripe, Vercel, Apple, Spotify, etc.) — color palettes, typography, style tags for matching company aesthetics",
    }

    lines = ["Available Design Playbooks:", ""]
    for name in PLAYBOOK_NAMES:
        desc = descriptions.get(name, "No description available")
        lines.append(f"  - {name}: {desc}")

    return "\n".join(lines)
