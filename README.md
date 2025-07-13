# Xeri Chat

Xeri Chat is a real-time, web-based chat application built with Python and Flask. It provides a simple and intuitive interface for users to communicate with each other, along with moderation tools for administrators.

## Features

*   **Real-time Messaging:** Instant message delivery using WebSockets.
*   **User Authentication:** Secure user registration and login system.
*   **Online User List:** See who's currently online with visual indicators for their status.
*   **AFK Status:** Users who are inactive for 5 minutes are marked as AFK (Away From Keyboard) with a red dot indicator.
*   **Typing Indicators:** See when other users are typing a message.
*   **Infinite Scroll:** Load older messages by scrolling to the top of the chat.
*   **Moderation Tools:**
    *   Moderators can delete any message in the chat.
    *   Moderators can mute and unmute users, preventing them from sending messages.
*   **Emoji & Image Support:** Share a variety of emojis and upload images directly in the chat.

## Tech Stack

*   **Backend:**
    *   Python
    *   Flask
    *   Flask-SocketIO (for WebSocket communication)
    *   Flask-SQLAlchemy (for database ORM)
    *   PostgreSQL (production database) / SQLite (local development)
*   **Frontend:**
    *   HTML5 / CSS3
    *   Vanilla JavaScript
    *   Socket.IO Client

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd xeri
    ```

2.  **Create a virtual environment and activate it:**
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```

3.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up the database:**
    *   For **local development**, a SQLite database (`instance/xeri.db`) will be automatically created.
    *   For **production deployment**, ensure you have PostgreSQL installed and running. Create a new database.
    *   Set the `DATABASE_URL` environment variable. For local development, you can create a `.env` file in the root directory and add the following line:
        ```
        DATABASE_URL='postgresql://USER:PASSWORD@HOST:PORT/DATABASE'
        ```
        (Replace with your PostgreSQL connection string)

5.  **Define Moderators:**
    *   Create a `config.json` file in the root directory (e.g., `/path/to/your/project/config.json`).
    *   Add a JSON array of usernames to the file. For example:
        ```json
        {
          "moderators": [
            "user1",
            "user2"
          ]
        }
        ```
    *   The application will automatically grant moderator privileges to these users on startup.

## Development

### Code Formatting and Linting

This project uses `black` for code formatting and `ruff` for linting. To format the code and fix linting issues, run:

```bash
black .
ruff check --fix .
```

### Running Tests

This project uses `pytest` for comprehensive testing. To run the tests:

```bash
# Run the provided test script (recommended)
./run_tests.sh

# Or run pytest directly
python -m pytest

# Run tests with coverage report
python -m pytest --cov=xeri

# Generate HTML coverage report
python -m pytest --cov=xeri --cov-report=html
```

The test suite includes extensive tests for:
-   **Authentication:** User registration, login, and logout (covered in `tests/unit/test_auth.py` and `tests/test_app.py`).
-   **Chat Functionality:** Message sending, loading older messages (infinite scroll), and real-time updates (covered in `tests/unit/test_chat.py` and `tests/test_app.py`).
-   **Socket.IO Real-time Events:** Connection/disconnection handling, chat message transmission, typing indicators, and user status updates (covered in `tests/test_app.py` and `tests/integration/test_app_integration.py`).
-   **Moderator Actions:** Message deletion, user muting/unmuting, and admin cleanup (covered in `tests/unit/test_moderators.py` and `tests/test_app.py`).
-   **Database Operations:** Ensuring proper storage and retrieval of users and messages (`tests/unit/test_models.py`).
-   **Error Handling:** Robustness of the application under various error conditions.
-   **Comprehensive Coverage:** `tests/unit/test_chat_coverage.py` specifically aims to increase test coverage for various chat module scenarios.

See the [tests/README.md](tests/README.md) file for more information about the test suite.

## Running the Application

To start the development server, run:

```bash
python run.py
```

The application will be available at `http://127.0.0.1:5000`.

### Environment Variables

Create a `.env` file in the root directory with the following variables:

```
DATABASE_URL=sqlite:///instance/xeri.db # Or your PostgreSQL connection string
SECRET_KEY=your-super-secret-key
```