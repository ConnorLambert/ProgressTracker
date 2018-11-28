"""
The ``task`` template.
"""

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from ptrak.db import get_db
from ptrak.user import login_required
import time, datetime   #

bp = Blueprint('task', __name__, url_prefix='/task')

@bp.route('/edit/<int:tid>', methods=('GET', 'POST'))
@login_required()
def edit(tid):
    dbcursor = get_db().cursor()
    # get data for this task to pass to the template (and the involvement check)
    dbcursor.execute(
        'SELECT * FROM Tasks WHERE tid=%s',
        (tid,)
    )
    thistask = dbcursor.fetchone()

    # involvement check: is the user actually assigned to this project?
    res = dbcursor.execute(
        'SELECT * FROM Involvements WHERE pid=(%s) AND uid=(%s)',
        (thistask['pid'], session['uid'],)
    )
    if not res:
        flash('You aren\'t involved in that project.', category='warning')
        return redirect(url_for('my.dashboard'))


    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        date_due = request.form['date_due']
        status = request.form['status']

        error = None

        if error is None:
            dbcursor.execute(
                'UPDATE Tasks SET title=%s, description=%s, date_due=%s, status=%s'
                ' WHERE tid=%s',
                (title, description, date_due, status, tid)
            )
            return redirect(url_for('project.project',pid=thistask['pid']))
        flash(error)
        
    return render_template('task/edit.html', thistask=thistask)
