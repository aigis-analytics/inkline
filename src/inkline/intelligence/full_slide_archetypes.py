"""Full-slide archetype registry, scoring, and compiled-manifest helpers."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from inkline.intelligence.reference_schema import (
    COMPILED_SLIDE_SCHEMA_NAME,
    COMPILED_SLIDE_SCHEMA_VERSION,
    FULL_SLIDE_ARCHETYPE_SCHEMA_NAME,
    FULL_SLIDE_ARCHETYPE_SCHEMA_VERSION,
    validate_compiled_slide_manifest,
    validate_full_slide_archetype,
)


@dataclass(frozen=True)
class CompileVariant:
    variant_id: str
    layout_id: str
    template_id: str | None = None
    builder_recipe_id: str = ""
    benchmark_tokens: dict[str, Any] | None = None
    editable_pptx_supported: bool = True
    fallback_policy: str = "fail_fast"

    def to_manifest(self, *, kind: str = "layout") -> dict[str, Any]:
        return {
            "variant_id": self.variant_id,
            "compile_target": {
                "kind": kind,
                "layout_id": self.layout_id,
                "template_id": self.template_id,
            },
            "builder_recipe_id": self.builder_recipe_id,
            "benchmark_tokens": deepcopy(self.benchmark_tokens or {}),
            "editable_pptx_supported": self.editable_pptx_supported,
            "fallback_policy": self.fallback_policy,
        }


@dataclass(frozen=True)
class FullSlideArchetype:
    id: str
    functional_roles: tuple[str, ...]
    deck_types: tuple[str, ...]
    content_schema_required: tuple[str, ...]
    content_schema_optional: tuple[str, ...]
    visual_intent: dict[str, str]
    compile_target_kind: str
    compile_layout_id: str
    compile_template_id: str | None
    compile_variants: tuple[CompileVariant, ...]
    density_class: str
    allowed_primitives: tuple[str, ...]
    benchmark_refs: tuple[dict[str, str], ...]
    anti_patterns: tuple[str, ...]
    audit_checks: tuple[str, ...]
    pptx_editability_policy: str = "native_required"

    def to_manifest(self) -> dict[str, Any]:
        return validate_full_slide_archetype(
            {
                "schema_name": FULL_SLIDE_ARCHETYPE_SCHEMA_NAME,
                "schema_version": FULL_SLIDE_ARCHETYPE_SCHEMA_VERSION,
                "id": self.id,
                "functional_roles": list(self.functional_roles),
                "deck_types": list(self.deck_types),
                "content_schema": {
                    "required": list(self.content_schema_required),
                    "optional": list(self.content_schema_optional),
                },
                "visual_intent": deepcopy(self.visual_intent),
                "compile_targets": {
                    "kind": self.compile_target_kind,
                    "layout_id": self.compile_layout_id,
                    "template_id": self.compile_template_id,
                },
                "compile_variants": [item.to_manifest(kind=self.compile_target_kind) for item in self.compile_variants],
                "density_class": self.density_class,
                "allowed_primitives": list(self.allowed_primitives),
                "benchmark_refs": [dict(item) for item in self.benchmark_refs],
                "pptx_editability_policy": self.pptx_editability_policy,
                "anti_patterns": list(self.anti_patterns),
                "audit_checks": list(self.audit_checks),
            }
        )


def _variant(
    variant_id: str,
    layout_id: str,
    *,
    builder_recipe_id: str = "",
    benchmark_tokens: dict[str, Any] | None = None,
    editable_pptx_supported: bool = True,
    fallback_policy: str = "fail_fast",
) -> CompileVariant:
    return CompileVariant(
        variant_id=variant_id,
        layout_id=layout_id,
        builder_recipe_id=builder_recipe_id,
        benchmark_tokens=benchmark_tokens,
        editable_pptx_supported=editable_pptx_supported,
        fallback_policy=fallback_policy,
    )


def _archetype(
    archetype_id: str,
    *,
    roles: tuple[str, ...],
    required: tuple[str, ...],
    optional: tuple[str, ...] = (),
    layout_id: str,
    visual_intent: dict[str, str],
    density_class: str,
    variants: tuple[CompileVariant, ...] = (),
    allowed_primitives: tuple[str, ...] = ("title", "cards", "table", "image", "timeline"),
    deck_types: tuple[str, ...] = ("investor", "consulting", "board"),
    anti_patterns: tuple[str, ...] = (),
    audit_checks: tuple[str, ...] = (),
    benchmark_refs: tuple[dict[str, str], ...] = (),
    pptx_editability_policy: str = "native_required",
) -> FullSlideArchetype:
    default_variants = variants or (_variant("default", layout_id),)
    return FullSlideArchetype(
        id=archetype_id,
        functional_roles=roles,
        deck_types=deck_types,
        content_schema_required=required,
        content_schema_optional=optional,
        visual_intent=visual_intent,
        compile_target_kind="layout",
        compile_layout_id=layout_id,
        compile_template_id=None,
        compile_variants=default_variants,
        density_class=density_class,
        allowed_primitives=allowed_primitives,
        benchmark_refs=benchmark_refs,
        anti_patterns=anti_patterns,
        audit_checks=audit_checks,
        pptx_editability_policy=pptx_editability_policy,
    )


_ARCHETYPES: dict[str, FullSlideArchetype] = {
    "cover_hero_photo_left_text_block": _archetype(
        "cover_hero_photo_left_text_block",
        roles=("cover",),
        required=("company",),
        optional=("tagline", "subtitle", "date", "background_image"),
        layout_id="title",
        density_class="low",
        visual_intent={"hero": "brand_title_block", "supporting": "image", "tone": "institutional_confident"},
        variants=(
            _variant("title_block", "title", builder_recipe_id="cover_title_block"),
            _variant("editorial_bleed", "title", builder_recipe_id="cover_editorial_bleed", benchmark_tokens={"hero_occupancy": "high"}),
        ),
        anti_patterns=("plain_title_without_hero", "small_cover_title"),
        audit_checks=("hero presence", "large title block"),
        benchmark_refs=({"ref_family": "ccc_angola_focus_v1"},),
    ),
    "cover_editorial_full_bleed": _archetype(
        "cover_editorial_full_bleed",
        roles=("cover",),
        required=("company",),
        optional=("tagline", "subtitle", "date", "background_image"),
        layout_id="title",
        density_class="low",
        visual_intent={"hero": "full_bleed_image", "supporting": "condensed_title", "tone": "editorial_confident"},
        variants=(
            _variant("full_bleed", "title", builder_recipe_id="cover_editorial_bleed"),
        ),
        allowed_primitives=("title", "hero_image", "logo"),
        anti_patterns=("floating_small_text",),
        audit_checks=("image dominance", "tight title hierarchy"),
    ),
    "divider_statement_band": _archetype(
        "divider_statement_band",
        roles=("divider", "section_divider"),
        required=("title",),
        optional=("subtitle",),
        layout_id="title",
        density_class="low",
        visual_intent={"hero": "statement_band", "supporting": "subtle_chrome", "tone": "section_break"},
        variants=(
            _variant("band", "title", builder_recipe_id="divider_statement_band"),
        ),
    ),
    "thesis_three_pillar_cards": _archetype(
        "thesis_three_pillar_cards",
        roles=("thesis", "proposition"),
        required=("cards",),
        optional=("section", "footnote"),
        layout_id="three_card",
        density_class="medium",
        visual_intent={"hero": "three pillars", "supporting": "short evidence", "tone": "strategic"},
        variants=(
            _variant("pillars", "three_card", builder_recipe_id="pillar_cards"),
            _variant("raised_cards", "three_card", builder_recipe_id="raised_info_cards"),
        ),
        anti_patterns=("equal_weight_bullet_blocks",),
        audit_checks=("three cards", "message-led titles"),
    ),
    "thesis_numbered_value_rail": _archetype(
        "thesis_numbered_value_rail",
        roles=("thesis", "proposition", "access_case"),
        required=("steps",),
        optional=("footnote",),
        layout_id="process_flow",
        density_class="medium",
        visual_intent={"hero": "numbered rail", "supporting": "short proofs", "tone": "assertive"},
        variants=(
            _variant("horizontal_rail", "process_flow", builder_recipe_id="numbered_value_rail"),
        ),
        anti_patterns=("plain_bullet_list",),
        audit_checks=("step numbers", "left-to-right message flow"),
    ),
    "proposition_two_zone_argument": _archetype(
        "proposition_two_zone_argument",
        roles=("proposition", "why_now", "investment_case"),
        required=("left_items", "right_items"),
        optional=("left_title", "right_title"),
        layout_id="split",
        density_class="medium",
        visual_intent={"hero": "dual_zone_argument", "supporting": "contrasting evidence", "tone": "commercial"},
        variants=(
            _variant("split_argument", "split", builder_recipe_id="two_zone_argument"),
        ),
    ),
    "thesis_zigzag_steps": _archetype(
        "thesis_zigzag_steps",
        roles=("process", "thesis", "entry_plan"),
        required=("steps",),
        layout_id="four_card",
        density_class="medium",
        visual_intent={"hero": "sequenced_zigzag_cards", "supporting": "micro_explanations", "tone": "dynamic"},
        variants=(
            _variant("zigzag", "four_card", builder_recipe_id="zigzag_steps"),
        ),
    ),
    "executive_bio_cards_centered": _archetype(
        "executive_bio_cards_centered",
        roles=("team", "people"),
        required=("members",),
        optional=("subheadline", "footer_note"),
        layout_id="team_grid",
        density_class="medium",
        visual_intent={"hero": "centered portraits", "supporting": "name_role", "tone": "institutional_human"},
        variants=(
            _variant("centered_cards", "team_grid", builder_recipe_id="people_headshot_cards"),
            _variant("circle_portraits", "team_grid", builder_recipe_id="people_circle_portraits"),
        ),
        allowed_primitives=("headshots", "bios", "badges", "cards"),
        anti_patterns=("generic_staff_grid", "small_headshots"),
        audit_checks=("portrait dominance", "name hierarchy", "consistent card sizing"),
        benchmark_refs=({"ref_family": "ccc_angola_focus_v1"},),
    ),
    "key_people_headshot_band": _archetype(
        "key_people_headshot_band",
        roles=("key_people", "people", "team"),
        required=("members",),
        optional=("subheadline",),
        layout_id="team_grid",
        density_class="medium",
        visual_intent={"hero": "headshot_band", "supporting": "tight bios", "tone": "senior_access"},
        variants=(
            _variant("band", "team_grid", builder_recipe_id="people_headshot_band"),
        ),
        allowed_primitives=("headshots", "bios", "cards"),
    ),
    "boots_on_ground_access_strip": _archetype(
        "boots_on_ground_access_strip",
        roles=("team", "network", "access"),
        required=("members",),
        optional=("footer_note",),
        layout_id="team_grid",
        density_class="medium",
        visual_intent={"hero": "access_profiles", "supporting": "institutional_links", "tone": "boots_on_ground"},
        variants=(
            _variant("access_strip", "team_grid", builder_recipe_id="boots_on_ground_strip"),
        ),
    ),
    "network_dual_column_profiles": _archetype(
        "network_dual_column_profiles",
        roles=("network", "people", "stakeholders"),
        required=("left_items", "right_items"),
        optional=("left_title", "right_title"),
        layout_id="split",
        density_class="medium",
        visual_intent={"hero": "dual_column_profiles", "supporting": "network nodes", "tone": "relational"},
        variants=(
            _variant("profiles_split", "split", builder_recipe_id="network_profiles_split"),
        ),
    ),
    "banker_vertical_process_spine": _archetype(
        "banker_vertical_process_spine",
        roles=("timeline", "process", "execution_plan"),
        required=("milestones",),
        optional=("footnote",),
        layout_id="timeline",
        density_class="medium",
        visual_intent={"hero": "vertical spine", "supporting": "milestone cards", "tone": "transactional"},
        variants=(
            _variant("vertical_spine", "timeline", builder_recipe_id="timeline_vertical_spine"),
            _variant("milestone_cards", "timeline", builder_recipe_id="timeline_milestone_cards"),
        ),
        anti_patterns=("text_wall_process_slide",),
        audit_checks=("milestone clarity", "chronological rhythm"),
        benchmark_refs=({"ref_family": "ccc_angola_focus_v1"},),
    ),
    "banker_horizontal_process_phases": _archetype(
        "banker_horizontal_process_phases",
        roles=("timeline", "process"),
        required=("milestones",),
        layout_id="timeline",
        density_class="medium",
        visual_intent={"hero": "phase_blocks", "supporting": "gated checkpoints", "tone": "banking"},
        variants=(
            _variant("phase_row", "timeline", builder_recipe_id="timeline_phase_row"),
        ),
    ),
    "roadshow_three_day_programme": _archetype(
        "roadshow_three_day_programme",
        roles=("roadshow", "timeline", "programme"),
        required=("milestones",),
        optional=("footnote",),
        layout_id="timeline",
        density_class="medium",
        visual_intent={"hero": "3_day_programme", "supporting": "meeting tracks", "tone": "orchestrated"},
        variants=(
            _variant("three_day", "timeline", builder_recipe_id="roadshow_three_day"),
        ),
    ),
    "execution_workstream_lanes": _archetype(
        "execution_workstream_lanes",
        roles=("execution_plan", "workstreams", "process"),
        required=("steps",),
        layout_id="process_flow",
        density_class="medium",
        visual_intent={"hero": "lane_workstreams", "supporting": "activity stacks", "tone": "operational"},
        variants=(
            _variant("lane_stack", "process_flow", builder_recipe_id="workstream_lanes"),
        ),
    ),
    "firepower_two_zone_summary": _archetype(
        "firepower_two_zone_summary",
        roles=("economics", "capital", "size_of_prize"),
        required=("stats",),
        optional=("bullets", "footnote"),
        layout_id="kpi_strip",
        density_class="medium",
        visual_intent={"hero": "two zone", "supporting": "support bullets", "tone": "commercial"},
        variants=(
            _variant("two_zone", "kpi_strip", builder_recipe_id="economics_two_zone"),
        ),
        anti_patterns=("dense_numbers_without_hierarchy",),
        audit_checks=("hero metrics", "clear two-zone split"),
    ),
    "capital_recycling_growth_bridge": _archetype(
        "capital_recycling_growth_bridge",
        roles=("economics", "capital", "build_case"),
        required=("stats",),
        optional=("bullets",),
        layout_id="dashboard",
        density_class="medium",
        visual_intent={"hero": "growth_bridge", "supporting": "capital recycling logic", "tone": "financial"},
        variants=(
            _variant("bridge", "dashboard", builder_recipe_id="capital_growth_bridge"),
        ),
    ),
    "reserves_value_bar_bridge": _archetype(
        "reserves_value_bar_bridge",
        roles=("economics", "valuation", "build_case"),
        required=("stats",),
        layout_id="dashboard",
        density_class="medium",
        visual_intent={"hero": "reserve_value_bars", "supporting": "value progression", "tone": "valuation"},
        variants=(
            _variant("bar_bridge", "dashboard", builder_recipe_id="reserves_bar_bridge"),
        ),
    ),
    "phased_acquisition_funding_map": _archetype(
        "phased_acquisition_funding_map",
        roles=("economics", "funding", "size_of_prize"),
        required=("steps",),
        optional=("stats",),
        layout_id="split",
        density_class="medium",
        visual_intent={"hero": "funding_map", "supporting": "phased deployment", "tone": "programmatic"},
        variants=(
            _variant("funding_map", "split", builder_recipe_id="phased_funding_map"),
        ),
    ),
    "opportunity_bucket_cards": _archetype(
        "opportunity_bucket_cards",
        roles=("opportunity_set", "opportunities", "market_map"),
        required=("cards",),
        optional=("footnote",),
        layout_id="four_card",
        density_class="medium",
        visual_intent={"hero": "bucket_cards", "supporting": "named examples", "tone": "market_scanning"},
        variants=(
            _variant("bucket_grid", "four_card", builder_recipe_id="opportunity_bucket_grid"),
        ),
    ),
    "live_pipeline_ranked_table": _archetype(
        "live_pipeline_ranked_table",
        roles=("pipeline", "appendix_ranked_table", "live_deals"),
        required=("rows",),
        optional=("headers", "footnote"),
        layout_id="table",
        density_class="high",
        visual_intent={"hero": "ranked_pipeline", "supporting": "deal detail", "tone": "institutional_dense"},
        variants=(
            _variant("ranked_table", "table", builder_recipe_id="pipeline_ranked_table"),
            _variant("dense_table", "table", builder_recipe_id="dense_appendix_table"),
        ),
        allowed_primitives=("table", "badges", "legend"),
        anti_patterns=("unstyled_data_dump",),
        audit_checks=("header hierarchy", "row consistency"),
    ),
    "market_map_reference_exhibit": _archetype(
        "market_map_reference_exhibit",
        roles=("market_map", "map", "asset_overview"),
        required=("image_path",),
        optional=("caption", "footnote"),
        layout_id="chart_caption",
        density_class="medium",
        visual_intent={"hero": "map exhibit", "supporting": "light framing", "tone": "evidence_led"},
        variants=(
            _variant("reference_map", "chart_caption", builder_recipe_id="reference_exhibit_frame"),
        ),
        anti_patterns=("rebuilding_strong_reference_map_badly",),
        audit_checks=("map dominance", "minimal clutter"),
        pptx_editability_policy="native_with_raster_exceptions",
    ),
    "asset_partner_snapshot": _archetype(
        "asset_partner_snapshot",
        roles=("asset_overview", "market_map", "portfolio"),
        required=("cards",),
        optional=("image_path",),
        layout_id="split",
        density_class="medium",
        visual_intent={"hero": "asset_cards_plus_map", "supporting": "partner notes", "tone": "asset_specific"},
        variants=(
            _variant("snapshot", "split", builder_recipe_id="asset_partner_snapshot"),
        ),
    ),
    "portfolio_build_case_bars": _archetype(
        "portfolio_build_case_bars",
        roles=("build_case", "size_of_prize", "economics"),
        required=("stats",),
        layout_id="dashboard",
        density_class="medium",
        visual_intent={"hero": "portfolio_progression", "supporting": "bars and milestones", "tone": "growth_case"},
        variants=(
            _variant("build_case", "dashboard", builder_recipe_id="portfolio_build_case"),
        ),
    ),
    "appendix_ranked_table_card": _archetype(
        "appendix_ranked_table_card",
        roles=("appendix_ranked_table", "matrix"),
        required=("rows",),
        optional=("headers", "footnote"),
        layout_id="table",
        density_class="high",
        visual_intent={"hero": "structured evidence", "supporting": "ranked details", "tone": "institutional_dense"},
        variants=(
            _variant("appendix_table", "table", builder_recipe_id="dense_appendix_table"),
        ),
        allowed_primitives=("table", "footnote"),
        audit_checks=("header hierarchy", "row consistency"),
    ),
    "appendix_dense_evidence_matrix": _archetype(
        "appendix_dense_evidence_matrix",
        roles=("appendix", "matrix", "evidence"),
        required=("rows",),
        optional=("headers", "footnote"),
        layout_id="table",
        density_class="high",
        visual_intent={"hero": "evidence_matrix", "supporting": "structured detail", "tone": "appendix_dense"},
        variants=(
            _variant("evidence_matrix", "table", builder_recipe_id="dense_appendix_table"),
        ),
    ),
    "appendix_stakeholder_register": _archetype(
        "appendix_stakeholder_register",
        roles=("appendix", "stakeholders", "network"),
        required=("rows",),
        optional=("headers",),
        layout_id="table",
        density_class="high",
        visual_intent={"hero": "stakeholder_register", "supporting": "relationship attributes", "tone": "institutional_dense"},
        variants=(
            _variant("stakeholder_table", "table", builder_recipe_id="dense_appendix_table"),
        ),
    ),
    "appendix_assumption_table": _archetype(
        "appendix_assumption_table",
        roles=("appendix", "assumptions", "valuation"),
        required=("rows",),
        optional=("headers",),
        layout_id="table",
        density_class="high",
        visual_intent={"hero": "assumption_register", "supporting": "valuation detail", "tone": "analytical"},
        variants=(
            _variant("assumptions", "table", builder_recipe_id="dense_appendix_table"),
        ),
    ),
}

_FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "stats": ("stats", "kpis"),
    "image_path": ("image_path", "chart_path", "graphic_path", "figure_path", "chart_request"),
    "cards": ("cards", "features"),
    "steps": ("steps", "items"),
    "members": ("members", "team"),
    "left_items": ("left_items", "left_bullets", "left"),
    "right_items": ("right_items", "right_bullets", "right"),
}

ROLE_TO_DEFAULT_ARCHETYPE: dict[str, str] = {
    "cover": "cover_hero_photo_left_text_block",
    "divider": "divider_statement_band",
    "section_divider": "divider_statement_band",
    "thesis": "thesis_three_pillar_cards",
    "proposition": "thesis_numbered_value_rail",
    "access_case": "thesis_numbered_value_rail",
    "team": "executive_bio_cards_centered",
    "people": "executive_bio_cards_centered",
    "key_people": "key_people_headshot_band",
    "network": "network_dual_column_profiles",
    "access": "boots_on_ground_access_strip",
    "economics": "firepower_two_zone_summary",
    "capital": "firepower_two_zone_summary",
    "size_of_prize": "portfolio_build_case_bars",
    "valuation": "reserves_value_bar_bridge",
    "funding": "phased_acquisition_funding_map",
    "build_case": "portfolio_build_case_bars",
    "timeline": "banker_vertical_process_spine",
    "process": "banker_vertical_process_spine",
    "execution_plan": "execution_workstream_lanes",
    "roadshow": "roadshow_three_day_programme",
    "programme": "roadshow_three_day_programme",
    "workstreams": "execution_workstream_lanes",
    "opportunity_set": "opportunity_bucket_cards",
    "opportunities": "opportunity_bucket_cards",
    "live_deals": "live_pipeline_ranked_table",
    "appendix_ranked_table": "appendix_ranked_table_card",
    "pipeline": "live_pipeline_ranked_table",
    "market_map": "market_map_reference_exhibit",
    "map": "market_map_reference_exhibit",
    "asset_overview": "asset_partner_snapshot",
    "portfolio": "asset_partner_snapshot",
    "stakeholders": "appendix_stakeholder_register",
    "appendix": "appendix_dense_evidence_matrix",
    "matrix": "appendix_dense_evidence_matrix",
    "assumptions": "appendix_assumption_table",
    "content": "",
}
KNOWN_SLIDE_ROLES = frozenset(ROLE_TO_DEFAULT_ARCHETYPE) | frozenset(
    role for archetype in _ARCHETYPES.values() for role in archetype.functional_roles
)

RETRIEVAL_WEIGHTS = {
    "role_match": 0.28,
    "content_schema_match": 0.18,
    "deck_type_match": 0.10,
    "density_match": 0.08,
    "composition_family_match": 0.14,
    "style_token_match": 0.10,
    "benchmark_quality": 0.07,
    "curator_confidence": 0.05,
}


def list_full_slide_archetypes() -> list[dict[str, Any]]:
    return [item.to_manifest() for item in _ARCHETYPES.values()]


def get_full_slide_archetype(archetype_id: str) -> dict[str, Any]:
    archetype = _ARCHETYPES.get(archetype_id)
    if not archetype:
        raise KeyError(archetype_id)
    return archetype.to_manifest()


def infer_slide_role(slide_spec: dict[str, Any]) -> str:
    storyboard = slide_spec.get("storyboard", {}) or {}
    if isinstance(storyboard, dict) and storyboard.get("role"):
        return str(storyboard["role"])
    slide_type = str(slide_spec.get("slide_type", "content"))
    return {
        "title": "cover",
        "section_divider": "section_divider",
        "team_grid": "team",
        "timeline": "timeline",
        "process_flow": "process",
        "table": "appendix_ranked_table",
        "chart_caption": "market_map",
        "chart": "market_map",
        "dashboard": "economics",
        "kpi_strip": "economics",
        "stat": "economics",
        "split": "proposition",
        "three_card": "thesis",
        "four_card": "opportunity_set",
    }.get(slide_type, "content")


def _has_required_fields(slide_spec: dict[str, Any], archetype: FullSlideArchetype) -> bool:
    data = slide_spec.get("data", {}) or {}
    slide_type = str(slide_spec.get("slide_type", ""))
    for field in archetype.content_schema_required:
        if field == "image_path" and slide_type in {"chart", "chart_caption"}:
            continue
        aliases = _FIELD_ALIASES.get(field, (field,))
        if not any(data.get(alias) for alias in aliases):
            return False
    return True


def _missing_required_fields(slide_spec: dict[str, Any], archetype: FullSlideArchetype) -> list[str]:
    data = slide_spec.get("data", {}) or {}
    slide_type = str(slide_spec.get("slide_type", ""))
    missing: list[str] = []
    for field in archetype.content_schema_required:
        if field == "image_path" and slide_type in {"chart", "chart_caption"}:
            continue
        aliases = _FIELD_ALIASES.get(field, (field,))
        if not any(data.get(alias) for alias in aliases):
            missing.append(field)
    return missing


def _infer_density_class(slide_spec: dict[str, Any]) -> str:
    data = slide_spec.get("data", {}) or {}
    if data.get("rows"):
        row_count = len(data.get("rows") or [])
        return "high" if row_count >= 6 else "medium"
    count = 0
    for key in ("cards", "features", "members", "steps", "stats", "items"):
        value = data.get(key)
        if isinstance(value, list):
            count += len(value)
    if count >= 8:
        return "high"
    if count >= 4:
        return "medium"
    return "low"


def _style_token_similarity(slide_spec: dict[str, Any], archetype: FullSlideArchetype) -> float:
    storyboard = slide_spec.get("storyboard", {}) or {}
    desired = str(storyboard.get("hero_kind") or "").strip().lower()
    actual = str(archetype.visual_intent.get("hero", "")).strip().lower()
    if desired and desired == actual:
        return 1.0
    return 0.6 if not desired else 0.0


def _preferred_composition_family(archetype: FullSlideArchetype) -> str:
    recipe = archetype.compile_variants[0].builder_recipe_id if archetype.compile_variants else ""
    if "people" in recipe:
        return "people_profiles"
    if "timeline" in recipe or "roadshow" in recipe:
        return "timeline_spine"
    if "economics" in recipe or "capital" in recipe or "portfolio" in recipe:
        return "two_zone_summary"
    if "table" in recipe:
        return "dense_table"
    if "cover" in recipe:
        return "hero_cover"
    return "card_grid"


def _reference_bonus(reference_signals: dict[str, Any], archetype: FullSlideArchetype) -> tuple[float, bool]:
    if not reference_signals:
        return 0.0, False
    composition = str(reference_signals.get("composition_family", "")).strip()
    target = _preferred_composition_family(archetype)
    matched = bool(composition and composition == target)
    return (1.0 if matched else 0.35 if composition else 0.0), matched


def _pick_variant(
    archetype: FullSlideArchetype,
    *,
    reference_signals: dict[str, Any],
    density_class: str,
) -> CompileVariant:
    variants = archetype.compile_variants
    if len(variants) == 1:
        return variants[0]
    composition = str(reference_signals.get("composition_family", "")).strip()
    if composition == "people_profiles":
        for item in variants:
            if "people" in item.builder_recipe_id:
                return item
    if composition == "timeline_spine":
        for item in variants:
            if "timeline" in item.builder_recipe_id:
                return item
    if density_class == "high":
        for item in variants:
            if "dense" in item.builder_recipe_id or item.layout_id == "table":
                return item
    if composition == "hero_cover":
        for item in variants:
            if "bleed" in item.builder_recipe_id:
                return item
    return variants[0]


def retrieve_full_slide_candidates(
    *,
    role: str,
    slide_spec: dict[str, Any],
    deck_type: str = "investor",
    reference_family: str = "",
    reference_signals: dict[str, Any] | None = None,
    top_k: int = 3,
) -> list[dict[str, Any]]:
    """Return ranked archetype candidates using richer explainable scoring."""
    resolved_role = role or infer_slide_role(slide_spec)
    inferred_density = _infer_density_class(slide_spec)
    candidates: list[dict[str, Any]] = []
    for archetype in _ARCHETYPES.values():
        role_match = 1.0 if role in archetype.functional_roles else 0.7 if resolved_role in archetype.functional_roles else 0.0
        if role_match <= 0:
            continue
        schema_match = _has_required_fields(slide_spec, archetype)
        deck_type_match = 1.0 if deck_type in archetype.deck_types else 0.0
        density_match = 1.0 if inferred_density == archetype.density_class else 0.6 if {
            inferred_density,
            archetype.density_class,
        } <= {"low", "medium"} or {inferred_density, archetype.density_class} <= {"medium", "high"} else 0.0
        composition_bonus, benchmark_family_match = _reference_bonus(reference_signals or {}, archetype)
        if reference_family and not reference_signals:
            composition_bonus = max(composition_bonus, 0.35)
        style_token_match = _style_token_similarity(slide_spec, archetype)
        benchmark_quality = float((reference_signals or {}).get("benchmark_quality_weight", 0.0) or 0.0)
        curator_confidence = float((reference_signals or {}).get("curator_confidence", 0.0) or 0.0)
        components = {
            "role_match": role_match,
            "content_schema_match": 1.0 if schema_match else 0.0,
            "deck_type_match": deck_type_match,
            "density_match": density_match,
            "composition_family_match": composition_bonus,
            "style_token_match": style_token_match,
            "benchmark_quality": benchmark_quality,
            "curator_confidence": curator_confidence,
        }
        score = round(sum(RETRIEVAL_WEIGHTS[key] * value for key, value in components.items()), 4)
        if ROLE_TO_DEFAULT_ARCHETYPE.get(resolved_role) == archetype.id:
            score = round(score + 0.015, 4)
        if score <= 0:
            continue
        variant = _pick_variant(archetype, reference_signals=reference_signals or {}, density_class=inferred_density)
        candidates.append(
            {
                "id": archetype.id,
                "score": score,
                "role_match": bool(role_match >= 1.0),
                "content_schema_match": schema_match,
                "reference_family_bonus_applied": bool(reference_family and (benchmark_family_match or not reference_signals)),
                "qualified": score >= 0.62 and schema_match,
                "advisory_only": 0.45 <= score < 0.62,
                "do_not_use": bool(not schema_match or score < 0.45),
                "score_components": components,
                "variant_id": variant.variant_id,
                "builder_recipe_id": variant.builder_recipe_id,
                "density_class": archetype.density_class,
            }
        )
    candidates.sort(key=lambda item: (-item["score"], item["do_not_use"], item["id"], item["variant_id"]))
    return candidates[:top_k]


def compile_slide_manifest(
    slide_spec: dict[str, Any],
    *,
    slide_id: str,
    resolved_role: str,
    archetype_id: str,
    source_reference_family: str = "",
    source_reference_slide_ids: list[str] | None = None,
    variant_id: str = "",
    builder_recipe_id: str = "",
    benchmark_tokens_applied: dict[str, Any] | None = None,
) -> dict[str, Any]:
    archetype = _ARCHETYPES.get(archetype_id) if archetype_id else None
    requested_slide_type = str(slide_spec.get("slide_type") or "")
    if archetype_id and not archetype:
        raise ValueError(f"Unknown archetype '{archetype_id}'")
    if not archetype:
        return validate_compiled_slide_manifest(
            {
                "schema_name": COMPILED_SLIDE_SCHEMA_NAME,
                "schema_version": COMPILED_SLIDE_SCHEMA_VERSION,
                "slide_id": slide_id,
                "source_archetype": "",
                "source_reference_family": source_reference_family,
                "source_reference_slide_ids": source_reference_slide_ids or [],
                "resolved_role": resolved_role,
                "requested_slide_type": requested_slide_type,
                "variant_id": "authored",
                "builder_recipe_id": "",
                "compile_target": {
                    "kind": "layout",
                    "layout_id": requested_slide_type or "content",
                    "template_id": None,
                },
                "benchmark_tokens_applied": benchmark_tokens_applied or {},
                "render_payload": {
                    "slide_type": requested_slide_type or "content",
                    "data": deepcopy(slide_spec.get("data", {})),
                },
                "parity_requirements": {
                    "pdf_visual_parity": "required",
                    "pptx_visual_parity": "required",
                    "pptx_native_editability": "required",
                },
                "pptx_editability_exceptions": [],
            }
        )
    missing_required = _missing_required_fields(slide_spec, archetype)
    if missing_required:
        raise ValueError(f"Archetype '{archetype_id}' missing required fields: {', '.join(missing_required)}")
    if resolved_role and resolved_role not in archetype.functional_roles:
        raise ValueError(f"Archetype '{archetype_id}' is incompatible with resolved role '{resolved_role}'")
    chosen_variant = next((item for item in archetype.compile_variants if item.variant_id == variant_id), None)
    if chosen_variant is None:
        chosen_variant = archetype.compile_variants[0]
    if builder_recipe_id and chosen_variant.builder_recipe_id != builder_recipe_id:
        chosen_variant = CompileVariant(
            variant_id=chosen_variant.variant_id,
            layout_id=chosen_variant.layout_id,
            template_id=chosen_variant.template_id,
            builder_recipe_id=builder_recipe_id,
            benchmark_tokens=chosen_variant.benchmark_tokens,
            editable_pptx_supported=chosen_variant.editable_pptx_supported,
            fallback_policy=chosen_variant.fallback_policy,
        )
    render_payload = {
        "slide_type": archetype.compile_layout_id,
        "data": deepcopy(slide_spec.get("data", {})),
    }
    compile_target = {
        "kind": archetype.compile_target_kind,
        "layout_id": chosen_variant.layout_id,
        "template_id": archetype.compile_template_id,
    }
    exceptions: list[str] = []
    data = render_payload["data"]
    if any(data.get(k) for k in ("image_path", "background_image", "logo_path")):
        exceptions.append("intentional_raster_asset")
    manifest = {
        "schema_name": COMPILED_SLIDE_SCHEMA_NAME,
        "schema_version": COMPILED_SLIDE_SCHEMA_VERSION,
        "slide_id": slide_id,
        "source_archetype": archetype_id,
        "source_reference_family": source_reference_family,
        "source_reference_slide_ids": source_reference_slide_ids or [],
        "variant_id": chosen_variant.variant_id,
        "builder_recipe_id": chosen_variant.builder_recipe_id,
        "benchmark_tokens_applied": benchmark_tokens_applied or deepcopy(chosen_variant.benchmark_tokens or {}),
        "resolved_role": resolved_role,
        "requested_slide_type": requested_slide_type,
        "compile_target": compile_target,
        "render_payload": render_payload,
        "parity_requirements": {
            "pdf_visual_parity": "required",
            "pptx_visual_parity": "required",
            "pptx_native_editability": "required" if not exceptions else "required_with_exceptions",
        },
        "pptx_editability_exceptions": exceptions,
    }
    return validate_compiled_slide_manifest(manifest)


def materialize_compiled_slide_spec(slide_spec: dict[str, Any]) -> dict[str, Any]:
    materialized = deepcopy(slide_spec)
    manifest = validate_compiled_slide_manifest(materialized.get("compiled_manifest", {}) or {})
    render_payload = manifest.get("render_payload", {})
    if isinstance(render_payload, dict):
        slide_type = render_payload.get("slide_type")
        data = render_payload.get("data")
        if slide_type:
            materialized["slide_type"] = slide_type
        if isinstance(data, dict):
            materialized["data"] = deepcopy(data)
    materialized["compiled_manifest"] = manifest
    return materialized


__all__ = [
    "COMPILED_SLIDE_SCHEMA_NAME",
    "COMPILED_SLIDE_SCHEMA_VERSION",
    "FULL_SLIDE_ARCHETYPE_SCHEMA_NAME",
    "FULL_SLIDE_ARCHETYPE_SCHEMA_VERSION",
    "KNOWN_SLIDE_ROLES",
    "ROLE_TO_DEFAULT_ARCHETYPE",
    "RETRIEVAL_WEIGHTS",
    "compile_slide_manifest",
    "get_full_slide_archetype",
    "infer_slide_role",
    "list_full_slide_archetypes",
    "materialize_compiled_slide_spec",
    "retrieve_full_slide_candidates",
]
