import pytest

from mentormatch.models import Person, Preference
from sqlalchemy.exc import IntegrityError

class TestPeople:
    def test_create_without_prefs(self, session):
        person = Person(name='Alice', is_mentor=True)
        session.add(person)
        assert session.query(Person).count() == 1
        
    def test_create_preference(self, session):
        mentor = Person(name='Alice', is_mentor=True)
        mentee = Person(name='Bob', is_mentor=False)
        session.add_all([mentor, mentee])
        session.flush()
        pref = Preference(preferrer_id=mentor.id, preferee_id=mentee.id)
        session.add(pref)
        assert pref in mentor.given_prefs and pref in mentee.received_prefs
        
    def test_uniqueness_of_name(self, session):
        mentor = Person(name='Alice', is_mentor=True)
        mentee = Person(name='Alice', is_mentor=False)
        session.add_all([mentor, mentee])
        with pytest.raises(IntegrityError):
            session.commit()
            
    def test_cascade_on_delete(self, session):
        alice = Person(name='Alice', is_mentor=True)
        bob = Person(name='Bob', is_mentor=False)
        charlie = Person(name='Charlie', is_mentor=False)
        session.add_all([alice, bob, charlie])
        session.flush()
        p1 = Preference(preferrer_id=alice.id, preferee_id=bob.id)
        p2 = Preference(preferrer_id=alice.id, preferee_id=charlie.id)
        session.add_all([p1, p2])
        assert session.query(Person).count() == 3
        session.delete(charlie)
        assert charlie not in alice.given_prefs
        
