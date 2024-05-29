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
    coin_symbol = Column(String, nullable=False)
    coingecko_coin_id = Column(String)
    is_valid = Column(Boolean, default=False)
    buy_price = Column(String, nullable=False)
    total_quantity_value = Column(String, nullable=False)
    board_id = Column(String, nullable=False)
    board_name = Column(String, nullable=False)
    valuation_price_column_id = Column(String, nullable=False)
    percentage_change_column_id = Column(String, nullable=False)
    projected_value_column_id = Column(String, nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP, default=datetime.now, onupdate=datetime.now) 

    alerts = relationship('Alert', back_populates='coin')

    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


class Alert(Base):
    __tablename__ = 'monday_alert'
    alert_id = Column(Integer, primary_key=True, autoincrement=True)
    alert_message = Column(String, nullable=False)
    alert_type = Column(String, nullable=False)
    coin_id = Column(Integer, ForeignKey('monday_coin.coin_id'), nullable=False)  
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP, default=datetime.now, onupdate=datetime.now) 

    coin = relationship('Coin', back_populates='alerts', lazy=True) 

    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

class Board(Base):
    __tablename__ = 'monday_board'
    board_id = Column(Integer, primary_key=True, autoincrement=True)
    board_name = Column(String, nullable=False)
    monday_board_id = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP, default=datetime.now, onupdate=datetime.now) 

    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}
    

class Bot(Base):
    __tablename__ = 'nv_invest_bot'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    interval = Column(Integer, default=3)
    status = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP, default=datetime.now, onupdate=datetime.now) 

    errors = relationship('Error', back_populates='bot')

    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}
    

class Error(Base):
    __tablename__ = 'nv_invest_bot_error'
    id = Column(Integer, primary_key=True, autoincrement=True)
    bot_id = Column(Integer, ForeignKey('nv_invest_bot.id'), nullable=False) 
    description = Column(String, nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.now)

    bot = relationship("Bot", back_populates="errors")

    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

# ------------------------------ NV INVEST MONITOR BOT ---------------------------------------


class Token(Base):
    __tablename__ = 'tokens'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol=Column(String)
    name = Column(String, nullable=False)
    take_profit_1 = Column(String)
    take_profit_2 = Column(String)
    take_profit_3 = Column(String)
    take_profit_4 = Column(String)
    monday_id = Column(Integer)
    board_name = Column(String)
    average_buy_price = Column(String)
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP, default=datetime.now, onupdate=datetime.now)
    
    token_alerts = relationship('TokenAlert', back_populates='token')

    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

class TokenAlert(Base):
    __tablename__ = 'token_alerts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    token_id = Column(Integer, ForeignKey('tokens.id'), nullable=False)
    message = Column(String, nullable=False)
    type = Column(String, nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.now)
    updated_at = Column(TIMESTAMP, default=datetime.now, onupdate=datetime.now)
    
    token = relationship('Token', back_populates='token_alerts')

    def as_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}



Base.metadata.create_all(engine)

# Export the sql session
Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
session = Session()  

# Create a bot entry in the database if it does not already exist.
def create_bot_entry(name, description):

    try:
        if not session.query(Bot).filter_by(name=name).first():
            new_bot = Bot(name=name, description=description)
            session.add(new_bot)
            session.commit()
            print(f'Default Bot "{name}" Created')
    except Exception as e:
        print(f'Error creating bot "{name}". {str(e)}')


create_bot_entry("nv invest", "This bot aims to update tokens on Monday.com")
create_bot_entry("nv invest - monitor", "This bot aims to monitor prices and send alerts when take profits are hit")

