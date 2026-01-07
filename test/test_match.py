import pytest

from app.matcher import Matcher
from conftest import add_people_with_prefs, session

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
            # Two mentors, one mentee
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
            
    def test_interrole_match_fails(self, session):
        INELIGIBLE_PAIRS = [
            {'name': 'Alice', 'is_mentor': True},
            {'name': 'Bob', 'is_mentor': True},
            {'name': 'Charlie', 'is_mentor': False},
            {'name': 'Dan', 'is_mentor': False}
        ]
        PREFS = [
            ('Alice', 'Bob'),
            ('Bob', 'Alice')
        ]
        p_info = add_people_with_prefs(session, INELIGIBLE_PAIRS, PREFS)
        matcher = Matcher(p_info)
        with pytest.raises(ValueError, match=r'Relationship between members of the same status'):
            matching = matcher.match()
