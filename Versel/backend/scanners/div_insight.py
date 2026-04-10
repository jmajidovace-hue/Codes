import yfinance as yf
import pandas as pd
import numpy as np
import warnings
import logging
import asyncio
import io

# --- 1. FORCE YFINANCE TO BE COMPLETELY SILENT ---
warnings.filterwarnings("ignore")
yf_logger = logging.getLogger('yfinance')
yf_logger.setLevel(logging.CRITICAL)
yf_logger.disabled = True

# --- YOUR MASTER LIST (Deduplicated & Sorted) ---
VALID_TICKERS = [
    "ACGLN", "ACGLO", "ACP-A", "ACR-C", "ACR-D", "ADAMG", "ADAMH", "ADAMI", "ADAML", "ADAMM",
    "ADAMN", "ADAMO", "ADAMZ", "ADC-A", "AEFC", "AFGB", "AFGC", "AFGD", "AFGE", "AGM-D",
    "AGM-E", "AGM-F", "AGM-G", "AGNCL", "AGNCM", "AGNCN", "AGNCO", "AGNCP", "AGNCZ", "AHH-A",
    "AIZN", "ALL-B", "ALL-H", "ALL-I", "ALL-J", "ALTG-A", "AMH-G", "AMH-H", "ANG-D", "AOMD",
    "AOMN", "APOS", "AQNB", "ARR-C", "ASB-E", "ASB-F", "ASBA", "ATH-A", "ATH-B", "ATH-D",
    "ATH-E", "ATHS", "ATLCL", "ATLCP", "ATLCZ", "AUB-A", "AXS-E", "BAC-B", "BAC-E", "BAC-K",
    "BAC-M", "BAC-N", "BAC-O", "BAC-P", "BAC-Q", "BAC-S", "BANC-F", "BANFP", "BC-C",
    "BCV-A", "BFS-D", "BFS-E", "BK-K", "BML-G", "BML-H", "BML-J", "BML-L", "BOH-A", "BOH-B",
    "BPOPM", "BUSEP", "C-N", "CCID", "CFG-E", "CFG-H", "CFG-I", "CGABL", "CHSCL", "CHSCM",
    "CHSCN", "CHSCO", "CHSCP", "CICB", "CIM-A", "CIM-B", "CIM-C", "CIM-D", "CIMN", "CIMO",
    "CIMP", "CLDT-A", "CMRE-B", "CMRE-C", "CMRE-D", "CMS-C", "CMSA", "CMSC", "CMSD", "CNO-A",
    "CNOBP", "COF-I", "COF-J", "COF-K", "COF-L", "COF-N", "CRBD", "CTA-A", "CTA-B", "CTO-A",
    "DCOMP", "DCOMG", "DDT", "DLR-J", "DLR-K", "DLR-L", "DRH-A", "DSX-B", "DTB", "DTG",
    "DTK", "DTW", "DUK-A", "DUKB", "DX-C", "EAI", "ECC-D", "ECCC", "ECCF", "ECCU",
    "ECCV", "ECCW", "ECCX", "ECF-A", "EFC-A", "EFC-B", "EFC-C", "EFC-D", "EICA", "EICC",
    "EIIA", "ELC", "EMP", "ENJ", "ENO", "EP-C", "EPR-C", "EPR-E", "EPR-G", "EQH-A",
    "EQH-C", "ETI-", "F-B", "F-C", "F-D", "FBRT-E", "FCNC", "FCNCO", "FCNCP", "FCRX",
    "FGN", "FGNXP", "FGSN", "FHN-C", "FHN-E", "FHN-F", "FITBI", "FITBM", "FITBO", "FITBP",
    "FLG-A", "FRMEP", "FRT-C", "FULTP", "GAB-G", "GAB-H", "GAB-K", "GAING", "GAINI", "GAINN",
    "GAINZ", "GAM-B", "GDV-H", "GDV-K", "GECCG", "GECCH", "GECCI", "GECCO", "GEGGL", "GGT-E",
    "GGT-G", "GJR", "GL-D", "GMRE-A", "GMRE-B", "GNL-B", "GNL-D", "GNL-E", "GNT-A", "GOODN",
    "GOODO", "GPJA", "GPMT-A", "GRBK-A", "GS-A", "GS-C", "GS-D", "GSL-B", "GUT-C", "HBANL",
    "HBANM", "HBANP", "HBANZ", "HCXY", "HIG-G", "HWCPZ", "INN-E", "INN-F", "IPB", "IVR-C",
    "JBK", "JPM-C", "JPM-D", "JPM-J", "JPM-K", "JPM-L", "JPM-M", "JSM", "JXN-A", "KEY-I",
    "KEY-J", "KEY-K", "KEY-L", "KIM-L", "KIM-M", "KIM-N", "KKRS", "KKRT", "KMPB", "LANDM",
    "LANDO", "LANDP", "LFT-A", "LNC-D", "LOB-A", "LTSAP", "LTSF", "LTSH", "LTSK", "LTSL",
    "LXP-C", "MAA-I", "MBINL", "MBINM", "MBINN", "MBNKO", "MDV-A", "MER-K", "MET-A", "MET-E",
    "MET-F", "MFA-B", "MFA-C", "MFAN", "MFAO", "MFICL", "MGR", "MGRB", "MGRD", "MGRE",
    "MITN", "MITP", "MITT-A", "MITT-B", "MITT-C", "MLCIL", "MS-A", "MS-E", "MS-F", "MS-I",
    "MS-K", "MS-L", "MS-O", "MS-P", "MS-Q", "MTB-H", "MTB-J", "MTB-K", "NCV-A", "NCZ-A",
    "NEE-N", "NEE-U", "NEWTG", "NEWTH", "NEWTI", "NEWTO", "NEWTP", "NEWTZ", "NHPAP", "NHPBP",
    "NMFCZ", "NTRSO", "OCCIM", "OCCIN", "OCCIO", "OFSSO", "ONBPP", "OPP-A", "OPP-B", "OPP-C",
    "OXLCG", "OXLCI", "OXLCL", "OXLCN", "OXLCO", "OXLCP", "OXLCZ", "OXSQG", "OXSQH", "OZKAP",
    "PDPA", "PEB-E", "PEB-F", "PEB-G", "PEB-H", "PFH", "PINE-A", "PMT-A", "PMT-B", "PMT-C",
    "PMTU", "PMTV", "PMTW", "PNFP-A", "PNFP-B", "PNFP-C", "PRH", "PRIF-D", "PRIF-J", "PRIF-K",
    "PRIF-L", "PRS", "PSA-F", "PSA-G", "PSA-H", "PSA-I", "PSA-J", "PSA-K", "PSA-L", "PSA-M",
    "PSA-N", "PSA-O", "PSA-P", "PSA-Q", "PSA-R", "PSA-S", "REGCO", "REGCP", "REXR-B", "RF-C",
    "RF-E", "RF-F", "RITM-A", "RITM-B", "RITM-C", "RITM-D", "RITM-E", "RIV-A", "RLJ-A", "RNR-F",
    "RNR-G", "RPT-C", "RWAYI", "RWAYL", "RWAYZ", "RWT-A", "RWTN", "RWTO", "RWTP", "RWTQ",
    "RZB", "RZC", "SAJ", "SAT", "SAV", "SAY", "SAZ", "SB-C", "SB-D", "SCHW-D",
    "SCHW-J", "SEAL-A", "SEAL-B", "SF-B", "SF-C", "SF-D", "SHO-H", "SHO-I", "SIGIP", "SOJC",
    "SOJD", "SOJE", "SOJF", "SPE-C", "SPMA", "SPME", "SPNT-B", "SR-A", "SREA", "SRJN",
    "SSSSL", "STT-G", "SWKHL", "SYF-A", "SYF-B", "T-A", "T-C", "TBB", "TCBIO", "TCPA",
    "TEN-E", "TEN-F", "TFC-I", "TFC-R", "TFSA", "TMUSI", "TMUSL", "TMUSZ", "TPGXL", "TPTA",
    "TRINI", "TRINZ", "TRTN-A", "TRTN-B", "TRTN-D", "TRTN-E", "TRTN-F", "TVC", "TVE",
    "UMH-D", "UNMA", "USB-H", "USB-P", "USB-Q", "USB-R", "USB-S", "VLYPN", "VLYPO", "VLYPP",
    "VOYA-B", "WAFDP", "WAL-A", "WBS-F", "WBS-G", "WFC-A", "WFC-C", "WFC-D", "WFC-Y",
    "WFC-Z", "WHFCL", "WRB-E", "WRB-F", "WRB-G", "WRB-H", "WSBCO", "WTFCN", "XELLL", "XOMAO",
    "XOMAP", "XRN-A", "XRN-B"
]

