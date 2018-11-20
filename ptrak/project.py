"""
The ``project``` template.
"""

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from ptrak.db import get_db
from ptrak.user import login_required
import time, datetime   #

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

@bp.route('/<int:pid>', methods=('GET', 'POST'))
@login_required
def project(pid):
    """
    The main project view. This will show info,
    including tasks and announcements
    for the given pid.
    """

    if request.method == 'POST':
        statusupdate = request.form['status']
        taskupdate = request.form['taskid']

        error = None

        if statusupdate is None:
            error = "No status update"
        if taskupdate is None:
            error = "No task id"

        if error is None:
            dbcursor = get_db().cursor()
            dbcursor.execute(
                ' UPDATE Tasks'
                ' SET status = (%s), date_updated = CURRENT_TIMESTAMP'
                ' WHERE tid = (%s)',
                (statusupdate, taskupdate,)
            )
            flash('Task status updated.')
            return redirect(url_for('project.project', pid=pid))

        elif error is not None:
            flash('Error updating task status.')
            return redirect(url_for('project.project', pid=pid))

    else:
        dbcursor = get_db().cursor()

        # get a cursor to the DB
        dbcursor = get_db().cursor()
        # get db data in several stages, resisting the urge
        # to mash them all into one massive table
        # note that not all information *has* to be used;
        # it's just gathered in case it's needed
        # first get the details for the project (with creator info)
        num = dbcursor.execute(
            'SELECT pid, uid, firstname, lastname, lastlogin, title, description, CAST(date_due AS char) AS date_due'
            ' FROM Projects JOIN Users ON owner=uid'
            ' WHERE pid=(%s)',
            (pid,)
        )
        thisproject = dbcursor.fetchone()

        if thisproject is None:
            flash('That project doesn\'t exist.', category='danger')
            return redirect(url_for('my.dashboard'))

        # involvement check: is the user actually assigned to this project?
        # for bonus points, we're going to also get the other users involved
        dbcursor.execute(
            ' SELECT *'
            ' FROM Involvements'
            ' NATURAL JOIN Users'
            ' NATURAL JOIN Projects'
            ' WHERE pid=(%s)',
            (pid,)
        )

        projectteam = dbcursor.fetchall()

        # admittedly, these next parts are a little difficult to read
        # first, see if any of the people involved has the current user's uid
        if not any(user['uid'] == session['uid'] for user in projectteam) :
            flash('You aren\'t assigned to that project.', category='danger')
            return redirect(url_for('my.dashboard'))
        else:
            # don't ask about the syntax of this one. It uses a 'generator expression'
            # to extract the row that matches the current user, then extracts
            # his/her rank from that row. That's all I know.
            g.rank = (row for row in projectteam if row["uid"] == session['uid']).__next__()['rank']

        # then get the announcements with author info
        dbcursor.execute(
            'SELECT aid, uid, firstname, lastname, content, CAST(date_made AS char) AS date_made, lastlogin'
            ' FROM Announcements JOIN Users ON author=uid'
            ' WHERE pid=(%s)',
            (pid,)
        )
        announcements = dbcursor.fetchall()

        # next get the task list and submitter info
        dbcursor.execute(
            'SELECT tid, uid, firstname, lastname, title, status, date_submitted, due_date, CAST(date_updated AS char) AS date_updated, tags, description'
            ' FROM Tasks JOIN Users ON Tasks.creator=Users.uid'
            ' WHERE Tasks.pid=(%s)'
            ' ORDER BY Tasks.date_updated DESC',
            (pid,)
        )
        tasks = dbcursor.fetchall()

        # and pass all of this data to the template
        return render_template('project/project.html', announcements=announcements, tasks=tasks, thisproject=thisproject, projectteam=projectteam)

