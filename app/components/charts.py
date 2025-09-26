"""Reusable chart components using Plotly Express."""

from __future__ import annotations

from typing import Iterable, Tuple

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


PX_TEMPLATE = "plotly_white"


def time_series(df: pd.DataFrame, *, x: str, y: str, title: str, unit: str) -> go.Figure:
    """Create a time series line chart."""

    fig = px.line(
        df,
        x=x,
        y=y,
        markers=True,
        template=PX_TEMPLATE,
    )
    fig.update_layout(title=title, yaxis_title=f"{unit}", xaxis_title="年")
    fig.update_yaxes(tickformat=",.")
    return fig


def bar_chart(df: pd.DataFrame, *, x: str, y: str, title: str, unit: str) -> go.Figure:
    """Create a simple bar chart."""

    fig = px.bar(df, x=x, y=y, template=PX_TEMPLATE)
    fig.update_layout(title=title, yaxis_title=f"{unit}")
    fig.update_yaxes(tickformat=",.")
    return fig


def scatter_density(df: pd.DataFrame, *, x: str, y: str, text: str, title: str) -> go.Figure:
    """Scatter plot showing competition density (per capita)."""

    fig = px.scatter(df, x=x, y=y, text=text, template=PX_TEMPLATE)
    fig.update_traces(textposition="top center")
    fig.update_layout(title=title, xaxis_title="人口1万人当たり事業所数", yaxis_title="市場規模（万円）")
    return fig


def figures_to_png(figures: Iterable[go.Figure]) -> Tuple[bytes, ...]:
    """Convert Plotly figures to PNG byte strings for exports."""

    return tuple(fig.to_image(format="png", scale=2) for fig in figures)

