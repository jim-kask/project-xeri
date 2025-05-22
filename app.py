from flask import Flask
from flask_socketio import SocketIO, emit
import os

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def index():
    return "Ξερή is live!"

@socketio.on('connect')
def handle_connect():
    print("A user connected")
    emit("message", "Welcome to the game!")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=port)
