# FILE: backend/charts/div_finder.py
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
import base64
from datetime import timedelta

# Set Matplotlib to non-interactive mode for Vercel
import matplotlib
matplotlib.use('Agg')

SECTOR_ETF_MAP = {
    "Technology": "XLK",
    "Financial Services": "XLF",
    "Healthcare": "XLV",
    "Consumer Cyclical": "XLY",
    "Communication Services": "XLC",
    "Industrials": "XLI",
    "Consumer Defensive": "XLP",
    "Energy": "XLE",
    "Real Estate": "XLRE",
    "Utilities": "XLU",
    "Basic Materials": "XLB"
}

def get_valid_ticker_data(user_ticker):
    stock = yf.Ticker(user_ticker)
    hist = stock.history(period="1mo", auto_adjust=False)

    if not hist.empty:
        return stock, user_ticker

    if "-" in user_ticker:
        base, suffix = user_ticker.split("-", 1)
        alt_ticker = f"{base}-P{suffix}"
        stock_alt = yf.Ticker(alt_ticker)
        hist_alt = stock_alt.history(period="1mo", auto_adjust=False)
        if not hist_alt.empty:
            return stock_alt, alt_ticker

    return None, None

def get_upcoming_dividend(stock, dividends_hist):
    today = pd.Timestamp.now().normalize()
    future_divs = dividends_hist[dividends_hist.index >= today]
    if not future_divs.empty:
        return future_divs.index[0], future_divs.iloc[0]
    
    try:
        info = stock.info
        ex_date_timestamp = info.get('exDividendDate')
        if ex_date_timestamp:
            ex_date = pd.to_datetime(ex_date_timestamp, unit='s').normalize()
            if ex_date >= today:
                return ex_date, info.get('dividendRate', 0)
    except:
        pass
    return None, None

def get_sector_info(ticker, info):
    return info.get('sector'), info.get('industry')

def get_benchmark_ticker(sector, industry):
    if industry == "Closed-End Fund - Equity": return "SPY"
    if industry == "Closed-End Fund - Debt": return "AGG"
    if sector and sector in SECTOR_ETF_MAP:
        return SECTOR_ETF_MAP[sector]
    return "SPY"

def generate_target_map_base64(valid_symbol, hist, dividends, upcoming_date, upcoming_amount, bench_hist, vix_hist):
    if hist.empty: return None

    hist = hist.copy()
    if hist.index.tz is not None: hist.index = hist.index.tz_localize(None)
    if bench_hist.index.tz is not None: bench_hist.index = bench_hist.index.tz_localize(None)
    if vix_hist.index.tz is not None: vix_hist.index = vix_hist.index.tz_localize(None)

    # Recovery Logic
    div_dates = dividends.index.normalize()
    recovery_data = []

    for d_date in div_dates:
        if d_date not in hist.index: continue
        
        pre_date = d_date - timedelta(days=1)
        while pre_date not in hist.index and pre_date > hist.index[0]:
            pre_date -= timedelta(days=1)
        
        if pre_date not in hist.index: continue
        
        pre_price = hist.loc[pre_date, 'Close']
        post_hist = hist[hist.index >= d_date]
        
        recovered_dates = post_hist[post_hist['Close'] >= pre_price].index
        days_to_recover = (recovered_dates[0] - d_date).days if not recovered_dates.empty else None
        
        recovery_data.append({
            'Ex-Date': d_date,
            'Pre-Price': pre_price,
            'Recovered_In_Days': days_to_recover
        })

    recovery_df = pd.DataFrame(recovery_data)
    
    # Plotting
    fig, axes = plt.subplots(2, 1, figsize=(12, 10), gridspec_kw={'height_ratios': [2, 1]})
    plt.subplots_adjust(hspace=0.3)

    # Top: Price and Benchmark
    ax1 = axes[0]
    ax1.plot(hist.index, hist['Close'], label=f'{valid_symbol} Price', color='#00f2ff', linewidth=2)
    ax1.set_title(f"{valid_symbol} Dividend Recovery & Market Context", color='white', fontsize=14, pad=20)
    
    ax1_bench = ax1.twinx()
    ax1_bench.plot(bench_hist.index, bench_hist['Close'], color='gray', alpha=0.3, label='Benchmark')
    
    # Bottom: VIX Context
    ax2 = axes[1]
    ax2.fill_between(vix_hist.index, vix_hist['Close'], color='red', alpha=0.2, label='VIX Index')
    ax2.set_ylabel('VIX', color='red')

    # Styling for Glassmorphism
    for ax in [ax1, ax2]:
        ax.set_facecolor('#0b0e14')
        ax.tick_params(colors='white')
        ax.xaxis.label.set_color('white')
        ax.yaxis.label.set_color('white')

    fig.patch.set_facecolor('#0b0e14')
    
    # Convert to Base64
    buf = io.BytesIO()
    plt.savefig(buf, format='png', facecolor='#0b0e14')
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return image_base64

def analyze_dividend_recovery_chart(ticker_input):
    stock, valid_symbol = get_valid_ticker_data(ticker_input)
    if stock is None:
        return None

    # Using 2y instead of max to be faster and avoid rate limits
    hist = stock.history(period="2y", auto_adjust=False)
    dividends = stock.dividends

    sector, industry = get_sector_info(valid_symbol, stock.info)
    benchmark_ticker = get_benchmark_ticker(sector, industry)

    benchmark = yf.Ticker(benchmark_ticker)
    bench_hist = benchmark.history(period="2y", auto_adjust=False)

    vix = yf.Ticker("^VIX")
    vix_hist = vix.history(period="2y", auto_adjust=False)

    if dividends.empty:
        return None

    upcoming_date, upcoming_amount = get_upcoming_dividend(stock, dividends)
    
    return generate_target_map_base64(
        valid_symbol, hist, dividends, 
        upcoming_date, upcoming_amount, 
        bench_hist, vix_hist
    )
