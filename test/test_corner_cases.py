from mentormatch.models import Person

class TestCornerCases:
    
    # Attempt to match with no people loaded, display error
    def test_empty_match(self, client):
        rsp = client.post('/match')
        assert b'No mentors or mentees available to match' in rsp.data
        
    # Attempt delete on person that doesn't exist, no-op with message
    def test_delete_invalid_person(self, client):
        rsp = client.post('/delete/Alice', follow_redirects=True)
        assert b'Person Alice not found' in rsp.data
        
    # Attempt to edit person that doesn't exist, display error
    def test_edit_invalid_name(self, client):
        form = {
            'name': 'Elise',
            'position': 'mentor',
            'matches': ['Charlie', 'Dan']
        }
        rsp = client.post('edit/Alice', data=form, follow_redirects=True)
        assert b'Person Alice not found' in rsp.data
        
    # Attempt to create pref between two mentors, edit should fail
    def test_edit_invalid_prefs(self, client, session, seed_data):
        form = {
            'name': 'Alice',
            'position': 'mentor',
            'matches': ['Bob']
        }
        rsp = client.post('edit/Alice', data=form, follow_redirects=True)
        assert b'Preference cannot exist between two mentors!' in rsp.data
        alice = session.query(Person).filter_by(name='Alice').first()
        alice_prefs = [pref.preferee.name for pref in alice.given_prefs]
        assert 'Charlie' in alice_prefs and 'Bob' not in alice_prefs