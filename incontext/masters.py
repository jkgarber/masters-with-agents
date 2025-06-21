from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from incontext.auth import login_required
from incontext.db import get_db

bp = Blueprint('masters', __name__, url_prefix='/masters')

@bp.route('/')
@login_required
def index():
    list_masters = get_user_masters('list')
    agent_masters = get_user_masters('agent')
    return render_template('masters/index.html', list_masters=list_masters, agent_masters=agent_masters)


@bp.route('/new/<master_type>', methods=('GET', 'POST'))
@login_required
def new(master_type):
    if master_type not in ['list', 'agent']:
        abort(404)
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        error = None
        if master_type == 'list':
            if not name:
                error = 'Name is required.'
            if error is not None:
                flash(error)
            else:
                db = get_db()
                db.execute(
                    'INSERT INTO masters (name, master_type, description, creator_id)'
                    ' VALUES (?, ?, ?, ?)',
                    (name, master_type, description, g.user['id'])
                )
                db.commit()
                return redirect(url_for('masters.index'))
        elif master_type == 'agent':
            description = request.form["description"]
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
            if not model or not name or not role or not instructions:
                error = 'Model, name, role, and instructions are all required.'
            if error is not None:
                flash(error)
            else:
                db = get_db()
                cur = db.cursor()
                cur.execute(
                    'INSERT INTO masters (master_type, name, description, creator_id)'
                    ' VALUES (?, ?, ?, ?)',
                    (master_type, name, description, g.user["id"])
                )
                master_id = cur.lastrowid
                cur.execute(
                    'INSERT INTO master_agents (model, role, instructions, creator_id, vendor)'
                    ' VALUES (?, ?, ?, ?, ?)',
                    (model, role, instructions, g.user['id'], vendor)
                )
                master_agent_id = cur.lastrowid
                cur.execute(
                    "INSERT INTO master_agent_relations (master_id, master_agent_id)"
                    " VALUES (?, ?)",
                    (master_id, master_agent_id)
                )
                db.commit()
                return redirect(url_for('masters.index'))
    return render_template('masters/new.html', master_type=master_type)


@bp.route('/<int:master_id>/view')
@login_required
def view(master_id):
    master = get_master(master_id)
    return render_template('masters/view.html', master=master)


@bp.route('/<int:master_id>/edit', methods=('GET', 'POST'))
@login_required
def edit(master_id):
    master = get_master(master_id)
    if request.method == "POST":
        name = request.form['name']
        description = request.form['description']
        error = None
        if not name:
            if master["master_type"] == "list":
                error = 'Name is required.'
            elif master["master_type"] == "agent":
                error = "Model, name, role, and instructions are all required."
        if master["master_type"] == "agent":
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
            if not model or not role or not instructions:
                error = "Model, name, role, and instructions are all required."
        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE masters SET name = ?, description = ?'
                ' WHERE id = ?',
                (name, description, master_id)
            )
            if master["master_type"] == "agent":
                db.execute(
                    "UPDATE master_agents"
                    " SET model = ?, role = ?, instructions = ?, vendor = ?"
                    " WHERE id = ?",
                    (model, role, instructions, vendor, master["master_agent_id"])
                )
            db.commit()
            return redirect(url_for('masters.index'))
    return render_template("masters/edit.html", master=master)


@bp.route("<int:master_id>/delete", methods=("POST",))
@login_required
def delete(master_id):
    master = get_master(master_id)
    db = get_db()
    if master["master_type"] == "list":
        # Delete master-related details
        db.execute(
            'DELETE FROM master_details'
            ' WHERE id IN'
            ' (SELECT master_detail_id FROM master_detail_relations WHERE master_id = ?)',
            (master_id,)
        )
        # Delete master-related items
        db.execute(
            'DELETE FROM master_items'
            ' WHERE id IN'
            ' (SELECT master_item_id FROM master_item_relations WHERE master_id = ?)',
            (master_id,)
        )
        # Delete item-detail relations
        db.execute(
            'DELETE FROM master_item_detail_relations'
            ' WHERE master_item_id IN'
            ' (SELECT master_item_id FROM master_item_relations WHERE master_id = ?)',
            (master_id,)
        )
        # Delete master-item relations
        db.execute('DELETE FROM master_item_relations WHERE master_id = ?',(master_id,))
        # Delete master-detail relations
        db.execute('DELETE FROM master_detail_relations WHERE master_id = ?', (master_id,))
    elif master["master_type"] == "agent":
        # Delete from master_agents
        db.execute("DELETE FROM master_agents WHERE id = ?", (master["master_agent_id"],))
        # Delete from master_agent_relations
        db.execute("DELETE FROM master_agent_relations WHERE master_id = ?", (master_id,))
    # Delete master
    db.execute('DELETE FROM masters WHERE id = ?', (master_id,))
    db.commit()
    return redirect(url_for('masters.index'))


