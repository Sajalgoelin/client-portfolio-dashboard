INITIAL_CAPITAL = 400_000  # Client's starting capital in INR

# Map sheet stock names → NSE tickers for yfinance live price fetch.
# Add new entries here as you add stocks to the sheet.
TICKER_MAP = {
    "ASIAN PAINTS":      "ASIANPAINT.NS",
    "DEN":               "DEN.NS",
    "IDFC FIRST BANK":   "IDFCFIRSTB.NS",
    "INDIAN  OIL CORP":  "IOC.NS",
    "INDIAN OIL CORP":   "IOC.NS",
    "JIO FIN":           "JIOFIN.NS",
    "TATA CONSUMER":     "TATACONSUM.NS",
    "VOLTAS":            "VOLTAS.NS",
    "HAL":               "HAL.NS",
    "TVS MOTORS":        "TVSMOTOR.NS",
    "TVS MOTOR":         "TVSMOTOR.NS",
    "SAMMAN CO":         "SAMMAANCAP.NS",
    "SAMMAN CAPITAL":    "SAMMAANCAP.NS",
    "CUMMINSIND":        "CUMMINSIND.NS",
    "TATA CHEMICALS":    "TATACHEM.NS",
    "GMDC":              "GMDCLTD.NS",
    "GMDCLTD":           "GMDCLTD.NS",
    "ABCAPITAL":         "ABCAPITAL.NS",
}
