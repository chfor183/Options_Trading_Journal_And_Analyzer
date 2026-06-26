import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Date, Boolean, MetaData, Numeric
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime

metadata = MetaData(schema="finance")
Base = declarative_base(metadata=metadata)

class Portfolio(Base):
    __tablename__ = 'portfolios'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255))
    
    trades = relationship("Trade", back_populates="portfolio", cascade="all, delete-orphan")

class Trade(Base):
    __tablename__ = 'trades'
    id = Column(Integer, primary_key=True)
    portfolio_id = Column(Integer, ForeignKey('portfolios.id'))
    ticker = Column(String(10), nullable=False)
    underlying_name = Column(String(100))
    category = Column(String(50))
    strategy_type = Column(String(50))
    expected_move = Column(String(50))
    idea_url = Column(String(255))
    date_opened = Column(DateTime, default=datetime.utcnow)
    collateral = Column(Float)
    status = Column(String(20), default="Open")
    
    # Calculated Fields (could be calculated dynamically, but stored for easy querying)
    max_profit = Column(Float)
    max_loss = Column(Float)
    probability_of_profit = Column(Float)
    probability_of_loss = Column(Float)
    probability_max_profit = Column(Float)
    probability_max_loss = Column(Float)
    expected_value = Column(Float)
    underlying_price_at_open = Column(Float)
    
    portfolio = relationship("Portfolio", back_populates="trades")
    legs = relationship("Leg", back_populates="trade", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="trade", cascade="all, delete-orphan")

class Leg(Base):
    __tablename__ = 'legs'
    id = Column(Integer, primary_key=True)
    trade_id = Column(Integer, ForeignKey('trades.id'))
    strike = Column(Float, nullable=False)
    expiry = Column(Date, nullable=False)
    option_type = Column(String(10), nullable=False) # 'Call' or 'Put'
    position = Column(String(10), nullable=False) # 'Long' or 'Short'
    price = Column(Numeric(10, 3))
    delta = Column(Numeric(10, 4))
    iv = Column(Numeric(10, 4))
    
    trade = relationship("Trade", back_populates="legs")

class Transaction(Base):
    __tablename__ = 'transactions'
    id = Column(Integer, primary_key=True)
    trade_id = Column(Integer, ForeignKey('trades.id'))
    date = Column(DateTime, default=datetime.utcnow)
    action = Column(String(50), nullable=False) # 'Open', 'Partial Close', 'Close', 'Roll'
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False) # Cost per contract: Debit(-), Credit(+)
    commission = Column(Float, default=0.0)
    
    trade = relationship("Trade", back_populates="transactions")
