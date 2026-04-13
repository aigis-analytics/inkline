"""Overflow audit — validates slide/exhibit sizing before and after rendering.

Used by the Archon review process to detect content that won't fit on a slide
or images that exceed the safe embed area. Returns actionable warnings so the
design advisor can re-plan slides with too much content.

Usage
-----
    from inkline.intelligence.overflow_audit import audit_deck, audit_image

    warnings = audit_deck(slides)  # list[SlideSpec]-like dicts
    for w in warnings:
        print(w)

    img_ok = audit_image("chart.png", max_width_cm=20.7, max_height_cm=8.5)
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from inkline.intelligence.layout_selector import SLIDE_CAPACITY

log = logging.getLogger(__name__)

# Slide geometry (must stay in sync with TypstSlideRenderer constants)
SLIDE_CONTENT_WIDTH_CM = 23.0
SLIDE_BODY_HEIGHT_CM = 8.5
MAX_IMAGE_WIDTH_CM = 20.7  # 90% of content width
MAX_IMAGE_HEIGHT_CM = 8.5
IMAGE_DPI_TARGET = 200


@dataclass
class AuditWarning:
    slide_index: int
    slide_type: str
    severity: str  # "info" | "warn" | "error"
    message: str

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] slide {self.slide_index} ({self.slide_type}): {self.message}"


# Field names that carry content arrays, keyed by slide_type
_CONTENT_FIELDS: dict[str, list[str]] = {
    "content": ["items"],
    "table": ["rows"],
    "bar_chart": ["bars"],
    "three_card": ["cards"],
    "four_card": ["cards"],
    "stat": ["stats"],
    "kpi_strip": ["kpis"],
    "split": ["left_items", "right_items"],
    "timeline": ["milestones"],
    "process_flow": ["steps"],
    "icon_stat": ["stats"],
    "progress_bars": ["bars"],
    "pyramid": ["tiers"],
    "comparison": ["left.items", "right.items"],
    "feature_grid": ["features"],
    "dashboard": ["bullets"],   # the limiting field — chart + 3 stats are fixed
    "chart_caption": ["bullets"],
}


def _get_nested(d: dict, dotted: str) -> Any:
    cur: Any = d
    for part in dotted.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def audit_slide(slide_index: int, slide_type: str, data: dict) -> list[AuditWarning]:
    """Audit one slide's content volume against its layout capacity."""
    warnings: list[AuditWarning] = []
    capacity = SLIDE_CAPACITY.get(slide_type, 0)

    for field in _CONTENT_FIELDS.get(slide_type, []):
        items = _get_nested(data, field)
        if not isinstance(items, list):
            continue
        if capacity and len(items) > capacity:
            warnings.append(AuditWarning(
                slide_index, slide_type, "warn",
                f"field '{field}' has {len(items)} items but slide capacity is {capacity}. "
                f"Excess items will be truncated by the renderer. Consider splitting into multiple slides.",
            ))

    # Long bullet/label strings tend to wrap and push content off slide
    for field in _CONTENT_FIELDS.get(slide_type, []):
        items = _get_nested(data, field)
        if isinstance(items, list):
            for i, item in enumerate(items):
                text = item if isinstance(item, str) else (
                    item.get("label") or item.get("title") or item.get("body") or ""
                    if isinstance(item, dict) else ""
                )
                if text and len(text) > 220:
                    warnings.append(AuditWarning(
                        slide_index, slide_type, "warn",
                        f"{field}[{i}] text is {len(text)} chars — risks wrapping beyond slide height.",
                    ))

    # Chart slides must reference an existing image
    if slide_type == "chart":
        path = data.get("image_path")
        if path and os.path.exists(path):
            warnings.extend(audit_image(path, slide_index=slide_index))
        elif path:
            warnings.append(AuditWarning(
                slide_index, "chart", "error",
                f"image_path '{path}' does not exist.",
            ))

    return warnings


