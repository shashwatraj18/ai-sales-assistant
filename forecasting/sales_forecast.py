"""
Sales forecasting: 30/90-day revenue projections with confidence intervals.

Uses gradient-boosted quantile regression (scikit-learn) rather than a
classical ARIMA/statsmodels model - it captures the day-of-week and
holiday-season seasonality already present in the data without hand-tuned
seasonal orders, and quantile loss gives a real prediction interval in a
few lines instead of a symmetric std-dev band.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor


@dataclass(frozen=True)
class ForecastResult:
    history: pd.DataFrame  # actuals: date, revenue
    forecast: pd.DataFrame  # date, forecast, lower, upper


def _daily_revenue(df: pd.DataFrame) -> pd.DataFrame:
    daily = df.groupby(df["order_date"].dt.floor("D"))["revenue"].sum().reset_index()
    daily.columns = ["date", "revenue"]
    return daily.sort_values("date").reset_index(drop=True)


def _build_features(dates: pd.Series, day_index_offset: int) -> pd.DataFrame:
    return pd.DataFrame({
        "day_index": np.arange(len(dates)) + day_index_offset,
        "day_of_week": dates.dt.weekday.to_numpy(),
        "month": dates.dt.month.to_numpy(),
        "is_weekend": (dates.dt.weekday >= 5).astype(int).to_numpy(),
        "is_holiday_season": dates.dt.month.isin([11, 12]).astype(int).to_numpy(),
    })


def forecast_revenue(df: pd.DataFrame, horizon_days: int = 30, random_state: int = 42) -> ForecastResult:
    """Forecast total daily revenue `horizon_days` past the last date in `df`.

    Returns both the historical daily series and the forecast (with a
    10th/90th percentile band) so the caller can plot history and forecast
    on one chart.
    """
    daily = _daily_revenue(df)
    if len(daily) < 30:
        raise ValueError("Need at least 30 days of history to fit a forecast")

    X_train = _build_features(daily["date"], day_index_offset=0)
    y_train = daily["revenue"].to_numpy()

    future_dates = pd.Series(
        pd.date_range(start=daily["date"].max() + pd.Timedelta(days=1), periods=horizon_days, freq="D")
    )
    X_future = _build_features(future_dates, day_index_offset=len(daily))

    predictions: dict[str, np.ndarray] = {}
    for label, alpha in (("lower", 0.1), ("forecast", 0.5), ("upper", 0.9)):
        model = GradientBoostingRegressor(
            loss="quantile", alpha=alpha, n_estimators=200, max_depth=3,
            learning_rate=0.05, random_state=random_state,
        )
        model.fit(X_train, y_train)
        predictions[label] = np.clip(model.predict(X_future), a_min=0, a_max=None)

    forecast = pd.DataFrame({"date": future_dates, **predictions})
    # The three quantile models are fit independently, so they can occasionally
    # cross (e.g. lower slightly above forecast); enforce a consistent order.
    ordered = np.sort(forecast[["lower", "forecast", "upper"]].to_numpy(), axis=1)
    forecast[["lower", "forecast", "upper"]] = ordered

    return ForecastResult(history=daily, forecast=forecast)
