""" """
import os
from flask import Flask, render_template, session, g
from base64 import b64decode

def create_app(test_config=None):
    """
    Create and configure the application (app factory method).

    :param test_config: configuration for testing
    :return: the Flask application
    """

    app = Flask(__name__, instance_relative_config=True)
    # WARNING: the following MUST be removed before production;
    # it is only here so that all of our local instances are on the
    # same page while testing
    app.config.from_mapping(
        SECRET_KEY=b'dev',
        MYSQL_HOST=b'165.227.119.138',
        MYSQL_USER=b'ptremote',
        MYSQL_PASS=b64decode(b'YmdoUlUkKjU2Nwo=').split(b'\n')[0],
        MYSQL_DB=b'pt',
        CONFIGURED=True
    )
    # --- END WARNING SECTION ---

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in at startup
        app.config.from_mapping(test_config)

    # ensure the instance directory exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass    # NOTE: maybe do something else here?

    # check whether first-time configuration is done already
    if not app.config['CONFIGURED']:
        # if not, only set up the setup blueprint
        pass    # NOTE: here we will eventually import the setup blueprint

    else:
        # since the app is configured, import & register the blueprints
        # add close_db() to the app context teardown
        from . import db
        db.init_app(app)

        # add the user blueprint to the app
        from . import user
        app.register_blueprint(user.bp)


        @app.route('/')
        def testindex():
            try:
                return render_template('index.html', email=session['user'])
            except:
                return render_template('index.html', email='')


        @app.route('/junktest')
        @user.login_required(level=7)
        def junktest():
            return "Hey, you made it!"

    return app
