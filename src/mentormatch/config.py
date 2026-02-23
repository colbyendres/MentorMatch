import os
import logging
from dotenv import load_dotenv


class Config:
    load_dotenv()
    logging.basicConfig(
        format='%(asctime)s - %(levelname)s - %(message)s', level=logging.DEBUG)
    
    @staticmethod
    def parse_database_url(url):
        modified_url = url 
        if 'postgres://' in url:
            # SQLAlchemy expects the URI to begin with postgresql
            modified_url = url.replace('postgres://', 'postgresql://')
            logging.debug('Using remote Postgres database')
        elif 'sqlite:///' in url:
            db_name = url.removeprefix('sqlite:///')
            curr_file_path = os.path.abspath(__file__)
            full_path = os.path.join(os.path.dirname(curr_file_path), 'data', db_name)
            modified_url = f'sqlite:///{full_path}'
        return modified_url
    
    SECRET_KEY = os.environ.get('SECRET_KEY')
    DATABASE_URL = os.environ.get('DATABASE_URL')
    TEST_DB_URL = os.environ.get('TEST_DB_URL')
    
    if DATABASE_URL is None:
        raise ValueError('Set DATABASE_URL in file')
    DATABASE_URL = parse_database_url(DATABASE_URL)
    if TEST_DB_URL is not None:
        print(f'{TEST_DB_URL=}')
        TEST_DB_URL = parse_database_url(TEST_DB_URL)
        
    REMOTE_MATCH_FILE = 'data/match.csv'
