"""Shared metadata-aware benchmark audit semantics for storyboard/archetype decks."""

from __future__ import annotations

from typing import Any

from inkline.intelligence.reference_schema import validate_benchmark_audit
from inkline.intelligence.storyboard import DEFAULT_AUDIT_SETTINGS


def _score_from_verdict(verdict: str) -> int:
    critique = verdict.upper()
    return 100 if critique == "PASS" else 75 if critique == "WARN" else 0


def _bool_status(required: bool, passed: bool, *, source: str, reason: str = "") -> dict[str, Any]:
    return {
        "status": "scored" if required else "not_evaluated",
        "required": required,
        "score": 100 if passed and required else 0 if required else None,
        "source": source if required else "not_applicable",
        "reason": reason,
    }


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
    proxy_score = _score_from_verdict(critique)
    storyboard = storyboard or {}
    source_reference_slide_ids = storyboard.get("source_reference_slide_ids") or []
    variant_id = str(storyboard.get("variant_id", "")).strip()
    builder_recipe_id = str(storyboard.get("builder_recipe_id", "")).strip()
    key_message = str(storyboard.get("key_message", "")).strip()

    hard_render = {
        "status": "scored",
        "required": True,
        "score": proxy_score,
        "source": "rendered_critique",
        "reason": "rendered slide critique",
    }
    archetype_compliance = _bool_status(
        archetype_declared,
        passed=archetype_declared and not fallback_used,
        source="storyboard_manifest",
        reason="archetype must compile without fallback and preserve variant metadata",
    )
    benchmark_alignment = _bool_status(
        reference_family_declared,
        passed=reference_family_declared and not hard_failed and bool(source_reference_slide_ids),
        source="reference_alignment_trace",
        reason="reference-aware slides must retain concrete benchmark slide ids",
    )
    message_delivery = _bool_status(
        bool(storyboard),
        passed=bool(storyboard) and not hard_failed and bool(key_message or storyboard.get("role")),
        source="storyboard_message_contract",
        reason="slides need a declared key message plus renderable structure",
    )
    if critique == "WARN":
        warning_count = sum(
            1 for meta in (archetype_compliance, benchmark_alignment, message_delivery) if meta["required"]
        )
    else:
        warning_count = 0
        for meta in (archetype_compliance, benchmark_alignment, message_delivery):
            if meta["required"] and meta["score"] == 0 and not hard_failed:
                warning_count += 1
    if hard_failed:
        verdict = "fail"
    elif warning_count > DEFAULT_AUDIT_SETTINGS["slide_warning_budget"]:
        verdict = "needs_human_signoff"
    elif fallback_used:
        verdict = "needs_human_signoff"
    elif warning_count:
        verdict = "pass_with_warnings"
    else:
        verdict = "pass"
    return {
        "slide_index": slide_index,
        "slide_id": str(storyboard.get("slide_id", "")),
        "verdict": verdict,
        "warning_count": warning_count,
        "dimensions": {
            "visual_quality": hard_render,
            "archetype_compliance": archetype_compliance,
            "reference_family_alignment": benchmark_alignment,
            "message_delivery": message_delivery,
        },
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

    slides = []
    for item in slide_results:
        dims = item["dimensions"]
        slides.append(
            {
                "slide_id": item.get("slide_id", ""),
                "slide_index": item["slide_index"],
                "hard_render": dims["visual_quality"],
                "archetype_compliance": dims["archetype_compliance"],
                "benchmark_alignment": dims["reference_family_alignment"],
                "message_delivery": dims["message_delivery"],
                "required_fix": "" if item["verdict"] == "pass" else item["verdict"],
                "verdict": item["verdict"],
            }
        )
    payload = validate_benchmark_audit(
        {
            "engineering_pass": deck_verdict in {"pass", "pass_with_warnings"},
            "design_pass": deck_verdict in {"pass", "pass_with_warnings"},
            "benchmark_alignment_pass": all(
                (not slide["benchmark_alignment"]["required"]) or slide["benchmark_alignment"]["score"] == 100
                for slide in slides
            ),
            "message_pass": all(
                (not slide["message_delivery"]["required"]) or slide["message_delivery"]["score"] == 100
                for slide in slides
            ),
            "ship_recommendation": deck_verdict,
            "slides": slides,
        }
    )
    payload.update(
        {
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
        }
    )
    return payload


__all__ = ["aggregate_deck_audit", "evaluate_slide_audit"]
