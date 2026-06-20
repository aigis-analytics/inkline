"""Shared metadata-aware audit semantics for storyboard/archetype decks."""

from __future__ import annotations

from typing import Any

from inkline.intelligence.storyboard import DEFAULT_AUDIT_SETTINGS


def evaluate_slide_audit(
    *,
    slide_index: int,
    storyboard: dict[str, Any] | None,
    critique_verdict: str,
    archetype_declared: bool,
    reference_family_declared: bool,
    fallback_used: bool = False,
) -> dict[str, Any]:
    critique = critique_verdict.upper()
    hard_failed = critique in {"FAIL", "INCOMPLETE"}
    proxy_score = 100 if critique == "PASS" else 75 if critique == "WARN" else 0
    dimensions: dict[str, dict[str, Any]] = {
        "visual_quality": {
            "status": "scored",
            "required": True,
            "score": proxy_score,
            "source": "rendered_critique",
        },
        "archetype_compliance": {
            "status": "scored" if archetype_declared else "not_evaluated",
            "required": archetype_declared,
            "score": proxy_score if archetype_declared else None,
            "source": "rendered_critique_proxy" if archetype_declared else "not_applicable",
        },
        "reference_family_alignment": {
            "status": "scored" if reference_family_declared else "not_evaluated",
            "required": reference_family_declared,
            "score": proxy_score if reference_family_declared else None,
            "source": "rendered_critique_proxy" if reference_family_declared else "not_applicable",
        },
        "message_delivery": {
            "status": "scored" if storyboard else "not_evaluated",
            "required": bool(storyboard),
            "score": proxy_score if storyboard else None,
            "source": "rendered_critique_proxy" if storyboard else "not_applicable",
        },
    }
    warning_count = (
        sum(1 for meta in dimensions.values() if meta["status"] == "scored")
        if critique == "WARN"
        else 0
    )
    if hard_failed:
        verdict = "fail"
    elif warning_count > DEFAULT_AUDIT_SETTINGS["slide_warning_budget"]:
        verdict = "needs_human_signoff"
    elif any(v["required"] and v["status"] == "not_evaluated" for v in dimensions.values()):
        verdict = "needs_human_signoff"
    elif fallback_used:
        verdict = "needs_human_signoff"
    elif warning_count:
        verdict = "pass_with_warnings"
    else:
        verdict = "pass"
    return {
        "slide_index": slide_index,
        "verdict": verdict,
        "warning_count": warning_count,
        "dimensions": dimensions,
        "hard_failed": hard_failed,
        "fallback_used": fallback_used,
    }


def aggregate_deck_audit(slide_results: list[dict[str, Any]]) -> dict[str, Any]:
    if any(item["verdict"] == "fail" for item in slide_results):
        deck_verdict = "fail"
    elif any(item["verdict"] == "needs_human_signoff" for item in slide_results):
        deck_verdict = "needs_human_signoff"
    else:
        warning_budget_used = sum(int(item.get("warning_count", 0)) for item in slide_results)
        if warning_budget_used > DEFAULT_AUDIT_SETTINGS["deck_warning_budget"]:
            deck_verdict = "needs_human_signoff"
        else:
            deck_verdict = "pass_with_warnings" if warning_budget_used > 0 else "pass"
    return {
        "schema_name": "deck_audit",
        "schema_version": 1,
        "deck_verdict": deck_verdict,
        "deck_required_fix_count": sum(1 for item in slide_results if item["verdict"] in {"fail", "needs_human_signoff"}),
        "slides_failed_hard_checks": [item["slide_index"] for item in slide_results if item["hard_failed"]],
        "slides_requiring_human_signoff": [item["slide_index"] for item in slide_results if item["verdict"] == "needs_human_signoff"],
        "dimensions_not_evaluated": [
            {
                "slide_index": item["slide_index"],
                "dimensions": [name for name, meta in item["dimensions"].items() if meta["status"] == "not_evaluated"],
            }
            for item in slide_results
            if any(meta["status"] == "not_evaluated" for meta in item["dimensions"].values())
        ],
        "warning_budget_used": sum(int(item.get("warning_count", 0)) for item in slide_results),
        "slides": slide_results,
    }


__all__ = ["aggregate_deck_audit", "evaluate_slide_audit"]
