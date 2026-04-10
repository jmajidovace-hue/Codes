# Antigravity Trading Hub

A premium, localized web application integrating advanced financial scanners and calculators for dividend and rebalancing strategies.

## Features

- **Global Dividend Scan**: Streams live market data to find upcoming ex-dividend plays, pre-dividend rallies, and "Holy Grail" trades.
- **Specific Dividend Finder**: Generates detailed historical recovery and target maps for specific tickers using Matplotlib.
- **EOM Rebalancing Matrix**: Scans hundreds of preferred stocks for monthly rebalancing distortions and mean-reversion opportunities.
- **EOM Rebalancing Map**: Maps the specific footprint of a ticker's behavior on the last day of the month.
- **Trade Calculators**: 
  - **SMI Calculator**: Calculates net profit after Short Margin Interest costs.
  - **Long Commission Calculator**: Evaluates trade profitability against fixed 8% margin rates.

## Local Installation

1. Ensure you have **Python 3.10+** installed.
2. Clone the repository:
   ```bash
   git clone https://github.com/jmajidovace-hue/Codes.git
   cd Codes
   ```
3. Run the dashboard:
   Double-click `START_WEBSITE.bat`. This will automatically install dependencies and launch your browser.

## Tech Stack

- **Backend**: FastAPI (Python)
- **Data**: yfinance, Pandas, Numpy
- **Charts**: Matplotlib 
- **Frontend**: Vanilla HTML5, CSS3, Javascript (Glassmorphic Design)

## Deployment Notes

This project includes a `vercel.json` for deployment to **Vercel**. 
> [!WARNING]
> While calculators and charts work on serverless platforms, the **Scanning** features (Dividend/Rebalance) will likely exceed the 10-second timeout on Vercel's hobby plan. For full scanning capabilities, it is recommended to run locally or use a persistent server like **Railway.app**.
