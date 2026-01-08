import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker

from mentormatch.app import start_app, db
from mentormatch.config import Config
from mentormatch.models import Preference, Person
from mentormatch.matcher import PeopleInfo, Matcher

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

@pytest.fixture(scope="session")
def test_engine():
    """Create a test database engine with test_schema."""
    engine = create_engine(Config.DATABASE_URL)
    yield engine


@pytest.fixture(scope="session")
def app():
    """Create and configure a test Flask app instance."""
    test_app = start_app()
    # Override database session to use test
    with test_app.app_context():
        yield test_app


@pytest.fixture(scope="function")
def client(app, session):
    """Create a test client for the Flask app."""
    with app.app_context():
        app.people = PeopleInfo(session)
        app.matcher = Matcher(app.people)
        yield app.test_client()

@pytest.fixture(scope="function")
def session(app, test_engine):
    """Create a transactional database session that rolls back after each test."""
    
    connection = test_engine.connect()
    transaction = connection.begin()
    connection.execute(text("SET search_path TO test"))
    
    session_factory = sessionmaker(bind=connection)
    test_session = scoped_session(session_factory)
    
    # Override commit and rollback to prevent them from closing the transaction
    test_session.commit = lambda: test_session.flush()
    test_session.rollback = lambda: test_session.flush()
    with app.app_context():
        db.session = test_session
        
        yield test_session
        
        # Rollback the transaction
        test_session.remove()
        if transaction.is_active:
            transaction.rollback()
    
    connection.close()
    
@pytest.fixture()
def seed_data(session):
    PERFECT_PAIRS = [
        {'name': 'Alice', 'is_mentor': True},
        {'name': 'Bob', 'is_mentor': True},
        {'name': 'Charlie', 'is_mentor': False},
        {'name': 'Dan', 'is_mentor': False}
    ]
    PREFS = [
        ('Alice', 'Charlie'),
        ('Charlie', 'Alice'),
        ('Bob', 'Dan'),
        ('Dan', 'Bob')
    ]
    return add_people_with_prefs(session, PERFECT_PAIRS, PREFS)
    