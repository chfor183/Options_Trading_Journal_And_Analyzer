# Options Trading Journal & Analyzer

A local, Python-based web application built with Streamlit to track, journal, and analyze complex options trading strategies. The application provides real-time market data integration, advanced payoff visualization, and probability metrics based on log-normal distributions.

## Features

- **Portfolio Management**: Create, switch between, and manage multiple portfolios with dynamic filtering across all dashboards.
- **Strategy Builder & Visualizer**: Construct multi-leg options strategies (up to 8 legs) with accurate quantity sizing. Generates interactive Plotly payoff charts (expiration & T+0 curves) with standard deviation overlays.
- **Automated OCR Trade Input**: Instantly parse TWS/Interactive Brokers screenshots from your clipboard to extract trade legs, prices, and tickers automatically.
- **Advanced Probability & Quant Metrics**: Calculates Probability of Profit (PoP), Probability of Loss (PoL), Probability of Max Profit/Loss, Expected Value (EV), and ROI based on log-normal distribution models.
- **Discounted Cash Flow (DCF) Evaluation**: A highly sophisticated valuation engine featuring a **10-Year 2-Stage Unlevered Free Cash Flow (FCFF) model** with linear tapering in Years 6-10. Includes:
  - **Live Financial Data Extraction**: Pre-populates default starting FCF, outstanding shares, cash, debt, and beta directly from annual balance sheets and cash flow statements via `yfinance`.
  - **Dynamic WACC Calculator**: Estimator based on the Capital Asset Pricing Model (CAPM) using live market-capitalized debt/equity weights, beta, tax rates, risk-free rates, and equity risk premiums.
  - **Tightly Coupled Growth Scenarios**: Side-by-side comparison of Conservative (80% of consensus growth, +0.5% discount), Base Case (consensus analyst estimates), and Aggressive (115% of consensus growth, -0.5% discount) scenarios.
  - **Reverse DCF (Market-Implied Expectations)**: Uses a fast binary search algorithm to solve for the exact growth rate priced into the current stock price, revealing whether expectations are overhyped or undervalued compared to analyst consensus.
  - **Plotly Visualizations**: Elegant line charts tracking historical Free Cash Flows alongside forward projections, and vertical bar charts highlighting scenario valuations against current prices and Wall Street target consensus lines.
- **Real-Time Market Data**: Integrates with `yfinance` and `Barchart` to fetch live underlying prices, ticker metadata, and real-time options chain data.
- **Trading Journal & Ledger**: Local PostgreSQL database integration tracking open/closed trades with custom pagination, sorting, dynamic filters (status, debit/credit, ticker), and bulk management. Includes a mechanism to seamlessly reopen closed trades.
- **Probabilities & Quantitative Analyzer**: Dedicated dashboard calculating exact consecutive drawdown streak probabilities using recurrence relations. Includes comprehensive educational math guides on Geometric Brownian Motion (GBM), Log-normal Distributions, Probability of Profit (PoP), and Expected Value (EV).
- **Dashboard & Analytics**: Track performance metrics such as Win Rate, Profit Factor, cumulative Net P&L equity curves, and grouped statistics by strategy, category, and DTE cohorts.
- **Pre-Trade Checklist & Education**: Interactive framework checklists with automated progress tracking, educational guides on cognitive biases, trading psychology, and dynamic extrinsic value decay curves.
- **PDF & CSV Export**: Export comprehensive PDF reports with tabular trade summaries, month-by-month performance tables, and raw data to CSV formats.

## Tech Stack

