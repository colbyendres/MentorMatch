import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker

from app.app import start_app, db
from app.config import Config
from app.models import Preference, Person
from app.matcher import PeopleInfo

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
def app(test_engine):
    """Create and configure a test Flask app instance."""
    test_app = start_app()
    # Override database session to use test
    with test_app.app_context():
        db.session.execute(text("SET search_path TO test"))    
        yield test_app


@pytest.fixture(scope="function")
def client(app):
    """Create a test client for the Flask app."""
    return app.test_client()

@pytest.fixture(scope="function")
def session(app, test_engine):
    """Create a transactional database session that rolls back after each test."""
    
    connection = test_engine.connect()
    transaction = connection.begin()
    connection.execute(text("SET search_path TO test"))
    
    session_factory = sessionmaker(bind=connection)
    test_session = scoped_session(session_factory)
    with app.app_context():
        db.session = test_session
        
        yield test_session
        
        # Rollback the transaction
        test_session.remove()
        if connection.in_transaction():
            transaction.rollback()
    
    connection.close()