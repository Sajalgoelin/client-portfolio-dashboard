import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date

from utils.benchmark import get_benchmark_data
from utils.prices import fetch_current_prices
from utils.portfolio import compute_summary_stats, build_return_series, enrich_open_positions
from utils.nav import build_daily_nav
from utils.sectors import get_sector
from utils.sheets import load_portfolio_data
from config import INITIAL_CAPITAL, TICKER_MAP

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="Portfolio Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Password gate ─────────────────────────────────────────────────────────────
def _check_password():
    def _verify():
        if st.session_state.get("pwd_input") == st.secrets.get("password", ""):
            st.session_state["authenticated"] = True
        else:
            st.session_state["authenticated"] = False

    if st.session_state.get("authenticated"):
        return True

    st.title("📈 Portfolio Dashboard")
    st.text_input("Enter password", type="password", key="pwd_input", on_change=_verify)
    if st.session_state.get("authenticated") is False:
        st.error("Incorrect password.")
    st.stop()

_check_password()

st.markdown(
    "<style>div[data-testid='metric-container']"
    "{background:#f8f9fa;border-radius:8px;padding:12px 16px;}</style>",
    unsafe_allow_html=True,
)

# ── Data loading ──────────────────────────────────────────────────────────────
trades, dividends = load_portfolio_data()
if trades.empty:
    st.error("No trade data found. Check the Google Sheet connection.")
    st.stop()

inception_date = trades["opening_date"].min().date()
benchmark_df = get_benchmark_data(str(inception_date))
benchmark_label = benchmark_df.attrs.get("label", "Benchmark") if not benchmark_df.empty else "Benchmark"

# Fetch live prices for open positions (30-min cached)
open_names = (
    trades[trades["closing_date"].isna() & trades["opening_date"].notna() & trades["qty"].notna()]["name"]
    .tolist()
)
current_prices = fetch_current_prices(open_names)

stats = compute_summary_stats(trades, dividends, current_prices)
return_series = build_return_series(trades)
open_pos_df = enrich_open_positions(trades, current_prices)
daily_nav = build_daily_nav(trades)

# ── Header ────────────────────────────────────────────────────────────────────
st.title("📊 Portfolio Performance")
st.caption(
    f"Inception: **{inception_date.strftime('%d %b %Y')}** · "
    f"Benchmark: **{benchmark_label}** · "
    f"Prices as of: **{date.today().strftime('%d %b %Y')}**"
)
st.divider()

# ── KPI Row 1 — Portfolio overview ────────────────────────────────────────────
benchmark_return = 0.0
if not benchmark_df.empty and len(benchmark_df) > 1:
    benchmark_return = (benchmark_df["close"].iloc[-1] / benchmark_df["close"].iloc[0] - 1) * 100

alpha = stats["total_return_pct"] - benchmark_return

k1, k2, k3, k4 = st.columns(4)

k1.metric(
    "Initial Capital",
    f"₹{INITIAL_CAPITAL:,.0f}",
)
k2.metric(
    "Portfolio NAV",
    f"₹{stats['portfolio_nav']:,.0f}",
    delta=f"{stats['total_return_pct']:+.2f}% total return",
    help="Cash + current value of open positions (live prices where available)",
)
k3.metric(
    "Cash Available",
    f"₹{stats['cash']:,.0f}",
    help="Initial capital − cost of open positions + realized P&L",
)
k4.metric(
    f"Alpha vs {benchmark_label}",
    f"{alpha:+.2f}%",
    delta=f"Portfolio {stats['total_return_pct']:+.2f}% | {benchmark_label} {benchmark_return:+.2f}%",
    delta_color="normal",
)

st.divider()

# ── KPI Row 2 — P&L breakdown ─────────────────────────────────────────────────
p1, p2, p3, p4, p5 = st.columns(5)

p1.metric(
    "Realized P&L",
    f"₹{stats['realized_pnl']:+,.0f}",
    delta=f"{stats['realized_return_pct']:+.2f}% on initial capital",
)
p2.metric(
    "Unrealized P&L",
    f"₹{stats['unrealized_pnl']:+,.0f}",
    delta=f"{stats['num_live_prices']}/{stats['num_open']} positions with live prices",
    delta_color="off",
)
p3.metric(
    "Win Rate",
    f"{stats['win_rate']:.1f}%",
    help=f"{stats['wins']} wins / {stats['num_closed']} closed trades",
)
p4.metric(
    "Avg Win",
    f"₹{stats['avg_win']:,.0f}",
)
p5.metric(
    "Avg Loss",
    f"₹{stats['avg_loss']:,.0f}",
)

