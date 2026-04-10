# FILE: backend/charts/rebalance_mapper.py
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
import base64
from datetime import timedelta

# Set Matplotlib to non-interactive mode
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

def get_sector_info(ticker, info):
    return info.get('sector'), info.get('industry')

def get_benchmark_ticker(sector, industry):
    if industry == "Closed-End Fund - Equity": return "SPY"
    if industry == "Closed-End Fund - Debt": return "AGG"
    elif sector in SECTOR_ETF_MAP: return SECTOR_ETF_MAP[sector]
    return "SPY"

def get_valid_ticker_data(user_ticker):
    stock = yf.Ticker(user_ticker)
    hist = stock.history(period="1mo", auto_adjust=False)
    if not hist.empty: return stock, user_ticker
    if "-" in user_ticker:
        base, suffix = user_ticker.split("-", 1)
        alt_ticker = f"{base}-P{suffix}"
        stock_alt = yf.Ticker(alt_ticker)
        hist_alt = stock_alt.history(period="1mo", auto_adjust=False)
        if not hist_alt.empty: return stock_alt, alt_ticker
    return None, None

def generate_rebalancing_plot_base64(ticker, stock_hist, vix_hist, stats_dict):
    plot_hist = stock_hist.tail(252).copy()
    
    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax1.plot(plot_hist.index, plot_hist['Close'], label=f'{ticker} Price', color='#00f2ff', linewidth=2)
    ax1.set_title(f"{ticker} EOM Behavior Map", color='white', fontsize=14)
    
    ax2 = ax1.twinx()
    ax2.fill_between(vix_hist.index, vix_hist['Close'], color='red', alpha=0.1, label='VIX Context')
    
    # Mark EOMs
    eom_dates = plot_hist[plot_hist.index.is_month_end].index
    for d in eom_dates:
        ax1.axvline(d, color='white', linestyle='--', alpha=0.3)

    # Style
    ax1.set_facecolor('#0b0e14')
    fig.patch.set_facecolor('#0b0e14')
    ax1.tick_params(colors='white')
    ax2.tick_params(colors='white')

    buf = io.BytesIO()
    plt.savefig(buf, format='png', facecolor='#0b0e14')
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return image_base64

def analyze_rebalancing_chart(ticker_input):
    stock, valid_symbol = get_valid_ticker_data(ticker_input)
    if stock is None: return None

    # Using 2y instead of 3y to reduce data load and avoid bans
    hist = stock.history(period="2y", auto_adjust=False)
    sector, industry = get_sector_info(valid_symbol, stock.info)
    benchmark_ticker = get_benchmark_ticker(sector, industry)

    benchmark = yf.Ticker(benchmark_ticker)
    bench_hist = benchmark.history(period="2y", auto_adjust=False)

    vix = yf.Ticker("^VIX")
    vix_hist = vix.history(period="2y", auto_adjust=False)

    if hist.index.tz is not None: hist.index = hist.index.tz_localize(None)
    if vix_hist.index.tz is not None: vix_hist.index = vix_hist.index.tz_localize(None)

    return generate_rebalancing_plot_base64(valid_symbol, hist, vix_hist, {})
