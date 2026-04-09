"""Chart generation engine — matplotlib with brand theming.

Generates high-DPI chart images suitable for embedding in PPTX slides.
Charts follow the brand's colour scheme and typography.

Usage:
    from inkline.core.charts import ChartEngine, ChartType
    engine = ChartEngine()
    png_path = engine.bar_chart(
        labels=["Q1", "Q2", "Q3"],
        values=[120, 185, 210],
        title="Revenue Growth ($MM)",
        output_path="chart.png",
    )
"""

from __future__ import annotations

import logging
import os
import tempfile
from enum import Enum
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

# Default chart colour palette
DEFAULT_CHART_COLORS = ["#1A7FA0", "#39D3BB", "#3fb950", "#f0883e", "#58a6ff", "#d2a8ff", "#e6c069"]
DEFAULT_CHART_BG = "#FFFFFF"
DEFAULT_CHART_TEXT = "#1A1A1A"
DEFAULT_CHART_GRID = "#E5E7EB"
DEFAULT_CHART_MUTED = "#6B7280"


class ChartType(Enum):
    BAR = "bar"
    HORIZONTAL_BAR = "horizontal_bar"
    LINE = "line"
    STACKED_BAR = "stacked_bar"
    PIE = "pie"
    DONUT = "donut"
    WATERFALL = "waterfall"
    SCATTER = "scatter"