def audit_image(
    path: str | Path,
    *,
    slide_index: int = -1,
    max_width_cm: float = MAX_IMAGE_WIDTH_CM,
    max_height_cm: float = MAX_IMAGE_HEIGHT_CM,
    dpi: int = IMAGE_DPI_TARGET,
) -> list[AuditWarning]:
    """Audit a PNG exhibit for size suitability as a slide embed.

    Returns warnings if the image's aspect ratio would force it to exceed the
    safe body height when scaled to slide width, or if the file is too small/large.
    """
    warnings: list[AuditWarning] = []
    try:
        from PIL import Image  # lazy import
    except ImportError:
        return warnings  # can't audit without PIL — skip silently

    try:
        with Image.open(path) as im:
            w_px, h_px = im.size
    except Exception as e:
        warnings.append(AuditWarning(
            slide_index, "chart", "error",
            f"failed to open image '{path}': {e}",
        ))
        return warnings

    # Convert px → cm at target DPI
    w_cm = w_px / dpi * 2.54
    h_cm = h_px / dpi * 2.54

    # If scaled to max_width, would it exceed max_height?
    if w_cm > 0:
        scale = max_width_cm / w_cm
        scaled_h = h_cm * scale
        if scaled_h > max_height_cm + 0.3:  # 3mm tolerance
            warnings.append(AuditWarning(
                slide_index, "chart", "warn",
                f"image {Path(path).name} is {w_px}×{h_px}px ({w_cm:.1f}×{h_cm:.1f}cm @ {dpi}dpi); "
                f"when fit to slide width it would be {scaled_h:.1f}cm tall (max {max_height_cm}cm). "
                f"Re-render with smaller matplotlib figsize (e.g. 8×4 inches) or use height constraint.",
            ))

    # Flag extreme aspect ratios that typically look bad on slides
    if h_px > 0:
        aspect = w_px / h_px
        if aspect < 1.2:
            warnings.append(AuditWarning(
                slide_index, "chart", "info",
                f"image aspect ratio {aspect:.2f} is nearly square/tall — wide-format (≥1.6) reads better on 16:9 slides.",
            ))

    return warnings


def audit_deck(slides: list[dict]) -> list[AuditWarning]:
    """Audit a full deck (list of {slide_type, data} dicts or SlideSpec-likes).

    Returns all warnings flattened across all slides.
    """
    warnings: list[AuditWarning] = []
    for i, slide in enumerate(slides):
        if hasattr(slide, "slide_type"):  # SlideSpec dataclass
            stype = slide.slide_type
            data = slide.data
        else:
            stype = slide.get("slide_type", "")
            data = slide.get("data", {})
        warnings.extend(audit_slide(i, stype, data))
    return warnings


def format_report(warnings: list[AuditWarning]) -> str:
    """Render an audit report as a printable string."""
    if not warnings:
        return "OK: no overflow issues detected."
    by_sev = {"error": 0, "warn": 0, "info": 0}
    for w in warnings:
        by_sev[w.severity] = by_sev.get(w.severity, 0) + 1
    header = (
        f"OVERFLOW AUDIT: {by_sev['error']} errors, "
        f"{by_sev['warn']} warnings, {by_sev['info']} info"
    )
    lines = [header, "-" * len(header)]
    lines.extend(str(w) for w in warnings)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# POST-RENDER VISUAL AUDIT
# ---------------------------------------------------------------------------
# After the PDF is compiled, count actual pages and compare to expected
# slide count. If they differ, content has overflowed onto extra pages.
# This is the only audit that catches real layout overflow (vs the static
# capacity audit above which is content-count-based).

