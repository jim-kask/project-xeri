"""
Helper functions for Socket.IO testing
"""
from flask_socketio import emit
import functools
import logging

_LOGGER = logging.getLogger(__name__)


def patch_socketio_test_client(app, socket_client):
    """
    Patch a socket_client instance with custom event handlers for testing.
    This function adds a middleware layer that records events for testing.
    """
    _LOGGER.debug("Patching Socket.IO test client")
    
    original_emit = emit
    received_events = []
    
    def patched_emit(event, *args, **kwargs):
        """Custom emit that also records events for testing"""
        _LOGGER.debug(f"Recording emitted event: {event}")
        received_events.append({"name": event, "args": args, "kwargs": kwargs})
        return original_emit(event, *args, **kwargs)
    
    # Save original functions
    original_get_received = socket_client.get_received
    
    # Override get_received to return recorded events
    def patched_get_received():
        _LOGGER.debug(f"Getting received events (count: {len(received_events)})")
        events = received_events.copy()
        received_events.clear()
        return events
    
    # Apply patches
    socket_client.get_received = patched_get_received
    
    # Patch the emit function in the chat module
    from xeri.chat import emit as chat_emit
    from xeri import chat
    chat.emit = patched_emit
    
    return socket_client