def format_sse(data: str) -> str:
    # Handle multi-line strings properly for SSE
    lines = str(data).split('\n')
    msg = ""
    for line in lines:
        msg += f"data: {line}\n"
    msg += "\n"
    return msg

def get_history_silent_and_smart(user_ticker):
    candidates = []
    candidates.append(user_ticker)
    
    if "-" in user_ticker:
        base, suffix = user_ticker.split("-", 1)
        candidates.append(f"{base}-P{suffix}")
        candidates.append(f"{base}-P-{suffix}")
        candidates.append(f"{base}.PR.{suffix}")

    if "-" not in user_ticker and len(user_ticker) >= 4:
        base1 = user_ticker[:-1]
        suffix1 = user_ticker[-1]
        candidates.append(f"{base1}-P{suffix1}")

    candidates = list(dict.fromkeys(candidates))

    for ticker_to_try in candidates:
        try:
            stock = yf.Ticker(ticker_to_try)
            hist = stock.history(period="5d", auto_adjust=False)

            if not hist.empty:
                # Use 2y instead of max for scanning speed and lower ban risk
                full_hist = stock.history(period="2y", auto_adjust=False)
                if full_hist.empty:
                    continue
                return stock, full_hist
        except Exception:
            pass

    return None, None

def get_upcoming_dividend(stock, dividends_hist):
    today = pd.Timestamp.now().normalize()
    if dividends_hist.index.tz is not None:
        today = today.tz_localize(dividends_hist.index.tz)

    next_date = None

    try:
        info = stock.info
        if 'exDividendDate' in info and info['exDividendDate'] is not None:
            ts = pd.to_datetime(info['exDividendDate'], unit='s')
            if ts.tz is None and today.tz is not None:
                ts = ts.tz_localize(today.tz)

            if ts.date() >= today.date():
                next_date = ts.date()
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

    return next_date

