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
  - **Single-Column Sorting**: Column headers in the Trading Journal can be clicked to toggle sorting (Ascending/Descending), with a clean, flat aesthetic.
  - **Sequential Trade Numbering**: Dynamically maps and permanently stores a chronological trade number (`#`) for every trade per-portfolio, displaying it as the first column after the select boxes.
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

**Session Date: 2026-07-02**
- **PDF Export Enhancements**:
  - **Sequential Trade IDs in PDF**: Added the persistent sequential `trade_number` (`#`) column as the very first column of the "Trades List" section in the exported PDF reports.
  - **Grid Realignment & Precise Sizing**: Recalculated and optimized the horizontal column widths of the Landscape PDF layout (e.g. allocating `12` width to `#`) to prevent any overflow or boundary clipping.
  - **Comprehensive Table Totals**: Implemented an automated summation row at the bottom of the "Trades List" table in the PDF export. This row dynamically aggregates and cleanly prints the sum of **Cost**, **Close**, **PnL**, and **Comm.** across all displayed trades, complete with safety boundary checks to handle multi-page overflow cleanly.
- **Trade Page Auto-Fill Improvements**:
  - Resolved an issue on the Trade page where changing the ticker input did not automatically update the **Name of Underlying** box. Configured an active state comparison check against `st.session_state["last_ticker"]` to programmatically trigger metadata fetches and update `"name_val"` reactively.
- **Journal Layout & Navigation Overhauls**:
  - Overhauled **Save Trade** and **Update Trade** buttons to follow the bottom-right corner of the viewport using a fixed overlay style (`position: fixed`) and styled them in a professional Forest Green (`#2e7d32`) theme with a clean drop shadow and hover scaling effects. Configured the buttons with a standard width of exactly `190px`.
  - Added seamless post-save routing: after successfully saving or updating a trade, the application automatically redirects the trader to the **Journal** page via `st.switch_page`.
- **Trading Journal Persistent Sequential IDs**:
  - Added a permanent chronological `trade_number` attribute to the `Trade` model in SQL database storage.
  - Implemented an automated schema migration in `src/db.py` to auto-detect and append the new column safely, alongside a chronological sequence backfill script for existing historical records.
  - Configured automatic incremental sequence assignment on save based on the highest existing trade number in that portfolio.
  - Placed the `#` column in the journal table header directly following the bulk select checkboxes.
- **Dynamic Multi-Column Header Sorting**:
  - Implemented single-column sorting for the Trading Journal by clicking directly on the column headers (e.g. Ticker, Name, Date Opened, Strategy, DTE, Cost, PnL, Status).
  - Designed flat, borderless, bold clickable header text using native Streamlit buttons styled via dynamic CSS overrides inside a parent document observer.
  - Retained clean reading by making the font size of other columns' sorting indicators look subtle, and further reduced the font size of non-sortable columns (such as Break-Even, Current/Closed Price, Details, Edit, and Action) to a highly distinct `13px` weight.
- **Expected Move Pine Script Visualization**:
  - Enhanced the Pine Script v5 trading visualizer with parsed `"expected_move"` inputs from your copied Streamlit trade details.
  - Displays upper and lower expected move standard deviation boundary lines along with translucent purple shaded channel fills directly inside TradingView.
  - Automatically exports `"expected_move"` in the TradingView Pine Script JSON panel of the expandable Details card in your journal.

**Session Date: 2026-07-01**
- **Option Strategies Playbook & Interactive Explorer Overhaul**:
  - **Dynamic Multi-Button Selector**: Replaced the previous `st.selectbox` strategy detail dropdown with an intuitive, interactive, and high-density horizontal 10-button selector organized into distinct category rows (Row 1 for **Debit Strategies**, Row 2 for **Credit Strategies**).
  - **Active State Highlights**: Styled the selected active button to explicitly render in **Forest Green** (`#2e7d32`) with custom hover, active, and focus background animations, contrasting beautifully against secondary gray option buttons.
  - **Symmetrical Covered Call Curve**: Overhauled the mathematical model for **Covered Call [Credit]** so it is a mirrored, synthetically identical equivalent to the **Cash-Secured Put [Credit]** but with its profit zone oriented properly to the left.
  - **Premium Buyer Disadvantage Visualizer**: Adjusted the payoff bounds and formulas for both the **Bull Call Spread [Debit]** and **Bear Put Spread [Debit]** graphs to represent premium drag. The current price line now aligns flawlessly with the exact max loss pivot point of the expiration curve, clearly communicating that debit premium buyers start with a minor structural deficit.
