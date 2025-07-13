# Xeri Chat App Tests

This directory contains comprehensive tests for the Xeri Chat application.

## Setup

Before running the tests, set up your environment:

```
python tests/setup_tests.py
```

This will install all required test dependencies.

## Running Tests

To run all tests:

```
python -m pytest
```

To run tests with coverage:

```
python -m pytest --cov=xeri
```

To run specific test files:

```
python -m pytest tests/test_app.py
```

## Test Structure

- `test_app.py` - Main test file containing tests for:
  - Authentication (register, login, logout)
  - Chat functionality
  - Socket.IO events
  - Moderator actions
  - Message operations
  - Error handling

## Adding New Tests

When adding new tests, follow these guidelines:

1. Group related tests under clearly named sections with comments
2. Use descriptive function names that start with `test_`
3. Add docstrings explaining what each test verifies
4. Use fixtures for setting up common test dependencies

## Socket.IO Testing

Socket.IO tests use the `SocketIOTestClient` class to simulate real-time client-server interactions. These tests verify:

- Connection/disconnection handling
- Chat message transmission
- Moderator actions (message deletion, user muting)
- User status updates (typing indicators, online/AFK status)

## Database Testing

Database tests use an in-memory SQLite database to verify:

- User registration and authentication
- Message storage and retrieval
- Moderator flag handling
- Message cleanup functionality
