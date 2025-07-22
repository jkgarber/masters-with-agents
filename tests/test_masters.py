import pytest
from incontext.db import get_db

def test_index(client, auth):
    # user must be logged in
    response = client.get('/masters/')
    assert response.status_code == 302
    assert response.headers['Location'] == '/auth/login'
    auth.login()
    response = client.get('/masters/')
    assert response.status_code == 200
    # test user's list master data gets served
    assert b'master name 1' in response.data
    assert b'master description 1' in response.data
    assert b'master name 2' in response.data
    assert b'master description 2' in response.data
    # other user's list master data does not get served
    assert b'master name 3' not in response.data
    assert b'master description 3' not in response.data
    assert b'master name 4' not in response.data
    assert b'master description 4' not in response.data
    # user's agent master data gets served
    assert b'master name 5' in response.data
    assert b'master description 5' in response.data
    assert b'master name 6' in response.data
    assert b'master description 6' in response.data
    # other user's agent master data does not get served
    assert b'master name 7' not in response.data
    assert b'master description 7' not in response.data


def test_new_master(app, client, auth):
    # user must be logged in
    response = client.get('/masters/new/list')
    assert response.status_code == 302
    assert response.headers['Location'] == '/auth/login'
    auth.login()
    response = client.get('/masters/new/list')
    assert response.status_code == 200
    # data validation (list master)
    response = client.post(
        'masters/new/list',
        data = {'name': '', 'description': ''}
    )
    assert b'Name is required' in response.data
    # list master is saved to database
    response = client.post(
        'masters/new/list',
        data = {'name': 'master name 8', 'description': 'master description 8'},
    )
    with app.app_context():
        db = get_db()
        masters = db.execute('SELECT master_type, name, description FROM masters WHERE creator_id = 2').fetchall()
        assert len(masters) == 5
        assert masters[4]["master_type"] == "list"
        assert masters[4]['name'] == 'master name 8'
        assert masters[4]['description'] == 'master description 8'
    # data validation (agent master)
    response = client.post(
        "masters/new/agent",
        data={"name": "", "description": "master description 9", "model": "gemini-1.5-pro", "role": "Testing Agent", "instructions": "Reply with one word: 'Working'. 4"}
    )
    assert b'Model, name, role, and instructions are all required.' in response.data
    response = client.post(
        "masters/new/agent",
        data={"name": "master name 9", "description": "master description 9", "model": "", "role": "Testing Agent", "instructions": "Reply with one word: 'Working'. 4"}
    )
    assert b'Model, name, role, and instructions are all required.' in response.data
    # invalid model
    response = client.post(
        "masters/new/agent",
        data={"name": "master name 9", "description": "master description 9", "model": "blah", "role": "Testing Agent", "instructions": "Reply with one word: 'Working'. 4"}
    )
    assert b'Model not recognized as a supported model.' in response.data
    response = client.post(
        "masters/new/agent",
        data={"name": "master name 9", "description": "master description 9", "model": "gemini-1.5-pro", "role": "", "instructions": "Reply with one word: 'Working'. 4"}
    )
    assert b'Model, name, role, and instructions are all required.' in response.data
    response = client.post(
        "masters/new/agent",
        data={"name": "master name 9", "description": "master description 9", "model": "gemini-1.5-pro", "role": "Testing Agent", "instructions": ""}
    )
    assert b'Model, name, role, and instructions are all required.' in response.data
    # agent master is saved to database
    response = client.post(
        'masters/new/agent',
        data = {'name': 'master name 9', 'description': 'master description 9', "model": "gemini-1.5-pro", "role": "Testing Agent 9", "instructions": "Reply with one word: 'Working'. 4"},
    )
    with app.app_context():
        db = get_db()
        masters = db.execute('SELECT * FROM masters WHERE creator_id = 2').fetchall()
        assert len(masters) == 6
        assert masters[5]["master_type"] == "agent"
        assert masters[5]['name'] == 'master name 9'
        assert masters[5]['description'] == 'master description 9'
        master_agents = db.execute('SELECT * FROM master_agents WHERE creator_id = 2').fetchall()
        assert len(master_agents) == 3
        new_master_agent = master_agents[-1]
        assert new_master_agent["model"] == "gemini-1.5-pro"
        assert new_master_agent["role"] == "Testing Agent 9"
        assert new_master_agent["instructions"] == "Reply with one word: 'Working'. 4"
        assert new_master_agent["vendor"] == "google"
        master_agent_relations = db.execute(
            "SELECT * FROM master_agent_relations"
            " WHERE master_id = ?",
            (masters[-1]["id"],)
        ).fetchone()
        assert master_agent_relations["master_agent_id"] == new_master_agent["id"]
    # redirected to masters.index
    assert response.status_code == 302
    assert response.headers['Location'] == '/masters/'
    # must be a valid master type
    assert client.get("/masters/new/blah").status_code == 404
    assert client.post("/masters/new/blah").status_code == 404
    # test other model providers
    response = client.post( # openai
        'masters/new/agent',
        data = {'name': 'master name 10', 'description': 'master description 10', "model": "gpt-4.1-mini", "role": "Testing Agent 10", "instructions": "Reply with one word: 'Working'. 10"},
    )
    assert response.status_code == 302
    response = client.post( # anthropic
        'masters/new/agent',
        data = {'name': 'master name 10', 'description': 'master description 10', "model": "claude-3-5-haiku-latest", "role": "Testing Agent 10", "instructions": "Reply with one word: 'Working'. 10"},
    )
    assert response.status_code == 302


