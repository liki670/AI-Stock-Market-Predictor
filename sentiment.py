"""
sentiment.py — News Sentiment Analyzer
Fetches top news for a stock via NewsData.io and scores via TextBlob.
Falls back to 0.0 (neutral) if API key missing or call fails.
"""

import os
import requests
from textblob import TextBlob
from dotenv import load_dotenv

load_dotenv()

NEWSDATA_API_KEY = os.getenv("NEWSDATA_API_KEY", "")
NEWSDATA_URL     = "https://newsdata.io/api/1/news"
MAX_ARTICLES     = 8


def _polarity(text: str) -> float:
    """TextBlob polarity in [-1, +1]."""
    return TextBlob(text).sentiment.polarity


def fetch_sentiment(query: str) -> dict:
    """
    Returns:
        score       float [-1, +1]
        label       str   (Bullish / Bearish / Neutral)
        articles    list of {title, url, score}
    """
    articles_out = []

    if not NEWSDATA_API_KEY or NEWSDATA_API_KEY == "your_key_here":
        return {"score": 0.0, "label": "Neutral", "articles": articles_out}

    try:
        params = {
            "apikey":   NEWSDATA_API_KEY,
            "q":        query,
            "language": "en",
            "size":     MAX_ARTICLES,
        }
        resp = requests.get(NEWSDATA_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        scores = []
        for art in data.get("results", []):
            title = art.get("title", "") or ""
            desc  = art.get("description", "") or ""
            text  = f"{title}. {desc}".strip()
            pol   = _polarity(text)
            scores.append(pol)
            articles_out.append({
                "title": title,
                "url":   art.get("link", ""),
                "score": round(pol, 3),
            })

        if not scores:
            return {"score": 0.0, "label": "Neutral", "articles": articles_out}

        avg = sum(scores) / len(scores)
        avg = round(avg, 4)
        if avg > 0.05:
            label = "Bullish 🟢"
        elif avg < -0.05:
            label = "Bearish 🔴"
        else:
            label = "Neutral 🟡"

        return {"score": avg, "label": label, "articles": articles_out}

    except Exception as e:
        print(f"[sentiment] Error: {e}")
        return {"score": 0.0, "label": "Neutral", "articles": articles_out}


if __name__ == "__main__":
    result = fetch_sentiment("Reliance Industries")
    print(result)