def analyze_ticker(user_ticker_name, hist, stock_obj):
    current_price = hist['Close'].iloc[-1]
    if pd.isna(current_price) or current_price > 30.0:
        return "OVER_PRICE"

    if hist.index.tz is None: hist.index = hist.index.tz_localize('UTC')
    else: hist.index = hist.index.tz_convert('UTC')

    dividends = stock_obj.dividends
    if dividends.index.tz is None: dividends.index = dividends.index.tz_localize('UTC')
    else: dividends.index = dividends.index.tz_convert('UTC')

    recovery_days_list_be = []
    recovery_days_list_full = []
    net_profits = []
    run_up_dollars_list = []
    run_up_days_list = []
    late_entry_days_list = []

    sweet_spot_days_list = []
    sweet_spot_dollars_list = []

    momentum_spike_ratios = []
    momentum_5d_list = []
    volatility_5d_list = []

    recent_dividends = dividends.sort_index(ascending=False).head(10)

    for date, amount in recent_dividends.items():
        if date not in hist.index:
            continue

        ex_date_idx = hist.index.get_loc(date)
        if ex_date_idx == 0: continue

        pre_div_price = hist.iloc[ex_date_idx - 1]['Close']
        ex_day_open = hist.iloc[ex_date_idx]['Open']

        after_tax_dividend = amount * 0.90
        price_drop = pre_div_price - ex_day_open
        net_profit_dollars = after_tax_dividend - price_drop
        net_profits.append(net_profit_dollars)

        lookback = 20
        start_idx = max(0, ex_date_idx - lookback)
        window_data = hist.iloc[start_idx : ex_date_idx]

        if not window_data.empty:
            min_price_in_window = window_data['Close'].min()
            min_price_date = window_data['Close'].idxmin()

            days_before = (date - min_price_date).days
            gross_run_up_dollars = pre_div_price - min_price_in_window

            daily_rate = (8.0 / 100.0) / 365.0
            commission_cost = (min_price_in_window * daily_rate) * days_before
            net_run_up_dollars = gross_run_up_dollars - commission_cost

            run_up_days_list.append(days_before)
            run_up_dollars_list.append(net_run_up_dollars)

            if len(window_data) > 1:
                daily_diffs = window_data['Close'].diff()
                biggest_spike_date = daily_diffs.idxmax()
                spike_idx = window_data.index.get_loc(biggest_spike_date)
                entry_idx = max(0, spike_idx - 1)

                sweet_dt = window_data.index[entry_idx]
                sweet_px = window_data['Close'].iloc[entry_idx]
            else:
                sweet_dt = min_price_date
                sweet_px = min_price_in_window

            sweet_days_before = (date - sweet_dt).days
            if sweet_days_before <= 0: sweet_days_before = 1

            sweet_commission = (sweet_px * daily_rate) * sweet_days_before
            net_sweet_run_up = (pre_div_price - sweet_px) - sweet_commission

            sweet_spot_days_list.append(sweet_days_before)
            sweet_spot_dollars_list.append(net_sweet_run_up)

            pre_div_dt = hist.index[ex_date_idx - 1]
            mom_window = hist.loc[sweet_dt:pre_div_dt]

            if len(mom_window) > 1 and net_sweet_run_up > 0:
                daily_diffs_osc = mom_window['Close'].diff().dropna()
                max_daily_pop = daily_diffs_osc.max()

                window_range = mom_window['Close'].max() - mom_window['Close'].min()

                if max_daily_pop > 0 and window_range > 0:
                    spike_ratio = max_daily_pop / window_range
                    spike_ratio = min(spike_ratio, 1.0)
                    momentum_spike_ratios.append(spike_ratio)
                else:
                    momentum_spike_ratios.append(0)

        lookback_5d = 5
        start_idx_5d = max(0, ex_date_idx - lookback_5d)
        window_data_5d = hist.iloc[start_idx_5d : ex_date_idx]

        if not window_data_5d.empty and len(window_data_5d) > 1:
            min_price_date_5d = window_data_5d['Close'].idxmin()
            days_before_5d = (date - min_price_date_5d).days
            late_entry_days_list.append(days_before_5d)

            price_5d_ago = window_data_5d['Close'].iloc[0]
            momentum_dlr = pre_div_price - price_5d_ago
            momentum_5d_list.append(momentum_dlr)

            max_h = window_data_5d['High'].max()
            min_l = window_data_5d['Low'].min()
            volatility_dlr = max_h - min_l
            volatility_5d_list.append(volatility_dlr)

        days_to_recover_be = 999
        days_to_recover_full = 999
        recovered_be = False
        recovered_full = False

        future_data = hist.iloc[ex_date_idx:]
        breakeven_target = pre_div_price - after_tax_dividend

        for i in range(len(future_data)):
            current_close = future_data.iloc[i]['Close']

            if not recovered_be and current_close >= breakeven_target:
                days_to_recover_be = i
                recovered_be = True

            if not recovered_full and current_close >= pre_div_price:
                days_to_recover_full = i
                recovered_full = True

            if recovered_be and recovered_full:
                break

        recovery_days_list_be.append(days_to_recover_be)
        recovery_days_list_full.append(days_to_recover_full)

    if not recovery_days_list_be and not recovery_days_list_full:
        return None

    valid_be = [d for d in recovery_days_list_be if d != 999]
    avg_be_recovery = np.mean(valid_be) if valid_be else 999

    valid_full = [d for d in recovery_days_list_full if d != 999]
    avg_full_recovery = np.mean(valid_full) if valid_full else 999

    avg_net_profit = np.mean(net_profits)
    avg_run_up_dlrs = np.mean(run_up_dollars_list) if run_up_dollars_list else 0
    avg_entry_days = np.mean(run_up_days_list) if run_up_days_list else 0

    avg_sweet_days = np.mean(sweet_spot_days_list) if sweet_spot_days_list else 0
    avg_sweet_dlrs = np.mean(sweet_spot_dollars_list) if sweet_spot_dollars_list else 0

    avg_spike_ratio = np.mean(momentum_spike_ratios) if momentum_spike_ratios else 0
    spike_pct = avg_spike_ratio * 100

    if spike_pct == 0:
        move_profile = "N/A"
    elif spike_pct <= 40:
        move_profile = "Continuous 🌊"
    elif spike_pct <= 70:
        move_profile = "Stepped 📈"
    else:
        move_profile = "Spike ⚡"

    avg_div_entry_days = np.mean(late_entry_days_list) if late_entry_days_list else 0

    avg_momentum = np.mean(momentum_5d_list) if momentum_5d_list else 0
    avg_volatility = np.mean(volatility_5d_list) if volatility_5d_list else 0

    if avg_volatility <= 0.35 and avg_momentum >= 0:
        smooth_status = "Yes ✅"
    elif avg_volatility >= 0.75 or avg_momentum < -0.20:
        smooth_status = "No ⚠️"
    else:
        smooth_status = "Moderate"

    fast_recoveries = sum(1 for d in recovery_days_list_be if d <= 30)
    success_rate = (fast_recoveries / len(recovery_days_list_be)) * 100 if recovery_days_list_be else 0

    next_ex_date = get_upcoming_dividend(stock_obj, dividends)
    today_date = pd.Timestamp.now().date()

    if next_ex_date:
        days_until_ex = (next_ex_date - today_date).days
        next_ex_str = next_ex_date.strftime('%Y-%m-%d')
    else:
        days_until_ex = -999
        next_ex_str = "Unknown"

    return {
        "Ticker": user_ticker_name,
        "Current Price ($)": round(current_price, 2),
        "Next Ex-Date": next_ex_str,
        "Days Until Ex": days_until_ex,
        "BE Recov (Days)": round(avg_be_recovery, 1),
        "Full Recov (Days)": round(avg_full_recovery, 1),
        "Avg Net Profit ($)": avg_net_profit,
        "Avg Run-Up ($)": avg_run_up_dlrs,
        "Avg Biggest Move ($)": avg_sweet_dlrs,
        "Rally Entry": round(avg_entry_days, 0),
        "Biggest Move Entry": round(avg_sweet_days, 0),
        "Pop %": round(spike_pct, 0),
        "Move Type": move_profile,
        "Div Entry": round(avg_div_entry_days, 0),
        "Success Rate %": round(success_rate, 0),
        "Smooth?": smooth_status
    }

