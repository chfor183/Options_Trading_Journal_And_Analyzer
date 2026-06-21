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
