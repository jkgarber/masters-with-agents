from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from incontext.auth import login_required
from incontext.db import get_db

bp = Blueprint('master_agents', __name__, url_prefix='/master-agents')

@bp.route('/')
@login_required
def index():
    master_agents = get_master_agents()
    return render_template('master-agents/index.html', master_agents=master_agents)


@bp.route('/new', methods=('GET', 'POST'))
@login_required
def new():
    if request.method == 'POST':
        error = None
        name = request.form['name']
        description = request.form['description']
        model = request.form['model']
        vendor = None
        if model in ['gpt-4.1-mini', 'gpt-4.1']:
            vendor = 'openai'
        elif model in ['claude-3-5-haiku-latest', 'claude-3-7-sonnet-latest']:
            vendor = 'anthropic'
        elif model in ["gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-1.5-flash", "gemini-1.5-flash-8b", "gemini-1.5-pro"]:
            vendor = 'google'
        else:
            error = "Model not recognized as a supported model."
        role = request.form['role']
        instructions = request.form['instructions']
        if not name or not model or not role or not instructions:
            error = 'Name, model, role, and instructions are all required.'
        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO master_agents (name, description, model, role, instructions, creator_id, vendor)'
                ' VALUES (?, ?, ?, ?, ?, ?, ?)',
                (name, description, model, role, instructions, g.user['id'], vendor)
            )
            db.commit()
            return redirect(url_for('master_agents.index'))
    return render_template('master-agents/new.html')


@bp.route('/<int:master_agent_id>/view')
@login_required
def view(master_agent_id):
    master_agent = get_master_agent(master_agent_id)
    return render_template('master-agents/view.html', master_agent=master_agent)


@bp.route('/<int:master_agent_id>/edit', methods=('GET', 'POST'))
@login_required
def edit(master_agent_id):
    master_agent = get_master_agent(master_agent_id)
    if request.method == "POST":
        error = None
        name = request.form['name']
        description = request.form['description']
        model = request.form["model"]
        if model in ['gpt-4.1-mini', 'gpt-4.1']:
            vendor = 'openai'
        elif model in ['claude-3-5-haiku-latest', 'claude-3-7-sonnet-latest']:
            vendor = 'anthropic'
        elif model in ["gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-1.5-flash", "gemini-1.5-flash-8b", "gemini-1.5-pro"]:
            vendor = 'google'
        else:
            error = "Model not recognized as a supported model."
        role = request.form["role"]
        instructions = request.form["instructions"]
        if not name or not model or not role or not instructions:
            error = "Name, model, role, and instructions are all required."
        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "UPDATE master_agents"
                " SET name = ?, description = ?, model = ?, role = ?, instructions = ?, vendor = ?"
                " WHERE id = ?",
                (name, description, model, role, instructions, vendor, master_agent_id)
            )
            db.commit()
            return redirect(url_for('master_agents.index'))
    return render_template("master-agents/edit.html", master_agent=master_agent)


@bp.route("<int:master_agent_id>/delete", methods=("POST",))
@login_required
def delete(master_agent_id):
    master_agent = get_master_agent(master_agent_id)
    db = get_db()
    db.execute("DELETE FROM master_agents WHERE id = ?", (master_agent_id,))
    db.commit()
    return redirect(url_for('master_agents.index'))


def get_master_agents():
    db = get_db()
    master_agents = db.execute(
        'SELECT m.id, m.created, m.name, m.description'
        ' FROM master_agents m'
        ' WHERE m.creator_id = ?'
        (g.user['id'],)
    ).fetchall()
    return master_agents


def get_master_agent(master_agent_id, check_access=True):
    db = get_db()
    master_agent = db.execute(
        'SELECT m.id, m.creator_id, m.created, m.name, m.description, m.model, m.role, m.instructions'
        ' FROM master_agents m'
        ' WHERE m.id = ?',
        (master_agent_id,)
    ).fetchone()
    if master_agent is None:
        abort(404)
    if check_access:
        if master_agent['creator_id'] != g.user['id']:
            abort(403)
    return master_agent
