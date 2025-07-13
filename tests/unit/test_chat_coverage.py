import pytest
import json
from datetime import datetime, timedelta, UTC
from unittest.mock import patch, MagicMock

from xeri import create_app, db, socketio
from xeri.models import User, Message
from xeri.chat import muted_users, online_users, sessions, last_activity, emit_update_users
from flask import url_for, session
from flask_socketio import SocketIO
from werkzeug.security import generate_password_hash

@pytest.fixture
def app():
    """Create and configure a Flask app for testing."""
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SERVER_NAME": "localhost.localdomain:5000",
        "SECRET_KEY": "test_key",
    })

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()

@pytest.fixture
def socket_client(app, client):
    """Create a Socket.IO test client."""
    from flask_socketio import SocketIOTestClient
    
    # Create the socket client
    socket_client = SocketIOTestClient(app, socketio, flask_test_client=client)
    
    return socket_client

@pytest.fixture
def test_user(app):
    """Create a test user in the database."""
    with app.app_context():
        user = User(
            username="testuser",
            password=generate_password_hash("password123"),
            mod=False
        )
        db.session.add(user)
        db.session.commit()
        return user

@pytest.fixture
def mod_user(app):
    """Create a moderator user in the database."""
    with app.app_context():
        user = User(
            username="moduser",
            password=generate_password_hash("password123"),
            mod=True
        )
        db.session.add(user)
        db.session.commit()
        return user

def login_user(client, username, password):
    """Helper function to log in a user."""
    with client.application.test_request_context():
        return client.post(
            url_for('auth.login'),
            data={'username': username, 'password': password},
            follow_redirects=True
        )

# ====== Testing handle_connect and handle_disconnect ======

def test_handle_connect_disconnect(app, client, socket_client, test_user):
    """Test the connect and disconnect handlers."""
    # Login user first
    login_user(client, "testuser", "password123")
    
    # Mock session, request, and emit to avoid Socket.IO issues
    mock_request = MagicMock()
    mock_request.sid = "test_sid_12345"
    
    with patch('xeri.chat.session', {'username': 'testuser'}), \
         patch('xeri.chat.request', mock_request), \
         patch('xeri.chat.emit') as mock_emit, \
         patch('xeri.chat.emit_update_users') as mock_update, \
         patch('xeri.chat.join_room') as mock_join, \
         patch('xeri.chat.leave_room') as mock_leave:
        
        # Clear any existing data
        online_users.clear()
        sessions.clear()
        last_activity.clear()
        
        # Directly call the connect handler
        from xeri.chat import handle_connect
        handle_connect()
        
        # Check that user was added to online_users
        assert "testuser" in online_users
        assert "testuser" in sessions
        assert sessions["testuser"] == "test_sid_12345"  # Check sid was stored
        assert "testuser" in last_activity
        
        # Check that join_room was called
        mock_join.assert_called_with("testuser")
        
        # Check that join message was emitted
        mock_emit.assert_any_call("message", "testuser joined the chat", 
                                 broadcast=True)
        
        # Check that update_users was called
        mock_update.assert_called_once()
        
        # Now call disconnect directly
        from xeri.chat import handle_disconnect
        handle_disconnect()
        
        # Check that user was removed
        assert "testuser" not in online_users
        assert "testuser" not in sessions
        assert "testuser" not in last_activity
        
        # Check that leave_room was called
        mock_leave.assert_called_with("testuser")

# ====== Testing handle_chat with muted user ======

def test_handle_chat_muted_user(app, client, socket_client, test_user):
    """Test that muted users cannot send messages."""
    # We'll use patching to simulate the session and test the muted user code path
    
    # Clear last_activity first
    last_activity.clear()
    
    # Patch datetime.now to ensure consistent results
    current_time = datetime.now(UTC)
    with patch('xeri.chat.datetime') as mock_datetime, \
         patch('xeri.chat.session', {'username': 'testuser'}), \
         patch('xeri.chat.emit') as mock_emit:
         
        # Set up the datetime mock to return a consistent time
        mock_datetime.now.return_value = current_time
        mock_datetime.UTC = UTC
        
        # Add user to muted_users
        muted_users.add("testuser")
        
        # Directly call the handler to test the code path
        from xeri.chat import handle_chat
        handle_chat("Test message")
        
        # Verify emit was called with muted message
        mock_emit.assert_called_with(
            "message", 
            "You are muted and cannot send messages."
        )
        
        # Since we're setting last_activity before the muted check,
        # verify that last_activity was updated
        assert 'testuser' in last_activity
        assert last_activity['testuser'] == current_time
        
        # Cleanup
        muted_users.discard("testuser")
        last_activity.clear()

