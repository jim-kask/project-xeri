import logging
from flask import Blueprint, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from .models import db, User

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    logger.debug("Register route accessed.")
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        logger.debug(f"Attempting to register user: {username}")

        if len(username) < 2 or len(username) > 24:
            logger.debug("Invalid username length.")
            return "Username must be between 2 and 24 characters"
        if len(password) < 8:
            logger.debug("Invalid password length.")
            return "Password must be at least 8 characters long"
        if User.query.filter_by(username=username).first():
            logger.debug(f"Username {username} already exists.")
            return "Username already exists"

        hashed_pw = generate_password_hash(password)
        new_user = User(username=username, password=hashed_pw, mod=False)
        db.session.add(new_user)
        db.session.commit()
        logger.info(f"User {username} registered successfully.")
        return redirect(url_for('auth.login'))

    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    logger.debug("Login route accessed.")
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        logger.debug(f"Attempting to log in user: {username}")

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            logger.info(f"User {username} logged in successfully.")
            session['username'] = username
            return redirect(url_for('chat.chat'))
        logger.debug(f"Invalid credentials for user: {username}")
        return "Invalid username or password"

    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    username = session.get('username')
    logger.info(f"User {username} logging out.")
    session.pop('username', None)
    # Need to handle online_users and sessions from chat module
    return redirect(url_for('auth.index'))

@auth_bp.route('/')
def index():
    logger.debug("Index route accessed.")
    return render_template('index.html')