def test_view_list_master(app, client, auth):
    # user must be logged in
    response = client.get('masters/1/view')
    assert response.status_code == 302
    assert response.headers['Location'] == '/auth/login'
    # user must be list master creator
    auth.login('other', 'other')
    assert client.get('masters/1/view').status_code == 403
    auth.login()
    response = client.get('/masters/1/view')
    assert response.status_code == 200
    # list master data gets served
    assert b'master name 1' in response.data
    assert b'master description 1' in response.data
    assert b'detail name 1' in response.data
    assert b'detail name 2' in response.data
    assert b'item name 1' in response.data
    assert b'item name 2' in response.data
    assert b'relation content 1' in response.data
    assert b'relation content 2' in response.data
    assert b'relation content 3' in response.data
    assert b'relation content 4' in response.data
    assert b'detail description 1' in response.data
    assert b'detail description 2' in response.data
    # other list master data does not get served
    assert b'item name 3' not in response.data
    assert b'detail name 3' not in response.data
    assert b'relation content 5' not in response.data
    assert b'detail description 3' not in response.data
    # other users list master data does not get served
    assert b'item name 4' not in response.data
    assert b'item name 5' not in response.data
    assert b'item name 6' not in response.data
    assert b'detail name 4' not in response.data
    assert b'detail name 5' not in response.data
    assert b'detail name 6' not in response.data
    assert b'relation content 5' not in response.data
    assert b'relation content 6' not in response.data
    assert b'relation content 7' not in response.data
    assert b'relation content 8' not in response.data
    assert b'relation content 9' not in response.data
    assert b'relation content 10' not in response.data
    assert b'detail description 4' not in response.data
    assert b'detail description 5' not in response.data
    assert b'detail description 6' not in response.data
    # list master must exist
    assert client.get('masters/8/view').status_code == 404


def test_edit_list_master(app, client, auth):
    # user must be logged in
    response = client.get('/masters/1/edit')
    assert response.status_code == 302
    assert response.headers['Location'] == '/auth/login'
    # user must be master creator
    auth.login('other', 'other')
    assert client.get('masters/1/edit').status_code == 403
    auth.login()
    response = client.get('masters/1/edit')
    assert response.status_code == 200
    # master data gets served
    assert b'master name 1' in response.data
    assert b'master description 1' in response.data
    # data validation
    response = client.post('masters/1/edit', data={'name': '', 'description': ''})
    assert b'Name is required' in response.data
    # changes are saved to database
    response = client.post(
        'masters/1/edit',
        data={'name': 'master name 1 updated', 'description': 'master description 1 updated'}
    )
    with app.app_context():
        db = get_db()
        masters = db.execute('SELECT name, description FROM masters').fetchall()
        assert masters[0]['name'] == 'master name 1 updated'
        assert masters[0]['description'] == 'master description 1 updated'
        # other masters are not changed
        for master in masters[1:]:
            assert master['name'] != 'master name 1 updated'
            assert master['description'] != 'master description 1 updated'
    # redirected to masters.index
    assert response.status_code == 302
    assert response.headers['Location'] == '/masters/'
    # master must exist
    assert client.get('/masters/8/edit').status_code == 404


