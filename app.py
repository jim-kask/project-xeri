from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Message

import os

from models import db, User

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
socketio = SocketIO(app, cors_allowed_origins="*")

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if len(password) < 8:
            return "Password must be at least 8 characters long"

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return "Username already exists"

        hashed_pw = generate_password_hash(password)
        new_user = User(username=username, password=hashed_pw)
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
            session['username'] = username
            return redirect(url_for('chat'))
        else:
            return "Invalid username or password"

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/chat')
def chat():
    if 'username' not in session:
        return redirect(url_for('login'))
    messages = Message.query.order_by(Message.timestamp.asc()).limit(50).all()
    return render_template('chat.html', username=session['username'], messages=messages)

@socketio.on('connect')
def handle_connect():
    print("Client connected")
    emit("message", "Καλώς τους!")

@socketio.on('chat')
def handle_chat(msg):
    username = session.get('username', 'Anonymous')
    full_msg = f"{username}: {msg}"

    # Save to database
    message = Message(username=username, text=msg)
    db.session.add(message)
    db.session.commit()

    emit('chat', full_msg, broadcast=True)


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port)