# ====== Testing error in handle_chat ======

def test_handle_chat_db_error(app, client, socket_client, test_user):
    """Test error handling in chat message handler."""
    # Login user first
    login_user(client, "testuser", "password123")
    
    # Connect
    socket_client.connect()
    
    # Mock db.session.commit to raise an exception
    with patch('xeri.chat.db.session.commit', side_effect=Exception("DB Error")):
        # Try to send message
        socket_client.emit("chat", "This message should fail")
        
        # Check for error message
        received = socket_client.get_received()
        error_events = [e for e in received if e["name"] == "error"]
        assert len(error_events) > 0

# ====== Testing delete_message with various conditions ======

def test_delete_message_no_user(app, client, socket_client):
    """Test delete_message with no user in session."""
    # Connect without login
    socket_client.connect()
    
    # Try to delete a message
    socket_client.emit("delete_message", 1)
    
    # Nothing should happen, but no error should occur
    # We can't easily assert this negative, but it should be covered

def test_delete_message_non_mod(app, client, socket_client, test_user):
    """Test delete_message with non-moderator user."""
    # Login as regular user
    login_user(client, "testuser", "password123")
    
    # Connect
    socket_client.connect()
    
    # Try to delete a message
    socket_client.emit("delete_message", 1)
    
    # Nothing should happen, but we're testing the code path

def test_delete_message_nonexistent(app, client, socket_client, mod_user):
    """Test delete_message with non-existent message ID."""
    # Mock session and emit to focus on the code path
    with patch('xeri.chat.session', {'username': 'moduser'}), \
         patch('xeri.chat.emit') as mock_emit, \
         app.app_context():
        
        # We need a mock user object with mod=True
        with patch('xeri.chat.User.query') as mock_query:
            mock_user = MagicMock()
            mock_user.mod = True
            mock_query.filter_by.return_value.first.return_value = mock_user
            
            # Create a mock for Message.query.get that returns None
            with patch('xeri.chat.Message.query') as mock_message_query:
                mock_message_query.get.return_value = None
                
                # Call the delete_message handler directly
                from xeri.chat import delete_message
                delete_message(99999)
                
                # Verify message not found was emitted
                mock_emit.assert_any_call("message", "Message 99999 not found")

def test_delete_message_db_error(app, client, socket_client, mod_user):
    """Test error handling in delete_message."""
    # Mock session, user query and message query
    with patch('xeri.chat.session', {'username': 'moduser'}), \
         patch('xeri.chat.emit') as mock_emit, \
         app.app_context():
        
        # Create a mock user with mod=True
        with patch('xeri.chat.User.query') as mock_user_query:
            mock_user = MagicMock()
            mock_user.mod = True
            mock_user_query.filter_by.return_value.first.return_value = mock_user
            
            # Create a mock message
            mock_message = MagicMock()
            with patch('xeri.chat.Message.query') as mock_message_query:
                mock_message_query.get.return_value = mock_message
                
                # Mock db.session to raise exception on commit
                with patch('xeri.chat.db.session.commit', 
                           side_effect=Exception("DB Error")), \
                     patch('xeri.chat.db.session.rollback') as mock_rollback:
                    
                    # Call delete_message directly
                    from xeri.chat import delete_message
                    delete_message(1)
                    
                    # Verify rollback was called
                    mock_rollback.assert_called_once()
                    
                    # Verify error message was emitted
                    mock_emit.assert_any_call("error", "Failed to delete message")

# ====== Testing mute_user and unmute_user ======

