import os
import logging
from dotenv import load_dotenv
from xeri import create_app, socketio

# Configure logging
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
