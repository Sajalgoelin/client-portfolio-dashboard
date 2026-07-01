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
    "BHEL":              "BHEL.NS",
}

# Map NSE ticker → sector (used for allocation pie chart).
# Keyed by ticker without .NS suffix, upper-case.
SECTOR_MAP = {
    "ASIANPAINT":   "Basic Materials",
    "DEN":          "Communication Services",
    "IDFCFIRSTB":   "Financial Services",
    "IOC":          "Energy",
    "JIOFIN":       "Financial Services",
    "TATACONSUM":   "Consumer Defensive",
    "VOLTAS":       "Consumer Cyclical",
    "HAL":          "Industrials",
    "TVSMOTOR":     "Consumer Cyclical",
    "SAMMAANCAP":   "Financial Services",
    "CUMMINSIND":   "Industrials",
    "TATACHEM":     "Basic Materials",
    "GMDCLTD":      "Energy",
    "ABCAPITAL":    "Financial Services",
    "BHEL":         "Industrials",
}
