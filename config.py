# config.py
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey, create_engine, Boolean

load_dotenv()

ROOT_DIRECTORY = Path(__file__).parent.resolve()
print('ROOT_DIRECTORY: ', ROOT_DIRECTORY)

DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')

db_url = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'


engine = create_engine(db_url)
Base = declarative_base()

class Coin(Base):
    __tablename__ = 'monday_coin'
    coin_id = Column(Integer, primary_key=True, nullable=False)
    coin_name = Column(String, nullable=False)
    coingecko_coin_id = Column(String)
    is_valid = Column(Boolean, default=False)
    buy_price = Column(String, nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow) 

    alerts = relationship('Alert', back_populates='coin')


class Alert(Base):
    __tablename__ = 'monday_alert'
    alert_id = Column(Integer, primary_key=True, autoincrement=True)
    alert_message = Column(String, nullable=False)
    alert_type = Column(String, nullable=False)
    coin_id = Column(Integer, ForeignKey('monday_coin.coin_id'), nullable=False)  
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow) 

    coin = relationship('Coin', back_populates='alerts', lazy=True) 

class Board(Base):
    __tablename__ = 'monday_board'
    board_id = Column(Integer, primary_key=True, autoincrement=True)
    board_name = Column(String, nullable=False)
    monday_board_id = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow) 

    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}




Base.metadata.create_all(engine)

# Export the sql session
Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
session = Session()  
