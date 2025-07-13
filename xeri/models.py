import logging
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, UTC

logger = logging.getLogger(__name__)

db = SQLAlchemy()

logger.debug("Loading database models...")

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    mod = db.Column(db.Boolean, default=False)


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(UTC))

logger.debug("Database models loaded.")
