"""
indicators.py — Technical Indicators (RSI, MACD, Moving Averages)
Works on a pandas DataFrame with a 'Close' column.
"""

import pandas as pd
import numpy as np


def compute_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Relative Strength Index."""
    close = df["Close"].squeeze()
    delta = close.diff()
    gain  = delta.clip(lower=0)
    loss  = (-delta).clip(lower=0)

    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()

    rs  = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.rename("RSI")


def compute_macd(
    df: pd.DataFrame,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> pd.DataFrame:
    """MACD line, Signal line, and Histogram."""
    close       = df["Close"].squeeze()
    ema_fast    = close.ewm(span=fast, adjust=False).mean()
    ema_slow    = close.ewm(span=slow, adjust=False).mean()
    macd_line   = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram   = macd_line - signal_line
    return pd.DataFrame({
        "MACD":      macd_line,
        "Signal":    signal_line,
        "Histogram": histogram,
    })


def compute_moving_averages(df: pd.DataFrame) -> pd.DataFrame:
    """MA20 and MA50."""
    close = df["Close"].squeeze()
    return pd.DataFrame({
        "MA20": close.rolling(20).mean(),
        "MA50": close.rolling(50).mean(),
    })


def get_all_indicators(df: pd.DataFrame) -> dict:
    """Return a dict with latest RSI, MACD values, and MA series."""
    rsi  = compute_rsi(df)
    macd = compute_macd(df)
    mas  = compute_moving_averages(df)

    latest_rsi        = round(float(rsi.dropna().iloc[-1]), 2)
    latest_macd       = round(float(macd["MACD"].dropna().iloc[-1]), 4)
    latest_macd_sig   = round(float(macd["Signal"].dropna().iloc[-1]), 4)
    latest_histogram  = round(float(macd["Histogram"].dropna().iloc[-1]), 4)

    return {
        "rsi":              latest_rsi,
        "macd":             latest_macd,
        "macd_signal":      latest_macd_sig,
        "macd_histogram":   latest_histogram,
        "rsi_series":       rsi,
        "macd_series":      macd,
        "ma_series":        mas,
    }