class ChartEngine:
    """Generate branded chart images using matplotlib."""

    def __init__(
        self,
        colors: list[str] | None = None,
        bg_color: str = DEFAULT_CHART_BG,
        text_color: str = DEFAULT_CHART_TEXT,
        grid_color: str = DEFAULT_CHART_GRID,
        font_family: str = "Inter",
        dpi: int = 200,
    ):
        self.colors = colors or DEFAULT_CHART_COLORS
        self.bg_color = bg_color
        self.text_color = text_color
        self.grid_color = grid_color
        self.font_family = font_family
        self.dpi = dpi

    def _apply_theme(self, fig: Any, ax: Any) -> None:
        """Apply brand theme to matplotlib figure and axes."""
        fig.patch.set_facecolor(self.bg_color)
        ax.set_facecolor(self.bg_color)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color(self.grid_color)
        ax.spines["bottom"].set_color(self.grid_color)
        ax.tick_params(colors=self.text_color, labelsize=10)
        ax.yaxis.grid(True, color=self.grid_color, linewidth=0.5, alpha=0.7)
        ax.xaxis.grid(False)
        ax.set_axisbelow(True)

    def _save(self, fig: Any, output_path: str | Path | None) -> Path:
        """Save figure to file."""
        if output_path is None:
            fd, output_path = tempfile.mkstemp(suffix=".png")
            os.close(fd)
        path = Path(output_path)
        fig.savefig(str(path), dpi=self.dpi, bbox_inches="tight",
                    facecolor=fig.get_facecolor(), edgecolor="none")
        import matplotlib.pyplot as plt
        plt.close(fig)
        return path

    def bar_chart(
        self,
        labels: list[str],
        values: list[float],
        title: str = "",
        ylabel: str = "",
        output_path: str | Path | None = None,
        figsize: tuple[float, float] = (8, 4.5),
        color_index: int = 0,
    ) -> Path:
        """Generate a vertical bar chart."""
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=figsize)
        self._apply_theme(fig, ax)

        color = self.colors[color_index % len(self.colors)]
        bars = ax.bar(labels, values, color=color, width=0.6, edgecolor="none", zorder=3)

        # Value labels on bars
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(values) * 0.02,
                    f"{val:,.0f}", ha="center", va="bottom", fontsize=9, color=self.text_color)

        if title:
            ax.set_title(title, fontsize=14, fontweight="bold", color=self.text_color, pad=12)
        if ylabel:
            ax.set_ylabel(ylabel, fontsize=10, color=self.text_color)

        plt.tight_layout()
        return self._save(fig, output_path)

    def horizontal_bar_chart(
        self,
        labels: list[str],
        values: list[float],
        title: str = "",
        xlabel: str = "",
        output_path: str | Path | None = None,
        figsize: tuple[float, float] = (8, 4.5),
        colors: list[str] | None = None,
    ) -> Path:
        """Generate a horizontal bar chart (e.g. for tornado/sensitivity)."""
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=figsize)
        self._apply_theme(fig, ax)

        bar_colors = colors or [self.colors[i % len(self.colors)] for i in range(len(labels))]
        ax.barh(labels, values, color=bar_colors, height=0.6, edgecolor="none", zorder=3)

        for i, (val, label) in enumerate(zip(values, labels)):
            ax.text(val + max(abs(v) for v in values) * 0.02, i,
                    f"{val:,.0f}", ha="left", va="center", fontsize=9, color=self.text_color)

        if title:
            ax.set_title(title, fontsize=14, fontweight="bold", color=self.text_color, pad=12)
        if xlabel:
            ax.set_xlabel(xlabel, fontsize=10, color=self.text_color)

        ax.invert_yaxis()
        plt.tight_layout()
        return self._save(fig, output_path)

    def line_chart(
        self,
        x: list[Any],
        y_series: dict[str, list[float]],
        title: str = "",
        ylabel: str = "",
        output_path: str | Path | None = None,
        figsize: tuple[float, float] = (8, 4.5),
    ) -> Path:
        """Generate a multi-series line chart."""
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=figsize)
        self._apply_theme(fig, ax)

        for i, (name, values) in enumerate(y_series.items()):
            color = self.colors[i % len(self.colors)]
            ax.plot(x, values, label=name, color=color, linewidth=2, zorder=3)

        if title:
            ax.set_title(title, fontsize=14, fontweight="bold", color=self.text_color, pad=12)
        if ylabel:
            ax.set_ylabel(ylabel, fontsize=10, color=self.text_color)

        if len(y_series) > 1:
            ax.legend(frameon=False, fontsize=9, labelcolor=self.text_color)

        plt.tight_layout()
        return self._save(fig, output_path)

    def stacked_area_chart(
        self,
        x: list[Any],
        y_series: dict[str, list[float]],
        title: str = "",
        ylabel: str = "",
        output_path: str | Path | None = None,
        figsize: tuple[float, float] = (8, 4.5),
    ) -> Path:
        """Generate a stacked area chart (e.g. production profile)."""
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=figsize)
        self._apply_theme(fig, ax)

        colors = [self.colors[i % len(self.colors)] for i in range(len(y_series))]
        ax.stackplot(x, *y_series.values(), labels=y_series.keys(),
                     colors=colors, alpha=0.85, zorder=3)

        if title:
            ax.set_title(title, fontsize=14, fontweight="bold", color=self.text_color, pad=12)
        if ylabel:
            ax.set_ylabel(ylabel, fontsize=10, color=self.text_color)

        ax.legend(loc="upper right", frameon=False, fontsize=9, labelcolor=self.text_color)
        plt.tight_layout()
        return self._save(fig, output_path)

    def donut_chart(
        self,
        labels: list[str],
        values: list[float],
        title: str = "",
        output_path: str | Path | None = None,
        figsize: tuple[float, float] = (5, 5),
    ) -> Path:
        """Generate a donut chart."""
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=figsize)
        fig.patch.set_facecolor(self.bg_color)

        colors = [self.colors[i % len(self.colors)] for i in range(len(labels))]
        wedges, texts, autotexts = ax.pie(
            values, labels=labels, colors=colors, autopct="%1.0f%%",
            startangle=90, pctdistance=0.8, wedgeprops=dict(width=0.35, edgecolor=self.bg_color),
        )

        for text in texts:
            text.set_fontsize(10)
            text.set_color(self.text_color)
        for text in autotexts:
            text.set_fontsize(9)
            text.set_color(self.text_color)

        if title:
            ax.set_title(title, fontsize=14, fontweight="bold", color=self.text_color, pad=12)

        return self._save(fig, output_path)

    def waterfall_chart(
        self,
        labels: list[str],
        values: list[float],
        title: str = "",
        output_path: str | Path | None = None,
        figsize: tuple[float, float] = (8, 4.5),
    ) -> Path:
        """Generate a waterfall chart (e.g. cash flow decomposition)."""
        import matplotlib.pyplot as plt
        import numpy as np

        fig, ax = plt.subplots(figsize=figsize)
        self._apply_theme(fig, ax)

        cumulative = np.cumsum(values)
        starts = np.concatenate([[0], cumulative[:-1]])

        colors = []
        for v in values:
            if v >= 0:
                colors.append(self.colors[0])  # positive
            else:
                colors.append("#dc2626")  # negative

        # Last bar = total (use accent)
        colors[-1] = self.colors[1]

        ax.bar(labels, values, bottom=starts, color=colors, width=0.6, edgecolor="none", zorder=3)

        # Connector lines
        for i in range(len(values) - 1):
            ax.plot([i + 0.3, i + 0.7], [cumulative[i], cumulative[i]],
                    color=self.grid_color, linewidth=0.8, zorder=2)

        if title:
            ax.set_title(title, fontsize=14, fontweight="bold", color=self.text_color, pad=12)

        plt.xticks(rotation=30, ha="right")
        plt.tight_layout()
        return self._save(fig, output_path)
