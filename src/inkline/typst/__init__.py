"""Typst output backend — slides (16:9 PDF) and documents (A4/Letter PDF).

This is Inkline's default output engine. It produces publication-quality
PDFs with embedded fonts via the Typst compiler.

Usage::

    from inkline.typst import export_typst_slides, export_typst_document

    # Slides from structured data
    export_typst_slides(
        slides=[
            {"slide_type": "title", "data": {"company": "Acme Corp", ...}},
            {"slide_type": "three_card", "data": {"section": "Problem", ...}},
        ],
        output_path="deck.pdf",
        brand="minimal",
        template="consulting",
    )

    # Document from Markdown
    export_typst_document(
        markdown="# Due Diligence Report\\n...",
        output_path="report.pdf",
        brand="minimal",
        title="DD Report",
    )
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

log = logging.getLogger(__name__)

_ASSETS_DIR = Path(__file__).parent.parent / "assets"
_FONTS_DIR = _ASSETS_DIR / "fonts"


def _verify_page_count(pdf_path: Path, expected: int) -> None:
    """Hard gate: verify rendered PDF has exactly the expected number of pages.

    If the page count doesn't match, content has overflowed onto extra pages.
    This logs a loud warning with details so the caller knows which slides
    overflowed. Does not raise — the PDF is still usable, but the caller
    should inspect and fix.
    """
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(str(pdf_path))
        actual = len(doc)
        doc.close()
    except ImportError:
        try:
            from pypdf import PdfReader
            actual = len(PdfReader(str(pdf_path)).pages)
        except ImportError:
            log.debug("No PDF reader available for page count verification")
            return

    if actual != expected:
        overflow = actual - expected
        import sys
        msg = (
            f"\n{'='*72}\n"
            f" INKLINE OVERFLOW GATE  |  {actual} pages rendered, {expected} expected\n"
            f" {overflow} slide(s) overflowed onto extra pages.\n"
            f" The PDF has been written but contains layout overflow.\n"
            f" Fix: reduce content, shorten titles, or split slides.\n"
            f"{'='*72}\n"
        )
        print(msg, file=sys.stderr)
        log.error("Page count mismatch: %d pages for %d slides", actual, expected)


def _auto_render_charts(
    slides: list[dict[str, Any]],
    brand: str,
    root: str,
) -> None:
    """Auto-render chart images requested via chart_request in slide data.

    When DesignAdvisor (LLM mode) picks a chart/chart_caption/dashboard slide,
    it embeds a ``chart_request`` dict with ``chart_type`` and ``chart_data``.
    This function renders those charts via matplotlib before Typst compilation,
    so the image files exist when the compiler needs them.
    """
    # Collect charts to render from all slide types:
    # - Top-level data.chart_request (chart/chart_caption/dashboard slides)
    # - Nested data.charts[i].chart_request (multi_chart slides)
    # Each entry: (slide, chart_entry_or_None, chart_req, full_path, chart_index)
    # chart_entry_or_None: the specific chart dict within data.charts[], or None for top-level
    # chart_index: position within data.charts[] (for multi_chart slot size lookup)
    charts_to_render = []
    for slide in slides:
        data = slide.get("data", {})
        # Top-level chart_request
        chart_req = data.get("chart_request")
        image_path = data.get("image_path")
        if chart_req and image_path:
            full_path = Path(root) / image_path
            if not full_path.exists():
                charts_to_render.append((slide, None, chart_req, full_path, 0))
        # Nested chart_requests inside multi_chart slides
        for chart_idx, chart_entry in enumerate(data.get("charts", [])):
            c_req = chart_entry.get("chart_request")
            c_path = chart_entry.get("image_path")
            if c_req and c_path:
                full_path = Path(root) / c_path
                if not full_path.exists():
                    charts_to_render.append((slide, chart_entry, c_req, full_path, chart_idx))
        # orbital / halo: hero chart_request + overlay chart_requests
        if slide.get("slide_type") in ("orbital", "halo"):
            hero = data.get("hero", {})
            h_req = hero.get("chart_request")
            h_path = hero.get("image_path")
            if h_req and h_path:
                full_path = Path(root) / "charts" / h_path
                if not full_path.exists():
                    # Use a sentinel chart_idx so the render loop picks orbital hero size
                    charts_to_render.append((slide, None, h_req, full_path, -2))
            for ov_idx, ov_entry in enumerate(data.get("overlays", [])):
                ov_req = ov_entry.get("chart_request")
                ov_path = ov_entry.get("image_path")
                if ov_req and ov_path:
                    full_path = Path(root) / "charts" / ov_path
                    if not full_path.exists():
                        charts_to_render.append((slide, ov_entry, ov_req, full_path, -1))

    if not charts_to_render:
        return

    # Verify matplotlib is available before entering the render loop
    try:
        import matplotlib  # noqa: F401
    except ImportError:
        log.warning("matplotlib not available — cannot auto-render %d chart(s)", len(charts_to_render))
        return

    # Base sizes for non-multi_chart slide types (in inches)
    _CHART_SIZES = {
        "chart_caption": (7.0, 3.0),
        "dashboard": (6.5, 3.4),
        "chart": (9.0, 4.5),
    }
    _DEFAULT_SIZE = (7.0, 3.5)
    # Orbital/halo hero: slide body is ~33.87cm wide × 8.31cm tall → ~13.3" × 3.27"
    # Matching the 4:1 aspect ratio fills the full width with no blank horizontal band.
    _ORBITAL_HERO_SIZE = (13.3, 3.27)

    for slide, chart_entry, chart_req, full_path, chart_idx in charts_to_render:
        chart_type = chart_req.get("chart_type", "")
        chart_data = chart_req.get("chart_data", {})
        if not chart_type or not chart_data:
            log.warning("Skipping chart_request with missing type or data: %s", full_path.name)
            continue

        if chart_idx == -2:
            # Orbital / halo hero chart — wide aspect ratio to fill slide width
            w, h = _ORBITAL_HERO_SIZE
        elif chart_idx == -1:
            # Orbital / halo overlay chart — mini-chart size (4.5cm × 3.5cm)
            w, h = 4.5 / 2.54, 3.5 / 2.54  # ~1.77" × 1.38"
        elif slide["slide_type"] == "multi_chart":
            # Slot-based sizing: compute the exact cell dimensions for this layout
            # and chart position so the PNG fills the Typst slot with no letterboxing.
            try:
                from inkline.typst.slide_renderer import get_multi_chart_slot
                layout = slide.get("data", {}).get("layout", "equal_2")
                n_charts = len(slide.get("data", {}).get("charts", []))
                w_cm, h_cm = get_multi_chart_slot(layout, chart_idx, n_charts)
                w = w_cm / 2.54   # cm → inches
                h = h_cm / 2.54
            except Exception:
                w, h = _DEFAULT_SIZE
        else:
            w, h = _CHART_SIZES.get(slide["slide_type"], _DEFAULT_SIZE)

        full_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            from inkline.typst.chart_auditor import render_and_audit
            result = render_and_audit(
                chart_type, chart_data, full_path,
                brand_name=brand, width=w, height=h,
            )
            if result.redesign_needed:
                log.warning(
                    "Chart '%s' (%s) needs redesign after %d attempt(s): %s",
                    full_path.name, chart_type, result.attempts,
                    "; ".join(result.issues),
                )
                # Chart file still exists — keep it in the slide.
                # Archon will see the warning and can trigger a redesign pass.
            elif result.fix_applied:
                log.info(
                    "Chart '%s' (%s): programmatic fix applied, passed audit "
                    "in %d attempt(s)",
                    full_path.name, chart_type, result.attempts,
                )
            else:
                log.info(
                    "Chart '%s' (%s, %.2f\"×%.2f\"): audit passed",
                    full_path.name, chart_type, w, h,
                )
        except ImportError:
            # chart_auditor not importable (e.g. requests missing) — plain render
            try:
                from inkline.typst.chart_renderer import render_chart_for_brand
                render_chart_for_brand(
                    chart_type, chart_data, str(full_path),
                    brand_name=brand, width=w, height=h,
                )
                log.info(
                    "Auto-rendered chart: %s (%s, %.2f\"×%.2f\")",
                    full_path.name, chart_type, w, h,
                )
            except Exception as e:
                log.warning("Failed to render chart %s: %s", full_path.name, e)
                if chart_entry is not None:
                    chart_entry.pop("image_path", None)
                    chart_entry.pop("chart_request", None)
                else:
                    slide["data"].pop("image_path", None)
                    slide["data"].pop("chart_request", None)
        except Exception as e:
            log.warning("Failed to render/audit chart %s: %s", full_path.name, e)
            # If no chart file was produced, remove the reference so the slide degrades
            if not full_path.exists():
                if chart_entry is not None:
                    chart_entry.pop("image_path", None)
                    chart_entry.pop("chart_request", None)
                else:
                    slide["data"].pop("image_path", None)
                    slide["data"].pop("chart_request", None)


def _degrade_placeholder_slides(slides: list, root: str) -> list:
    """Convert any slides with missing chart images to text-based equivalents.

    Called after _auto_render_charts. If a chart slot still has no image file,
    we cannot show a meaningful chart — degrade the slide rather than show a
    grey "Chart not available" placeholder to the user.

    Degradation strategy by slide type:
    - multi_chart: remove chart entries that have no image; if ALL charts
      are missing, convert the whole slide to a content slide using the
      footnote/title as narrative.
    - chart / chart_caption / dashboard: if top-level image missing, convert
      to a content slide with any available bullets/narrative.
    """
    from pathlib import Path
    root_path = Path(root)
    result = []

    for slide in slides:
        slide_type = slide.get("slide_type", "")
        data = dict(slide.get("data", {}))

        if slide_type == "multi_chart":
            charts = data.get("charts", [])
            # Keep only charts that have a real image on disk (check root/ and root/charts/)
            good_charts = [
                c for c in charts
                if c.get("image_path") and (
                    (root_path / c["image_path"]).exists()
                    or (root_path / "charts" / c["image_path"]).exists()
                )
            ]
            bad_count = len(charts) - len(good_charts)

            if bad_count == 0:
                result.append(slide)  # All good
            elif len(good_charts) == 0:
                # All charts missing — convert entire slide to content slide
                log.warning(
                    "Degrading slide '%s' (multi_chart/%s) → content: all %d charts missing",
                    data.get("title", "?"), data.get("layout", "?"), len(charts),
                )
                # Build bullet points from chart titles as a narrative substitute
                bullets = [
                    c.get("title", c.get("image_path", "Chart unavailable"))
                    for c in charts if c.get("title") or c.get("image_path")
                ]
                result.append({
                    "slide_type": "content",
                    "data": {
                        "section": data.get("section", ""),
                        "title": data.get("title", ""),
                        "items": bullets[:8],
                        "footnote": data.get("footnote", ""),
                    },
                })
            else:
                # Some charts present — keep the good ones, adjust layout
                log.warning(
                    "Slide '%s' (multi_chart/%s): %d/%d charts missing, keeping %d",
                    data.get("title", "?"), data.get("layout", "?"),
                    bad_count, len(charts), len(good_charts),
                )
                # Adjust layout to match remaining chart count
                n = len(good_charts)
                layout_map = {1: "equal_2", 2: "equal_2", 3: "equal_3", 4: "quad"}
                new_data = dict(data)
                new_data["charts"] = good_charts
                new_data["layout"] = layout_map.get(n, "equal_2")
                result.append({"slide_type": "multi_chart", "data": new_data})

        elif slide_type in ("chart", "chart_caption", "dashboard"):
            image_path = data.get("image_path", "")
            # Check both root/ and root/charts/ so callers don't need to
            # include the "charts/" prefix in image_path.
            image_found = (
                not image_path
                or (root_path / image_path).exists()
                or (root_path / "charts" / image_path).exists()
            )
            if image_path and not image_found:
                # Convert to content slide with available narrative
                log.warning(
                    "Degrading slide '%s' (%s) → content: image '%s' missing",
                    data.get("title", "?"), slide_type, image_path,
                )
                bullets = data.get("bullets", []) or data.get("items", [])
                caption = data.get("caption", "")
                if caption:
                    bullets = [caption] + list(bullets)
                result.append({
                    "slide_type": "content",
                    "data": {
                        "section": data.get("section", ""),
                        "title": data.get("title", ""),
                        "items": bullets[:8],
                        "footnote": data.get("footnote", ""),
                    },
                })
            else:
                result.append(slide)

        else:
            result.append(slide)

    return result


def _preflight_images(slides: list, root: str) -> None:
    """Validate image paths before rendering; log warnings for missing files.

    Slides with missing image_path are left as-is — the renderer will
    substitute a Typst-native placeholder at render time.

    Also counts how many chart slots still have placeholders after auto-render
    and emits a WARNING if > 0, so the issue is visible at summary level.
    """
    from pathlib import Path
    root_path = Path(root)
    image_slide_types = {"chart", "chart_caption", "dashboard"}
    placeholder_count = 0
    total_chart_slots = 0

    for slide in slides:
        data = slide.get("data", {})
        # Top-level image for chart/chart_caption/dashboard slides
        if slide.get("slide_type") in image_slide_types:
            image_path = data.get("image_path", "")
            if image_path:
                total_chart_slots += 1
                # Check both root/ and root/charts/ subdirectory
                full = root_path / image_path
                if not full.exists() and not (root_path / "charts" / image_path).exists():
                    placeholder_count += 1
                    log.warning(
                        "Pre-flight: image '%s' not found for %s slide — renderer will use placeholder",
                        image_path, slide["slide_type"],
                    )
        # Nested images in multi_chart slides
        for chart_entry in data.get("charts", []):
            image_path = chart_entry.get("image_path", "")
            if image_path:
                total_chart_slots += 1
                full = root_path / image_path
                if not full.exists() and not (root_path / "charts" / image_path).exists():
                    placeholder_count += 1
                    log.warning(
                        "Image not found, using placeholder: %s", image_path
                    )

    if placeholder_count > 0:
        log.warning(
            "Pre-flight: %d/%d chart slots will render as placeholders — "
            "check chart_request entries and auto-render coverage",
            placeholder_count, total_chart_slots,
        )


def export_typst_slides(
    slides: list[dict[str, Any]],
    output_path: str | Path,
    *,
    visual_brief: Optional[Any] = None,
    brand: str = "minimal",
    template: str = "brand",
    title: str = "Untitled",
    date: str = "",
    subtitle: str = "",
    font_paths: Optional[list[str | Path]] = None,
    image_root: Optional[str | Path] = None,
    source_narrative: str = "",
    audit: bool = True,
    auto_fix: bool = True,
    max_overflow_attempts: int = 6,
    max_visual_attempts: int = 5,
) -> Path:
    """Generate a slide deck PDF with closed-loop quality assurance.

    The pipeline runs two nested loops:
    - **Inner loop** (deterministic): fixes structural overflow until
      page count matches slide count.
    - **Outer loop** (LLM-driven): runs Claude vision audit on every slide,
      applies targeted fixes for ERROR findings, and re-renders until the
      visual auditor gives a clean pass.

    The visual audit is an integral part of the quality loop and always runs
    when ``audit=True``. There is no mechanism to disable it independently —
    if you don't want quality checking at all, pass ``audit=False``.

    Parameters
    ----------
    slides : list[dict]
        List of slide dicts, each with ``slide_type`` and ``data`` keys.
    output_path : Path
        Where to write the PDF.
    brand : str
        Brand name.
    template : str
        Slide template.
    title, date, subtitle : str
        Deck metadata.
    font_paths : list[Path], optional
        Additional font directories.
    image_root : Path, optional
        Root directory for image resolution.
    source_narrative : str, optional
        The source document or report text the deck is summarising.
        Passed to the visual auditor so it can check whether each slide
        faithfully conveys the key insight from the source (narrative
        fidelity). Per-slide source can also be embedded in
        ``slide["data"]["source_section"]``, which takes precedence.
    audit : bool
        Enable quality assurance loop (overflow detection + visual audit).
        Pass ``False`` only in tests or draft previews. Default: True.
    auto_fix : bool
        Enable closed-loop auto-fixing (default True).
    max_overflow_attempts : int
        Max inner loop iterations for structural overflow (default 3).
    max_visual_attempts : int
        Max outer loop iterations for visual quality (default 5).

    Returns
    -------
    Path
        Path to the generated PDF.
    """
    import shutil

    from inkline.brands import get_brand
    from inkline.typst.compiler import compile_typst
    from inkline.typst.slide_renderer import DeckSpec, SlideSpec, TypstSlideRenderer
    from inkline.typst.theme_registry import brand_to_typst_theme

    # === PHASE 0: Setup ===
    brand_obj = get_brand(brand)
    theme = brand_to_typst_theme(brand_obj, template)

    # Apply visual brief palette overrides if provided
    if visual_brief:
        if visual_brief.accent:
            theme["accent"] = visual_brief.accent
        if visual_brief.divider_bg:
            theme["title_bg"] = visual_brief.divider_bg  # section_divider uses title_bg

    output_path = Path(output_path)

    # Determine root for image resolution
    root = None
    if image_root:
        root = str(image_root)
    else:
        has_images = any(
            s.get("data", {}).get("image_path")
            or s.get("data", {}).get("hero", {}).get("image_path")
            or any(ov.get("image_path") for ov in s.get("data", {}).get("overlays", []))
            for s in slides
        )
        has_logo = bool(theme.get("logo_light_path"))
        if has_images or has_logo:
            root = str(output_path.parent)

    # Copy logo to output directory
    logo_path = theme.get("logo_light_path", "")
    if logo_path:
        logo_src = _ASSETS_DIR / logo_path
        if not logo_src.exists():
            import os
            brands_dir = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "inkline" / "assets"
            logo_src = brands_dir / logo_path
        if logo_src.exists():
            logo_target = output_path.parent / logo_path
            shutil.copy2(logo_src, logo_target)  # Always copy (may have changed)

    # Collect font paths
    all_font_paths = [str(_FONTS_DIR)]
    if font_paths:
        all_font_paths.extend(str(p) for p in font_paths)

    # === PHASE 0b: Taste enforcement (deterministic, before any rendering) ===
    try:
        from inkline.typst.taste_enforcer import TasteEnforcer
        slides = TasteEnforcer().apply(slides)
    except Exception as _te_err:
        log.debug("TasteEnforcer skipped: %s", _te_err)

    # === PHASE 1: Chart rendering (ONE TIME) ===
    _auto_render_charts(slides, brand, root or str(output_path.parent))

    # === PHASE 1b: Graceful degradation — convert any chart slide that still
    # has missing images into text-based content slides so NO placeholder
    # grey boxes reach the final PDF.
    slides = _degrade_placeholder_slides(slides, root or str(output_path.parent))

    # Chart audit
    pre_warnings: list = []
    if audit and auto_fix:
        try:
            from inkline.intelligence.slide_fixer import audit_charts
            chart_warnings = audit_charts(slides, root or str(output_path.parent), brand)
            pre_warnings.extend({"severity": w.get("severity", "info"), "message": w.get("issue", "")}
                                for w in chart_warnings if isinstance(w, dict))
        except Exception as e:
            log.debug("Chart audit skipped: %s", e)

    # === PHASE 2: Pre-render validation & auto-fix ===
    if auto_fix:
        try:
            from inkline.intelligence.slide_fixer import validate_and_fix_slides, equalise_card_heights
            slides, fix_log = validate_and_fix_slides(slides)
            slides = equalise_card_heights(slides)
            if fix_log:
                log.info("Pre-render fixer applied %d fixes", len(fix_log))
        except Exception as e:
            log.debug("Pre-render fixer skipped: %s", e)

    # === PHASE 2b: Pre-flight image validation ===
    _preflight_images(slides, root or str(output_path.parent))

    # === PHASE 3: Overflow fix loop (deterministic, NO LLM redesigns) ===
    # Only structural fixes here. Visual redesigns live in the Archon phase.
    # This prevents "overflow bouncing" where LLM redesigns create new overflows.
    all_warnings: list = list(pre_warnings)
    source = None

    def _render_and_compile(slides_list, source_str, force_rerender):
        """Helper: render Typst source from slides if needed, compile to PDF."""
        if force_rerender or source_str is None:
            deck = DeckSpec(
                slides=[SlideSpec(slide_type=s["slide_type"], data=s.get("data", {})) for s in slides_list],
                title=title, date=date, subtitle=subtitle,
            )
            renderer = TypstSlideRenderer(theme, image_root=root)
            source_str = renderer.render_deck(deck)
        try:
            compile_typst(source_str, output_path=output_path, root=root, font_paths=all_font_paths)
        except Exception as compile_err:
            # Save .typ source so the offending code can be inspected.
            debug_typ = output_path.with_suffix(".debug.typ")
            try:
                debug_typ.write_text(source_str, encoding="utf-8")
            except Exception:
                pass
            log.error(
                "Typst compile failed: %s  (source saved to %s)",
                compile_err, debug_typ,
            )
            raise
        return source_str

    overflow_attempt = 0
    needs_rerender = True
    prev_actual = None

    while overflow_attempt <= max_overflow_attempts:
        try:
            source = _render_and_compile(slides, source, needs_rerender)
        except Exception as e:
            if overflow_attempt == 0:
                # No PDF exists yet — surface to caller so the gen script can diagnose.
                raise
            # A subsequent overflow-fix compile failed; keep the previous PDF and
            # proceed to Phase 4 so the visual audit can still run.
            log.warning(
                "Overflow-fix compile failed (attempt %d) — keeping previous PDF: %s",
                overflow_attempt, e,
            )
            break
        actual = _count_pages(output_path)
        expected = len(slides)

        if actual == expected:
            break  # No overflow
        if actual == 0:
            log.debug("Page count unavailable (no PDF reader installed) — skipping overflow detection")
            break  # Can't detect overflow without a PDF reader

        # Anti-runaway: if page count grew since last attempt, fixes are
        # making things worse. Accept current state and move on.
        if prev_actual is not None and actual >= prev_actual:
            log.warning(
                "Overflow anti-runaway: page count grew %d→%d, stopping fix loop",
                prev_actual, actual,
            )
            _verify_page_count(output_path, expected)
            break
        prev_actual = actual

        if overflow_attempt >= max_overflow_attempts or not auto_fix:
            _verify_page_count(output_path, expected)
            break

        # Identify and fix overflow (deterministic fixer only)
        try:
            from inkline.intelligence.slide_fixer import (
                identify_overflow_slides, apply_graduated_fixes,
            )
            overflow_indices = identify_overflow_slides(output_path, slides, source)
            overflow_attempt += 1
            log.info("Overflow fix attempt %d: slides %s", overflow_attempt, overflow_indices)
            slides, source, needs_rerender = apply_graduated_fixes(
                slides, source, overflow_indices, overflow_attempt, theme,
            )
        except Exception as e:
            log.warning("Overflow fix failed: %s", e)
            break

    # === PHASE 4: Archon closed-loop review (audit → fix → re-audit, max N passes) ===
    # Full quality gate: visual fidelity, narrative fidelity, storytelling
    # quality, and commercial viability. Wrapped in an outer loop that:
    #   1. Runs the audit
    #   2. Exits on clean pass
    #   3. On errors: applies revision + re-renders + re-audits
    #   4. Exits if a pass made no changes (nothing more we can fix)
    #   5. Otherwise continues until max_visual_attempts is reached.
    if audit:
        try:
            from inkline.intelligence.overflow_audit import (
                audit_rendered_pdf, audit_chart_image,
                audit_deck_with_llm,
            )
        except ImportError:
            log.debug("overflow_audit not available — skipping Archon review")
            audit = False

    if audit:
        visual_attempt = 0
        archon_passed_clean = False
        archon_last_error_count = None

        while visual_attempt <= max_visual_attempts:
            # Re-identify persistent overflow (structural info for Archon)
            persistent_overflow_indices: list[int] = []
            final_actual = _count_pages(output_path)
            if 0 < final_actual != len(slides):
                try:
                    from inkline.intelligence.slide_fixer import identify_overflow_slides
                    persistent_overflow_indices = identify_overflow_slides(output_path, slides, source or "")
                    log.info("Archon: persistent overflow slides %s", persistent_overflow_indices)
                except Exception:
                    pass

            post_warnings = audit_rendered_pdf(output_path, expected_slides=len(slides))

            # Inject per-slide overflow errors so Archon knows which slides to redesign
            if persistent_overflow_indices:
                try:
                    from inkline.intelligence.overflow_audit import AuditWarning
                    for idx in persistent_overflow_indices:
                        if idx < len(slides):
                            stype = slides[idx].get("slide_type", "unknown")
                            stitle = slides[idx].get("data", {}).get("title", "")[:50]
                            post_warnings.append(AuditWarning(
                                slide_index=idx + 1,
                                slide_type=stype,
                                severity="error",
                                message=(
                                    f"Slide {idx + 1} ({stype}: '{stitle}') overflows onto an extra page. "
                                    f"Replace with a simpler slide type (content/split/three_card) "
                                    f"or reduce the number of items."
                                ),
                            ))
                except Exception:
                    pass

            # Chart image clipping audit
            seen_images: set = set()
            for s in slides:
                img = s.get("data", {}).get("image_path")
                if img and img not in seen_images:
                    seen_images.add(img)
                    img_path = Path(root or str(output_path.parent)) / img
                    if img_path.exists():
                        post_warnings.extend(audit_chart_image(img_path))

            # --- Archon visual + narrative audit (parallel per-slide) ---
            log.info(
                "Archon review pass %d/%d: auditing %d slides (parallel vision calls)...",
                visual_attempt + 1, max_visual_attempts + 1, len(slides),
            )
            llm_warnings = audit_deck_with_llm(
                output_path, slides, brand=brand, source_narrative=source_narrative,
                overflow_slide_indices=persistent_overflow_indices,
            )
            post_warnings.extend(llm_warnings)
            all_warnings.extend(post_warnings)

            # Collect actionable errors
            llm_errors = [w for w in llm_warnings if w.severity == "error"]
            structural_errors = [
                w for w in post_warnings
                if getattr(w, "severity", "") == "error" and w not in llm_warnings
            ]
            actionable = llm_errors + structural_errors

            # Exit 1 — CLEAN PASS
            if not actionable:
                archon_passed_clean = True
                log.info(
                    "Archon review PASSED (clean) after %d fix pass(es) — deck is ready",
                    visual_attempt,
                )
                break

            # Exit 2 — auto_fix disabled
            if not auto_fix:
                log.info(
                    "Archon review: %d errors found (auto_fix=False, shipping as-is)",
                    len(actionable),
                )
                break

            # Exit 3 — reached the iteration ceiling; ship whatever we have
            if visual_attempt >= max_visual_attempts:
                log.warning(
                    "Archon review: max_visual_attempts=%d reached with %d errors remaining — shipping",
                    max_visual_attempts, len(actionable),
                )
                break

            # --- Attempt a targeted revision and re-render ---
            log.info(
                "Archon pass %d: %d errors found — applying targeted revision",
                visual_attempt + 1, len(actionable),
            )
            revision_changed_something = False
            try:
                from inkline.intelligence.design_advisor import DesignAdvisor
                advisor = DesignAdvisor(brand=brand, template=template, mode="llm")
                source_sections = (
                    [{"narrative": source_narrative}] if source_narrative else None
                )
                revised = advisor.revise_slides_from_review(
                    slides, actionable, original_sections=source_sections,
                )
                if revised != slides:
                    slides = revised
                    _auto_render_charts(slides, brand, root or str(output_path.parent))
                    slides = _degrade_placeholder_slides(slides, root or str(output_path.parent))
                    # Re-render and recompile so the next audit sees the fix
                    source = None
                    source = _render_and_compile(slides, source, True)
                    log.info("Archon pass %d: revision applied — deck re-rendered", visual_attempt + 1)
                    revision_changed_something = True
                else:
                    # DesignAdvisor made no structural change — try deterministic fixer
                    from inkline.intelligence.slide_fixer import fix_from_llm_findings
                    slides, applied = fix_from_llm_findings(slides, actionable)
                    if applied:
                        source = None
                        source = _render_and_compile(slides, source, True)
                        log.info(
                            "Archon pass %d: fixer applied %d fixes — deck re-rendered",
                            visual_attempt + 1, len(applied),
                        )
                        revision_changed_something = True
                    else:
                        log.info(
                            "Archon pass %d: no actionable changes possible — exiting loop",
                            visual_attempt + 1,
                        )
            except Exception as e:
                log.warning(
                    "Archon pass %d: revision failed: %s — exiting loop",
                    visual_attempt + 1, e,
                )

            # Exit 4 — this pass made no changes: further loops would repeat the same work
            if not revision_changed_something:
                break

            # Additional guard: if error count did not decrease across passes,
            # we're likely looping on uncorrectable findings — bail out early.
            if archon_last_error_count is not None and len(actionable) >= archon_last_error_count:
                log.info(
                    "Archon pass %d: error count did not decrease (%d → %d) — exiting loop",
                    visual_attempt + 1, archon_last_error_count, len(actionable),
                )
                # We still advance — we'll re-audit once more to confirm improvement or exit.
            archon_last_error_count = len(actionable)

            visual_attempt += 1

        # Final summary line — always emitted so callers can see how the loop resolved
        log.info(
            "Archon closed-loop result: %d revision pass(es), clean_pass=%s",
            visual_attempt, archon_passed_clean,
        )

    # === PHASE 4: Final report ===
    if all_warnings:
        try:
            from inkline.intelligence.overflow_audit import emit_audit_report, AuditWarning
            # Convert any raw dicts to AuditWarning objects
            typed_warnings = []
            for w in all_warnings:
                if isinstance(w, AuditWarning):
                    typed_warnings.append(w)
            if typed_warnings:
                emit_audit_report(typed_warnings)
        except Exception:
            pass

    # === PHASE 5: Zero-placeholder gate ===
    # Scan the rendered PDF for "Chart not available" text.
    # Any occurrence means a grey placeholder reached the final output — hard fail.
    _assert_no_placeholders(output_path)

    log.info("Typst slide deck written to %s", output_path)
    return output_path


def _assert_no_placeholders(pdf_path: Path) -> None:
    """Scan the compiled PDF for placeholder text. Raise if any found.

    A grey "Chart not available" box in the output means chart rendering failed
    AND graceful degradation also failed — the slide is unfit for presentation.
    This is a hard failure: the PDF exists but should NOT be sent to the user.
    """
    try:
        import fitz
    except ImportError:
        return  # Can't check without pymupdf; log and move on
    try:
        doc = fitz.open(str(pdf_path))
        placeholder_pages = []
        for page_num in range(len(doc)):
            text = doc[page_num].get_text()
            if "Chart not available" in text:
                placeholder_pages.append(page_num + 1)
        doc.close()
        if placeholder_pages:
            log.error(
                "PLACEHOLDER GATE: %d page(s) contain 'Chart not available' placeholder(s): %s. "
                "The PDF has been written but is NOT ready for the user. "
                "Fix chart rendering or ensure graceful degradation ran correctly.",
                len(placeholder_pages), placeholder_pages,
            )
    except Exception as e:
        log.debug("Placeholder gate check failed: %s", e)


def _count_pages(pdf_path: Path) -> int:
    """Count pages in a PDF. Returns 0 if no reader available."""
    try:
        import fitz
        doc = fitz.open(str(pdf_path))
        n = len(doc)
        doc.close()
        return n
    except ImportError:
        pass
    try:
        from pypdf import PdfReader
        return len(PdfReader(str(pdf_path)).pages)
    except ImportError:
        pass
    return 0


def export_typst_document(
    markdown: str,
    output_path: str | Path,
    *,
    brand: str = "minimal",
    title: str = "",
    subtitle: str = "",
    date: Optional[str | datetime] = None,
    author: str = "",
    paper: str = "a4",
    sections: Optional[list[dict[str, Any]]] = None,
    font_paths: Optional[list[str | Path]] = None,
) -> Path:
    """Generate a branded document PDF from Markdown or structured sections.

    Parameters
    ----------
    markdown : str
        Markdown content. Ignored if ``sections`` is provided.
    output_path : Path
        Where to write the PDF.
    brand : str
        Brand name.
    title : str
        Document title.
    subtitle : str
        Document subtitle.
    date : str or datetime
        Document date.
    author : str
        Author name.
    paper : str
        Paper size ("a4" or "us-letter").
    sections : list[dict], optional
        Structured sections (overrides markdown).
    font_paths : list[Path], optional
        Additional font directories.

    Returns
    -------
    Path
        Path to the generated PDF.
    """
    from inkline.brands import get_brand
    from inkline.typst.compiler import compile_typst
    from inkline.typst.document_renderer import DocumentSpec, TypstDocumentRenderer
    from inkline.typst.theme_registry import brand_to_typst_theme

    brand_obj = get_brand(brand)
    theme = brand_to_typst_theme(brand_obj, "brand")

    if isinstance(date, datetime):
        date = date.strftime("%B %Y")
    elif not date:
        date = datetime.now().strftime("%B %Y")

    doc_spec = DocumentSpec(
        title=title,
        subtitle=subtitle,
        date=date,
        author=author,
        sections=sections or [],
        paper=paper,
    )

    renderer = TypstDocumentRenderer(theme)

    if sections:
        source = renderer.render_document(doc_spec)
    else:
        source = renderer.render_from_markdown(markdown, doc_spec)

    # Collect font paths
    all_font_paths = [str(_FONTS_DIR)]
    if font_paths:
        all_font_paths.extend(str(p) for p in font_paths)

    # Copy logo to temp location if needed (Typst needs file access)
    output_path = Path(output_path)
    logo_path = theme.get("logo_light_path", "")
    root_dir = None
    if logo_path:
        logo_file = _ASSETS_DIR / logo_path
        if logo_file.exists():
            # Copy logo next to output so Typst can find it
            target = output_path.parent / logo_path
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                import shutil
                shutil.copy2(logo_file, target)
            root_dir = str(output_path.parent)
        else:
            # Logo not in package assets — try user config assets dir
            import re as _re
            user_logo = Path.home() / ".config" / "inkline" / "assets" / logo_path
            if user_logo.exists():
                target = output_path.parent / logo_path
                target.parent.mkdir(parents=True, exist_ok=True)
                import shutil
                shutil.copy2(user_logo, target)
                root_dir = str(output_path.parent)
            else:
                log.warning("Logo file not found: %s — stripping from source", logo_file)
                source = _re.sub(rf'#image\("{_re.escape(logo_path)}"[^)]*\)', "", source)

    compile_typst(source, output_path=output_path, root=root_dir, font_paths=all_font_paths)

    log.info("Typst document written to %s", output_path)
    return output_path


# ---------------------------------------------------------------------------
# Convenience: list available templates and brands
# ---------------------------------------------------------------------------

def list_templates() -> list[str]:
    """Return names of all available slide templates."""
    from inkline.typst.theme_registry import SLIDE_TEMPLATES
    return list(SLIDE_TEMPLATES.keys())


def list_slide_types() -> list[str]:
    """Return all supported slide types."""
    return [
        "title", "content", "three_card", "four_card", "stat",
        "table", "split", "chart", "bar_chart", "kpi_strip",
        "timeline", "process_flow", "icon_stat", "progress_bars",
        "pyramid", "comparison", "closing",
    ]


# ---------------------------------------------------------------------------
# Capability manifest (for cross-project integration)
# ---------------------------------------------------------------------------

def get_capabilities() -> dict:
    """Return a dict describing Inkline's full capabilities.

    Used by client applications to discover available output
    formats, brands, templates, and chart types.
    """
    from inkline.brands import list_brands
    return {
        "version": "0.2.0",
        "output_formats": ["typst_slides", "typst_document", "html", "pdf", "docx", "pptx", "google_slides"],
        "default_format": "typst_document",
        "brands": list_brands(),
        "slide_templates": list_templates(),
        "slide_types": list_slide_types(),
        "document_paper_sizes": ["a4", "us-letter"],
        "chart_types": [
            "bar_chart", "horizontal_bar", "line_chart", "stacked_bar",
            "waterfall", "scatter", "donut", "kpi_strip", "hero_stat",
            "data_table", "rag_cards", "risk_heatmap", "two_by_two_matrix",
        ],
        "infographic_styles": [
            "timeline", "process_flow", "comparison", "pyramid",
            "icon_grid", "stat_strip", "progress_bars",
        ],
    }