st.divider()

# ── Performance Chart ─────────────────────────────────────────────────────────
st.subheader("Portfolio NAV vs Benchmark")

fig = go.Figure()

# 1. Daily NAV curve — smooth line showing mark-to-market value every day
if not daily_nav.empty:
    fig.add_trace(go.Scatter(
        x=daily_nav.index,
        y=daily_nav.values,
        mode="lines",
        name="Portfolio NAV (daily)",
        line=dict(color="#2ca02c", width=2),
        hovertemplate="%{x|%d %b %Y}<br>NAV return: %{y:.2f}%<extra></extra>",
        fill="tozeroy",
        fillcolor="rgba(44,160,44,0.07)",
    ))

# 2. Realized return step line — shows only locked-in P&L at each trade close
if not return_series.empty:
    fig.add_trace(go.Scatter(
        x=return_series.index,
        y=return_series.values,
        mode="lines+markers",
        name="Realized return (trade closes)",
        line=dict(color="#1f77b4", width=2.5, shape="hv"),
        marker=dict(size=7, color="#1f77b4"),
        hovertemplate="%{x|%d %b %Y}<br>Realized: %{y:.2f}%<extra></extra>",
    ))

# 3. Benchmark line
if not benchmark_df.empty:
    bm_indexed = (benchmark_df["close"] / benchmark_df["close"].iloc[0] - 1) * 100
    fig.add_trace(go.Scatter(
        x=bm_indexed.index,
        y=bm_indexed.values,
        mode="lines",
        name=benchmark_label,
        line=dict(color="#ff7f0e", width=2, dash="dot"),
        hovertemplate="%{x|%d %b %Y}<br>" + benchmark_label + ": %{y:.2f}%<extra></extra>",
    ))

fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.4)
fig.update_layout(
    yaxis_title="Return (%)",
    xaxis_title=None,
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    height=420,
    margin=dict(l=0, r=0, t=30, b=0),
    plot_bgcolor="white",
    paper_bgcolor="white",
)
fig.update_xaxes(showgrid=True, gridcolor="#eeeeee")
fig.update_yaxes(showgrid=True, gridcolor="#eeeeee", ticksuffix="%")

st.plotly_chart(fig, use_container_width=True)
st.caption(
    "Green = daily portfolio NAV (mark-to-market using historical prices). "
    "Blue = realized return locked in at each trade close (step line). "
    "Orange = {} return since inception.".format(benchmark_label)
)

st.divider()

# ── Open Positions ─────────────────────────────────────────────────────────────
st.subheader(f"Open Positions ({len(open_pos_df)})")

if not open_pos_df.empty:
    display_open = open_pos_df[[
        "name", "opening_date", "qty", "trade_price",
        "notional_buy_after_comm", "current_price", "current_value",
        "unrealized_pnl", "unrealized_pnl_pct", "price_live",
    ]].copy()

    display_open.columns = [
        "Stock", "Opened", "Qty", "Buy Price",
        "Cost Basis", "Current Price", "Current Value",
        "Unrealized P&L", "Return %", "Live Price",
    ]
    display_open["Opened"] = display_open["Opened"].dt.strftime("%d %b %y")
    display_open["Buy Price"] = display_open["Buy Price"].apply(lambda x: f"₹{x:,.2f}")
    display_open["Cost Basis"] = display_open["Cost Basis"].apply(lambda x: f"₹{x:,.0f}")
    display_open["Current Price"] = display_open.apply(
        lambda r: f"₹{r['Current Price']:,.2f}" + ("" if r["Live Price"] else " *"), axis=1
    )
    display_open["Current Value"] = display_open["Current Value"].apply(lambda x: f"₹{x:,.0f}")
    display_open["Unrealized P&L"] = display_open["Unrealized P&L"].apply(lambda x: f"₹{x:+,.0f}")
    display_open["Return %"] = display_open["Return %"].apply(lambda x: f"{x:+.2f}%")
    display_open = display_open.drop(columns=["Live Price"])

    st.dataframe(display_open, use_container_width=True, hide_index=True)

    no_price = open_pos_df.loc[~open_pos_df["price_live"], "name"].tolist()
    if no_price:
        st.caption(
            f"\\* Live price unavailable for: {', '.join(no_price)}. "
            "Showing buy price as placeholder. Add NSE ticker to `config.py → TICKER_MAP`."
        )

    # ── Allocation pie charts ──────────────────────────────────────────────────
    st.subheader("Portfolio Allocation")
    pie_left, pie_right = st.columns(2)

    # Position-wise pie
    with pie_left:
        pos_labels = open_pos_df["name"].tolist()
        pos_values = open_pos_df["current_value"].tolist()
        fig_pos = go.Figure(go.Pie(
            labels=pos_labels,
            values=pos_values,
            hole=0.45,
            textinfo="label+percent",
            hovertemplate="<b>%{label}</b><br>₹%{value:,.0f} (%{percent})<extra></extra>",
        ))
        fig_pos.update_layout(
            title_text="By Position",
            height=360,
            margin=dict(l=0, r=0, t=40, b=0),
            showlegend=False,
        )
        st.plotly_chart(fig_pos, use_container_width=True)

    # Sector-wise pie
    with pie_right:
        sector_values: dict[str, float] = {}
        for _, row in open_pos_df.iterrows():
            ticker = TICKER_MAP.get(row["name"].strip(), "")
            sector = get_sector(ticker) if ticker else "Other"
            sector_values[sector] = sector_values.get(sector, 0.0) + float(row["current_value"])

        fig_sec = go.Figure(go.Pie(
            labels=list(sector_values.keys()),
            values=list(sector_values.values()),
            hole=0.45,
            textinfo="label+percent",
            hovertemplate="<b>%{label}</b><br>₹%{value:,.0f} (%{percent})<extra></extra>",
        ))
        fig_sec.update_layout(
            title_text="By Sector",
            height=360,
            margin=dict(l=0, r=0, t=40, b=0),
            showlegend=False,
        )
        st.plotly_chart(fig_sec, use_container_width=True)

