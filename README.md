# Options Trading Journal & Analyzer

A local, Python-based web application built with Streamlit to track, journal, and analyze complex options trading strategies. The application provides real-time market data integration, advanced payoff visualization, and probability metrics based on log-normal distributions.

## Features

- **Portfolio Management**: Create, switch between, and manage multiple portfolios with dynamic filtering across all dashboards.
- **Strategy Builder & Visualizer**: Construct multi-leg options strategies (up to 8 legs) with accurate quantity sizing. Generates interactive Plotly payoff charts (expiration & T+0 curves) with standard deviation overlays, including simultaneous dynamic tracking of **Current Expected Move** vs **Expected Move at Open**.
- **Advanced Probability & Quant Metrics**: Calculates Probability of Profit (PoP), Probability of Loss (PoL), Probability of Max Profit/Loss, Expected Value (EV), and ROI based on log-normal distribution models.
- **Discounted Cash Flow (DCF) Evaluation**: A highly sophisticated valuation engine featuring an advanced **10-Year Multi-Scenario Free Cash Flow (FCFF) model** with customizable growth decay patterns. Includes:
  - **Live Financial Data Extraction**: Pre-populates default starting FCF, outstanding shares, cash, debt, and beta directly from annual balance sheets and cash flow statements via `yfinance`.
  - **Dynamic WACC & CAPM Calculator**: Estimator based on the Capital Asset Pricing Model (CAPM) using live market-capitalized debt/equity weights, beta, tax rates, risk-free rates, and equity risk premiums.
  - **4-Scenario Concurrency Framework**: Concurrent comparison across **Conservative**, **Base Case**, **Aggressive**, and **Wall Street Consensus** scenarios side-by-side, presenting margin of safety metrics.
  - **Growth Decay Configurations**: Flexible growth trajectory models including Continuous Decay from Year 2, Keeping Stable for 10 years, Delayed Decay from Year 6, or fixed additive/subtractive yearly step increments (X%).
  - **Annual Projection & PV Flow Matrix**: Full-width high-density projection grid outlining growth rates, projected cash flows, and discounted Present Values (PV) across all 10 years and terminal values, featuring row-level custom styling.
  - **Reverse DCF (Market-Implied Expectations)**: Solves for the exact growth rate priced into the stock's current price using a fast numerical bisection solver under any selected growth decay pattern.
  - **Plotly Visualizations**: Elegant vertical bar charts tracking scenario valuations against the current price and Wall Street target consensus mean line.
- **Real-Time Market Data**: Integrates with `yfinance` and `Barchart` to fetch live underlying prices, ticker metadata, and real-time options chain data.
- **Trading Journal & Ledger**: Local PostgreSQL database integration tracking open/closed trades with custom pagination, sorting, dynamic filters (status, debit/credit, ticker), and bulk management. Includes a mechanism to seamlessly reopen closed trades.
- **Probabilities & Quantitative Analyzer**: Dedicated dashboard calculating exact consecutive drawdown streak probabilities using recurrence relations. Includes comprehensive educational math guides on Geometric Brownian Motion (GBM), Log-normal Distributions, Probability of Profit (PoP), and Expected Value (EV).
- **Dashboard & Analytics**: Track performance metrics such as Win Rate, Profit Factor, cumulative Net P&L equity curves, and grouped statistics by strategy, category, and DTE cohorts. Includes an integrated S&P 500 market context comparison (matching timeframe returns, moving average momentum trends, and historical monthly seasonality charts).
- **Pre-Trade Checklist & Education**: Interactive framework checklists with automated progress tracking, educational guides on cognitive biases, trading psychology, and dynamic extrinsic value decay curves.
- **PDF & CSV Export**: Export comprehensive PDF reports with tabular trade summaries, month-by-month performance tables, and raw data to CSV formats.

## Tech Stack

- **Frontend / UI**: [Streamlit](https://streamlit.io/)
- **Data & Math**: Pandas, NumPy, SciPy (Log-normal distribution models)
- **Charting**: Plotly
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **Market Data**: yfinance, Barchart API (via custom Python requests session with token generation)
- **PDF Generation**: `fpdf2`

## Project Structure

```text
finance/
├── Home.py                 # Main Streamlit entry point / Navigation router
├── docker-compose.yml      # PostgreSQL database container configuration
├── requirements.txt        # Python dependencies
├── README.md               # Project documentation
├── pages/
│   ├── 0_Home_Content.py   # Home page content
│   ├── 1_Trade.py          # Trade recommendation wizard, trade entry form, and payoff chart
│   ├── 2_Journal.py        # Ledger of saved trades (pagination, filters, bulk delete)
│   ├── 3_Open_Trades.py    # Live open trades tracker, P&L estimator, and health dashboard
│   ├── 4_Closed Trades Review.py # High-level performance metrics and dashboards
│   ├── 5_Close Trade.py    # Hidden navigation tab for executing closing transactions
│   ├── 6_Research.py       # Market research tools and data integration
│   ├── 7_Export.py         # Dynamic PDF Report generation and downloading
│   ├── 8_Framework.py      # Interactive pre-trade checklists and mindset guidelines
│   ├── 9_Strategies.py     # Responsive reference tables and setup rules
│   ├── 10_Probabilities.py # Interactive streak calculator and quantitative math guide
│   ├── 11_DCF_Evaluation.py # Dynamic 10-Year multi-scenario DCF models, growth decay patterns, & Reverse DCF bisection solver
│   ├── 12_Trade_Details.py # Detailed view of individual trades and leg history
│   └── 13_Update_Trade.py  # Hidden navigation tab for editing existing trades
└── src/
    ├── db.py               # Database connection, finance schema setup, and session management
    ├── market_data.py      # yfinance API wrappers
    ├── models.py           # SQLAlchemy ORM models (Portfolio, Trade, Leg, Transaction)
    ├── options_math.py     # Complex payoff calculations, standard deviation logic, and Black-Scholes derivations
    └── trade_screener.py   # Trade permutation generation, criteria screening, and ranking engine
```

## Installation & Setup

### 1. Prerequisites
- Python 3.10+
- Docker & Docker Compose (for the PostgreSQL database)

### 2. Install Dependencies
Create a virtual environment (recommended) 
```bash
python -m venv .venv
```

Activate it

Bash
```bash
source .venv/bin/activate
```
Powershell
```powershell
.venv\Scripts\Activate.ps1
```

and install the required packages:
```bash
pip install -r requirements.txt
```

### 3. Start the Database
The project requires a PostgreSQL database. A `docker-compose.yml` file is provided to spin one up instantly:
```bash
docker-compose up -d
```
You can also just install the database on your local computer with the right user and password.

*This exposes PostgreSQL on `localhost:5432` with user `postgres` and password `pg`.*

### 4. Run the Application
Launch the Streamlit web interface:
```bash
streamlit run {path_to_the_repo}\Home.py
```
