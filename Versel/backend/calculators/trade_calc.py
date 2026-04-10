import pandas as pd
import io

def calculate_smi(file_content: bytes, filename: str, ticker: str, shares: float, price: float, days: int, target_profit: float):
    # Process the file exactly as the Colab notebook did
    if filename.lower().endswith('.csv'):
        df = pd.read_csv(io.BytesIO(file_content))
    else:
        df = pd.read_excel(io.BytesIO(file_content))

    if 'Symbol' not in df.columns:
        first_col_name = df.columns[0]
        if "," in str(first_col_name):
            headers = str(first_col_name).split(',')
            headers = [h.strip() for h in headers]
            df_split = df[first_col_name].astype(str).str.split(',', expand=True)

            if len(headers) >= df_split.shape[1]:
                df_split.columns = headers[:df_split.shape[1]]
            else:
                df_split.columns = headers
            df = df_split

    df.columns = [str(c).strip() for c in df.columns]

    if 'Rate' in df.columns:
         df['Rate'] = pd.to_numeric(df['Rate'], errors='coerce')

    if 'Symbol' not in df.columns:
        raise Exception("Could not find 'Symbol' column in the uploaded file.")

    row = df[df['Symbol'] == ticker]
    if row.empty:
        raise Exception(f"Ticker '{ticker}' not found in the uploaded file.")

    yearly_rate_raw = abs(float(row.iloc[0]['Rate']))
    daily_rate = (yearly_rate_raw / 100.0) / 365.0

    daily_cost = (shares * price) * daily_rate
    total_smi_cost = daily_cost * days

    gross_profit = target_profit * shares
    net_profit = gross_profit - total_smi_cost

    return {
        "yearly_rate": yearly_rate_raw,
        "position_value": shares * price,
        "daily_cost": daily_cost,
        "total_cost": total_smi_cost,
        "potential_gain": gross_profit,
        "net_profit": net_profit,
        "is_good": net_profit > 0
    }

def calculate_long_commission(ticker: str, shares: float, price: float, days: int, target_profit: float):
    yearly_rate_raw = 8.0
    daily_rate = (yearly_rate_raw / 100.0) / 365.0

    daily_cost = (shares * price) * daily_rate
    total_commission_cost = daily_cost * days

    gross_profit = target_profit * shares
    net_profit = gross_profit - total_commission_cost

    return {
        "yearly_rate": yearly_rate_raw,
        "position_value": shares * price,
        "daily_cost": daily_cost,
        "total_cost": total_commission_cost,
        "potential_gain": gross_profit,
        "net_profit": net_profit,
        "is_good": net_profit > 0
    }
