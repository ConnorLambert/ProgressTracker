import pymysql
# g is a request-unique global object where we'll store the db connection
from flask import current_app, g
from flask.cli import with_appcontext
import click

def get_db():
    """
    Initialize and return a connection to the database.

    :return: db connection object
    """
    # see if we already have an active connection
    if 'db' not in g:
        # create one if not
        # most of the options are self-explanatory; autocommit makes sure
        # that each DB insert/update takes immediate effect
        g.db = pymysql.connect(
            host=current_app.config['MYSQL_HOST'],
            user=current_app.config['MYSQL_USER'],
            password=current_app.config['MYSQL_PASS'],
            db=current_app.config['MYSQL_DB'],
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True
        )
    return g.db

def close_db(e=None):
    """
    Close the database connection.
    """
    # remove db from g
    db = g.pop('db', None)
    if db is not None:
        # and close the connection
        db.close()

# wrap close_db() so create_app() can call it later
def init_app(app):
    """
    Add ``close_db()`` to the session teardown code.
    """
    app.teardown_appcontext(close_db)
