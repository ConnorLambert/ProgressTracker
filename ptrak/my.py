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
        'SELECT mid, source, firstname, lastname, email, content, date_sent'
        ' FROM Messages JOIN Users ON Messages.source = Users.uid '
        ' WHERE Messages.destination = (%s)'
        ' ORDER BY date_sent DESC',
        (session['uid'],)
    )
    messages = dbcursor.fetchall()

    # get a list of users for addressing outgoing messages
    dbcursor.execute(
        'SELECT uid, firstname, lastname, email FROM Users ORDER BY lastname, firstname ASC'
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
    # QUESTION what exactly do we want to show on the dashboard?
    # TODO finish this
    return "Incomplete!"
    
