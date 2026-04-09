"""Chart renderer — generates publication-quality chart images via matplotlib.

Produces PNG files that can be embedded in Typst slides via the ``chart``
slide type. Applies brand colors and consistent styling.

Supported chart types:
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

    fig.savefig(str(output_path), dpi=dpi, bbox_inches="tight",
                facecolor=bg, edgecolor="none", transparent=False)
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
        xs = [p["x"] for p in pts]
        ys = [p["y"] for p in pts]
        sizes = [p.get("size", 60) for p in pts]
        ax.scatter(xs, ys, c=color, s=sizes, alpha=0.7, label=group_name if group_name != "default" else None, edgecolors="white", linewidth=0.5)

        # Label points
        for p in pts:
            if p.get("label"):
                ax.annotate(p["label"], (p["x"], p["y"]), fontsize=8, color=text_color,
                            textcoords="offset points", xytext=(5, 5))

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
    ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=9)
    ax.axhline(y=0, color=muted, linewidth=0.5)
    ax.grid(axis="y", alpha=0.2, color=muted)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Donut chart
# ---------------------------------------------------------------------------

def _render_donut(data, *, colors, accent, bg, text_color, muted, width, height):
    """Donut chart (max 6 segments) — uses shades of accent for brand consistency.

    data:
        segments: list of {label, value}
        center_label: str (optional — text in center)
    """
    fig, ax = _plt.subplots(figsize=(min(width, height), min(width, height)))
    fig.patch.set_facecolor(bg)

    segments = data.get("segments", [])[:6]
    labels = [s["label"] for s in segments]
    values = [s["value"] for s in segments]

    # Use shades of accent (mono palette) — NOT rainbow.
    # Each segment gets a different opacity / lightness of the brand colour.
    seg_colors = _shades_of(accent, len(segments))

    wedges, texts, autotexts = ax.pie(
        values, labels=labels, colors=seg_colors, autopct="%1.0f%%",
        startangle=90, pctdistance=0.75, labeldistance=1.1,
        wedgeprops={"width": 0.4, "edgecolor": bg, "linewidth": 2},
    )
    for t in texts:
        t.set_color(text_color)
        t.set_fontsize(9)
    for t in autotexts:
        t.set_color("white")
        t.set_fontsize(9)
        t.set_fontweight("bold")

    if data.get("center_label"):
        ax.text(0, 0, data["center_label"], ha="center", va="center",
                fontsize=14, fontweight="bold", color=text_color)

    fig.tight_layout()
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

    data:
        axes: list of str (axis labels)
        series: list of {name, values} (values 0-100 or 0-max)
    """
    import numpy as np

    fig, ax = _plt.subplots(figsize=(min(width, height), min(width, height)),
                             subplot_kw={"projection": "polar"})
    fig.patch.set_facecolor(bg)

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
        ax.plot(angles, values, color=color, linewidth=2, label=s.get("name", ""))
        ax.fill(angles, values, color=color, alpha=0.15)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(axes_labels, fontsize=9, color=text_color)
    ax.tick_params(axis="y", labelsize=8, colors=muted)
    ax.grid(color=muted, alpha=0.3)
    ax.set_facecolor(bg)

    if len(series) > 1:
        ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.0), frameon=False, fontsize=9, labelcolor=text_color)

    fig.tight_layout()
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
        "line_chart", "area_chart", "scatter", "waterfall",
        "donut", "pie", "stacked_bar", "grouped_bar",
        "heatmap", "radar", "gauge",
    ]