async def scan_div_insight():
    yield format_sse("--- 🚀 STARTING FULL MARKET SCAN (UPCOMING FOCUS) ---")
    yield format_sse(f"Scanning {len(VALID_TICKERS)} tickers...")
    yield format_sse("Finding: Live Upcoming Trades across Arbitrage, Rallies, Free Divs, and Holy Grails.")
    yield format_sse("Constraints: Price <= $30, Next Ex-Date <= 30 Days")
    yield format_sse("Progress:")

    results = []
    skipped_not_found = []
    skipped_no_divs = []
    skipped_low_history = []
    skipped_over_price = []

    for i, ticker in enumerate(VALID_TICKERS):
        if i > 0 and i % 50 == 0:
            yield format_sse(f"  ... checked {i}/{len(VALID_TICKERS)} ...")
        
        await asyncio.sleep(0.2)
        stock, hist = get_history_silent_and_smart(ticker)

        if stock is None or hist is None or hist.empty:
            skipped_not_found.append(ticker)
            continue

        dividends = stock.dividends
        if dividends.empty:
            skipped_no_divs.append(ticker)
            continue

        recent_dividends = dividends.sort_index(ascending=False).head(10)
        if len(recent_dividends) < 3:
            skipped_low_history.append(ticker)
            continue

        stats = analyze_ticker(ticker, hist, stock)
        if stats == "OVER_PRICE":
            skipped_over_price.append(ticker)
        elif stats:
            results.append(stats)
            # Optionally yield a small update for every find
            # yield format_sse(f"  Found target: {ticker}")
        else:
            skipped_low_history.append(ticker)

    yield format_sse(f"\n  ... DONE! Scanned {len(VALID_TICKERS)} tickers.")
    yield format_sse("  --------------------------------------------------")
    yield format_sse(f"  -> Skipped {len(skipped_not_found)}: Could not fetch data (Likely Yahoo Block/Rate Limit)")
    yield format_sse(f"  -> Skipped {len(skipped_no_divs)}: No dividend history found")
    yield format_sse(f"  -> Skipped {len(skipped_low_history)}: Not enough dividend cycles to analyze")
    yield format_sse(f"  -> Skipped {len(skipped_over_price)}: Priced strictly over $30")
    yield format_sse("  --------------------------------------------------")
    yield format_sse(f"Successfully processed {len(results)} tickers.\n")

    df = pd.DataFrame(results)

    if df.empty:
        yield format_sse("No valid data found under $30.")
        yield format_sse("EOF")
        return

    def format_money(val):
        if pd.isna(val): return "N/A"
        return f"+${val:.2f}" if val >= 0 else f"-${abs(val):.2f}"

    df["Net Profit Str"] = df["Avg Net Profit ($)"].apply(format_money)
    df["Run-Up Str"] = df["Avg Run-Up ($)"].apply(format_money)
    df["Biggest Move Str"] = df["Avg Biggest Move ($)"].apply(format_money)

    upcoming_base = df[(df["Days Until Ex"] != -999) & (df["Days Until Ex"] >= 0) & (df["Days Until Ex"] <= 30)].copy()

    if upcoming_base.empty:
        yield format_sse("\n❌ NO UPCOMING DIVIDENDS FOUND in the next 30 days for tickers under $30.")
        yield format_sse("EOF")
        return

    yield format_sse("\n" + "="*90)
    yield format_sse("🏆 TOP 50: UPCOMING BEST NET DIV PLAY (Arbitrage)")
    yield format_sse("Criteria: Net Profit >= $0.10, Next 30 Days, Price <= $30.")
    yield format_sse("Sorted by: Closest Ex-Date First, then highest Net Profit.")
    yield format_sse("="*90)
    upc_arb = upcoming_base[upcoming_base["Avg Net Profit ($)"] >= 0.10].sort_values(by=["Days Until Ex", "Avg Net Profit ($)"], ascending=[True, False]).head(50)
    yield format_sse(upc_arb[["Ticker", "Next Ex-Date", "Days Until Ex", "Div Entry", "Net Profit Str", "Current Price ($)", "Smooth?", "Success Rate %"]].to_string(index=False))

    yield format_sse("\n" + "="*125)
    yield format_sse("📈 TOP 50: UPCOMING BEST PRE-DIVIDEND RALLIES")
    yield format_sse("Criteria: Next 30 Days, Price <= $30. Sorted by Closest Ex-Date First, then best Pre-Div Run-Up.")
    yield format_sse("="*125)
    upc_rally = upcoming_base.sort_values(by=["Days Until Ex", "Avg Run-Up ($)"], ascending=[True, False]).head(50)
    yield format_sse(upc_rally[["Ticker", "Next Ex-Date", "Days Until Ex", "Rally Entry", "Biggest Move Entry", "Run-Up Str", "Biggest Move Str", "Move Type", "Pop %", "Current Price ($)"]].to_string(index=False))

    yield format_sse("\n" + "="*90)
    yield format_sse("🆓 TOP 50: UPCOMING FREE DIVIDEND PLAYS (Fastest Full Recovery)")
    yield format_sse("Criteria: Next 30 Days, Price <= $30. Sorted by Closest Ex-Date First, then Fastest Full Recovery.")
    yield format_sse("="*90)
    upc_free = upcoming_base.sort_values(by=["Days Until Ex", "Full Recov (Days)"], ascending=[True, True]).head(50)
    yield format_sse(upc_free[["Ticker", "Next Ex-Date", "Days Until Ex", "Div Entry", "Full Recov (Days)", "Net Profit Str", "Current Price ($)"]].to_string(index=False))

    yield format_sse("\n" + "="*90)
    yield format_sse("⚡ TOP 50: UPCOMING FASTEST BREAK-EVEN RECOVERY")
    yield format_sse("Criteria: >70% Success Rate, Next 30 Days, Price <= $30.")
    yield format_sse("Sorted by: Closest Ex-Date First, then fastest BE Recovery.")
    yield format_sse("="*90)
    upc_fast = upcoming_base[upcoming_base["Success Rate %"] >= 70].sort_values(by=["Days Until Ex", "BE Recov (Days)"], ascending=[True, True]).head(50)

    if upc_fast.empty:
         yield format_sse("No upcoming trades meet the 70% success rate for fast break-even right now.")
    else:
         yield format_sse(upc_fast[["Ticker", "Next Ex-Date", "Days Until Ex", "Div Entry", "BE Recov (Days)", "Net Profit Str", "Current Price ($)"]].to_string(index=False))

    yield format_sse("\n" + "="*90)
    yield format_sse("💎 TOP 50: UPCOMING HOLY GRAIL TRADES (Fast BE Recovery + Positive Arbitrage)")
    yield format_sse("Criteria: <= 10 days BE Recov, Net Profit > -$0.10, >= 80% Success Rate, Price <= $30.")
    yield format_sse("Sorted by: Closest Ex-Date First, then best Net Profit.")
    yield format_sse("="*90)
    upc_grail = upcoming_base[
        (upcoming_base["BE Recov (Days)"] <= 10) &
        (upcoming_base["Avg Net Profit ($)"] > -0.10) &
        (upcoming_base["Success Rate %"] >= 80)
    ].sort_values(by=["Days Until Ex", "Avg Net Profit ($)"], ascending=[True, False]).head(50)

    if upc_grail.empty:
        yield format_sse("No Upcoming Holy Grail matches found today. Keep scanning!")
    else:
        yield format_sse(upc_grail[["Ticker", "Next Ex-Date", "Days Until Ex", "Div Entry", "Net Profit Str", "BE Recov (Days)", "Run-Up Str", "Current Price ($)"]].to_string(index=False))
        
    yield format_sse("EOF")
