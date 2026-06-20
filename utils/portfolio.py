import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import INITIAL_CAPITAL


def _valid_open(trades: pd.DataFrame) -> pd.DataFrame:
    """Open trades that have an actual opening date and quantity (not placeholder rows)."""
    open_mask = trades["closing_date"].isna()
    has_data = trades["opening_date"].notna() & trades["qty"].notna()
    return trades[open_mask & has_data].copy()


def enrich_open_positions(trades: pd.DataFrame, current_prices: dict) -> pd.DataFrame:
    """
    Return the open positions DataFrame enriched with:
        current_price, current_value, unrealized_pnl, unrealized_pnl_pct
    Falls back to cost basis when live price is unavailable.
    """
    df = _valid_open(trades).copy()
    if df.empty:
        return df

    df["current_price"] = df["name"].map(current_prices)
    df["price_live"] = df["current_price"].notna()

    # Where live price exists use it; otherwise fall back to buy price
    df["current_price"] = df["current_price"].fillna(df["trade_price"])

    df["current_value"] = df["current_price"] * df["qty"]
    df["unrealized_pnl"] = df["current_value"] - df["notional_buy_after_comm"]
    df["unrealized_pnl_pct"] = df["unrealized_pnl"] / df["notional_buy_after_comm"] * 100

    return df


def compute_summary_stats(
    trades: pd.DataFrame,
    dividends: pd.DataFrame,
    current_prices: dict | None = None,
) -> dict:
    if current_prices is None:
        current_prices = {}

    closed = trades[trades["closing_date"].notna()].copy()
    open_pos = enrich_open_positions(trades, current_prices)

    realized_pnl = float(closed["profit_loss"].sum()) if not closed.empty else 0.0

    wins = int((closed["profit_loss"] > 0).sum()) if not closed.empty else 0
    losses = int((closed["profit_loss"] < 0).sum()) if not closed.empty else 0
    total_closed = len(closed)
    win_rate = (wins / total_closed * 100) if total_closed > 0 else 0.0

    avg_win = closed.loc[closed["profit_loss"] > 0, "profit_loss"].mean() if wins > 0 else 0.0
    avg_loss = closed.loc[closed["profit_loss"] < 0, "profit_loss"].mean() if losses > 0 else 0.0

    open_cost = float(open_pos["notional_buy_after_comm"].sum()) if not open_pos.empty else 0.0
    open_current_value = float(open_pos["current_value"].sum()) if not open_pos.empty else 0.0
    unrealized_pnl = float(open_pos["unrealized_pnl"].sum()) if not open_pos.empty else 0.0
    num_live_prices = int(open_pos["price_live"].sum()) if not open_pos.empty else 0

    # Cash = what's left from initial capital after funding open positions,
    # plus any proceeds from closed trades.
    cash = INITIAL_CAPITAL - open_cost + realized_pnl

    # Portfolio NAV: cash + current value of open positions
    portfolio_nav = cash + open_current_value

    # Total return on initial capital (realized + unrealized)
    total_return_pct = (portfolio_nav - INITIAL_CAPITAL) / INITIAL_CAPITAL * 100

    # Realized-only return (for the chart denominator)
    realized_return_pct = realized_pnl / INITIAL_CAPITAL * 100

    total_dividends = 0.0
    if not dividends.empty and "total_dividend" in dividends.columns:
        total_dividends = float(dividends["total_dividend"].sum())

    return {
        "initial_capital": float(INITIAL_CAPITAL),
        "cash": cash,
        "open_cost": open_cost,
        "open_current_value": open_current_value,
        "realized_pnl": realized_pnl,
        "unrealized_pnl": unrealized_pnl,
        "portfolio_nav": portfolio_nav,
        "total_return_pct": total_return_pct,
        "realized_return_pct": realized_return_pct,
        "win_rate": win_rate,
        "avg_win": float(avg_win) if not np.isnan(avg_win) else 0.0,
        "avg_loss": float(avg_loss) if not np.isnan(avg_loss) else 0.0,
        "total_dividends": total_dividends,
        "num_closed": total_closed,
        "num_open": len(open_pos),
        "wins": wins,
        "losses": losses,
        "num_live_prices": num_live_prices,
    }


def build_return_series(trades: pd.DataFrame) -> pd.Series:
    """
    Cumulative realized return % on initial capital, indexed by close date.
    This is what we plot as the portfolio performance curve.
    """
    closed = trades[trades["closing_date"].notna()].copy()
    if closed.empty:
        return pd.Series(dtype=float)

    by_date = closed.groupby("closing_date")["profit_loss"].sum().sort_index().cumsum()
    pct_series = by_date / INITIAL_CAPITAL * 100

    inception = trades["opening_date"].min()
    start = pd.Series([0.0], index=pd.DatetimeIndex([inception]))
    return pd.concat([start, pct_series]).sort_index()
