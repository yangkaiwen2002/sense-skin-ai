from typing import Optional


def compute_risk_labels(
    volatility_7d: Optional[float],
    liquidity_score: Optional[float],
    current_price: Optional[float],
    avg_30d: Optional[float],
) -> list[str]:
    labels = []

    if volatility_7d is not None and volatility_7d > 0.08:
        labels.append("High Volatility")

    if liquidity_score is not None and liquidity_score < 40:
        labels.append("Low Liquidity")

    if current_price is not None and avg_30d is not None and avg_30d > 0:
        if current_price > avg_30d * 1.15:
            labels.append("Potential Overheat")

    if (
        volatility_7d is not None
        and volatility_7d < 0.04
        and liquidity_score is not None
        and liquidity_score > 60
        and "High Volatility" not in labels
        and "Low Liquidity" not in labels
        and "Potential Overheat" not in labels
    ):
        labels.append("Stable")

    return labels
