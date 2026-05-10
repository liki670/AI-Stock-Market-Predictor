"""
model.py — LSTM Stock Price Predictor
Trains on 5 years of historical Close price data.
Saves one model per ticker to models/<TICKER>.h5
"""

import os
import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.preprocessing import MinMaxScaler
import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping
import warnings
warnings.filterwarnings("ignore")

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(MODELS_DIR, exist_ok=True)

SEQ_LEN      = 60   # look-back window (days)
EPOCHS       = 15
BATCH_SIZE   = 32
TRAIN_SPLIT  = 0.85


# ─────────────────────────────────────────────
# Data helpers
# ─────────────────────────────────────────────

def fetch_history(ticker: str, period: str = "5y") -> pd.DataFrame:
    """Download OHLCV data via yFinance. Returns empty df on failure."""
    try:
        df = yf.download(ticker, period=period, auto_adjust=True, progress=False)
        df.dropna(inplace=True)
        
        # Flatten MultiIndex columns if yfinance returns them
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0] for col in df.columns]
            
        return df
    except Exception as e:
        print(f"[model] fetch_history error for {ticker}: {e}")
        return pd.DataFrame()


def _build_sequences(scaled_data: np.ndarray, seq_len: int):
    X, y = [], []
    for i in range(seq_len, len(scaled_data)):
        X.append(scaled_data[i - seq_len : i, :])  # Both features (Price, Sentiment)
        y.append(scaled_data[i, 0])                # Target is just Price
    return np.array(X), np.array(y)


# ─────────────────────────────────────────────
# Model builder
# ─────────────────────────────────────────────

def _build_model(seq_len: int) -> Sequential:
    model = Sequential([
        LSTM(128, return_sequences=True, input_shape=(seq_len, 2)),
        Dropout(0.2),
        LSTM(64, return_sequences=False),
        Dropout(0.2),
        Dense(32, activation="relu"),
        Dense(1),
    ])
    model.compile(optimizer="adam", loss="mean_squared_error")
    return model


# ─────────────────────────────────────────────
# Train & save
# ─────────────────────────────────────────────

def train_model(ticker: str, force_retrain: bool = False) -> str:
    """
    Train Multivariate LSTM for `ticker` using Price + Sentiment.
    Saves to _v2.h5 to avoid conflicts with old univariate models.
    """
    model_path = os.path.join(MODELS_DIR, f"{ticker.upper()}_v2.h5")

    if os.path.exists(model_path) and not force_retrain:
        print(f"[model] Cached v2 model found for {ticker} → {model_path}")
        return model_path

    print(f"[model] Training new multivariate model for {ticker}...")
    df = fetch_history(ticker)
    if df.empty:
        raise ValueError(f"No data returned for ticker '{ticker}'")

    # Simulate historical sentiment correlated to price movement for training
    np.random.seed(42)
    df["Sentiment"] = np.where(
        df["Close"] > df["Close"].shift(1), 
        np.random.uniform(0.1, 0.8, len(df)), 
        np.random.uniform(-0.8, -0.1, len(df))
    )
    df["Sentiment"] = df["Sentiment"].fillna(0.0)

    features = df[["Close", "Sentiment"]].values
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled = scaler.fit_transform(features)

    split = int(len(scaled) * TRAIN_SPLIT)
    train_data = scaled[:split]

    X_train, y_train = _build_sequences(train_data, SEQ_LEN)
    X_train = X_train.reshape(X_train.shape[0], SEQ_LEN, 2)

    model = _build_model(SEQ_LEN)
    es = EarlyStopping(monitor="loss", patience=3, restore_best_weights=True)
    model.fit(
        X_train, y_train,
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        callbacks=[es],
        verbose=1,
    )
    model.save(model_path)
    print(f"[model] Saved → {model_path}")
    return model_path


# ─────────────────────────────────────────────
# Predict
# ─────────────────────────────────────────────

def predict_price(ticker: str, live_sentiment: float = 0.0) -> dict:
    """
    Returns multivariate predictions based on past 60 days of [Price, Sentiment].
    Replaces the final sequence day's sentiment with the true `live_sentiment`.
    """
    model_path = train_model(ticker)

    df = fetch_history(ticker)
    if df.empty:
        raise ValueError(f"No price data for '{ticker}'")

    # Generate baseline simulated sentiment so the scaler matches training
    np.random.seed(42)
    df["Sentiment"] = np.where(
        df["Close"] > df["Close"].shift(1), 
        np.random.uniform(0.1, 0.8, len(df)), 
        np.random.uniform(-0.8, -0.1, len(df))
    )
    df["Sentiment"] = df["Sentiment"].fillna(0.0)

    features = df[["Close", "Sentiment"]].values
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled = scaler.fit_transform(features)

    # Grab the last SEQ_LEN days
    last_seq = scaled[-SEQ_LEN:].copy()

    # Inject the real-world live sentiment for today into the final step
    dummy_row = np.array([[0.0, live_sentiment]])
    scaled_live_sentiment = scaler.transform(dummy_row)[0][1]
    last_seq[-1, 1] = scaled_live_sentiment

    X_input  = last_seq.reshape(1, SEQ_LEN, 2)

    model = load_model(model_path, compile=False)
    pred_scaled = model.predict(X_input, verbose=0)
    
    # Inverse transform (pad with dummy sentiment to match 2 features)
    pad = np.zeros((1, 2))
    pad[0, 0] = pred_scaled[0][0]
    predicted = float(scaler.inverse_transform(pad)[0][0])
    
    current     = float(features[-1][0])
    pct_change  = ((predicted - current) / current) * 100

    return {
        "current_price":   round(current, 2),
        "predicted_price": round(predicted, 2),
        "pct_change":      round(pct_change, 4),
        "history_df":      df.tail(200),
    }


if __name__ == "__main__":
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    result = predict_price(ticker)
    print(result)
