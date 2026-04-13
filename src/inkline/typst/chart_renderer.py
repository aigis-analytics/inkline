"""Chart renderer — generates publication-quality chart images via matplotlib.

Produces PNG files that can be embedded in Typst slides via the ``chart``
slide type. Applies brand colors and consistent styling.

Supported chart types (data charts):
- line_chart: single or multi-series time series
- area_chart: filled line chart
- scatter: scatter plot with optional size/color encoding
- waterfall: sequential positive/negative changes
- donut: part-of-whole (max 6 segments)
- pie: traditional pie chart
- stacked_bar: vertical stacked bar chart
- grouped_bar: side-by-side grouped bars
- heatmap: 2D color matrix
- radar: spider/radar chart for multi-axis comparison
- gauge: single-value meter (0-100%)

Supported infographic types (structural/conceptual diagrams):
- iceberg: above/below-the-surface concept diagram
- funnel_ribbon: trapezoid-band funnel with stage values
- waffle: 10×10 grid proportion chart (pywaffle or fallback)
- dual_donut: concentric donut rings
- hexagonal_honeycomb: hexagon grid of content cards
- radial_pinwheel: central hub with radiating item cards
- semicircle_taxonomy: arc-based grouping taxonomy
- process_curved_arrows: S-curve step process flow
- pyramid_detailed: tiered pyramid with detail callouts
- ladder: ascending steps / staircase diagram
- petal_teardrop: petal-burst around a center concept
- funnel_kpi_strip: funnel + KPI metrics strip below
- persona_dashboard: user persona card layout
- sidebar_profile: two-panel profile + content layout
- metaphor_backdrop: backdrop silhouette + overlay cards
- chart_row: side-by-side mini charts composited into one figure
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Optional

log = logging.getLogger(__name__)

# Lazy import matplotlib to keep it optional
_mpl = None
_plt = None


def _ensure_matplotlib():
    global _mpl, _plt
    if _mpl is None:
        import matplotlib as mpl
        mpl.use("Agg")  # Non-interactive backend
        import matplotlib.pyplot as plt
        _mpl = mpl
        _plt = plt


def _shades_of(hex_color: str, n: int) -> list[str]:
    """Return n shades of a single brand colour.

    Used for category charts (donut, pie, stacked bar) to maintain brand
    discipline — the chart is recognisably ONE colour, not a rainbow.
    First shade is the base colour at full intensity; subsequent shades
    fade towards a lighter tint.
    """
    if n <= 0:
        return []
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    # Range from 100% to 35% intensity (mixed with white)
    out = []
    for i in range(n):
        t = i / max(n - 1, 1)  # 0 to 1
        mix = 0.65 * t  # max 65% white
        rr = int(r + (255 - r) * mix)
        gg = int(g + (255 - g) * mix)
        bb = int(b + (255 - b) * mix)
        out.append(f"#{rr:02X}{gg:02X}{bb:02X}")
    return out


def render_chart(
    chart_type: str,
    data: dict[str, Any],
    output_path: str | Path,
    *,
    brand_colors: Optional[list[str]] = None,
    secondary: Optional[str] = None,
    accent: str = "#1A7FA0",
    bg: str = "#FFFFFF",
    text_color: str = "#1A1A1A",
    muted: str = "#6B7280",
    width: float = 7.5,
    height: float = 4.2,
    dpi: int = 200,
    color_mode: str = "duo",
) -> Path:
    """Render a chart to PNG with brand-disciplined colors.

    Parameters
    ----------
    chart_type : str
        One of: line_chart, area_chart, scatter, waterfall, donut, pie,
        stacked_bar, grouped_bar, heatmap, radar, gauge.
    data : dict
        Chart-specific data (see individual renderers for schema).
    output_path : Path
        Where to save the PNG.
    brand_colors : list[str], optional
        Full brand palette. Will be SUBSET based on color_mode.
    secondary : str, optional
        Secondary brand color (used in "duo" mode).
    accent, bg, text_color, muted : str
        Brand color tokens.
    width, height : float
        Figure size in inches. Aspect ratio matches Typst slide chart area.
    dpi : int
        Resolution.
    color_mode : str
        "mono" — single accent color (best for category data with one
                 conceptual group).
        "duo"  — accent + secondary (DEFAULT — primary colour discipline,
                 matches brand identity, no rainbow).
        "palette" — full brand_colors palette (use only for genuinely
                    multi-category data like 6+ products or RAG charts).
    """
    _ensure_matplotlib()

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Brand colour discipline: by default use 2 colours, not 6.
    full_palette = brand_colors or [accent, "#39D3BB", "#f0883e", "#58a6ff", "#d2a8ff", "#e6c069"]
    if color_mode == "mono":
        colors = [accent]
    elif color_mode == "duo":
        sec = secondary or (full_palette[1] if len(full_palette) > 1 else "#94A3B8")
        colors = [accent, sec]
    else:  # "palette"
        colors = full_palette

    renderers = {
        "line_chart": _render_line_chart,
        "area_chart": _render_area_chart,
        "scatter": _render_scatter,
        "waterfall": _render_waterfall,
        "donut": _render_donut,
        "pie": _render_pie,
        "stacked_bar": _render_stacked_bar,
        "grouped_bar": _render_grouped_bar,
        "heatmap": _render_heatmap,
        "radar": _render_radar,
        "gauge": _render_gauge,
        # Infographic types
        "iceberg": _render_infographic_iceberg,
        "funnel_ribbon": _render_infographic_funnel_ribbon,
        "waffle": _render_infographic_waffle,
        "dual_donut": _render_infographic_dual_donut,
        "hexagonal_honeycomb": _render_infographic_hexagonal_honeycomb,
        "radial_pinwheel": _render_infographic_radial_pinwheel,
        "semicircle_taxonomy": _render_infographic_semicircle_taxonomy,
        "process_curved_arrows": _render_infographic_process_curved_arrows,
        "pyramid_detailed": _render_infographic_pyramid_detailed,
        "ladder": _render_infographic_ladder,
        "petal_teardrop": _render_infographic_petal_teardrop,
        "funnel_kpi_strip": _render_infographic_funnel_kpi_strip,
        "persona_dashboard": _render_infographic_persona_dashboard,
        "sidebar_profile": _render_infographic_sidebar_profile,
        "metaphor_backdrop": _render_infographic_metaphor_backdrop,
        "chart_row": _render_infographic_chart_row,
    }

    renderer = renderers.get(chart_type)
    if not renderer:
        raise ValueError(f"Unknown chart type: {chart_type}. Available: {list(renderers.keys())}")

    fig = renderer(data, colors=colors, accent=accent, bg=bg, text_color=text_color, muted=muted, width=width, height=height)

    # Illustrative watermark — diagonal across chart background
    if data.get("illustrative"):
        fig.text(
            0.5, 0.5, "ILLUSTRATIVE",
            ha="center", va="center",
            fontsize=44, color=muted, alpha=0.08,
            rotation=20, weight="bold",
            transform=fig.transFigure, zorder=0,
        )

    # Save with generous padding so rotated labels and axis ticks never clip.
    # bbox_inches="tight" with pad_inches=0.25 leaves margin for the worst case.
    fig.savefig(
        str(output_path), dpi=dpi,
        bbox_inches="tight", pad_inches=0.25,
        facecolor=bg, edgecolor="none", transparent=False,
    )
    _plt.close(fig)

    log.info("Chart rendered: %s (%s, %d bytes)", chart_type, output_path, output_path.stat().st_size)
    return output_path


def render_chart_for_brand(
    chart_type: str,
    data: dict[str, Any],
    output_path: str | Path,
    brand_name: str = "minimal",
    **kwargs,
) -> Path:
    """Render a chart using a brand's color palette.

    Convenience wrapper that loads brand colors automatically.
    """
    from inkline.brands import get_brand
    brand = get_brand(brand_name)
    return render_chart(
        chart_type, data, output_path,
        brand_colors=brand.chart_colors,
        secondary=brand.secondary,
        accent=brand.primary,
        bg=brand.background,
        text_color=brand.text,
        muted=brand.muted,
        **kwargs,
    )


# ---------------------------------------------------------------------------
# Shared styling
# ---------------------------------------------------------------------------

def _style_axes(ax, bg, text_color, muted):
    """Apply consistent styling to axes."""
    ax.set_facecolor(bg)
    ax.tick_params(colors=muted, labelsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_color(muted)
    ax.spines["left"].set_color(muted)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_color(text_color)


# ---------------------------------------------------------------------------
# Line chart
# ---------------------------------------------------------------------------

def _render_line_chart(data, *, colors, accent, bg, text_color, muted, width, height):
    """Line chart with optional multi-series.

    data:
        x: list — x-axis values (dates, labels, numbers)
        series: list of {name, values} — y-axis series
        x_label: str — x-axis label
        y_label: str — y-axis label
        title: str — chart title (optional, usually in slide title)
    """
    fig, ax = _plt.subplots(figsize=(width, height))
    fig.patch.set_facecolor(bg)
    _style_axes(ax, bg, text_color, muted)

    x = data.get("x", [])
    series = data.get("series", [])

    for i, s in enumerate(series):
        color = colors[i % len(colors)]
        ax.plot(x, s["values"], color=color, linewidth=2.5, label=s.get("name", f"Series {i+1}"),
                marker="o" if len(x) <= 20 else None, markersize=5)

    if data.get("x_label"):
        ax.set_xlabel(data["x_label"], color=text_color, fontsize=10)
    if data.get("y_label"):
        ax.set_ylabel(data["y_label"], color=text_color, fontsize=10)
    if len(series) > 1:
        ax.legend(frameon=False, fontsize=9, labelcolor=text_color)

    ax.grid(axis="y", alpha=0.3, color=muted)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Area chart
# ---------------------------------------------------------------------------

def _render_area_chart(data, *, colors, accent, bg, text_color, muted, width, height):
    """Filled area chart."""
    fig, ax = _plt.subplots(figsize=(width, height))
    fig.patch.set_facecolor(bg)
    _style_axes(ax, bg, text_color, muted)

    x = data.get("x", [])
    series = data.get("series", [])

    for i, s in enumerate(series):
        color = colors[i % len(colors)]
        ax.fill_between(range(len(x)), s["values"], alpha=0.3, color=color)
        ax.plot(range(len(x)), s["values"], color=color, linewidth=2, label=s.get("name", ""))

    ax.set_xticks(range(len(x)))
    ax.set_xticklabels(x, rotation=45 if len(x) > 8 else 0, ha="right" if len(x) > 8 else "center")
    if len(series) > 1:
        ax.legend(frameon=False, fontsize=9, labelcolor=text_color)
    ax.grid(axis="y", alpha=0.3, color=muted)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Scatter plot
# ---------------------------------------------------------------------------

def _render_scatter(data, *, colors, accent, bg, text_color, muted, width, height):
    """Scatter plot with optional size encoding.

    data:
        points: list of {x, y, label?, size?, group?}
        x_label, y_label: str
    """
    fig, ax = _plt.subplots(figsize=(width, height))
    fig.patch.set_facecolor(bg)
    _style_axes(ax, bg, text_color, muted)

    points = data.get("points", [])
    groups = {}
    for p in points:
        g = p.get("group", "default")
        groups.setdefault(g, []).append(p)

    for i, (group_name, pts) in enumerate(groups.items()):
        color = colors[i % len(colors)]

        # Separate highlighted vs regular points
        regular = [p for p in pts if not p.get("highlight")]
        highlighted = [p for p in pts if p.get("highlight")]

        # Regular points
        if regular:
            xs = [p["x"] for p in regular]
            ys = [p["y"] for p in regular]
            sizes = [p.get("size", 50) for p in regular]
            ax.scatter(xs, ys, c=color, s=sizes, alpha=0.6,
                       label=group_name if group_name != "default" else None,
                       edgecolors="white", linewidth=0.5)
            for p in regular:
                if p.get("label"):
                    ax.annotate(p["label"], (p["x"], p["y"]), fontsize=7.5,
                                color=muted, textcoords="offset points", xytext=(5, 5))

        # Highlighted points — large filled circle, bold label, accent colour
        if highlighted:
            hx = [p["x"] for p in highlighted]
            hy = [p["y"] for p in highlighted]
            hs = [p.get("size", 300) for p in highlighted]
            # Outer glow ring
            ax.scatter(hx, hy, c="none", s=[s * 2 for s in hs], alpha=0.15,
                       edgecolors=accent, linewidth=2, zorder=9)
            # Main dot
            ax.scatter(hx, hy, c=accent, s=hs, alpha=1.0, marker="o",
                       edgecolors="white", linewidth=2, zorder=10)
            for p in highlighted:
                if p.get("label"):
                    ax.annotate(
                        p["label"], (p["x"], p["y"]),
                        fontsize=12, fontweight="bold", color=accent,
                        textcoords="offset points", xytext=(10, 10),
                        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=accent, alpha=0.9),
                    )

    if data.get("x_label"):
        ax.set_xlabel(data["x_label"], color=text_color, fontsize=10)
    if data.get("y_label"):
        ax.set_ylabel(data["y_label"], color=text_color, fontsize=10)
    if len(groups) > 1:
        ax.legend(frameon=False, fontsize=9, labelcolor=text_color)
    ax.grid(alpha=0.2, color=muted)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Waterfall chart
# ---------------------------------------------------------------------------

def _render_waterfall(data, *, colors, accent, bg, text_color, muted, width, height):
    """Waterfall chart showing sequential changes.

    data:
        items: list of {label, value, total? (bool)}
    """
    import numpy as np

    fig, ax = _plt.subplots(figsize=(width, height))
    fig.patch.set_facecolor(bg)
    _style_axes(ax, bg, text_color, muted)

    items = data.get("items", [])
    labels = [it["label"] for it in items]
    values = [it["value"] for it in items]
    is_total = [it.get("total", False) for it in items]

    # Brand-disciplined waterfall colours:
    #   totals → primary accent (the hero)
    #   positive deltas → primary accent (lighter shade)
    #   negative deltas → secondary brand colour (NOT red)
    accent_light = _shades_of(accent, 3)[1]  # mid shade of primary
    secondary_color = colors[1] if len(colors) > 1 else accent_light

    cumulative = 0
    bottoms = []
    bar_colors = []
    for i, (val, total) in enumerate(zip(values, is_total)):
        if total:
            bottoms.append(0)
            bar_colors.append(accent)
        else:
            if val >= 0:
                bottoms.append(cumulative)
                bar_colors.append(accent_light)
            else:
                bottoms.append(cumulative + val)
                bar_colors.append(secondary_color)
        if not total:
            cumulative += val

    x = np.arange(len(labels))
    ax.bar(x, [abs(v) for v in values], bottom=bottoms, color=bar_colors, width=0.6, edgecolor="white", linewidth=0.5)

    # Value labels
    for i, (val, bot) in enumerate(zip(values, bottoms)):
        y_pos = bot + abs(val) / 2
        ax.text(i, y_pos, f"{val:+,.0f}" if not is_total[i] else f"{val:,.0f}",
                ha="center", va="center", fontsize=9, fontweight="bold", color="white")

    ax.set_xticks(x)
    # Keep labels horizontal — much cleaner. Use small font if any label
    # is long. Reserve generous bottom margin via subplots_adjust.
    max_label_len = max((len(str(l)) for l in labels), default=0)
    if max_label_len > 12:
        ax.set_xticklabels(labels, fontsize=7)
    elif max_label_len > 8:
        ax.set_xticklabels(labels, fontsize=8)
    else:
        ax.set_xticklabels(labels, fontsize=9)
    fig.subplots_adjust(bottom=0.20)
    ax.axhline(y=0, color=muted, linewidth=0.5)
    ax.grid(axis="y", alpha=0.2, color=muted)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Donut chart
# ---------------------------------------------------------------------------

def _render_donut(data, *, colors, accent, bg, text_color, muted, width, height):
    """Donut chart (max 6 segments) — uses shades of accent for brand consistency.

    Layout: donut on the left, labelled legend on the right. This avoids
    the chronic clipping problem of pie/donut charts with external labels.

    data:
        segments: list of {label, value}
        center_label: str (optional — text in center)
    """
    fig, ax = _plt.subplots(figsize=(width, height))
    fig.patch.set_facecolor(bg)

    segments = data.get("segments", [])[:6]
    labels = [s["label"] for s in segments]
    values = [s["value"] for s in segments]
    total = sum(values) if values else 1

    # Use shades of accent (mono palette) — NOT rainbow.
    seg_colors = _shades_of(accent, len(segments))

    # Place donut in left ~55% of figure; legend in right ~45%
    ax.set_position([0.02, 0.05, 0.55, 0.9])

    wedges, autotexts = ax.pie(
        values, colors=seg_colors, autopct="%1.0f%%",
        startangle=90, pctdistance=0.78,
        wedgeprops={"width": 0.42, "edgecolor": bg, "linewidth": 2},
        textprops={"fontsize": 10, "color": "white", "fontweight": "bold"},
    )[:2]
    for t in autotexts:
        t.set_color("white")
        t.set_fontsize(10)
        t.set_fontweight("bold")

    if data.get("center_label"):
        ax.text(0, 0, data["center_label"], ha="center", va="center",
                fontsize=15, fontweight="bold", color=text_color)

    # Right-side legend with label + value, vertically centered
    legend_lines = [
        f"{labels[i]}  ·  {values[i]}" for i in range(len(segments))
    ]
    legend_handles = [
        _plt.Rectangle((0, 0), 1, 1, color=seg_colors[i]) for i in range(len(segments))
    ]
    fig.legend(
        legend_handles, legend_lines,
        loc="center left", bbox_to_anchor=(0.6, 0.5),
        frameon=False, fontsize=11, labelcolor=text_color,
        handlelength=1.2, handleheight=1.2, handletextpad=0.8,
        labelspacing=1.0,
    )

    return fig


# ---------------------------------------------------------------------------
# Pie chart
# ---------------------------------------------------------------------------

def _render_pie(data, **kwargs):
    """Traditional pie chart (delegates to donut with full width)."""
    # Same as donut but with full wedge width
    fig = _render_donut(data, **kwargs)
    ax = fig.axes[0]
    for wedge in ax.patches:
        wedge.set_width(1.0)
    return fig


# ---------------------------------------------------------------------------
# Stacked bar chart
# ---------------------------------------------------------------------------

def _render_stacked_bar(data, *, colors, accent, bg, text_color, muted, width, height):
    """Vertical stacked bar chart.

    data:
        categories: list of str (x-axis labels)
        series: list of {name, values}
    """
    import numpy as np

    fig, ax = _plt.subplots(figsize=(width, height))
    fig.patch.set_facecolor(bg)
    _style_axes(ax, bg, text_color, muted)

    categories = data.get("categories", [])
    series = data.get("series", [])
    x = np.arange(len(categories))
    bottom = np.zeros(len(categories))

    # Stacked bar — use shades of accent for brand discipline
    seg_colors = _shades_of(accent, len(series))
    for i, s in enumerate(series):
        color = seg_colors[i]
        vals = s["values"]
        ax.bar(x, vals, bottom=bottom, color=color, label=s.get("name", ""), width=0.6, edgecolor="white", linewidth=0.5)
        bottom += np.array(vals)

    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=9)
    ax.legend(frameon=False, fontsize=9, labelcolor=text_color, loc="upper left")
    ax.grid(axis="y", alpha=0.2, color=muted)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Grouped bar chart
# ---------------------------------------------------------------------------

def _render_grouped_bar(data, *, colors, accent, bg, text_color, muted, width, height):
    """Side-by-side grouped bar chart.

    data:
        categories: list of str
        series: list of {name, values}
    """
    import numpy as np

    fig, ax = _plt.subplots(figsize=(width, height))
    fig.patch.set_facecolor(bg)
    _style_axes(ax, bg, text_color, muted)

    categories = data.get("categories", [])
    series = data.get("series", [])
    n_series = len(series)
    x = np.arange(len(categories))
    bar_width = 0.7 / n_series

    for i, s in enumerate(series):
        color = colors[i % len(colors)]
        offset = (i - n_series / 2 + 0.5) * bar_width
        ax.bar(x + offset, s["values"], bar_width, color=color, label=s.get("name", ""), edgecolor="white", linewidth=0.5)

    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=9)
    ax.legend(frameon=False, fontsize=9, labelcolor=text_color)
    ax.grid(axis="y", alpha=0.2, color=muted)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Heatmap
# ---------------------------------------------------------------------------

def _render_heatmap(data, *, colors, accent, bg, text_color, muted, width, height):
    """2D color matrix heatmap.

    data:
        matrix: list of lists (2D values)
        x_labels: list of str
        y_labels: list of str
        colormap: str (optional, e.g. "RdYlGn", "Blues")
    """
    import numpy as np

    fig, ax = _plt.subplots(figsize=(width, height))
    fig.patch.set_facecolor(bg)

    matrix = np.array(data.get("matrix", [[]]))
    x_labels = data.get("x_labels", [])
    y_labels = data.get("y_labels", [])
    cmap = data.get("colormap", "RdYlGn")

    im = ax.imshow(matrix, cmap=cmap, aspect="auto")

    ax.set_xticks(range(len(x_labels)))
    ax.set_yticks(range(len(y_labels)))
    ax.set_xticklabels(x_labels, fontsize=9, color=text_color)
    ax.set_yticklabels(y_labels, fontsize=9, color=text_color)

    # Annotate cells
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            val = matrix[i, j]
            text_c = "white" if val > (matrix.max() + matrix.min()) / 2 else text_color
            ax.text(j, i, f"{val:.1f}", ha="center", va="center", fontsize=9, color=text_c, fontweight="bold")

    ax.spines[:].set_visible(False)
    fig.colorbar(im, ax=ax, shrink=0.8)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Radar / spider chart
# ---------------------------------------------------------------------------

def _render_radar(data, *, colors, accent, bg, text_color, muted, width, height):
    """Radar/spider chart for multi-axis comparison.

    Layout: radar on the left, legend on the right (separated). Axis labels
    given generous padding so they never clip. Designed for the wider
    chart_caption / dashboard cells.

    data:
        axes: list of str (axis labels)
        series: list of {name, values} (values 0-100 or 0-max)
    """
    import numpy as np

    fig = _plt.figure(figsize=(width, height))
    fig.patch.set_facecolor(bg)

    # Polar plot in left ~62% of figure with margin for axis labels;
    # legend on the right ~32%.
    ax = fig.add_axes([0.08, 0.10, 0.55, 0.80], projection="polar")
    ax.set_facecolor(bg)

    axes_labels = data.get("axes", [])
    series = data.get("series", [])
    n_axes = len(axes_labels)

    angles = np.linspace(0, 2 * np.pi, n_axes, endpoint=False).tolist()
    angles += angles[:1]  # Close the polygon

    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_rlabel_position(0)

    for i, s in enumerate(series):
        color = colors[i % len(colors)]
        values = s["values"] + s["values"][:1]
        ax.plot(angles, values, color=color, linewidth=2.2, label=s.get("name", ""))
        ax.fill(angles, values, color=color, alpha=0.15)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(axes_labels, fontsize=8, color=text_color)
    ax.tick_params(axis="y", labelsize=7, colors=muted, pad=2)
    ax.grid(color=muted, alpha=0.3, linewidth=0.5)
    # Push axis labels further from the chart so they don't clip
    ax.tick_params(axis="x", pad=8)
    # Hide r-axis tick labels for cleaner look (the legend explains scale)
    ax.set_yticklabels([])

    # External legend (right side) — does NOT overlap chart
    if len(series) > 0:
        legend_handles = [
            _plt.Line2D([0], [0], color=colors[i % len(colors)], linewidth=2.2,
                        label=s.get("name", ""))
            for i, s in enumerate(series)
        ]
        fig.legend(
            handles=legend_handles,
            loc="center left", bbox_to_anchor=(0.66, 0.5),
            frameon=False, fontsize=10, labelcolor=text_color,
            handlelength=1.6, labelspacing=1.2,
        )

    return fig


# ---------------------------------------------------------------------------
# Gauge / meter
# ---------------------------------------------------------------------------

def _render_gauge(data, *, colors, accent, bg, text_color, muted, width, height):
    """Semi-circular gauge meter (0-100%).

    data:
        value: float (0-100)
        label: str
        thresholds: list of {value, color} (optional — e.g. red/amber/green zones)
    """
    import numpy as np

    fig, ax = _plt.subplots(figsize=(width, height * 0.7))
    fig.patch.set_facecolor(bg)

    value = data.get("value", 0)
    label = data.get("label", "")
    thresholds = data.get("thresholds", [
        {"value": 33, "color": "#dc2626"},
        {"value": 66, "color": "#f59e0b"},
        {"value": 100, "color": "#10b981"},
    ])

    # Draw background arc segments
    prev = 0
    for thresh in thresholds:
        theta_start = np.pi * (1 - prev / 100)
        theta_end = np.pi * (1 - thresh["value"] / 100)
        theta = np.linspace(theta_start, theta_end, 50)
        ax.fill_between(np.cos(theta), np.sin(theta), 0, color=thresh["color"], alpha=0.2)
        prev = thresh["value"]

    # Draw full arc outline
    theta_full = np.linspace(0, np.pi, 100)
    ax.plot(np.cos(theta_full), np.sin(theta_full), color=muted, linewidth=2)

    # Needle
    needle_angle = np.pi * (1 - value / 100)
    ax.plot([0, 0.85 * np.cos(needle_angle)], [0, 0.85 * np.sin(needle_angle)],
            color=accent, linewidth=3, solid_capstyle="round")
    ax.plot(0, 0, "o", color=accent, markersize=8)

    # Value text
    ax.text(0, -0.15, f"{value:.0f}%", ha="center", va="center",
            fontsize=28, fontweight="bold", color=text_color)
    if label:
        ax.text(0, -0.35, label, ha="center", va="center",
                fontsize=12, color=muted)

    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-0.5, 1.1)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Utility: list available chart types
# ---------------------------------------------------------------------------

def list_chart_types() -> list[str]:
    """Return all supported chart types."""
    return [
        # Data charts
        "line_chart", "area_chart", "scatter", "waterfall",
        "donut", "pie", "stacked_bar", "grouped_bar",
        "heatmap", "radar", "gauge",
        # Infographic types
        "iceberg", "funnel_ribbon", "waffle", "dual_donut",
        "hexagonal_honeycomb", "radial_pinwheel", "semicircle_taxonomy",
        "process_curved_arrows", "pyramid_detailed", "ladder",
        "petal_teardrop", "funnel_kpi_strip", "persona_dashboard",
        "sidebar_profile", "metaphor_backdrop", "chart_row",
    ]


# ===========================================================================
# Infographic renderers
# ===========================================================================

# ---------------------------------------------------------------------------
# 1. Iceberg
# ---------------------------------------------------------------------------

def _render_infographic_iceberg(data, *, colors, accent, bg, text_color, muted, width, height):
    """Iceberg diagram — visible vs hidden layers.

    data:
        above: list of {label, desc}   (visible, 2-4 items)
        below: list of {label, desc}   (hidden,  3-6 items)
        above_label: str
        below_label: str
    """
    import numpy as np
    import textwrap

    height = data.get("_height", height)
    fig, ax = _plt.subplots(figsize=(width, height))
    fig.patch.set_facecolor(bg)
    ax.set_facecolor(bg)
    ax.axis("off")
    ax.set_xlim(-1.5, 1.5)
    ax.set_ylim(-1.0, 0.75)

    above_items = data.get("above", [])[:4]
    below_items = data.get("below", [])[:6]
    above_label = data.get("above_label", "What's Visible")
    below_label = data.get("below_label", "What's Hidden")

    col_above = colors[0] if colors else accent
    col_below = colors[1] if len(colors) > 1 else _shades_of(col_above, 3)[2]

    # Ocean fill
    ax.fill_between([-1.5, 1.5], -1.0, 0.0, color="#C8E6F5", alpha=0.35, zorder=1)

    # Above water: triangle/pentagon shape
    above_xs = [-0.35, 0.0, 0.35, 0.25, -0.25]
    above_ys = [0.02, 0.60, 0.02, 0.02, 0.02]
    from matplotlib.patches import Polygon as MplPolygon, FancyBboxPatch
    tri = MplPolygon(list(zip(above_xs, above_ys)), closed=True,
                     facecolor=col_above, edgecolor=bg, linewidth=1.5, zorder=4, alpha=0.92)
    ax.add_patch(tri)

    # Below water: inverted trapezoid
    below_xs = [-0.25, 0.25, 0.70, -0.70]
    below_ys = [0.0, 0.0, -0.90, -0.90]
    trap = MplPolygon(list(zip(below_xs, below_ys)), closed=True,
                      facecolor=col_below, edgecolor=bg, linewidth=1.5, zorder=4, alpha=0.85)
    ax.add_patch(trap)

    # Waterline
    ax.axhline(0, color=muted, lw=2, zorder=5, xmin=0.0, xmax=1.0)

    # Above-label
    ax.text(0.0, 0.68, above_label, ha="center", va="center",
            fontsize=9, fontweight="bold", color=text_color, zorder=6)

    # Below-label
    ax.text(0.0, -0.96, below_label, ha="center", va="bottom",
            fontsize=9, fontweight="bold", color=text_color, zorder=6)

    # Right side: above items
    n_above = len(above_items)
    for i, item in enumerate(above_items):
        y = 0.48 - i * (0.38 / max(n_above, 1))
        label = item.get("label", "")
        desc = item.get("desc", "")
        ax.text(0.55, y, f"• {label}", ha="left", va="center",
                fontsize=9, fontweight="bold", color=text_color, zorder=6)
        if desc:
            ax.text(0.58, y - 0.07, textwrap.fill(desc, 28), ha="left", va="top",
                    fontsize=7.5, color=muted, zorder=6)

    # Right side: below items
    n_below = len(below_items)
    for i, item in enumerate(below_items):
        y = -0.12 - i * (0.72 / max(n_below, 1))
        label = item.get("label", "")
        desc = item.get("desc", "")
        ax.text(0.75, y, f"• {label}", ha="left", va="center",
                fontsize=9, fontweight="bold", color=text_color, zorder=6)
        if desc:
            ax.text(0.78, y - 0.07, textwrap.fill(desc, 22), ha="left", va="top",
                    fontsize=7.5, color=muted, zorder=6)

    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# 2. Funnel ribbon
# ---------------------------------------------------------------------------

def _render_infographic_funnel_ribbon(data, *, colors, accent, bg, text_color, muted, width, height):
    """Trapezoid-band funnel: wide top, narrow bottom.

    data:
        stages: list of {label, value}  (3-6 stages)
        title: str
    """
    import textwrap

    fig, ax = _plt.subplots(figsize=(width, height))
    fig.patch.set_facecolor(bg)
    ax.set_facecolor(bg)
    ax.axis("off")

    stages = data.get("stages", [])[:6]
    title = data.get("title", "")
    n = len(stages)
    if n == 0:
        fig.tight_layout()
        return fig

    ax.set_xlim(-1, 1)
    ax.set_ylim(-0.05, 1.05)

    if title:
        ax.text(0, 1.02, title, ha="center", va="bottom",
                fontsize=12, fontweight="bold", color=text_color)

    from matplotlib.patches import Polygon as MplPolygon

    band_h = 0.90 / n
    # Width at each horizontal division: linearly decreasing from 0.9 to 0.2
    widths = [0.9 - (0.9 - 0.2) * (i / max(n, 1)) for i in range(n + 1)]

    for i, stage in enumerate(stages):
        color = colors[i % len(colors)]
        y_top = 0.95 - i * band_h
        y_bot = y_top - band_h + 0.005  # small gap
        w_top = widths[i]
        w_bot = widths[i + 1]

        pts = [
            (-w_top / 2, y_top), (w_top / 2, y_top),
            (w_bot / 2, y_bot), (-w_bot / 2, y_bot),
        ]
        poly = MplPolygon(pts, closed=True, facecolor=color, edgecolor=bg,
                          linewidth=1.5, zorder=3, alpha=0.88)
        ax.add_patch(poly)

        y_mid = (y_top + y_bot) / 2
        label = stage.get("label", "")
        value = stage.get("value", "")
        ax.text(0, y_mid, label, ha="center", va="center",
                fontsize=10, fontweight="bold", color="white", zorder=4)
        if value:
            ax.text(w_bot / 2 + 0.05, y_mid, str(value), ha="left", va="center",
                    fontsize=9, color=text_color, zorder=4)

    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# 3. Waffle chart
# ---------------------------------------------------------------------------

def _render_infographic_waffle(data, *, colors, accent, bg, text_color, muted, width, height):
    """10×10 waffle/proportion chart.

    data:
        categories: list of {label, value}  (values ideally sum to 100)
        rows: int (default 10)
        columns: int (default 10)
    """
    import numpy as np

    try:
        from pywaffle import Waffle  # type: ignore
        HAVE_PYWAFFLE = True
    except ImportError:
        HAVE_PYWAFFLE = False

    categories = data.get("categories", [])
    rows = data.get("rows", 10)
    cols = data.get("columns", 10)
    total_cells = rows * cols

    labels = [c.get("label", f"Cat {i+1}") for i, c in enumerate(categories)]
    raw_vals = [max(c.get("value", 0), 0) for c in categories]
    total = sum(raw_vals) or 1
    # Normalize to total_cells
    norm_vals = [int(round(v / total * total_cells)) for v in raw_vals]
    # Fix rounding so sum == total_cells
    diff = total_cells - sum(norm_vals)
    if norm_vals:
        norm_vals[0] += diff

    cat_colors = [colors[i % len(colors)] for i in range(len(categories))]

    if HAVE_PYWAFFLE and categories:
        fig = _plt.figure(
            FigureClass=Waffle,
            rows=rows, columns=cols,
            values=norm_vals,
            colors=cat_colors,
            labels=labels,
            legend={"loc": "lower left", "bbox_to_anchor": (0, -0.25),
                    "ncol": min(len(labels), 4), "frameon": False,
                    "fontsize": 9},
            figsize=(width, height),
        )
        fig.patch.set_facecolor(bg)
        fig.tight_layout()
        return fig

    # Fallback: matplotlib scatter squares
    fig, ax = _plt.subplots(figsize=(width, height))
    fig.patch.set_facecolor(bg)
    ax.set_facecolor(bg)
    ax.axis("off")
    ax.set_xlim(-0.5, cols - 0.5)
    ax.set_ylim(-1.5, rows - 0.5)

    # Build cell color grid row by row (bottom-left to top-right)
    cell_colors = []
    for i, (color, count) in enumerate(zip(cat_colors, norm_vals)):
        cell_colors.extend([color] * count)
    cell_colors.extend([muted] * max(0, total_cells - len(cell_colors)))

    cell_idx = 0
    for r in range(rows):
        for c in range(cols):
            if cell_idx < len(cell_colors):
                ax.scatter(c, r, marker="s", s=280, color=cell_colors[cell_idx],
                           linewidths=0, zorder=3)
                cell_idx += 1

    # Legend
    from matplotlib.patches import Patch
    handles = [Patch(facecolor=cat_colors[i], label=f"{labels[i]} ({raw_vals[i]}%)")
               for i in range(len(categories))]
    ax.legend(handles=handles, loc="lower left", bbox_to_anchor=(0, -0.18),
              ncol=min(len(labels), 4), frameon=False, fontsize=9,
              labelcolor=text_color)

    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# 4. Dual donut
# ---------------------------------------------------------------------------

def _render_infographic_dual_donut(data, *, colors, accent, bg, text_color, muted, width, height):
    """Concentric double donut chart.

    data:
        outer: {title, segments: [{label, value}]}
        inner: {title, segments: [{label, value}]}
    """
    fig, ax = _plt.subplots(figsize=(width, height))
    fig.patch.set_facecolor(bg)
    ax.set_facecolor(bg)
    ax.set_aspect("equal")
    ax.axis("off")

    outer = data.get("outer", {})
    inner = data.get("inner", {})

    outer_segs = outer.get("segments", [])[:8]
    inner_segs = inner.get("segments", [])[:8]

    outer_vals = [s.get("value", 0) for s in outer_segs]
    inner_vals = [s.get("value", 0) for s in inner_segs]

    outer_colors = _shades_of(colors[0] if colors else accent, max(len(outer_segs), 1))
    inner_colors = _shades_of(colors[1] if len(colors) > 1 else accent, max(len(inner_segs), 1))

    if outer_vals:
        ax.pie(outer_vals, colors=outer_colors, radius=1.0,
               wedgeprops=dict(width=0.35, edgecolor=bg, linewidth=2),
               startangle=90)

    if inner_vals:
        ax.pie(inner_vals, colors=inner_colors, radius=0.60,
               wedgeprops=dict(width=0.35, edgecolor=bg, linewidth=2),
               startangle=90)

    # Center circle (background hole)
    center_circle = _plt.Circle((0, 0), 0.22, color=bg, zorder=5)
    ax.add_artist(center_circle)

    # Titles
    outer_title = outer.get("title", "")
    inner_title = inner.get("title", "")
    if outer_title:
        ax.text(0, 1.20, outer_title, ha="center", va="center",
                fontsize=10, fontweight="bold", color=text_color)
    if inner_title:
        ax.text(0, 0.0, inner_title, ha="center", va="center",
                fontsize=9, color=text_color, zorder=6)

    # Legends: outer on left, inner on right
    from matplotlib.patches import Patch
    if outer_segs:
        handles_outer = [Patch(facecolor=outer_colors[i], label=outer_segs[i].get("label", ""))
                         for i in range(len(outer_segs))]
        fig.legend(handles=handles_outer, loc="center left", bbox_to_anchor=(0.02, 0.5),
                   frameon=False, fontsize=8, labelcolor=text_color,
                   title=outer_title, title_fontsize=9)
    if inner_segs:
        handles_inner = [Patch(facecolor=inner_colors[i], label=inner_segs[i].get("label", ""))
                         for i in range(len(inner_segs))]
        fig.legend(handles=handles_inner, loc="center right", bbox_to_anchor=(0.98, 0.5),
                   frameon=False, fontsize=8, labelcolor=text_color,
                   title=inner_title, title_fontsize=9)

    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# 5. Hexagonal honeycomb
# ---------------------------------------------------------------------------

def _render_infographic_hexagonal_honeycomb(data, *, colors, accent, bg, text_color, muted, width, height):
    """Hexagon grid of content cards.

    data:
        cells: list of {title, value, subtitle}  (3-9 cells)
        columns: int (default 3)
    """
    import numpy as np
    import textwrap
    from matplotlib.patches import RegularPolygon

    cells = data.get("cells", [])[:9]
    n_cols = data.get("columns", 3)
    n = len(cells)
    if n == 0:
        fig, ax = _plt.subplots(figsize=(width, height))
        fig.patch.set_facecolor(bg)
        ax.axis("off")
        fig.tight_layout()
        return fig

    fig, ax = _plt.subplots(figsize=(width, height))
    fig.patch.set_facecolor(bg)
    ax.set_facecolor(bg)
    ax.set_aspect("equal")
    ax.axis("off")

    r = 0.9  # hex radius
    dx = r * np.sqrt(3)   # horizontal spacing
    dy = r * 1.5           # vertical spacing (for flat-top layout we use pointy-top)
    # Pointy-top hexagons
    dx_pt = r * np.sqrt(3)
    dy_pt = r * 1.5

    centers = []
    for i, cell in enumerate(cells):
        col = i % n_cols
        row = i // n_cols
        x = col * dx_pt + (row % 2) * dx_pt / 2
        y = -row * dy_pt
        centers.append((x, y))

    # Center the grid
    if centers:
        cx = sum(p[0] for p in centers) / len(centers)
        cy = sum(p[1] for p in centers) / len(centers)
        centers = [(p[0] - cx, p[1] - cy) for p in centers]

    for i, (cell, (cx, cy)) in enumerate(zip(cells, centers)):
        color = colors[i % len(colors)]
        hex_patch = RegularPolygon(
            (cx, cy), numVertices=6, radius=r * 0.92,
            orientation=0,  # pointy-top
            facecolor=color, edgecolor=bg, linewidth=2, alpha=0.88, zorder=3
        )
        ax.add_patch(hex_patch)

        title = textwrap.fill(cell.get("title", ""), 12)
        value = cell.get("value", "")
        subtitle = textwrap.fill(cell.get("subtitle", ""), 14)

        ax.text(cx, cy + r * 0.25, title, ha="center", va="center",
                fontsize=8, fontweight="bold", color="white", zorder=4,
                multialignment="center")
        if value:
            ax.text(cx, cy - r * 0.05, value, ha="center", va="center",
                    fontsize=13, fontweight="bold", color="white", zorder=4)
        if subtitle:
            ax.text(cx, cy - r * 0.40, subtitle, ha="center", va="center",
                    fontsize=7, color="white", alpha=0.85, zorder=4,
                    multialignment="center")

    # Auto-scale
    all_x = [p[0] for p in centers]
    all_y = [p[1] for p in centers]
    pad = r * 1.2
    ax.set_xlim(min(all_x) - pad, max(all_x) + pad)
    ax.set_ylim(min(all_y) - pad, max(all_y) + pad)

    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# 6. Radial pinwheel
# ---------------------------------------------------------------------------

def _render_infographic_radial_pinwheel(data, *, colors, accent, bg, text_color, muted, width, height):
    """Hub-and-spoke radial diagram with item cards.

    data:
        center: {title, subtitle}
        items: list of {title, body}   (4-8 items)
    """
    import numpy as np
    import textwrap
    from matplotlib.patches import FancyBboxPatch, Circle, FancyArrowPatch

    fig, ax = _plt.subplots(figsize=(width, height))
    fig.patch.set_facecolor(bg)
    ax.set_facecolor(bg)
    ax.set_aspect("equal")
    ax.axis("off")

    center_data = data.get("center", {})
    items = data.get("items", [])[:8]
    n = len(items)
    if n == 0:
        fig.tight_layout()
        return fig

    R = 2.8  # spoke length
    hub_r = 0.65
    card_w, card_h = 1.8, 0.9

    ax.set_xlim(-R - card_w, R + card_w)
    ax.set_ylim(-R - card_h, R + card_h)

    # Hub circle
    hub = Circle((0, 0), hub_r, facecolor=accent, edgecolor=bg, linewidth=2, zorder=5)
    ax.add_patch(hub)
    c_title = center_data.get("title", "")
    c_sub = center_data.get("subtitle", "")
    ax.text(0, 0.1, textwrap.fill(c_title, 10), ha="center", va="center",
            fontsize=9, fontweight="bold", color="white", zorder=6,
            multialignment="center")
    if c_sub:
        ax.text(0, -0.22, textwrap.fill(c_sub, 12), ha="center", va="center",
                fontsize=7, color="white", alpha=0.85, zorder=6,
                multialignment="center")

    for i, item in enumerate(items):
        theta = 2 * np.pi * i / n - np.pi / 2
        ix = R * np.cos(theta)
        iy = R * np.sin(theta)
        color = colors[i % len(colors)]

        # Spoke (from hub edge to card edge)
        spoke_start_x = hub_r * np.cos(theta)
        spoke_start_y = hub_r * np.sin(theta)
        card_edge_x = ix - (card_w / 2) * np.cos(theta)
        card_edge_y = iy - (card_h / 2 + 0.1) * np.sin(theta)

        ax.annotate("", xy=(card_edge_x, card_edge_y),
                    xytext=(spoke_start_x, spoke_start_y),
                    arrowprops=dict(arrowstyle="-", color=muted, lw=1.2,
                                   connectionstyle="arc3,rad=0.0"),
                    zorder=2)

        # Card
        card = FancyBboxPatch(
            (ix - card_w / 2, iy - card_h / 2), card_w, card_h,
            boxstyle="round,pad=0.08", facecolor=color,
            edgecolor=bg, linewidth=1.5, alpha=0.90, zorder=4
        )
        ax.add_patch(card)

        title = textwrap.fill(item.get("title", ""), 18)
        body = textwrap.fill(item.get("body", ""), 22)
        ax.text(ix, iy + 0.22, title, ha="center", va="center",
                fontsize=8, fontweight="bold", color="white", zorder=5,
                multialignment="center")
        if body:
            ax.text(ix, iy - 0.18, body, ha="center", va="center",
                    fontsize=7, color="white", alpha=0.85, zorder=5,
                    multialignment="center")

    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# 7. Semicircle taxonomy
# ---------------------------------------------------------------------------

def _render_infographic_semicircle_taxonomy(data, *, colors, accent, bg, text_color, muted, width, height):
    """Arc-based grouping taxonomy with group arc segments.

    data:
        groups: list of {name, items: [str]}   (2-4 groups)
        center_label: str
    """
    import numpy as np
    import textwrap

    fig, ax = _plt.subplots(figsize=(width, height))
    fig.patch.set_facecolor(bg)
    ax.set_facecolor(bg)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_xlim(-2.2, 2.2)
    ax.set_ylim(-0.5, 2.2)

    groups = data.get("groups", [])[:4]
    center_label = data.get("center_label", "")
    n_groups = len(groups)
    if n_groups == 0:
        fig.tight_layout()
        return fig

    # Total items across all groups
    all_items = []
    for g in groups:
        for item in g.get("items", []):
            all_items.append((item, g))

    n_items = len(all_items)
    group_angles = {}  # group_name -> (start_angle, end_angle)

    # Assign angular spans to groups proportionally
    group_sizes = [len(g.get("items", [])) for g in groups]
    total_size = sum(group_sizes) or 1
    cum_frac = 0.0
    for g, sz in zip(groups, group_sizes):
        frac = sz / total_size
        start_deg = cum_frac * 180
        end_deg = (cum_frac + frac) * 180
        group_angles[g["name"]] = (start_deg, end_deg)
        cum_frac += frac

    R_arc = 1.6   # arc radius for items
    R_grp = 1.85  # arc radius for group labels

    # Draw group arc segments
    for i, g in enumerate(groups):
        color = colors[i % len(colors)]
        start, end = group_angles[g["name"]]
        thetas = np.linspace(np.radians(start), np.radians(end), 60)
        xs_out = R_grp * np.cos(thetas)
        ys_out = R_grp * np.sin(thetas)
        xs_in = (R_grp - 0.15) * np.cos(thetas)
        ys_in = (R_grp - 0.15) * np.sin(thetas)
        ax.fill(
            list(xs_out) + list(xs_in[::-1]),
            list(ys_out) + list(ys_in[::-1]),
            color=color, alpha=0.75, zorder=3
        )
        # Group label at midpoint
        mid_theta = np.radians((start + end) / 2)
        lx = (R_grp + 0.15) * np.cos(mid_theta)
        ly = (R_grp + 0.15) * np.sin(mid_theta)
        ax.text(lx, ly, g["name"], ha="center", va="center",
                fontsize=9, fontweight="bold", color=text_color, zorder=5)

    # Draw items along the main arc
    if n_items > 0:
        for k, (item_text, group) in enumerate(all_items):
            angle_deg = (k + 0.5) / n_items * 180
            theta = np.radians(angle_deg)
            ix = R_arc * np.cos(theta)
            iy = R_arc * np.sin(theta)
            g_name = group["name"]
            g_idx = next((j for j, g in enumerate(groups) if g["name"] == g_name), 0)
            color = colors[g_idx % len(colors)]

            ax.plot([0, ix * 0.85], [0, iy * 0.85], color=muted, lw=0.8, alpha=0.5, zorder=2)
            ax.scatter(ix, iy, color=color, s=80, zorder=4, edgecolors=bg, linewidths=1.5)
            # Label outside
            lx = (R_arc + 0.25) * np.cos(theta)
            ly = (R_arc + 0.25) * np.sin(theta)
            ha = "left" if np.cos(theta) > 0 else "right"
            ax.text(lx, ly, textwrap.fill(item_text, 14), ha=ha, va="center",
                    fontsize=8, color=text_color, zorder=5)

    # Center label
    if center_label:
        ax.text(0, 0, center_label, ha="center", va="center",
                fontsize=11, fontweight="bold", color=text_color, zorder=5)

    # Baseline
    ax.plot([-2.0, 2.0], [0, 0], color=muted, lw=1, alpha=0.4, zorder=1)

    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# 8. Process curved arrows
# ---------------------------------------------------------------------------

def _render_infographic_process_curved_arrows(data, *, colors, accent, bg, text_color, muted, width, height):
    """S-curve step process flow with numbered boxes and curved arrows.

    data:
        steps: list of {number, title, body}   (3-6 steps)
    """
    import numpy as np
    import textwrap
    from matplotlib.patches import FancyBboxPatch, Circle, FancyArrowPatch

    fig, ax = _plt.subplots(figsize=(width, height))
    fig.patch.set_facecolor(bg)
    ax.set_facecolor(bg)
    ax.axis("off")

    steps = data.get("steps", [])[:6]
    n = len(steps)
    if n == 0:
        fig.tight_layout()
        return fig

    # Layout: rows of up to 3
    cols_per_row = min(n, 3)
    n_rows = (n + cols_per_row - 1) // cols_per_row

    card_w = 1.8
    card_h = 1.0
    h_gap = 0.5
    v_gap = 0.8
    total_w = cols_per_row * card_w + (cols_per_row - 1) * h_gap
    total_h = n_rows * card_h + (n_rows - 1) * v_gap

    ax.set_xlim(-0.3, total_w + 0.3)
    ax.set_ylim(-total_h - 0.3, 0.3)

    positions = []
    for i in range(n):
        row = i // cols_per_row
        col = i % cols_per_row
        # Reverse column on odd rows (snake/S-curve)
        if row % 2 == 1:
            col = cols_per_row - 1 - col
        x = col * (card_w + h_gap)
        y = -row * (card_h + v_gap)
        positions.append((x, y))

    for i, (step, (sx, sy)) in enumerate(zip(steps, positions)):
        color = colors[i % len(colors)]

        # Card background
        card = FancyBboxPatch(
            (sx, sy - card_h), card_w, card_h,
            boxstyle="round,pad=0.08", facecolor=color,
            edgecolor=bg, linewidth=1.5, alpha=0.90, zorder=3
        )
        ax.add_patch(card)

        # Step number circle
        num_circle = Circle((sx + 0.22, sy - 0.22), 0.16,
                            facecolor=bg, edgecolor=color, linewidth=2, zorder=4)
        ax.add_patch(num_circle)
        num_str = str(step.get("number", i + 1))
        ax.text(sx + 0.22, sy - 0.22, num_str, ha="center", va="center",
                fontsize=9, fontweight="bold", color=color, zorder=5)

        title = textwrap.fill(step.get("title", ""), 18)
        body = textwrap.fill(step.get("body", ""), 22)
        ax.text(sx + card_w / 2, sy - 0.35, title, ha="center", va="center",
                fontsize=9, fontweight="bold", color="white", zorder=4,
                multialignment="center")
        if body:
            ax.text(sx + card_w / 2, sy - 0.72, body, ha="center", va="center",
                    fontsize=7.5, color="white", alpha=0.88, zorder=4,
                    multialignment="center")

        # Arrow to next step
        if i < n - 1:
            nx, ny = positions[i + 1]
            # Start from right or bottom of card depending on direction
            arrow = FancyArrowPatch(
                (sx + card_w / 2, sy - card_h / 2),
                (nx + card_w / 2, ny - card_h / 2),
                arrowstyle="-|>",
                color=muted, lw=1.5, alpha=0.7,
                connectionstyle="arc3,rad=0.25",
                mutation_scale=15, zorder=2
            )
            ax.add_patch(arrow)

    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# 9. Pyramid detailed
# ---------------------------------------------------------------------------

def _render_infographic_pyramid_detailed(data, *, colors, accent, bg, text_color, muted, width, height):
    """Tiered pyramid with tier labels and right-side detail callouts.

    data:
        tiers: list of {label, detail}   (3-6 tiers, index 0 = apex)
    """
    import numpy as np
    import textwrap
    from matplotlib.patches import Polygon as MplPolygon

    height = data.get("_height", height)
    fig, ax = _plt.subplots(figsize=(width, height))
    fig.patch.set_facecolor(bg)
    ax.set_facecolor(bg)
    ax.axis("off")
    ax.set_xlim(-0.2, 1.3)
    ax.set_ylim(-0.05, 1.05)

    tiers = data.get("tiers", [])[:6]
    n = len(tiers)
    if n == 0:
        fig.tight_layout()
        return fig

    shades = _shades_of(colors[0] if colors else accent, n)

    # Pyramid: tier 0 = apex (top), tier n-1 = base
    tier_h = 0.90 / n
    # Width grows linearly from apex_w to 0.85
    apex_w = 0.10
    base_w = 0.85

    for i, (tier, color) in enumerate(zip(tiers, shades)):
        frac_top = i / n
        frac_bot = (i + 1) / n
        w_top = apex_w + (base_w - apex_w) * frac_top
        w_bot = apex_w + (base_w - apex_w) * frac_bot
        y_top = 0.95 - i * tier_h
        y_bot = y_top - tier_h + 0.004

        pts = [
            (0.5 - w_top / 2, y_top), (0.5 + w_top / 2, y_top),
            (0.5 + w_bot / 2, y_bot), (0.5 - w_bot / 2, y_bot),
        ]
        poly = MplPolygon(pts, closed=True, facecolor=color, edgecolor=bg,
                          linewidth=1.5, zorder=3)
        ax.add_patch(poly)

        y_mid = (y_top + y_bot) / 2
        label = tier.get("label", "")
        detail = tier.get("detail", "")

        ax.text(0.5, y_mid, label, ha="center", va="center",
                fontsize=9, fontweight="bold", color="white", zorder=4)

        if detail:
            # Leader line to right side
            right_x = 0.5 + w_bot / 2
            ax.plot([right_x + 0.02, 0.92], [y_mid, y_mid],
                    color=muted, lw=0.8, alpha=0.6, zorder=4)
            ax.text(0.94, y_mid, textwrap.fill(detail, 28),
                    ha="left", va="center",
                    fontsize=7.5, color=text_color, zorder=4)

    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# 10. Ladder / staircase
# ---------------------------------------------------------------------------

def _render_infographic_ladder(data, *, colors, accent, bg, text_color, muted, width, height):
    """Ascending staircase / ladder diagram.

    data:
        steps: list of {label, body}   (3-6 steps, left=low, right=high)
    """
    import textwrap
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

    fig, ax = _plt.subplots(figsize=(width, height))
    fig.patch.set_facecolor(bg)
    ax.set_facecolor(bg)
    ax.axis("off")

    steps = data.get("steps", [])[:6]
    n = len(steps)
    if n == 0:
        fig.tight_layout()
        return fig

    ax.set_xlim(-0.1, 1.1)
    ax.set_ylim(-0.1, 1.1)

    card_w = 0.7 / n
    card_h = 0.18

    x_step = (1.0 - card_w) / max(n - 1, 1)
    y_step = (0.85 - card_h) / max(n - 1, 1)

    shades = [colors[i % len(colors)] for i in range(n)]

    for i, (step, color) in enumerate(zip(steps, shades)):
        x = i * x_step
        y = 0.05 + i * y_step
        card = FancyBboxPatch(
            (x, y), card_w, card_h,
            boxstyle="round,pad=0.02", facecolor=color,
            edgecolor=bg, linewidth=1.5, alpha=0.90, zorder=3
        )
        ax.add_patch(card)

        label = textwrap.fill(step.get("label", ""), 14)
        body = textwrap.fill(step.get("body", ""), 16)
        ax.text(x + card_w / 2, y + card_h * 0.65, label,
                ha="center", va="center",
                fontsize=8.5, fontweight="bold", color="white", zorder=4,
                multialignment="center")
        if body:
            ax.text(x + card_w / 2, y + card_h * 0.25, body,
                    ha="center", va="center",
                    fontsize=7, color="white", alpha=0.88, zorder=4,
                    multialignment="center")

        # Arrow to next
        if i < n - 1:
            nx = (i + 1) * x_step
            ny = 0.05 + (i + 1) * y_step
            arrow = FancyArrowPatch(
                (x + card_w, y + card_h / 2),
                (nx, ny + card_h / 2),
                arrowstyle="-|>",
                color=muted, lw=1.2, alpha=0.7,
                connectionstyle="arc3,rad=-0.15",
                mutation_scale=12, zorder=2
            )
            ax.add_patch(arrow)

    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# 11. Petal / teardrop burst
# ---------------------------------------------------------------------------

def _render_infographic_petal_teardrop(data, *, colors, accent, bg, text_color, muted, width, height):
    """Petal burst around a central concept.

    data:
        center: {title, subtitle}
        petals: list of {title, value}   (4-8 petals)
    """
    import numpy as np
    import textwrap
    from matplotlib.patches import Circle
    from matplotlib.path import Path
    from matplotlib.patches import PathPatch

    height = data.get("_height", height)
    fig, ax = _plt.subplots(figsize=(width, height))
    fig.patch.set_facecolor(bg)
    ax.set_facecolor(bg)
    ax.set_aspect("equal")
    ax.axis("off")

    center_data = data.get("center", {})
    petals = data.get("petals", [])[:8]
    n = len(petals)
    if n == 0:
        fig.tight_layout()
        return fig

    petal_len = 1.8
    petal_w = 0.55
    hub_r = 0.55

    ax.set_xlim(-(petal_len + 0.5), petal_len + 0.5)
    ax.set_ylim(-(petal_len + 0.5), petal_len + 0.5)

    for i, petal in enumerate(petals):
        theta = 2 * np.pi * i / n - np.pi / 2
        color = colors[i % len(colors)]

        # Petal: two cubic Bezier curves forming a teardrop
        # Tip at (0, petal_len), width at mid-point
        cos_t, sin_t = np.cos(theta), np.sin(theta)

        def rot(x, y):
            return x * cos_t - y * sin_t, x * sin_t + y * cos_t

        p0 = rot(0, 0)
        ctrl1 = rot(petal_w, petal_len * 0.4)
        ctrl2 = rot(petal_w, petal_len * 0.8)
        tip = rot(0, petal_len)
        ctrl3 = rot(-petal_w, petal_len * 0.8)
        ctrl4 = rot(-petal_w, petal_len * 0.4)

        verts = [p0, ctrl1, ctrl2, tip, ctrl3, ctrl4, p0]
        codes = [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4,
                 Path.CURVE4, Path.CURVE4, Path.CURVE4]
        path = Path(verts, codes)
        patch = PathPatch(path, facecolor=color, edgecolor=bg,
                          linewidth=1.5, alpha=0.82, zorder=3)
        ax.add_patch(patch)

        # Label near tip
        tip_x, tip_y = rot(0, petal_len * 0.70)
        title = textwrap.fill(petal.get("title", ""), 12)
        value = petal.get("value", "")
        ax.text(tip_x, tip_y + 0.10, title, ha="center", va="center",
                fontsize=8, fontweight="bold", color="white", zorder=4,
                multialignment="center")
        if value:
            ax.text(tip_x, tip_y - 0.18, value, ha="center", va="center",
                    fontsize=11, fontweight="bold", color="white", zorder=4)

    # Center hub
    hub = Circle((0, 0), hub_r, facecolor=accent, edgecolor=bg,
                 linewidth=2, zorder=5)
    ax.add_patch(hub)
    c_title = center_data.get("title", "")
    c_sub = center_data.get("subtitle", "")
    ax.text(0, 0.12, textwrap.fill(c_title, 10), ha="center", va="center",
            fontsize=9, fontweight="bold", color="white", zorder=6,
            multialignment="center")
    if c_sub:
        ax.text(0, -0.18, textwrap.fill(c_sub, 12), ha="center", va="center",
                fontsize=7.5, color="white", alpha=0.85, zorder=6,
                multialignment="center")

    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# 12. Funnel KPI strip
# ---------------------------------------------------------------------------

def _render_infographic_funnel_kpi_strip(data, *, colors, accent, bg, text_color, muted, width, height):
    """Funnel in top panel + KPI metric cards in bottom strip.

    data:
        stages: list of {label, value}   (3-6 stages)
        kpis:   list of {metric, value}  (3-5 KPIs)
    """
    import textwrap
    from matplotlib.gridspec import GridSpec
    from matplotlib.patches import Polygon as MplPolygon, FancyBboxPatch

    fig = _plt.figure(figsize=(width, height))
    fig.patch.set_facecolor(bg)

    gs = GridSpec(2, 1, figure=fig, height_ratios=[3, 1], hspace=0.08)
    ax_funnel = fig.add_subplot(gs[0])
    ax_kpi = fig.add_subplot(gs[1])

    for ax in (ax_funnel, ax_kpi):
        ax.set_facecolor(bg)
        ax.axis("off")

    stages = data.get("stages", [])[:6]
    kpis = data.get("kpis", [])[:5]
    n_stages = len(stages)

    # --- Funnel in ax_funnel ---
    if n_stages:
        ax_funnel.set_xlim(-1, 1)
        ax_funnel.set_ylim(-0.05, 1.05)

        band_h = 0.90 / n_stages
        widths = [0.9 - (0.9 - 0.2) * (i / max(n_stages, 1)) for i in range(n_stages + 1)]

        for i, stage in enumerate(stages):
            color = colors[i % len(colors)]
            y_top = 0.95 - i * band_h
            y_bot = y_top - band_h + 0.005
            w_top = widths[i]
            w_bot = widths[i + 1]
            pts = [
                (-w_top / 2, y_top), (w_top / 2, y_top),
                (w_bot / 2, y_bot), (-w_bot / 2, y_bot),
            ]
            poly = MplPolygon(pts, closed=True, facecolor=color, edgecolor=bg,
                              linewidth=1.5, zorder=3, alpha=0.88,
                              transform=ax_funnel.transData)
            ax_funnel.add_patch(poly)
            y_mid = (y_top + y_bot) / 2
            label = stage.get("label", "")
            value = stage.get("value", "")
            ax_funnel.text(0, y_mid, label, ha="center", va="center",
                           fontsize=9, fontweight="bold", color="white", zorder=4)
            if value:
                ax_funnel.text(w_bot / 2 + 0.05, y_mid, str(value), ha="left", va="center",
                               fontsize=8.5, color=text_color, zorder=4)

    # --- KPI strip in ax_kpi ---
    if kpis:
        n_kpis = len(kpis)
        ax_kpi.set_xlim(0, n_kpis)
        ax_kpi.set_ylim(0, 1)
        card_w = 0.85
        for j, kpi in enumerate(kpis):
            cx = j + 0.5
            card = FancyBboxPatch(
                (j + 0.075, 0.1), card_w, 0.8,
                boxstyle="round,pad=0.04", facecolor=colors[j % len(colors)],
                edgecolor=bg, linewidth=1.2, alpha=0.88, zorder=3,
                transform=ax_kpi.transData
            )
            ax_kpi.add_patch(card)
            ax_kpi.text(cx, 0.68, kpi.get("value", ""), ha="center", va="center",
                        fontsize=14, fontweight="bold", color="white", zorder=4)
            ax_kpi.text(cx, 0.28, textwrap.fill(kpi.get("metric", ""), 16),
                        ha="center", va="center",
                        fontsize=7.5, color="white", alpha=0.85, zorder=4,
                        multialignment="center")

    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# 13. Persona dashboard
# ---------------------------------------------------------------------------

def _render_infographic_persona_dashboard(data, *, colors, accent, bg, text_color, muted, width, height):
    """User persona card with avatar, name/role, and attribute grid.

    data:
        name: str
        role: str
        avatar_initial: str
        attributes: list of {label, value}   (4-8 attributes)
    """
    import textwrap
    from matplotlib.gridspec import GridSpec
    from matplotlib.patches import Circle, FancyBboxPatch

    fig = _plt.figure(figsize=(width, height))
    fig.patch.set_facecolor(bg)
    gs = GridSpec(3, 4, figure=fig, hspace=0.4, wspace=0.3)

    ax_avatar = fig.add_subplot(gs[0:2, 0])
    ax_info = fig.add_subplot(gs[0:2, 1:])
    ax_attrs = fig.add_subplot(gs[2, :])

    for ax in (ax_avatar, ax_info, ax_attrs):
        ax.set_facecolor(bg)
        ax.axis("off")

    name = data.get("name", "Persona")
    role = data.get("role", "")
    initial = data.get("avatar_initial", name[0].upper() if name else "?")
    attributes = data.get("attributes", [])[:8]

    # Avatar
    ax_avatar.set_xlim(-1, 1)
    ax_avatar.set_ylim(-1, 1)
    circ = Circle((0, 0), 0.75, facecolor=accent, edgecolor=bg, linewidth=2, zorder=3)
    ax_avatar.add_patch(circ)
    ax_avatar.text(0, 0, initial.upper(), ha="center", va="center",
                   fontsize=32, fontweight="bold", color="white", zorder=4)
    ax_avatar.set_aspect("equal")

    # Name / role
    ax_info.set_xlim(0, 1)
    ax_info.set_ylim(0, 1)
    ax_info.text(0.05, 0.70, name, ha="left", va="center",
                 fontsize=16, fontweight="bold", color=text_color)
    ax_info.text(0.05, 0.40, role, ha="left", va="center",
                 fontsize=11, color=muted)
    # Accent underline
    ax_info.axhline(0.55, xmin=0.03, xmax=0.97, color=accent, lw=2, alpha=0.6)

    # Attributes grid
    n_attrs = len(attributes)
    if n_attrs:
        ax_attrs.set_xlim(0, n_attrs)
        ax_attrs.set_ylim(0, 1)
        card_w = 0.88
        for j, attr in enumerate(attributes):
            color = colors[j % len(colors)]
            card = FancyBboxPatch(
                (j + 0.06, 0.08), card_w, 0.84,
                boxstyle="round,pad=0.03", facecolor=color,
                edgecolor=bg, linewidth=1.2, alpha=0.85, zorder=3,
                transform=ax_attrs.transData
            )
            ax_attrs.add_patch(card)
            ax_attrs.text(j + 0.5, 0.65, attr.get("value", ""),
                          ha="center", va="center",
                          fontsize=12, fontweight="bold", color="white", zorder=4)
            ax_attrs.text(j + 0.5, 0.28,
                          textwrap.fill(attr.get("label", ""), 12),
                          ha="center", va="center",
                          fontsize=7.5, color="white", alpha=0.85, zorder=4,
                          multialignment="center")

    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# 14. Sidebar profile
# ---------------------------------------------------------------------------

def _render_infographic_sidebar_profile(data, *, colors, accent, bg, text_color, muted, width, height):
    """Two-panel card: colored sidebar (avatar/name/tags) + content panel.

    data:
        profile: {name, role, avatar_initial, tags: [str]}
        content: {title, items: [str]}
    """
    import textwrap
    from matplotlib.gridspec import GridSpec
    from matplotlib.patches import Circle, FancyBboxPatch, Patch

    fig = _plt.figure(figsize=(width, height))
    fig.patch.set_facecolor(bg)
    gs = GridSpec(1, 2, figure=fig, width_ratios=[1, 3], wspace=0)

    ax_left = fig.add_subplot(gs[0])
    ax_right = fig.add_subplot(gs[1])

    profile = data.get("profile", {})
    content = data.get("content", {})

    # Left sidebar: colored background
    sidebar_color = colors[0] if colors else accent
    ax_left.set_facecolor(sidebar_color)
    ax_left.axis("off")
    ax_left.set_xlim(-1, 1)
    ax_left.set_ylim(-1, 1)

    # Avatar circle
    initial = profile.get("avatar_initial", "?")
    circ = Circle((0, 0.55), 0.30, facecolor=bg, edgecolor=bg,
                  linewidth=2, zorder=3)
    ax_left.add_patch(circ)
    ax_left.text(0, 0.55, initial.upper(), ha="center", va="center",
                 fontsize=20, fontweight="bold", color=sidebar_color, zorder=4)
    ax_left.set_aspect("equal")

    name = profile.get("name", "")
    role = profile.get("role", "")
    tags = profile.get("tags", [])[:4]

    ax_left.text(0, 0.10, textwrap.fill(name, 12), ha="center", va="center",
                 fontsize=9, fontweight="bold", color="white", zorder=4,
                 multialignment="center")
    ax_left.text(0, -0.15, textwrap.fill(role, 14), ha="center", va="center",
                 fontsize=7.5, color="white", alpha=0.85, zorder=4,
                 multialignment="center")

    for k, tag in enumerate(tags):
        ty = -0.40 - k * 0.18
        tag_box = FancyBboxPatch((-0.55, ty - 0.07), 1.10, 0.14,
                                 boxstyle="round,pad=0.02", facecolor=bg,
                                 alpha=0.25, edgecolor="none", zorder=4,
                                 transform=ax_left.transData)
        ax_left.add_patch(tag_box)
        ax_left.text(0, ty, tag, ha="center", va="center",
                     fontsize=7, color="white", zorder=5)

    # Right content panel
    ax_right.set_facecolor(bg)
    ax_right.axis("off")
    ax_right.set_xlim(0, 1)
    ax_right.set_ylim(0, 1)

    c_title = content.get("title", "")
    items = content.get("items", [])

    ax_right.text(0.06, 0.90, c_title, ha="left", va="center",
                  fontsize=13, fontweight="bold", color=text_color)
    ax_right.axhline(0.82, xmin=0.03, xmax=0.97, color=accent, lw=1.5, alpha=0.5)

    for k, item in enumerate(items[:8]):
        iy = 0.73 - k * 0.10
        ax_right.text(0.06, iy, "•", ha="left", va="center",
                      fontsize=10, color=accent)
        ax_right.text(0.12, iy, textwrap.fill(item, 48), ha="left", va="center",
                      fontsize=9, color=text_color)

    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# 15. Metaphor backdrop
# ---------------------------------------------------------------------------

def _render_infographic_metaphor_backdrop(data, *, colors, accent, bg, text_color, muted, width, height):
    """Programmatic backdrop silhouette with overlaid content cards.

    data:
        backdrop: "building" | "circuit" | "mountain"
        items: list of {title, body}   (3-5 items)
    """
    import numpy as np
    import textwrap
    from matplotlib.patches import Rectangle, Polygon as MplPolygon, Circle, FancyBboxPatch

    fig, ax = _plt.subplots(figsize=(width, height))
    fig.patch.set_facecolor(bg)
    ax.set_facecolor(bg)
    ax.axis("off")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)

    backdrop = data.get("backdrop", "building")
    items = data.get("items", [])[:5]
    n = len(items)

    # ---- Backdrop silhouettes ----
    backdrop_alpha = 0.12
    backdrop_color = colors[0] if colors else accent

    if backdrop == "building":
        # Main building body
        ax.add_patch(Rectangle((3.0, 0.5), 4.0, 4.5, facecolor=backdrop_color,
                                alpha=backdrop_alpha, zorder=1))
        # Tower
        ax.add_patch(Rectangle((4.5, 5.0), 1.0, 1.0, facecolor=backdrop_color,
                                alpha=backdrop_alpha, zorder=1))
        # Window grid
        for row in range(4):
            for col in range(3):
                wx = 3.4 + col * 1.1
                wy = 0.8 + row * 0.95
                ax.add_patch(Rectangle((wx, wy), 0.5, 0.55,
                                       facecolor=backdrop_color,
                                       alpha=backdrop_alpha * 2, zorder=1))

    elif backdrop == "mountain":
        # Main peak
        mountain = MplPolygon(
            [(1, 0.5), (5, 5.5), (9, 0.5)], closed=True,
            facecolor=backdrop_color, alpha=backdrop_alpha, zorder=1
        )
        ax.add_patch(mountain)
        # Snow cap
        snowcap = MplPolygon(
            [(4.2, 4.4), (5, 5.5), (5.8, 4.4)], closed=True,
            facecolor="white", alpha=0.5, zorder=2
        )
        ax.add_patch(snowcap)
        # Secondary hill
        hill = MplPolygon(
            [(6.5, 0.5), (8.5, 3.0), (10, 0.5)], closed=True,
            facecolor=backdrop_color, alpha=backdrop_alpha * 0.7, zorder=1
        )
        ax.add_patch(hill)

    elif backdrop == "circuit":
        # Horizontal and vertical traces
        for y in [1.5, 3.0, 4.5]:
            ax.plot([0.5, 9.5], [y, y], color=backdrop_color,
                    lw=1.5, alpha=backdrop_alpha * 3, zorder=1)
        for x in [2.0, 4.0, 6.0, 8.0]:
            ax.plot([x, x], [0.5, 5.5], color=backdrop_color,
                    lw=1.5, alpha=backdrop_alpha * 3, zorder=1)
        # Nodes at intersections
        for x in [2.0, 4.0, 6.0, 8.0]:
            for y in [1.5, 3.0, 4.5]:
                circ = Circle((x, y), 0.12, facecolor=backdrop_color,
                              alpha=backdrop_alpha * 5, zorder=2)
                ax.add_patch(circ)

    # ---- Content cards overlaid ----
    if n > 0:
        card_positions = []
        if n <= 3:
            for i in range(n):
                card_positions.append((1.0 + i * 3.0, 2.0))
        elif n <= 5:
            # Top row: ceil(n/2), bottom row: floor(n/2)
            top = (n + 1) // 2
            bot = n // 2
            for i in range(top):
                card_positions.append((0.5 + i * (9.0 / max(top, 1)), 3.5))
            for i in range(bot):
                card_positions.append((1.5 + i * (9.0 / max(bot, 1)), 1.0))

        card_w, card_h = 2.4, 1.6
        for i, (item, (cx, cy)) in enumerate(zip(items, card_positions)):
            color = colors[i % len(colors)]
            card = FancyBboxPatch(
                (cx - card_w / 2, cy - card_h / 2), card_w, card_h,
                boxstyle="round,pad=0.1", facecolor=color,
                edgecolor=bg, linewidth=1.5, alpha=0.88, zorder=4
            )
            ax.add_patch(card)
            title = textwrap.fill(item.get("title", ""), 18)
            body = textwrap.fill(item.get("body", ""), 22)
            ax.text(cx, cy + 0.38, title, ha="center", va="center",
                    fontsize=9, fontweight="bold", color="white", zorder=5,
                    multialignment="center")
            if body:
                ax.text(cx, cy - 0.28, body, ha="center", va="center",
                        fontsize=7.5, color="white", alpha=0.88, zorder=5,
                        multialignment="center")

    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# 16. Chart row (composited mini-charts)
# ---------------------------------------------------------------------------

def _render_infographic_chart_row(data, *, colors, accent, bg, text_color, muted, width, height):
    """Side-by-side mini charts composited into one figure.

    data:
        charts: list of {chart_type, data, title}   (2-4 charts)
    """
    import tempfile
    import numpy as np
    from pathlib import Path as _Path
    from matplotlib.gridspec import GridSpec

    charts = data.get("charts", [])[:4]
    n = len(charts)
    if n == 0:
        fig, ax = _plt.subplots(figsize=(width, height))
        fig.patch.set_facecolor(bg)
        ax.axis("off")
        fig.tight_layout()
        return fig

    fig = _plt.figure(figsize=(width, height))
    fig.patch.set_facecolor(bg)
    gs = GridSpec(1, n, figure=fig, wspace=0.08)

    sub_w = width / n
    sub_h = height - 0.4  # leave room for title

    for i, chart_spec in enumerate(charts):
        chart_type = chart_spec.get("chart_type", "bar")
        chart_data = chart_spec.get("data", {})
        chart_title = chart_spec.get("title", "")

        # Render to a temp file
        tmp = _Path(tempfile.mktemp(suffix=".png"))
        try:
            render_chart(
                chart_type, chart_data, tmp,
                brand_colors=colors,
                accent=accent, bg=bg, text_color=text_color, muted=muted,
                width=sub_w, height=sub_h, dpi=150,
                color_mode="palette",
            )
            ax_sub = fig.add_subplot(gs[i])
            ax_sub.set_facecolor(bg)
            if tmp.exists():
                img = _plt.imread(str(tmp))
                ax_sub.imshow(img, aspect="auto")
            ax_sub.axis("off")
            if chart_title:
                ax_sub.set_title(chart_title, fontsize=9, fontweight="bold",
                                 color=text_color, pad=4)
        finally:
            if tmp.exists():
                try:
                    tmp.unlink()
                except OSError:
                    pass

    fig.tight_layout()
    return fig