@bp.route('<int:master_id>/items/new', methods=("GET", "POST"))
@login_required
def new_item(master_id):
    master = get_master(master_id)
    if request.method == "POST":
        name = request.form['name']
        detail_fields = []
        details = [detail for detail in master['details']]
        for detail in details:
            detail_id = detail['id']
            detail_content = request.form[str(detail_id)]
            detail_fields.append((detail_id, detail_content))
        error = None
        if not name:
            error = 'Name is required.'
        if error is not None:
            flash(error)
        else:
            db = get_db()
            cur = db.cursor()
            cur.execute(
                'INSERT INTO master_items (name, creator_id)'
                ' VALUES (?, ?)',
                (name, g.user['id'])
            )
            item_id = cur.lastrowid
            cur.execute(
                'INSERT INTO master_item_relations (master_id, master_item_id)'
                ' VALUES (?, ?)',
                (master_id, item_id)
            )
            relations = []
            for field in detail_fields:
                relations.append((item_id,) + field)
            cur.executemany(
                'INSERT INTO master_item_detail_relations (master_item_id, master_detail_id, content)'
                ' VALUES(?, ?, ?)',
                relations
            )
            db.commit()
            return redirect(url_for('masters.view', master_id=master_id))
    return render_template("masters/items/new.html", master=master)


@bp.route("<int:master_id>/items/<int:item_id>/view")
@login_required
def view_item(master_id, item_id):
    master = get_master(master_id)
    requested_item = None
    for item in master['items']:
        if item['id'] == item_id:
            requested_item = item
    if not requested_item:
        abort(404)
    return render_template("masters/items/view.html", master=master, item=requested_item, details=master["details"])


@bp.route("<int:master_id>/items/<int:item_id>/edit", methods=("GET", "POST"))
@login_required
def edit_item(master_id, item_id):
    master = get_master(master_id)
    requested_item = next((item for item in master["items"] if item["id"] == item_id), None)
    if not requested_item:
        abort(404)
    if request.method == "POST":
        name = request.form['name']
        detail_fields = []
        details = [detail for detail in master['details']]
        for detail in details:
            detail_id = detail['id']
            detail_content = request.form[str(detail_id)]
            detail_fields.append((detail_content, item_id, detail_id))
        error = None
        if not name:
            error = 'Name is required.'
        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE master_items SET name = ?'
                ' WHERE id = ?',
                (name, item_id)
            )
            db.executemany(
                'UPDATE master_item_detail_relations'
                ' SET content = ?'
                ' WHERE master_item_id = ?'
                ' AND master_detail_id = ?',
                detail_fields
            )
            db.commit()
            return redirect(url_for('masters.view', master_id=master_id))
    return render_template("masters/items/edit.html", master=master, item=requested_item)


@bp.route("<int:master_id>/items/<int:item_id>/delete", methods=("POST",))
@login_required
def delete_item(master_id, item_id):
    master = get_master(master_id)
    requested_item = next((item for item in master["items"] if item["id"] == item_id), None)
    if not requested_item:
        abort(404)
    details = master["details"]
    db = get_db()
    db.execute('DELETE FROM master_items WHERE id = ?', (item_id,))
    db.execute('DELETE FROM master_item_detail_relations WHERE master_item_id = ?', (item_id,))
    db.execute(
        'DELETE from master_item_relations'
        ' WHERE master_id = ? AND master_item_id = ?',
        (master_id, item_id)
    )
    db.commit()
    return redirect(url_for('masters.view', master_id=master_id))


@bp.route("/<int:master_id>/details/new", methods=("GET", "POST"))
@login_required
def new_detail(master_id):
    master = get_master(master_id)
    if request.method == "POST":
        name = request.form['name']
        description = request.form['description']
        error = None
        if not name:
            error = 'Name is required.'
        if error is not None:
            flash(error)
        else:
            db = get_db()
            cur = db.cursor()
            cur.execute(
                'INSERT INTO master_details (name, description, creator_id)'
                ' VALUES (?, ?, ?)',
                (name, description, g.user['id'])
            )
            detail_id = cur.lastrowid
            cur.execute(
                'INSERT INTO master_detail_relations (master_id, master_detail_id)'
                ' VALUES (?, ?)',
                (master_id, detail_id)
            )
            master_items = master["items"]
            data = [(item['id'], detail_id, '') for item in master_items]
            cur.executemany(
                'INSERT INTO master_item_detail_relations (master_item_id, master_detail_id, content)'
                'VALUES (?, ?, ?)',
                data
            )
            db.commit()
            return redirect(url_for('masters.view', master_id=master["id"]))
    return render_template("masters/details/new.html", master=master)


