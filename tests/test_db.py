import sqlite3
import os

import pytest
from incontext.db import get_db
from flask import g, session


def test_get_close_db(app):
    with app.app_context():
        db = get_db()
        assert db is get_db() # within an application context, `get_db` should return the same connection each time it's called.

    with pytest.raises(sqlite3.ProgrammingError) as e:
        db.execute('SELECT 1')

    assert 'closed' in str(e.value) # After the context, the connection should be closed.


def test_init_db_command(runner, monkeypatch):
    class Recorder:
        called = False

    def fake_init_db():
        Recorder.called = True

    monkeypatch.setattr('incontext.db.init_db', fake_init_db) # pytest's monkeypatch replaces the `init_db` function with one that does nothing but record that it was called.
    result = runner.invoke(args=['init-db']) # the runner fixture called the `init-db` command (which calls the monkeypatched `init_db` function).
    assert 'Initialized' in result.output
    assert Recorder.called


def test_data_entry(app):
    with app.app_context():
        db = get_db()
        master_item_count = db.execute('SELECT COUNT(id) AS count FROM master_items').fetchone()['count']
        assert master_item_count == 6
        master_detail_count = db.execute('SELECT COUNT(id) AS count FROM master_details').fetchone()['count']
        assert master_detail_count == 6
        midr_count = db.execute('SELECT COUNT(id) AS count FROM master_item_detail_relations').fetchone()['count']
        assert midr_count == 10
        master_count = db.execute('SELECT COUNT(id) AS count FROM masters').fetchone()['count']
        assert master_count == 7
        mir_count = db.execute('SELECT COUNT(id) AS count FROM master_item_relations').fetchone()['count']
        assert mir_count == 6
        mdr_count = db.execute('SELECT COUNT(id) AS count FROM master_detail_relations').fetchone()['count']
        assert mdr_count == 6
        master_agent_count = db.execute("SELECT COUNT(id) AS count FROM master_agents").fetchone()["count"]
        assert master_agent_count == 3
        mar_count = db.execute("SELECT COUNT(id) AS count FROM master_agent_relations").fetchone()["count"]
        assert mar_count == 3
       

def test_admin_login(client, auth):
    username = 'admin'
    password = os.environ.get('IC_ADMIN_PW_RAW')
    auth.login(username, password)
    with client:
        client.get('/')
        assert session['user_id'] == 1
        assert g.user['username'] == 'admin'

