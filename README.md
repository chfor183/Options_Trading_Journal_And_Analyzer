# Options Trading Journal & Analyzer

A local, Python-based web application built with Streamlit to track, journal, and analyze complex options trading strategies. The application provides real-time market data integration, advanced payoff visualization, and probability metrics based on log-normal distributions.

## Features

- **Portfolio Management**: Create, switch between, and manage multiple portfolios with dynamic filtering across all dashboards.
- **Strategy Builder & Visualizer**: Construct multi-leg options strategies (up to 8 legs) with accurate quantity sizing. Generates interactive Plotly payoff charts (expiration & T+0 curves) with standard deviation overlays, including simultaneous dynamic tracking of **Current Expected Move** vs **Expected Move at Open**.
- **Automated OCR Trade Input**: Instantly parse TWS/Interactive Brokers screenshots from your clipboard to extract trade legs, prices, and tickers automatically.
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
│   └── 11_DCF_Evaluation.py # Dynamic 10-Year multi-scenario DCF models, growth decay patterns, & Reverse DCF bisection solver
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
- **Discounted Cash Flow (DCF) Valuation**: 
  - **Unlevered Free Cash Flow (FCFF)**: Intrinsic equity value is modeled by projecting Free Cash Flows for 10 years and discounting them to Present Value (PV) using the Weighted Average Cost of Capital (WACC), plus a discounted terminal perpetual value:
    $$\text{Enterprise Value (EV)} = \sum_{t=1}^{10} \frac{\text{FCF}_t}{(1 + d)^t} + \frac{\text{Terminal Value}_{10}}{(1 + d)^{10}}$$
    $$\text{Equity Value} = \text{EV} + \text{Cash} - \text{Debt}$$
    $$\text{Intrinsic Value per Share} = \frac{\text{Equity Value}}{\text{Shares Outstanding}}$$
    Where $d$ is the Discount Rate (WACC), and the Terminal Value (perpetual growth model) is:
    $$\text{Terminal Value}_{10} = \frac{\text{FCF}_{10} \cdot (1 + g_{\text{terminal}})}{d - g_{\text{terminal}}}$$
    *(Note: To maintain mathematical sanity, $d$ must strictly be greater than $g_{\text{terminal}}$.)*
  - **Growth Projection decay Patterns**:
    Let $g_1$ be the Initial Growth Rate (Year 1) and $g_{\text{terminal}}$ be the Perpetual Terminal Growth Rate. The projected growth rate $g_t$ for any year $t \in \{1, \dots, 10\}$ is calculated dynamically based on the selected decay pattern:
    - **Continuous Linear Decay (Decay from Year 2)**:
      $$g_t = \begin{cases} g_1 & \text{for } t = 1 \\ g_1 - \frac{t - 2}{8} \cdot (g_1 - g_{\text{terminal}}) & \text{for } t \ge 2 \end{cases}$$
    - **Delayed Linear Decay (Decay starts in Year 6)**:
      $$g_t = \begin{cases} g_1 & \text{for } 1 \le t \le 5 \\ g_1 - \frac{t - 6}{4} \cdot (g_1 - g_{\text{terminal}}) & \text{for } t \ge 6 \end{cases}$$
    - **Stable Growth (Keep Stable)**:
      $$g_t = g_1 \quad \forall t \in \{1, \dots, 10\}$$
    - **Additive Growth Step Increment (Add X% each year)**:
      $$g_t = g_1 + (t - 1) \cdot X$$
    - **Subtractive Growth Step Decrement (Remove X% each year)**:
      $$g_t = g_1 - (t - 1) \cdot X$$
  - **Reverse DCF expectations Solver**: 
    Uses a fast numerical bisection search algorithm to solve for the exact $g_1$ such that:
    $$\text{Intrinsic Value}(g_1) = \text{Current Market Price}$$
    This reverse-engineered rate represents the growth expectations priced in by the market. We also apply this to Wall Street target mean prices to determine the consensus market expectation.
