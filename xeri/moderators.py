import logging
import json
from datetime import datetime, timedelta, UTC

from flask import Blueprint, session

from .models import db, User, Message

_LOGGER = logging.getLogger(__name__)

moderators_bp = Blueprint("moderators", __name__)


def setup_moderators(app, config_path=None):
    """Reads moderator usernames from config.json and sets their `mod` flag in the DB."""
    _LOGGER.debug("Attempting to set up moderators from config.json.")

    config_file = config_path if config_path else "config.json"
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)
            moderators = config.get("moderators", [])
            _LOGGER.debug(f"Found moderators in config: {moderators}")

            with app.app_context():
                for username in moderators:
                    user = User.query.filter_by(username=username).first()
                    if user:
                        user.mod = True
                        _LOGGER.info(f"Granted moderator privileges to {username}.")
                    else:
                        _LOGGER.warning(
                            f"Moderator user {username} not found in database."
                        )
                db.session.commit()
                _LOGGER.info("Moderator setup complete.")

    except FileNotFoundError:
        _LOGGER.warning("config.json not found. Skipping moderator setup.")
    except json.JSONDecodeError:
        _LOGGER.error("Error decoding config.json. Skipping moderator setup.")


@moderators_bp.route("/admin/cleanup")
def manual_cleanup():
    username = session.get("username")
    _LOGGER.debug(f"Admin cleanup route accessed by user: {username}")
    user = User.query.filter_by(username=username).first()
    if not user or not user.mod:
        _LOGGER.warning(
            f"User {username} attempted cleanup without moderator privileges."
        )
        return "Access denied", 403
    delete_old_messages(30)
    _LOGGER.info("Manual cleanup initiated by moderator.")
    return "Old messages older than 30 days deleted."


def delete_old_messages(days=30):
    _LOGGER.debug(f"Deleting messages older than {days} days.")
    threshold = datetime.now(UTC) - timedelta(days=days)
    deleted = Message.query.filter(Message.timestamp < threshold).delete()
    db.session.commit()
    _LOGGER.info(f"[CLEANUP] Deleted {deleted} messages older than {days} days.")
