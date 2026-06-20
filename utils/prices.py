import yfinance as yf
import pandas as pd
import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import TICKER_MAP


def _fetch_single(ticker: str) -> float | None:
    """Fetch latest close for one ticker via Ticker.history — more reliable than batch."""
    try:
        hist = yf.Ticker(ticker).history(period="5d", auto_adjust=True)
        if not hist.empty:
            return float(hist["Close"].dropna().iloc[-1])
    except Exception:
        pass
    return None


@st.cache_data(ttl=1800)  # 30-minute cache
def fetch_current_prices(stock_names: list) -> dict:
    """
    Fetch the latest closing price for a list of stock names.
    Returns {stock_name: price_float}. Missing tickers return no entry.

    Strategy: try batch download first (fast), then fall back to individual
    Ticker.history() calls for any ticker not returned by the batch.
    """
    name_to_ticker: dict[str, str] = {}
    for name in stock_names:
        ticker = TICKER_MAP.get(name.strip())
        if ticker:
            name_to_ticker[name] = ticker

    if not name_to_ticker:
        return {}

    tickers = list(name_to_ticker.values())
    prices: dict[str, float] = {}

    # ── Batch download ────────────────────────────────────────────────────────
    try:
        raw = yf.download(tickers, period="5d", progress=False, auto_adjust=True)
        if not raw.empty:
            close = raw["Close"]
            for name, ticker in name_to_ticker.items():
                try:
                    col = close if isinstance(close, pd.Series) else close[ticker]
                    val = col.dropna().iloc[-1]
                    prices[name] = float(val)
                except Exception:
                    pass  # will retry individually below
    except Exception:
        pass

    # ── Individual fallback for anything the batch missed ─────────────────────
    missing = [name for name in name_to_ticker if name not in prices]
    for name in missing:
        ticker = name_to_ticker[name]
        price = _fetch_single(ticker)
        if price is not None:
            prices[name] = price

    return prices
