"""
The ``user`` blueprint. This blueprint contains authentication
and profile retrieval functions, as well as user creation
functionality.
"""
# for wrapping functions in a decorator
import functools
# a few flask components
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
# functions for generating and checking password hashes
# check_password_hash() is needed because you can hash a password twice
# and get two different results, courtesy of salting
from werkzeug.security import check_password_hash, generate_password_hash
# import our get_db() function
from ptrak.db import get_db

# init the blueprint object
bp = Blueprint('user', __name__, url_prefix='/user')


@bp.before_app_request
def load_logged_in_user():
    """
    Get user data for the currently logged-in user.
    Its decorator makes sure this function gets called
    before each request so that user data is available
    before any view function is called (for example).
    """
    uid = session.get('uid')

    if uid is None:
        g.user = None
    else:
        dbcursor = get_db().cursor()
        dbcursor.execute(
            'SELECT * FROM Users WHERE uid = (%s)', (uid,)
        )
        g.user = dbcursor.fetchone()

def login_required(view=None, level=None):
    """
    We need some way to restrict users to only those pages they
    have the authority to access. It wouldn't make sense for
    unregistered users to be able to create and delete projects,
    or for regular users to be able to add new users.

    This functon is implemented as a *decorator* for ease of use.
    To mark a view function (say, ``adminview()``) as requiring
    admin-level permissions, define it as::

        @login_required(5)
        def adminview():
            # do view-related things
            return(render_template('admin/adminview')) # or whatever

    Then it will take appropriate action if the user fails to
    meet the qualifications.
    """
    if view is None:
        return functools.partial(login_required, level=level)
    @functools.wraps(view)
    def wrapped_view(*args, **kwargs):
        # first, send non-logged-in users to the login page
        if g.user is None:
            return redirect(url_for('user.login'))

        # if the user is logged in, make sure they have
        # the required permission level
        if g.user['level'] < level:
            flash('You don\'t have permission to view that page.')
            # FIXME: since my.dashboard doesn't exist yet, we'll
            #        redirect to a test page
            #return(redirect(url_for('my.dashboard')))
            return(redirect(url_for('testindex')))
        return view(*args, **kwargs)
    return wrapped_view

# actual route is /user/login
@bp.route('/login', methods=('GET', 'POST'))
def login():
    """
    Either display the
    """
    # if attempting to log in with credentials
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        error = None
        dbcursor = get_db().cursor()
        dbcursor.execute(
            'SELECT * FROM Users WHERE email = (%s)', (email,)
        )
        user_result = dbcursor.fetchone()

        if user_result is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user_result['password'], password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['uid'] = user_result['uid']
            return redirect(url_for('testindex'))

        flash(error)

    # if called with GET, just show the login page
    return render_template('user/login.html')

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('testindex'))
