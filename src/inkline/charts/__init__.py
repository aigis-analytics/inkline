"""Chart backends -- static (matplotlib) and interactive (Plotly).

Usage::

    # Interactive HTML charts (Plotly)
    from inkline.charts import render_interactive_chart, render_interactive_chart_json

    render_interactive_chart("bar", data, "output.html", brand_name="minimal")
    spec = render_interactive_chart_json("bar", data, brand_name="minimal")

    # Static PNG charts (matplotlib) -- original backend
    from inkline.typst.chart_renderer import render_chart_for_brand
"""

from inkline.charts.interactive import (
    render_interactive_chart,
    render_interactive_chart_json,
    list_chart_types,
)

__all__ = [
    "render_interactive_chart",
    "render_interactive_chart_json",
    "list_chart_types",
]
