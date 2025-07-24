import pytest
from incontext.db import get_db


def test_index_master_agent(app, client, auth):
    # user must be logged in
    response = client.get("master-agents/")
    assert response.status_code == 302
    assert response.headers["Location"] == "/auth/login"
    # user must be admin
    auth.login("other", "other")
    response = client.get("master-agents/")
    assert response.status_code == 403
    # user must be master agent creator
    auth.login("test", "test")
    response = client.get("master-agents/")
    assert response.status_code == 200
    # master agent data gets served
    assert b"master agent name 1" in response.data
    assert b"master agent description 1" in response.data
    assert b"master agent name 2" in response.data
    assert b"master agent description 2" in response.data
    assert b"master agent name 3" in response.data
    assert b"master agent description 3" in response.data


def test_new_master_agent(app, client, auth):
    # user must be logged in
    response = client.get("/master-agents/new")
    assert response.status_code == 302
    assert response.headers["Location"] == "/auth/login"
    # user must be admin
    auth.login("other", "other")
    response = client.get("/master-agents/new")
    assert response.status_code == 403
    auth.login()
    response = client.get("/master-agents/new")
    assert response.status_code == 200
    # agent models get served
    with app.app_context():
        db = get_db()
        agent_models = db.execut("SELECT model_name FROM agent_models")
        for agent_model in agent_models:
            assert agent_model["model_name"].encode() in response.data
    # data validation
    response = client.post(
        "master-agents/new",
        data={
			"name": "",
			"description": "master agent description 4",
			"model_id": "1",
			"role": "master agent role 4",
            "instructions": "Reply with one word: Working"
        }
    )
    assert b'Name, model, role, and instructions are all required.' in response.data
    response = client.post(
        "master-agents/new",
        data={
			"name": "master agent name 4",
			"description": "master agent description 4",
			"model_id": "",
			"role": "master agent role 4",
            "instructions": "Reply with one word: Working"
        }
    )
    assert b'Model, name, role, and instructions are all required.' in response.data
    # invalid model
    response = client.post(
        "master-agents/new",
        data={
			"name": "master agent name 4",
			"description": "master agent description 4",
			"model_id": "1",
			"role": "",
            "instructions": "Reply with one word: Working"
        }
    )
    assert b'Model not recognized as a supported model.' in response.data
    response = client.post(
        "master-agents/new",
        data={
			"name": "master agent name 4",
			"description": "master agent description 4",
			"model_id": "1",
			"role": "master agent role 4",
            "instructions": ""
        }
    )
    assert b"Model, name, role, and instructions are all required." in response.data
    # master agent is saved to database
    response = client.post(
        "master-agents/new",
        data = {
            "name": "master agent name 4",
            "description": "master agent description 4",
            "model_id": "1",
            "role": "master agent role 4",
            "instructions": "Reply with one word: Working"
        }
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
    # redirected to master_agents.index
    assert response.status_code == 302
    assert response.headers["Location"] == "/master-agents/"


def test_view_master_agent(app, client, auth):
    # user must be logged in
    response = client.get("master-agents/1/view")
    assert response.status_code == 302
    assert response.headers["Location"] == "/auth/login"
    # user must be admin
    auth.login("other", "other")
    response = client.get("master-agents/1/view")
    assert response.status_code == 403
    auth.login()
    response = client.get("master-agents/1/view")
    assert response.status_code == 200
    # master agent data gets served
    assert b"master agent name 1" in response.data
    assert b"master agent description 1" in response.data
    assert b"GPT-4.1 nano" in response.data
    assert b"OpenAI" in response.data
    assert b"master agent role 1" in response.data
    assert b"Reply with one word: Working" in response.data
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
