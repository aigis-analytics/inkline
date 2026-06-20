from __future__ import annotations

from inkline.intelligence.audit_storyboard import aggregate_deck_audit, evaluate_slide_audit
from inkline.intelligence.full_slide_archetypes import (
    compile_slide_manifest,
    materialize_compiled_slide_spec,
    retrieve_full_slide_candidates,
)
from inkline.intelligence.storyboard import resolve_storyboard_spec
import pytest


def test_resolve_storyboard_spec_applies_slide_ids_and_metadata():
    spec = {
        "title": "Deck",
        "audience": "IC",
        "storyboard": {
            "deck": {"objective": "Win approval", "reference_family": "family_v1"},
            "slides": {
                "1": {"role": "cover", "key_message": "Enter Angola"},
            },
        },
        "slides": [
            {
                "slide_type": "title",
                "data": {"company": "7GI", "tagline": "Angola"},
                "_archetype": "cover_hero_photo_left_text_block",
            },
            {
                "slide_type": "team_grid",
                "data": {
                    "title": "Boots on the Ground",
                    "members": [{"name": "A", "role": "B", "bio": "C"}],
                },
            },
        ],
    }

    from inkline.intelligence import storyboard as storyboard_module

    original = storyboard_module.load_reference_family
    storyboard_module.load_reference_family = lambda family_id: {"reference_family_id": family_id}
    try:
        resolved = resolve_storyboard_spec(spec, source_name="fixture.json")
    finally:
        storyboard_module.load_reference_family = original
    assert resolved["storyboard"]["schema_version"] == 1
    assert resolved["slides"][0]["slide_id"].startswith("s01_")
    assert resolved["slides"][0]["storyboard"]["role"] == "cover"
    assert resolved["slides"][0]["storyboard"]["archetype"] == "cover_hero_photo_left_text_block"
    assert resolved["slides"][1]["storyboard"]["role"] == "team"
    assert resolved["slides"][1]["compiled_manifest"]["schema_name"] == "compiled_slide_manifest"
    assert resolved["_authoring_trace"]["schema_name"] == "authoring_trace"
    assert len(resolved["_authoring_trace"]["slides"]) == 2


def test_retrieve_candidates_prefers_matching_role_and_schema():
    slide = {
        "slide_type": "team_grid",
        "data": {"members": [{"name": "A"}]},
    }
    candidates = retrieve_full_slide_candidates(role="team", slide_spec=slide)
    assert candidates
    assert candidates[0]["id"] == "executive_bio_cards_centered"


def test_retrieve_candidates_applies_reference_family_bonus_for_matching_role():
    slide = {
        "slide_type": "team_grid",
        "data": {"members": [{"name": "A"}]},
    }
    base = retrieve_full_slide_candidates(role="team", slide_spec=slide, reference_family="")
    with_family = retrieve_full_slide_candidates(
        role="team",
        slide_spec=slide,
        reference_family="family_v1",
    )
    assert base and with_family
    assert with_family[0]["id"] == "executive_bio_cards_centered"
    assert with_family[0]["score"] > base[0]["score"]
    assert with_family[0]["reference_family_bonus_applied"] is True


def test_compile_manifest_records_renderer_native_payload():
    slide = {
        "slide_type": "content",
        "data": {"members": [{"name": "A"}], "image_path": "headshot.png"},
    }
    manifest = compile_slide_manifest(
        slide,
        slide_id="s02_team",
        resolved_role="team",
        archetype_id="executive_bio_cards_centered",
    )
    assert manifest["render_payload"]["slide_type"] == "team_grid"
    assert manifest["compile_target"]["layout_id"] == "team_grid"
    assert manifest["pptx_editability_exceptions"] == ["intentional_raster_asset"]
    assert manifest["requested_slide_type"] == "content"


