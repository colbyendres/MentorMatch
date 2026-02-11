import re
from mentormatch.models import Person

class TestRoutes:
    def test_home(self, client):
        rsp = client.get('/home')
        assert b'<title>MentorMatch | Home</title>' in rsp.data
        
    def test_add_get(self, client):
        rsp = client.get('/add')
        assert b'<title>MentorMatch | Add Person</title>' in rsp.data
         
    def test_add_post(self, client):
        form = {
            'name': 'Alice',
            'position': 'mentor',
            'matches': []
        }
        rsp = client.post('/add', data=form, follow_redirects=True)
        assert rsp.status_code == 200
        assert b'Added mentor Alice to MentorMatch' in rsp.data
        
    def test_view_get(self, client, seed_data):
        rsp = client.get('/view')
        assert re.search(r'Alice[\s\w="-<>]+prefers: Charlie', str(rsp.data))
        
    def test_match_post(self, client, seed_data):
        rsp = client.post('/match')
        assert b'Match found with 100% satisfaction' in rsp.data
        
    def test_delete_valid_person(self, client, seed_data):
        rsp = client.post('/delete/Alice', follow_redirects=True)
        assert rsp.status_code == 200
        assert b'Person Alice deleted'
        
    def test_get_edit(self, client, seed_data):
        rsp = client.get('edit/Alice', query_string='is_mentor=True')
        assert rsp.status_code == 200
        # Kludge to make sure that query parameters set default position
        assert re.search(r'value="mentor" required checked', str(rsp.data))
        
    def test_edit_valid_person(self, client, session, seed_data):
        form = {
            'name': 'Elise',
            'position': 'mentor',
            'matches': ['Charlie', 'Dan']
        }
        rsp = client.post('edit/Alice', data=form, follow_redirects=True)
        assert b'Profile updated' in rsp.data
        person = session.query(Person).filter_by(name='Elise').first()
        assert person and person.is_mentor
        assert person.name == 'Elise'
        new_matches = [pref.preferee.name for pref in person.given_prefs]
        assert 'Charlie' in new_matches and 'Dan' in new_matches