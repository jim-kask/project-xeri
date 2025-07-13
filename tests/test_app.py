import sys
sys.path.insert(0, '/home/alexandrosanastasiou/workspace/xeri')
import pytest
from xeri import create_app, db
from xeri.models import User, Message
from werkzeug.security import generate_password_hash

@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    })

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()

def register_user(client, username, password):
    return client.post(
        '/register',
        data={'username': username, 'password': password},
        follow_redirects=True
    )

def login_user(client, username, password):
    return client.post(
        '/login',
        data={'username': username, 'password': password},
        follow_redirects=True
    )

def test_index(client):
    rv = client.get('/')
    assert rv.status_code == 200

def test_register_user(client):
    rv = register_user(client, 'testuser', 'password123')
    assert b"Login" in rv.data
    with client.application.app_context():
        user = User.query.filter_by(username='testuser').first()
        assert user is not None

def test_register_duplicate_username(client):
    register_user(client, 'testuser', 'password123')
    rv = register_user(client, 'testuser', 'anotherpassword')
    assert b"Username already exists" in rv.data

def test_register_invalid_username_length(client):
    rv = register_user(client, 'a', 'password123')
    assert b"Username must be between 2 and 24 characters" in rv.data
    rv = register_user(client, 'a' * 25, 'password123')
    assert b"Username must be between 2 and 24 characters" in rv.data

def test_register_invalid_password_length(client):
    rv = register_user(client, 'testuser', 'short')
    assert b"Password must be at least 8 characters long" in rv.data

def test_login_user(client):
    register_user(client, 'testuser', 'password123')
    rv = login_user(client, 'testuser', 'password123')
    assert b"Chatroom" in rv.data

def test_login_invalid_credentials(client):
    register_user(client, 'testuser', 'password123')
    rv = login_user(client, 'testuser', 'wrongpassword')
    assert b"Invalid username or password" in rv.data

def test_login_non_existent_user(client):
    rv = login_user(client, 'nonexistent', 'password123')
    assert b"Invalid username or password" in rv.data

def test_chat_page_requires_login(client):
    rv = client.get('/chat', follow_redirects=True)
    assert b"Login" in rv.data

def test_logout_user(client):
    register_user(client, 'testuser', 'password123')
    login_user(client, 'testuser', 'password123')
    rv = client.get('/logout', follow_redirects=True)
    assert b"Welcome" in rv.data

# Test message sending (requires Socket.IO client, which is more complex for Flask test client)
# For now, we'll test the database entry after a simulated message send.
def test_message_storage(app):
    with app.app_context():
        user = User(username='sender', password=generate_password_hash('password'))
        db.session.add(user)
        db.session.commit()

        message = Message(username='sender', text='Hello, world!')
        db.session.add(message)
        db.session.commit()

        retrieved_message = Message.query.filter_by(username='sender').first()
        assert retrieved_message is not None
        assert retrieved_message.text == 'Hello, world!'

# Test moderator actions (requires Socket.IO client and user sessions)
# These tests would typically involve a more advanced testing setup with Socket.IO clients.
# For now, we'll focus on the backend logic that Flask handles directly.

def test_admin_cleanup_requires_mod(client):
    register_user(client, 'regularuser', 'password123')
    login_user(client, 'regularuser', 'password123')
    rv = client.get('/admin/cleanup')
    assert b"Access denied" in rv.data
    assert rv.status_code == 403

def test_admin_cleanup_as_mod(client, app):
    with app.app_context():
        mod_user = User(username='moduser', password=generate_password_hash('password'), mod=True)
        db.session.add(mod_user)
        db.session.commit()

    with client.session_transaction() as sess:
        sess['username'] = 'moduser'

    rv = client.get('/admin/cleanup')
    assert b"Old messages older than 30 days deleted." in rv.data
    assert rv.status_code == 200