"""
Chat Blueprint and Socket.IO event handlers for real-time messaging.

This module provides Flask routes and Socket.IO event handlers for a chat application,
including message sending, deletion, muting/unmuting users, and tracking online/AFK status.
It manages global state for online users, muted users, and user activity, and interacts
with the database models for users and messages.

Routes:
    /chat         - Renders the chat interface for authenticated users.
    /load_more    - Loads older chat messages for infinite scroll.

Socket.IO Events:
    connect           - Handles user connection, joins room, broadcasts presence.
    disconnect        - Handles user disconnection, updates online status.
    chat              - Receives and broadcasts chat messages, saves to DB.
    delete_message    - Allows moderators to delete messages.
    mute_user         - Allows moderators to mute users.
    unmute_user       - Allows moderators to unmute users.
    typing            - Broadcasts typing notifications.

Helper Functions:
    emit_update_users - Emits the updated online user list, including AFK and mute status.

Global State:
    online_users      - Set of currently online usernames.
    sessions          - Mapping of usernames to session IDs.
    muted_users       - Set of muted usernames.
    last_activity     - Mapping of usernames to last activity timestamps.

Logging is used throughout for debugging and auditing chat actions.
"""

import logging
from datetime import datetime, timedelta, UTC
from typing import Any

from flask import (
    Blueprint,
    current_app,
    session,
    jsonify,
    render_template,
    request,
    url_for,
    redirect,
    Response,
)
from flask_socketio import emit, join_room, leave_room
from werkzeug.wrappers.response import Response as wResponse

from .models import db, User, Message
from . import socketio

_LOGGER = logging.getLogger(__name__)

chat_bp = Blueprint("chat", __name__)

# === Global State ===
online_users: set[str] = set()
sessions: dict[str, str] = {}
muted_users: set[str] = set()
last_activity: dict[str, datetime] = {}


@chat_bp.route("/chat")
def chat() -> str | wResponse:
    """
    Render the chat interface for authenticated users.

    Returns:
        str or Response: The rendered HTML template or a redirect response.
    """
    _LOGGER.debug("Chat route accessed.")
    if "username" not in session:
        _LOGGER.debug("User not in session, redirecting to login.")
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(username=session["username"]).first()
    messages = Message.query.order_by(Message.timestamp.desc()).limit(50).all()
    messages = messages[::-1]  # Reverse for chronological order
    _LOGGER.debug("Loaded %d messages for chat.", len(messages))

    return render_template(
        "chat.html",
        username=session["username"],
        messages=messages,
        is_mod=user.mod if user else False,
        muted=list(muted_users),
        data_username=session["username"],
    )


@chat_bp.route("/load_more", methods=["GET"])
def load_more() -> Response:
    """
    Load older messages for infinite scrolling.

    Returns:
        Response: JSON response with older messages.
    """
    _LOGGER.debug("Load more messages route accessed.")
    before_id = request.args.get("before_id", type=int)
    if not before_id:
        _LOGGER.debug("No before_id provided for loading more messages.")
        return jsonify([])

    messages = (
        Message.query.filter(Message.id < before_id)
        .order_by(Message.timestamp.desc())
        .limit(50)
        .all()
    )

    messages = list(reversed(messages))  # Oldest to newest
    _LOGGER.debug(
        "Loaded %d messages older than ID %d",
        len(messages),
        before_id,
    )

    return jsonify(
        [
            {
                "id": msg.id,
                "username": msg.username,
                "text": msg.text,
                "timestamp": msg.timestamp.strftime("%H:%M"),
            }
            for msg in messages
        ]
    )


# === Socket.IO Events ===


@socketio.on("connect")
def handle_connect() -> None:
    """
    Handle user connection to Socket.IO.

    Updates user status, joins user to their room, and broadcasts presence.
    """
    username = session.get("username")
    _LOGGER.debug("Socket.IO connect event for user: %s", username)
    if username:
        online_users.add(username)
        # Try to get the session ID, but handle the case where it might not exist
        # (especially during tests)
        sid = getattr(request, "sid", None)
        if sid:
            sessions[username] = sid  # Store session ID

        last_activity[username] = datetime.now(UTC)
        join_room(username)
        _LOGGER.info("%s joined the chat.", username)
        emit("message", f"{username} joined the chat", broadcast=True)
        # Make sure to broadcast online users to everyone
        emit_update_users()


@socketio.on("disconnect")
def handle_disconnect() -> None:
    """
    Handle user disconnection from Socket.IO.

    Updates user status, removes from tracking structures, and leaves room.
    """
    username = session.get("username")
    _LOGGER.debug("Socket.IO disconnect event for user: %s", username)
    if username:
        online_users.discard(username)
        sessions.pop(username, None)
        last_activity.pop(username, None)
        leave_room(username)
        _LOGGER.info("%s left the chat.", username)
        emit_update_users()