def test_delete_list_master(app, client, auth):
    # user must be logged in
    response = client.post('/masters/1/delete')
    assert response.status_code == 302
    assert response.headers['Location'] == '/auth/login'
    # user must be master creator
    auth.login('other', 'other')
    assert client.post('masters/1/delete').status_code == 403
    # list master gets deleted
    auth.login()
    with app.app_context():
        db = get_db()
        master_item_count = db.execute(
            'SELECT COUNT(id) AS count FROM master_items'
        ).fetchone()['count']
        master_detail_count = db.execute(
            'SELECT COUNT(id) AS count FROM master_details'
        ).fetchone()['count']
        master_item_detail_relation_count = db.execute(
            'SELECT COUNT(id) AS count FROM master_item_detail_relations'
        ).fetchone()['count']
        master_count = db.execute(
            'SELECT COUNT(id) AS count FROM masters'
        ).fetchone()['count']
        master_item_relation_count = db.execute(
            'SELECT COUNT(id) AS count FROM master_item_relations'
        ).fetchone()['count']
        master_detail_relation_count = db.execute(
            'SELECT COUNT(id) AS count FROM master_detail_relations'
        ).fetchone()['count']
        affected_item_ids = db.execute(
            'SELECT master_item_id FROM master_item_relations WHERE master_id = 1'
        ).fetchall()
        assert len(affected_item_ids) == 2
        affected_item_ids = [item_id['master_item_id'] for item_id in affected_item_ids]
        placeholders_affected_item_ids = f'{"?, " * len(affected_item_ids)}'[:-2]
        affected_detail_ids = db.execute(
            'SELECT master_detail_id FROM master_detail_relations WHERE master_id = 1'
        ).fetchall()
        assert len(affected_detail_ids) == 2
        affected_detail_ids = [detail_id['master_detail_id'] for detail_id in affected_detail_ids]
        placeholders_affected_detail_ids = f'{"?, " * len(affected_detail_ids)}'[:-2]
        affected_item_and_detail_ids = affected_item_ids + affected_detail_ids
        affected_relation_ids = db.execute(
            'SELECT id, master_item_id FROM master_item_detail_relations'
            f' WHERE master_item_id IN ({placeholders_affected_item_ids})'
            f' OR master_detail_id IN ({placeholders_affected_detail_ids})',
            affected_item_and_detail_ids
        ).fetchall()
        assert len(affected_relation_ids) == 4
        response = client.post('/masters/1/delete')
        deleted_master = db.execute('SELECT * FROM masters WHERE id = 1').fetchone()
        assert deleted_master == None
        deleted_master_item_relations = db.execute(
            'SELECT * FROM master_item_relations WHERE master_id = 1'
        ).fetchall()
        assert len(deleted_master_item_relations) == 0
        deleted_master_detail_relations = db.execute('SELECT * FROM master_detail_relations WHERE master_id = 1').fetchall()
        assert len(deleted_master_detail_relations) == 0
        deleted_master_items = db.execute(
            f'SELECT * FROM master_items WHERE id IN ({placeholders_affected_item_ids})',
            affected_item_ids
        ).fetchall()
        assert len(deleted_master_items) == 0
        deleted_master_details = db.execute(
            f'SELECT * FROM master_details WHERE id IN ({placeholders_affected_detail_ids})',
            affected_detail_ids
        ).fetchall()
        assert len(deleted_master_details) == 0
        deleted_master_relations = db.execute(
            'SELECT * FROM master_item_detail_relations'
            f' WHERE master_item_id IN ({placeholders_affected_item_ids})'
            f' OR master_detail_id IN ({placeholders_affected_detail_ids})',
            affected_item_and_detail_ids
        ).fetchall()
        assert len(deleted_master_relations) == 0
        # other master data does not get deleted
        master_items = db.execute('SELECT * FROM master_items').fetchall()
        assert len(master_items) == master_item_count - len(affected_item_ids)
        master_details = db.execute('SELECT * FROM master_details').fetchall()
        assert len(master_details) == master_detail_count - len(affected_detail_ids)
        master_item_detail_relations = db.execute('SELECT * FROM master_item_detail_relations').fetchall()
        assert len(master_item_detail_relations) == master_item_detail_relation_count - len(affected_relation_ids)
        masters = db.execute('SELECT * FROM masters').fetchall()
        assert len(masters) == master_count - 1
        master_item_relations = db.execute('SELECT * FROM master_item_relations').fetchall()
        assert len(master_item_relations) == master_item_relation_count - len(affected_item_ids)
        master_detail_relations = db.execute('SELECT * FROM master_detail_relations').fetchall()
        assert len(master_detail_relations) == master_detail_relation_count - len(affected_detail_ids)
    # redirected to lists.index
    response = client.post('masters/2/delete')
    assert response.status_code == 302
    assert response.headers['Location'] == '/masters/'
    # list master must exist
    response = client.post("masters/8/delete")
    assert response.status_code == 404