def test_materialized_compiled_manifest_overrides_slide_type():
    slide = {
        "slide_type": "content",
        "data": {"members": [{"name": "A"}]},
        "compiled_manifest": compile_slide_manifest(
            {"slide_type": "content", "data": {"members": [{"name": "A"}]}},
            slide_id="s02_team",
            resolved_role="team",
            archetype_id="executive_bio_cards_centered",
        ),
    }
    materialized = materialize_compiled_slide_spec(slide)
    assert materialized["slide_type"] == "team_grid"


def test_resolve_storyboard_spec_respects_plain_fixture_overrides():
    spec = {
        "title": "Deck",
        "slides": [
            {
                "slide_type": "content",
                "role": "team",
                "archetype": "executive_bio_cards_centered",
                "key_message": "Local access matters",
                "reference_family": "family_v1",
                "data": {"members": [{"name": "A", "role": "B"}]},
            }
        ],
    }
    from inkline.intelligence import storyboard as storyboard_module

    original = storyboard_module.load_reference_family
    storyboard_module.load_reference_family = lambda family_id: {"reference_family_id": family_id}
    try:
        resolved = resolve_storyboard_spec(spec, source_name="fixture.json")
    finally:
        storyboard_module.load_reference_family = original
    slide = resolved["slides"][0]
    assert slide["storyboard"]["role"] == "team"
    assert slide["storyboard"]["archetype"] == "executive_bio_cards_centered"
    assert slide["storyboard"]["key_message"] == "Local access matters"
    assert slide["storyboard"]["reference_family"] == "family_v1"
    assert slide["slide_type"] == "team_grid"
    assert resolved["storyboard"]["slides"][0]["reference_family"] == "family_v1"


def test_resolve_storyboard_spec_honors_slide_id_keyed_storyboard_entry():
    spec = {
        "title": "Deck",
        "storyboard": {
            "slides": {
                "s01_cover": {
                    "role": "cover",
                    "archetype": "cover_hero_photo_left_text_block",
                    "key_message": "Enter Angola",
                }
            }
        },
        "slides": [
            {
                "slide_id": "s01_cover",
                "slide_type": "content",
                "data": {"company": "7GI", "tagline": "Angola"},
            }
        ],
    }
    resolved = resolve_storyboard_spec(spec, source_name="fixture.json")
    slide = resolved["slides"][0]
    assert slide["storyboard"]["role"] == "cover"
    assert slide["storyboard"]["archetype"] == "cover_hero_photo_left_text_block"
    assert slide["storyboard"]["key_message"] == "Enter Angola"
    assert slide["slide_type"] == "title"
    assert resolved["storyboard"]["slides"][0]["reference_family"] == ""


def test_content_slide_preserves_authored_layout_when_no_archetype_match():
    spec = {
        "title": "Deck",
        "slides": [
            {
                "slide_type": "content",
                "data": {"title": "Overview", "items": ["A", "B"]},
            }
        ],
    }
    resolved = resolve_storyboard_spec(spec, source_name="fixture.json")
    slide = resolved["slides"][0]
    assert slide["storyboard"]["role"] == "content"
    assert slide["storyboard"]["archetype"] == ""
    assert slide["slide_type"] == "content"


def test_execute_mode_resolver_does_not_auto_select_archetypes():
    spec = {
        "title": "Deck",
        "slides": [
            {
                "slide_type": "team_grid",
                "data": {"title": "Team", "members": [{"name": "A", "role": "B"}]},
            }
        ],
    }
    resolved = resolve_storyboard_spec(spec, source_name="fixture.json", allow_inference=False)
    slide = resolved["slides"][0]
    assert slide["storyboard"]["archetype"] == ""
    assert slide["slide_type"] == "team_grid"
    assert resolved["storyboard"]["slides"][0]["fallback_used"] is False


def test_execute_mode_explicit_archetype_is_not_marked_as_fallback():
    spec = {
        "title": "Deck",
        "slides": [
            {
                "slide_type": "content",
                "role": "team",
                "archetype": "executive_bio_cards_centered",
                "data": {"members": [{"name": "A", "role": "B"}]},
            }
        ],
    }
    resolved = resolve_storyboard_spec(spec, source_name="fixture.json", allow_inference=False)
    assert resolved["storyboard"]["slides"][0]["fallback_used"] is False