else:
    st.info("No open positions.")

st.divider()

# ── Closed Trades + P&L Chart ─────────────────────────────────────────────────
left_col, right_col = st.columns([3, 2])

closed_trades = trades[trades["closing_date"].notna()].copy()

with left_col:
    st.subheader("Closed Trade P&L")
    if not closed_trades.empty:
        colors = closed_trades["profit_loss"].apply(lambda x: "#2ecc71" if x >= 0 else "#e74c3c")
        fig2 = go.Figure(go.Bar(
            x=closed_trades["name"],
            y=closed_trades["profit_loss"],
            marker_color=colors.tolist(),
            text=closed_trades["profit_loss"].apply(lambda x: f"₹{x:+,.0f}"),
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>P&L: ₹%{y:,.2f}<extra></extra>",
        ))
        fig2.add_hline(y=0, line_color="gray", line_width=1, opacity=0.5)
        fig2.update_layout(
            yaxis_title="P&L (₹)",
            height=310,
            margin=dict(l=0, r=0, t=20, b=0),
            plot_bgcolor="white",
            paper_bgcolor="white",
            showlegend=False,
        )
        fig2.update_xaxes(showgrid=False)
        fig2.update_yaxes(showgrid=True, gridcolor="#eeeeee")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No closed trades yet.")

with right_col:
    st.subheader("All Closed Trades")
    if not closed_trades.empty:
        ct = closed_trades[[
            "name", "opening_date", "closing_date",
            "qty", "trade_price", "closing_price",
            "profit_loss", "profit_loss_pct",
        ]].copy()
        ct.columns = ["Stock", "Opened", "Closed", "Qty", "Buy", "Sell", "P&L (₹)", "Return"]
        ct["Opened"] = ct["Opened"].dt.strftime("%d %b %y")
        ct["Closed"] = ct["Closed"].dt.strftime("%d %b %y")
        ct["Buy"] = ct["Buy"].apply(lambda x: f"₹{x:,.2f}")
        ct["Sell"] = ct["Sell"].apply(lambda x: f"₹{x:,.2f}")
        ct["P&L (₹)"] = ct["P&L (₹)"].apply(lambda x: f"₹{x:+,.0f}")
        ct["Return"] = ct["Return"].apply(lambda x: f"{x:+.2f}%")
        st.dataframe(ct, use_container_width=True, hide_index=True, height=320)

# ── Dividends ─────────────────────────────────────────────────────────────────
if not dividends.empty:
    st.divider()
    st.subheader("Dividend Income")
    div_display = dividends.copy()
    if "total_dividend" in div_display.columns:
        div_display["total_dividend"] = div_display["total_dividend"].apply(
            lambda x: f"₹{float(x):,.2f}" if pd.notna(x) else "-"
        )
    div_display.columns = [c.replace("_", " ").title() for c in div_display.columns]
    st.dataframe(div_display, use_container_width=True, hide_index=True)

# ── Footer ─────────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "Portfolio data: Google Sheets (refreshes every 5 min) · "
    "Live prices: Yahoo Finance (refreshes every 30 min) · "
    f"Benchmark: {benchmark_label} via Yahoo Finance"
)
