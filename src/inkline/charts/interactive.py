"""Interactive chart renderer -- Plotly HTML charts with brand theming.

Alternative backend to the matplotlib chart_renderer. Produces interactive
HTML files or Plotly JSON specs for web dashboard embedding. Same data
format conventions as the matplotlib renderer -- the two are interchangeable.

Supported: line_chart, area_chart, scatter, waterfall, donut, pie,
stacked_bar, grouped_bar, heatmap, radar, gauge.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Optional

log = logging.getLogger(__name__)

_go = None  # plotly.graph_objects (lazy)
_pio = None  # plotly.io (lazy)


def _ensure_plotly():
    global _go, _pio
    if _go is None:
        import plotly.graph_objects as go
        import plotly.io as pio
        _go = go
        _pio = pio


def _rgba(hex_color: str, alpha: float) -> str:
    """Hex color to rgba() string for Plotly."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def _shades_of(hex_color: str, n: int) -> list[str]:
    """Return *n* shades from full intensity to lighter tint."""
    if n <= 0:
        return []
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    out = []
    for i in range(n):
        t = i / max(n - 1, 1)
        mix = 0.65 * t
        rr = int(r + (255 - r) * mix)
        gg = int(g + (255 - g) * mix)
        bb = int(b + (255 - b) * mix)
        out.append(f"#{rr:02X}{gg:02X}{bb:02X}")
    return out


def _load_brand_colors(brand_name: Optional[str]) -> dict[str, Any]:
    """Load brand colors, falling back to sensible defaults."""
    defaults = {
        "primary": "#6366F1", "secondary": "#F59E0B",
        "background": "#FAFAFA", "text": "#1A1A1A", "muted": "#64748B",
        "chart_colors": ["#6366F1", "#F59E0B", "#10B981", "#F43F5E", "#3B82F6", "#8B5CF6"],
    }
    if not brand_name:
        return defaults
    try:
        from inkline.brands import get_brand
        brand = get_brand(brand_name)
        return {
            "primary": brand.primary, "secondary": brand.secondary,
            "background": brand.background, "text": brand.text,
            "muted": brand.muted, "chart_colors": brand.chart_colors,
        }
    except Exception:
        log.warning("Could not load brand %r, using defaults", brand_name)
        return defaults


def _base_layout(bc: dict[str, Any], **overrides) -> dict[str, Any]:
    """Shared Plotly layout with brand theming."""
    axis = lambda: dict(gridcolor=bc["muted"], gridwidth=0.5, griddash="dot",
                        linecolor=bc["muted"], zerolinecolor=bc["muted"])
    layout = dict(
        paper_bgcolor=bc["background"], plot_bgcolor=bc["background"],
        font=dict(color=bc["text"], family="Inter, system-ui, sans-serif", size=13),
        margin=dict(l=60, r=30, t=40, b=60),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=bc["text"], size=11)),
        xaxis=axis(), yaxis=axis(),
    )
    layout.update(overrides)
    return layout


# -- Chart renderers --------------------------------------------------------

def _render_line_chart(data: dict, bc: dict) -> Any:
    _ensure_plotly()
    fig, x, colors = _go.Figure(), data.get("x", []), bc["chart_colors"]
    for i, s in enumerate(data.get("series", [])):
        fig.add_trace(_go.Scatter(
            x=x, y=s["values"],
            mode="lines+markers" if len(x) <= 20 else "lines",
            name=s.get("name", f"Series {i+1}"),
            line=dict(color=colors[i % len(colors)], width=2.5),
            marker=dict(size=6),
        ))
    layout = _base_layout(bc)
    if data.get("x_label"): layout["xaxis"]["title"] = data["x_label"]
    if data.get("y_label"): layout["yaxis"]["title"] = data["y_label"]
    fig.update_layout(**layout)
    return fig


def _render_area_chart(data: dict, bc: dict) -> Any:
    _ensure_plotly()
    fig, x, colors = _go.Figure(), data.get("x", []), bc["chart_colors"]
    for i, s in enumerate(data.get("series", [])):
        color = colors[i % len(colors)]
        fig.add_trace(_go.Scatter(
            x=x, y=s["values"], mode="lines",
            name=s.get("name", f"Series {i+1}"),
            fill="tozeroy", line=dict(color=color, width=2),
            fillcolor=_rgba(color, 0.3),
        ))
    fig.update_layout(**_base_layout(bc))
    return fig


