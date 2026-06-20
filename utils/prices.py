import yfinance as yf
import pandas as pd
import streamlit as st
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import TICKER_MAP


@st.cache_data(ttl=1800)  # 30-minute cache — not live, just reasonably fresh
def fetch_current_prices(stock_names: list) -> dict:
    """
    Fetch the latest closing price for a list of stock names.
    Returns {stock_name: price_float}. Missing tickers return no entry.
    """
    name_to_ticker = {}
    for name in stock_names:
        ticker = TICKER_MAP.get(name.strip())
        if ticker:
            name_to_ticker[name] = ticker

    if not name_to_ticker:
        return {}

    tickers = list(name_to_ticker.values())

    try:
        raw = yf.download(tickers, period="5d", progress=False, auto_adjust=True)
        if raw.empty:
            return {}

        close = raw["Close"]
        prices = {}

        for name, ticker in name_to_ticker.items():
            try:
                if isinstance(close, pd.Series):
                    # Single ticker — close is a Series
                    price = float(close.dropna().iloc[-1])
                else:
                    # Multiple tickers — close is a DataFrame
                    price = float(close[ticker].dropna().iloc[-1])
                prices[name] = price
            except Exception:
                pass

        return prices

    except Exception:
        return {}
