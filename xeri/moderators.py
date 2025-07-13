"""
This module provides moderator-related functionality for the application.

It includes:
- Setup of moderator privileges based on a configuration file (`config.json`).
- A Flask blueprint for moderator/admin routes.
- Functions for cleaning up old messages from the database.

Key components:
- `setup_moderators(app, config_path=None)`: Reads moderator usernames from config and updates their privileges in the database.
- `/admin/cleanup` route: Allows moderators to manually delete messages older than 30 days.
- `delete_old_messages(days=30)`: Deletes messages older than the specified number of days.

Logging is used throughout for monitoring actions and errors.
"""

import logging
import json
from datetime import datetime, timedelta, UTC

from flask import Blueprint, session

from .models import db, User, Message

_LOGGER = logging.getLogger(__name__)

moderators_bp = Blueprint("moderators", __name__)


def setup_moderators(app, config_path=None) -> None:
    """
    Reads moderator usernames from a configuration file and sets their moderator flag in the database.

    This function loads a list of moderator usernames from a JSON configuration file (default: "config.json").
    For each username found, it queries the database for a matching user and sets their `mod` attribute to True.
    If a username is not found in the database, a warning is logged. The function commits all changes to the database
    after processing the list.

    Args:
        app (Flask): The Flask application instance, used to provide an application context for database operations.
        config_path (str, optional): Path to the configuration JSON file. If not provided, defaults to "config.json".
    """
    _LOGGER.debug("Attempting to set up moderators from config.json.")

    config_file = config_path if config_path else "config.json"
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)
            moderators = config.get("moderators", [])
            _LOGGER.debug("Found moderators in config: %s", moderators)

            with app.app_context():
                for username in moderators:
                    user = User.query.filter_by(username=username).first()
                    if user:
                        user.mod = True
                        _LOGGER.info("Granted moderator privileges to %s.", username)
                    else:
                        _LOGGER.warning(
                            "Moderator user %s not found in database.", username
                        )
                db.session.commit()
                _LOGGER.info("Moderator setup complete.")

    except FileNotFoundError:
        _LOGGER.warning("config.json not found. Skipping moderator setup.")
    except json.JSONDecodeError:
        _LOGGER.error("Error decoding config.json. Skipping moderator setup.")


@moderators_bp.route("/admin/cleanup")
def manual_cleanup() -> str | tuple:
    """
    Handles manual cleanup of old messages by moderators.

    This route allows a moderator to manually trigger the deletion of messages older than 30 days.
    Access is restricted to users with moderator privileges.

    Returns:
        Tuple[str, int]: "Access denied" and HTTP 403 if the user is not a moderator.
        str: Confirmation message if cleanup is successful.
    """
    username = session.get("username")
    _LOGGER.debug("Admin cleanup route accessed by user: %s", username)
    user = User.query.filter_by(username=username).first()
    if not user or not user.mod:
        _LOGGER.warning(
            "User %s attempted cleanup without moderator privileges.", username
        )
        return "Access denied", 403
    delete_old_messages(30)
    _LOGGER.info("Manual cleanup initiated by moderator.")
    return "Old messages older than 30 days deleted."


def delete_old_messages(days=30) -> None:
    """
    Deletes messages older than a specified number of days from the database.

    Args:
        days (int, optional): The age threshold in days for messages to be deleted. Defaults to 30.
    """
    _LOGGER.debug("Deleting messages older than %d days.", days)
    threshold = datetime.now(UTC) - timedelta(days=days)
    deleted = Message.query.filter(Message.timestamp < threshold).delete()
    db.session.commit()
    _LOGGER.info("[CLEANUP] Deleted %d messages older than %d days.", deleted, days)
