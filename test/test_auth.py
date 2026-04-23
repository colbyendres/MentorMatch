from mentormatch.models import Person

class TestAuth:
    
    # Ensure regular users can't generate matches
    def test_regular_user_cant_match(self, regular_client, seed_data):
        rsp = regular_client.post('/match', follow_redirects=True)
        assert b'Must be admin user to view match' in rsp.data
        
    # Ensure admin can generate matches
    def test_admin_user_can_match(self, admin_client, seed_data):
        rsp = admin_client.post('/match')
        print(str(rsp.data))
        assert b'Match found with' in rsp.data
        
    # Check that regular users can see only their preferences
    def test_regular_user_preference_visibility(self, regular_client, seed_data):
        rsp = regular_client.get('/view')
        # Client represents Alice, who prefers Charlie
        assert b'prefers: Charlie' in rsp.data
        assert b'prefers: Alice' not in rsp.data
        
    # Check that admin users can see all preferences
    def test_admin_user_preference_visibility(self, admin_client, seed_data):
        rsp = admin_client.get('/view')
        assert b'prefers: Charlie' in rsp.data and b'prefers: Alice' in rsp.data
       
    # Check that regular users can edit their person
    def test_regular_user_can_edit_self(self, regular_client, session, seed_data):
        form = {
            'name': 'Alice',
            'position': 'mentor',
            'matches': ['Charlie', 'Dan']
        }
        rsp = regular_client.post('edit/Alice', data=form, follow_redirects=True)
        assert b'Profile updated' in rsp.data
        alice = session.query(Person).filter_by(name='Alice').first()
        assert 'Dan' in alice.get_prefs_as_str()

    # Check that regular users cannot edit other people
    def test_regular_user_cant_edit_others(self, regular_client, session, seed_data):
        form = {
            'name': 'Charlie',
            'position': 'mentor',
            'matches': ['Alice', 'Bob']
        }
        rsp = regular_client.post('edit/Charlie', data=form, follow_redirects=True)
        assert b'Cannot edit person associated with different user' in rsp.data

    # Check that admin users can edit anyone
    def test_admin_user_can_edit_others(self, admin_client, session, seed_data):
        form = {
            'name': 'Charlie',
            'position': 'mentee',
            'matches': ['Alice', 'Bob']
        }
        rsp = admin_client.post('edit/Charlie', data=form, follow_redirects=True)
        assert b'Profile updated' in rsp.data
        
    # Check that regular users can delete their person
    def test_regular_user_can_delete_self(self, regular_client, session, seed_data):
        rsp = regular_client.post('delete/Alice', follow_redirects=True)
        assert b'Person Alice deleted' in rsp.data
        alice = session.query(Person).filter_by(name='Alice').first()
        assert not alice

    # Check that regular users cannot delete other people
    def test_regular_user_cant_delete_others(self, regular_client, session, seed_data):
        rsp = regular_client.post('delete/Charlie', follow_redirects=True)
        assert b'Cannot delete person associated with different user' in rsp.data

    # Check that admin users can delete anyone
    def test_admin_user_can_delete_others(self, admin_client, session, seed_data):
        rsp = admin_client.post('delete/Charlie', follow_redirects=True)
        assert b'Person Charlie deleted' in rsp.data
        charlie = session.query(Person).filter_by(name='Charlie').first()
        assert not charlie