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

def login_required(view=None, level=0):
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
            return(redirect(url_for('my.dashboard')))
        return view(*args, **kwargs)
    return wrapped_view

# actual route is /user/login
@bp.route('/login', methods=('GET', 'POST'))
def login():
    """
    Either display the login page or allow a user to log in.
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
            # empty the session and store the user's uid in it
            session.clear()
            session['uid'] = user_result['uid']
            # update the Users table to show that the user has logged in recently
            dbcursor.execute(
                'UPDATE Users SET lastlogin=CURRENT_TIMESTAMP WHERE uid=(%s)',
                (session['uid'],)
            )
            firstname = user_result['firstname']
            lastname = user_result['lastname']
            if password == firstname[0]+lastname:
                return redirect(url_for('user.resetPwd'))
            return redirect(url_for('testindex'))

        flash(error)

    # if called with GET, just show the login page
    return render_template('user/login.html')

@bp.route('/resetPwd', methods=('GET', 'POST'))
@login_required#(level=0)
def resetPwd():
        if request.method == 'POST':
            password1 = request.form['password1']
            password2 = request.form['password2']

            error = None
            #checks to make sure fields are assigned properly
            if password1 != password2:
                error = 'Your password needs to be the same for both text boxes!'


            #insert new user
            if error is None:
                dbcursor = get_db().cursor()
                dbcursor.execute(
                    'UPDATE Users SET '
                    'password = %s WHERE uid = %s',
                    (generate_password_hash(password1), session['uid'])
                )
                flash('Password successfully reset!')
                return redirect(url_for('my.dashboard'))
            flash(error)
        return render_template('user/resetPwd.html')

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('testindex'))

@bp.route('/new', methods=('GET', 'POST'))
@login_required(level=3)    # this level is open for debate
def new():
    if request.method == 'POST':
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        email = request.form['email']
        level = request.form['level']
        try:
            projects = request.form['projects']
        except:
            projects = None

        error = None
        #checks to make sure fields are assigned properly
        if firstname is None:
            error = 'Missing first name!'
        elif lastname is None:
            error = 'Missing last name!'
        elif email is None:
            error = 'Missing an email!'
        elif level is None:
            error = 'No level assigned!'

        #insert new user
        if error is None:
            dbcursor = get_db().cursor()
            dbcursor.execute(
                'INSERT INTO Users (firstname, lastname, email, password, level, projects) '
                'VALUES (%s, %s, %s, %s, %s, %s)',
                (firstname, lastname, email, generate_password_hash(firstname[0]+lastname), level, projects,)
            )
            #return redirect(url_for('my.dashboard'))
            flash('Successful User Added')
            return redirect(url_for('testindex'))
        flash(error)

    return render_template('user/new.html')