def audit_rendered_pdf(pdf_path: str | Path, expected_slides: int) -> list[AuditWarning]:
    """Audit a compiled PDF: every slide must occupy exactly one page.

    Counts actual pages in the PDF and compares to expected slide count.
    Returns errors if any slides overflowed onto extra pages.
    """
    warnings: list[AuditWarning] = []
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        return warnings

    actual_pages = _count_pdf_pages(pdf_path)
    if actual_pages is None:
        return warnings

    if actual_pages > expected_slides:
        overflow = actual_pages - expected_slides
        warnings.append(AuditWarning(
            slide_index=-1,
            slide_type="deck",
            severity="error",
            message=(
                f"VISUAL OVERFLOW: deck has {expected_slides} slides but rendered "
                f"{actual_pages} pages ({overflow} slides overflow onto extra pages). "
                f"Most likely cause: a chart/grid + 2-line title combination exceeds "
                f"the slide content area. Reduce chart height, shorten titles, or "
                f"split content across multiple slides. Inspect: {pdf_path}"
            ),
        ))
    elif actual_pages < expected_slides:
        warnings.append(AuditWarning(
            slide_index=-1,
            slide_type="deck",
            severity="warn",
            message=(
                f"deck has {expected_slides} slides but only {actual_pages} pages "
                f"rendered — some slides may have been merged or are empty."
            ),
        ))

    return warnings


def audit_chart_image(image_path: str | Path) -> list[AuditWarning]:
    """Detect content touching the edge of a chart PNG (bbox clipping).

    When matplotlib renders with `bbox_inches="tight"`, labels positioned
    outside the axes can be clipped. This audit checks if any content
    pixels are touching the outer 4px border of the image — that's a
    near-certain sign of clipping.

    Returns warning(s) if the chart appears to be clipped.
    """
    warnings: list[AuditWarning] = []
    try:
        from PIL import Image
        import numpy as np
    except ImportError:
        return warnings

    image_path = Path(image_path)
    if not image_path.exists():
        return warnings

    try:
        with Image.open(image_path) as im:
            im_rgba = im.convert("RGBA")
            arr = np.array(im_rgba)
    except Exception:
        return warnings

    if arr.size == 0 or arr.shape[0] < 20 or arr.shape[1] < 20:
        return warnings

    # Detect "content" pixels — anything that's not the chart background.
    # Background is whatever colour is in the corner pixels (most chart
    # backgrounds are uniform white/off-white). A content pixel differs
    # from background by more than 25/255 in any channel.
    bg_pixel = arr[2, 2, :3].astype(int)  # near-corner sample
    diff = np.abs(arr[:, :, :3].astype(int) - bg_pixel).max(axis=2)
    content_mask = diff > 25  # boolean

    # Check the outer 4px border for content
    border = 4
    h, w = content_mask.shape
    edges_with_content = []
    if content_mask[:border, :].any():
        edges_with_content.append("top")
    if content_mask[-border:, :].any():
        edges_with_content.append("bottom")
    if content_mask[:, :border].any():
        edges_with_content.append("left")
    if content_mask[:, -border:].any():
        edges_with_content.append("right")

    if edges_with_content:
        warnings.append(AuditWarning(
            slide_index=-1,
            slide_type="chart_image",
            severity="warn",
            message=(
                f"CHART CLIPPING: {image_path.name} has content touching the "
                f"{', '.join(edges_with_content)} edge — labels or data are "
                f"likely cut off. Increase figure size, move labels inside the "
                f"plot area, or use an external legend. Inspect: {image_path}"
            ),
        ))

    return warnings


def audit_all_chart_images(charts_dir: str | Path) -> list[AuditWarning]:
    """Audit every PNG in a charts directory for edge clipping."""
    charts_dir = Path(charts_dir)
    if not charts_dir.is_dir():
        return []
    warnings: list[AuditWarning] = []
    for png in sorted(charts_dir.glob("*.png")):
        warnings.extend(audit_chart_image(png))
    return warnings