@bp.route("/<int:master_id>/details/<int:detail_id>/edit", methods=("GET", "POST"))
@login_required
def edit_detail(master_id, detail_id):
    master = get_master(master_id)
    requested_detail = next((detail for detail in master["details"] if detail["id"] == detail_id), None)
    if requested_detail is None:
        abort(404)
    if request.method == "POST":
        name = request.form['name']
        description = request.form['description']
        error = None
        if not name:
            error = 'Name is required.'
        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE master_details SET name = ?, description = ?'
                ' WHERE id = ?',
                (name, description, detail_id)
            )
            db.commit()
            return redirect(url_for('masters.view', master_id=master_id))
    return render_template("masters/details/edit.html", master=master, detail=requested_detail)


@bp.route('/<int:master_id>/details/<int:detail_id>/delete', methods=('POST',))
@login_required
def delete_detail(master_id, detail_id):
    master = get_master(master_id)
    requested_detail = next((detail for detail in master["details"] if detail["id"] == detail_id), None)
    if not requested_detail:
        abort(404)
    db = get_db()
    db.execute('DELETE FROM master_details WHERE id = ?', (detail_id,))
    db.execute('DELETE FROM master_item_detail_relations WHERE master_detail_id = ?', (detail_id,))
    db.execute('DELETE FROM master_detail_relations WHERE master_detail_id = ?', (detail_id,))
    db.commit()
    return redirect(url_for('masters.view', master_id=master_id))


def get_user_masters(master_type):
    db = get_db()
    user_masters = db.execute(
        'SELECT m.id, m.name, m.master_type, m.description, m.created'
        ' FROM masters m'
        ' WHERE m.creator_id = ?'
        ' AND m.master_type = ?',
        (g.user['id'], master_type)
    ).fetchall()
    return user_masters


def get_master(master_id, check_access=True):
    db = get_db()
    master = db.execute(
        'SELECT m.id, m.creator_id, m.created, m.master_type, m.name, m.description'
        ' FROM masters m'
        ' WHERE m.id = ?',
        (master_id,)
    ).fetchone()
    if master is None:
        abort(404)
    if check_access:
        if master['creator_id'] != g.user['id']:
            abort(403)
    if master['master_type'] == 'list':
        list_master = {}
        for key in master.keys():
            list_master[key] = master[key]
        items = db.execute(
            'SELECT i.id, i.name, i.created, u.username'
            ' FROM master_items i'
            ' JOIN master_item_relations m'
            ' ON m.master_item_id = i.id'
            ' JOIN users u'
            ' ON u.id = i.creator_id'
            ' WHERE m.master_id = ?',
            (master_id,)
        ).fetchall()
        list_master['items'] = []
        for item in items:
            new_item = {}
            for key in item.keys():
                new_item[key] = item[key]
            new_item['contents'] = []
            item_id = str(item['id'])
            list_master['items'].append(new_item)
        details = db.execute(
            'SELECT d.id, d.name, d.description'
            ' FROM master_details d'
            ' JOIN master_detail_relations m'
            ' ON m.master_detail_id = d.id'
            ' WHERE m.master_id = ?',
            (master_id,)
        ).fetchall()
        list_master['details'] = details
        contents = db.execute(
            'SELECT master_item_id, content'
            ' FROM master_item_detail_relations'
            ' WHERE master_detail_id IN'
            ' (SELECT master_detail_id'
            '  FROM master_detail_relations'
            '  WHERE master_id = ?)',
            (master_id,)
        ).fetchall()
        for content in contents:
            item_id = content['master_item_id']
            item = next((item for item in list_master["items"] if item["id"] == item_id), None)
            item['contents'].append(content['content'])
        return list_master
    elif master["master_type"] == "agent":
        agent_master = db.execute(
            "SELECT m.master_type, u.username, m.id, m.created, m.name, m.description, a.model, a.role, a.instructions, a.vendor, a.id as master_agent_id"
            " FROM masters m"
            " JOIN users u ON u.id = m.creator_id"
            " JOIN master_agent_relations r ON r.master_id = m.id"
            " JOIN master_agents a ON a.id = r.master_agent_id"
            " WHERE m.id = ?",
            (master_id,)
        ).fetchone()
        return agent_master
