"""
This module initialises the Flask application for the Xeri project, including
configuration of the database, SocketIO for real-time communication, and
registration of application blueprints for authentication, chat, and moderator
management. It provides the `create_app` factory function to set up the app
with the necessary settings and components.
"""

import os

from flask import Flask
from flask_socketio import SocketIO

from .models import db
from .moderators import setup_moderators

socketio = SocketIO()


def create_app(config_path=None) -> Flask:
    """
    Creates and configures a Flask application instance.

    This function initialises the Flask app, sets up configuration values,
    initialises the database and SocketIO, creates database tables, sets up moderators,
    and registers application blueprints for authentication, chat, and moderators.

    Args:
        config_path (str, optional): Path to the configuration file for setting up moderators.
            Defaults to None.

    Returns:
        Flask: The configured Flask application instance.
    """
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "your-secret-key-fallback")

    # Create an absolute path to the database file
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    db_path = os.path.join(basedir, "instance", "xeri.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", f"sqlite:///{db_path}"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")
    with app.app_context():
        db.create_all()
        # Call setup_moderators after creating all tables
        setup_moderators(app, config_path)
        setup_moderators(app, config_path)

    # Import blueprints after app and socketio are initialised
    from .auth import auth_bp  # pylint: disable=import-outside-toplevel
    from .chat import chat_bp  # pylint: disable=import-outside-toplevel
    from .moderators import moderators_bp  # pylint: disable=import-outside-toplevel

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(moderators_bp)

    return app