# ---------------------------------------------------------------------------
# LLM-DRIVEN VISUAL AUDIT (Claude vision)
# ---------------------------------------------------------------------------
# A real designer looks at each slide and tells you what's wrong. Claude can
# do the same — vastly more accurate than pixel-scanning heuristics. This is
# the audit that catches:
#  - Donut chart label clipping
#  - Radar chart legend overlap
#  - Multi-coloured elements that should be single-colour (brand discipline)
#  - Misalignment, weak hierarchy, awkward spacing
#  - Style inconsistency across slides

def _build_visual_audit_system(brand: str = "", source_text: str = "") -> str:
    """Build the visual auditor system prompt with FULL design context.

    The auditor receives the SAME design knowledge as DesignAdvisor:
    - Full playbooks (untruncated)
    - Full SLIDE_TYPE_GUIDE (all slide types + data schemas)
    - Learned patterns for the brand
    This ensures equal authority in the design dialogue.
    """
    # Load design playbooks — FULL content, not truncated
    playbook_context = ""
    try:
        from inkline.intelligence.playbooks import load_playbooks_for_task
        playbooks = load_playbooks_for_task("slide")
        parts = []
        for name, content in playbooks.items():
            parts.append(f"## {name.replace('_', ' ').title()}")
            parts.append(content)  # FULL content, no truncation
        playbook_context = "\n\n".join(parts)
    except Exception:
        pass

    # Load SLIDE_TYPE_GUIDE so auditor knows what alternatives exist
    slide_type_guide = ""
    try:
        from inkline.intelligence.design_advisor import SLIDE_TYPE_GUIDE
        slide_type_guide = SLIDE_TYPE_GUIDE
    except Exception:
        pass

    # Load learned patterns for this brand
    pattern_context = ""
    if brand:
        try:
            from inkline.intelligence.pattern_memory import format_patterns_for_prompt
            pattern_context = format_patterns_for_prompt(brand)
        except Exception:
            pass

    # Narrative fidelity instruction — injected into criterion 15
    if source_text:
        narrative_instruction = (
            f"Source content for this slide is provided below. Verify:\n"
            f"   a) The slide title states the KEY INSIGHT from the source (action title), "
            f"not just the topic.\n"
            f"   b) The exhibit (chart/table/infographic) visually proves the claim in the title.\n"
            f"   c) Key facts and figures from the source appear correctly on the slide.\n"
            f"   d) No important points from the source are missing or misrepresented.\n"
            f"   Flag: title contradicts source → ERROR. Missing key insight → WARN. "
            f"Exhibit doesn't support the claim → WARN. Always include a proposed_redesign "
            f"for narrative findings.\n\n"
            f"SOURCE CONTENT:\n{source_text[:2000]}"
        )
    else:
        narrative_instruction = (
            "No source content provided. Skip this check."
        )

    from inkline.intelligence.vishwakarma import VISHWAKARMA_AUDIT_CRITERIA

    return f"""You are Inkline's Visual Auditor — an expert graphic designer reviewing \
rendered slide images before a deck ships to investors.

{VISHWAKARMA_AUDIT_CRITERIA}

You evaluate slides against TWO standards:

A. MECHANICAL QUALITY (errors that break the slide)
B. DESIGN QUALITY (professional presentation design principles)

====================================================================
A. MECHANICAL QUALITY CHECKS
====================================================================

1. CLIPPING — text, chart labels, axis ticks, legends, or icons cut off \
at the edge of the slide or any container. Always ERROR.

2. OVERFLOW — content that has pushed onto a second page, leaving the slide \
visually incomplete. Always ERROR.

3. OVERLAP — legends on plots, text on text, icons on borders. ERROR.

4. MISSING CONTENT — slide title promises N items but fewer are shown \
(e.g., "8-agent mesh" but only 6 rows visible). ERROR.

====================================================================
B. DESIGN QUALITY CHECKS (consulting-grade standard)
====================================================================

5. WHITESPACE & PROPORTIONS — Is the slide using space efficiently? \
Flag: massive empty areas below compact content, charts that are too \
small for their container, narrow panels that waste vertical space. \
A chart_caption layout should have the chart filling 60-65%% of width \
and the full available height. Cards should fill their row height. WARN.

6. VISUAL HIERARCHY — Is the main message immediately clear? The title \
should state the insight (action title), not the topic. Hero numbers \
should dominate. The eye should be guided: title → exhibit → supporting \
text. Flag slides where nothing stands out. WARN.

7. CARD/BOX CONSISTENCY — In three_card, four_card, and feature_grid \
layouts: ALL cards/boxes MUST be the same height. Uneven card heights \
look unprofessional. The tallest card sets the standard. WARN if uneven.

8. BRAND DISCIPLINE — A branded deck uses a 2-3 colour system. Flag:
   - Numbered badges/icons using multiple colours (should be single accent)
   - Stats in a strip using different accent colours
   - Progress bars in different colours
   WARN. But do NOT flag: donut shades, 2-3 series comparisons, semantic colours.

9. DATA VISUALISATION QUALITY — For charts:
   - Is the key data point or company highlighted/differentiated? (e.g., in a \
     competitive landscape, the client's position should stand out via colour, \
     size, or annotation)
   - Are axis labels readable? Are they present?
   - Does the chart type match the data? (scatter for positioning, bar for \
     comparison, line for trends, donut for composition)
   WARN if the chart fails to communicate its message clearly.

10. INFOGRAPHIC > TABLE — Flag any slide that uses a plain table when an \
infographic layout would be more effective. Tables are for dense reference \
data. For 3-5 items with value/description, prefer icon_stat, process_flow, \
timeline, or bar_chart. WARN.

11. TYPOGRAPHY — Consistent font sizes, weights, families within a slide. \
Title should be bold and large. Body text should be readable (≥10pt). WARN.

12. AXIS ELIMINATION — For bar charts, waterfall, and donut charts: if the \
slide shows both axis labels AND direct value labels on every bar/segment, \
the axis is redundant. Flag as WARN with suggestion to drop the axis. \
Exception: keep axes on multi-series line charts and scatter plots.

13. LEGEND NECESSITY — If a donut, pie, or bar chart has a separate legend \
box AND the segments/bars are large enough to hold embedded labels, flag as \
WARN. Embedded labels (on the arc, above the bar, inside the segment) are \
always preferred over a detached legend box.

14. INSIGHT TITLE — If the slide title is a neutral topic label (e.g., \
"Revenue Overview", "Market Data", "Financials") rather than an action title \
stating the analytical conclusion, flag as WARN. A professional action title \
states the insight: "Revenue grew 34%% YoY driven by enterprise segment". \
Exception: title slides and section dividers are exempt.

15. NARRATIVE FIDELITY — {narrative_instruction}

16. STORYTELLING SHARPNESS — Does this slide tell a clear story or just \
display data? Ask: "What is the ONE thing a viewer should remember from \
this slide?" If the answer isn't immediately obvious from the slide, flag \
as WARN. Criteria for sharp storytelling:
   - The title is the conclusion, not the topic
   - The exhibit (chart/table/infographic) is chosen to PROVE the title claim
   - Supporting text amplifies the insight, not repeats it
   - Numbers are formatted for impact (e.g. "$3.2B" not "3,200,000,000")
   Flag: slide that shows lots of data with no clear hero message. WARN.

17. WOW FACTOR — Rate the overall visual impact on a 1-5 scale:
   5 = Boardroom-ready. Would look at home in a McKinsey deck.
   4 = Professional and clean. Minor improvement opportunities.
   3 = Adequate. Conveys information but unremarkable.
   2 = Needs work. Too dense, too sparse, or visually confusing.
   1 = Broken or unfit for presentation.
   If rated 1-2: flag as WARN with "wow_factor" category and specific fix.
   If rated 5: include as a "positive" finding to confirm quality.

18. POSITIVE — If the slide is well-designed, return []. Don't flag issues \
that aren't there.

====================================================================
DESIGN KNOWLEDGE (from playbooks — same as DesignAdvisor)
====================================================================

{playbook_context}

====================================================================
AVAILABLE SLIDE TYPES (for redesign proposals)
====================================================================

{slide_type_guide}

{pattern_context}

====================================================================
OUTPUT FORMAT — STRUCTURED PROPOSALS
====================================================================

Return a JSON array of findings. Each finding has:
  {{
    "severity": "error|warn|info",
    "category": "clipping|overflow|overlap|missing_content|whitespace|hierarchy|card_consistency|brand|data_viz|layout_change|typography|narrative|storytelling|wow_factor|positive",
    "message": "<what's wrong and how to fix>",
    "proposed_redesign": null or {{"slide_type": "...", "data": {{...}}}}
  }}

IMPORTANT: For "layout_change" and "narrative" findings, include a
"proposed_redesign" with a COMPLETE slide spec using the recommended type.
Use the SLIDE TYPE CATALOGUE above to construct valid data schemas.

Output ONLY the JSON array. No prose, no markdown, no commentary.
Return [] for a well-designed slide."""


