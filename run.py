from dotenv import load_dotenv
from xeri import create_app, socketio

load_dotenv()

app = create_app()

if __name__ == '__main__':
    print("Attempting to launch the application...")
    socketio.run(app, debug=True)
