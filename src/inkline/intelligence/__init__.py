"""Inkline Intelligence Layer — smart document and presentation design.

Provides rules-based (and optionally LLM-advised) layout, chart type,
and visual hierarchy decisions. Any client application gets intelligent
output without implementing its own presentation logic.

Usage::

    from inkline.intelligence import DesignAdvisor

    advisor = DesignAdvisor(brand="minimal", template="consulting")

    # Smart slides from structured data
    slides = advisor.design_deck(
        title="Q4 Strategy Review",
        sections=[
            {"type": "executive_summary", "metrics": {...}, "narrative": "..."},
            {"type": "financial_overview", "table_data": {...}},
        ],
    )

    # Smart document from markdown
    doc_source = advisor.design_document(
        markdown="# Due Diligence Report\\n...",
        exhibits=[{"type": "table", "data": {...}}],
    )
"""

from inkline.intelligence.design_advisor import DesignAdvisor, LLMCaller
from inkline.intelligence.claude_code import (
    build_claude_code_caller,
    claude_code_available,
    ensure_bridge_running,
    ClaudeCodeNotInstalled,
)
from inkline.intelligence.overflow_audit import (
    audit_deck,
    audit_image,
    audit_slide,
    format_report,
    AuditWarning,
)
from inkline.intelligence.template_catalog import (
    ARCHETYPES,
    find_templates,
    get_archetype_recipe,
    list_archetypes,
    load_manifest,
    suggest_archetype,
)
from inkline.intelligence.archon import Archon, Issue, PhaseResult
from inkline.intelligence.anti_patterns import check_anti_patterns, AntiPatternResult
from inkline.intelligence.quality_scorer import score_deck, QualityScore
from inkline.intelligence.polish import polish_deck, PolishResult
from inkline.intelligence.design_brief import generate_brief, DesignBrief
from inkline.intelligence.vishwakarma import (
    VISHWAKARMA_SYSTEM_PREAMBLE,
    VISHWAKARMA_AUDIT_CRITERIA,
    VISUAL_HIERARCHY,
    BRIDGE_FIRST,
    AUDIT_MANDATORY,
    ARCHON_OVERSIGHT,
)

__all__ = [
    "DesignAdvisor",
    "LLMCaller",
    # Claude Code subscription bridge
    "build_claude_code_caller",
    "claude_code_available",
    "ensure_bridge_running",
    "ClaudeCodeNotInstalled",
    # Audit
    "audit_deck",
    "audit_image",
    "audit_slide",
    "format_report",
    "AuditWarning",
    # Template catalog
    "ARCHETYPES",
    "find_templates",
    "get_archetype_recipe",
    "list_archetypes",
    "load_manifest",
    "suggest_archetype",
    # Archon oversight
    "Archon",
    "Issue",
    "PhaseResult",
    # Vishwakarma philosophy
    "VISHWAKARMA_SYSTEM_PREAMBLE",
    "VISHWAKARMA_AUDIT_CRITERIA",
    "VISUAL_HIERARCHY",
    "BRIDGE_FIRST",
    "AUDIT_MANDATORY",
    "ARCHON_OVERSIGHT",
    # Impeccable design intelligence
    "check_anti_patterns",
    "AntiPatternResult",
    "score_deck",
    "QualityScore",
    "polish_deck",
    "PolishResult",
    "generate_brief",
    "DesignBrief",
]
