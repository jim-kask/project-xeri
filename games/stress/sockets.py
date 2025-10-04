from flask_socketio import Namespace, emit, join_room
from .engine import StressGame

_games = {}  # room -> StressGame

class StressNamespace(Namespace):
    def on_join(self, data):
        user = data.get('username')
        room = data.get('room')
        if not user or not room:
            return
        join_room(room)
        game = _games.setdefault(room, StressGame(room))
        allowed = game.add_player(user)
        if not allowed:
            emit('room_full', {"message": "Room is full"}, to=self.sid)
            return
        game.deal_if_ready()
        for u in game.players:
            emit('update_state', game.state_for(u), room=room)

    def on_play_card(self, data):
        room = data.get('room')
        user = data.get('username')
        card = data.get('card')
        pile = int(data.get('pile', 0))
        game = _games.get(room)
        if not game:
            return
        if game.play_card(user, card, pile):
    for u in game.players:
        emit('update_state', game.state_for(u), room=room)
else:
    emit('invalid_play', {"user": user, "card": card, "pile": pile}, room=self.namespace)


    def on_draw_request(self, data):
        room = data.get('room')
        game = _games.get(room)
        if not game:
            return
        if game.draw_new_centers():
            for u in game.players:
                emit('update_state', game.state_for(u), room=room)
        else:
            emit('no_draw', {"message": "No more cards to draw."}, room=room)
