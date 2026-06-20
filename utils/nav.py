import pandas as pd
import numpy as np
import yfinance as yf
import streamlit as st
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import INITIAL_CAPITAL, TICKER_MAP


@st.cache_data(ttl=3600)
def build_daily_nav(trades: pd.DataFrame) -> pd.Series:
    """
    Compute daily portfolio NAV % return vs initial capital, for every business
    day from inception to today.

    NAV(t) = cash(t) + Σ(qty × market_price(t))  for all positions open on day t

    cash(t) = INITIAL_CAPITAL
              - Σ notional_buy_after_comm  for positions opened on or before t
              + Σ notional_sell_after_comm for positions closed strictly before t
    """
    valid = trades[trades["opening_date"].notna() & trades["qty"].notna()].copy()
    if valid.empty:
        return pd.Series(dtype=float)

    inception = valid["opening_date"].min()
    today = pd.Timestamp.today().normalize()

    # ── Fetch all historical prices in one batch ─────────────────────────────
    name_to_ticker: dict[str, str] = {}
    for name in valid["name"].unique():
        t = TICKER_MAP.get(name.strip())
        if t:
            name_to_ticker[name.strip()] = t

    prices: dict[str, pd.Series] = {}  # ticker → daily close Series
    if name_to_ticker:
        tickers = list(set(name_to_ticker.values()))
        try:
            raw = yf.download(
                tickers, start=str(inception.date()), progress=False, auto_adjust=True
            )
            if not raw.empty:
                close = raw["Close"]
                if isinstance(close, pd.Series):
                    # Single ticker returned as Series
                    prices[tickers[0]] = close.squeeze()
                else:
                    for tk in tickers:
                        if tk in close.columns:
                            s = close[tk].dropna()
                            if not s.empty:
                                prices[tk] = s
        except Exception:
            pass

    def _price_on(name: str, day: pd.Timestamp, fallback: float) -> float:
        ticker = name_to_ticker.get(name.strip())
        if ticker and ticker in prices:
            available = prices[ticker].loc[prices[ticker].index <= day].dropna()
            if not available.empty:
                return float(available.iloc[-1])
        return fallback

    # ── Build daily NAV series (business days only) ───────────────────────────
    date_range = pd.bdate_range(start=inception, end=today)
    nav_pct: dict[pd.Timestamp, float] = {}

    for day in date_range:
        # Positions open on this day
        open_mask = (valid["opening_date"] <= day) & (
            valid["closing_date"].isna() | (valid["closing_date"] >= day)
        )
        open_pos = valid[open_mask]

        # Cash balance
        buys = valid.loc[valid["opening_date"] <= day, "notional_buy_after_comm"].sum()
        sells = valid.loc[
            valid["closing_date"].notna() & (valid["closing_date"] < day),
            "notional_sell_after_comm",
        ].sum()
        cash = float(INITIAL_CAPITAL - buys + sells)

        # Market value of open positions
        open_value = sum(
            float(row["qty"]) * _price_on(row["name"], day, float(row["trade_price"]))
            for _, row in open_pos.iterrows()
        )

        nav = cash + open_value
        nav_pct[day] = (nav - INITIAL_CAPITAL) / INITIAL_CAPITAL * 100

    return pd.Series(nav_pct)
