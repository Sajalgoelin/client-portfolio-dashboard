import yfinance as yf
import pandas as pd
import streamlit as st
from datetime import date

# Try Nifty 500 first, fall back to Nifty 50
_TICKERS = [
    ("^CRSLDX", "Nifty 500"),
    ("^NSEI", "Nifty 50"),
]


@st.cache_data(ttl=3600)
def get_benchmark_data(start_date, end_date=None):
    """Return a DataFrame with columns [close, benchmark_name] from start_date to today."""
    if end_date is None:
        end_date = date.today()

    for ticker, label in _TICKERS:
        try:
            raw = yf.download(ticker, start=start_date, end=end_date, progress=False, auto_adjust=True)
            if raw.empty:
                continue
            close = raw["Close"].squeeze()
            df = close.to_frame(name="close")
            df.index = pd.to_datetime(df.index)
            df.attrs["label"] = label
            return df
        except Exception:
            continue

    return pd.DataFrame()