_VISUAL_AUDIT_SYSTEM = _build_visual_audit_system()  # default (no brand)


def audit_slide_with_llm(
    image_path: str | Path,
    *,
    slide_index: int = -1,
    slide_type: str = "",
    slide_data: dict | None = None,
    source_text: str = "",
    brand: str = "",
    api_key: str | None = None,
    model: str = "claude-sonnet-4-6",
    bridge_url: str = "http://localhost:8082",
) -> list[AuditWarning]:
    """Send a rendered slide PNG to Claude and ask for a visual audit.

    Routing order:
    1. LLM bridge ``/vision`` endpoint (Claude Max — zero API cost)
    2. Anthropic SDK with explicitly supplied ``api_key`` (paid fallback)

    IMPORTANT: ``api_key`` is never auto-read from ``ANTHROPIC_API_KEY`` env.
    Pass it explicitly only if you want to permit API fallback. Without it,
    if the bridge is also unavailable, the call is skipped cleanly.

    Parameters
    ----------
    source_text : str, optional
        The source content this slide is supposed to convey. When provided,
        the auditor checks narrative fidelity — whether the slide accurately
        and compellingly represents the key insight from the source.
    """
    image_path = Path(image_path)
    if not image_path.exists():
        return []

    try:
        import base64
        import json as _json
    except ImportError:
        return []

    img_b64 = base64.standard_b64encode(image_path.read_bytes()).decode("utf-8")

    # Build system prompt — always include brand + source_text for narrative fidelity
    system_prompt = (
        _build_visual_audit_system(brand, source_text)
        if (brand or source_text)
        else _VISUAL_AUDIT_SYSTEM
    )

    # Include slide data context so auditor knows what content was intended
    data_context = ""
    if slide_data:
        data_context = (
            f"\n\nOriginal slide data (what was INTENDED to render):\n"
            f"```json\n{_json.dumps(slide_data, indent=2, default=str)[:800]}\n```\n\n"
            f"CRITICAL: Compare the rendered image against the intended data above.\n"
            f"- If the data specifies different sizes (e.g., size: 40 vs size: 130), "
            f"verify the rendered elements are VISUALLY different sizes.\n"
            f"- If the data specifies N items, verify N items are visible.\n"
            f"- If values/numbers in the data don't match what's rendered, flag as ERROR.\n"
            f"- If elements that should be visually distinct (different sizes, colours, "
            f"emphasis) render as identical, flag as ERROR."
        )

    user_text = (
        f"Audit this rendered slide image (slide_index={slide_index}, "
        f"slide_type='{slide_type}').{data_context}\n\n"
        f"Return JSON array of findings. For layout_change suggestions, "
        f"include a proposed_redesign with a complete slide spec."
    )

    text = None

    # --- 1. Try bridge /vision (Claude Max, zero API cost) ---
    try:
        import requests as _req
        resp = _req.post(
            f"{bridge_url}/vision",
            json={
                "prompt": user_text,
                "system": system_prompt,
                "image_base64": img_b64,
                "image_media_type": "image/png",
            },
            timeout=(1, 120),  # 1s connect, 120s read
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("response"):
                text = data["response"]
    except Exception:
        pass

    # --- 2. Anthropic SDK fallback (only if explicitly supplied api_key) ---
    if text is None:
        if not api_key:
            return [AuditWarning(
                slide_index=slide_index, slide_type=slide_type,
                severity="info",
                message="LLM visual audit skipped: bridge unavailable and no api_key supplied",
            )]
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                model=model,
                max_tokens=2048,
                system=system_prompt,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": img_b64,
                            },
                        },
                        {"type": "text", "text": user_text},
                    ],
                }],
            )
            text = response.content[0].text.strip()
        except Exception as e:
            return [AuditWarning(
                slide_index=slide_index, slide_type=slide_type,
                severity="info",
                message=f"LLM visual audit skipped: {str(e)[:80]}",
            )]

    text = (text or "").strip()
    # Strip markdown fences if present
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

    try:
        findings = json.loads(text)
    except json.JSONDecodeError:
        return []

    if not isinstance(findings, list):
        return []

    warnings: list[AuditWarning] = []
    for f in findings:
        if not isinstance(f, dict):
            continue
        sev = f.get("severity", "info")
        msg = f.get("message", "")
        if sev not in ("error", "warn", "info"):
            sev = "warn"
        if msg:
            warnings.append(AuditWarning(
                slide_index=slide_index,
                slide_type=slide_type,
                severity=sev,
                message=msg,
            ))
    return warnings


