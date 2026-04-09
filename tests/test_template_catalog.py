"""Tests for the template catalog and the new template_catalog playbook.

These tests exercise the JSON-bundled metadata search, archetype lookup, and
playbook registration. No network or LLM access required.
"""

from __future__ import annotations

import pytest

from inkline.intelligence import (
    ARCHETYPES,
    find_templates,
    get_archetype_recipe,
    list_archetypes,
    load_manifest,
    suggest_archetype,
)
from inkline.intelligence.playbooks import (
    PLAYBOOK_NAMES,
    PLAYBOOK_REGISTRY,
    load_playbook,
    load_playbooks_for_task,
)


# ── Manifest loading ───────────────────────────────────────────────────────


def test_slidemodel_manifest_loads_and_has_results():
    m = load_manifest("slidemodel")
    assert "results" in m
    assert isinstance(m["results"], list)
    assert len(m["results"]) >= 300, f"expected >=300 templates, got {len(m['results'])}"
    sample = m["results"][0]
    # Required keys present on every template
    for key in ("title", "url", "palette", "tags", "slides"):
        assert key in sample, f"missing key '{key}' on first SlideModel entry"


def test_genspark_pro_manifest_loads():
    m = load_manifest("genspark_professional")
    assert "groups" in m
    assert len(m["groups"]) >= 100
    sample = m["groups"][0]
    assert "title" in sample and "uuid" in sample and "urls" in sample


def test_genspark_creative_manifest_loads():
    m = load_manifest("genspark_creative")
    assert "groups" in m
    assert len(m["groups"]) >= 100


def test_load_manifest_unknown_raises():
    with pytest.raises(ValueError):
        load_manifest("nope")


# ── find_templates search ──────────────────────────────────────────────────


def test_find_templates_by_tag():
    hits = find_templates(tags=["dashboard"], limit=20)
    # SlideModel infographics tag definitely contains dashboards
    assert len(hits) >= 5
    for h in hits:
        joined = " ".join(h.get("tags", [])).lower()
        assert "dashboard" in joined


def test_find_templates_by_color():
    # Pick a hex code that appears in many templates
    hits = find_templates(color="#FFFFFF", limit=10)
    assert len(hits) > 0
    for h in hits:
        assert "#FFFFFF" in [c.upper() for c in h["palette"]]


def test_find_templates_by_title():
    hits = find_templates(title_contains="dashboard", limit=10)
    assert len(hits) > 0
    for h in hits:
        assert "dashboard" in h["title"].lower()


def test_find_templates_combined_filters():
    hits = find_templates(
        tags=["data visualization"],
        color="#FFFFFF",
        limit=10,
    )
    # AND-combined: every hit satisfies both
    for h in hits:
        joined = " ".join(h.get("tags", [])).lower()
        assert "data visualization" in joined
        assert "#FFFFFF" in [c.upper() for c in h["palette"]]


def test_find_templates_genspark_title_search():
    hits = find_templates(
        title_contains="business",
        source="genspark_professional",
        limit=10,
    )
    assert len(hits) > 0
    for h in hits:
        assert "business" in h["title"].lower()


# ── Archetype API ──────────────────────────────────────────────────────────


def test_list_archetypes_has_16():
    names = list_archetypes()
    assert len(names) == 16
    # Spot-check a few that the playbook documents
    for expected in ("iceberg", "pyramid", "hexagonal_honeycomb", "dual_donut", "waffle"):
        assert expected in names


def test_get_archetype_recipe_iceberg():
    recipe = get_archetype_recipe("iceberg")
    assert recipe["n_items"] == 2
    assert "risk" in recipe["best_for"]
    assert recipe["needs_metaphor_image"] is True
    assert recipe["palette_rule"] == "single_hue_monochrome"


def test_get_archetype_recipe_unknown_raises():
    with pytest.raises(ValueError):
        get_archetype_recipe("not_a_real_archetype")


def test_suggest_archetype_by_intent():
    # "customer_journey" tag should map to the curved-arrow process flow
    suggestions = suggest_archetype(intent="customer_journey")
    assert "process_curved_arrows" in suggestions


def test_suggest_archetype_by_n_items_5_prefers_pyramid_or_pentagon():
    suggestions = suggest_archetype(n_items=5)
    # The closest n_items=5 archetypes should rank high
    top3 = suggestions[:3]
    # pyramid (5), ladder (5), iceberg (2) — first two should be present
    assert "pyramid" in top3 or "ladder" in top3


def test_archetypes_dict_immutable_per_call():
    # get_archetype_recipe returns a copy so callers can't pollute the registry
    r = get_archetype_recipe("iceberg")
    r["best_for"] = ["mutated"]
    assert get_archetype_recipe("iceberg")["best_for"] != ["mutated"]


# ── Playbook registration ─────────────────────────────────────────────────


def test_template_catalog_playbook_registered():
    assert "template_catalog" in PLAYBOOK_NAMES
    assert "template_catalog" in PLAYBOOK_REGISTRY


def test_template_catalog_playbook_loads():
    content = load_playbook("template_catalog")
    assert len(content) > 5000  # the playbook is substantial
    # Spot-check that the archetype names appear in the playbook text
    for token in ("Iceberg", "Pyramid", "Hexagonal", "Waffle", "archetype"):
        assert token in content, f"expected token '{token}' in playbook"


def test_slide_task_includes_template_catalog():
    pb = load_playbooks_for_task("slide")
    assert "template_catalog" in pb
    # Existing playbooks still loaded
    assert "slide_layouts" in pb
    assert "color_theory" in pb


def test_infographic_task_includes_template_catalog():
    pb = load_playbooks_for_task("infographic")
    assert "template_catalog" in pb
