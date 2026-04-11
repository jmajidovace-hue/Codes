import yfinance as yf
import pandas as pd
import numpy as np
import warnings
import matplotlib
matplotlib.use('Agg') # Ensure no GUI popup
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import io
import base64

warnings.filterwarnings("ignore")

# Map of common tickers to their respective ETFs
INDUSTRY_ETF_MAP = {
    "Banks - Regional": "KRE",
    "Banks - Diversified": "KBE",
    "REIT - Mortgage": "REM",
    "REIT - Retail": "VNQ",
    "REIT - Office": "VNQ",
    "REIT - Healthcare Facilities": "VNQ",
    "REIT - Diversified": "VNQ",
    "Insurance - Property & Casualty": "KIE",
    "Insurance - Life": "KIE",
    "Insurance - Diversified": "KIE",
    "Insurance - Reinsurance": "KIE",
    "Insurance - Specialty": "KIE",
    "Asset Management": "XLF",
    "Capital Markets": "XLF",
    "Credit Services": "XLF",
    "Marine Shipping": "IYT",
    "Oil & Gas Midstream": "AMLP",
    "Telecom Services": "XLC",
    "Utilities - Regulated Electric": "XLU",
    "Utilities - Diversified": "XLU"
}

SECTOR_ETF_MAP = {
    "Financial Services": "XLF",
    "Real Estate": "VNQ",
    "Energy": "XLE",
    "Utilities": "XLU",
    "Industrials": "XLI",
    "Technology": "XLK",
    "Healthcare": "XLV",
    "Consumer Cyclical": "XLY",
    "Consumer Defensive": "XLP",
    "Basic Materials": "XLB",
    "Communication Services": "XLC"
}

def get_sector_info(user_ticker, info_dict):
    sector = info_dict.get('sector')
    industry = info_dict.get('industry')

    if not sector:
        base_ticker = user_ticker.split('-')[0].split('.')[0]
        try:
            base_info = yf.Ticker(base_ticker).info
            sector = base_info.get('sector', 'Unknown')
            industry = base_info.get('industry', 'Unknown')
        except:
            sector = 'Unknown'
            industry = 'Unknown'

    return sector, industry

def get_benchmark_ticker(sector, industry):
    if industry in INDUSTRY_ETF_MAP:
        return INDUSTRY_ETF_MAP[industry]
    elif sector in SECTOR_ETF_MAP:
        return SECTOR_ETF_MAP[sector]
    return "SPY"

import requests

def get_valid_ticker_data(user_ticker):
    # Use a session with a browser-like user agent to bypass rate limits
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
    })
    
    stock = yf.Ticker(user_ticker, session=session)
    hist = stock.history(period="1mo", auto_adjust=False)

    if not hist.empty:
        return stock, user_ticker, session

    if "-" in user_ticker:
        base, suffix = user_ticker.split("-", 1)
        alt_ticker = f"{base}-P{suffix}"
        stock_alt = yf.Ticker(alt_ticker, session=session)
        hist_alt = stock_alt.history(period="1mo", auto_adjust=False)
        if not hist_alt.empty:
            return stock_alt, alt_ticker, session

    return None, None, None

def get_upcoming_dividend(stock, dividends_hist):
    today = pd.Timestamp.now().normalize()
    if dividends_hist.index.tz is not None:
        today = today.tz_localize(dividends_hist.index.tz)

    next_date = None
    date_source = "Unknown"

    try:
        info = stock.info
        if 'exDividendDate' in info and info['exDividendDate'] is not None:
            ts = pd.to_datetime(info['exDividendDate'], unit='s')
            if ts.tz is None and today.tz is not None:
                ts = ts.tz_localize(today.tz)

            if ts.date() >= today.date():
                next_date = ts.date()
                date_source = "Confirmed by Yahoo Schedule"
    except Exception:
        pass

    if next_date is None and len(dividends_hist) >= 3:
        recent_dates = dividends_hist.index[-4:]
        diffs = np.diff(recent_dates).astype('timedelta64[D]').astype(int)
        avg_days = int(np.round(np.mean(diffs)))

        last_div_date = dividends_hist.index[-1]
        estimated_ts = last_div_date + pd.Timedelta(days=avg_days)

        while estimated_ts.date() < today.date():
            estimated_ts += pd.Timedelta(days=avg_days)

        next_date = estimated_ts.date()
        date_source = f"Estimated based on historical {avg_days}-day frequency"

    return next_date, date_source


