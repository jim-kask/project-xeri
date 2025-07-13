import os
import json
from datetime import datetime, timedelta, UTC

from flask import Flask
from flask_socketio import SocketIO

from .models import db

socketio = SocketIO()


def create_app(config_path=None):
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
        # Import setup_moderators here to avoid circular import with app_context
        from .moderators import setup_moderators

        setup_moderators(app, config_path)

    # Import blueprints after app and socketio are initialised
    from .auth import auth_bp
    from .chat import chat_bp
    from .moderators import moderators_bp

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(moderators_bp)

    return app
