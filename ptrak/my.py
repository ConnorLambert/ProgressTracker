"""
The ``my`` template. Here are the views that a user will have for
working with information pertinent to him/her:
the dashboard, recent messages, involved projects, and so on.

"""

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from ptrak.db import get_db
from ptrak.user import login_required
# init the blueprint
bp = Blueprint('my', __name__, url_prefix='/my')

@bp.route('/messages')
@login_required
def messages():
    """
    This view first gets all messages addressed to the current user,
    along with some basic info about the sender.
    Then it loads some basic info about all users to be used
    to provide options for addressing new outgoing messages.
    It passes both of these lists of dictionaries to the template as arguments
    (``messages`` and ``users``, respectively).
    """
    # load some items from the DB to pass to the template
    dbcursor = get_db().cursor()
    # get all messages addressed to the current user, newest first
    dbcursor.execute(
        'SELECT mid, source, firstname, lastname, email, content, date_sent, subject, unread'
        ' FROM Messages JOIN Users ON Messages.source = Users.uid '
        ' WHERE Messages.destination = (%s)'
        ' ORDER BY date_sent DESC',
        (session['uid'],)
    )
    messages = dbcursor.fetchall()

    # and mark all messages as read, AFTER getting the unread ones
    dbcursor.execute(
        'UPDATE Messages SET unread=0'
        ' WHERE destination=(%s)',
        (session['uid'],)
    )
    # also, clear the notification
    g.unreadmsgs = []

    # get a list of users for addressing outgoing messages
    dbcursor.execute(
        'SELECT uid, firstname, lastname, email FROM Users WHERE uid <> %s'
        ' ORDER BY lastname, firstname ASC', (g.user['uid'],)
    )
    users = dbcursor.fetchall()

    return render_template('my/messages.html', messages=messages, users=users)

@bp.route('/dashboard')
@login_required
def dashboard():
    """
    Most of a user's time will be spent on this route.
    That said, the view itself is pretty simple -
    it just gets a few values out of the database
    and renders the dashboard template.
    """
    # get a db connection
    dbcursor = get_db().cursor()

    error = None
    dbcursor = get_db().cursor()

    dbcursor.execute(
    #Will need to be changed to search by uid once db schema is updated
    #Currently just grabs projects with owner as 1
        'SELECT * FROM Involvements JOIN Projects ON Involvements.pid = Projects.pid '
        'WHERE uid = (%s) ',
        (session['uid'],)
    )
    userProjects = dbcursor.fetchall()

    # every user is expected to belong to at least one project
    # IDEA: maybe redirect to the pit page instead? Or nowhere at all?
    if userProjects is None:
        error = 'User belongs to no projects!'
        flash(error, category='danger')
        return redirect(url_for('testindex'))

    # I don't...I don't really want to think too much about this one.
    # This beastly query gets 5 of the most recent announcements
    # made on projects with which the current user is involved.
    # It took a surprising amount of thought to assemble.
    dbcursor.execute(
        'SELECT content, date_made, title, firstname, lastname, aid '
        ' FROM Projects natural join Announcements JOIN Users ON author=uid'
        ' WHERE pid IN'
        ' (select pid from Users NATURAL JOIN Involvements where uid=(%s))'
        ' ORDER BY date_made DESC LIMIT 5',
        (session['uid'],)
    )
    announcements = dbcursor.fetchall()

    return render_template('my/dashboard.html', userProjects=userProjects, announcements=announcements)
