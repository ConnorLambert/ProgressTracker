"""
The ``project``` template.
"""

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from ptrak.db import get_db
from ptrak.user import login_required

bp = Blueprint('project', __name__, url_prefix='/project')

@bp.route('/')
@login_required
def index():
    """
    This is a dummy route, to ensure that if the user
    navigates to /project/ (without a project id),
    he/she will be shown something other than a 404.
    In fact, it will send the user to the dashboard.
    """
    return redirect(url_for('my.dashboard'))

@bp.route('/<int:pid>')
@login_required
def project(pid):
    """
    The main project view. This will show info,
    including tasks and announcements
    for the given pid.
    """
    # get a cursor to the DB
    dbcursor = get_db().cursor()
    # get db data in several stages, resisting the urge
    # to mash them all into one massive table
    # note that not all information *has* to be used;
    # it's just gathered in case it's needed
    # first get the announcements with author info
    dbcursor.execute(
        'SELECT uid, firstname, lastname, content, date_made, lastlogin'
        ' FROM Announcements JOIN Users ON author=uid'
        ' WHERE pid=(%s)',
        (pid,)
    )
    announcements = dbcursor.fetchall()

    # next get the task list and submitter info
    dbcursor.execute(
        'SELECT uid, firstname, lastname, title, status, date_submitted, due_date, date_updated, tags, description'
        ' FROM Tasks JOIN Users ON Tasks.creator=Users.uid'
        ' WHERE Tasks.pid=(%s)',
        (pid,)
    )
    tasks = dbcursor.fetchall()

    # and now get the details for the project (with creator info)
    dbcursor.execute(
        'SELECT uid, firstname, lastname, lastlogin, title, description, date_due'
        ' FROM Projects JOIN Users ON owner=uid'
        ' WHERE pid=(%s)',
        (pid,)
    )
    thisproject = dbcursor.fetchone()

    # and pass all of this data to the template
    return render_template('project/project.html', announcements=announcements, tasks=tasks, thisproject=thisproject)

@bp.route('/new')
@login_required(level=3)
def new():
    return 'STUB: adding new project'

@bp.route('/<int:pid>/newtask')
@login_required
def newtask(pid):
    return 'STUB: adding new task to project {}'.format(pid)

@bp.route('/<int:pid>/edit')
@login_required(level=3)
def edit(pid):
    return 'STUB: editing project {}'.format(pid)