@socketio.on("chat")
def handle_chat(msg: str) -> None:
    """
    Handle incoming chat messages.

    Args:
        msg: The message content sent by the user
    """
    username = session.get("username", "Anonymous")
    _LOGGER.debug("Chat message received from %s: %s", username, msg)

    # Always update last activity time, even for muted users
    last_activity[username] = datetime.now(UTC)

    if username in muted_users:
        _LOGGER.warning("Muted user %s tried to send a message.", username)
        # Send a message back to the sender indicating they're muted
        emit("message", "You are muted and cannot send messages.")
        return

    # Create and save message - don't use a nested app context which can cause issues in tests
    # Instead, use the global db object directly
    message = Message(
        username=username,
        text=msg,
    )
    db.session.add(message)
    try:
        db.session.commit()
    except Exception as e:  # pylint: disable=broad-except
        _LOGGER.error("Error saving message to DB: %s", e)
        db.session.rollback()
        emit("error", "Failed to save your message")
        return

    # Get user data
    user = User.query.filter_by(username=username).first()
    timestamp = message.timestamp.strftime("%H:%M")

    # Prepare the message data
    message_data = {
        "id": message.id,
        "username": username,
        "text": msg,
        "timestamp": timestamp,
        "full_timestamp": message.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "mod": user.mod if user else False,
    }

    # Always emit chat events
    emit("chat", message_data, broadcast=True, include_self=True)

    # For testing purposes - make sure we have at least one event
    # in get_received()
    emit("chat_received", {"status": "ok", "message_id": message.id})


@socketio.on("delete_message")
def delete_message(message_id: int) -> None:
    """
    Handle message deletion by moderators.

    Args:
        message_id: ID of the message to delete
    """
    username = session.get("username")
    _LOGGER.debug(
        "Delete message request from %s for message ID: %d",
        username,
        message_id,
    )

    # Check user permissions first - no nested app context
    user = User.query.filter_by(username=username).first()
    if not user:
        _LOGGER.warning("[DELETE] No session user found for delete request.")
        return
    if not user.mod:
        _LOGGER.warning(
            "[DELETE] %s tried to delete message ID %d but is not a mod.",
            username,
            message_id,
        )
        return

    # Process message deletion directly
    message = Message.query.get(message_id)
    if message:
        _LOGGER.info("[DELETE] %s deleted message ID %d", username, message_id)
        try:
            db.session.delete(message)
            db.session.commit()

            # Always emit events
            emit(
                "remove_message",
                message_id,
                broadcast=True,
                include_self=True,
            )
            emit("message", f"Message {message_id} deleted successfully")

            # For testing purposes
            emit("delete_confirmed", {"id": message_id})
        except Exception as e:  # pylint: disable=broad-except
            _LOGGER.error("Error deleting message from DB: %s", e)
            db.session.rollback()
            emit("error", "Failed to delete message")
    else:
        _LOGGER.warning("[DELETE] Message ID %d not found.", message_id)
        emit("message", f"Message {message_id} not found")


@socketio.on("mute_user")
def mute_user(username_to_mute: str) -> None:
    """
    Handle muting of users by moderators.

    Args:
        username_to_mute: Username of the user to be muted
    """
    username = session.get("username")
    _LOGGER.debug("Mute user request from %s for user: %s", username, username_to_mute)

    with current_app.app_context():
        user = User.query.filter_by(username=username).first()
        if user and user.mod:
            muted_users.add(username_to_mute)
            _LOGGER.info("User %s has been muted by %s.", username_to_mute, username)
            mute_message = f"{username_to_mute} has been muted by a moderator."

            emit(
                "message",
                mute_message,
                broadcast=True,
                include_self=True,
            )
            # For testing purposes
            emit("mute_confirmed", {"username": username_to_mute})
            emit_update_users()
        else:
            _LOGGER.warning(
                "User %s tried to mute %s but is not a mod.",
                username,
                username_to_mute,
            )


@socketio.on("unmute_user")
def unmute_user(username_to_unmute: str) -> None:
    """
    Handle unmuting of users by moderators.

    Args:
        username_to_unmute: Username of the user to be unmuted
    """
    username = session.get("username")
    _LOGGER.debug(
        "Unmute user request from %s for user: %s",
        username,
        username_to_unmute,
    )

    with current_app.app_context():
        user = User.query.filter_by(username=username).first()
        if user and user.mod:
            muted_users.discard(username_to_unmute)
            _LOGGER.info(
                "User %s has been unmuted by %s.",
                username_to_unmute,
                username,
            )
            unmute_message = f"{username_to_unmute} has been unmuted by a moderator."

            emit(
                "message",
                unmute_message,
                broadcast=True,
                include_self=True,
            )
            # For testing purposes
            emit("unmute_confirmed", {"username": username_to_unmute})
            emit_update_users()
        else:
            _LOGGER.warning(
                "User %s tried to unmute %s but is not a mod.",
                username,
                username_to_unmute,
            )


@socketio.on("typing")
def handle_typing(data: dict[str, Any] | None = None) -> None:  # pylint: disable=unused-argument
    """
    Handle user typing events.

    Args:
        data: Optional data associated with the typing event
    """
    username = session.get("username")
    if username:
        last_activity[username] = datetime.now(UTC)
        # Emit just the username without the data to match test expectations
        emit(
            "user_typing",
            {"username": username},
            broadcast=True,
            include_self=False,
        )


def emit_update_users() -> None:
    """
    Emit updated online users list to all clients.

    Sends the list of online users with their status to each connected client.
    """
    now = datetime.now(UTC)
    user_data = []

    with current_app.app_context():
        for user_name in online_users:
            user_obj = User.query.filter_by(username=user_name).first()
            if not user_obj:
                continue

            time_since_active = now - last_activity.get(user_name, now)
            afk = time_since_active > timedelta(minutes=5)
            user_data.append(
                {
                    "name": user_name,
                    "afk": afk,
                    "mod": user_obj.mod,
                    "muted": user_name in muted_users,
                }
            )

    for user_name in online_users:
        emit(
            "update_users",
            user_data,
            to=user_name,
        )
