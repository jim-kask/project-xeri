"""
Entry point for launching the Xeri Flask application server with Socket.IO support.

This module performs the following tasks:
- Configures logging for debugging and informational output.
- Loads environment variables from a .env file.
- Creates the Flask application instance using the factory pattern.
- Runs the application server with Socket.IO, listening on all interfaces and a configurable port.

Usage:
    python run.py

Environment Variables:
    PORT: The port number on which the server will listen (default: 5000).
"""

import os
import logging
from dotenv import load_dotenv
from xeri import create_app, socketio

logging.basicConfig(
    level=logging.DEBUG, format="(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
_LOGGER = logging.getLogger(__name__)

load_dotenv(override=True)
_LOGGER.debug("Environment variables loaded.")

app = create_app()
_LOGGER.debug("Flask app created.")

if __name__ == "__main__":
    _LOGGER.info("Attempting to launch the application server...")
    socketio.run(
        app, debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000))
    )
    _LOGGER.info("Application server stopped.")