def test_audit_aggregation_respects_fail_and_human_signoff():
    slide_1 = evaluate_slide_audit(
        slide_index=1,
        storyboard={"role": "cover"},
        critique_verdict="PASS",
        archetype_declared=True,
        reference_family_declared=True,
    )
    slide_2 = evaluate_slide_audit(
        slide_index=2,
        storyboard=None,
        critique_verdict="INCOMPLETE",
        archetype_declared=False,
        reference_family_declared=False,
    )
    deck = aggregate_deck_audit([slide_1, slide_2])
    assert deck["deck_verdict"] == "fail"
    assert deck["slides_failed_hard_checks"] == [2]


def test_native_with_exceptions_is_not_treated_as_fallback():
    slide = evaluate_slide_audit(
        slide_index=1,
        storyboard={"role": "market_map"},
        critique_verdict="PASS",
        archetype_declared=True,
        reference_family_declared=False,
        fallback_used=False,
    )
    assert slide["verdict"] == "pass"


def test_missing_required_fields_for_explicit_archetype_fail_fast():
    spec = {
        "title": "Deck",
        "slides": [
            {
                "slide_type": "content",
                "archetype": "executive_bio_cards_centered",
                "data": {"title": "Overview"},
            }
        ],
    }
    with pytest.raises(ValueError):
        resolve_storyboard_spec(spec, source_name="fixture.json")


def test_unknown_explicit_archetype_override_fails_fast():
    spec = {
        "title": "Deck",
        "slides": [
            {
                "slide_type": "content",
                "archetype": "not_a_real_archetype",
                "data": {"title": "Overview"},
            }
        ],
    }
    with pytest.raises(ValueError, match="Unknown archetype"):
        resolve_storyboard_spec(spec, source_name="fixture.json")


def test_storyboarded_slide_can_reach_clean_pass():
    slide = evaluate_slide_audit(
        slide_index=1,
        storyboard={"role": "cover", "key_message": "Enter Angola"},
        critique_verdict="PASS",
        archetype_declared=True,
        reference_family_declared=True,
        fallback_used=False,
    )
    assert slide["verdict"] == "pass"
    assert slide["dimensions"]["message_delivery"]["status"] == "scored"
    assert slide["dimensions"]["reference_family_alignment"]["status"] == "scored"


def test_invalid_explicit_role_fails_fast():
    spec = {
        "title": "Deck",
        "slides": [
            {
                "slide_type": "content",
                "role": "teem",
                "data": {"title": "Overview"},
            }
        ],
    }
    with pytest.raises(ValueError, match="Unknown slide role"):
        resolve_storyboard_spec(spec, source_name="fixture.json")


def test_warn_slide_exceeding_warning_budget_requires_human_signoff():
    slide = evaluate_slide_audit(
        slide_index=1,
        storyboard={"role": "cover", "key_message": "Enter Angola"},
        critique_verdict="WARN",
        archetype_declared=True,
        reference_family_declared=True,
        fallback_used=False,
    )
    assert slide["warning_count"] > 2
    assert slide["verdict"] == "needs_human_signoff"


def test_incompatible_role_and_archetype_fail_fast():
    spec = {
        "title": "Deck",
        "slides": [
            {
                "slide_type": "content",
                "role": "cover",
                "archetype": "executive_bio_cards_centered",
                "data": {"members": [{"name": "A", "role": "B"}]},
            }
        ],
    }
    with pytest.raises(ValueError, match="incompatible with resolved role"):
        resolve_storyboard_spec(spec, source_name="fixture.json")


def test_unknown_reference_family_fails_fast():
    spec = {
        "title": "Deck",
        "reference_family": "missing_family",
        "slides": [
            {
                "slide_type": "content",
                "data": {"title": "Overview"},
            }
        ],
    }
    with pytest.raises(ValueError, match="Unknown reference family"):
        resolve_storyboard_spec(spec, source_name="fixture.json")
