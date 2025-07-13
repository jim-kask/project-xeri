import pytest
from xeri import create_app, db
from xeri.models import User, Message
from flask import url_for
from werkzeug.security import generate_password_hash

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

def register_and_login_user(client, username, password):
    with client.application.test_request_context():
        client.post(
            url_for('auth.register'),
            data={'username': username, 'password': password},
            follow_redirects=True
        )
    with client.application.test_request_context():
        client.post(
            url_for('auth.login'),
            data={'username': username, 'password': password},
            follow_redirects=True
        )

def test_chat_page_requires_login(client):
    with client.application.test_request_context():
        rv = client.get(url_for('chat.chat'), follow_redirects=True)
    assert b"Login" in rv.data

def test_chat_page_logged_in(client):
    register_and_login_user(client, 'testuser', 'password123')
    with client.application.test_request_context():
        rv = client.get(url_for('chat.chat'))
    assert rv.status_code == 200
    assert b"Chatroom" in rv.data

def test_load_more_messages(client, app):
    with app.app_context():
        user = User(username='testuser', password=generate_password_hash('password'))
        db.session.add(user)
        db.session.commit()

        for i in range(5):
            message = Message(username='testuser', text=f'Message {i}')
            db.session.add(message)
        db.session.commit()

    with client.application.test_request_context():
        rv = client.get(url_for('chat.load_more', before_id=100))
    assert rv.status_code == 200
    json_data = rv.get_json()
    assert len(json_data) == 5
    assert json_data[0]['text'] == 'Message 0'