def generate_plot_base64(ticker, stock_hist, vix_hist, dividends_hist, stats_dict):
    plot_hist = stock_hist.tail(252).copy()
    start_date = plot_hist.index[0]
    plot_vix = vix_hist.loc[start_date:].copy()
    plot_bench = stats_dict['benchmark_hist'].loc[start_date:].copy() if stats_dict.get('benchmark_hist') is not None else None
    historical_cycles = stats_dict.get('historical_cycles', [])

    tz_info = plot_hist.index.tz
    today = pd.Timestamp.now().tz_localize('UTC') if tz_info is None else pd.Timestamp.now().tz_localize(tz_info).tz_convert(tz_info)

    fig = plt.figure(figsize=(14, 10))
    gs = fig.add_gridspec(3, 1, height_ratios=[4, 1.2, 1.2])

    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1], sharex=ax1)
    ax3 = fig.add_subplot(gs[2], sharex=ax1)

    fig.suptitle(f"🎯 Precision Target Map: {ticker}", fontsize=18, fontweight='bold')

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
        ax1.axhline(y=recent_support, color='#7f7f7f', linestyle=':', linewidth=1.5, alpha=0.8, zorder=1, label=f'3M Recent Support (${recent_support:.2f})')

    added_hist_legend = False
    for cycle in historical_cycles:
        if cycle['ex_date'] >= start_date:
            ax1.axvline(x=cycle['ex_date'], color='grey', linestyle=':', alpha=0.5, zorder=1)
            if cycle['rally_start_date']:
                ax1.scatter(cycle['rally_start_date'], cycle['rally_start_price'], color='green', marker='^', s=80, zorder=5, label='Hist. Bottom (Full Move)' if not added_hist_legend else "")
            if cycle['sweet_dt'] and cycle['sweet_dt'] != cycle['rally_start_date']:
                ax1.scatter(cycle['sweet_dt'], cycle['sweet_px'], color='dodgerblue', marker='*', s=120, zorder=6, label='Hist. Momentum Entry' if not added_hist_legend else "")
            if cycle['div_entry_date']:
                ax1.scatter(cycle['div_entry_date'], cycle['div_entry_price'], color='orange', marker='^', s=80, zorder=5, label='Hist. Div Entry' if not added_hist_legend else "")
            if cycle['rally_start_date'] and cycle['pre_div_date']:
                ax1.plot([cycle['rally_start_date'], cycle['pre_div_date']], [cycle['rally_start_price'], cycle['pre_div_price']], color='blue', linestyle=':', alpha=0.6, linewidth=2, zorder=3)
            added_hist_legend = True

    future_end = today
    if stats_dict.get('next_ex_date'):
        ex_date_raw = pd.Timestamp(stats_dict['next_ex_date'])
        if tz_info is not None: ex_date_raw = ex_date_raw.tz_localize(tz_info)
        rally_target_raw = pd.Timestamp(stats_dict['target_rally_date'])
        if tz_info is not None: rally_target_raw = rally_target_raw.tz_localize(tz_info)
        sweet_target_raw = pd.Timestamp(stats_dict['target_sweet_date'])
        if tz_info is not None: sweet_target_raw = sweet_target_raw.tz_localize(tz_info)
        div_target_raw = pd.Timestamp(stats_dict['target_div_date'])
        if tz_info is not None: div_target_raw = div_target_raw.tz_localize(tz_info)

        future_end = ex_date_raw + pd.Timedelta(days=max(20, int(stats_dict['avg_recovery']) + 5))
        ax1.set_xlim(start_date, future_end)

        ax1.axvline(ex_date_raw, color='red', linestyle='--', linewidth=2, label='Upcoming Ex-Date', zorder=1)
        ax1.axvline(rally_target_raw, color='green', linestyle='-', linewidth=1.5, alpha=0.8, label='Target: Full Rally Bottom', zorder=1)
        ax1.axvline(sweet_target_raw, color='dodgerblue', linestyle='-', linewidth=2, alpha=0.9, label='Target: Momentum Entry (Big Move)', zorder=2)
        ax1.axvline(div_target_raw, color='orange', linestyle='-', linewidth=1.5, alpha=0.8, label='Target: Upcoming Div Dip', zorder=1)

        recovery_end = ex_date_raw + pd.Timedelta(days=stats_dict['avg_recovery'])
        ax1.axvspan(ex_date_raw, recovery_end, color='green', alpha=0.15, label=f'BE Recovery ({stats_dict["avg_recovery"]:.1f}d)')
    else:
        ax1.set_xlim(start_date, today)

    if stats_dict.get('target_limit_avg') and stats_dict.get('target_limit_min'):
        avg_limit = stats_dict['target_limit_avg']
        min_limit = stats_dict['target_limit_min']
        five_days_ago = plot_hist.index[-5] if len(plot_hist) >= 5 else plot_hist.index[0]
        ax1.plot([five_days_ago, future_end], [avg_limit, avg_limit], color='#e377c2', linestyle='-.', linewidth=2.5, zorder=6, label=f'Standard 5D Avg (${avg_limit:.2f})')
        ax1.plot([five_days_ago, future_end], [min_limit, min_limit], color='red', linestyle=':', linewidth=2.5, zorder=6, label=f'VIX-Adj Min (${min_limit:.2f})')

    ax1.set_title("Strategic Setup, Entry Limits & Support Levels", fontsize=12)
    ax1.set_ylabel("Price ($)", fontsize=11)
    ax1.grid(True, linestyle='--', alpha=0.5)
    ax1.legend(loc="upper left", framealpha=0.9, fontsize=9, ncol=2)
    plt.setp(ax1.get_xticklabels(), visible=False)

    if plot_bench is not None and not plot_bench.empty:
        ax2.plot(plot_bench.index, plot_bench['Close'], label=f'Benchmark ETF ({stats_dict["benchmark_ticker"]})', color='#17becf', linewidth=2)
        ax2.fill_between(plot_bench.index, plot_bench['Close'], plot_bench['Close'].min(), color='#17becf', alpha=0.1)
        ax2.set_title(f"Macro Trend: {stats_dict.get('industry', 'Unknown')} ({stats_dict.get('sector', 'Unknown')})", fontsize=12)
        ax2.set_ylabel("ETF Price", fontsize=11)
        ax2.legend(loc="upper left", fontsize=10)
    plt.setp(ax2.get_xticklabels(), visible=False)

    ax3.plot(plot_vix.index, plot_vix['Close'], label='VIX Level', color='#9467bd', linewidth=1.5)
    ax3.axhline(y=stats_dict['hist_avg_vix'], color='purple', linestyle='--', alpha=0.6, label='Hist Avg VIX')
    ax3.axhline(y=20, color='orange', linestyle=':', alpha=0.8, label='Elevated Risk (>20)')
    ax3.axhline(y=25, color='red', linestyle=':', alpha=0.8, label='High Risk (>25)')
    ax3.set_title("Market Environment (VIX Context)", fontsize=12)
    ax3.set_ylabel("VIX", fontsize=11)
    ax3.legend(loc="upper left", fontsize=10)

    prof_sign = "+" if stats_dict['avg_net_profit'] >= 0 else "-"
    stats_text = (
        f"📊 LIVE STATS\n"
        f"------------------------\n"
        f"Industry:    {stats_dict.get('industry', 'Unknown')[:15]}...\n"
        f"ETF Corr:    {stats_dict.get('correlation', 0.0):.2f}\n"
        f"Move Type:   {stats_dict.get('move_profile', 'N/A')}\n"
        f"Net Profit:  {prof_sign}${abs(stats_dict['avg_net_profit']):.2f}\n"
        f"BE Recovery: {stats_dict['avg_recovery']:.1f} Days\n"
        f"Drawdown:    -${stats_dict['avg_dip']:.2f}\n"
        f"5D Vol:      ${stats_dict['avg_volatility']:.2f}\n"
        f"Current VIX: {stats_dict['current_vix']:.1f}"
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
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    return image_base64

def analyze_dividend_recovery_chart(ticker_input):
    stock, valid_symbol, session = get_valid_ticker_data(ticker_input)
    if stock is None:
        return None

    # Using 2y instead of max to be faster and avoid rate limits
    hist = stock.history(period="2y", auto_adjust=False)
    dividends = stock.dividends

    sector, industry = get_sector_info(valid_symbol, stock.info)
    benchmark_ticker = get_benchmark_ticker(sector, industry)

    benchmark = yf.Ticker(benchmark_ticker, session=session)
    bench_hist = benchmark.history(period="2y", auto_adjust=False)

    vix = yf.Ticker("^VIX", session=session)
    vix_hist = vix.history(period="2y", auto_adjust=False)

    if dividends.empty:
        return None

    if hist.index.tz is None: hist.index = hist.index.tz_localize('UTC')
    else: hist.index = hist.index.tz_convert('UTC')

    if dividends.index.tz is None: dividends.index = dividends.index.tz_localize('UTC')
    else: dividends.index = dividends.index.tz_convert('UTC')

    if vix_hist.index.tz is None: vix_hist.index = vix_hist.index.tz_localize('UTC')
    else: vix_hist.index = vix_hist.index.tz_convert('UTC')

    if not bench_hist.empty:
        if bench_hist.index.tz is None: bench_hist.index = bench_hist.index.tz_localize('UTC')
        else: bench_hist.index = bench_hist.index.tz_convert('UTC')

    correlation = 0.0
    if not bench_hist.empty and not hist.empty:
        s_ret = hist['Close'].pct_change().dropna()
        b_ret = bench_hist['Close'].pct_change().dropna()
        aligned = pd.concat([s_ret, b_ret], axis=1, join='inner').tail(252)
        if not aligned.empty and len(aligned) > 10:
            correlation = aligned.iloc[:, 0].corr(aligned.iloc[:, 1])

    recovery_days_list = []
    net_profits = []
    run_up_days_list = []
    late_entry_days_list = []
    sweet_spot_days_list = []
    momentum_5d_list = []
    volatility_5d_list = []
    vix_levels_list = []
    drawdowns_5d_list = []
    momentum_spike_ratios = []
    historical_cycles = []

    recent_dividends = dividends.sort_index(ascending=False).head(10)

    for date, amount in recent_dividends.items():
        if date not in hist.index: continue
        ex_date_idx = hist.index.get_loc(date)
        if ex_date_idx == 0: continue

        pre_div_price = hist.iloc[ex_date_idx - 1]['Close']
        ex_day_open = hist.iloc[ex_date_idx]['Open']
        pre_div_date = hist.index[ex_date_idx - 1]
        
        try:
            vix_level = vix_hist.loc[pre_div_date]['Close']
        except KeyError:
            vix_level_idx = vix_hist.index.get_indexer([pre_div_date], method='nearest')[0]
            vix_level = vix_hist.iloc[vix_level_idx]['Close']

        vix_levels_list.append(vix_level)
        price_drop = pre_div_price - ex_day_open
        after_tax_dividend = amount * 0.90
        net_profits.append(after_tax_dividend - price_drop)

        lookback = 20
        start_idx = max(0, ex_date_idx - lookback)
        window_data = hist.iloc[start_idx : ex_date_idx]

        rally_start_dt, rally_start_px, sweet_dt, sweet_px, div_entry_dt, div_entry_px = None, None, None, None, None, None

        if not window_data.empty:
            min_price_date = window_data['Close'].idxmin()
            rally_start_dt = min_price_date
            rally_start_px = window_data['Close'].min()
            run_up_days_list.append((date - min_price_date).days)

            if len(window_data) > 1:
                daily_diffs = window_data['Close'].diff()
                spike_idx = window_data.index.get_loc(daily_diffs.idxmax())
                entry_idx = max(0, spike_idx - 1)
                sweet_dt = window_data.index[entry_idx]
                sweet_px = window_data['Close'].iloc[entry_idx]
            else:
                sweet_dt = min_price_date
                sweet_px = rally_start_px

            sweet_spot_days_list.append((date - sweet_dt).days)

            pre_div_dt = hist.index[ex_date_idx - 1]
            mom_window = hist.loc[sweet_dt:pre_div_dt]
            if len(mom_window) > 1:
                daily_diffs_osc = mom_window['Close'].diff().dropna()
                if not daily_diffs_osc.empty:
                    max_daily_pop = daily_diffs_osc.max()
                    window_range = mom_window['Close'].max() - mom_window['Close'].min()
                    if max_daily_pop > 0 and window_range > 0:
                        spike_ratio = min(max_daily_pop / window_range, 1.0)
                        momentum_spike_ratios.append(spike_ratio)

        lookback_5d = 5
        start_idx_5d = max(0, ex_date_idx - lookback_5d)
        window_data_5d = hist.iloc[start_idx_5d : ex_date_idx]
        if not window_data_5d.empty and len(window_data_5d) > 1:
            div_entry_dt = window_data_5d['Close'].idxmin()
            div_entry_px = window_data_5d['Close'].min()
            late_entry_days_list.append((date - div_entry_dt).days)
            
            price_5d_ago = window_data_5d['Close'].iloc[0]
            momentum_5d_list.append(pre_div_price - price_5d_ago)
            
            min_l = window_data_5d['Low'].min()
            volatility_5d_list.append(window_data_5d['High'].max() - min_l)
            
            dip_from_entry = price_5d_ago - min_l
            drawdowns_5d_list.append(dip_from_entry if dip_from_entry > 0 else 0.0)

        historical_cycles.append({
            'ex_date': date, 'pre_div_date': pre_div_date, 'pre_div_price': pre_div_price,
            'rally_start_date': rally_start_dt, 'rally_start_price': rally_start_px,
            'sweet_dt': sweet_dt, 'sweet_px': sweet_px, 'div_entry_date': div_entry_dt, 'div_entry_price': div_entry_px
        })

        future_data = hist.iloc[ex_date_idx:]
        breakeven_target = pre_div_price - after_tax_dividend
        for i in range(len(future_data)):
            if future_data.iloc[i]['Close'] >= breakeven_target:
                recovery_days_list.append(i)
                break

    valid_recoveries = [d for d in recovery_days_list if d != 999]
    avg_recovery = np.mean(valid_recoveries) if valid_recoveries else 999
    avg_net_profit = np.mean(net_profits) if net_profits else 0
    avg_entry_days = np.mean(run_up_days_list) if run_up_days_list else 0
    avg_sweet_days = np.mean(sweet_spot_days_list) if sweet_spot_days_list else 0
    avg_entry_days_5d = np.mean(late_entry_days_list) if late_entry_days_list else 0
    avg_momentum = np.mean(momentum_5d_list) if momentum_5d_list else 0
    avg_volatility = np.mean(volatility_5d_list) if volatility_5d_list else 0
    avg_dip = np.mean(drawdowns_5d_list) if drawdowns_5d_list else 0
    avg_vix = np.mean(vix_levels_list) if vix_levels_list else 15.0
    current_vix = vix_hist['Close'].iloc[-1]

    spike_pct = (np.mean(momentum_spike_ratios) if momentum_spike_ratios else 0) * 100
    if spike_pct == 0: move_profile = "N/A"
    elif spike_pct <= 40: move_profile = "Continuous 🌊"
    elif spike_pct <= 70: move_profile = "Stepped 📈"
    else: move_profile = "Spike ⚡"

    live_5d_data = hist.tail(5)
    current_price = hist['Close'].iloc[-1]
    live_5d_avg_low = live_5d_data['Low'].mean() if not live_5d_data.empty else current_price
    live_5d_min_low = live_5d_data['Low'].min() if not live_5d_data.empty else current_price

    next_ex_date, _ = get_upcoming_dividend(stock, dividends)
    today_date = pd.Timestamp.now().date()
    
    target_entry_date_20d, target_entry_date_sweet, target_entry_date_5d, rally_left = None, None, None, None
    if next_ex_date:
        target_entry_date_20d = next_ex_date - timedelta(days=int(avg_entry_days))
        target_entry_date_sweet = next_ex_date - timedelta(days=int(avg_sweet_days))
        target_entry_date_5d = next_ex_date - timedelta(days=int(avg_entry_days_5d))

    stats_dict = {
        'avg_net_profit': avg_net_profit, 'avg_recovery': avg_recovery, 'avg_momentum': avg_momentum,
        'avg_volatility': avg_volatility, 'avg_dip': avg_dip, 'current_vix': current_vix,
        'hist_avg_vix': avg_vix, 'next_ex_date': next_ex_date, 'target_rally_date': target_entry_date_20d,
        'target_sweet_date': target_entry_date_sweet, 'target_div_date': target_entry_date_5d,
        'rally_left': rally_left, 'target_limit_avg': live_5d_avg_low, 'target_limit_min': live_5d_min_low,
        'historical_cycles': historical_cycles, 'sector': sector, 'industry': industry,
        'benchmark_ticker': benchmark_ticker, 'benchmark_hist': bench_hist, 'correlation': correlation,
        'move_profile': move_profile
    }
    
    return generate_plot_base64(valid_symbol, hist, vix_hist, dividends, stats_dict)
