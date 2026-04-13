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

def generate_plot_base64(ticker, stock_hist, vix_hist, dividends, stats_dict):
    plot_hist = stock_hist.tail(252).copy()
    start_date = plot_hist.index[0]
    plot_vix = vix_hist.loc[start_date:].copy()
    plot_divs = dividends[dividends.index >= start_date].copy()
    
    historical_cycles = stats_dict.get('historical_cycles', [])

    fig = plt.figure(figsize=(14, 10))
    gs = fig.add_gridspec(3, 1, height_ratios=[4, 1.2, 1.2])
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1], sharex=ax1)
    ax3 = fig.add_subplot(gs[2], sharex=ax1)

    fig.suptitle(f"Dividend Performance Analysis: {ticker}", fontsize=18, fontweight='bold')

    # Main Chart (Price)
    up = plot_hist[plot_hist.Close >= plot_hist.Open]
    down = plot_hist[plot_hist.Close < plot_hist.Open]
    ax1.vlines(up.index, up.Low, up.High, color='black', linewidth=0.8, zorder=2)
    ax1.vlines(down.index, down.Low, down.High, color='black', linewidth=0.8, zorder=2)
    ax1.bar(up.index, up.Close - up.Open, width=0.9, bottom=up.Open, color='green', edgecolor='black', linewidth=0.5, zorder=3)
    ax1.bar(down.index, down.Open - down.Close, width=0.9, bottom=down.Close, color='red', edgecolor='black', linewidth=0.5, zorder=3)

    # Recovery markers
    for cycle in historical_cycles:
        ex_dt = pd.to_datetime(cycle['ex_date'])
        if ex_dt in plot_hist.index:
            ax1.axvline(x=ex_dt, color='blue', linestyle='--', alpha=0.3, zorder=1)
            ax1.scatter(ex_dt, cycle['ex_day_open'], color='blue', marker='v', s=40, zorder=5)

    ax1.set_title("Price Action & Dividend Ex-Dates", fontsize=12)
    ax1.set_ylabel("Price ($)", fontsize=11)
    ax1.grid(True, linestyle='--', alpha=0.5)

    # VIX Chart
    ax3.plot(plot_vix.index, plot_vix['Close'], label='VIX Level', color='#9467bd', linewidth=1.5)
    ax3.axhline(y=stats_dict['hist_avg_vix'], color='purple', linestyle='--', alpha=0.6, label='Hist Avg VIX')
    ax3.axhline(y=20, color='orange', linestyle=':', alpha=0.8, label='Risk Threshold (20)')
    ax3.set_title("Market Volatility (VIX)", fontsize=12)
    ax3.set_ylabel("VIX", fontsize=11)
    ax3.grid(True, linestyle='--', alpha=0.5)
    ax3.legend(loc="upper left", fontsize=10)

    # Stats Text
    avg_net_profit = stats_dict['avg_net_profit']
    avg_recovery_be = stats_dict['avg_recovery']
    # We'll just use a subset for the box
    stats_text = (
        f"DIVIDEND STRATEGY INSIGHTS\n"
        f"------------------------\n"
        f"Avg Net P/L:    +${avg_net_profit:.2f}\n"
        f"BE Recovery:     {avg_recovery_be:.1f} Days\n"
        f"Limit Entry:     ${stats_dict['target_limit_avg']:.2f}\n"
        f"VIX-Adj Limit:   ${stats_dict['target_limit_min']:.2f}"
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

def analyze_dividend_recovery_chart(ticker_input):
    stock, valid_symbol = get_valid_ticker_data(ticker_input)
    if stock is None:
        return None

    # Using 2y instead of max to be faster and avoid rate limits
    hist = stock.history(period="2y", auto_adjust=False)
    dividends = stock.dividends

    if dividends.empty:
        return None

    if hist.index.tz is None: hist.index = hist.index.tz_localize('UTC')
    else: hist.index = hist.index.tz_convert('UTC')

    if dividends.index.tz is None: dividends.index = dividends.index.tz_localize('UTC')
    else: dividends.index = dividends.index.tz_convert('UTC')

    # Get Macro Data
    info = stock.info
    sector, industry = get_sector_info(valid_symbol, info)
    benchmark_ticker = get_benchmark_ticker(sector, industry)

    benchmark = yf.Ticker(benchmark_ticker)
    bench_hist = benchmark.history(period="2y", auto_adjust=False)
    if not bench_hist.empty:
        if bench_hist.index.tz is None: bench_hist.index = bench_hist.index.tz_localize('UTC')
        else: bench_hist.index = bench_hist.index.tz_convert('UTC')

    vix = yf.Ticker("^VIX")
    vix_hist = vix.history(period="2y", auto_adjust=False)
    if vix_hist.index.tz is None: vix_hist.index = vix_hist.index.tz_localize('UTC')
    else: vix_hist.index = vix_hist.index.tz_convert('UTC')

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
        ex_day_high = hist.iloc[ex_date_idx]['High']
        pre_div_date = hist.index[ex_date_idx - 1]
        
        try:
            vix_level = vix_hist.loc[pre_div_date]['Close']
        except KeyError:
            vix_level_idx = vix_hist.index.get_indexer([pre_div_date], method='nearest')[0]
            vix_level = vix_hist.iloc[vix_level_idx]['Close']

        vix_levels_list.append(vix_level)
        price_drop = pre_div_price - ex_day_open
        after_tax_dividend = amount * 0.90
        net_profit = after_tax_dividend - price_drop
        net_profits.append(net_profit)

        lookback = 20
        start_idx = max(0, ex_date_idx - lookback)
        window_data = hist.iloc[start_idx : ex_date_idx]

        rally_start_dt, rally_start_px, sweet_dt, sweet_px, div_entry_dt, div_entry_px = None, None, None, None, None, None

        if not window_data.empty:
            min_price_date = window_data['Close'].idxmin()
            rally_start_dt = min_price_date
            rally_start_px = window_data['Close'].min()
            days_before = (date - min_price_date).days
            run_up_days_list.append(days_before)

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
            days_before_5d = (date - div_entry_dt).days
            late_entry_days_list.append(days_before_5d)
            
            price_5d_ago = window_data_5d['Close'].iloc[0]
            momentum_dlr = pre_div_price - price_5d_ago
            momentum_5d_list.append(momentum_dlr)
            
            min_l = window_data_5d['Low'].min()
            volatility_5d_list.append(window_data_5d['High'].max() - min_l)
            
            dip_from_entry = price_5d_ago - min_l
            drawdowns_5d_list.append(dip_from_entry if dip_from_entry > 0 else 0.0)
        else:
            days_before_5d = "N/A"
            momentum_dlr = 0.0

        if 'days_before' not in locals():
            days_before = "N/A"

        days_to_recover_be = 999
        days_to_recover_full = 999
        future_data = hist.iloc[ex_date_idx:]
        breakeven_target = pre_div_price - after_tax_dividend
        
        recovered_be = False
        recovered_full = False
        
        for i in range(len(future_data)):
            current_close = future_data.iloc[i]['Close']
            
            if not recovered_be and current_close >= breakeven_target:
                days_to_recover_be = i
                recovery_days_list.append(i)
                recovered_be = True
                
            if not recovered_full and current_close >= pre_div_price:
                days_to_recover_full = i
                recovered_full = True
                
            if recovered_be and recovered_full:
                break

        # Append to cycles
        historical_cycles.append({
            'ex_date': date,
            'pre_div_date': pre_div_date,
            'pre_div_price': pre_div_price,
            'ex_day_open': ex_day_open,
            'ex_day_high': ex_day_high,
            'div_amount': amount,
            'net_profit': net_profit,
            'vix_level': vix_level,
            'five_d_trend': momentum_dlr,
            'rally_ent_days': days_before,
            'div_ent_days': days_before_5d,
            'be_recovery': days_to_recover_be,
            'full_recovery': days_to_recover_full,
            'rally_start_date': rally_start_dt,
            'rally_start_price': rally_start_px,
            'sweet_dt': sweet_dt,
            'sweet_px': sweet_px,
            'div_entry_date': div_entry_dt,
            'div_entry_price': div_entry_px
        })

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
    elif spike_pct <= 40: move_profile = "Continuous"
    elif spike_pct <= 70: move_profile = "Stepped"
    else: move_profile = "Spike"

    live_5d_data = hist.tail(5)
    current_price = hist['Close'].iloc[-1]
    live_5d_avg_low = live_5d_data['Low'].mean() if not live_5d_data.empty else current_price
    live_5d_min_low = live_5d_data['Low'].min() if not live_5d_data.empty else current_price

    next_ex_date, _ = get_upcoming_dividend(stock, dividends)
    
    target_entry_date_20d, target_entry_date_sweet, target_entry_date_5d = None, None, None
    if next_ex_date:
        target_entry_date_20d = next_ex_date - timedelta(days=int(avg_entry_days))
        target_entry_date_sweet = next_ex_date - timedelta(days=int(avg_sweet_days))
        target_entry_date_5d = next_ex_date - timedelta(days=int(avg_entry_days_5d))

    stats_dict = {
        'avg_net_profit': avg_net_profit, 'avg_recovery': avg_recovery, 'avg_momentum': avg_momentum,
        'avg_volatility': avg_volatility, 'avg_dip': avg_dip, 'current_vix': current_vix,
        'hist_avg_vix': avg_vix, 'next_ex_date': str(next_ex_date) if next_ex_date else None,
        'target_rally_date': str(target_entry_date_20d) if target_entry_date_20d else None,
        'target_sweet_date': str(target_entry_date_sweet) if target_entry_date_sweet else None,
        'target_div_date': str(target_entry_date_5d) if target_entry_date_5d else None,
        'target_limit_avg': live_5d_avg_low, 'target_limit_min': live_5d_min_low,
        'historical_cycles': historical_cycles, 'sector': sector, 'industry': industry,
        'benchmark_ticker': benchmark_ticker, 'correlation': correlation,
        'move_profile': move_profile, 'current_price': current_price,
        'bench_5d_trend': ((bench_hist['Close'].iloc[-1] / bench_hist['Close'].iloc[-5]) - 1) * 100 if len(bench_hist) >= 5 else 0
    }
    
    # Process historical_cycles to be JSON serializable
    for cycle in stats_dict['historical_cycles']:
        for k, v in cycle.items():
            if isinstance(v, (pd.Timestamp, datetime)):
                try: cycle[k] = str(v.date())
                except: cycle[k] = str(v)
            elif isinstance(v, float) and pd.isna(v):
                cycle[k] = None

    image_b64 = generate_plot_base64(valid_symbol, hist, vix_hist, dividends, stats_dict)
    
    return {
        "image": image_b64,
        "stats": stats_dict
    }
