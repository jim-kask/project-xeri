# Xeri Chat App Tests

This directory contains comprehensive tests for the Xeri Chat application.

## Setup

Before running the tests, ensure you have the project dependencies installed as per the main `README.md`.

To install specific test dependencies (if not already covered by `requirements.txt`):

```bash
python tests/setup_tests.py
```

This script will install `pytest`, `pytest-flask`, `pytest-socket`, `pytest-cov`, and `pytest-mock`.

## Running Tests

To run all tests:

```bash
python -m pytest
```

To run tests with coverage:

```bash
python -m pytest --cov=xeri
```

To generate an HTML coverage report (output in `htmlcov/`):

```bash
python -m pytest --cov=xeri --cov-report=html
```

To run specific test files:

```bash
python -m pytest tests/unit/test_auth.py
python -m pytest tests/integration/test_app_integration.py
```

## Test Structure

The test suite is organized into `unit` and `integration` tests:

*   `tests/unit/`:
    *   `test_auth.py`: Focuses on authentication-related functionalities (registration, login, logout).
    *   `test_chat.py`: Tests core chat functionalities and message loading.
    *   `test_chat_coverage.py`: Contains additional tests to improve code coverage for the `chat` module, including error handling and specific Socket.IO event scenarios.
    *   `test_models.py`: Verifies the SQLAlchemy models (`User` and `Message`) for correct data storage.
    *   `test_moderators.py`: Tests moderator-specific functionalities like `setup_moderators` and `manual_cleanup`.

*   `tests/integration/`:
    *   `test_app_integration.py`: Contains broader integration tests that simulate real user interactions, including Socket.IO connections, chat messages, and moderator actions across different components.

*   `test_app.py`: A comprehensive test file that includes a mix of unit and integration tests, covering various aspects of the application.

*   `conftest.py`: Contains shared pytest fixtures (e.g., `app`, `client`, `socket_client`, `test_user`, `mod_user`) used across multiple test files to set up the testing environment.

*   `socketio_test_helper.py`: Provides utility functions to patch `SocketIOTestClient` for more effective testing of Socket.IO events.

## Adding New Tests

When adding new tests, follow these guidelines:

1.  **Group related tests:** Organize tests logically within appropriate files (unit or integration) and use comments to delineate sections.
2.  **Descriptive names:** Use clear and descriptive function names that start with `test_` (e.g., `test_user_registration_success`).
3.  **Docstrings:** Add docstrings to explain what each test verifies.
4.  **Fixtures:** Utilize existing fixtures from `conftest.py` for setting up common test dependencies (e.g., `app`, `client`, `test_user`).
5.  **Assertions:** Use `assert` statements to verify expected outcomes.

## Socket.IO Testing

Socket.IO tests use the `SocketIOTestClient` class to simulate real-time client-server interactions. These tests verify:

*   Connection/disconnection handling.
*   Chat message transmission and reception.
*   Moderator actions (message deletion, user muting/unmuting).
*   User status updates (typing indicators, online/AFK status).

## Database Testing

Database tests primarily use an in-memory SQLite database to ensure isolation and speed. They verify:

*   User registration and authentication.
*   Message storage and retrieval.
*   Moderator flag handling.
*   Message cleanup functionality.

This setup ensures that tests are fast, reliable, and do not interfere with actual development databases.