# Options Trading Journal & Analyzer

A local, Python-based web application built with Streamlit to track, journal, and analyze complex options trading strategies. The application provides real-time market data integration, advanced payoff visualization, and probability metrics based on log-normal distributions.

## Features

- **Portfolio Management**: Create, switch between, and delete multiple distinct portfolios. Trades, journal entries, and dashboards are dynamically filtered based on the active portfolio.
- **Strategy Builder**: Construct multi-leg options strategies (up to 8 legs).
- **Interactive UI**: Custom styled toggle buttons for "Buy/Sell" and "Call/Put" to easily build spreads, condors, butterflies, etc.
- **Payoff Visualization**: Generates interactive Plotly charts showing the expected profit and loss at expiration across varying underlying prices.
- **Advanced Metrics**: 
  - Maximum Profit & Maximum Loss
  - Breakeven Points
  - Probability of Profit (PoP), Probability of Loss (PoL), Probability of Max Profit, Probability of Max Loss
  - Expected Value (EV) & Expected Return
  - Risk to Reward Ratio
  - Dynamic Collateral Calculation (Max Loss * 1.6)
  - Auto-calculated commissions and net trade costs
  - Return on Investment (ROI)
  - 1 Standard Deviation & 2 Standard Deviation Expected Move Overlays
- **Market Data**: Integrates with `yfinance` to fetch live underlying prices and ticker metadata, and `Barchart` for highly-accurate real-time options chain data (Prices, Bid/Ask, and IV).
- **Trade Management**: Edit open trades dynamically and easily record closing transactions (for profit, loss, rolling, or expiration).
  - **Reopen Trades**: Un-stack and reverse accidental or temporary closing transactions directly from the Journal, restoring the trade to its open state with full accuracy.
- **Journal & Ledger**: 
  - Save trades to a local PostgreSQL database (`finance` schema).
  - View trades with pagination, sorting, and dynamic filtering (Ticker, Date, Status, Strategy).
  - Bulk management with "Select All Filtered", "Deselect All", and bulk delete functionality.
  - Live "Current Price", "Break-Even", and real-time Probability metrics comparison to monitor active trades.
- **Dashboard**: Advanced performance analytics based on actual closed and open trades.
  - Interactive cumulative Net PnL equity curve over time.
  - Key Aggregate Metrics: Win Rate, Average Win/Loss, Net PnL, Total Commission, Premium Collected vs Paid.
  - Filterable by Date Interval (Last 7 days, 3 Months, YTD, etc.) and Trade Status.
  - Detailed grouped breakdowns by Strategy, Category, Expected Move, and dynamic DTE (Days to Expiration) ranges.

## Tech Stack

