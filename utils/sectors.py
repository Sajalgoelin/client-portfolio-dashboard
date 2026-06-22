import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import SECTOR_MAP


def get_sector(ticker_ns: str) -> str:
    """Return sector for an NSE ticker like 'GMDCLTD.NS'. Falls back to 'Other'."""
    symbol = ticker_ns.replace(".NS", "").upper()
    return SECTOR_MAP.get(symbol, "Other")
