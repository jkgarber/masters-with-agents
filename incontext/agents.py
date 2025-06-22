from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from incontext.auth import login_required
from incontext.db import get_db
from incontext.master_agents import get_agent_models

bp = Blueprint('agents', __name__, url_prefix='/agents')

@bp.route('/')
@login_required
def index():
    agents = get_agents()
    return render_template('agents/index.html', agents=agents)


@bp.route('/new', methods=('GET', 'POST'))
@login_required
def new():
    agent_models = get_agent_models()
    if request.method == 'POST':
        error = None
        name = request.form['name']
        description = request.form["description"]
        model_id = int(request.form['model_id'])
        model = next((agent_model for agent_model in agent_models if agent_model["id"] == model_id), None)
        role = request.form['role']
        instructions = request.form['instructions']
        if not name or not model or not role or not instructions:
            error = 'Name, model, role, and instructions are all required.'
        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO agents (name, description, model_id, role, instructions, creator_id)'
                ' VALUES (?, ?, ?, ?, ?, ?)',
                (name, description, model_id, role, instructions, g.user['id'])
            )
            db.commit()
            return redirect(url_for('agents.index'))
    return render_template('agents/new.html', agent_models=agent_models)


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id): # id corresponds to the <int:id> in the route. Flask will capture the "id" from the url, ensure it's an int, and pass it as the id argument. To generate a URL to the update page, `url_for()` needs to be passed the `id` such as `url_for('context.update', id=context['id']).
    agent = get_agent(id)

    if request.method == 'POST':
        model = request.form['model']
        name = request.form['name']
        role = request.form['role']
        instructions = request.form['instructions']
        error = None

        if not model or not name or not role or not instructions:
            error = 'Model, name, role, and instructions are all required.'

        if error is not None:
            flash(error)
        else:
            if model in ['gpt-4.1-mini', 'gpt-4.1']:
                vendor = 'openai'
            elif model in ['claude-3-5-haiku-latest', 'claude-3-7-sonnet-latest']:
                vendor = 'anthropic'
            else:
                vendor = 'google'
            db = get_db()
            db.execute(
                'UPDATE agents SET model = ?, name = ?, role = ?, instructions = ?, vendor = ?'
                ' WHERE id = ?',
                (model, name, role, instructions, vendor, id)
            )
            db.commit()
            return redirect(url_for('agents.index'))
    
    return render_template('agents/update.html', agent=agent)

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    agent = get_agent(id)
    db = get_db()
    relations = db.execute(
        'SELECT COUNT(id) FROM conversation_agent_relations WHERE agent_id = ?', (id,)
    ).fetchone()
    n = relations[0]
    if n > 0:
        flash(f'Cannot delete this agent as it is linked to {n} conversation(s).', 'error')
        return redirect(url_for('agents.update', id=id))
    else:
        db.execute('DELETE FROM agents WHERE id = ?', (id,))
        db.commit()
        return redirect(url_for('agents.index'))


def get_agents():
    db = get_db()
    agents = db.execute(
        'SELECT a.id, a.creator_id, a.created, a.name, a.description, a.model_id, a.role, a.instructions, u.username'
        ' FROM agents a JOIN users u ON a.creator_id = u.id'
    ).fetchall()
    return agents


def get_agent(id, check_creator=True):
    agent = get_db().execute(
        'SELECT a.id, model, name, role, instructions, created, creator_id, username, a.vendor'
        ' FROM agents a JOIN users u ON a.creator_id = u.id'
        ' WHERE a.id = ?',
        (id,)
    ).fetchone()
    if agent is None:
        abort(404)
    if check_creator and agent['creator_id'] != g.user['id']:
        abort(403)
    return agent
