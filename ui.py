"""
ui.py — Streamlit Frontend for AI Stock Market Predictor
Run with: streamlit run ui.py
"""

import os
import streamlit as st
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

API_BASE = os.getenv("API_BASE_URL", "http://localhost:5000")

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Stock Predictor",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Dark background */
.stApp {
    background: linear-gradient(135deg, #0a0e1a 0%, #0d1526 50%, #0a0e1a 100%);
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: rgba(13, 21, 38, 0.95) !important;
    border-right: 1px solid rgba(99, 179, 237, 0.15);
}

/* Metric cards */
.metric-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(99,179,237,0.18);
    border-radius: 16px;
    padding: 20px 24px;
    text-align: center;
    backdrop-filter: blur(12px);
    transition: transform 0.2s, box-shadow 0.2s;
}
.metric-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 32px rgba(99,179,237,0.15);
}
.metric-label {
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    color: #63b3ed;
    margin-bottom: 6px;
}
.metric-value {
    font-size: 28px;
    font-weight: 800;
    color: #f0f4ff;
}
.metric-sub {
    font-size: 13px;
    color: #718096;
    margin-top: 4px;
}

/* Signal badge */
.signal-badge {
    display: inline-block;
    padding: 10px 32px;
    border-radius: 50px;
    font-size: 26px;
    font-weight: 800;
    letter-spacing: 3px;
    animation: pulse 2s infinite;
}
.signal-BUY  { background: linear-gradient(135deg,#00c851,#007e33); color:#fff; box-shadow:0 0 24px rgba(0,200,81,0.45); }
.signal-SELL { background: linear-gradient(135deg,#ff4444,#cc0000); color:#fff; box-shadow:0 0 24px rgba(255,68,68,0.45); }
.signal-HOLD { background: linear-gradient(135deg,#ffbb33,#ff8800); color:#fff; box-shadow:0 0 24px rgba(255,187,51,0.45); }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.82} }

/* Explanation box */
.expl-box {
    background: rgba(99,179,237,0.07);
    border-left: 4px solid #63b3ed;
    border-radius: 0 12px 12px 0;
    padding: 18px 22px;
    color: #cbd5e0;
    font-size: 15px;
    line-height: 1.7;
}

/* Section header */
.section-title {
    font-size: 18px;
    font-weight: 700;
    color: #e2e8f0;
    margin: 24px 0 12px 0;
    padding-bottom: 8px;
    border-bottom: 1px solid rgba(99,179,237,0.2);
}

/* News card */
.news-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 8px;
}
.news-title { font-size: 14px; color: #e2e8f0; font-weight: 500; }
.news-score-pos { color: #48bb78; font-size: 12px; font-weight: 600; }
.news-score-neg { color: #fc8181; font-size: 12px; font-weight: 600; }
.news-score-neu { color: #a0aec0; font-size: 12px; font-weight: 600; }

/* Hide Streamlit branding */
#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ── Ticker data ────────────────────────────────────────────────────────
INDIAN_TICKERS = {
    "Reliance":  "RELIANCE.NS",
    "TCS":       "TCS.NS",
    "Infosys":   "INFY.NS",
    "HDFC Bank": "HDFCBANK.NS",
    "Wipro":     "WIPRO.NS",
    "SBI":       "SBIN.NS",
    "ICICI":     "ICICIBANK.NS",
}
GLOBAL_TICKERS = {
    "Apple":     "AAPL",
    "Tesla":     "TSLA",
    "Nvidia":    "NVDA",
    "Microsoft": "MSFT",
    "Google":    "GOOGL",
    "Amazon":    "AMZN",
    "Meta":      "META",
}

# Ticker → display name
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
    "NFLX":  "Netflix",
    "AMD":   "AMD",
    "INTC":  "Intel",
    "ORCL":  "Oracle",
    "IBM":   "IBM",
}

# ── Smart name → ticker resolver ──────────────────────────────────
# Maps every lowercase keyword a user might type → canonical ticker
NAME_TO_TICKER = {
    # Indian companies
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
    # Global companies
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
    "instagram":             "META",
    "whatsapp":              "META",
    "netflix":               "NFLX",
    "nflx":                  "NFLX",
    "amd":                   "AMD",
    "advanced micro":        "AMD",
    "intc":                  "INTC",
    "oracle":                "ORCL",
    "ibm":                   "IBM",
}

@st.cache_data(ttl=86400, show_spinner=False)
def _load_extended_market_data():
    """Loads all NSE stocks dynamically to populate the resolver."""
    n2t = NAME_TO_TICKER.copy()
    cnames = COMPANY_NAMES.copy()
    try:
        import pandas as pd
        url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
        df = pd.read_csv(url)
        for _, row in df.iterrows():
            sym = str(row["SYMBOL"]).strip() + ".NS"
            name = str(row["NAME OF COMPANY"]).strip()
            cnames[sym] = name
            
            # Map full name
            n2t[name.lower()] = sym
            
            # Map bare symbol (TITAN -> TITAN.NS)
            bare_sym = str(row["SYMBOL"]).strip().lower()
            if bare_sym not in n2t:
                n2t[bare_sym] = sym
    except Exception as e:
        print(f"Failed to load NSE dataset: {e}")
    
    return n2t, cnames

# Evaluate once per run (cached)
FULL_NAME_TO_TICKER, FULL_COMPANY_NAMES = _load_extended_market_data()


def resolve_ticker(user_input: str) -> tuple[str, str | None]:
    """
    Given free-form user text, return (resolved_ticker, match_label).
    match_label is None if the input already looks like a raw ticker.

    Priority:
      1. Exact ticker match  (AAPL, TCS.NS)
      2. Exact name match    (apple, reliance)
      3. Substring match     (tata -> TCS.NS)
      4. Fuzzy match         (appl -> AAPL)
      5. Return input as-is  (user may know an exotic ticker)
    """
    import difflib

    raw   = user_input.strip()
    lower = raw.lower()

    # 1. Already a known exact ticker
    if raw.upper() in FULL_COMPANY_NAMES:
        return raw.upper(), None

    # 2. Exact name match
    if lower in FULL_NAME_TO_TICKER:
        ticker = FULL_NAME_TO_TICKER[lower]
        return ticker, FULL_COMPANY_NAMES.get(ticker, ticker)

    # 3. Substring match
    for key, ticker in FULL_NAME_TO_TICKER.items():
        if lower in key or key in lower:
            return ticker, FULL_COMPANY_NAMES.get(ticker, ticker)

    # 4. Fuzzy match against all keys
    all_keys = list(FULL_NAME_TO_TICKER.keys())
    matches  = difflib.get_close_matches(lower, all_keys, n=1, cutoff=0.6)
    if matches:
        ticker = FULL_NAME_TO_TICKER[matches[0]]
        return ticker, FULL_COMPANY_NAMES.get(ticker, ticker)

    # 5. Treat as raw ticker symbol
    return raw.upper(), None


def get_company_name(ticker: str) -> str:
    return FULL_COMPANY_NAMES.get(ticker.upper(), ticker)


# ── Helpers ───────────────────────────────────────────────────────────────────
def call_predict(ticker: str) -> dict:
    try:
        r = requests.post(f"{API_BASE}/predict", json={"symbol": ticker}, timeout=300)
        return r.json()
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to Flask API. Please run: python app.py"}
    except Exception as e:
        return {"error": str(e)}


def call_history(ticker: str) -> list:
    try:
        r = requests.get(f"{API_BASE}/history/{ticker}", timeout=60)
        return r.json().get("data", [])
    except Exception:
        return []


def signal_color(sig: str) -> str:
    return {"BUY": "#00c851", "SELL": "#ff4444", "HOLD": "#ffbb33"}.get(sig, "#a0aec0")


def fmt_price(val, currency=""):
    return f"{currency}{val:,.2f}"


def make_chart(history: list, ticker: str) -> go.Figure:
    if not history:
        return None

    df = pd.DataFrame(history)
    df["date"] = pd.to_datetime(df["date"])

    # MA
    df["MA20"] = df["close"].rolling(20).mean()
    df["MA50"] = df["close"].rolling(50).mean()

    # RSI
    delta = df["close"].diff()
    gain  = delta.clip(lower=0).ewm(com=13, min_periods=14).mean()
    loss  = (-delta).clip(lower=0).ewm(com=13, min_periods=14).mean()
    rs    = gain / loss.replace(0, float("nan"))
    df["RSI"] = 100 - 100 / (1 + rs)

    # MACD
    ema12       = df["close"].ewm(span=12, adjust=False).mean()
    ema26       = df["close"].ewm(span=26, adjust=False).mean()
    df["MACD"]  = ema12 - ema26
    df["MACDs"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["MACDh"] = df["MACD"] - df["MACDs"]

    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        row_heights=[0.55, 0.22, 0.23],
        vertical_spacing=0.04,
        subplot_titles=(f"{ticker} — Price & Volume", "RSI (14)", "MACD (12,26,9)"),
    )

    # ── Candlestick
    fig.add_trace(go.Candlestick(
        x=df["date"], open=df["open"], high=df["high"],
        low=df["low"], close=df["close"], name="Price",
        increasing_line_color="#00c851", decreasing_line_color="#ff4444",
        increasing_fillcolor="rgba(0,200,81,0.8)",
        decreasing_fillcolor="rgba(255,68,68,0.8)",
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=df["date"], y=df["MA20"], name="MA 20",
        line=dict(color="#63b3ed", width=1.5, dash="dot"),
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["MA50"], name="MA 50",
        line=dict(color="#f6ad55", width=1.5, dash="dot"),
    ), row=1, col=1)

    # Volume bars
    vol_colors = ["rgba(0,200,81,0.45)" if c >= o else "rgba(255,68,68,0.45)"
                  for c, o in zip(df["close"], df["open"])]
    fig.add_trace(go.Bar(
        x=df["date"], y=df["volume"], name="Volume",
        marker_color=vol_colors, yaxis="y2",
        showlegend=False,
    ), row=1, col=1)

    # ── RSI
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["RSI"], name="RSI",
        line=dict(color="#b794f4", width=1.8),
    ), row=2, col=1)
    fig.add_hline(y=70, line_dash="dot", line_color="rgba(255,68,68,0.5)", row=2, col=1)
    fig.add_hline(y=30, line_dash="dot", line_color="rgba(0,200,81,0.5)", row=2, col=1)
    fig.add_hrect(y0=30, y1=70, fillcolor="rgba(255,255,255,0.02)", line_width=0, row=2, col=1)

    # ── MACD
    macd_colors = ["rgba(0,200,81,0.7)" if v >= 0 else "rgba(255,68,68,0.7)" for v in df["MACDh"]]
    fig.add_trace(go.Bar(
        x=df["date"], y=df["MACDh"], name="MACD Hist",
        marker_color=macd_colors,
    ), row=3, col=1)
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["MACD"], name="MACD",
        line=dict(color="#63b3ed", width=1.5),
    ), row=3, col=1)
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["MACDs"], name="Signal",
        line=dict(color="#f6ad55", width=1.5),
    ), row=3, col=1)

    fig.update_layout(
        height=680,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color="#a0aec0", size=12),
        legend=dict(
            bgcolor="rgba(13,21,38,0.8)",
            bordercolor="rgba(99,179,237,0.2)",
            borderwidth=1,
            font=dict(size=11),
        ),
        xaxis_rangeslider_visible=False,
        margin=dict(l=0, r=0, t=40, b=0),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="rgba(13,21,38,0.95)",
            bordercolor="rgba(99,179,237,0.3)",
            font_family="Inter",
        ),
    )
    for i in range(1, 4):
        fig.update_xaxes(
            showgrid=True, gridcolor="rgba(255,255,255,0.05)",
            zeroline=False, row=i, col=1,
        )
        fig.update_yaxes(
            showgrid=True, gridcolor="rgba(255,255,255,0.05)",
            zeroline=False, row=i, col=1,
        )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📈 AI Stock Predictor")
    st.markdown("<hr style='border-color:rgba(99,179,237,0.2);margin:8px 0 16px 0'>", unsafe_allow_html=True)

    # Persist selected ticker across re-runs via session_state
    if "selected_ticker" not in st.session_state:
        st.session_state["selected_ticker"] = "AAPL"
    if "last_search" not in st.session_state:
        st.session_state["last_search"] = ""

    def handle_button_click(sym):
        st.session_state["selected_ticker"] = sym
        st.session_state["last_search"] = ""
        if "match_label" in st.session_state:
            del st.session_state["match_label"]

    typed_raw = st.text_input(
        "Search company or ticker",
        value="",
        placeholder="e.g. Apple, Reliance, TCS, NVDA...",
        help="Type a company name or ticker symbol — we'll match it automatically",
        key="ticker_text_input",
    ).strip()

    # Resolve typed input only if it changed
    if typed_raw and typed_raw != st.session_state["last_search"]:
        resolved, match_label = resolve_ticker(typed_raw)
        st.session_state["selected_ticker"] = resolved
        st.session_state["last_search"] = typed_raw
        if match_label:
            st.session_state["match_label"] = match_label
        else:
            st.session_state.pop("match_label", None)
    elif not typed_raw:
        st.session_state["last_search"] = ""
        st.session_state.pop("match_label", None)

    if typed_raw and "match_label" in st.session_state:
        st.markdown(
            f"<div style='background:rgba(72,187,120,0.12);border:1px solid rgba(72,187,120,0.35);"
            f"border-radius:8px;padding:8px 12px;margin-bottom:4px'>"
            f"<span style='color:#68d391;font-size:12px;font-weight:600'>Matched →</span> "
            f"<span style='color:#f0f4ff;font-size:13px;font-weight:700'>{st.session_state['match_label']}</span><br>"
            f"<span style='color:#63b3ed;font-size:11px'>{st.session_state['selected_ticker']}</span></div>",
            unsafe_allow_html=True,
        )

    st.markdown("**🇮🇳 Indian Stocks**")
    cols_in = st.columns(2)
    for idx, (name, sym) in enumerate(INDIAN_TICKERS.items()):
        cols_in[idx % 2].button(name, key=f"in_{sym}", use_container_width=True, on_click=handle_button_click, args=(sym,))

    st.markdown("**🌐 Global Stocks**")
    cols_gl = st.columns(2)
    for idx, (name, sym) in enumerate(GLOBAL_TICKERS.items()):
        cols_gl[idx % 2].button(name, key=f"gl_{sym}", use_container_width=True, on_click=handle_button_click, args=(sym,))

    st.markdown("<br>", unsafe_allow_html=True)
    analyze_btn = st.button("🔍 Analyze Stock", type="primary", use_container_width=True)

    # Show currently selected stock
    cur_sel = st.session_state["selected_ticker"]
    st.markdown(
        f"<p style='font-size:12px;color:#63b3ed;text-align:center;margin-top:4px'>"
        f"Selected: <strong>{get_company_name(cur_sel)}</strong><br>"
        f"<span style='color:#4a5568'>{cur_sel}</span></p>",
        unsafe_allow_html=True,
    )

    st.markdown("<hr style='border-color:rgba(99,179,237,0.1);margin:16px 0 8px 0'>", unsafe_allow_html=True)
    st.markdown(
        "<p style='font-size:11px;color:#4a5568;text-align:center'>"
        "⚠️ For educational purposes only.<br>Not financial advice.</p>",
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# MAIN CONTENT
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    "<h1 style='color:#f0f4ff;font-size:36px;font-weight:800;margin-bottom:4px'>"
    "🤖 AI Stock Market Predictor</h1>"
    "<p style='color:#718096;font-size:15px;margin-bottom:28px'>"
    "LSTM Deep Learning · News Sentiment · Technical Indicators · BUY / SELL / HOLD Signals</p>",
    unsafe_allow_html=True,
)

