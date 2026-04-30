"""Inkline Exhibit API — render a branded chart PNG for embedding in external tools.

Aigis and other callers use this to get a brand-consistent chart without knowing
anything about matplotlib or brand configuration.

Usage::

    from inkline.exhibit import render_exhibit

    result = render_exhibit(
        chart_type="line",
        labels=["2024", "2025", "2026", "2027", "2028"],
        values={"Oil (boepd)": [4200, 3800, 3400, 3000, 2700]},
        title="Production Profile",
        ylabel="boepd",
        brand_name="aigis",
    )
    # result["image_b64"] — PNG bytes as base64 string
    # result["audit"]["passed"] — True if image looks valid
"""

from __future__ import annotations

import base64
import io
import logging
import tempfile
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

# Audit thresholds
_MIN_FILE_BYTES = 5_000
_MIN_PIXEL_VARIANCE = 50.0


def _audit_png(png_bytes: bytes) -> dict:
    """Quick pixel-based sanity check on a rendered PNG."""
    warnings: list[str] = []

    if len(png_bytes) < _MIN_FILE_BYTES:
        warnings.append(f"File suspiciously small ({len(png_bytes)} bytes) — may be blank")

    try:
        from PIL import Image, ImageStat
        img = Image.open(io.BytesIO(png_bytes)).convert("L")
        stat = ImageStat.Stat(img)
        variance = stat.var[0]
        if variance < _MIN_PIXEL_VARIANCE:
            warnings.append(f"Low pixel variance ({variance:.1f}) — chart may be empty")
    except Exception as exc:
        warnings.append(f"Pixel audit skipped ({exc})")

    return {
        "passed": len(warnings) == 0,
        "file_size_bytes": len(png_bytes),
        "warnings": warnings,
    }


def render_exhibit(
    chart_type: str,
    labels: list[str],
    values: Any,
    title: str = "",
    ylabel: str = "",
    brand_name: str = "aigis",
    series_names: list[str] | None = None,
    figsize: tuple[float, float] | None = None,
) -> dict:
    """Render a branded chart and return base64 PNG + audit result.

    Args:
        chart_type: One of ``bar``, ``line``, ``stacked_area``, ``waterfall``,
            ``donut``, ``horizontal_bar``.
        labels: X-axis labels (or category names for donut/bar).
        values: Numeric data. For single-series charts: a flat list of floats.
            For ``line`` / ``stacked_area`` with multiple series: a dict
            ``{series_name: [floats]}`` OR a list of lists paired with
            ``series_names``.
        title: Chart title.
        ylabel: Y-axis label.
        brand_name: Inkline brand to apply (default ``"aigis"``).
        series_names: Required only when ``values`` is a list-of-lists (multi-series).
        figsize: ``(width_inches, height_inches)`` override. Defaults vary by type.

    Returns:
        ``{"image_b64": str, "format": "png", "chart_type": str, "audit": dict}``
    """
    from inkline.brands import get_brand
    from inkline.core.charts import ChartEngine

    brand = get_brand(brand_name)
    engine = ChartEngine(
        colors=brand.chart_colors,
        bg_color=brand.background,
        text_color=brand.text,
        grid_color=getattr(brand, "border", "#D1D5DB"),
        dpi=180,
    )

    # Normalise multi-series values to dict
    def _to_series_dict(v: Any, names: list[str] | None) -> dict[str, list[float]]:
        if isinstance(v, dict):
            return v
        if isinstance(v, list) and v and isinstance(v[0], (list, tuple)):
            ns = names or [f"Series {i+1}" for i in range(len(v))]
            return {n: list(s) for n, s in zip(ns, v)}
        # Single series
        ns = names or ["Value"]
        return {ns[0]: list(v)}

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        ct = chart_type.lower()

        if ct == "bar":
            kw = {"figsize": figsize or (9, 5)}
            flat = values if isinstance(values, list) and not (values and isinstance(values[0], list)) else list(next(iter(_to_series_dict(values, series_names).values())))
            engine.bar_chart(labels=labels, values=flat, title=title, ylabel=ylabel, output_path=tmp_path, **kw)

        elif ct == "horizontal_bar":
            kw = {"figsize": figsize or (9, 5)}
            flat = values if isinstance(values, list) and not (values and isinstance(values[0], list)) else list(next(iter(_to_series_dict(values, series_names).values())))
            engine.horizontal_bar_chart(labels=labels, values=flat, title=title, ylabel=ylabel, output_path=tmp_path, **kw)

        elif ct == "line":
            kw = {"figsize": figsize or (9, 5)}
            engine.line_chart(x=labels, y_series=_to_series_dict(values, series_names), title=title, ylabel=ylabel, output_path=tmp_path, **kw)

        elif ct == "stacked_area":
            kw = {"figsize": figsize or (9, 5)}
            engine.stacked_area_chart(x=labels, y_series=_to_series_dict(values, series_names), title=title, ylabel=ylabel, output_path=tmp_path, **kw)

        elif ct == "waterfall":
            kw = {"figsize": figsize or (9, 5)}
            flat = values if isinstance(values, list) and not (values and isinstance(values[0], list)) else list(next(iter(_to_series_dict(values, series_names).values())))
            engine.waterfall_chart(labels=labels, values=flat, title=title, output_path=tmp_path, **kw)

        elif ct == "donut":
            kw = {"figsize": figsize or (5.5, 5.5)}
            flat = values if isinstance(values, list) and not (values and isinstance(values[0], list)) else list(next(iter(_to_series_dict(values, series_names).values())))
            engine.donut_chart(labels=labels, values=flat, title=title, output_path=tmp_path, **kw)

        else:
            raise ValueError(f"Unknown chart_type '{chart_type}'. Supported: bar, horizontal_bar, line, stacked_area, waterfall, donut")

        png_bytes = tmp_path.read_bytes()

    finally:
        tmp_path.unlink(missing_ok=True)

    audit = _audit_png(png_bytes)
    if not audit["passed"]:
        log.warning("Exhibit audit warnings for '%s': %s", chart_type, audit["warnings"])
    else:
        log.info("Exhibit rendered OK — %s, %d bytes", chart_type, audit["file_size_bytes"])

    return {
        "image_b64": base64.b64encode(png_bytes).decode(),
        "format": "png",
        "chart_type": chart_type,
        "brand": brand_name,
        "audit": audit,
    }
