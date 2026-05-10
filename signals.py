"""
signals.py — BUY / SELL / HOLD Signal Engine
Combines ML prediction, sentiment, RSI, and MACD into a trading signal.
"""


# ─────────────────────────────────────────────
# Signal logic
# ─────────────────────────────────────────────

def generate_signal(
    pct_change: float,
    sentiment_score: float,
    rsi: float,
    macd_histogram: float,
) -> dict:
    """
    Returns:
        signal       str   (BUY / SELL / HOLD)
        confidence   float (0-100 %)
        explanation  str
    """

    # ── Score each factor (–1 to +1) ──────────
    price_score     = _score_price(pct_change)
    sentiment_score_norm = max(-1.0, min(1.0, sentiment_score * 5))  # amplify subtle sentiment
    rsi_score       = _score_rsi(rsi)
    macd_score      = _score_macd(macd_histogram)

    # Weighted composite
    composite = (
        price_score          * 0.40 +
        sentiment_score_norm * 0.25 +
        rsi_score            * 0.20 +
        macd_score           * 0.15
    )

    # ── Map composite → signal ─────────────────
    if composite > 0.15:
        signal = "BUY"
    elif composite < -0.15:
        signal = "SELL"
    else:
        signal = "HOLD"

    # ── Confidence: 50 + scaled composite ─────
    confidence = round(50 + composite * 50, 1)
    confidence = max(5.0, min(95.0, confidence))

    explanation = _explain(signal, pct_change, sentiment_score, rsi, macd_histogram)

    return {
        "signal":      signal,
        "confidence":  confidence,
        "explanation": explanation,
        "composite":   round(composite, 4),
    }


# ─────────────────────────────────────────────
# Sub-scorers
# ─────────────────────────────────────────────

def _score_price(pct: float) -> float:
    """Map pct_change to [-1, +1]."""
    if pct > 3:
        return 1.0
    elif pct > 1:
        return 0.6
    elif pct > 0:
        return 0.2
    elif pct > -1:
        return -0.2
    elif pct > -3:
        return -0.6
    else:
        return -1.0


def _score_rsi(rsi: float) -> float:
    """Oversold → bullish. Overbought → bearish."""
    if rsi < 30:
        return 0.8    # deeply oversold → strong buy signal
    elif rsi < 40:
        return 0.4
    elif rsi < 60:
        return 0.0    # neutral zone
    elif rsi < 70:
        return -0.4
    else:
        return -0.8   # overbought → sell pressure


def _score_macd(histogram: float) -> float:
    """Positive histogram → bullish momentum."""
    if histogram > 0.5:
        return 1.0
    elif histogram > 0:
        return 0.4
    elif histogram > -0.5:
        return -0.4
    else:
        return -1.0


# ─────────────────────────────────────────────
# Explanation generator
# ─────────────────────────────────────────────

def _explain(signal: str, pct: float, sentiment: float, rsi: float, macd_hist: float) -> str:
    parts = []

    # Price
    if pct > 0:
        parts.append(f"The model predicts a price increase of {pct:.2f}%.")
    else:
        parts.append(f"The model predicts a price decline of {abs(pct):.2f}%.")

    # Sentiment
    if sentiment > 0.05:
        parts.append("Market sentiment from recent news is positive (Bullish).")
    elif sentiment < -0.05:
        parts.append("Market sentiment from recent news is negative (Bearish).")
    else:
        parts.append("Market sentiment is currently neutral.")

    # RSI
    if rsi < 30:
        parts.append(f"RSI is {rsi:.1f} — the stock is oversold and may rebound.")
    elif rsi > 70:
        parts.append(f"RSI is {rsi:.1f} — the stock is overbought and may correct.")
    else:
        parts.append(f"RSI is {rsi:.1f} — momentum is in a neutral range.")

    # MACD
    if macd_hist > 0:
        parts.append("MACD histogram is positive, indicating upward momentum.")
    else:
        parts.append("MACD histogram is negative, indicating downward momentum.")

    # Conclusion
    if signal == "BUY":
        parts.append("📈 Overall, indicators support a BUY decision. Consider entering a position.")
    elif signal == "SELL":
        parts.append("📉 Overall, indicators suggest a SELL decision. Consider exiting or shorting.")
    else:
        parts.append("⏸️ Signals are mixed. A HOLD strategy is recommended until clarity emerges.")

    return " ".join(parts)