def test_new_master_item(app, client, auth):
    # user must be logged in
    response = client.get('/masters/1/items/new')
    assert response.status_code == 302
    assert response.headers['Location'] == '/auth/login'
    # user must be master creator
    auth.login('other', 'other')
    assert client.get('/masters/1/items/new').status_code == 403
    auth.login()
    response = client.get('/masters/1/items/new')
    assert response.status_code == 200
    # master-specific detail names are served
    with app.app_context():
        db = get_db()
        master_details = db.execute(
            'SELECT d.name'
            ' FROM master_details d'
            ' JOIN master_detail_relations r'
            ' ON d.id = r.master_detail_id'
            ' WHERE r.master_id = 1'
        ).fetchall()
        for master_detail in master_details:
            assert master_detail['name'].encode() in response.data
        # other master detail names are not served
        other_master_details = db.execute(
            'SELECT d.name'
            ' FROM master_details d'
            ' JOIN master_detail_relations r'
            ' ON d.id = r.master_detail_id'
            ' WHERE r.master_id <> 1'
        ).fetchall()
        for master_detail in other_master_details:
            assert master_detail['name'].encode() not in response.data
    # data validationa
    response = client.post(
        '/masters/1/items/new', data={'name': '', '1': '', '2': ''}
    )
    assert b'Name is required' in response.data
    # new master item is saved to db correctly
    with app.app_context():
        db = get_db()
        master_items_before = db.execute(
            'SELECT id, creator_id, name FROM master_items'
        ).fetchall()
        master_details_before = db.execute(
            'SELECT d.id, d.name FROM master_details d'
            ' JOIN master_detail_relations r'
            ' ON r.master_detail_id = d.id'
            ' WHERE r.master_id = 1'
        ).fetchall()
        master_item_detail_relations_before = db.execute(
            'SELECT id, master_item_id, master_detail_id, content'
            ' FROM master_item_detail_relations'
        ).fetchall()
        master_item_relations_before = db.execute(
            'SELECT id, master_id, master_item_id'
            ' FROM master_item_relations'
        ).fetchall()
        response = client.post(
            '/masters/1/items/new',
            data={
                'name': 'item name 7',
                '1': 'relation content 11',
                '2': 'relation content 12',
            }
        )
        master_items_after = db.execute(
            'SELECT id, creator_id, name FROM master_items'
        ).fetchall()
        master_details_after = db.execute(
            'SELECT d.id, d.name FROM master_details d'
            ' JOIN master_detail_relations r'
            ' ON r.master_detail_id = d.id'
            ' WHERE r.master_id = 1'
        ).fetchall()
        master_item_detail_relations_after = db.execute(
            'SELECT id, master_item_id, master_detail_id, content'
            ' FROM master_item_detail_relations'
        ).fetchall()
        master_item_relations_after = db.execute(
            'SELECT id, master_id, master_item_id'
            ' FROM master_item_relations'
        ).fetchall()
        assert master_items_after[:-1] == master_items_before
        assert master_details_after == master_details_before
        assert master_item_detail_relations_after[:-2] == master_item_detail_relations_before
        assert master_item_relations_after[:-1] == master_item_relations_before
        assert master_items_after[-1]['name'] == 'item name 7'
        assert master_item_detail_relations_after[-2]['master_detail_id'] == 1
        assert master_item_detail_relations_after[-2]['content'] == 'relation content 11'
        assert master_item_detail_relations_after[-1]['master_detail_id'] == 2
        assert master_item_detail_relations_after[-1]['content'] == 'relation content 12'
        assert master_item_relations_after[-1]['master_id'] == 1
        assert master_item_relations_after[-1]['master_item_id'] == len(master_items_after)
        # redirect to master.view
        assert response.status_code == 302
        assert response.headers['Location'] == '/masters/1/view'