def audit_deck_with_llm(
    pdf_path: str | Path,
    slides: list[dict],
    *,
    brand: str = "",
    source_narrative: str = "",
    api_key: str | None = None,
    model: str = "claude-sonnet-4-6",
    page_dir: str | Path | None = None,
    bridge_url: str = "http://localhost:8082",
) -> list[AuditWarning]:
    """Render each PDF page to PNG and run LLM visual audit on each.

    Tries the LLM bridge ``/vision`` endpoint first (Claude Max, free).
    Falls back to Anthropic SDK only if ``api_key`` is explicitly supplied.
    Never auto-reads ANTHROPIC_API_KEY from the environment.

    Uses pymupdf if available (fast), else falls back to recompiling the
    Typst source via typst.compile(format='png').

    Parameters
    ----------
    source_narrative : str, optional
        The source document or report content the deck is summarising.
        When provided, each slide audit includes a narrative fidelity check:
        does this slide accurately and compellingly convey the key insight
        from the source? Per-slide source can also be embedded in
        ``slide["data"]["source_section"]`` — that takes precedence.
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        return []

    # Render PDF pages to PNGs in a temp/output dir
    if page_dir is None:
        page_dir = pdf_path.parent / f"_audit_{pdf_path.stem}"
    page_dir = Path(page_dir)
    page_dir.mkdir(parents=True, exist_ok=True)

    page_pngs = _render_pdf_pages(pdf_path, page_dir)
    if not page_pngs:
        return []

    # Only audit pages that correspond to actual slides — overflow pages
    # beyond len(slides) are structural artifacts, not real slides, and
    # auditing them wastes API calls.
    audit_pngs = page_pngs[:len(slides)]

    # Audit slides in parallel — each slide is an independent vision call.
    # max_workers=5: enough to saturate the bridge's throughput without
    # overwhelming it (bridge may serialize internally anyway, but concurrent
    # connections prevent head-of-line blocking on slow slides).
    from concurrent.futures import ThreadPoolExecutor, as_completed

    def _audit_one(i: int, png: Path) -> tuple[int, list[AuditWarning]]:
        slide_type = slides[i].get("slide_type", "?") if i < len(slides) else "?"
        slide_data = slides[i].get("data", {}) if i < len(slides) else {}
        slide_source = slide_data.get("source_section", "") or source_narrative
        page_warnings = audit_slide_with_llm(
            png,
            slide_index=i + 1,
            slide_type=slide_type,
            slide_data=slide_data,
            source_text=slide_source,
            brand=brand,
            api_key=api_key,
            model=model,
            bridge_url=bridge_url,
        )
        return (i, page_warnings)

    results: dict[int, list[AuditWarning]] = {}
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = {pool.submit(_audit_one, i, png): i for i, png in enumerate(audit_pngs)}
        for future in as_completed(futures):
            try:
                idx, page_warnings = future.result()
                results[idx] = page_warnings
                log.info("Archon audit: slide %d/%d done (%d warnings)",
                         idx + 1, len(audit_pngs), len(page_warnings))
            except Exception as e:
                idx = futures[future]
                log.warning("Archon audit: slide %d failed: %s", idx + 1, e)
                results[idx] = []

    # Flatten in slide order
    warnings: list[AuditWarning] = []
    for i in range(len(audit_pngs)):
        warnings.extend(results.get(i, []))

    return warnings


def _render_pdf_pages(pdf_path: Path, out_dir: Path) -> list[Path]:
    """Render PDF pages to PNGs. Tries pymupdf, then falls back to nothing."""
    # Try pymupdf (fitz)
    try:
        import fitz  # pymupdf
        doc = fitz.open(str(pdf_path))
        pages = []
        for i, page in enumerate(doc):
            pix = page.get_pixmap(dpi=120)
            png_path = out_dir / f"page_{i+1:02d}.png"
            pix.save(str(png_path))
            pages.append(png_path)
        doc.close()
        return pages
    except ImportError:
        pass
    except Exception:
        return []

    # No PDF→PNG library available
    return []


def extract_page_texts(pdf_path: Path) -> list[str]:
    """Extract text content from each page of a PDF.

    Returns list of strings, one per page. Empty list if no PDF reader.
    """
    try:
        import fitz
        doc = fitz.open(str(pdf_path))
        texts = [page.get_text() for page in doc]
        doc.close()
        return texts
    except ImportError:
        pass
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(pdf_path))
        return [page.extract_text() or "" for page in reader.pages]
    except ImportError:
        pass
    return []


def _count_pdf_pages(pdf_path: Path) -> int | None:
    """Count pages in a PDF. Returns None if no PDF library available."""
    # Try pypdf first
    try:
        from pypdf import PdfReader
        return len(PdfReader(str(pdf_path)).pages)
    except ImportError:
        pass
    # Try pdfplumber
    try:
        import pdfplumber
        with pdfplumber.open(str(pdf_path)) as pdf:
            return len(pdf.pages)
    except ImportError:
        pass
    # Try PyPDF2
    try:
        from PyPDF2 import PdfReader
        return len(PdfReader(str(pdf_path)).pages)
    except ImportError:
        pass
    return None


def emit_audit_report(warnings: list[AuditWarning]) -> None:
    """Print audit report directly to stderr — visible without logging config.

    This is the user-facing audit. Logging warnings get swallowed by default;
    stderr prints are always visible.
    """
    if not warnings:
        return

    import sys
    errors = [w for w in warnings if w.severity == "error"]
    warns = [w for w in warnings if w.severity == "warn"]
    infos = [w for w in warnings if w.severity == "info"]

    bar = "=" * 76
    print("", file=sys.stderr)
    print(bar, file=sys.stderr)
    print(
        f" INKLINE AUDIT  ·  {len(errors)} errors  ·  {len(warns)} warnings  ·  {len(infos)} info",
        file=sys.stderr,
    )
    print(bar, file=sys.stderr)
    for w in errors + warns + infos:
        print(f"  {w}", file=sys.stderr)
    print(bar, file=sys.stderr)
    print("", file=sys.stderr)
