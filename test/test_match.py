import os
from dotenv import load_dotenv
from app.matcher import Matcher

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from test_utils import add_people_with_prefs


class TestMatching:
    def test_perfect_match(self, session):
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
        p_info = add_people_with_prefs(session, PERFECT_PAIRS, PREFS)
        matcher = Matcher(p_info)
        matching = matcher.match()
        for mentor, mentee, score in matching:
            assert score == 2
            if mentor == 'Alice':
                assert mentee == 'Charlie'
            else:
                assert mentee == 'Dan'

    def test_imperfect_match(self, session):
        IMPERFECT_PAIRS = [
            {'name': 'Alice', 'is_mentor': True},
            {'name': 'Bob', 'is_mentor': True},
            {'name': 'Charlie', 'is_mentor': False},
            {'name': 'Dan', 'is_mentor': False}
        ]
        PREFS = [
            ('Alice', 'Charlie'),
            ('Charlie', 'Alice'),
            ('Bob', 'Dan'),
            # Missing Dan -> Bob pref
        ]
        p_info = add_people_with_prefs(session, IMPERFECT_PAIRS, PREFS)
        matcher = Matcher(p_info)
        matching = matcher.match()
        for mentor, mentee, score in matching:
            if mentor == 'Alice':
                assert score == 2 and mentee == 'Charlie'
            else:
                assert score == 1 and mentee == 'Dan'

    def test_uneven_match(self, session):
        UNEVEN_PAIRS = [
            {'name': 'Alice', 'is_mentor': True},
            {'name': 'Bob', 'is_mentor': True},
            {'name': 'Charlie', 'is_mentor': False},
        ]
        PREFS = [
            ('Alice', 'Charlie'),
            ('Charlie', 'Alice'),
            ('Bob', 'Charlie'),
        ]
        p_info = add_people_with_prefs(session, UNEVEN_PAIRS, PREFS)
        matcher = Matcher(p_info)
        with pytest.raises(ValueError, match=r'Number of mentees and mentors differ'):
            matching = matcher.match()


@pytest.fixture
def session():
    load_dotenv()
    DB_URL = os.environ.get('DATABASE_URL').replace(
        'postgres://', 'postgresql://')
    engine = create_engine(DB_URL)
    conn = engine.connect()
    # Ensure the test tables appear before the prod tables in search
    transaction = conn.begin()
    conn.execute(text('SET search_path TO test_schema'))

    SessionLocal = sessionmaker(bind=conn)
    session = SessionLocal()

    yield session

    session.close()
    transaction.rollback()
    conn.close()
