import yfinance as yf
import pandas as pd
import numpy as np
import warnings
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pandas.tseries.offsets import BMonthEnd
from datetime import datetime
import io
import base64
from curl_cffi import requests
from backend.utils.cache_helper import get_cached_macro_data

# yf_session = requests.Session(impersonate="chrome110") # Disabling manual session as per YF error

warnings.filterwarnings("ignore")

INDUSTRY_ETF_MAP = {
    "Banks - Regional": "KRE", "Banks - Diversified": "KBE", "REIT - Mortgage": "REM",
    "REIT - Retail": "VNQ", "REIT - Office": "VNQ", "REIT - Healthcare Facilities": "VNQ",
    "REIT - Diversified": "VNQ", "Insurance - Property & Casualty": "KIE", "Insurance - Life": "KIE",
    "Insurance - Diversified": "KIE", "Insurance - Reinsurance": "KIE", "Insurance - Specialty": "KIE",
    "Asset Management": "XLF", "Capital Markets": "XLF", "Credit Services": "XLF",
    "Marine Shipping": "IYT", "Oil & Gas Midstream": "AMLP", "Telecom Services": "XLC",
    "Utilities - Regulated Electric": "XLU", "Utilities - Diversified": "XLU"
}
SECTOR_ETF_MAP = {
    "Financial Services": "XLF", "Real Estate": "VNQ", "Energy": "XLE", "Utilities": "XLU",
    "Industrials": "XLI", "Technology": "XLK", "Healthcare": "XLV", "Consumer Cyclical": "XLY",
    "Consumer Defensive": "XLP", "Basic Materials": "XLB", "Communication Services": "XLC"
}

def get_sector_info(user_ticker, info_dict):
    sector = info_dict.get('sector')
    industry = info_dict.get('industry')
    if not sector:
        try:
            base_ticker = user_ticker.split('-')[0].split('.')[0]
            base_info = yf.Ticker(base_ticker).info
            sector = base_info.get('sector', 'Unknown')
            industry = base_info.get('industry', 'Unknown')
        except:
            sector, industry = 'Unknown', 'Unknown'
    return sector, industry

