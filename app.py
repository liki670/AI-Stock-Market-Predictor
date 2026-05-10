# -*- coding: utf-8 -*-
import os, sys
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"]  = "3"
os.environ["PYTHONIOENCODING"]       = "utf-8"
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
"""
app.py -- Flask REST API Backend
Endpoints:
  GET  /              → health check
  POST /predict       → main prediction endpoint
  GET  /history/<sym> → OHLCV history for charting
"""

import os
import json
import numpy as np
import pandas as pd
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

from model      import predict_price
from sentiment  import fetch_sentiment
from indicators import get_all_indicators
from signals    import generate_signal

load_dotenv()

app = Flask(__name__)
CORS(app)


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

COMPANY_NAMES = {
    "RELIANCE.NS":  "Reliance Industries",
    "TCS.NS":       "Tata Consultancy Services",
    "INFY.NS":      "Infosys",
    "HDFCBANK.NS":  "HDFC Bank",
    "WIPRO.NS":     "Wipro",
    "SBIN.NS":      "State Bank of India",
    "ICICIBANK.NS": "ICICI Bank",
    "BAJFINANCE.NS":"Bajaj Finance",
    "HINDUNILVR.NS":"Hindustan Unilever",
    "AAPL":  "Apple Inc.",
    "TSLA":  "Tesla",
    "NVDA":  "Nvidia",
    "MSFT":  "Microsoft",
    "GOOGL": "Alphabet (Google)",
    "AMZN":  "Amazon",
    "META":  "Meta Platforms",
}
NAME_TO_TICKER = {
    "reliance":              "RELIANCE.NS",
    "reliance industries":   "RELIANCE.NS",
    "ril":                   "RELIANCE.NS",
    "tcs":                   "TCS.NS",
    "tata consultancy":      "TCS.NS",
    "tata consultancy services": "TCS.NS",
    "infosys":               "INFY.NS",
    "infy":                  "INFY.NS",
    "hdfc":                  "HDFCBANK.NS",
    "hdfc bank":             "HDFCBANK.NS",
    "hdfcbank":              "HDFCBANK.NS",
    "wipro":                 "WIPRO.NS",
    "sbi":                   "SBIN.NS",
    "state bank":            "SBIN.NS",
    "state bank of india":   "SBIN.NS",
    "icici":                 "ICICIBANK.NS",
    "icici bank":            "ICICIBANK.NS",
    "bajaj finance":         "BAJFINANCE.NS",
    "bajaj":                 "BAJFINANCE.NS",
    "hindustan unilever":    "HINDUNILVR.NS",
    "hul":                   "HINDUNILVR.NS",
    "unilever":              "HINDUNILVR.NS",
    "apple":                 "AAPL",
    "apple inc":             "AAPL",
    "aapl":                  "AAPL",
    "tesla":                 "TSLA",
    "tsla":                  "TSLA",
    "elon musk":             "TSLA",
    "nvidia":                "NVDA",
    "nvda":                  "NVDA",
    "microsoft":             "MSFT",
    "msft":                  "MSFT",
    "google":                "GOOGL",
    "alphabet":              "GOOGL",
    "googl":                 "GOOGL",
    "amazon":                "AMZN",
    "amzn":                  "AMZN",
    "meta":                  "META",
    "facebook":              "META",
}

def _load_extended_market_data():
    """Loads all NSE stocks dynamically to populate the resolver."""
    n2t = NAME_TO_TICKER.copy()
    cnames = COMPANY_NAMES.copy()
    try:
        url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
        df = pd.read_csv(url)
        for _, row in df.iterrows():
            sym = str(row["SYMBOL"]).strip() + ".NS"
            name = str(row["NAME OF COMPANY"]).strip()
            cnames[sym] = name
            n2t[name.lower()] = sym
            bare_sym = str(row["SYMBOL"]).strip().lower()
            if bare_sym not in n2t:
                n2t[bare_sym] = sym
    except Exception as e:
        print(f"Failed to load NSE dataset: {e}")
    return n2t, cnames

FULL_NAME_TO_TICKER, FULL_COMPANY_NAMES = _load_extended_market_data()