def _render_scatter(data: dict, bc: dict) -> Any:
    _ensure_plotly()
    fig, colors = _go.Figure(), bc["chart_colors"]
    groups: dict[str, list] = {}
    for p in data.get("points", []):
        groups.setdefault(p.get("group", "default"), []).append(p)
    for i, (gname, pts) in enumerate(groups.items()):
        color = colors[i % len(colors)]
        fig.add_trace(_go.Scatter(
            x=[p["x"] for p in pts], y=[p["y"] for p in pts],
            mode="markers+text", name=gname if gname != "default" else None,
            text=[p.get("label", "") for p in pts], textposition="top right",
            textfont=dict(size=9, color=bc["muted"]),
            marker=dict(color=color, size=[p.get("size", 10) for p in pts],
                        opacity=0.7, line=dict(color="white", width=1)),
            showlegend=gname != "default",
        ))
    layout = _base_layout(bc)
    if data.get("x_label"): layout["xaxis"]["title"] = data["x_label"]
    if data.get("y_label"): layout["yaxis"]["title"] = data["y_label"]
    fig.update_layout(**layout)
    return fig


def _render_waterfall(data: dict, bc: dict) -> Any:
    _ensure_plotly()
    items = data.get("items", [])
    labels = [it["label"] for it in items]
    values = [it["value"] for it in items]
    measures = ["total" if it.get("total") else "relative" for it in items]
    fig = _go.Figure(_go.Waterfall(
        x=labels, y=values, measure=measures,
        connector=dict(line=dict(color=bc["muted"], width=1)),
        increasing=dict(marker=dict(color=bc["primary"])),
        decreasing=dict(marker=dict(color=bc["secondary"])),
        totals=dict(marker=dict(color=bc["primary"])),
        textposition="outside",
        text=[f"{v:+,.0f}" if m != "total" else f"{v:,.0f}" for v, m in zip(values, measures)],
        textfont=dict(size=11),
    ))
    fig.update_layout(**_base_layout(bc))
    return fig


def _render_donut(data: dict, bc: dict) -> Any:
    _ensure_plotly()
    segments = data.get("segments", [])[:6]
    labels = [s["label"] for s in segments]
    values = [s["value"] for s in segments]
    seg_colors = _shades_of(bc["primary"], len(segments))
    fig = _go.Figure(_go.Pie(
        labels=labels, values=values, hole=0.55,
        marker=dict(colors=seg_colors, line=dict(color=bc["background"], width=2)),
        textinfo="label+percent", textfont=dict(size=12),
        insidetextorientation="auto",
    ))
    annotations = []
    if data.get("center_label"):
        annotations.append(dict(
            text=f"<b>{data['center_label']}</b>", x=0.5, y=0.5,
            font=dict(size=16, color=bc["text"]), showarrow=False,
        ))
    fig.update_layout(**_base_layout(bc, annotations=annotations), showlegend=True)
    return fig


def _render_pie(data: dict, bc: dict) -> Any:
    _ensure_plotly()
    segments = data.get("segments", [])[:6]
    labels = [s["label"] for s in segments]
    values = [s["value"] for s in segments]
    seg_colors = _shades_of(bc["primary"], len(segments))
    fig = _go.Figure(_go.Pie(
        labels=labels, values=values, hole=0,
        marker=dict(colors=seg_colors, line=dict(color=bc["background"], width=2)),
        textinfo="label+percent", textfont=dict(size=12),
    ))
    fig.update_layout(**_base_layout(bc), showlegend=True)
    return fig


def _render_stacked_bar(data: dict, bc: dict) -> Any:
    _ensure_plotly()
    fig = _go.Figure()
    categories = data.get("categories", [])
    series = data.get("series", [])
    seg_colors = _shades_of(bc["primary"], len(series))
    for i, s in enumerate(series):
        fig.add_trace(_go.Bar(
            x=categories, y=s["values"],
            name=s.get("name", f"Series {i+1}"), marker_color=seg_colors[i],
        ))
    fig.update_layout(**_base_layout(bc), barmode="stack")
    return fig


def _render_grouped_bar(data: dict, bc: dict) -> Any:
    _ensure_plotly()
    fig, colors = _go.Figure(), bc["chart_colors"]
    for i, s in enumerate(data.get("series", [])):
        fig.add_trace(_go.Bar(
            x=data.get("categories", []), y=s["values"],
            name=s.get("name", f"Series {i+1}"), marker_color=colors[i % len(colors)],
        ))
    fig.update_layout(**_base_layout(bc), barmode="group")
    return fig


def _render_heatmap(data: dict, bc: dict) -> Any:
    _ensure_plotly()
    fig = _go.Figure(_go.Heatmap(
        z=data.get("matrix", [[]]),
        x=data.get("x_labels", []), y=data.get("y_labels", []),
        colorscale=data.get("colormap", "RdYlGn"),
        texttemplate="%{z:.1f}", textfont=dict(size=11),
        hovertemplate="x: %{x}<br>y: %{y}<br>value: %{z:.2f}<extra></extra>",
    ))
    fig.update_layout(**_base_layout(bc))
    return fig


