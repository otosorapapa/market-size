"""Simple nowcast utilities for extrapolating annual statistics."""

from __future__ import annotations

from typing import Tuple

import pandas as pd


def _cumulative_growth(latest_value: float, monthly_growth: pd.Series) -> Tuple[float, float]:
    """Compute cumulative growth based on monthly percentage changes."""

    growth = (monthly_growth.fillna(0) / 100).add(1).prod()
    projected = latest_value * growth
    rate = (projected - latest_value) / latest_value if latest_value else 0.0
    return projected, rate


def apply_nowcast(
    annual_series: pd.Series,
    monthly_growth: pd.Series,
    *,
    method: str = "cumrate",
    alpha: float = 0.3,
) -> pd.Series:
    """Apply a simple nowcast adjustment to an annual series."""

    if annual_series.empty:
        return annual_series
    annual_series = annual_series.sort_index()
    latest_year = annual_series.index.max()
    latest_value = annual_series.loc[latest_year]

    if method == "cumrate" and not monthly_growth.empty:
        projected, _ = _cumulative_growth(latest_value, monthly_growth)
    else:
        smoothed = annual_series.ewm(alpha=alpha).mean()
        projected = smoothed.iloc[-1]

    result = annual_series.copy()
    result.loc[latest_year + 1] = projected
    result.attrs["nowcast"] = True
    return result

