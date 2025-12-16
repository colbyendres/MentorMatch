import pytest

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.models import Person, Preference, db
from app.matcher import PeopleInfo
from app.app import start_app
from app.config import Config

def add_people_with_prefs(session, people, prefs):
    people_ids = {}
    for spec in people:
        p = Person(**spec)
        session.add(p)
        session.flush()
        people_ids[p.name] = p.id

    for preferrer, preferee in prefs:
        pref = Preference(
            preferrer_id=people_ids[preferrer], preferee_id=people_ids[preferee])
        session.add(pref)

    session.commit()
    p_info = PeopleInfo(session)
    return p_info


@pytest.fixture
def session():
    engine = create_engine(Config.DATABASE_URL)
    connection = engine.connect()

    transaction = connection.begin()
    connection.execute(text("SET search_path TO test_schema"))
    SessionLocal = sessionmaker(bind=connection)
    session = SessionLocal()

    yield session

    session.close()
    if connection.in_transaction():
        transaction.rollback()
    connection.close()


@pytest.fixture
def connection():
    engine = create_engine(Config.DATABASE_URL, execution_options={
                           'schema_translate_map': {None: 'test_schema'}})
    connection = engine.connect()

    transaction = connection.begin()

    yield connection

    transaction.rollback()
    connection.close()


@pytest.fixture
def client():
     # Set the Testing configuration prior to creating the Flask application
    flask_app = start_app()
    flask_app.config['TESTING'] = True
    
    # Create a test client using the Flask application configured for testing
    with flask_app.test_client() as testing_client:
        # Establish an application context
        with flask_app.app_context():
            yield testing_client  # this is where the testing happens!