def test_view_master_item(client, auth, app):
    # user must be logged in
    response = client.get('/masters/1/items/1/view')
    assert response.status_code == 302
    assert response.headers['Location'] == '/auth/login'
    # user must be master owner
    auth.login('other', 'other')
    assert client.get('/masters/1/items/1/view').status_code == 403
    auth.login()
    response = client.get('/masters/1/items/1/view')
    assert response.status_code == 200
    # master item data gets served
    with app.app_context():
        db = get_db()
        master_item = db.execute(
            'SELECT id, name'
            ' FROM master_items'
            ' WHERE id = 1'
        ).fetchone()
        contents = db.execute(
            'SELECT r.content, d.name AS master_detail_name'
            ' FROM master_item_detail_relations r'
            ' JOIN master_details d ON r.master_detail_id = d.id'
            ' WHERE r.master_item_id = 1'
        ).fetchall()
        assert str(master_item['id']).encode() in response.data
        assert master_item['name'].encode() in response.data
        for content in contents:
            assert content['content'].encode() in response.data
            assert content['master_detail_name'].encode() in response.data
        # other master item data does not get served
        other_master_items = db.execute(
            'SELECT id, name'
            ' FROM master_items'
            ' WHERE id <> 1'
        ).fetchall()
        for other_master_item in other_master_items:
            assert other_master_item['name'].encode() not in response.data
        other_contents = db.execute(
            'SELECT r.content'
            ' FROM master_item_detail_relations r'
            ' WHERE r.master_item_id <> 1'
        ).fetchall()
        for other_content in other_contents:
            assert other_content['content'].encode() not in response.data
        other_master_details = db.execute(
            'SELECT d.name'
            ' FROM master_details d'
            ' JOIN master_detail_relations r'
            ' ON r.master_detail_id = d.id'
            ' WHERE r.master_id <> 1'
        ).fetchall()
        for other_master_detail in other_master_details:
            assert other_master_detail['name'].encode() not in response.data
    # master item must exist
    assert client.get('masters/1/items/7/view').status_code == 404


def test_edit_master_item(client, auth, app):
    # user must be logged in
    response = client.get('masters/1/items/1/edit')
    assert response.status_code == 302
    assert response.headers['Location'] == '/auth/login'
    # user must have access to item
    auth.login('other', 'other')
    assert client.get('masters/1/items/1/edit').status_code == 403
    auth.login()
    response = client.get('masters/1/items/1/edit')
    assert response.status_code == 200
    # item data gets served
    with app.app_context():
        db = get_db()
        master = db.execute(
            'SELECT name, description'
            ' FROM masters'
            ' WHERE id = 1'
        ).fetchone()
        master_item = db.execute(
            'SELECT id, name'
            ' FROM master_items'
            ' WHERE id = 1'
        ).fetchone()
        contents = db.execute(
            'SELECT r.content, d.name AS master_detail_name'
            ' FROM master_item_detail_relations r'
            ' JOIN master_details d ON r.master_detail_id = d.id'
            ' WHERE r.master_item_id = 1'
        ).fetchall()
        assert master['name'].encode() in response.data
        assert master['description'].encode() in response.data
        assert str(master_item['id']).encode() in response.data
        assert master_item['name'].encode() in response.data
        for content in contents:
            assert content['content'].encode() in response.data
            assert content['master_detail_name'].encode() in response.data
        # other master item data does not get served
        other_masters = db.execute(
            'SELECT name, description'
            ' FROM masters'
            ' WHERE id <> 1'
        ).fetchall()
        for other_master in other_masters:
            assert other_master['name'].encode() not in response.data
            assert other_master['description'].encode() not in response.data
        other_master_items = db.execute(
            'SELECT id, name'
            ' FROM master_items'
            ' WHERE id <> 1'
        ).fetchall()
        for other_master_item in other_master_items:
            assert other_master_item['name'].encode() not in response.data
        other_contents = db.execute(
            'SELECT r.content'
            ' FROM master_item_detail_relations r'
            ' WHERE r.master_item_id <> 1'
        ).fetchall()
        for other_content in other_contents:
            assert other_content['content'].encode() not in response.data
        other_master_details = db.execute(
            'SELECT d.name'
            ' FROM master_details d'
            ' JOIN master_detail_relations r'
            ' ON r.master_detail_id = d.id'
            ' WHERE r.master_id <> 1'
        ).fetchall()
        for other_master_detail in other_master_details:
            assert other_master_detail['name'].encode() not in response.data
    # data validation
    response = client.post(
        'masters/1/items/1/edit',
        data={
            'name': '',
            '1': '',
            '2': ''
        }
    )
    assert b'Name is required' in response.data
    # changes are saved to database
    with app.app_context():
        db = get_db()
        master_items_before = db.execute('SELECT name FROM master_items').fetchall()
        relations_before = db.execute('SELECT content FROM master_item_detail_relations').fetchall()
        response = client.post(
            'masters/1/items/1/edit',
            data={
                'name': 'item name 1 updated',
                '1': 'relation content 1 updated',
                '2': 'relation content 2 updated'
            }
        )
        master_items_after = db.execute('SELECT name FROM master_items').fetchall()
        relations_after = db.execute('SELECT content FROM master_item_detail_relations').fetchall()
        assert master_items_after[0]['name'] == 'item name 1 updated'
        assert relations_after[0]['content'] == 'relation content 1 updated'
        assert relations_after[1]['content'] == 'relation content 2 updated'
        # other items and relations are unchanged
        assert master_items_after[1:] == master_items_before[1:]
        assert relations_after[2:] == relations_before[2:]
    # redirected to lists.view
    assert response.status_code == 302
    assert response.headers['Location'] == '/masters/1/view'
    # item must exist
    assert client.get('masters/1/items/7/edit').status_code == 404