def get_benchmark_ticker(sector, industry):
    if industry in INDUSTRY_ETF_MAP: return INDUSTRY_ETF_MAP[industry]
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
    start_date = plot_hist.index[0]
    plot_vix = vix_hist.loc[start_date:].copy()
    historical_cycles = stats_dict.get('historical_cycles', [])

    today = pd.Timestamp.now()

    fig = plt.figure(figsize=(14, 10))
    gs = fig.add_gridspec(3, 1, height_ratios=[4, 1.2, 1.2])
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1], sharex=ax1)
    ax3 = fig.add_subplot(gs[2], sharex=ax1)

    fig.suptitle(f"EOM Rebalancing Map: {ticker}", fontsize=18, fontweight='bold')

    up = plot_hist[plot_hist.Close >= plot_hist.Open]
    down = plot_hist[plot_hist.Close < plot_hist.Open]
    ax1.vlines(up.index, up.Low, up.High, color='black', linewidth=0.8, zorder=2)
    ax1.vlines(down.index, down.Low, down.High, color='black', linewidth=0.8, zorder=2)
    ax1.bar(up.index, up.Close - up.Open, width=0.9, bottom=up.Open, color='green', edgecolor='black', linewidth=0.5, zorder=3)
    ax1.bar(down.index, down.Open - down.Close, width=0.9, bottom=down.Close, color='red', edgecolor='black', linewidth=0.5, zorder=3)

    major_support = plot_hist['Low'].min()
    recent_support = plot_hist['Low'].tail(60).min()
    ax1.axhline(y=major_support, color='#8c564b', linestyle='--', linewidth=1.5, alpha=0.7, zorder=1, label=f'1Y Major Support (${major_support:.2f})')
    if (recent_support - major_support) / major_support > 0.015:
        ax1.axhline(y=recent_support, color='#7f7f7f', linestyle=':', linewidth=1.5, alpha=0.8, zorder=1, label=f'3M Support (${recent_support:.2f})')

    added_legend = False
    for cycle in historical_cycles:
        cy_date = pd.to_datetime(cycle['eom_date'])
        if cy_date >= start_date:
            ax1.axvline(x=cy_date, color='grey', linestyle=':', alpha=0.4, zorder=1, label='Hist. EOM Day' if not added_legend else "")
            if cycle['eom_move'] <= -0.125:
                ax1.scatter(cy_date, cycle['eom_price'], color='red', marker='v', s=80, zorder=5, label='EOM Dump' if not added_legend else "")
            elif cycle['pre_move'] <= -0.125:
                ax1.scatter(cy_date - pd.Timedelta(days=3), cycle['pre_price'], color='darkred', marker='v', s=60, alpha=0.6, zorder=5, label='Pre-EOM Dump' if not added_legend else "")
            if cycle['eom_move'] >= 0.125:
                ax1.scatter(cy_date, cycle['eom_price'], color='green', marker='^', s=80, zorder=5, label='EOM Spike' if not added_legend else "")
            added_legend = True

    future_end = today
    if stats_dict.get('next_eom_date'):
        next_eom_raw = pd.Timestamp(stats_dict['next_eom_date'])
        future_end = next_eom_raw + pd.Timedelta(days=15)
        ax1.set_xlim(start_date, future_end)
        ax1.axvline(next_eom_raw, color='purple', linestyle='--', linewidth=2, label='Upcoming EOM Rebalance', zorder=1)
        ax1.axvspan(next_eom_raw - pd.Timedelta(days=4), next_eom_raw, color='purple', alpha=0.1, label='Pre-EOM 3-Day Window')

    ax1.set_title("Rebalancing Footprints & Support Levels", fontsize=12)
    ax1.set_ylabel("Price ($)", fontsize=11)
    ax1.grid(True, linestyle='--', alpha=0.5)
    ax1.legend(loc="upper left", framealpha=0.9, fontsize=9, ncol=3)
    plt.setp(ax1.get_xticklabels(), visible=False)

    ax3.plot(plot_vix.index, plot_vix['Close'], label='VIX Level', color='#9467bd', linewidth=1.5)
    ax3.axhline(y=stats_dict['hist_avg_vix'], color='purple', linestyle='--', alpha=0.6, label='Hist Avg VIX')
    ax3.axhline(y=20, color='orange', linestyle=':', alpha=0.8, label='Elevated Risk (>20)')
    ax3.set_title("Market Environment (VIX Context)", fontsize=12)
    ax3.set_ylabel("VIX", fontsize=11)
    ax3.grid(True, linestyle='--', alpha=0.5)
    ax3.legend(loc="upper left", fontsize=10)

    stats_text = (
        f"REBALANCING PROFILE\n"
        f"------------------------\n"
        f"Primary Action: {stats_dict.get('move_profile', 'Unknown')}\n"
        f"Avg EOM Move:   {stats_dict.get('avg_eom_move', 0.0):+.2f}\n"
        f"Avg Base Vol:   {stats_dict.get('avg_base_vol', 0):,.0f}\n"
        f"Avg EOM Vol:    {stats_dict.get('avg_eom_vol', 0):,.0f}\n"
        f"Avg Post Vol:   {stats_dict.get('avg_post_vol', 0):,.0f}\n"
        f"Rec. Speed:     {stats_dict.get('avg_recovery', 0.0):.1f} Days\n"
        f"Current VIX:    {stats_dict.get('current_vix', 0.0):.1f}"
    )
    props = dict(boxstyle='round', facecolor='#f8f9fa', alpha=0.9, edgecolor='gray')
    ax1.text(0.02, 0.05, stats_text, transform=ax1.transAxes, fontsize=11, verticalalignment='bottom', bbox=props, fontfamily='monospace', zorder=10)

    ax3.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    plt.xticks(rotation=45)
    plt.tight_layout(pad=1.0)
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    plt.close('all')
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')

