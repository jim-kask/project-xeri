# Xeri Chat

Xeri Chat is a real-time, web-based chat application built with Python and Flask. It provides a simple and intuitive interface for users to communicate with each other, along with moderation tools for administrators.

## Features

*   **Real-time Messaging:** Instant message delivery using WebSockets.
*   **User Authentication:** Secure user registration and login system.
*   **Online User List:** See who's currently online.
*   **AFK Status:** Users who are inactive for 5 minutes are marked as AFK (Away From Keyboard).
*   **Typing Indicators:** See when other users are typing a message.
*   **Infinite Scroll:** Load older messages by scrolling to the top of the chat.
*   **Moderation Tools:**
    *   Moderators can delete any message in the chat.
    *   Moderators can mute and unmute users.
*   **Emoji & Image Support:** Share emojis and upload images directly in the chat.

## Tech Stack

*   **Backend:**
    *   Python
    *   Flask
    *   Flask-SocketIO (for WebSocket communication)
    *   Flask-SQLAlchemy (for database ORM)
    *   PostgreSQL (database)
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
    *   Ensure you have PostgreSQL installed and running.
    *   Create a new database.
    *   Set the `DATABASE_URL` environment variable. For local development, you can create a `.env` file and add the following line:
        ```
        DATABASE_URL='postgresql://USER:PASSWORD@HOST:PORT/DATABASE'
        ```

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

This project uses `pytest` for testing. To run the test suite, run:

```bash
pytest
```

## Running the Application

To start the development server, run:

```bash
python run.py
```

The application will be available at `http://127.0.0.1:5000`.

### Environment Variables

Create a `.env` file in the root directory with the following variables:

```
DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DATABASE
SECRET_KEY=your-super-secret-key
```

For local development, you can use a SQLite database by setting `DATABASE_URL` to `sqlite:///instance/xeri.db`.
