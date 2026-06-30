# Options Trading Journal & Analyzer

A local, Python-based web application built with Streamlit to track, journal, and analyze complex options trading strategies. The application provides real-time market data integration, advanced payoff visualization, and probability metrics based on log-normal distributions.

## Features

- **Portfolio Management**: Create, switch between, and delete multiple distinct portfolios. Trades, journal entries, and dashboards are dynamically filtered based on the active portfolio.
- **Strategy Builder**: Construct multi-leg options strategies (up to 8 legs).
  - Comprehensive strategy classification with explicit Debit/Credit designations (e.g., *Bull Put Spread (credit)*, *Iron Condor (debit)*).
  - Flexible, accurate contract quantity sizing per leg.
- **Automated Trade Input (OCR)**: Seamlessly copy a screenshot of your broker's trade confirmation to your clipboard and click one button to instantly extract the ticket data using Optical Character Recognition (Tesseract-OCR) and automatically populate all trade legs and pricing in the UI. Supports parsing both complex multi-leg groupings (like Iron Condors) and detailed single-contract order screens.
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
  - Performance-optimized data fetching (bypasses live API calls for closed trades).
  - Live "Current Price", "Break-Even", and real-time Probability metrics comparison to monitor active trades.
  - Responsive table layout handling large dollar amounts seamlessly.
- **Dashboard & Analytics**: Advanced performance analytics based on actual closed and open trades.
  - Interactive cumulative Net PnL equity curve over time.
  - Key Aggregate Metrics: Win Rate, Average Win/Loss, Net PnL, Total Commission, Premium Collected vs Paid.
  - Filterable by Date Interval (Last 7 days, 3 Months, YTD, etc.) and Trade Status.
  - Detailed grouped breakdowns by Strategy, Category, Expected Move, and dynamic DTE (Days to Expiration) ranges.
- **PDF Export**: Instantly generate and download multi-page PDF performance reports summarizing your filtered trading statistics and individual trade logs, complete with responsive column layouts and automatic pagination.

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
│   ├── 3_Dashboard.py      # High-level performance metrics
│   ├── 4_Close Trade.py    # Hidden navigation tab for executing closing transactions
│   ├── 5_Research.py       # Market research tools and data integration
│   ├── 6_Export.py         # Dynamic PDF Report generation and downloading
│   ├── 7_Framework.py      # Interactive pre-trade checklists and mindset guidelines
│   └── 8_Strategies.py     # Responsive reference tables and setup rules
└── src/
    ├── db.py               # Database connection, finance schema setup, and session management
    ├── market_data.py      # yfinance API wrappers
    ├── models.py           # SQLAlchemy ORM models (Portfolio, Trade, Leg, Transaction)
    └── ocr_parser.py       # Tesseract-OCR clipboard image processing and Regex pattern matching
```

## Future Improvements
- Implement interactive paper-trading tracking to simulate portfolio margin utilization.

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
- **Expected Value (EV)**: The integral (sum across price steps) of the strategy's payoff multiplied by the theoretical probability of the underlying reaching that price.
- **Collateral**: For net credit trades, the collateral is calculated as `Maximum Potential Loss * 1.6`. If the trade involves no potential loss or is a net debit, collateral evaluates to `$0.00`.
- **Commissions**: Defaults to `$0.65` per options contract leg.
- **DTE Categorization**: Automatically categorizes trades by Days to Expiration based on the earliest expiring leg into custom cohorts (`0 DTE`, `1-3 DTE`, `4-7 DTE`, `8-20 DTE`, `21-60 DTE`, `61-200 DTE`, `201+ DTE`).

## Recent Updates

**Session Date: 2026-06-30**
- **Trade Close Types Expansion**: Added `"Closed by stop-loss"` to the closing options types. Adjusted the Landscape PDF layout width limit for the Status column from 18 to 20 characters to ensure the longer stop-loss labels do not undergo truncation in reports.
- **Interactive Checklists (Framework)**: Built an interactive, state-preserving, and highly responsive Investment Checklist system (`pages/7_Framework.py`) featuring automated progress bars, real-time completeness percentage calculators, expandable category panels, and robust global reset controls ("Uncheck all" callbacks).
- **Core Guidelines & Mindset**: Fully synthesized detailed, readable analyses on Cognitive Biases (Confirmation, Loss Aversion, Recency, Anchoring, Overconfidence), the Psychology of Money, and The Intelligent Investor key takeaways.
- **Dynamic Options Curves**: Plotted a responsive, high-performance Plotly visualization mapping the exponential curve of Option Extrinsic Value against Days to Expiration (DTE), highlighting the 30-45 DTE acceleration and the structural Theta cliff.
- **Option Strategies Playbook**: Created an interactive Strategies deck (`pages/8_Strategies.py`) compiling quick-reference summaries and exhaustive rulesets (Stock Picking, Risk Management, Exit Triggers, Take Profits, and Follow-ups) for spreads (Bull Call, Bear Put, Bear Call, Bull Put) and Iron Condors. Designed using responsive HTML/CSS layouts with adaptive dark/light forest green headers and credit/debit indicators.
- **Streamlit Widget Session State Resolutions**: Resolved several widget warning messages occurring in the Trade and Journal pages caused by duplicate default value overrides on session-state-bound input keys.

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
