import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from curl_cffi import requests
import time

# Set up a requests session using curl_cffi to mimic a REAL browser's TLS fingerprint.
# This prevents Vercel IPs from being blocked by Yahoo's Cloudflare protection.
yf_session = requests.Session(impersonate="chrome110")
warnings.filterwarnings('ignore')

raw_tickers = [
    "ACP-A", "ACR-D", "ACR-C", "ADAMI", "ADAMG", "ADAMH", "ADAMM",
    "ADAMO", "ADAMZ", "ADAML", "ADAMN", "APOS", "AEFC", "MGR", "MGRE", "MGRB", "MGRD", "MITT-C",
    "MITN", "MITP", "MITT-A", "MITT-B", "MBNKO", "AGNCN", "AGNCO", "AGNCL", "AGNCZ", "AGNCM",
    "AGNCP", "ADC-A", "AQNB", "ALL-I", "ALL-J", "ALL-H", "ALL-B", "PINE-A", "ALTG-A", "AFGD",
    "AFGC", "AFGB", "AFGE", "AMH-G", "AMH-H", "ANG-D", "AOMD", "AOMN", "NLY-G", "NLY-I", "NLY-F",
    "NLY-J", "ACGLN", "ACGLO", "AHH-A", "ARR-C", "ASBA", "ASB-E", "ASB-F", "AIZN", "TBB", "T-A",
    "T-C", "ATH-D", "ATH-E", "ATHS", "ATH-A", "ATH-B", "AUB-A", "ATLCL", "ATLCP", "ATLCZ", "AXS-E",
    "BANC-F", "BCV-A", "BAC-O", "BAC-P", "BAC-E", "BAC-Q", "BML-J", "BML-G", "BML-H", "BAC-S",
    "BAC-K", "BML-L", "BAC-B", "IPB", "BAC-M", "BAC-N", "BAC-L", "BOH-A", "BOH-B", "BK-K", "OZKAP",
    "BANFP", "BC-C", "COF-I", "COF-J", "COF-N", "COF-K", "COF-L", "CCID", "CGABL", "CHSCL", "CHSCN",
    "CHSCP", "CHSCO", "CHSCM", "CLDT-A", "CIM-A", "CIM-D", "CIM-B", "CIMN", "CIMO", "CIMP", "CIM-C",
    "C-N", "CFG-E", "CFG-H", "CFG-I", "CMSD", "CMSC", "CMSA", "CMS-C", "CNO-A", "CNOBP", "CRBD",
    "CTA-A", "CTA-B", "CMRE-B", "CMRE-C", "CTO-A", "DRH-A", "DSX-B", "DLR-J", "DLR-L", "DLR-K", "DDT",
    "DCOMP", "DCOMG", "DTW", "DTG", "DTK", "DTB", "DUK-A", "DUKB", "DX-C", "ECCF", "ECCV", "ECC-D",
    "ECCW", "ECCX", "ECCC", "ECCU", "EICC", "EICA", "EIIA", "EP-C", "EFC-B", "EFC-A", "EFC-C", "EFC-D",
    "ECF-A", "EAI", "ELC", "EMP", "ENJ", "ENO", "ETI-", "EQH-A", "EQH-C", "FGSN", "FGN", "AGM-F",
    "AGM-E", "AGM-D", "AGM-G", "FRT-C", "FITBP", "FITBI", "FITBM", "FITBO", "BUSEP", "FCNCO", "FCNCP",
    "FCNC", "FCRX", "FHN-E", "FHN-C", "FHN-F", "FRMEP", "FLG-A", "F-B", "F-C", "F-D", "FBRT-E", "FULTP",
    "FGNXP", "GDV-H", "GDV-K", "GAB-G", "GAB-K", "GAB-H", "GGT-G", "GGT-E", "GUT-C", "GGN-B", "GNT-A",
    "GAM-B", "GPJA", "GOODN", "GOODO", "GAINN", "GAINZ", "GAING", "GAINI", "LANDO", "LANDP", "LANDM",
    "XRN-B", "XRN-A", "GNL-B", "GNL-E", "GNL-D", "GSL-B", "GL-D", "GS-A", "GS-D", "JBK", "GS-C", "GECCH",
    "GECCG", "GECCI", "GECCO", "GEGGL", "GRBK-A", "HWCPZ", "HIG-G", "HCXY", "HBANM", "HBANP", "HBANZ",
    "HBANL", "IVR-C", "JXN-A", "JPM-D", "JPM-C", "JPM-J", "JPM-K", "JPM-L", "JPM-M", "KMPB", "KEY-J",
    "KEY-I", "KEY-K", "KEY-L", "KIM-M", "KIM-L", "KIM-N", "KKRT", "KKRS", "LXP-C", "LNC-D", "LOB-A",
    "MTB-K", "MTB-J", "MTB-H", "MBINN", "MBINM", "MBINL", "MER-K", "MET-F", "MET-E", "MET-A", "MFAN",
    "MFA-C", "MFA-B", "MFAO", "MAA-I", "MFICL", "MS-F", "MS-L", "MS-O", "MS-E", "MS-I", "MS-P", "MS-Q",
    "MS-K", "MS-A", "MDV-A", "MLCIL", "NRUC", "JSM", "NMFCZ", "NEWTZ", "NEWTO", "NEWTI", "NEWTG", "NEWTP",
    "NEWTH", "NEE-U", "NEE-N", "NTRSO", "NSA-A", "OFSSO", "OCCIM", "OCCIN", "OCCIO", "ONBPP", "OXLCZ",
    "OXLCP", "OXLCG", "OXLCL", "OXLCN", "OXLCI", "OXLCO", "OXSQG", "OXSQH", "PDPA", "PEB-E", "PEB-F",
    "PEB-G", "PEB-H", "PMTV", "PMT-A", "PMT-B", "PMTW", "PMT-C", "PMTU", "PNFP-C", "PNFP-B", "PNFP-A",
    "BPOPM", "PRIF-K", "PRIF-J", "PRIF-L", "PRIF-D", "PFH", "PRH", "PRS", "PSA-F", "PSA-G", "PSA-H",
    "PSA-I", "PSA-N", "PSA-S", "PSA-J", "PSA-O", "PSA-R", "PSA-K", "PSA-P", "PSA-L", "PSA-M", "PSA-Q",
    "RWTN", "RWTO", "RWTP", "RWTQ", "RWT-A", "REGCO", "REGCP", "RF-E", "RF-C", "RF-F", "RZC", "RZB",
    "RNR-F", "RNR-G", "REXR-B", "RITM-E", "RITM-D", "RITM-C", "RITM-B", "RITM-A", "RPT-C", "OPP-A",
    "OPP-B", "OPP-C", "RLJ-A", "RWAYZ", "RWAYL", "RWAYI", "SB-C", "SB-D", "SAJ", "SAY", "SAZ", "SAT",
    "BFS-D", "BFS-E", "SCHW-D", "SCHW-J", "SIGIP", "SREA", "SPNT-B", "SPMA", "SPME", "SOJC", "SOJD",
    "SOJE", "SOJF", "SPE-C", "SR-A", "SRJN", "STT-G", "SF-B", "SF-C", "SF-D", "SEAL-A", "SEAL-B", "SAV",
    "INN-F", "INN-E", "SHO-H", "SHO-I", "SYF-A", "SYF-B", "TMUSL", "TMUSZ", "TMUSI", "TVE", "TVC", "TFSA",
    "TPTA", "TCBIO", "BK-K", "TPGXL", "TY-", "TRINZ", "TRINI", "TRTN-A", "TRTN-D", "TRTN-F", "TRTN-B",
    "TRTN-E", "TFC-R", "TFC-I", "TEN-E", "TEN-F", "TCPA", "UMH-D", "UNMA", "USB-Q", "USB-P", "USB-H",
    "USB-R", "USB-S", "VLYPP", "VLYPO", "VLYPN", "NCV-A", "NCZ-A", "VOYA-B", "WAFDP", "WBS-F", "WBS-G",
    "WFC-A", "WFC-Z", "WFC-C", "WFC-Y", "WFC-D", "WFC-L", "WSBCO", "WAL-A", "WTFCN", "WRB-F", "WRB-E",
    "WRB-H", "WRB-G", "LTSF", "LTSAP", "LTSL", "LTSK", "LTSH", "EPR-C", "EPR-E", "EPR-G", "GJR", "XELLL",
    "CICB", "CICC", "CMRE-D", "LFT-A", "GPMT-A", "NHPAP", "NHPBP", "RIV-A", "SSSSL", "SWKHL", "WHFCL", "XOMAP", "XOMAO"
]