- **Frontend / UI**: [Streamlit](https://streamlit.io/)
- **Data & Math**: Pandas, NumPy, SciPy (Log-normal distribution models)
- **Charting**: Plotly
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **Market Data**: yfinance, Barchart API (via custom Python requests session with token generation)

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
│   ├── 3_Dashboard.py      # High-level performance metrics
│   └── 4_Close Trade.py    # Hidden navigation tab for executing closing transactions
└── src/
    ├── db.py               # Database connection, finance schema setup, and session management
    ├── market_data.py      # yfinance API wrappers
    ├── models.py           # SQLAlchemy ORM models (Portfolio, Trade, Leg, Transaction)
    └── options_math.py     # Payoff arrays, EV, and Probability calculations
```

## Future Improvements
- **Automated Trade Input**: Implement a feature to automatically parse, import, and input trade information directly by copy-pasting raw text data straight from broker platforms.

## Installation & Setup

### 1. Prerequisites
- Python 3.10+
- Docker & Docker Compose (for the PostgreSQL database)

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
- **Expected Value (EV)**: The integral (sum across price steps) of the strategy's payoff multiplied by the theoretical probability of the underlying reaching that price.
- **Collateral**: For net credit trades, the collateral is calculated as `Maximum Potential Loss * 1.6`. If the trade involves no potential loss or is a net debit, collateral evaluates to `$0.00`.
- **Commissions**: Defaults to `$0.65` per options contract leg.
- **DTE Categorization**: Automatically categorizes trades by Days to Expiration based on the earliest expiring leg into custom cohorts (`0 DTE`, `1-3 DTE`, `4-7 DTE`, `8-20 DTE`, `21-60 DTE`, `61-200 DTE`, `201+ DTE`).

## Recent Updates

**Session Date: 2026-06-29**
- **Dynamic Research Hub**: Created a new compact, 3-column "Research" tab featuring dynamic URL generation for tickers (Barchart, MarketBeat, Yahoo Finance, etc.) alongside curated static links for screeners, earnings, and sentiment analysis tools.
- **Reporting & Export**: Implemented a comprehensive `fpdf2` PDF Export engine. Users can now filter trades and generate a printable, landscape-oriented PDF that perfectly captures Key Metrics, Month-by-Month breakdowns, and full tabular data layouts with proper Unicode sanitization.
- **Dashboard UI Optimization**: Overhauled the Dashboard styling by replacing raw text with compact, custom-styled CSS metric cards, dynamic colorization rules (red/yellow/green for batting averages and PnL), and shifting filters from the sidebar into a unified top-row header.
- **Improved Visualizations**: Upgraded the Equity Curve graph to scale dynamically across minimum 1-year timelines, converted X-axis to clean Month/Year timestamps, and applied a visually soothing semi-transparent green styling.

**Session Date: 2026-06-27**
- **Dashboard & Analytics Implementation**: Fully built out the Dashboard tab to provide comprehensive performance insights.
  - Interactive Plotly equity curve mapping cumulative PnL over time.
  - High-level metrics tracking batting average, average win/loss sizes, net premium flow, and commissions.
  - Grouped analysis tables allowing users to drill down performance by Strategy Type, Category, Expected Move, and dynamically calculated DTE cohorts.
  - Fully reactive UI driven by granular Date Interval and Trade Status filters.
- **Trade Lifecycle Controls**: 
  - Overhauled the "Close Trade" view to prominently display immutable trade statistics, expected probabilities, legs, and entry metrics as a read-only receipt before confirming a close transaction.
  - Engineered a "Reopen" workflow in the Journal. If a trade is erroneously closed, users can dynamically un-stack the closing transaction and instantly restore the trade to an active "Open" state without data loss.

**Session Date: 2026-06-24**
- **Dependency Resolution**: Fixed a compatibility issue between `uvicorn` and `websockets` that caused Streamlit to crash on startup. 
- **UI Enhancements**: 
  - Fixed a LaTeX rendering bug that caused multiple dollar signs (e.g., in breakeven prices) to render as math blocks in Streamlit.
  - Revamped the Journal page loading sequence: a central spinner now displays while fetching live pricing and metrics, rendering the table all at once instead of loading row-by-row.
  - Upgraded the Journal's "Details" button logic so opening a trade's details automatically closes any other expanded panels.

**Session Date: 2026-06-21**
- **Portfolio Management**: Implemented support for multiple portfolios. Users can now create, switch between, and delete entire portfolios from the sidebar. The Trade, Journal, and Dashboard pages now automatically filter their context to only display information corresponding to the actively selected portfolio.
- **Live Options Data**: Integrated with `yfinance` to fetch live options chain data (bid, ask, last price, and IV) on-demand in the Trade menu.
- **Realistic Pricing**: Upgraded the pricing logic to automatically use the current *bid* price for selling legs and the current *ask* price for buying legs, reflecting real-world market mechanics.
- **Dynamic Delta**: Added real-time Black-Scholes Delta calculations for individual options legs.
- **Journal Enhancements**: 
  - Added a "Strategy" filter to quickly find specific types of trades.
  - Implemented "Select All Filtered" and "Deselect All" capabilities to make bulk deletion seamless.
  - Upgraded the Metrics Comparison tool in trade details to calculate current live probabilities (PoP, Max Profit, Max Loss) using real-time options data rather than approximated opening costs.

**Session Date: 2026-06-20**
- **Database Schema Update**: Added `underlying_price_at_open`, `probability_max_profit`, and `probability_max_loss` to the `Trade` model to capture and persist the exact state of the underlying asset and probabilities at the time the trade is opened.
- **Data Persistence Fixes**: Ensured that Numpy types (`np.float64`) calculated by `scipy` are properly cast to standard Python `float` types before saving to PostgreSQL via SQLAlchemy, preventing `psycopg2` serialization schema errors.
- **Journal UI Enhancements**:
  - Replaced the static, bulky expander layout in the Journal with a compact "**Details**" toggle button.
  - Clicking "Details" drops down a clear table of the trade's specific legs.
  - Added a side-by-side **Metrics Comparison** component inside the details view that dynamically calculates the delta between the *current* metrics (POP, Max Profit/Loss probability, Underlying Price) and the *opening* metrics persisted in the database.
  - Fixed a bug where total trade cost was incorrectly applied in full to every leg during current metric recalculation; net cost is now evenly distributed across legs to produce accurate current payoff metrics.

**Session Date: 2026-06-26**
- **High-Precision Data Persistence**: 
  - Upgraded the database schema and `Leg` model to natively store exact values for `price` (3 decimal places), `delta` (4 decimal places), and `iv` (Implied Volatility).
  - Executed a migration strategy to sanitize legacy database records, replacing missing (`NULL`) historical leg data with strict zeroes to prevent application crashes and UI rendering issues.
- **Accurate Edit & Journal Workflows**: 
  - Eradicated approximate math estimations (like dividing total cost by leg count). The app now strictly trusts and surfaces the exact database values.
  - Expanding a trade in the Journal now precisely displays the stored Price, Delta, and IV for each leg.
  - Editing a trade securely pulls these highly precise figures back into the UI. Legacy trades seamlessly fallback to `0.0` to allow the user to easily input their exact historical data and permanently save it.
- **UI Precision Formatting**: Upgraded Streamlit number inputs across the Trade page to support, display, and capture the new fractional decimal precision.
