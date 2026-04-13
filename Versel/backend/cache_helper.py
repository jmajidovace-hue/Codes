import time
import pandas as pd
import yfinance as yf

# Global cache dictionary: { "ticker": (timestamp, DataFrame) }
_MACRO_CACHE = {}
CACHE_EXPIRY_SECONDS = 3600 # 1 hour

def get_cached_macro_data(ticker, period="2y"):
    """
    Fetches macro data (VIX, Benchmark ETFs) with a 1-hour in-memory cache.
    Helps avoid 429 rate limit errors on Vercel.
    """
    now = time.time()
    
    if ticker in _MACRO_CACHE:
        timestamp, df = _MACRO_CACHE[ticker]
        if now - timestamp < CACHE_EXPIRY_SECONDS:
            return df

    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period, auto_adjust=False)
        
        if df.empty:
            return pd.DataFrame()

        if df.index.tz is None:
            df.index = df.index.tz_localize('UTC')
        else:
            df.index = df.index.tz_convert('UTC')

        _MACRO_CACHE[ticker] = (now, df)
        return df
    except Exception as e:
        print(f"Error fetching macro data for {ticker}: {e}")
        # Return empty df on failure to avoid crashing, but don't cache it
        return pd.DataFrame()

def clear_macro_cache():
    global _MACRO_CACHE
    _MACRO_CACHE = {}
