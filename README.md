# Options Trading Journal & Analyzer

A local, Python-based web application built with Streamlit to track, journal, and analyze complex options trading strategies. The application provides real-time market data integration, advanced payoff visualization, and probability metrics based on log-normal distributions.

## Features

- **Strategy Builder**: Construct multi-leg options strategies (up to 8 legs).
- **Interactive UI**: Custom styled toggle buttons for "Buy/Sell" and "Call/Put" to easily build spreads, condors, butterflies, etc.
- **Payoff Visualization**: Generates interactive Plotly charts showing the expected profit and loss at expiration across varying underlying prices.
- **Advanced Metrics**: 
  - Maximum Profit & Maximum Loss
  - Breakeven Points
  - Probability of Profit (PoP), Probability of Max Profit, Probability of Max Loss
  - Expected Value (EV) & Expected Return
  - Risk to Reward Ratio
  - Dynamic Collateral Calculation (Max Loss * 1.6)
  - Auto-calculated commissions and net trade costs
- **Market Data**: Integrates with `yfinance` to fetch live underlying prices and ticker metadata.
- **Journal & Dashboard**: Save trades to a local PostgreSQL database, view your active journal, and manage historical performance.

## Tech Stack

- **Frontend / UI**: [Streamlit](https://streamlit.io/)
- **Data & Math**: Pandas, NumPy, SciPy (Log-normal distribution models)
- **Charting**: Plotly
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **Market Data**: yfinance

## Project Structure

```text
finance/
├── app.py                  # Main Streamlit entry point
├── docker-compose.yml      # PostgreSQL database container configuration
├── requirements.txt        # Python dependencies
├── README.md               # Project documentation
├── pages/
│   ├── 1_Trade.py          # Trade entry, strategy builder, and payoff chart
│   ├── 2_Journal.py        # Ledger of saved trades with delete functionality
│   └── 3_Dashboard.py      # High-level performance metrics
└── src/
    ├── db.py               # Database connection and session management
    ├── market_data.py      # yfinance API wrappers
    ├── models.py           # SQLAlchemy ORM models (Trade, Leg, Transaction)
    └── options_math.py     # Payoff arrays, EV, and Probability calculations
```

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
streamlit run app.py
```

## Calculations & Math

- **Probability Models**: The app uses the `scipy.stats.norm` module to calculate the log-normal Probability Density Function (PDF) of the underlying asset at expiration, factoring in Days to Expiration (DTE), the risk-free rate, and Implied Volatility (IV).
- **Expected Value (EV)**: The integral (sum across price steps) of the strategy's payoff multiplied by the theoretical probability of the underlying reaching that price.
- **Collateral**: For net credit trades, the collateral is calculated as `Maximum Potential Loss * 1.6`. If the trade involves no potential loss or is a net debit, collateral evaluates to `$0.00`.
- **Commissions**: Defaults to `$0.65` per options contract leg.

## Future Enhancements
- Integration with live options chains to automatically pull leg prices, IV, and Delta.
- Partial close tracking and rolling mechanisms.
- Historical equity curve generation on the Dashboard.
- USD/CAD currency conversion toggle.
