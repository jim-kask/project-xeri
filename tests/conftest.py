"""
Conftest.py for pytest configuration for xeri chat app.
This file contains shared fixtures for all tests.
"""
import os
import sys
import pytest

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from xeri import create_app, socketio
