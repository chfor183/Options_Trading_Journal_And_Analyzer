import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from src.models import Base

# Using PostgreSQL as per the plan
DB_USER = "postgres"
DB_PASS = "pg"
DB_HOST = "localhost:5432"
DB_NAME = "finance"

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    with engine.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS finance"))
        conn.commit()
    Base.metadata.create_all(bind=engine)
    
    # Check if trade_number column exists and alter table if not
    with engine.connect() as conn:
        res = conn.execute(text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_schema = 'finance' AND table_name = 'trades' AND column_name = 'trade_number'"
        )).fetchone()
        if not res:
            conn.execute(text("ALTER TABLE finance.trades ADD COLUMN trade_number INTEGER"))
            conn.commit()
            
            # Populate existing trade numbers chronologically for all portfolios
            db_session = SessionLocal()
            from src.models import Portfolio, Trade
            portfolios = db_session.query(Portfolio).all()
            for port in portfolios:
                trades = db_session.query(Trade).filter(Trade.portfolio_id == port.id).order_by(Trade.date_opened, Trade.id).all()
                for idx, trade in enumerate(trades):
                    trade.trade_number = idx + 1
            db_session.commit()
            db_session.close()

        # Check if expected_move column exists and rename to expected_direction if expected_direction doesn't exist
        res_move = conn.execute(text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_schema = 'finance' AND table_name = 'trades' AND column_name = 'expected_move'"
        )).fetchone()
        res_direction = conn.execute(text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_schema = 'finance' AND table_name = 'trades' AND column_name = 'expected_direction'"
        )).fetchone()
        if res_move and not res_direction:
            conn.execute(text("ALTER TABLE finance.trades RENAME COLUMN expected_move TO expected_direction"))
            conn.commit()

        # Check if underlying_price_at_close column exists and add it if not
        res_underlying_price_at_close = conn.execute(text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_schema = 'finance' AND table_name = 'trades' AND column_name = 'underlying_price_at_close'"
        )).fetchone()
        if not res_underlying_price_at_close:
            conn.execute(text("ALTER TABLE finance.trades ADD COLUMN underlying_price_at_close DOUBLE PRECISION"))
            conn.commit()

    # Create default portfolio if none exist
    db = SessionLocal()
    from src.models import Portfolio
    if db.query(Portfolio).count() == 0:
        default_portfolio = Portfolio(name="Default Portfolio", description="Automatically created default portfolio")
        db.add(default_portfolio)
        db.commit()
    db.close()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