def test_delete_master_item(client, auth, app):
    # user must be logged in
    response = client.post('/masters/1/items/1/delete')
    assert response.status_code == 302
    assert response.headers['Location'] == '/auth/login'
    # user must have permission
    auth.login('other', 'other')
    assert client.post('/masters/1/items/1/delete').status_code == 403
    auth.login()
    with app.app_context():
        db = get_db()
        master_items_before = db.execute('SELECT id, name FROM master_items').fetchall()
        contents_before = db.execute('SELECT content FROM master_item_detail_relations').fetchall()
        relations_before = db.execute('SELECT master_id, master_item_id FROM master_item_relations').fetchall()
        response = client.post('/masters/1/items/1/delete')
        master_items_after = db.execute('SELECT id, name FROM master_items').fetchall()
        contents_after = db.execute('SELECT content FROM master_item_detail_relations').fetchall()
        relations_after = db.execute('SELECT master_id, master_item_id FROM master_item_relations').fetchall()
        # only the affected master_item gets deleted
        assert master_items_after == master_items_before[1:]
        # only the affected detail relations get deleted
        assert contents_after == contents_before[2:]
        # only the affected master relation gets deleted
        assert relations_after == relations_before[1:]
    # redirected to master
    assert response.status_code == 302
    assert response.headers['Location'] == '/masters/1/view'
    # master item must exist
    response = client.post('masters/1/items/7/delete')
    assert response.status_code == 404


def test_new_master_detail(client, auth, app):
    # user must be logged in
    response = client.get('/masters/1/details/new')
    assert response.status_code == 302
    assert response.headers['Location'] == '/auth/login'
    auth.login()
    response = client.get('/masters/1/details/new')
    assert response.status_code == 200
    # user must have permission
    auth.login('other', 'other')
    assert client.get('/masters/1/details/new').status_code == 403
    assert client.post('/masters/1/details/new').status_code == 403
    auth.login()
    response = client.get('/masters/1/details/new')
    assert response.status_code == 200
    # data validation
    response = client.post('/masters/1/details/new',
        data={'name': '', 'description': ''}
    )
    assert b'Name is required' in response.data
    with app.app_context():
        db = get_db()
        master_details_before = db.execute('SELECT * FROM master_details').fetchall()
        rels_before = db.execute('SELECT * FROM master_detail_relations').fetchall()
        response = client.post('/masters/1/details/new',
            data={
                'name': 'detail name 7',
                'description': 'detail description 7'
            }
        )
        master_details_after = db.execute('SELECT * FROM master_details').fetchall()
        rels_after = db.execute('SELECT * FROM master_detail_relations').fetchall()
        assert master_details_after[-1]['name'] == 'detail name 7'
        assert master_details_after[-1]['description'] == 'detail description 7'
        assert master_details_after[:-1] == master_details_before
        assert rels_after[:-1] == rels_before
        assert rels_after[-1]['master_id'] == 1
        master_details = db.execute(
            'SELECT name FROM master_details d'
            ' JOIN master_detail_relations r'
            ' ON r.master_detail_id = d.id'
            ' WHERE r.master_id = 1'
        ).fetchall()
        assert master_details[-1]['name'] == 'detail name 7'
    assert response.status_code == 302
    assert response.headers['Location'] == '/masters/1/view'