# Check API connectivity
try:
    ping = requests.get(f"{API_BASE}/", timeout=3)
    api_ok = ping.status_code == 200
except Exception:
    api_ok = False

if not api_ok:
    st.error(
        "⚡ **Flask API is not running.**  \n"
        "Open a terminal and run:  \n```\npython app.py\n```",
        icon="🔌",
    )
    st.stop()

if analyze_btn or "result" in st.session_state:
    if analyze_btn:
        st.session_state.pop("result", None)
        st.session_state.pop("history", None)
        # Always use the persisted selected_ticker
        st.session_state["ticker"] = st.session_state["selected_ticker"]

    current_ticker = st.session_state.get("ticker", st.session_state["selected_ticker"])
    company_name   = get_company_name(current_ticker)

    if analyze_btn:
        with st.spinner(f"Analyzing {company_name} ({current_ticker}) — first run trains the LSTM model, please wait…"):
            result  = call_predict(current_ticker)
            history = call_history(current_ticker)
        st.session_state["result"]  = result
        st.session_state["history"] = history
    else:
        result  = st.session_state["result"]
        history = st.session_state["history"]
        company_name = get_company_name(current_ticker)

    if "error" in result:
        st.error(f"❌ {result['error']}")
        st.stop()

    # ── Company name header ─────────────────────────────────────────────────
    st.markdown(
        f"<div style='margin-bottom:20px'>"
        f"<span style='font-size:22px;font-weight:800;color:#f0f4ff'>{company_name}</span>"
        f"&nbsp;&nbsp;<span style='font-size:14px;color:#63b3ed;background:rgba(99,179,237,0.12);"
        f"padding:4px 10px;border-radius:20px;font-weight:600'>{current_ticker}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # ── METRIC CARDS ────────────────────────────────────────────────────────
    cur   = result["current_price"]
    pred  = result["predicted_price"]
    pct   = result["pct_change"]
    sig   = result["signal"]
    conf  = result["confidence"]
    sent  = result["sentiment"]
    rsi   = result["rsi"]
    macd  = result["macd"]

    pct_color  = "#48bb78" if pct >= 0 else "#fc8181"
    pct_arrow  = "▲" if pct >= 0 else "▼"
    sent_color = "#48bb78" if sent > 0.05 else ("#fc8181" if sent < -0.05 else "#a0aec0")

    c1, c2, c3, c4, c5 = st.columns(5)
    cards = [
        (c1, "Current Price",    f"${cur:,.2f}" if not current_ticker.endswith(".NS") else f"₹{cur:,.2f}", ""),
        (c2, "Predicted Price",  f"${pred:,.2f}" if not current_ticker.endswith(".NS") else f"₹{pred:,.2f}", ""),
        (c3, "Expected Change",  f"{pct_arrow} {abs(pct):.2f}%", pct_color),
        (c4, "RSI (14)",         f"{rsi:.1f}", "#48bb78" if rsi < 40 else ("#fc8181" if rsi > 65 else "#a0aec0")),
        (c5, "Sentiment Score",  f"{sent:+.3f}", sent_color),
    ]
    for col, label, val, color in cards:
        with col:
            col_style = f"color:{color}" if color else "color:#f0f4ff"
            st.markdown(
                f"<div class='metric-card'>"
                f"<div class='metric-label'>{label}</div>"
                f"<div class='metric-value' style='{col_style}'>{val}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── SIGNAL + CONFIDENCE ─────────────────────────────────────────────────
    col_sig, col_conf = st.columns([1, 2])
    with col_sig:
        st.markdown(
            f"<div style='text-align:center;padding:20px 0'>"
            f"<div class='signal-badge signal-{sig}'>{sig}</div>"
            f"<div style='color:#718096;font-size:13px;margin-top:10px'>Trading Signal</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
    with col_conf:
        st.markdown("<div class='section-title'>Confidence Score</div>", unsafe_allow_html=True)
        st.progress(int(conf) / 100)
        st.markdown(
            f"<p style='color:#a0aec0;font-size:14px'>"
            f"Model confidence: <strong style='color:#f0f4ff'>{conf:.1f}%</strong> — "
            f"Sentiment: <strong style='color:{sent_color}'>{result['sentiment_label']}</strong>"
            f"</p>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<p style='color:#a0aec0;font-size:13px'>"
            f"MACD: <strong style='color:#63b3ed'>{macd:.4f}</strong> &nbsp;|&nbsp; "
            f"MACD Signal: <strong style='color:#f6ad55'>{result['macd_signal']:.4f}</strong> &nbsp;|&nbsp; "
            f"Histogram: <strong>{result['macd_histogram']:.4f}</strong>"
            f"</p>",
            unsafe_allow_html=True,
        )

    # ── AI EXPLANATION ──────────────────────────────────────────────────────
    st.markdown("<div class='section-title'>🤖 AI Explanation</div>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='expl-box'>{result['explanation']}</div>",
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── CHART ───────────────────────────────────────────────────────────────
    st.markdown("<div class='section-title'>📊 Interactive Chart</div>", unsafe_allow_html=True)
    fig = make_chart(history, current_ticker)
    if fig:
        st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})
    else:
        st.info("Chart data unavailable — history endpoint may still be loading.")

    # ── NEWS ────────────────────────────────────────────────────────────────
    news = result.get("news", [])
    if news:
        st.markdown("<div class='section-title'>📰 Latest News & Sentiment</div>", unsafe_allow_html=True)
        for art in news:
            sc    = art["score"]
            sc_cl = "news-score-pos" if sc > 0.05 else ("news-score-neg" if sc < -0.05 else "news-score-neu")
            sc_lbl = f"{'▲' if sc>0 else '▼'} {sc:+.3f}"
            url   = art.get("url", "#")
            st.markdown(
                f"<div class='news-card'>"
                f"<span class='news-title'><a href='{url}' target='_blank' style='color:#e2e8f0;text-decoration:none'>{art['title']}</a></span>"
                f"&nbsp;&nbsp;<span class='{sc_cl}'>{sc_lbl}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
    elif not result.get("news"):
        st.info("💡 Add your NewsData.io API key in `.env` to enable live news sentiment analysis.")

else:
    # ── WELCOME STATE ────────────────────────────────────────────────────────
    st.markdown(
        "<div style='text-align:center;padding:60px 20px'>"
        "<div style='font-size:72px;margin-bottom:16px'>📈</div>"
        "<h2 style='color:#e2e8f0;font-weight:700'>Select a stock and click Analyze</h2>"
        "<p style='color:#718096;font-size:16px;max-width:500px;margin:0 auto'>"
        "Choose from Indian or global stocks in the sidebar, or enter any ticker symbol. "
        "The AI will predict prices, analyze sentiment, and generate a trading signal."
        "</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    # Feature cards
    fc1, fc2, fc3 = st.columns(3)
    feats = [
        ("🧠", "LSTM Prediction", "Deep learning model trained on 5 years of historical price data"),
        ("📰", "News Sentiment", "Live news analysis using TextBlob NLP sentiment scoring"),
        ("📊", "Technical Analysis", "RSI, MACD, Moving Averages with interactive Plotly charts"),
    ]
    for col, (icon, title, desc) in zip([fc1, fc2, fc3], feats):
        with col:
            st.markdown(
                f"<div class='metric-card' style='text-align:left'>"
                f"<div style='font-size:32px;margin-bottom:10px'>{icon}</div>"
                f"<div style='color:#e2e8f0;font-weight:700;font-size:16px;margin-bottom:6px'>{title}</div>"
                f"<div style='color:#718096;font-size:13px'>{desc}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