@bp.route('/new', methods=('GET', 'POST'))
@login_required(level=3)
def new():
    """
    Add a new project.
    """
    # get the db cursor at the start; it'll be needed throughout
    dbcursor = get_db().cursor()

    if request.method == 'POST':
        # get the form elements
        owner = session['uid']
        description = request.form['description']
        date_due = request.form['date_due']
        name = request.form['name']

        # TODO: validate the elements
        error = None
        #Converts the due date string to a useable Timestamp format
        tsdue = time.strftime('%Y-%m-%d %H:%M:%S', datetime.datetime.strptime(date_due, "%Y-%m-%d").timetuple())

        # and do the insertion and redirect
        if error is None:

            #Add the project to the project table
            dbcursor.execute(
                'INSERT INTO Projects (owner, description, date_due, title)'
                ' VALUES (%s, %s, %s, %s)',
                (owner, description, tsdue, name,)
            )

            #Grab newest pid added to the Project table
            dbcursor.execute(
                'SELECT LAST_INSERT_ID() AS pid'
            )
            newpid = dbcursor.fetchone()

            #Add the user and project to the Involvements TABLE, set creator to project rank 3
            dbcursor.execute(
                'INSERT INTO Involvements (uid, pid, rank)'
                ' VALUES (%s, %s, %s)',
                (session['uid'], newpid['pid'], 3,)
            )

            # return the user to the newly-inserted project
            return redirect(url_for('project.project', pid=newpid['pid']))

    #return render_template('project/new.html')
    return render_template('project/new.html')

@bp.route('/<int:pid>/newtask')
@login_required
def newtask(pid):
    # involvement check: is the user actually assigned to this project?
    if str(pid) not in g.user['projects'].split(';'):
        flash('You aren\'t assigned to that project.', category='danger')
        return redirect(url_for('my.dashboard'))

    return 'STUB: adding new task to project {}'.format(pid)

@bp.route('/<int:pid>/edit')
@login_required(level=3)
def edit(pid):
    # involvement check: is the user actually assigned to this project?
    if str(pid) not in g.user['projects'].split(';'):
        flash('You aren\'t assigned to that project.')
        return redirect(url_for('my.dashboard'))

    return 'STUB: editing project {}'.format(pid)

@bp.route('/<int:pid>/announce')
@login_required(level=3)
def announce(pid):
    # involvement check: is the user actually assigned to this project?
    if str(pid) not in g.user['projects'].split(';'):
        flash('You aren\'t assigned to that project.')
        return redirect(url_for('my.dashboard'))

    return 'STUB: adding announcement to project {}'.format(pid)

@bp.route('/<int:pid>/settings', methods=('GET', 'POST'))
@login_required(level=3)
def settings(pid):
    if request.method == 'POST':
        return 'STUB: editing project settings {}'.format(pid)

    else:

        dbcursor = get_db().cursor()

        num = dbcursor.execute(
            'SELECT pid, uid, firstname, lastname, lastlogin, title, description, CAST(date_due AS char) AS date_due'
            ' FROM Projects JOIN Users ON owner=uid'
            ' WHERE pid=(%s)',
            (pid,)
        )
        thisproject = dbcursor.fetchone()

        if thisproject is None:
            flash('That project doesn\'t exist.', category='danger')
            return redirect(url_for('my.dashboard'))

        # involvement check: is the user actually assigned to this project?
        dbcursor.execute(
            ' SELECT *'
            ' FROM Involvements'
            ' WHERE (Involvements.uid = (%s)) AND (Involvements.pid = (%s))'
            ' ORDER BY Involvements.pid DESC',
            (session['uid'], pid,)
        )

        projectscheck = dbcursor.fetchone()

        if projectscheck is None or projectscheck['uid'] < 3:
            flash('You don\'t have permission to edit this project.')
            return redirect(url_for('my.dashboard'))

        # then get the announcements with author info
        dbcursor.execute(
            'SELECT aid, uid, firstname, lastname, content, CAST(date_made AS char) AS date_made, lastlogin'
            ' FROM Announcements JOIN Users ON author=uid'
            ' WHERE pid=(%s)',
            (pid,)
        )
        announcements = dbcursor.fetchall()

        # next get the task list and submitter info
        dbcursor.execute(
            'SELECT tid, uid, firstname, lastname, title, status, date_submitted, due_date, CAST(date_updated AS char) AS date_updated, tags, description'
            ' FROM Tasks JOIN Users ON Tasks.creator=Users.uid'
            ' WHERE Tasks.pid=(%s)'
            ' ORDER BY Tasks.date_updated DESC',
            (pid,)
        )
        tasks = dbcursor.fetchall()

        # and pass all of this data to the template
        return render_template('project/settings.html', announcements=announcements, tasks=tasks, thisproject=thisproject)