def test_edit_master_detail(client, auth, app):
    # user must be logged in
    response = client.get('/masters/1/details/1/edit')
    assert response.status_code == 302
    assert response.headers['Location'] == '/auth/login'
    response = client.post('masters/1/details/1/edit')
    assert response.status_code == 302
    assert response.headers['Location'] == '/auth/login'
    # user must have permission
    auth.login('other', 'other')
    response = client.get('/masters/1/details/1/edit')
    assert response.status_code == 403
    response = client.post('masters/1/details/1/edit')
    assert response.status_code == 403
    auth.login()
    response = client.get('/masters/1/details/1/edit')
    assert response.status_code == 200
    # master_detail must exist
    response = client.get('/masters/1/details/7/edit')
    assert response.status_code == 404
    # data validation
    response = client.post(
        '/masters/1/details/1/edit',
        data={'name': '', 'description': ''}
    )
    assert b'Name is required' in response.data
    # master_detail is updated in db
    with app.app_context():
        db = get_db()
        master_details_before = db.execute('SELECT * FROM master_details').fetchall()
        rels_before = db.execute('SELECT * FROM master_detail_relations').fetchall()
        irels_before = db.execute('SELECT * FROM master_item_detail_relations').fetchall()
        response = client.post(
            '/masters/1/details/1/edit',
            data={
                'name': 'detail name 1 updated',
                'description': 'detail description 1 updated'
            }
        )
        master_details_after = db.execute('SELECT * FROM master_details').fetchall()
        rels_after = db.execute('SELECT * FROM master_detail_relations').fetchall()
        irels_after = db.execute('SELECT * FROM master_item_detail_relations').fetchall()
        assert master_details_after[1:] == master_details_before[1:]
        assert master_details_after[0] != master_details_before[0]
        assert master_details_after[0]['name'] == 'detail name 1 updated'
        assert master_details_after[0]['description'] == 'detail description 1 updated'
        assert rels_before == rels_after
        assert irels_before == irels_after
    # redirect to master view
    assert response.status_code == 302
    assert response.headers['Location'] == '/masters/1/view'


def test_delete_master_detail(client, auth, app):
    # user must be logged in
    response = client.post('/masters/1/details/1/delete')
    assert response.status_code == 302
    assert response.headers['Location'] == '/auth/login'
    # user must have permisstion
    auth.login('other', 'other')
    response = client.post('/masters/1/details/1/delete')
    assert response.status_code == 403
    # master detail must exist
    auth.login()
    response = client.post('/masters/1/details/7/delete')
    assert response.status_code == 404
    # detail and related records get deleted
    with app.app_context():
        db = get_db()
        mast_dets_before = db.execute('SELECT * FROM master_details').fetchall()
        m_i_d_rels_before = db.execute('SELECT * FROM master_item_detail_relations').fetchall()
        m_d_rels_before = db.execute('SELECT * FROM master_detail_relations').fetchall()
        response = client.post('/masters/1/details/1/delete')
        mast_dets_after = db.execute('SELECT * FROM master_details').fetchall()
        m_i_d_rels_after = db.execute('SELECT * FROM master_item_detail_relations').fetchall()
        m_d_rels_after = db.execute('SELECT * FROM master_detail_relations').fetchall()
        assert mast_dets_before[1:] == mast_dets_after
        assert len(m_i_d_rels_before) == len(m_i_d_rels_after) + 2
        for rel in m_i_d_rels_after:
            assert rel['master_detail_id'] != 1
        assert m_d_rels_before[1:] == m_d_rels_after
    # redirect to master view
    assert response.status_code == 302
    assert response.headers['Location'] == '/masters/1/view'


def test_view_agent_master(app, client, auth):
    # user must be logged in
    response = client.get('masters/5/view')
    assert response.status_code == 302
    assert response.headers['Location'] == '/auth/login'
    # user must be agent master creator
    auth.login('other', 'other')
    assert client.get('masters/5/view').status_code == 403
    auth.login()
    response = client.get('/masters/5/view')
    assert response.status_code == 200
    # agent master data gets served
    assert b'master name 5' in response.data
    assert b'master description 5' in response.data
    assert b'gpt-4o-mini' in response.data
    assert b'Testing Agent 1' in response.data
    assert b'Reply with one word: &#34;Working&#34; 1.' in response.data
    # do not need to test that other data does not get served
    # because the template only accepts one of each parameter.


