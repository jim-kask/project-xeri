from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Message
from datetime import datetime
import os
from moderators import moderators

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

socketio = SocketIO(app, cors_allowed_origins="*")
db.init_app(app)

with app.app_context():
    db.create_all()
    for mod_name in moderators:
        mod_user = User.query.filter_by(username=mod_name).first()
        if mod_user and not mod_user.mod:
            mod_user.mod = True
    db.session.commit()

# Track online users and active sessions
online_users = set()
sessions = {}
muted_users = set()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if len(username) < 2 or len(username) > 24:
            return "Username must be between 2 and 24 characters"

        if len(password) < 8:
            return "Password must be at least 8 characters long"

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return "Username already exists"

        hashed_pw = generate_password_hash(password)
        is_mod = username in moderators
        new_user = User(username=username, password=hashed_pw, mod=is_mod)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            if username in sessions:
                return "User is already logged in elsewhere"

            user.mod = username in moderators
            db.session.commit()

            session['username'] = username
            sessions[username] = True
            return redirect(url_for('chat'))
        else:
            return "Invalid username or password"

    return render_template('login.html')

@app.route('/logout')
def logout():
    username = session.get('username')
    if username:
        online_users.discard(username)
        sessions.pop(username, None)
        emit_update_users()
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/chat')
def chat():
    if 'username' not in session:
        return redirect(url_for('login'))
    user = User.query.filter_by(username=session['username']).first()
    messages = Message.query.order_by(Message.timestamp.asc()).limit(50).all()
    return render_template(
        'chat.html',
        username=session['username'],
        messages=messages,
        is_mod=user.mod if user else False,
        muted=list(muted_users),
        data_username=session['username']  # ✅ used for HTML <body data-username=...>
    )

@socketio.on('connect')
def handle_connect():
    username = session.get('username')
    if username:
        online_users.add(username)
        join_room(username)
        emit('message', f"{username} joined the chat", broadcast=True)
        emit_update_users()

@socketio.on('disconnect')
def handle_disconnect():
    username = session.get('username')
    if username:
        online_users.discard(username)
        sessions.pop(username, None)
        leave_room(username)
        emit_update_users()

@socketio.on('chat')
def handle_chat(msg):
    username = session.get('username', 'Anonymous')
    if username in muted_users:
        return
    user = User.query.filter_by(username=username).first()
    message = Message(username=username, text=msg)
    db.session.add(message)
    db.session.commit()
    timestamp = message.timestamp.strftime('%H:%M')
    emit('chat', {
        'id': message.id,
        'username': username,
        'text': msg,
        'timestamp': timestamp,
        'mod': False
    }, broadcast=True)

@socketio.on('delete_message')
def delete_message(message_id):
    username = session.get('username')
    user = User.query.filter_by(username=username).first()
    if user and user.mod:
        message = Message.query.get(message_id)
        if message:
            db.session.delete(message)
            db.session.commit()
            emit('remove_message', message_id, broadcast=True)

@socketio.on('mute_user')
def mute_user(username_to_mute):
    username = session.get('username')
    user = User.query.filter_by(username=username).first()
    if user and user.mod:
        muted_users.add(username_to_mute)
        emit('message', f"{username_to_mute} has been muted by a moderator.", broadcast=True)
        emit_update_users()

@socketio.on('unmute_user')
def unmute_user(username_to_unmute):
    username = session.get('username')
    user = User.query.filter_by(username=username).first()
    if user and user.mod:
        muted_users.discard(username_to_unmute)
        emit('message', f"{username_to_unmute} has been unmuted by a moderator.", broadcast=True)
        emit_update_users()

@socketio.on('typing')
def handle_typing():
    username = session.get('username')
    if username:
        emit('typing', username, broadcast=True, include_self=False)

@socketio.on('stop_typing')
def handle_stop_typing():
    emit('stop_typing', broadcast=True, include_self=False)

def emit_update_users():
    for user in online_users:
        is_mod = user in moderators
        socketio.emit('update_users', (list(online_users), is_mod, list(muted_users)), room=user)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port)