- **Windows Startup & "First of the Day" Bug Fix**:
  - **Silenced Telemetry Crash**: Added `.streamlit/config.toml` to disable the automatic daily background update and telemetry checks (`gatherUsageStats = false`) that crashed the Streamlit server on first boot.
  - **Selector Event Loop Workaround**: Configured a platform check at the head of `Home.py` to use `WindowsSelectorEventLoopPolicy` instead of the default `ProactorEventLoop` to solve the Python 3.8+ Windows event loop shutdown crash (`RuntimeError: Event loop is closed`). Wrapped inside `warnings.catch_warnings()` context to silently bypass deprecation warnings on newer Python engines.
- **TradingView Pine Script Integration**:
  - **Options Strategy Visualizer**: Created a versatile **Pine Script v5** indicator in `assets/pinescript` that parses option strategy details in a clean multi-line JSON format directly inside TradingView.
  - **Automatic Visual Overlays**: Draws horizontal lines at option leg strikes, dashed vertical lines at trade open and expiry dates, and highlights the target profit zones using translucent green fills.
  - **Intelligent Breakeven Lines**: Automatically calculates and draws precise breakeven lines (dotted yellow) anchored from the start of the trade, with labels positioned cleanly on the left side of the chart.
  - **Smart Scale & Premium Corrections**: Features double-sided breakevens for Iron Condor configurations and includes an intelligent auto-scaling module that handles both contract-wide total premium (e.g. `132.0`) and per-share premium (e.g. `1.32`) seamlessly.
  - **On-Screen Information Table**: Injects a sleek, screen-aligned metadata table in the top-right corner summarizing the active strategy, underlying open price, net credit/debit premium, trade duration, and Probability of Profit (POP).
  - **Streamlit Copy-Paste JSON Panel**: Embedded a copy-ready JSON generator directly into your Streamlit Journal trade details panel. It displays alongside the text-based trade idea, allowing you to instantly copy and paste structured trade parameters into your TradingView indicator.
- **Performance Optimizations (Trade & Journal Pages)**:
  - **Caching `yfinance` requests**: Cached metadata fetches (`get_ticker_info` and `get_options_chains`) in `src/market_data.py` using Streamlit's `@st.cache_data`. This speeds up page loads from ~6 seconds down to instantaneous loads (<5ms) and prevents duplicate, blocking API requests when jumping between tabs.
- **Visual Payoff Chart Overhaul**:
  - **X-Axis Expansion**: Rewrote the chart range generator so the x-axis automatically expands past its standard ±20% boundary to cover far-out Current Prices and ±1 Standard Deviation Expected Moves. This completely fixes visual truncations (goofy missing data cuts) in the profit/loss curves.
  - **Dynamic Annotation Facing**: Automatically flips the horizontal layout direction of labels (`xanchor` as `left` or `right`) based on whether the Current Price is above or below Breakeven. This prevents overlapping boxes and keeps labels visually oriented towards the empty space.
  - **Column Swap in Summary**: Swapped the columns inside the *Strategies Summary* markdown grid, moving **Strategy** to the first column position and **Category** to the second column position to emphasize action-oriented learning.
  - **Deprecation Cleanups**: Replaced all 11 instances of the deprecated `use_container_width=True` with `width='stretch'` for the Plotly charts and `st.dataframe` to future-proof the application against upcoming Streamlit releases.
- **Trading Journal Layout & Usability Improvements**:
  - **DTE Column**: Added a dedicated **DTE** (Days to Expiry) column to the Trading Journal main table immediately following the **Strategy** column, allowing quick sorting and identification of trade lifespans at a glance.
  - **Column Width Optimization**: Adjusted and expanded the overall journal table layout to make better use of widescreen layouts. Optimized columns specifically to increase breathing room for **Ticker** (+50%), **Strategy** (+36%), **PnL** (+62%), and **Name** (+63%) to prevent text overlapping and wrap-around.
  - **Button Centering & Flexbox Styling**: Addressed an alignment issue where the text on actions buttons ("Details", "Edit", "Close", "Reopen") appeared off-center. Configured explicit CSS flex centering rules (`display: flex !important; justify-content: center !important;`) applied down the button hierarchy to ensure perfect text positioning.
- **Copyable Trade Idea Refinements**:
  - Overhauled the header line of the **Copyable Trade Idea** raw text output block to act as a highly informative, clean title structured as `[Ticker] - [Strategy Type] ([DTE] DTE) @ [Cost/Premium]` without any redundant `"Title :"` or `[POP: ...]` prefixes. This ensures the output can be cleanly shared with other tools/users immediately with all necessary high-density parameters intact.
- **OCR Tutorial Modals**:
  - Overhauled the manual OCR help system, replacing the hover tooltips with Streamlit's native `@st.dialog` closable modal views for both the Multi-Leg Strategy extractor and the Single Contract Details extractor.
  - Implemented sleek "❓" help triggers that trigger centered modal overlays displaying high-fidelity screenshot tutorial guides (`Multileg_tutorial.png` and `Singleleg_tutorial.png`) paired with step-by-step usage workflows.
  - Added a distinct, prominent information banner stating that the clipboard OCR extractor feature is designed exclusively for the **Interactive Brokers Desktop App** (Trader Workstation / TWS).
  - Streamlined and narrowed the OCR action buttons row using compact, theme-aware layout columns (`[2.6, 0.5, 2.8, 0.5, 5.6]`) to eliminate unnecessary wide whitespace and align flawlessly with the Streamlit theme's styling cues.

