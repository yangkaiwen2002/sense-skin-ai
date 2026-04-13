import numpy as np
import pandas as pd
from typing import Optional


def compute_avg(prices: list[float], days: int) -> Optional[float]:
    if not prices:
        return None
    recent = prices[-days:] if len(prices) >= days else prices
    return round(float(np.mean(recent)), 2)


def compute_return(prices: list[float], days: int) -> Optional[float]:
    if len(prices) < 2:
        return None
    current = prices[-1]
    past_idx = max(0, len(prices) - days - 1)
    past = prices[past_idx]
    if past == 0:
        return None
    return round((current - past) / past, 4)


def compute_volatility(prices: list[float]) -> Optional[float]:
    if len(prices) < 3:
        return None
    series = pd.Series(prices)
    daily_returns = series.pct_change().dropna()
    if len(daily_returns) < 2:
        return None
    return round(float(daily_returns.std()), 4)


def compute_liquidity_score(
    volume_24h: Optional[float],
    liquidity_depth: Optional[float],
    spread: Optional[float],
    listing_price: Optional[float],
    max_volume: float = 500,
    max_depth: float = 100,
) -> Optional[float]:
    if volume_24h is None and liquidity_depth is None:
        return None

    norm_volume = min((volume_24h or 0) / max_volume, 1.0)
    norm_depth = min((liquidity_depth or 0) / max_depth, 1.0)

    if spread is not None and listing_price and listing_price > 0:
        spread_ratio = spread / listing_price
        inverse_spread = max(0.0, 1.0 - spread_ratio * 10)
    else:
        inverse_spread = 0.5

    score = 0.4 * norm_volume + 0.4 * norm_depth + 0.2 * inverse_spread
    return round(score * 100, 1)
