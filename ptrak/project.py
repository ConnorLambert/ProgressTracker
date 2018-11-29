"""
The ``project`` template.
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
    # get a cursor to the DB
    dbcursor = get_db().cursor()

    if request.method == 'POST':
        statusupdate = request.form['status']
        taskupdate = request.form['taskid']

        error = None

        if statusupdate is None:
            error = "No status update"
        if taskupdate is None:
            error = "No task id"

        if error is None:
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
            g.rank = next(row for row in projectteam if row["uid"] == session['uid'])['rank']

        # then get the announcements with author info
        dbcursor.execute(
            'SELECT aid, uid, firstname, lastname, content, CAST(date_made AS char) AS date_made, lastlogin'
            ' FROM Announcements JOIN Users ON author=uid'
            ' WHERE pid=(%s) ORDER BY date_made DESC',
            (pid,)
        )
        announcements = dbcursor.fetchall()

        # next get the task list and submitter info
        dbcursor.execute(
            'SELECT tid, uid, firstname, lastname, title, status, date_submitted, date_due, CAST(date_updated AS char) AS date_updated, tags, description'
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

@bp.route('/<int:pid>/newtask', methods=('GET', 'POST'))
@login_required
def newtask(pid):
    dbcursor = get_db().cursor()
    # involvement check: is the user actually assigned to this project?
    res = dbcursor.execute(
        'SELECT * FROM Involvements WHERE pid=(%s) AND uid=(%s)',
        (pid, session['uid'],)
    )
    if not res:
        flash('You aren\'t involved in that project.', category='warning')
        return redirect(url_for('my.dashboard'))

    if request.method == 'POST':
        title = request.form['title']
        date_due = request.form['date_due']
        description = request.form['description']
        status = request.form['status'] 

        error = None
        # TODO: add validation
        if error is None:
            dbcursor.execute(
                'INSERT INTO Tasks'
                ' (title, date_due, description, status, pid, creator)'
                ' VALUES (%s, %s, %s, %s, %s, %s)',
                (title, date_due, description, status, pid, session['uid'],)
            )
            return redirect(url_for('project.project', pid=pid))
        flash(error, category='warning')

    return render_template('project/newtask.html')

@bp.route('/<int:pid>/edit', methods=('GET', 'POST'))
@login_required(level=3)
def edit(pid):
    dbcursor = get_db().cursor()
    # involvement check: is the user actually assigned to this project?
    # and is (s)he at least project manager?
    res = dbcursor.execute(
        'SELECT * FROM Involvements WHERE pid=(%s) AND uid=(%s)'
        ' AND rank > 1',
        (pid, session['uid'],)
    )
    if not res:
        flash('You don\'t have permission to edit that project.', category='warning')
        return redirect(url_for('project.project', pid=pid))


    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        date_due = request.form['date_due']
        toremove = request.form.getlist('toremove')
        toadd = request.form.getlist('toadd')

        # commit changes
        dbcursor.execute(
            'UPDATE Projects SET title=%s, description=%s, date_due=%s'
            ' WHERE pid=%s',
            (title, description, date_due, pid,)
        )

        # add new users (as rank 1!)
        for uid in toadd:
            dbcursor.execute(
                'INSERT INTO Involvements (uid, pid, rank)'
                ' VALUES (%s, %s, %s)',
                (uid, pid, 1)
            )
        # remove old users
        for uid in toremove:
            dbcursor.execute(
                'DELETE FROM Involvements WHERE uid=%s AND pid=%s',
                (uid, pid,)
            )

        return redirect(url_for('project.project', pid=pid))

    dbcursor.execute(
        'SELECT * FROM Projects WHERE pid=%s',
        (pid,)
    )
    thisproject = dbcursor.fetchone()

    # get info for users currently involved in this project
    dbcursor.execute(
        'SELECT firstname, lastname, uid, email'
        ' FROM Users NATURAL JOIN Involvements'
        ' WHERE pid=%s',
        (pid,)
    )
    projectteam = dbcursor.fetchall()

    # get info for users who aren't currently involved in this project
    dbcursor.execute(
        'SELECT firstname, lastname, uid, email'
        ' FROM Users WHERE uid NOT IN'
        ' (SELECT uid FROM Involvements WHERE pid=%s)',
        (pid,)
    )
    otherusers = dbcursor.fetchall()

    return render_template('project/edit.html', thisproject=thisproject, projectteam=projectteam, otherusers=otherusers)

@bp.route('/<int:pid>/announce', methods=('GET', 'POST'))
@login_required(level=3)
def announce(pid):
    dbcursor = get_db().cursor()
    # involvement check: is the user actually assigned to this project?
    res = dbcursor.execute(
        'SELECT * FROM Involvements WHERE pid=(%s) AND uid=(%s)',
        (pid, session['uid'],)
    )
    if not res:
        flash('You aren\'t involved in that project.', category='warning')
        return redirect(url_for('my.dashboard'))

    if request.method == 'POST':
        content = request.form['content']

        dbcursor.execute(
            'INSERT INTO Announcements (pid, author, content)'
            ' VALUES (%s, %s, %s)',
            (pid, session['uid'], content,)
        )

        return redirect(url_for('project.project', pid=pid))

    return render_template('project/announce.html')

# TODO fix this up. right now it's a copy of project.project
@bp.route('/<int:pid>/settings', methods=('GET', 'POST'))
@login_required(level=3)
def settings(pid):
    if request.method == 'POST':
        return 'STUB: editing project settings {}'.format(pid)

    else:
        dbcursor = get_db().cursor()

        num = dbcursor.execute(
            'SELECT * FROM Projects WHERE pid=(%s)',
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
            ' WHERE Involvements.uid = (%s) AND Involvements.pid = (%s)'
            ' ORDER BY Involvements.pid DESC',
            (session['uid'], pid,)
        )

        projectscheck = dbcursor.fetchone()

        # make sure the user has the correct rank to edit this project
        if projectscheck is None or projectscheck['rank'] < 3:
            flash('You don\'t have permission to edit this project.', category='warning')
            return redirect(url_for('project.project', pid=pid))

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
            'SELECT tid, uid, firstname, lastname, title, status, date_submitted, date_due, CAST(date_updated AS char) AS date_updated, tags, description'
            ' FROM Tasks JOIN Users ON Tasks.creator=Users.uid'
            ' WHERE Tasks.pid=(%s)'
            ' ORDER BY Tasks.date_updated DESC',
            (pid,)
        )
        tasks = dbcursor.fetchall()

        # and pass all of this data to the template
        return render_template('project/settings.html', announcements=announcements, tasks=tasks, thisproject=thisproject)

@bp.route('/<int:pid>/leave', methods=('GET', 'POST'))
def leave(pid):
    # as always, start with a cursor
    dbcursor = get_db().cursor()

    # involvement check
    res = dbcursor.execute(
        'SELECT * FROM Involvements WHERE pid=(%s) AND uid=(%s)',
        (pid, session['uid'],)
    )
    if not res:
        flash('You aren\'t involved in that project.', category='warning')
        return redirect(url_for('my.dashboard'))

    if request.method == 'POST':
        name1 = request.form['name1']
        name2 = request.form['name2']

        # first make sure the given titles at least match
        if name1 == name2:
            dbcursor.execute(
                'SELECT title FROM Projects WHERE pid=%s',
                (pid,)
            )
            title = dbcursor.fetchone()['title']
            # now make sure they're the title for this project
            if name1 == title:
                dbcursor.execute(
                    'DELETE FROM Involvements '
                    ' WHERE pid=%s AND uid=%s',
                    (pid, session['uid'],)
                )
                flash('Successfully left '+title+'.', category='success')
                return redirect(url_for('my.dashboard'))
            flash('Failed to leave project.',category='warning')

    return render_template('project/leave.html')
