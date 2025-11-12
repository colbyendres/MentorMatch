import os
import logging
from dotenv import load_dotenv


class Logger:
    logging.basicConfig(
        format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

    @staticmethod
    def info(msg):
        logging.info(msg)

    @staticmethod
    def warn(msg):
        logging.warning(msg)

    @staticmethod
    def error(msg):
        logging.error(msg)

    @staticmethod
    def debug(msg):
        logging.debug(msg)


class Config:
    load_dotenv()
    SECRET_KEY = os.environ.get('SECRET_KEY')
    DATABASE_URL = os.environ.get('DATABASE_URL').replace(
        'postgres://', 'postgresql://')
    REMOTE_MATCH_FILE = 'data/match.csv'
    logger = Logger()