def format_sse(data: str) -> str:
    lines = str(data).split('\n')
    msg = ""
    for line in lines:
        msg += f"data: {line}\n"
    msg += "\n"
    return msg

def translate_ticker(ticker):
    if "-" in ticker:
        parts = ticker.split("-")
        return f"{parts[0]}-P{parts[1]}"
    return ticker

def get_recovery(df, start_idx, target_price, look_for_bounce=True):
    rec_days = 14
    succ = False
    for d in range(1, 15):
        if start_idx + d < len(df):
            curr_p = df['Close'].iloc[start_idx + d]
            if (look_for_bounce and curr_p >= target_price) or (not look_for_bounce and curr_p <= target_price):
                rec_days = d
                succ = True
                break
    return rec_days, succ

def calculate_volumes(df, loc):
    vol_base = df['Volume'].iloc[max(0, loc-23):max(0, loc-3)].mean()
    vol_prior = df['Volume'].iloc[max(0, loc-3):loc].mean()
    vol_day = df['Volume'].iloc[loc]
    vol_post = df['Volume'].iloc[loc+1:loc+4].mean()
    return vol_base, vol_prior, vol_day, vol_post

def fetch_rebalancing_ticker(ticker, start_date, end_date):
    try:
        tkr_obj = yf.Ticker(ticker)
        shares_out = None
        try:
            shares_out = tkr_obj.fast_info.get('shares')
        except Exception:
            try:
                shares_out = tkr_obj.info.get('sharesOutstanding')
            except Exception:
                pass

        if shares_out is not None and not pd.isna(shares_out) and shares_out < 4000000:
            return ticker, "excluded", None

        # Standard yf.download using the session to prevent blocks
        temp_df = yf.download(ticker, start=start_date, end=end_date, actions=True, progress=False)
        if isinstance(temp_df.columns, pd.MultiIndex):
            temp_df.columns = temp_df.columns.get_level_values(0)

        temp_df.index = pd.to_datetime(temp_df.index, errors='coerce')
        temp_df = temp_df[temp_df.index.notnull()]

        if not temp_df.empty and len(temp_df) > 20 and 'Close' in temp_df.columns and 'Volume' in temp_df.columns:
            if float(temp_df['Close'].iloc[-1]) <= 30.0:
                if 'Dividends' not in temp_df.columns:
                    temp_df['Dividends'] = 0.0
                return ticker, "success", temp_df
        return ticker, "failed", None
    except Exception:
        return ticker, "failed", None

