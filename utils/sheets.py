import pandas as pd
import requests
import streamlit as st
from io import StringIO

SHEET_ID = "1C1LhV_oMb3VzaCLT2_6M2esmvDGfIZwTtqj0DnehcmY"

# Column positions in the raw CSV (0-indexed)
# NO | OPENING | CLOSING(date) | NAME | SEGMENT | COMM | QTY | TRADE PRICE |
# CLOSING(price) | TRADE PRICE AFTER COMM | CLOSING PRICE AFTER COMM |
# STOP LOSS | TAKE PROFIT | NOTIONAL BUY BEFORE COMM | NOTIONAL SELL BEFORE COMM |
# NOTIONAL BUY AFTER COMM | NOTIONAL SELL AFTER COMM | COMMISSION |
# PROFIT/LOSS | PROFIT/LOSS% | NOTES
TRADE_COL_NAMES = [
    "trade_no", "opening_date", "closing_date", "name", "segment",
    "comm_rate", "qty", "trade_price", "closing_price",
    "trade_price_after_comm", "closing_price_after_comm",
    "stop_loss", "take_profit",
    "notional_buy_before_comm", "notional_sell_before_comm",
    "notional_buy_after_comm", "notional_sell_after_comm",
    "commission", "profit_loss", "profit_loss_pct", "notes",
]

DIV_COL_NAMES = ["name", "ex_date", "payment_date", "dividend_per_share", "shares", "total_dividend"]


def _to_num(series):
    return pd.to_numeric(
        series.astype(str).str.replace(",", "").str.replace("%", "").str.strip(),
        errors="coerce",
    )


@st.cache_data(ttl=300)
def load_portfolio_data():
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        raise RuntimeError(
            f"Cannot fetch sheet. Ensure it is shared as 'Anyone with the link can view'. Error: {e}"
        )

    lines = resp.text.strip().split("\n")

    # Locate dividends table (starts where a row contains "EX DATE")
    div_start_idx = None
    for i, line in enumerate(lines):
        if "EX DATE" in line.upper():
            div_start_idx = i
            break

    trade_lines = lines[:div_start_idx] if div_start_idx else lines
    # Remove rows that are entirely empty (just commas)
    trade_lines = [l for l in trade_lines if l.replace(",", "").strip()]

    # --- Parse trades ---
    raw = pd.read_csv(StringIO("\n".join(trade_lines)), header=0, dtype=str)

    # Trim to expected number of columns and rename
    n_cols = len(TRADE_COL_NAMES)
    if raw.shape[1] >= n_cols:
        raw = raw.iloc[:, :n_cols]
    raw.columns = TRADE_COL_NAMES[: raw.shape[1]]

    # Drop rows with no stock name
    trades = raw[raw["name"].notna() & (raw["name"].str.strip() != "")].copy()

    trades["opening_date"] = pd.to_datetime(trades["opening_date"], dayfirst=True, errors="coerce")
    trades["closing_date"] = pd.to_datetime(trades["closing_date"], dayfirst=True, errors="coerce")

    for col in [
        "qty", "trade_price", "closing_price",
        "notional_buy_after_comm", "notional_sell_after_comm",
        "commission", "profit_loss",
    ]:
        if col in trades.columns:
            trades[col] = _to_num(trades[col])

    if "profit_loss_pct" in trades.columns:
        trades["profit_loss_pct"] = _to_num(trades["profit_loss_pct"])

    # Open trades: closing_date is null — zero out the placeholder P&L the sheet writes
    open_mask = trades["closing_date"].isna()
    trades.loc[open_mask, "profit_loss"] = pd.NA
    trades.loc[open_mask, "profit_loss_pct"] = pd.NA

    # --- Parse dividends ---
    dividends = pd.DataFrame()
    if div_start_idx is not None:
        div_lines = [l for l in lines[div_start_idx:] if l.replace(",", "").strip()]
        if len(div_lines) > 1:
            div_raw = pd.read_csv(StringIO("\n".join(div_lines)), header=0, dtype=str)
            div_raw.columns = DIV_COL_NAMES[: div_raw.shape[1]]
            dividends = div_raw.dropna(subset=["name"])
            dividends["total_dividend"] = _to_num(dividends["total_dividend"])

    return trades, dividends