**Session Date: 2026-06-30**
- **Home Page Redesign**:
  - Overhauled the root welcome section with a custom-styled, forest-green sidebar hero callout box showcasing the application's central design philosophy.
  - Relocated the database connection check, status, and active error warnings to the immediate top of the dashboard.
  - Implemented an interactive, highly compact **Options Trading Core Basics** block outlining Calls, Puts, Intrinsic/Extrinsic valuation breakdowns, Bid/Ask spreads (with liquidity guidelines), and essential trading Greeks ($\Delta, \theta, \nu$).
- **Advanced Payoff Plotter Layout Enhancements**:
  - Overhauled the Options Payoff plot in `src/options_math.py` to prevent any vertical lines and labels from overlapping. Relocated the **Current Price** annotation to the top-right (`y=0.85` paper coordinates) and staggered **Breakeven** annotations sequentially along the bottom (`y=0.15 + (i * 0.1)`) with distinct alignment settings.
  - Moved the **Expected Move (±1 SD)** metric label into a stylized, non-overlapping slate background overlay card located cleanly at the top-left of the chart canvas.
  - Re-themed the Expected Move rectangle fill from orange to a high-contrast, premium **semi-transparent blue** (`rgba(59, 130, 246, 0.05)`) with dashed borders.
  - Increased the legibility of all key annotation text strings by upgrading font sizing to **12px** and applying a solid **bold** weight.
  - Tightened chart resolution by restricting the default x-axis boundaries to **±20% of the calculated Breakevens** (Lower: `min_be * 0.8`, Upper: `max_be * 1.2`), making setups highly readable and zoomed in on the active payoff channel.
- **Journal Layout Polish**:
  - Repositioned the **Idea URL** metadata link inside the Journal trade details dropdown directly above the **Copyable Trade Idea** block to create a better, more logical reading hierarchy.
- **New Trade Entries Defaults**:
  - Configured a high-probability **GLD Bull Put Spread** ($1.293 credit spread, 79.2% PoP, ±6.8% expected move) as the default layout on the Trade entry page (`pages/1_Trade.py`) to give users an instant high-quality strategy template.
- **Option Strategies Playbook & Advanced Payoff Analysis**:
  - Overhauled and shifted the **Options Theory** system from the Framework page (`pages/7_Framework.py`) to the dedicated Strategies Page (`pages/8_Strategies.py`) for better thematic grouping. Removed the "Barchart Option Filters" section to keep the module strictly focused on setups and analytics.
  - Implemented 4 new basic option strategies: **Long Call [Debit]**, **Long Put [Debit]**, **Covered Call [Credit]**, and **Cash-Secured Put [Credit]** inside the "Strategies Details" module, supporting full definitions, selection parameters, and exit setups.
  - Renamed advanced strategies to use explicit, clear transaction markers (**Short Iron Condor [Credit]** and **Long Iron Condor [Debit]**).
  - Developed a high-fidelity **Plotly Options Payoff Plotter** for all 10 strategies that includes realistic, custom mathematical curves for both *At Expiration* (solid green line) and *Current (T+0)* (dashed blue line) states.
  - Added visual-grade **Green Profit / Red Loss background fills** dynamically calculated below and above $y=0$ (PnL line) to simulate modern options-broker graphics. Removed distracting B/E lines, boosted chart vertical scale by 25% for better visibility, and annotated the active stock price directly on the curves.
  - Restructured all Strategy Summary sections to display parameters in structured, clean Markdown tables rather than raw bullets. Removed backticks to match parent Streamlit styles seamlessly.
- **Trade Close Types Expansion**: Added `"Closed by stop-loss"` to the closing options types. Adjusted the Landscape PDF layout width limit for the Status column from 18 to 20 characters to ensure the longer stop-loss labels do not undergo truncation in reports.
- **Interactive Checklists (Framework)**: Built an interactive, state-preserving, and highly responsive Investment Checklist system (`pages/7_Framework.py`) featuring automated progress bars, real-time completeness percentage calculators, expandable category panels, and robust global reset controls ("Uncheck all" callbacks).
- **Core Guidelines & Mindset**: Fully synthesized detailed, readable analyses on Cognitive Biases (Confirmation, Loss Aversion, Recency, Anchoring, Overconfidence), the Psychology of Money, and The Intelligent Investor key takeaways.
- **Dynamic Options Curves**: Plotted a responsive, high-performance Plotly visualization mapping the exponential curve of Option Extrinsic Value against Days to Expiration (DTE), highlighting the 30-45 DTE acceleration and the structural Theta cliff.
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