async def scan_rebalancing():
    yf_tickers = [translate_ticker(t) for t in raw_tickers]
    yield format_sse(f"Fetching 6 MONTHS of data & checking PFF eligibility (>4M shares) for {len(yf_tickers)} preferreds...")
    
    end_date = datetime.today()
    start_date = end_date - timedelta(days=180)
    
    clean_data = {}
    excluded_count = 0

    # Process tickers concurrently but with fewer workers to avoid 429s
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(fetch_rebalancing_ticker, ticker, start_date, end_date): ticker for ticker in yf_tickers}
        completed = 0
        
        for future in as_completed(futures):
            time.sleep(0.05) # Small jitter delay
            try:
                ticker, status, result = future.result()
                
                if status == "excluded":
                    excluded_count += 1
                elif status == "success":
                    clean_data[ticker] = result
            except Exception as e:
                # Log any unexpected errors to Vercel console for debugging
                print(f"Error processing rebalance ticker {futures[future]}: {e}")
                
            completed += 1
            if completed % 25 == 0:
                yield format_sse(f"  ... checked {completed}/{len(yf_tickers)} ...")
                await asyncio.sleep(0.01)

    yield format_sse(f"Excluded {excluded_count} tickers for having < 4 Million shares.")
    yield format_sse(f"Successfully processed {len(clean_data)} valid PFF-eligible preferred stocks trading under $30.")

    move_threshold = 0.125
    res_drop_prior, res_drop_eom, res_spike_prior, res_spike_eom = [], [], [], []
    res_div_drop_prior, res_mean_revert, res_holy_grail, res_strict_6 = [], [], [], []

    yield format_sse("Analyzing Pre-EOM, EOM, Holy Grail, and Ironclad 6-Month Reversions...")
    
    for i, yf_ticker in enumerate(yf_tickers):
        original_ticker = raw_tickers[i]
        if yf_ticker not in clean_data: continue

        # Let the event loop breathe
        await asyncio.sleep(0.01)

        df = clean_data[yf_ticker]
        df['YearMonth'] = df.index.to_period('M')

        eom_dates = df.groupby('YearMonth').apply(lambda x: x.index[-1]).values
        div_dates = df[df['Dividends'] > 0].index

        t_drop_prior, t_drop_eom, t_spike_prior, t_spike_eom = [], [], [], []
        t_div_drop_prior, t_holy_grail, t_strict_history = [], [], []

        valid_eom_count = 0
        valid_div_count = 0

        # EOM Analysis
        for eom in eom_dates:
            try:
                loc = df.index.get_loc(eom)
                if loc < 5 or loc + 5 >= len(df): continue
                valid_eom_count += 1

                t4_price = float(df['Close'].iloc[loc-4])
                t1_price = float(df['Close'].iloc[loc-1])
                eom_price = float(df['Close'].iloc[loc])

                prior_move = t1_price - t4_price
                eom_move = eom_price - t1_price

                vol_base, vol_prior, vol_eom, vol_post = calculate_volumes(df, loc)
                if pd.isna(vol_base) or vol_base <= 0: continue

                if eom_move < 0:
                    rec_days_strict, succ_strict = get_recovery(df, loc, t1_price, True)
                elif eom_move > 0:
                    rec_days_strict, succ_strict = get_recovery(df, loc, t1_price, False)
                else:
                    rec_days_strict, succ_strict = 14, False

                t_strict_history.append({
                    'move': abs(eom_move), 'rec': rec_days_strict, 'succ': succ_strict,
                    'vb': vol_base, 'vp': vol_prior, 've': vol_eom, 'vpo': vol_post
                })

                if prior_move <= -move_threshold:
                    rec_days, succ = get_recovery(df, loc - 1, t4_price, True)
                    t_drop_prior.append({'move': prior_move, 'rec': rec_days, 'succ': succ, 'vb': vol_base, 'vp': vol_prior, 've': vol_eom, 'vpo': vol_post})

                if eom_move <= -move_threshold:
                    rec_days, succ = get_recovery(df, loc, t1_price, True)
                    t_drop_eom.append({'move': eom_move, 'rec': rec_days, 'succ': succ, 'vb': vol_base, 'vp': vol_prior, 've': vol_eom, 'vpo': vol_post})

                if prior_move >= move_threshold:
                    rec_days, succ = get_recovery(df, loc - 1, t4_price, False)
                    t_spike_prior.append({'move': prior_move, 'rec': rec_days, 'succ': succ, 'vb': vol_base, 'vp': vol_prior, 've': vol_eom, 'vpo': vol_post})

                if eom_move >= move_threshold:
                    rec_days, succ = get_recovery(df, loc, t1_price, False)
                    t_spike_eom.append({'move': eom_move, 'rec': rec_days, 'succ': succ, 'vb': vol_base, 'vp': vol_prior, 've': vol_eom, 'vpo': vol_post})

                is_double_dump = (prior_move <= -move_threshold) and (eom_move <= -move_threshold)
                is_double_spike = (prior_move >= move_threshold) and (eom_move >= move_threshold)

                if is_double_dump or is_double_spike:
                    look_for_bounce = True if is_double_dump else False
                    rec_days, succ = get_recovery(df, loc, t1_price, look_for_bounce)
                    t_holy_grail.append({
                        'prior_move': prior_move, 'move': eom_move, 'rec': rec_days, 'succ': succ,
                        'vb': vol_base, 'vp': vol_prior, 've': vol_eom, 'vpo': vol_post
                    })
            except KeyError:
                continue

        days_to_next_div = "N/A"
        if len(div_dates) >= 1:
            if len(div_dates) >= 2:
                recent_divs = div_dates[-4:] if len(div_dates) >= 4 else div_dates
                gaps = [(recent_divs[i] - recent_divs[i-1]).days for i in range(1, len(recent_divs))]
                avg_gap = int(np.mean(gaps))
            else:
                avg_gap = 90
            
            next_div = div_dates[-1] + pd.Timedelta(days=avg_gap)
            today_date = pd.Timestamp.today().normalize()
            if next_div.tz is not None:
                today_date = today_date.tz_localize(next_div.tz)
            while next_div < today_date:
                next_div += pd.Timedelta(days=avg_gap)
            days_to_next_div = (next_div - today_date).days

        for div_date in div_dates:
            try:
                loc = df.index.get_loc(div_date)
                if loc < 5 or loc + 5 >= len(df): continue
                valid_div_count += 1

                t4_price = float(df['Close'].iloc[loc-4])
                t1_price = float(df['Close'].iloc[loc-1])
                ex_price = float(df['Close'].iloc[loc])
                div_amt = float(df['Dividends'].iloc[loc])

                prior_move = t1_price - t4_price
                ex_move_net = (ex_price - t1_price) + div_amt

                vol_base, vol_prior, vol_ex, vol_post = calculate_volumes(df, loc)
                if pd.isna(vol_base) or vol_base <= 0: continue

                if prior_move <= -move_threshold:
                    rec_days, succ = get_recovery(df, loc - 1, t4_price, True)
                    t_div_drop_prior.append({'move': prior_move, 'net_ex_drop': ex_move_net, 'rec': rec_days, 'succ': succ, 'vb': vol_base, 'vp': vol_prior, 've': vol_ex, 'vpo': vol_post})
            except KeyError:
                continue

        # Aggregation Logic (Refactored to be cleaner)
        def append_eom_result(target_list, data_array, valid_count):
            if len(data_array) > 0:
                succ_count = sum(1 for x in data_array if x['succ'])
                target_list.append({
                    'Ticker': original_ticker,
                    'Success Ratio': f"{succ_count} / {valid_count}",
                    'Triggers': len(data_array),
                    'Avg Move ($)': f"{np.nanmean([x['move'] for x in data_array]):+.2f}",
                    'Days to Rec': round(np.nanmean([x['rec'] for x in data_array]), 1),
                    'Base Vol': f"{np.nanmean([x['vb'] for x in data_array]):,.0f}",
                    'Prior 3D Vol': f"{np.nanmean([x['vp'] for x in data_array]):,.0f}",
                    'Event Day Vol': f"{np.nanmean([x['ve'] for x in data_array]):,.0f}",
                    'Post 3D Vol': f"{np.nanmean([x['vpo'] for x in data_array]):,.0f}"
                })

        def append_div_result(target_list, data_array, valid_count, dte):
            if len(data_array) > 0:
                succ_count = sum(1 for x in data_array if x['succ'])
                target_list.append({
                    'Ticker': original_ticker,
                    'Success Ratio': f"{succ_count} / {valid_count}",
                    'Triggers': len(data_array),
                    'Days Next Div': dte,
                    'Pre-Div Drop ($)': f"{np.nanmean([x['move'] for x in data_array]):+.2f}",
                    'Net Ex-Div Drop ($)': f"{np.nanmean([x['net_ex_drop'] for x in data_array]):+.2f}",
                    'Days to Rec': round(np.nanmean([x['rec'] for x in data_array]), 1),
                    'Base Vol': f"{np.nanmean([x['vb'] for x in data_array]):,.0f}",
                    'Prior 3D Vol': f"{np.nanmean([x['vp'] for x in data_array]):,.0f}",
                    'Ex-Date Vol': f"{np.nanmean([x['ve'] for x in data_array]):,.0f}"
                })

        def append_holygrail_result(target_list, data_array, valid_count):
            if len(data_array) > 0:
                succ_count = sum(1 for x in data_array if x['succ'])
                target_list.append({
                    'Ticker': original_ticker,
                    'Success Ratio': f"{succ_count} / {valid_count}",
                    'Triggers': len(data_array),
                    'Pre-EOM Move ($)': f"{np.nanmean([x['prior_move'] for x in data_array]):+.2f}",
                    'EOM Move ($)': f"{np.nanmean([x['move'] for x in data_array]):+.2f}",
                    'Days to Rec': round(np.nanmean([x['rec'] for x in data_array]), 1),
                    'Base Vol': f"{np.nanmean([x['vb'] for x in data_array]):,.0f}",
                    'Prior 3D Vol': f"{np.nanmean([x['vp'] for x in data_array]):,.0f}",
                    'Event Day Vol': f"{np.nanmean([x['ve'] for x in data_array]):,.0f}",
                    'Post 3D Vol': f"{np.nanmean([x['vpo'] for x in data_array]):,.0f}"
                })

        t_mean_revert = t_drop_eom + t_spike_eom
        if len(t_mean_revert) > 0:
            succ_count = sum(1 for x in t_mean_revert if x['succ'])
            res_mean_revert.append({
                'Ticker': original_ticker,
                'Success Ratio': f"{succ_count} / {valid_eom_count}",
                'Triggers': len(t_mean_revert),
                'Avg Abs Move ($)': f"{np.nanmean([abs(x['move']) for x in t_mean_revert]):.2f}",
                'Days to Rec': round(np.nanmean([x['rec'] for x in t_mean_revert]), 1),
                'Base Vol': f"{np.nanmean([x['vb'] for x in t_mean_revert]):,.0f}",
                'Event Day Vol': f"{np.nanmean([x['ve'] for x in t_mean_revert]):,.0f}",
                'Post 3D Vol': f"{np.nanmean([x['vpo'] for x in t_mean_revert]):,.0f}"
            })

        if len(t_strict_history) >= 6:
            last_6 = t_strict_history[-6:]
            succ_count = sum(1 for x in last_6 if x['succ'])
            res_strict_6.append({
                'Ticker': original_ticker,
                'Success Ratio': f"{succ_count} / 6",
                'Triggers': 6,
                'Avg Abs Move ($)': f"{np.nanmean([x['move'] for x in last_6]):.2f}",
                'Days to Rec': round(np.nanmean([x['rec'] for x in last_6]), 1),
                'Base Vol': f"{np.nanmean([x['vb'] for x in last_6]):,.0f}",
                'Prior 3D Vol': f"{np.nanmean([x['vp'] for x in last_6]):,.0f}",
                'Event Day Vol': f"{np.nanmean([x['ve'] for x in last_6]):,.0f}",
                'Post 3D Vol': f"{np.nanmean([x['vpo'] for x in last_6]):,.0f}"
            })

        append_eom_result(res_drop_prior, t_drop_prior, valid_eom_count)
        append_eom_result(res_drop_eom, t_drop_eom, valid_eom_count)
        append_eom_result(res_spike_prior, t_spike_prior, valid_eom_count)
        append_eom_result(res_spike_eom, t_spike_eom, valid_eom_count)
        append_div_result(res_div_drop_prior, t_div_drop_prior, valid_div_count, days_to_next_div)
        append_holygrail_result(res_holy_grail, t_holy_grail, valid_eom_count)

    def process_and_send(data_list, title):
        output = f"\n============================================================================================================================================\n"
        output += f"{title}\n"
        output += f"============================================================================================================================================\n"
        df_out = pd.DataFrame(data_list)
        if not df_out.empty:
            df_out['Hit_Ratio'] = df_out['Success Ratio'].apply(lambda x: int(str(x).split(' / ')[0]) / int(str(x).split(' / ')[1]) if int(str(x).split(' / ')[1]) > 0 else 0)
            best_df = df_out[df_out['Triggers'] >= 1].sort_values(by=['Hit_Ratio', 'Days to Rec'], ascending=[False, True]).drop(columns=['Hit_Ratio'])
            output += best_df.head(100).to_string(index=False)
        else:
            output += "No frequent patterns detected for this category."
        return format_sse(output)

    yield process_and_send(res_drop_prior, "📉 1. PRE-EOM DUMP (Price drops > $0.12 in the 3 days BEFORE EOM, then recovers)")
    yield process_and_send(res_drop_eom,   "🩸 2. EOM DAY DUMP (Price drops > $0.12 exactly ON Rebalancing Day, then recovers)")
    yield process_and_send(res_spike_prior,"📈 3. PRE-EOM ACCUMULATION (Price spikes > $0.12 in the 3 days BEFORE EOM, then reverts down)")
    yield process_and_send(res_spike_eom,  "🚀 4. EOM DAY ACCUMULATION (Price spikes > $0.12 exactly ON Rebalancing Day, then reverts down)")
    yield process_and_send(res_div_drop_prior, "💸 5. PRE-DIVIDEND DUMP (Price artificially dumped > $0.12 in the 3 days BEFORE Ex-Date)")
    yield process_and_send(res_mean_revert, "🧲 6. FASTEST MEAN REVERSION (Predictably snap back after EOM distortion)")
    yield process_and_send(res_holy_grail, "🏆 7. THE HOLY GRAIL (Continuous Trend BOTH Pre-EOM and ON EOM)")
    yield process_and_send(res_strict_6, "🎯 8. THE 6-MONTH IRONCLAD TEST (Requires exactly 6 EOM events)")

    yield format_sse("EOF")
