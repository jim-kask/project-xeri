import pytest
from xeri import create_app, db
from xeri.models import User, Message
from datetime import datetime, UTC

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

def test_user_model(app):
    with app.app_context():
        user = User(username='testuser', password='hashed_password', mod=False)
        db.session.add(user)
        db.session.commit()

        retrieved_user = User.query.filter_by(username='testuser').first()
        assert retrieved_user is not None
        assert retrieved_user.username == 'testuser'
        assert retrieved_user.password == 'hashed_password'
        assert retrieved_user.mod is False

def test_message_model(app):
    with app.app_context():
        message = Message(username='testuser', text='Hello, world!')
        db.session.add(message)
        db.session.commit()

        retrieved_message = Message.query.filter_by(username='testuser').first()
        assert retrieved_message is not None
        assert retrieved_message.username == 'testuser'
        assert retrieved_message.text == 'Hello, world!'
        assert isinstance(retrieved_message.timestamp, datetime)
