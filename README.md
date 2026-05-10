# 🚀 AI Stock Market Predictor

An AI-powered stock market prediction web app using **LSTM deep learning**, **live news sentiment**, and **technical indicators** to generate intelligent BUY / SELL / HOLD trading signals.

---

## ✨ Features

| Feature | Details |
|---|---|
| 🧠 LSTM Model | 2-layer LSTM trained on 5 years of Close price data |
| 📊 Technical Indicators | RSI, MACD, MA20, MA50 |
| 📰 News Sentiment | Live news via NewsData.io + TextBlob NLP |
| 📈 Interactive Charts | Candlestick + Volume + RSI + MACD (Plotly) |
| 🎯 Signal Engine | BUY / SELL / HOLD with confidence % |
| 🤖 AI Explanation | Human-readable reasoning for every signal |
| 🇮🇳 Indian & Global | Supports NSE (.NS) and global tickers |

---

## 🛠️ Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API key (optional but recommended)

Edit `.env` and add your free [NewsData.io](https://newsdata.io) API key:

```env
NEWSDATA_API_KEY=your_actual_key_here
```

> The app works **without** a key — it just skips live news sentiment.

### 3. Run the Flask backend

```bash
python app.py
```

Keep this terminal running. The API starts on `http://localhost:5000`.

### 4. Run the Streamlit frontend (new terminal)

```bash
streamlit run ui.py
```

Opens automatically at `http://localhost:8501`.

---

## 🎮 Usage

1. Choose a stock from the **sidebar quick-buttons** or type any ticker (e.g. `TSLA`, `RELIANCE.NS`)
2. Click **🔍 Analyze Stock**
3. Wait for the model to train on first run (**3–10 min**, then cached)
4. View predictions, signal, chart, and AI explanation

---

## 📁 Project Structure

```
stock/
├── app.py          # Flask REST API
├── ui.py           # Streamlit frontend
├── model.py        # LSTM trainer + predictor
├── sentiment.py    # News sentiment analyzer
├── indicators.py   # RSI, MACD, Moving Averages
├── signals.py      # BUY/SELL/HOLD signal engine
├── requirements.txt
├── .env            # API keys
├── README.md
└── models/         # Saved .h5 models (auto-created)
```

---

## 📈 Supported Tickers

### Indian (NSE)
`RELIANCE.NS` `TCS.NS` `INFY.NS` `HDFCBANK.NS` `WIPRO.NS` `SBIN.NS` `ICICIBANK.NS` `BAJFINANCE.NS`

### Global
`AAPL` `TSLA` `NVDA` `MSFT` `GOOGL` `AMZN` `META`

> Any ticker supported by Yahoo Finance works!

---

## ⚠️ Disclaimer

This application is for **educational purposes only**. It does not constitute financial advice. Always consult a qualified financial advisor before making investment decisions.