- **Frontend / UI**: [Streamlit](https://streamlit.io/)
- **Data & Math**: Pandas, NumPy, SciPy (Log-normal distribution models)
- **Charting**: Plotly
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **Market Data**: yfinance, Barchart API (via custom Python requests session with token generation)
- **OCR Processing**: `pytesseract` and `Pillow` (requires local Tesseract-OCR installation)
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
│   ├── 1_Trade.py          # Trade entry, editing, and payoff chart
│   ├── 2_Journal.py        # Ledger of saved trades (pagination, filters, bulk delete)
│   ├── 3_Open_Trades.py    # Live open trades tracker, P&L estimator, and health dashboard
│   ├── 4_Closed Trades Review.py # High-level performance metrics and dashboards
│   ├── 5_Close Trade.py    # Hidden navigation tab for executing closing transactions
│   ├── 6_Research.py       # Market research tools and data integration
│   ├── 7_Export.py         # Dynamic PDF Report generation and downloading
│   ├── 8_Framework.py      # Interactive pre-trade checklists and mindset guidelines
│   ├── 9_Strategies.py     # Responsive reference tables and setup rules
│   ├── 10_Probabilities.py # Interactive streak calculator and quantitative math guide
│   └── 11_DCF_Evaluation.py # Dynamic 10-Year 2-Stage DCF scenarios & Reverse DCF analyzer
└── src/
    ├── db.py               # Database connection, finance schema setup, and session management
    ├── market_data.py      # yfinance API wrappers
    ├── models.py           # SQLAlchemy ORM models (Portfolio, Trade, Leg, Transaction)
    └── ocr_parser.py       # Tesseract-OCR clipboard image processing and Regex pattern matching
```

## Installation & Setup

### 1. Prerequisites
- Python 3.10+
- Docker & Docker Compose (for the PostgreSQL database)
- **Tesseract-OCR**: Required for the clipboard image parsing feature. [Download the Windows installer here](https://github.com/UB-Mannheim/tesseract/wiki) and ensure it is added to your system PATH (or installed in the default `C:\Program Files\Tesseract-OCR\` directory).

### 2. Install Dependencies
Create a virtual environment (recommended) and install the required packages:
```bash
pip install -r requirements.txt
```

### 3. Start the Database
The project requires a PostgreSQL database. A `docker-compose.yml` file is provided to spin one up instantly:
```bash
docker-compose up -d
```
*This exposes PostgreSQL on `localhost:5432` with user `postgres` and password `pg`.*

### 4. Run the Application
Launch the Streamlit web interface:
```bash
streamlit run C:\Lab\finance\Home.py
```

## Calculations & Math

- **Probability Models**: The app uses the `scipy.stats.norm` module to calculate the log-normal Probability Density Function (PDF) of the underlying asset at expiration, factoring in Days to Expiration (DTE), the risk-free rate, and Implied Volatility (IV).
- **Probability of Profit (PoP)**: Calculated by numerically integrating the area under the curve of the log-normal probability distribution of the stock price at expiration across all profitable price ranges (i.e. where the expiration payoff is greater than $0$).
  - **Distribution Parameters**: 
    $$\mu = \ln(S_0) + \left(r - \frac{1}{2}\sigma^2\right) \cdot t$$
    $$\sigma_{dist} = \sigma \cdot \sqrt{t}$$
    Where $S_0$ is the current spot price, $r$ is the risk-free rate (hardcoded at $5\%$), $\sigma$ is the mean Implied Volatility of all legs, and $t$ is the time to maturity in years.
  - **Probability Density Function (PDF)**:
    $$f(S) = \frac{1}{S \sigma_{dist} \sqrt{2\pi}} e^{-\frac{(\ln(S) - \mu)^2}{2\sigma_{dist}^2}}$$
  - **Numerical Integration**:
    $$\text{PoP} = \sum_{S: \text{Payoff}(S) > 0} f(S) \cdot \Delta S$$
    The app generates a dense grid of $10,000$ points spanning from $1\%$ to $400\%$ of the current stock price, calculates the payoff at each price point, and sums the corresponding probability slices where the net trade payoff is positive.
- **Expected Value (EV)**: The integral (sum across price steps) of the strategy's payoff multiplied by the theoretical probability of the underlying reaching that price.
- **Collateral**: For net credit trades, the collateral is calculated as `Maximum Potential Loss * 1.6`. If the trade involves no potential loss or is a net debit, collateral evaluates to `$0.00`.
- **Commissions**: Defaults to `$0.65` per options contract leg.
- **DTE Categorization**: Automatically categorizes trades by Days to Expiration based on the earliest expiring leg into custom cohorts (`0 DTE`, `1-3 DTE`, `4-7 DTE`, `8-20 DTE`, `21-60 DTE`, `61-200 DTE`, `201+ DTE`).
