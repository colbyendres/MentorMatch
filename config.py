import os 
import logging
from dotenv import load_dotenv

class Config:
    load_dotenv()
    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
    SECRET_KEY = os.environ.get('SECRET_KEY')
    DATABASE_URL = os.environ.get('DATABASE_URL').replace('postgres://', 'postgresql://')
    LOCAL_FILE_PATH = 'data/people.json'
    REMOTE_MATCH_FILE = 'data/match.csv'

    