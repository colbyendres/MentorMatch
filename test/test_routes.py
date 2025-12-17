from conftest import client, app, session

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
        rsp = client.post('/add', data=form, follow_redirects=False)
        assert rsp.status_code == 200
        assert b'Success: Added mentor Alice to MentorMatch' in rsp.data