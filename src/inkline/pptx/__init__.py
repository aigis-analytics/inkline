"""Inkline PPTX backend.

Primary offline slide builder using ``python-pptx`` plus a lightweight
spec-to-PPTX exporter for execute-mode slide manifests.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from inkline.brands import get_brand
from inkline.pptx.auditor import DeckAuditor
from inkline.pptx.builder import PptxBuilder, resolve_pptx_layout

log = logging.getLogger(__name__)


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        result = []
        for item in value:
            if isinstance(item, dict):
                label = item.get("label") or item.get("title") or item.get("name") or item.get("value")
                body = item.get("body") or item.get("desc") or item.get("description")
                if label and body:
                    result.append(f"{label}: {body}")
                elif label:
                    result.append(str(label))
                else:
                    result.append(str(item))
            else:
                result.append(str(item))
        return result
    if isinstance(value, tuple):
        return [str(v) for v in value]
    if isinstance(value, str):
        return [line.strip("- ").strip() for line in value.splitlines() if line.strip()]
    return [str(value)]


def _card_triplets(cards: Any, *, limit: int) -> list[tuple[str, str, str]]:
    result: list[tuple[str, str, str]] = []
    for item in (cards or [])[:limit]:
        if isinstance(item, dict):
            result.append((
                str(item.get("icon", "")),
                str(item.get("title", item.get("label", ""))),
                str(item.get("body", item.get("desc", item.get("description", "")))),
            ))
        elif isinstance(item, (list, tuple)):
            seq = [str(x) for x in item]
            if len(seq) >= 3:
                result.append((seq[0], seq[1], seq[2]))
            elif len(seq) == 2:
                result.append(("", seq[0], seq[1]))
            elif len(seq) == 1:
                result.append(("", seq[0], ""))
        else:
            result.append(("", str(item), ""))
    return result


def _stat_triplets(stats: Any) -> list[tuple[str, str, str]]:
    result: list[tuple[str, str, str]] = []
    for item in stats or []:
        if isinstance(item, dict):
            result.append((
                str(item.get("value", item.get("stat", ""))),
                str(item.get("label", item.get("title", ""))),
                str(item.get("desc", item.get("body", item.get("description", "")))),
            ))
        elif isinstance(item, (list, tuple)):
            seq = [str(x) for x in item]
            if len(seq) >= 3:
                result.append((seq[0], seq[1], seq[2]))
            elif len(seq) == 2:
                result.append((seq[0], seq[1], ""))
            elif len(seq) == 1:
                result.append((seq[0], "", ""))
        else:
            result.append((str(item), "", ""))
    return result


def _table_rows(rows: Any, *, headers: list[str] | None = None) -> list[list[str]]:
    result: list[list[str]] = []
    for row in rows or []:
        if isinstance(row, dict):
            if headers:
                result.append([str(row.get(header, "")) for header in headers])
            else:
                result.append([str(v) for v in row.values()])
        elif isinstance(row, (list, tuple)):
            result.append([str(v) for v in row])
        else:
            result.append([str(row)])
    return result


def _first_existing_path(candidates: list[str | Path | None], *, root: Path) -> Path | None:
    for candidate in candidates:
        if not candidate:
            continue
        path = Path(candidate)
        if not path.is_absolute():
            path = root / path
        if path.exists():
            return path
    return None


def _coerce_chart_path(
    slide_spec: dict[str, Any],
    *,
    output_path: Path,
    source_root: Path,
    brand_name: str,
    slide_index: int,
) -> Path | None:
    data = slide_spec.get("data", {})

    # Reuse an existing image if one is already provided.
    explicit = _first_existing_path(
        [
            data.get("image_path"),
            data.get("chart_path"),
            data.get("graphic_path"),
            data.get("figure_path"),
        ],
        root=source_root,
    )
    if explicit:
        return explicit

    chart_req = data.get("chart_request")
    if not chart_req:
        charts = data.get("charts", [])
        if charts:
            explicit_nested = _first_existing_path(
                [charts[0].get("image_path"), charts[0].get("chart_path")],
                root=source_root,
            )
            if explicit_nested:
                return explicit_nested
            chart_req = charts[0].get("chart_request")

    if not chart_req:
        return None

    chart_type = chart_req.get("chart_type", "")
    chart_data = chart_req.get("chart_data", {})
    if not chart_type or not chart_data:
        return None

    render_dir = output_path.parent / f"{output_path.stem}_charts"
    render_dir.mkdir(parents=True, exist_ok=True)
    chart_path = render_dir / f"slide_{slide_index + 1:02d}_{chart_type}.png"

    from inkline.typst.chart_renderer import render_chart_for_brand

    render_chart_for_brand(
        chart_type=chart_type,
        data=chart_data,
        output_path=chart_path,
        brand_name=brand_name,
        width=float(chart_req.get("width", 7.0)),
        height=float(chart_req.get("height", 3.5)),
        color_mode=chart_req.get("color_mode"),
    )
    return chart_path


def _fallback_items(data: dict[str, Any]) -> list[str]:
    items = _as_list(data.get("bullets") or data.get("items"))
    if items:
        return items
    for key in ("caption", "summary", "body", "description", "narrative"):
        if data.get(key):
            return _as_list(data.get(key))
    return []


def _freeform_contains_raster_asset(data: dict[str, Any]) -> bool:
    shapes = data.get("shapes") or data.get("_shapes_manifest") or []
    if not isinstance(shapes, list):
        return False
    for shape in shapes:
        if isinstance(shape, dict) and str(shape.get("type", "")).strip().lower() == "image":
            return True
    return False


def export_pptx_slides(
    slides: list[dict[str, Any]],
    output_path: str | Path,
    *,
    brand: str = "minimal",
    title: str = "",
    source_root: str | Path | None = None,
    metadata_path: str | Path | None = None,
    editable_institutional: bool = False,
    deck_metadata: dict[str, Any] | None = None,
) -> Path:
    """Render a list of slide specs to a PPTX file."""
    output = Path(output_path)
    resolved_source_root = Path(source_root) if source_root else output.parent
    brand_obj = get_brand(brand)
    deck_title = title or output.stem
    builder = PptxBuilder(
        title=deck_title,
        brand=brand_obj.name,
        heading_font=brand_obj.heading_font,
        body_font=brand_obj.body_font,
    )
    metadata_slides: list[dict[str, Any]] = []

    for idx, slide_spec in enumerate(slides):
        data = slide_spec.get("data", {})
        slide_type = resolve_pptx_layout(slide_spec)
        compiled_manifest = (slide_spec.get("compiled_manifest", {}) or {})
        builder_recipe_id = str(compiled_manifest.get("builder_recipe_id", "")).strip()
        section = str(data.get("section", ""))
        heading = str(data.get("title", data.get("headline", "")))
        requested_type = str(slide_spec.get("slide_type", "content"))
        status = "native"
        fallback_reason = ""
        editability_exceptions = list(
            compiled_manifest.get("pptx_editability_exceptions", [])
        )

        if builder_recipe_id in {"cover_title_block", "cover_editorial_bleed", "divider_statement_band"} or slide_type in {"title", "section_divider"}:
            builder.add_title_slide(
                company=str(data.get("company", deck_title)),
                tagline=str(data.get("tagline", heading)),
                date=str(data.get("date", "")),
                subtitle=str(data.get("subtitle", section)),
            )
        elif builder_recipe_id in {"people_headshot_cards", "people_circle_portraits", "people_headshot_band", "boots_on_ground_strip"}:
            builder.add_people_headshot_slide(
                section=section or "People",
                title=heading or deck_title,
                members=data.get("members") or data.get("team") or [],
                footnote=str(data.get("footnote", "")),
            )
        elif builder_recipe_id in {"timeline_vertical_spine", "timeline_milestone_cards", "timeline_phase_row", "roadshow_three_day", "workstream_lanes"}:
            milestones = data.get("milestones") or []
            if not milestones and data.get("steps"):
                milestones = [
                    {
                        "date": str(index + 1),
                        "label": item.get("title", item.get("label", "")) if isinstance(item, dict) else str(item),
                        "desc": item.get("body", item.get("desc", "")) if isinstance(item, dict) else "",
                    }
                    for index, item in enumerate(data.get("steps") or [])
                ]
            builder.add_timeline_spine_slide(
                section=section or "Timeline",
                title=heading or deck_title,
                milestones=milestones,
                footnote=str(data.get("footnote", "")),
            )
        elif builder_recipe_id in {"economics_two_zone", "capital_growth_bridge", "reserves_bar_bridge", "portfolio_build_case", "phased_funding_map"}:
            builder.add_economics_bridge_slide(
                section=section or "Economics",
                title=heading or deck_title,
                stats=_stat_triplets(data.get("stats") or data.get("kpis") or []),
                bullets=_as_list(data.get("bullets") or data.get("items") or []),
                footnote=str(data.get("footnote", "")),
            )
        elif builder_recipe_id in {"pipeline_ranked_table", "dense_appendix_table"}:
            headers = [str(h) for h in data.get("headers", [])]
            rows = _table_rows(data.get("rows"), headers=headers)
            if not headers and rows:
                headers = [f"Column {i + 1}" for i in range(max(len(r) for r in rows))]
            builder.add_pipeline_table_slide(
                section=section or "Detail",
                title=heading or deck_title,
                headers=headers,
                rows=rows,
                footnote=str(data.get("footnote", "")),
            )
        elif slide_type == "content":
            builder.add_content_slide(
                section=section or "Overview",
                title=heading or deck_title,
                items=_fallback_items(data),
                accent_stat=str(data.get("accent_stat", data.get("hero_value", ""))),
                accent_label=str(data.get("accent_label", data.get("hero_label", ""))),
                footnote=str(data.get("footnote", "")),
            )
        elif slide_type == "three_card":
            builder.add_three_card_slide(
                section=section or "Overview",
                title=heading or deck_title,
                cards=_card_triplets(data.get("cards"), limit=3),
                footnote=str(data.get("footnote", "")),
            )
        elif slide_type in {"four_card", "feature_grid", "team_grid", "credentials"}:
            card_source = data.get("cards") or data.get("features") or data.get("team") or data.get("members") or data.get("items")
            builder.add_four_card_slide(
                section=section or "Overview",
                title=heading or deck_title,
                cards=_card_triplets(card_source, limit=4),
                footnote=str(data.get("footnote", "")),
            )
        elif slide_type == "timeline":
            milestones = data.get("milestones") or []
            cards = []
            for milestone in milestones[:4]:
                if isinstance(milestone, dict):
                    cards.append(
                        (
                            str(milestone.get("date", "")),
                            str(milestone.get("label", milestone.get("title", ""))),
                            str(milestone.get("desc", milestone.get("body", ""))),
                        )
                    )
            if cards:
                status = "fallback"
                fallback_reason = "timeline_backend_degraded_to_four_card"
                builder.add_four_card_slide(
                    section=section or "Timeline",
                    title=heading or deck_title,
                    cards=cards,
                    footnote=str(data.get("footnote", "")),
                )
            else:
                status = "fallback"
                fallback_reason = "timeline_missing_milestones"
                builder.add_content_slide(
                    section=section or "Timeline",
                    title=heading or deck_title,
                    items=_fallback_items(data),
                    footnote=str(data.get("footnote", "")),
                )
        elif slide_type in {"stat", "icon_stat", "kpi_strip"}:
            stats = data.get("stats") or data.get("kpis") or data.get("items")
            builder.add_stat_slide(
                section=section or "Highlights",
                title=heading or deck_title,
                stats=_stat_triplets(stats),
            )
        elif slide_type == "table":
            headers = [str(h) for h in data.get("headers", [])]
            rows = _table_rows(data.get("rows"), headers=headers)
            if not headers and rows:
                headers = [f"Column {i + 1}" for i in range(max(len(r) for r in rows))]
            builder.add_table_slide(
                section=section or "Detail",
                title=heading or deck_title,
                headers=headers,
                rows=rows,
                footnote=str(data.get("footnote", "")),
            )
        elif slide_type in {"split", "comparison", "before_after"}:
            builder.add_split_slide(
                section=section or "Comparison",
                title=heading or deck_title,
                left_title=str(data.get("left_title", "Left")),
                left_items=_as_list(data.get("left_items") or data.get("left_bullets") or data.get("left")),
                right_title=str(data.get("right_title", "Right")),
                right_items=_as_list(data.get("right_items") or data.get("right_bullets") or data.get("right")),
                left_dark=bool(data.get("left_dark", True)),
            )
        elif slide_type in {
            "chart", "chart_caption", "dashboard", "multi_chart",
            "progress_bars", "process_flow", "pyramid",
        }:
            chart_path = _coerce_chart_path(
                slide_spec,
                output_path=output,
                source_root=resolved_source_root,
                brand_name=brand_obj.name,
                slide_index=idx,
            )
            if chart_path:
                builder.add_chart_slide(
                    section=section or "Exhibit",
                    title=heading or deck_title,
                    chart_path=chart_path,
                    footnote=str(data.get("footnote", data.get("caption", ""))),
                )
                if chart_path or data.get("image_path"):
                    status = "native_with_exceptions"
                    if "intentional_raster_asset" not in editability_exceptions:
                        editability_exceptions.append("intentional_raster_asset")
            else:
                status = "fallback"
                fallback_reason = "chart_request_missing_or_unrenderable"
                builder.add_content_slide(
                    section=section or "Overview",
                    title=heading or deck_title,
                    items=_fallback_items(data),
                    footnote=str(data.get("footnote", "")),
                )
        elif slide_type == "freeform":
            builder.add_freeform_slide(
                title=heading,
                section=section,
                shapes=data.get("shapes") or data.get("_shapes_manifest") or [],
            )
            if _freeform_contains_raster_asset(data):
                status = "native_with_exceptions"
                if "intentional_raster_asset" not in editability_exceptions:
                    editability_exceptions.append("intentional_raster_asset")
        elif slide_type == "closing":
            builder.add_closing_slide(
                name=str(data.get("name", "")),
                role=str(data.get("role", "")),
                email=str(data.get("email", "")),
                company=str(data.get("company", "")),
                tagline=str(data.get("tagline", "")),
            )
        else:
            log.warning("PPTX exporter falling back for unsupported slide type: %s", slide_type)
            status = "fallback"
            fallback_reason = f"unsupported_slide_type:{slide_type}"
            builder.add_content_slide(
                section=section or "Overview",
                title=heading or deck_title,
                items=_fallback_items(data),
                footnote=str(data.get("footnote", "")),
            )

        if (
            status == "native"
            and (data.get("image_path") or data.get("background_image"))
        ):
            status = "native_with_exceptions"
            if "intentional_raster_asset" not in editability_exceptions:
                editability_exceptions.append("intentional_raster_asset")

        metadata_slides.append(
            {
                "slide_number": idx + 1,
                "requested_type": requested_type,
                "resolved_type": slide_type,
                "status": status,
                "fallback_reason": fallback_reason,
                "slide_id": slide_spec.get("slide_id", ""),
                "storyboard": slide_spec.get("storyboard", {}),
                "compiled_manifest": slide_spec.get("compiled_manifest", {}),
                "pptx_editability_exceptions": editability_exceptions,
            }
        )

    if editable_institutional:
        fallback_slides = [
            item for item in metadata_slides if item["status"] == "fallback"
        ]
        if fallback_slides:
            slide_summary = ", ".join(
                f"{item['slide_number']} ({item['fallback_reason'] or item['resolved_type']})"
                for item in fallback_slides
            )
            raise RuntimeError(
                "Editable institutional PPTX export requires native slides or declared editability exceptions only; "
                f"fallback slides encountered: {slide_summary}"
            )

    builder.apply_notes_from_slides(slides)
    saved = builder.save(output)
    if metadata_path:
        import json

        total = len(metadata_slides) or 1
        editable_count = sum(
            1
            for item in metadata_slides
            if item["status"] in {"native", "native_with_exceptions"}
        )
        fully_native_count = sum(1 for item in metadata_slides if item["status"] == "native")
        payload = {
            "pptx_path": saved.name,
            "editable_institutional": editable_institutional,
            "editable_native_ratio": editable_count / total,
            "fully_native_ratio": fully_native_count / total,
            "slides_with_image_fallback": [
                item["slide_number"] for item in metadata_slides if item["status"] == "fallback"
            ],
            "slides_with_editability_exceptions": [
                item["slide_number"] for item in metadata_slides if item["status"] == "native_with_exceptions"
            ],
            "fallback_reasons": {
                str(item["slide_number"]): item["fallback_reason"]
                for item in metadata_slides
                if item["fallback_reason"]
            },
            "slide_statuses": {
                str(item["slide_number"]): item["status"] for item in metadata_slides
            },
            "slides": metadata_slides,
            "deck_metadata": deck_metadata or {},
        }
        meta_file = Path(metadata_path)
        meta_file.parent.mkdir(parents=True, exist_ok=True)
        meta_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return saved


__all__ = ["PptxBuilder", "DeckAuditor", "export_pptx_slides"]
