"""Tests for forecasting.sales_forecast."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from forecasting.sales_forecast import forecast_revenue


@pytest.fixture
def daily_history() -> pd.DataFrame:
    """60 days of synthetic-but-trending daily revenue - enough history to fit on."""
    dates = pd.date_range("2026-01-01", periods=60, freq="D")
    rng = np.random.default_rng(0)
    revenue = 1000 + np.arange(60) * 10 + rng.normal(0, 50, 60)
    df = pd.DataFrame({"order_date": dates, "revenue": np.clip(revenue, 100, None)})
    df["order_id"] = [f"ORD{i:04d}" for i in range(60)]
    return df


def test_forecast_shape_and_ordering(daily_history: pd.DataFrame) -> None:
    result = forecast_revenue(daily_history, horizon_days=14)
    assert len(result.forecast) == 14
    assert (result.forecast["lower"] <= result.forecast["forecast"]).all()
    assert (result.forecast["forecast"] <= result.forecast["upper"]).all()
    assert (result.forecast[["lower", "forecast", "upper"]] >= 0).all().all()


def test_forecast_dates_continue_after_history(daily_history: pd.DataFrame) -> None:
    result = forecast_revenue(daily_history, horizon_days=7)
    assert result.forecast["date"].min() == result.history["date"].max() + pd.Timedelta(days=1)


def test_forecast_raises_on_too_little_history() -> None:
    tiny = pd.DataFrame({
        "order_date": pd.date_range("2026-01-01", periods=5, freq="D"),
        "revenue": [100.0] * 5,
        "order_id": [f"ORD{i}" for i in range(5)],
    })
    with pytest.raises(ValueError):
        forecast_revenue(tiny, horizon_days=30)
