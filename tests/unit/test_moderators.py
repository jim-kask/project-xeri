import pytest
import os
import json
from xeri import create_app, db
from xeri.models import User, Message
from flask import url_for
from werkzeug.security import generate_password_hash
from unittest import mock

@pytest.fixture
def app(tmpdir):
    # Create a dummy config.json for the app factory
    config_content = {"moderators": []}
    config_path_for_app = tmpdir.join("app_config.json")
    config_path_for_app.write(json.dumps(config_content))

    app = create_app(config_path=str(config_path_for_app))
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

def test_setup_moderators_from_config(app, tmpdir):
    # Create a dummy config.json for testing in tmpdir
    config_content = {"moderators": ["moduser1", "moduser2"]}
    config_file_path = tmpdir.join("config.json")
    config_file_path.write(json.dumps(config_content))

    # Temporarily change the current working directory to tmpdir
    original_cwd = os.getcwd()
    os.chdir(str(tmpdir))

    try:
        with app.app_context():
            # Create users that will be mods
            user1 = User(username='moduser1', password=generate_password_hash('password'))
            user2 = User(username='moduser2', password=generate_password_hash('password'))
            db.session.add_all([user1, user2])
            db.session.commit()

            # Re-run setup_moderators (it's called during app creation, but we can call it again for testing)
            from xeri.moderators import setup_moderators
            setup_moderators(app, str(config_file_path))

            mod1 = User.query.filter_by(username='moduser1').first()
            mod2 = User.query.filter_by(username='moduser2').first()
            assert mod1.mod is True
            assert mod2.mod is True
    finally:
        # Change back to the original working directory
        os.chdir(original_cwd)

def test_admin_cleanup_requires_mod(client):
    register_user(client, 'regularuser', 'password123')
    login_user(client, 'regularuser', 'password123')
    with client.application.test_request_context():
        rv = client.get(url_for('moderators.manual_cleanup'))
    assert b"Access denied" in rv.data
    assert rv.status_code == 403

def test_admin_cleanup_as_mod(client, app):
    with app.app_context():
        mod_user = User(username='moduser', password=generate_password_hash('password'), mod=True)
        db.session.add(mod_user)
        db.session.commit()

    with client.session_transaction() as sess:
        sess['username'] = 'moduser'

    with client.application.test_request_context():
        rv = client.get(url_for('moderators.manual_cleanup'))
    assert b"Old messages older than 30 days deleted." in rv.data
    assert rv.status_code == 200