def _render_radar(data: dict, bc: dict) -> Any:
    _ensure_plotly()
    fig, colors = _go.Figure(), bc["chart_colors"]
    axes_labels = data.get("axes", [])
    for i, s in enumerate(data.get("series", [])):
        color = colors[i % len(colors)]
        values = s["values"] + s["values"][:1]
        theta = axes_labels + axes_labels[:1]
        fig.add_trace(_go.Scatterpolar(
            r=values, theta=theta, fill="toself",
            fillcolor=_rgba(color, 0.15),
            name=s.get("name", f"Series {i+1}"),
            line=dict(color=color, width=2.2),
        ))
    fig.update_layout(
        **_base_layout(bc),
        polar=dict(
            bgcolor=bc["background"],
            radialaxis=dict(visible=True, gridcolor=bc["muted"], gridwidth=0.5, linecolor=bc["muted"]),
            angularaxis=dict(gridcolor=bc["muted"], gridwidth=0.5, linecolor=bc["muted"]),
        ),
    )
    return fig


def _render_gauge(data: dict, bc: dict) -> Any:
    _ensure_plotly()
    value, label = data.get("value", 0), data.get("label", "")
    thresholds = data.get("thresholds", [
        {"value": 33, "color": "#dc2626"},
        {"value": 66, "color": "#f59e0b"},
        {"value": 100, "color": "#10b981"},
    ])
    steps, prev = [], 0
    for t in thresholds:
        steps.append(dict(range=[prev, t["value"]], color=_rgba(t["color"], 0.2)))
        prev = t["value"]
    fig = _go.Figure(_go.Indicator(
        mode="gauge+number", value=value,
        number=dict(suffix="%", font=dict(size=36, color=bc["text"])),
        title=dict(text=label, font=dict(size=14, color=bc["muted"])),
        gauge=dict(
            axis=dict(range=[0, 100], tickcolor=bc["muted"]),
            bar=dict(color=bc["primary"]),
            bgcolor=bc["background"], bordercolor=bc["muted"], steps=steps,
        ),
    ))
    fig.update_layout(**_base_layout(bc, margin=dict(l=30, r=30, t=60, b=30)))
    return fig


# -- Registry ---------------------------------------------------------------

_RENDERERS = {
    "line_chart": _render_line_chart, "area_chart": _render_area_chart,
    "scatter": _render_scatter, "waterfall": _render_waterfall,
    "donut": _render_donut, "pie": _render_pie,
    "stacked_bar": _render_stacked_bar, "grouped_bar": _render_grouped_bar,
    "heatmap": _render_heatmap, "radar": _render_radar, "gauge": _render_gauge,
}


# -- Public API -------------------------------------------------------------

def render_interactive_chart(
    chart_type: str,
    data: dict[str, Any],
    output_path: str | Path,
    brand_name: Optional[str] = None,
    *,
    width: int = 800,
    height: int = 500,
    include_plotlyjs: bool = True,
    **kwargs,
) -> Path:
    """Render an interactive Plotly chart to an HTML file.

    Same chart_type names and data schemas as the matplotlib renderer.
    Set *include_plotlyjs* to ``"cdn"`` for smaller output files.
    """
    _ensure_plotly()
    renderer = _RENDERERS.get(chart_type)
    if not renderer:
        raise ValueError(f"Unknown chart type: {chart_type}. Available: {list(_RENDERERS.keys())}")
    bc = _load_brand_colors(brand_name)
    fig = renderer(data, bc)
    fig.update_layout(width=width, height=height)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _pio.write_html(fig, str(output_path), include_plotlyjs=include_plotlyjs, full_html=True)
    log.info("Interactive chart rendered: %s (%s, %d bytes)", chart_type, output_path, output_path.stat().st_size)
    return output_path


def render_interactive_chart_json(
    chart_type: str,
    data: dict[str, Any],
    brand_name: Optional[str] = None,
    *,
    width: int = 800,
    height: int = 500,
    **kwargs,
) -> dict:
    """Return the Plotly JSON spec (``data`` + ``layout``) for dashboard embedding."""
    _ensure_plotly()
    renderer = _RENDERERS.get(chart_type)
    if not renderer:
        raise ValueError(f"Unknown chart type: {chart_type}. Available: {list(_RENDERERS.keys())}")
    bc = _load_brand_colors(brand_name)
    fig = renderer(data, bc)
    fig.update_layout(width=width, height=height)
    return json.loads(fig.to_json())


def list_chart_types() -> list[str]:
    """Return all supported interactive chart types."""
    return list(_RENDERERS.keys())