def resolve_ticker(user_input: str) -> tuple[str, str | None]:
    import difflib
    raw   = user_input.strip()
    lower = raw.lower()

    if raw.upper() in FULL_COMPANY_NAMES:
        return raw.upper(), None

    if lower in FULL_NAME_TO_TICKER:
        ticker = FULL_NAME_TO_TICKER[lower]
        return ticker, FULL_COMPANY_NAMES.get(ticker, ticker)

    for key, ticker in FULL_NAME_TO_TICKER.items():
        if lower in key or key in lower:
            return ticker, FULL_COMPANY_NAMES.get(ticker, ticker)

    all_keys = list(FULL_NAME_TO_TICKER.keys())
    matches  = difflib.get_close_matches(lower, all_keys, n=1, cutoff=0.6)
    if matches:
        ticker = FULL_NAME_TO_TICKER[matches[0]]
        return ticker, FULL_COMPANY_NAMES.get(ticker, ticker)

    return raw.upper(), None

def _ticker_to_query(ticker: str) -> str:
    """Convert a ticker like RELIANCE.NS → news search query."""
    return FULL_COMPANY_NAMES.get(ticker.upper(), ticker.replace(".", " ").replace("-", " "))


from flask.json.provider import DefaultJSONProvider

class _CustomProvider(DefaultJSONProvider):
    @staticmethod
    def default(obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        raise TypeError(f"Not serializable: {type(obj)}")

app.json_provider_class = _CustomProvider
app.json = _CustomProvider(app)


# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/<path:path>")
def static_files(path):
    return send_from_directory("static", path)

@app.route("/health")
def health():
    return jsonify({"status": "ok", "message": "AI Stock Predictor API is running 🚀"})


@app.route("/predict", methods=["POST"])
def predict():
    body   = request.get_json(force=True, silent=True) or {}
    raw_ticker = (body.get("symbol") or "AAPL").strip()
    ticker, match_label = resolve_ticker(raw_ticker)
    company_name = FULL_COMPANY_NAMES.get(ticker, ticker)

    try:
        # 1. Fetch Live Sentiment first
        query    = _ticker_to_query(ticker)
        sent     = fetch_sentiment(query)

        # 2. ML prediction (Multivariate LSTM using real sentiment)
        ml = predict_price(ticker, live_sentiment=sent["score"])

        # 3. Technical indicators
        indic    = get_all_indicators(ml["history_df"])

        # 4. Signal
        sig      = generate_signal(
            pct_change      = ml["pct_change"],
            sentiment_score = sent["score"],
            rsi             = indic["rsi"],
            macd_histogram  = indic["macd_histogram"],
        )

        return jsonify({
            "ticker":          ticker,
            "company_name":    company_name,
            "current_price":   ml["current_price"],
            "predicted_price": ml["predicted_price"],
            "pct_change":      ml["pct_change"],
            "signal":          sig["signal"],
            "confidence":      sig["confidence"],
            "sentiment":       sent["score"],
            "sentiment_label": sent["label"],
            "explanation":     sig["explanation"],
            "rsi":             indic["rsi"],
            "macd":            indic["macd"],
            "macd_signal":     indic["macd_signal"],
            "macd_histogram":  indic["macd_histogram"],
            "news":            sent["articles"][:5],
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/history/<symbol>", methods=["GET"])
def history(symbol: str):
    ticker, _ = resolve_ticker(symbol)
    from model import fetch_history
    try:
        df = fetch_history(ticker, period="1y")
        if df.empty:
            return jsonify({"error": "No data"}), 404

        df = df.tail(250).copy()

        # Flatten MultiIndex columns e.g. ('Close', 'AAPL') -> 'Close'
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0] for col in df.columns]

        df = df.reset_index()
        df.columns = [str(c).strip() for c in df.columns]

        # Date column may be 'Date' or 'Datetime'
        date_col = next(
            (c for c in df.columns if c.lower() in ("date", "datetime")),
            df.columns[0]
        )

        records = []
        for _, row in df.iterrows():
            try:
                records.append({
                    "date":   str(row[date_col])[:10],
                    "open":   round(float(row["Open"]),   2),
                    "high":   round(float(row["High"]),   2),
                    "low":    round(float(row["Low"]),    2),
                    "close":  round(float(row["Close"]),  2),
                    "volume": int(row["Volume"]),
                })
            except Exception:
                continue

        return jsonify({"symbol": symbol.upper(), "data": records})

    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    print(f"[*] Starting AI Stock Predictor API on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug)
