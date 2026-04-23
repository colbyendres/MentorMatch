import pytest
from sqlalchemy import create_engine
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
    """Create a test database engine using TEST_DB_URL."""
    if Config.TEST_DB_URL is None:
        raise ValueError("TEST_DB_URL not set in environment")
    engine = create_engine(Config.TEST_DB_URL)
    yield engine


@pytest.fixture(scope="session")
def app():
    """Create and configure a test Flask app instance with test database."""
    test_app = start_app(is_testing=True)
    with test_app.app_context():
        yield test_app


@pytest.fixture(scope="function")
def client(app, session):
    """Create a test client for the Flask app."""
    with app.app_context():
        app.config["AUTH_ENABLED"] = False
        app.people = PeopleInfo(session)
        app.matcher = Matcher(app.people)
        yield app.test_client()

@pytest.fixture(scope="function")
def session(app, test_engine):
    """Create a transactional database session that rolls back after each test."""
    
    connection = test_engine.connect()
    transaction = connection.begin()
    
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

@pytest.fixture
def auth_client_factory(app, session, monkeypatch):
    # Turn auth checks on for these tests
    monkeypatch.setitem(app.config, "AUTH_ENABLED", True)

    # Define who is admin in tests
    monkeypatch.setattr(Config, "ADMIN_USERS", {"admin@gmail.com"})

    with app.app_context():
        app.people = PeopleInfo(session)
        app.matcher = Matcher(app.people)

        def _make_client(email: str, name: str):
            auth_client = app.test_client()
            with auth_client.session_transaction() as sess:
                sess["user"] = {
                    "email": email,
                    "name": name,
                    "picture": None,
                }
            return auth_client

        return _make_client


@pytest.fixture
def regular_client(auth_client_factory):
    return auth_client_factory("test1@gmail.com", "Alice")

@pytest.fixture
def admin_client(auth_client_factory):
    return auth_client_factory("admin@gmail.com", "Admin")
 
@pytest.fixture()
def seed_data(session):
    PERFECT_PAIRS = [
        {'name': 'Alice', 'is_mentor': True, 'email': 'test1@gmail.com'},
        {'name': 'Bob', 'is_mentor': True, 'email': 'test2@gmail.com'},
        {'name': 'Charlie', 'is_mentor': False, 'email': 'test3@gmail.com'},
        {'name': 'Dan', 'is_mentor': False, 'email': 'test4@gmail.com'}
    ]
    PREFS = [
        ('Alice', 'Charlie'),
        ('Charlie', 'Alice'),
        ('Bob', 'Dan'),
        ('Dan', 'Bob')
    ]
    return add_people_with_prefs(session, PERFECT_PAIRS, PREFS)
    