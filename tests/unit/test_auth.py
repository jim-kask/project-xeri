import pytest
from xeri import create_app, db
from xeri.models import User
from flask import url_for

@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SERVER_NAME": "localhost.localdomain:5000",
    })

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def register_user(client, username, password):
    with client.application.test_request_context():
        return client.post(
            url_for('auth.register'),
            data={'username': username, 'password': password},
            follow_redirects=True
        )

def login_user(client, username, password):
    with client.application.test_request_context():
        return client.post(
            url_for('auth.login'),
            data={'username': username, 'password': password},
            follow_redirects=True
        )

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

def test_logout_user(client):
    register_user(client, 'testuser', 'password123')
    login_user(client, 'testuser', 'password123')
    with client.application.test_request_context():
        rv = client.get(url_for('auth.logout'), follow_redirects=True)
    assert b"Welcome" in rv.data
