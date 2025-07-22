import pytest
from incontext.db import get_db


def test_index(client, auth):
    response = client.get('/agents/') # when not logged in each page shows links to log in or register. 
    assert b'Log In' in response.data
    assert b'Register' in response.data

    auth.login()
    response = client.get('/agents/') # the index view should display information about the agent that was added with the test data.
    assert b'Log Out' in response.data # when logged in there's a ling to log out.
    assert b'test model' in response.data
    assert b'test name' in response.data
    assert b'test role' in response.data
    assert b'Created: 01.01.2025' in response.data
    assert b'Creator: test' in response.data
    assert b'test\ninstructions' in response.data
    assert b'href="/agents/1/update"' in response.data


@pytest.mark.parametrize('path', (
    'agents/create',
    'agents/1/update',
    'agents/1/delete',
))
def test_login_required(client, path):
    response = client.post(path)
    assert response.headers['Location'] == '/auth/login'


def test_creator_required(app, client, auth):
    # change the agent creator to another user
    with app.app_context():
        db = get_db()
        db.execute('UPDATE agents SET creator_id = 3 WHERE id = 1')
        db.commit()

    auth.login()
    # current user can't modify another user's context
    assert client.post('agents/1/update').status_code == 403
    assert client.post('agents/1/delete').status_code == 403
    # current user doesn't see Edit link
    assert b'href="/agents/1/update"' not in client.get('/agents').data


@pytest.mark.parametrize('path', (
    'agents/2/update',
    'agents/2/delete',
))
def test_exists_required(client, auth, path):
    auth.login()
    assert client.post(path).status_code == 404


def test_create(client, auth, app):
    auth.login()
    assert client.get('agents/create').status_code == 200

    response = client.post('agents/create', data={'model': 'llm', 'name': 'created', 'role': 'talker', 'instructions': 'have a conversation'})

    with app.app_context():
        db = get_db()
        count = db.execute('SELECT COUNT(id) FROM agents').fetchone()[0]
        assert count == 2
    

def test_update(client, auth, app):
    auth.login()
    assert client.get('agents/1/update').status_code == 200
    
    client.post('/agents/1/update', data={'model': 'llm2', 'name': 'updated', 'role': 'senior talker', 'instructions': 'have a better conversation'})

    with app.app_context():
        db = get_db()
        agent = db.execute('SELECT * FROM agents WHERE id = 1').fetchone()
        assert agent['model'] == 'llm2'
        assert agent['name'] == 'updated'
        assert agent['role'] == 'senior talker'
        assert agent['instructions'] == 'have a better conversation'


@pytest.mark.parametrize('path', (
    '/agents/create',
    '/agents/1/update',
))
def test_create_update_validate(client, auth, path):
    auth.login()
    response = client.post(path, data={'model': '', 'name': '', 'role': '', 'instructions': ''})
    assert b'Model, name, role, and instructions are all required.' in response.data

    response = client.post(path, data={'model': 'llm', 'name': '', 'role': '', 'instructions': ''})
    assert b'Model, name, role, and instructions are all required.' in response.data
    
    response = client.post(path, data={'model': 'llm', 'name': 'test', 'role': '', 'instructions': ''})
    assert b'Model, name, role, and instructions are all required.' in response.data

    response = client.post(path, data={'model': 'llm', 'name': 'test', 'role': 'test', 'instructions': ''})
    assert b'Model, name, role, and instructions are all required.' in response.data

    response = client.post(path, data={'model': '', 'name': 'test', 'role': 'test', 'instructions': 'test'})
    assert b'Model, name, role, and instructions are all required.' in response.data


def test_delete(client, auth, app): # the delete view should should redirect to the index url and the agent should no longer exist in the db.
    auth.login()
    response = client.post('/agents/1/delete')
    assert response.headers['Location'] == '/agents/'

    with app.app_context():
        db = get_db()
        agent = db.execute('SELECT * FROM agents WHERE id = 1').fetchone()
        assert agent is None


