import pandas as pd
import os

_METRICS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    "data", "stock_metrics_new.csv",
)

_sector_map: dict[str, str] | None = None


def _load_sector_map() -> dict[str, str]:
    global _sector_map
    if _sector_map is not None:
        return _sector_map
    try:
        df = pd.read_csv(_METRICS_PATH, usecols=["Stock Name", "Sector"])
        _sector_map = df.dropna(subset=["Sector"]).set_index("Stock Name")["Sector"].to_dict()
    except Exception:
        _sector_map = {}
    return _sector_map


def get_sector(ticker_ns: str) -> str:
    """Return sector string for an NSE ticker like 'GMDCLTD.NS'. Falls back to 'Other'."""
    symbol = ticker_ns.replace(".NS", "").upper()
    return _load_sector_map().get(symbol, "Other")
