"""Plan auditor — rejects deck plans that violate VFEP constraints.

**Used in Draft Mode only.** The execute-mode path (inkline render) does not
invoke the VFEP plan auditor. This module runs inside the 4-phase Archon
pipeline triggered by /prompt (Draft Mode). In execute-mode, spec validation
is done at parse time by inkline.authoring.image_strategy and the preprocessor.

Called between _plan_deck_llm and _review_plan_llm in _design_deck_llm.
Returns a PlanAuditResult; callers retry planning when the audit fails.

VFEP constraints enforced:
  - ≤ 30 % of content slides may be T5 text layouts (split/content/table)
  - No 3+ consecutive slides of the same slide_type
  - Every T5 slide must carry a non-empty "vfep_justification" in its notes
    (enforced at planning time; rendered decks tolerate absence gracefully)
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Slide types classified as T5 (last-resort text fallbacks)
_T5_TYPES: frozenset[str] = frozenset({"split", "content", "table"})

# Structural slides excluded from the content-slide count and ratio
_STRUCTURAL: frozenset[str] = frozenset({"title", "closing", "section_divider"})


@dataclass
class PlanAuditResult:
    """Result of auditing a deck plan against VFEP constraints."""
    passed: bool
    t5_count: int = 0
    content_count: int = 0          # Non-structural slides
    t5_ratio: float = 0.0
    consecutive_violations: list[str] = field(default_factory=list)
    missing_justifications: list[int] = field(default_factory=list)  # 1-based slide indices
    feedback: str = ""


def audit_plan(plan: list[dict]) -> PlanAuditResult:
    """Audit a plan list for VFEP compliance.

    Parameters
    ----------
    plan : list[dict]
        Plan entries, each with at least a ``"slide_type"`` key and
        optionally a ``"notes"`` key.

    Returns
    -------
    PlanAuditResult
        ``.passed`` is True when all constraints are satisfied.
    """
    content_slides = [
        (i, entry) for i, entry in enumerate(plan)
        if entry.get("slide_type", "") not in _STRUCTURAL
    ]
    content_count = len(content_slides)
    t5_slides = [
        (i, entry) for i, entry in content_slides
        if entry.get("slide_type", "") in _T5_TYPES
    ]
    t5_count = len(t5_slides)
    t5_ratio = t5_count / content_count if content_count else 0.0

    # Check 1: T5 ratio ≤ 30 %
    ratio_ok = t5_ratio <= 0.30

    # Check 2: No 3+ consecutive identical slide_types
    consecutive_violations: list[str] = []
    types = [e.get("slide_type", "") for e in plan]
    for j in range(len(types) - 2):
        if types[j] == types[j + 1] == types[j + 2]:
            label = f"slides {j+1}–{j+3}: {types[j]}"
            if label not in consecutive_violations:
                consecutive_violations.append(label)

    # Check 3: T5 slides should carry vfep_justification in notes
    missing_justifications: list[int] = []
    for i, entry in t5_slides:
        notes = entry.get("notes", "") or ""
        if "vfep_justification" not in notes.lower() and "vfep" not in notes.lower():
            missing_justifications.append(i + 1)  # 1-based

    passed = ratio_ok and not consecutive_violations

    # Build feedback string for retry prompt injection
    lines: list[str] = []
    if not ratio_ok:
        lines.append(
            f"VFEP VIOLATION: {t5_count}/{content_count} content slides "
            f"({t5_ratio:.0%}) are T5 text layouts (split/content/table). "
            f"Limit is 30 %. Upgrade at least "
            f"{t5_count - int(content_count * 0.30)} of them to visual layouts."
        )
    if consecutive_violations:
        for v in consecutive_violations:
            lines.append(
                f"CONSECUTIVE VIOLATION: {v} — break the run with a different "
                f"slide type (use a higher-tier visual alternative)."
            )
    if missing_justifications:
        indices = ", ".join(str(x) for x in missing_justifications)
        lines.append(
            f"MISSING VFEP JUSTIFICATION: slides {indices} are T5 but their "
            f"notes field does not explain why visual layouts were exhausted. "
            f"Add a brief vfep_justification note to each."
        )

    return PlanAuditResult(
        passed=passed,
        t5_count=t5_count,
        content_count=content_count,
        t5_ratio=t5_ratio,
        consecutive_violations=consecutive_violations,
        missing_justifications=missing_justifications,
        feedback="\n".join(lines),
    )
