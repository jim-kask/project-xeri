import logging
import json
from datetime import datetime, timedelta, UTC

from flask import (
    Blueprint,
    current_app,
    session,
    jsonify,
    render_template,
    request,
    url_for,
    redirect,
)
from flask_socketio import emit, join_room, leave_room

from .models import db, User, Message
from . import socketio

_LOGGER = logging.getLogger(__name__)

chat_bp = Blueprint("chat", __name__)

# === Global State ===
online_users = set()
sessions = {}
muted_users = set()
last_activity = {}


@chat_bp.route("/chat")
def chat():
    _LOGGER.debug("Chat route accessed.")
    if "username" not in session:
        _LOGGER.debug("User not in session, redirecting to login.")
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(username=session["username"]).first()
    messages = Message.query.order_by(Message.timestamp.desc()).limit(50).all()
    messages = messages[::-1]  # Reverse for chronological order
    _LOGGER.debug(f"Loaded {len(messages)} messages for chat.")

    return render_template(
        "chat.html",
        username=session["username"],
        messages=messages,
        is_mod=user.mod if user else False,
        muted=list(muted_users),
        data_username=session["username"],
    )


@chat_bp.route("/load_more", methods=["GET"])
def load_more():
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
    _LOGGER.debug(f"Loaded {len(messages)} older messages before ID {before_id}.")

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
def handle_connect():
    username = session.get("username")
    _LOGGER.debug(f"Socket.IO connect event for user: {username}")
    if username:
        online_users.add(username)
        # Try to get the session ID, but handle the case where it might not exist
        # (especially during tests)
        sid = getattr(request, "sid", None)
        if sid:
            sessions[username] = sid  # Store session ID

        last_activity[username] = datetime.now(UTC)
        join_room(username)
        _LOGGER.info(f"{username} joined the chat.")
        emit("message", f"{username} joined the chat", broadcast=True)
        # Make sure to broadcast online users to everyone
        emit_update_users()


@socketio.on("disconnect")
def handle_disconnect():
    username = session.get("username")
    _LOGGER.debug(f"Socket.IO disconnect event for user: {username}")
    if username:
        online_users.discard(username)
        sessions.pop(username, None)
        last_activity.pop(username, None)
        leave_room(username)
        _LOGGER.info(f"{username} left the chat.")
        emit_update_users()


@socketio.on("chat")
def handle_chat(msg):
    """Handle incoming chat messages."""
    username = session.get("username", "Anonymous")
    _LOGGER.debug(f"Chat message received from {username}: {msg}")

    # Always update last activity time, even for muted users
    last_activity[username] = datetime.now(UTC)

    if username in muted_users:
        _LOGGER.warning(f"Muted user {username} tried to send a message.")
        # Send a message back to the sender indicating they're muted
        emit("message", "You are muted and cannot send messages.")
        return

    # Create and save message - don't use a nested app context which can cause issues in tests
    # Instead, use the global db object directly
    message = Message(username=username, text=msg)
    db.session.add(message)
    try:
        db.session.commit()
        _LOGGER.info(f"Message from {username} saved to DB with ID: {message.id}")
    except Exception as e:
        _LOGGER.error(f"Error saving message to DB: {e}")
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
def delete_message(message_id):
    """Handle message deletion by moderators."""
    username = session.get("username")
    _LOGGER.debug(
        f"Delete message request from {username} for message ID: {message_id}"
    )

    # Check user permissions first - no nested app context
    user = User.query.filter_by(username=username).first()
    if not user:
        _LOGGER.warning("[DELETE] No session user found for delete request.")
        return
    if not user.mod:
        _LOGGER.warning(
            f"[DELETE] {username} tried to delete message ID {message_id} but is not a mod."
        )
        return

    # Process message deletion directly
    message = Message.query.get(message_id)
    if message:
        _LOGGER.info(f"[DELETE] {username} deleted message ID {message_id}")
        try:
            db.session.delete(message)
            db.session.commit()

            # Always emit events with include_self=True for tests
            emit("remove_message", message_id, broadcast=True, include_self=True)
            emit("message", f"Message {message_id} deleted successfully")

            # For testing purposes
            emit("delete_confirmed", {"id": message_id})
        except Exception as e:
            _LOGGER.error(f"Error deleting message from DB: {e}")
            db.session.rollback()
            emit("error", "Failed to delete message")
    else:
        _LOGGER.warning(f"[DELETE] Message ID {message_id} not found.")
        emit("message", f"Message {message_id} not found")


@socketio.on("mute_user")
def mute_user(username_to_mute):
    """Handle muting of users by moderators."""
    username = session.get("username")
    _LOGGER.debug(f"Mute user request from {username} for user: {username_to_mute}")

    with current_app.app_context():
        user = User.query.filter_by(username=username).first()
        if user and user.mod:
            muted_users.add(username_to_mute)
            _LOGGER.info(f"User {username_to_mute} has been muted by {username}.")
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
                f"User {username} tried to mute {username_to_mute} but is not a mod."
            )


@socketio.on("unmute_user")
def unmute_user(username_to_unmute):
    """Handle unmuting of users by moderators."""
    username = session.get("username")
    _LOGGER.debug(f"Unmute user request from {username} for user: {username_to_unmute}")

    with current_app.app_context():
        user = User.query.filter_by(username=username).first()
        if user and user.mod:
            muted_users.discard(username_to_unmute)
            _LOGGER.info(f"User {username_to_unmute} has been unmuted by {username}.")
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
                f"User {username} tried to unmute {username_to_unmute} but is not a mod."
            )


@socketio.on("typing")
def handle_typing(data=None):
    """Handle user typing events."""
    username = session.get("username")
    if username:
        last_activity[username] = datetime.now(UTC)
        emit("user_typing", {"username": username}, broadcast=True, include_self=False)


def emit_update_users():
    """Emit updated online users list to all clients."""
    now = datetime.now(UTC)
    user_data = []

    with current_app.app_context():
        for user_name in online_users:
            user_obj = User.query.filter_by(username=user_name).first()
            if not user_obj:
                continue

            afk = (now - last_activity.get(user_name, now)) > timedelta(minutes=5)
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
            room=user_name,
        )