def analyze_rebalancing_chart(ticker_input):
    stock, valid_symbol = get_valid_ticker_data(ticker_input)
    if stock is None: return None

    hist = stock.history(period="2y", auto_adjust=False)
    sector, industry = get_sector_info(valid_symbol, stock.info)
    benchmark_ticker = get_benchmark_ticker(sector, industry)

    vix_hist = get_cached_macro_data("^VIX")
    # Also reuse sector data if possible? No, sector info is already fetched.

    if hist.index.tz is not None: hist.index = hist.index.tz_localize(None)
    # vix_hist coming from the cache is already tz-handled

    hist['YearMonth'] = hist.index.to_period('M')
    eom_dates = hist.groupby('YearMonth').apply(lambda x: x.index[-1]).values

    move_threshold = 0.125
    historical_cycles = []
    dumps, spikes = 0, 0
    total_eom_moves, total_recoveries, total_base_vols, total_eom_vols, total_post_vols, vix_levels = [], [], [], [], [], []

    recent_eoms = eom_dates[-13:]
    for eom in recent_eoms:
        try:
            loc_raw = hist.index.get_loc(eom)
            if isinstance(loc_raw, slice): loc = loc_raw.stop - 1
            elif isinstance(loc_raw, np.ndarray): loc = np.where(loc_raw)[0][-1]
            else: loc = loc_raw

            if loc < 4 or loc >= len(hist): continue

            t4_price = hist['Close'].iloc[loc-4]
            t1_price = hist['Close'].iloc[loc-1]
            eom_price = hist['Close'].iloc[loc]

            prior_move_dlr = t1_price - t4_price
            eom_move_dlr = eom_price - t1_price
            total_eom_moves.append(eom_move_dlr)

            vol_start, vol_end = max(0, loc-23), max(0, loc-3)
            vol_base = hist['Volume'].iloc[vol_start:vol_end].mean() if vol_start < vol_end else 0.0
            vol_eom = hist['Volume'].iloc[loc]

            vol_post_start, vol_post_end = loc + 1, loc + 4
            if vol_post_start < len(hist): 
                vol_post = hist['Volume'].iloc[vol_post_start:min(vol_post_end, len(hist))].mean()
            else: 
                vol_post = float('nan')

            if not pd.isna(vol_base) and vol_base > 0:
                total_base_vols.append(vol_base)
                total_eom_vols.append(vol_eom)
                if not pd.isna(vol_post) and vol_post > 0:
                    total_post_vols.append(vol_post)

            try:
                date_val = hist.index[loc]
                if date_val in vix_hist.index:
                    v_res = vix_hist.loc[date_val]['Close']
                    vix_levels.append(v_res.iloc[0] if isinstance(v_res, pd.Series) else v_res)
                else:
                    vix_idx = vix_hist.index.get_indexer([date_val], method='nearest')[0]
                    if vix_idx >= 0: vix_levels.append(vix_hist.iloc[vix_idx]['Close'])
            except Exception: pass

            rec_days = "..."
            if eom_move_dlr <= -move_threshold:
                dumps += 1
                rec_days = ">14d"
                for d in range(1, 15):
                    if loc + d < len(hist) and hist['Close'].iloc[loc + d] >= t1_price:
                        total_recoveries.append(d)
                        rec_days = f"{d}d"
                        break
            elif eom_move_dlr >= move_threshold:
                spikes += 1
                rec_days = ">14d"
                for d in range(1, 15):
                    if loc + d < len(hist) and hist['Close'].iloc[loc + d] <= t1_price:
                        total_recoveries.append(d)
                        rec_days = f"{d}d"
                        break

            historical_cycles.append({
                'eom_date': hist.index[loc],
                'pre_price': t4_price,
                'eom_price': eom_price,
                'pre_move': prior_move_dlr,
                'eom_move': eom_move_dlr,
                'vol_base': vol_base,
                'vol_eom': vol_eom,
                'vol_post': vol_post if not pd.isna(vol_post) else None,
                'recovery': rec_days
            })
        except Exception: 
            continue

    today = pd.Timestamp.now()
    next_eom = today + BMonthEnd(0)
    if next_eom.date() < today.date(): next_eom = today + BMonthEnd(1)

    avg_eom_move = np.nanmean(total_eom_moves) if total_eom_moves else 0
    avg_base = np.nanmean(total_base_vols) if total_base_vols else 0
    avg_eom_vol = np.nanmean(total_eom_vols) if total_eom_vols else 0
    avg_post_vol = np.nanmean(total_post_vols) if total_post_vols else 0
    avg_rec = np.nanmean(total_recoveries) if total_recoveries else 0.0
    avg_vix = np.nanmean(vix_levels) if vix_levels else 15.0
    current_vix = vix_hist['Close'].iloc[-1]

    if dumps > spikes and dumps >= 3: profile = "Predominantly DUMPED at EOM"
    elif spikes > dumps and spikes >= 3: profile = "Predominantly ACCUMULATED at EOM"
    elif dumps > 0 or spikes > 0: profile = "Mixed / Unpredictable"
    else: profile = "No Significant Action"

    stats_dict = {
        'industry': industry, 'sector': sector, 'benchmark_ticker': benchmark_ticker,
        'move_profile': profile, 'avg_eom_move': avg_eom_move,
        'avg_base_vol': avg_base if avg_base > 0 else float('nan'),
        'avg_eom_vol': avg_eom_vol if avg_base > 0 else float('nan'),
        'avg_post_vol': avg_post_vol if avg_base > 0 else float('nan'),
        'avg_recovery': avg_rec, 'current_vix': current_vix, 'hist_avg_vix': avg_vix,
        'next_eom_date': str(next_eom.date()), 'historical_cycles': historical_cycles,
        'days_away': (next_eom.date() - today.date()).days
    }
    
    for cycle in stats_dict['historical_cycles']:
        for k, v in cycle.items():
            if isinstance(v, (pd.Timestamp, datetime)):
                cycle[k] = str(v.date())
            elif isinstance(v, float) and pd.isna(v):
                cycle[k] = None

    image_b64 = generate_rebalancing_plot_base64(valid_symbol, hist, vix_hist, stats_dict)
    
    return {
        "image": image_b64,
        "stats": stats_dict
    }
