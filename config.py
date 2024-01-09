# config.py
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ROOT_DIRECTORY = Path(__file__).parent.resolve()
print('ROOT_DIRECTORY: ', ROOT_DIRECTORY)

DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')

db_url = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'