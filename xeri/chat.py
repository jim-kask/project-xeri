import logging
import json
from datetime import datetime, timedelta, UTC

from flask import Blueprint, session, jsonify, render_template, request, url_for, redirect
from flask_socketio import emit, join_room, leave_room

from .models import db, User, Message
from . import socketio

logger = logging.getLogger(__name__)

chat_bp = Blueprint('chat', __name__)

# === Global State ===
online_users = set()
sessions = {}
muted_users = set()
last_activity = {}

@chat_bp.route('/chat')
def chat():
    logger.debug("Chat route accessed.")
    if 'username' not in session:
        logger.debug("User not in session, redirecting to login.")
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(username=session['username']).first()
    messages = Message.query.order_by(Message.timestamp.desc()).limit(50).all()[::-1]
    logger.debug(f"Loaded {len(messages)} messages for chat.")

    return render_template(
        'chat.html',
        username=session['username'],
        messages=messages,
        is_mod=user.mod if user else False,
        muted=list(muted_users),
        data_username=session['username'],
    )

@chat_bp.route('/load_more', methods=['GET'])
def load_more():
    logger.debug("Load more messages route accessed.")
    before_id = request.args.get('before_id', type=int)
    if not before_id:
        logger.debug("No before_id provided for loading more messages.")
        return jsonify([])

    messages = (
        Message.query.filter(Message.id < before_id)
        .order_by(Message.timestamp.desc())
        .limit(50)
        .all()
    )

    messages = list(reversed(messages))  # Oldest to newest
    logger.debug(f"Loaded {len(messages)} older messages before ID {before_id}.")

    return jsonify(
        [
            {
                'id': msg.id,
                'username': msg.username,
                'text': msg.text,
                'timestamp': msg.timestamp.strftime('%H:%M'),
            }
            for msg in messages
        ]
    )

# === Socket.IO Events ===

@socketio.on('connect')
def handle_connect():
    username = session.get('username')
    logger.debug(f"Socket.IO connect event for user: {username}")
    if username:
        online_users.add(username)
        sessions[username] = request.sid # Store session ID
        last_activity[username] = datetime.now(UTC)
        join_room(username)
        logger.info(f"{username} joined the chat.")
        emit('message', f"{username} joined the chat", broadcast=True)
        emit_update_users()

@socketio.on('disconnect')
def handle_disconnect():
    username = session.get('username')
    logger.debug(f"Socket.IO disconnect event for user: {username}")
    if username:
        online_users.discard(username)
        sessions.pop(username, None)
        last_activity.pop(username, None)
        leave_room(username)
        logger.info(f"{username} left the chat.")
        emit_update_users()

@socketio.on('chat')
def handle_chat(msg):
    username = session.get('username', 'Anonymous')
    logger.debug(f"Chat message received from {username}: {msg}")
    if username in muted_users:
        logger.warning(f"Muted user {username} tried to send a message.")
        return
    last_activity[username] = datetime.now(UTC)
    message = Message(username=username, text=msg)
    db.session.add(message)
    db.session.commit()
    timestamp = message.timestamp.strftime('%H:%M')
    user = User.query.filter_by(username=username).first()
    logger.info(f"Message from {username} saved to DB.")

    emit(
        'chat',
        {
            'id': message.id,
            'username': username,
            'text': msg,
            'timestamp': timestamp,
            'full_timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'mod': user.mod if user else False,
        },
        broadcast=True,
    )

@socketio.on('delete_message')
def delete_message(message_id):
    username = session.get('username')
    logger.debug(f"Delete message request from {username} for message ID: {message_id}")
    user = User.query.filter_by(username=username).first()
    if not user:
        logger.warning("[DELETE] No session user found for delete request.")
        return
    if not user.mod:
        logger.warning(f"[DELETE] {username} tried to delete message ID {message_id} but is not a mod.")
        return

    message = Message.query.get(message_id)
    if message:
        logger.info(f"[DELETE] {username} deleted message ID {message_id}")
        db.session.delete(message)
        db.session.commit()
        emit('remove_message', message_id, broadcast=True)
    else:
        logger.warning(f"[DELETE] Message ID {message_id} not found for deletion.")

@socketio.on('mute_user')
def mute_user(username_to_mute):
    username = session.get('username')
    logger.debug(f"Mute user request from {username} for user: {username_to_mute}")
    user = User.query.filter_by(username=username).first()
    if user and user.mod:
        muted_users.add(username_to_mute)
        logger.info(f"User {username_to_mute} has been muted by {username}.")
        emit(
            'message',
            f"{username_to_mute} has been muted by a moderator.",
            broadcast=True,
        )
        emit_update_users()
    else:
        logger.warning(f"User {username} tried to mute {username_to_mute} but is not a mod.")

@socketio.on('unmute_user')
def unmute_user(username_to_unmute):
    username = session.get('username')
    logger.debug(f"Unmute user request from {username} for user: {username_to_unmute}")
    user = User.query.filter_by(username=username).first()
    if user and user.mod:
        muted_users.discard(username_to_unmute)
        logger.info(f"User {username_to_unmute} has been unmuted by {username}.")
        emit(
            'message',
            f"{username_to_unmute} has been unmuted by a moderator.",
            broadcast=True,
        )
        emit_update_users()
    else:
        logger.warning(f"User {username} tried to unmute {username_to_unmute} but is not a mod.")

@socketio.on('typing')
def handle_typing():
    username = session.get('username')
    if username:
        last_activity[username] = datetime.now(UTC)
        logger.debug(f"User {username} is typing.")
        emit('typing', username, broadcast=True, include_self=False)

@socketio.on('stop_typing')
def handle_stop_typing():
    username = session.get('username')
    if username:
        logger.debug(f"User {username} stopped typing.")
        emit('stop_typing', username, broadcast=True, include_self=False)

# === Utility ===

def emit_update_users():
    logger.debug("Emitting user list update.")
    now = datetime.now(UTC)
    user_data = []
    for user_name in online_users:
        user_obj = User.query.filter_by(username=user_name).first()
        if user_obj:
            afk = (now - last_activity.get(user_name, now)) > timedelta(minutes=5)
            user_data.append({'name': user_name, 'afk': afk, 'mod': user_obj.mod})

    for user_name in online_users:
        user_obj = User.query.filter_by(username=user_name).first()
        if user_obj:
            socketio.emit(
                'update_users',
                (user_data, user_obj.mod, list(muted_users)),
                room=user_name,
            )
    logger.debug("User list update emitted.")
