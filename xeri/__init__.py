import os
import json
from datetime import datetime, timedelta, UTC

from flask import (
    Flask,
    request,
    session,
    jsonify,
    redirect,
    render_template,
    url_for,
)
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.security import generate_password_hash, check_password_hash

from .models import db, User, Message

socketio = SocketIO()


def create_app():
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
        setup_moderators(app)

    # === Global State ===
    online_users = set()
    sessions = {}
    muted_users = set()
    last_activity = {}

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            username = request.form["username"]
            password = request.form["password"]

            if len(username) < 2 or len(username) > 24:
                return "Username must be between 2 and 24 characters"
            if len(password) < 8:
                return "Password must be at least 8 characters long"
            if User.query.filter_by(username=username).first():
                return "Username already exists"

            hashed_pw = generate_password_hash(password)
            new_user = User(
                username=username,
                password=hashed_pw,
                mod=False
            )
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for("login"))

        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form["username"]
            password = request.form["password"]

            user = User.query.filter_by(username=username).first()
            if user and check_password_hash(user.password, password):
                if username in sessions:
                    return "User is already logged in elsewhere"

                session["username"] = username
                sessions[username] = True
                return redirect(url_for("chat"))
            return "Invalid username or password"

        return render_template("login.html")

    @app.route("/logout")
    def logout():
        username = session.get("username")
        if username:
            online_users.discard(username)
            sessions.pop(username, None)
            last_activity.pop(username, None)
            emit_update_users()
        session.pop("username", None)
        return redirect(url_for("index"))

    @app.route("/chat")
    def chat():
        if "username" not in session:
            return redirect(url_for("login"))

        user = User.query.filter_by(username=session["username"]).first()
        messages = Message.query.order_by(Message.timestamp.desc()).limit(50).all()[::-1]

        return render_template(
            "chat.html",
            username=session["username"],
            messages=messages,
            is_mod=user.mod if user else False,
            muted=list(muted_users),
            data_username=session["username"],
        )

    # === Socket.IO Events ===

    @socketio.on("connect")
    def handle_connect():
        username = session.get("username")
        if username:
            online_users.add(username)
            last_activity[username] = datetime.now(UTC)
            join_room(username)
            emit("message", f"{username} joined the chat", broadcast=True)
            emit_update_users()

    @socketio.on("disconnect")
    def handle_disconnect():
        username = session.get("username")
        if username:
            online_users.discard(username)
            sessions.pop(username, None)
            last_activity.pop(username, None)
            leave_room(username)
            emit_update_users()

    @socketio.on("chat")
    def handle_chat(msg):
        username = session.get("username", "Anonymous")
        if username in muted_users:
            return
        last_activity[username] = datetime.now(UTC)
        message = Message(
            username=username,
            text=msg
        )
        db.session.add(message)
        db.session.commit()
        timestamp = message.timestamp.strftime("%H:%M")
        user = User.query.filter_by(username=username).first()

        emit(
            "chat",
            {
                "id": message.id,
                "username": username,
                "text": msg,
                "timestamp": timestamp,
                "full_timestamp": message.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "mod": user.mod if user else False,
            },
            broadcast=True,
        )

    @socketio.on("delete_message")
    def delete_message(message_id):
        username = session.get("username")
        user = User.query.filter_by(username=username).first()
        if not user:
            print("[DELETE] No session user.")
            return
        if not user.mod:
            print(f"[DELETE] {username} tried to delete but is not a mod.")
            return

        message = Message.query.get(message_id)
        if message:
            print(f"[DELETE] {username} deleted message ID {message_id}")
            db.session.delete(message)
            db.session.commit()
            emit("remove_message", message_id, broadcast=True)
        else:
            print(f"[DELETE] Message ID {message_id} not found.")

    @socketio.on("mute_user")
    def mute_user(username_to_mute):
        username = session.get("username")
        user = User.query.filter_by(username=username).first()
        if user and user.mod:
            muted_users.add(username_to_mute)
            emit(
                "message",
                f"{username_to_mute} has been muted by a moderator.",
                broadcast=True,
            )
            emit_update_users()

    @socketio.on("unmute_user")
    def unmute_user(username_to_unmute):
        username = session.get("username")
        user = User.query.filter_by(username=username).first()
        if user and user.mod:
            muted_users.discard(username_to_unmute)
            emit(
                "message",
                f"{username_to_unmute} has been unmuted by a moderator.",
                broadcast=True,
            )
            emit_update_users()

    @socketio.on("typing")
    def handle_typing():
        username = session.get("username")
        if username:
            last_activity[username] = datetime.now(UTC)
            emit("typing", username, broadcast=True, include_self=False)

    @socketio.on("stop_typing")
    def handle_stop_typing():
        username = session.get("username")
        if username:
            emit("stop_typing", username, broadcast=True, include_self=False)

    # === Utility ===

    def emit_update_users():
        now = datetime.now(UTC)
        user_data = []
        for user_name in online_users:
            user_obj = User.query.filter_by(username=user_name).first()
            if user_obj:
                afk = (now - last_activity.get(user_name, now)) > timedelta(minutes=5)
                user_data.append({"name": user_name, "afk": afk, "mod": user_obj.mod})

        for user_name in online_users:
            user_obj = User.query.filter_by(username=user_name).first()
            if user_obj:
                socketio.emit(
                    "update_users",
                    (user_data, user_obj.mod, list(muted_users)),
                    room=user_name,
                )

    @app.route("/admin/cleanup")
    def manual_cleanup():
        username = session.get("username")
        user = User.query.filter_by(username=username).first()
        if not user or not user.mod:
            return "Access denied", 403
        delete_old_messages(30)
        return "Old messages older than 30 days deleted."

    @app.route("/load_more", methods=["GET"])
    def load_more():
        before_id = request.args.get("before_id", type=int)
        if not before_id:
            return jsonify([])

        messages = (
            Message.query.filter(Message.id < before_id)
            .order_by(Message.timestamp.desc())
            .limit(50)
            .all()
        )

        messages = list(reversed(messages))  # Oldest to newest

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

    def delete_old_messages(days=30):
        threshold = datetime.now(UTC) - timedelta(days=days)
        deleted = Message.query.filter(Message.timestamp < threshold).delete()
        db.session.commit()
        print(f"[CLEANUP] Deleted {deleted} messages older than {days} days.")

    return app

def setup_moderators(app):
    """Reads moderator usernames from config.json and sets their `mod` flag in the DB."""
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
            moderators = config.get("moderators", [])

            with app.app_context():
                for username in moderators:
                    user = User.query.filter_by(username=username).first()
                    if user:
                        user.mod = True
                db.session.commit()
                print("Moderator setup complete.")

    except FileNotFoundError:
        print("config.json not found. Skipping moderator setup.")
    except json.JSONDecodeError:
        print("Error decoding config.json. Skipping moderator setup.")