def test_edit_agent_master(app, client, auth):
    # user must be logged in
    response = client.get('/masters/5/edit')
    assert response.status_code == 302
    assert response.headers['Location'] == '/auth/login'
    # user must be master creator
    auth.login('other', 'other')
    assert client.get('masters/5/edit').status_code == 403
    auth.login()
    response = client.get('masters/5/edit')
    assert response.status_code == 200
    # agent master data gets served
    assert b'master name 5' in response.data
    assert b'master description 5' in response.data
    assert b'gpt-4o-mini' in response.data
    assert b'Testing Agent 1' in response.data
    assert b'Reply with one word: &#34;Working&#34; 1.' in response.data
    # data validation
    response = client.post(
        "masters/5/edit",
        data={"name": "", "description": "master description 9", "model": "gemini-1.5-pro", "role": "Testing Agent", "instructions": "Reply with one word: 'Working'"}
    )
    assert b'Model, name, role, and instructions are all required.' in response.data
    response = client.post(
        "masters/5/edit",
        data={"name": "master name 9", "description": "master description 9", "model": "", "role": "Testing Agent", "instructions": "Reply with one word: 'Working'"}
    )
    assert b'Model, name, role, and instructions are all required.' in response.data
    # invalid model
    response = client.post(
        "masters/5/edit",
        data={"name": "master name 9", "description": "master description 9", "model": "blah", "role": "Testing Agent", "instructions": "Reply with one word: 'Working'"}
    )
    assert b'Model not recognized as a supported model.' in response.data
    response = client.post(
        "masters/5/edit",
        data={"name": "master name 9", "description": "master description 9", "model": "gemini-1.5-pro", "role": "", "instructions": "Reply with one word: 'Working'"}
    )
    assert b'Model, name, role, and instructions are all required.' in response.data
    response = client.post(
        "masters/5/edit",
        data={"name": "master name 9", "description": "master description 9", "model": "gemini-1.5-pro", "role": "Testing Agent", "instructions": ""}
    )
    assert b'Model, name, role, and instructions are all required.' in response.data
    # changes are saved to database without affecting other data
    with app.app_context():
        db = get_db()
        masters_before = db.execute("SELECT * FROM masters").fetchall()
        master_agents_before = db.execute("SELECT * FROM master_agents").fetchall()
        master_agent_relations_before = db.execute("SELECT * FROM master_agent_relations").fetchall()
        response = client.post(
            'masters/5/edit',
            data={
                "name": "master name 5 updated",
                "description": "master description 5 updated",
                "model": "gemini-2.0-flash",
                "role": "Testing Agent Updated",
                "instructions": "Response with one word: 'Working' 1 updated."
            }
        )
        masters_after = db.execute('SELECT * FROM masters').fetchall()
        master_agents_after = db.execute("SELECT * FROM master_agents").fetchall()
        master_agent_relations_after = db.execute("SELECT * FROM master_agent_relations").fetchall()
        assert masters_after[:4] == masters_before[:4]
        assert masters_after[4] != masters_before[4]
        assert masters_after[5:] == masters_before[5:]
        assert masters_after[4]['name'] == 'master name 5 updated'
        assert masters_after[4]['description'] == 'master description 5 updated'
        assert master_agents_after[1:] == master_agents_before[1:]
        assert master_agents_after[0] != master_agents_before[0]
        assert master_agents_after[0]["model"] == "gemini-2.0-flash"
        assert master_agents_after[0]["role"] == "Testing Agent Updated"
        assert master_agent_relations_after == master_agent_relations_before
        assert "updated" in master_agents_after[0]["instructions"]
    # redirected to masters.index
    assert response.status_code == 302
    assert response.headers['Location'] == '/masters/'
    # test other model providers
    response = client.post( # openai
        'masters/5/edit',
        data = {'name': 'master name 5', 'description': 'master description 5', "model": "gpt-4.1", "role": "Testing Agent 5", "instructions": "Reply with one word: 'Working'. 1"},
    )
    assert response.status_code == 302
    response = client.post( # anthropic
        'masters/5/edit',
        data = {'name': 'master name 5', 'description': 'master description 5', "model": "claude-3-5-haiku-latest", "role": "Testing Agent 5", "instructions": "Reply with one word: 'Working'. 1"},
    )
    assert response.status_code == 302


def test_delete_agent_master(client, auth, app):
    # user must be logged in
    response = client.post("/masters/5/delete")
    assert response.status_code == 302
    assert response.headers["Location"] == "/auth/login"
    # user must have permission
    auth.login('other', 'other')
    response = client.post("masters/5/delete")
    assert response.status_code == 403
    # agent master gets deleted and others are unaffected.
    auth.login()
    with app.app_context():
        db = get_db()
        masters_before = db.execute("SELECT * FROM masters").fetchall()
        master_agents_before = db.execute("SELECT * FROM master_agents").fetchall()
        master_agent_relations_before = db.execute("SELECT * FROM master_agent_relations").fetchall()
        response = client.post("masters/5/delete")
        masters_after = db.execute('SELECT * FROM masters').fetchall()
        master_agents_after = db.execute("SELECT * FROM master_agents").fetchall()
        master_agent_relations_after = db.execute("SELECT * FROM master_agent_relations").fetchall()
        assert masters_after[:4] == masters_before[:4]
        assert masters_after[4:] == masters_before[5:]
        assert len(masters_after) == len(masters_before) - 1
        assert master_agents_after ==  master_agents_before[1:]
        assert len(master_agents_after) == len(master_agents_before) - 1
        assert master_agent_relations_after == master_agent_relations_before[1:]
        assert len(master_agent_relations_after) == len(master_agent_relations_before) - 1
    # redirected to lists.index
    assert response.status_code == 302
    assert response.headers["Location"] == "/masters/"