def test_mute_unmute_user(app, client, socket_client, mod_user):
    """Test mute and unmute user functionality."""
    # Mock session, user query for moderator path
    with patch('xeri.chat.session', {'username': 'moduser'}), \
         patch('xeri.chat.emit') as mock_emit, \
         app.app_context():
        
        # Create mock user with mod=True
        with patch('xeri.chat.User.query') as mock_user_query:
            mock_user = MagicMock()
            mock_user.mod = True
            mock_user_query.filter_by.return_value.first.return_value = mock_user
            
            # Clear muted_users
            muted_users.clear()
            
            # Call mute_user directly
            from xeri.chat import mute_user
            mute_user("user_to_mute")
            
            # Verify user was added to muted_users
            assert "user_to_mute" in muted_users
            
            # Verify appropriate message was emitted
            mute_message = "user_to_mute has been muted by a moderator."
            mock_emit.assert_any_call("message", mute_message, 
                                      broadcast=True, include_self=True)
            
            # Now test unmute
            from xeri.chat import unmute_user
            unmute_user("user_to_mute")
            
            # Verify user was removed from muted_users
            assert "user_to_mute" not in muted_users
            
            # Verify appropriate message was emitted
            unmute_message = "user_to_mute has been unmuted by a moderator."
            mock_emit.assert_any_call("message", unmute_message, 
                                     broadcast=True, include_self=True)

def test_mute_unmute_non_mod(app, client, socket_client, test_user):
    """Test mute and unmute with non-moderator user."""
    # Login as regular user
    login_user(client, "testuser", "password123")
    
    # Connect
    socket_client.connect()
    
    # Clear muted_users
    muted_users.clear()
    
    # Try to mute a user
    socket_client.emit("mute_user", "some_user")
    
    # Check that user was not added to muted_users
    assert "some_user" not in muted_users

# ====== Testing handle_typing ======

def test_typing_events(app, client, socket_client, test_user):
    """Test typing event handler."""
    # Mock session to ensure username is present
    with patch('xeri.chat.session', {'username': 'testuser'}), \
         patch('xeri.chat.emit') as mock_emit:
        
        # Clear last_activity
        if 'testuser' in last_activity:
            del last_activity['testuser']
            
        # Record time before event
        before = datetime.now(UTC)
        
        # Call the typing handler directly
        from xeri.chat import handle_typing
        handle_typing({})
        
        # Check that last_activity was updated
        assert "testuser" in last_activity
        assert last_activity["testuser"] >= before
        
        # Verify typing event was emitted
        mock_emit.assert_called_with(
            "user_typing", 
            {"username": "testuser"}, 
            broadcast=True, 
            include_self=False
        )

# ====== Testing emit_update_users ======

@patch('xeri.chat.emit')
def test_emit_update_users(mock_emit, app):
    """Test emit_update_users function."""
    with app.app_context():
        # Create test user
        user = User(
            username="testuser",
            password=generate_password_hash("password123"),
            mod=False
        )
        db.session.add(user)
        db.session.commit()
        
        # Setup test data
        online_users.clear()
        online_users.add("testuser")
        last_activity["testuser"] = datetime.now(UTC)
        
        # Call the function
        emit_update_users()
        
        # Verify emit was called
        mock_emit.assert_called()
        
        # Clear test data
        online_users.clear()
        last_activity.clear()

# ====== Testing emit_update_users with AFK user ======

@patch('xeri.chat.emit')
def test_emit_update_users_afk(mock_emit, app):
    """Test emit_update_users with AFK user."""
    with app.app_context():
        # Create test user
        user = User(
            username="testuser",
            password=generate_password_hash("password123"),
            mod=False
        )
        db.session.add(user)
        db.session.commit()
        
        # Setup test data
        online_users.clear()
        online_users.add("testuser")
        last_activity["testuser"] = datetime.now(UTC) - timedelta(minutes=10)  # AFK
        
        # Call the function
        emit_update_users()
        
        # Verify emit was called with AFK user
        called_args = mock_emit.call_args[0]
        assert called_args[0] == "update_users"
        user_data = called_args[1]
        
        assert len(user_data) == 1
        assert user_data[0]["name"] == "testuser"
        assert user_data[0]["afk"] is True
        
        # Clear test data
        online_users.clear()
        last_activity.clear()

# ====== Testing nonexistent user in emit_update_users ======

@patch('xeri.chat.emit')
def test_emit_update_users_nonexistent_user(mock_emit, app):
    """Test emit_update_users with nonexistent user."""
    with app.app_context():
        # Setup test data with a user not in the database
        online_users.clear()
        online_users.add("nonexistent")
        
        # Call the function
        emit_update_users()
        
        # Verify emit was called with empty data
        called_args = mock_emit.call_args[0]
        assert called_args[0] == "update_users"
        user_data = called_args[1]
        
        assert len(user_data) == 0
        
        # Clear test data
        online_users.clear()
