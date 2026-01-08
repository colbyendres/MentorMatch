import pytest
import logging

class TestCaching:
    def test_matrix_cache(self, seed_data, caplog):
        seed_data.construct_matrix()
        caplog.set_level(logging.DEBUG)
        seed_data.construct_matrix()
        assert 'Returning cached pref matrix' in caplog.text
        
    def test_add_invalidates_matrix(self, seed_data):
        seed_data.construct_matrix()
        seed_data.add_person('Elise', 'mentor', ['Charlie'])
        assert not seed_data.matrix_valid and seed_data.indices_valid
        
    def test_edit_invalidates_matrix(self, seed_data):
        seed_data.construct_matrix()
        seed_data.edit_person('Alice', 'Alice', True, ['Dan'])
        assert not seed_data.matrix_valid and seed_data.indices_valid
        
    def test_delete_invalidates_all(self, seed_data):
        seed_data.construct_matrix()
        seed_data.delete_person('Alice')
        assert not seed_data.matrix_valid and not seed_data.indices_valid
        
    def test_match_cache(self, client, seed_data, caplog):
        caplog.set_level(logging.DEBUG)
        client.post('/match')
        assert 'Returning cached matching' not in caplog.text
        client.post('/match')
        assert 'Returning cached matching' in caplog.text
        
    def test_rematch_overrides_cache(self, client, seed_data, caplog):
        client.post('/match')
        caplog.set_level(logging.DEBUG)
        client.post('/match', query_string={'force_rematch': 'true'})
        assert 'Returning cached matching' not in caplog.text
        