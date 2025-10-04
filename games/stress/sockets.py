from flask_socketio import Namespace, emit, join_room
from flask import request
from .engine import StressGame

_games = {}        # room -> StressGame
_user_sids = {}    # room -> { username: sid }

class StressNamespace(Namespace):
    def on_join(self, data):
        user = data.get('username')
        room = data.get('room')
        if not user or not room:
            return

        join_room(room)

        # track this user's socket id per room
        sid = request.sid
        room_map = _user_sids.setdefault(room, {})
        room_map[user] = sid

        game = _games.setdefault(room, StressGame(room))
        allowed = game.add_player(user)
        if not allowed:
            # send only to the current socket
            emit('room_full', {"message": "Room is full"}, room=sid)
            return

        game.deal_if_ready()

        # Send each player their own personalized state
        for u in game.players:
            u_sid = _user_sids.get(room, {}).get(u)
            if u_sid:
                emit('update_state', game.state_for(u), room=u_sid)

    def on_play_card(self, data):
        room = data.get('room')
        user = data.get('username')
        card = data.get('card')
        pile = int(data.get('pile', 0))

        game = _games.get(room)
        if not game:
            return

        if game.play_card(user, card, pile):
            # refresh both players with their own state
            for u in game.players:
                u_sid = _user_sids.get(room, {}).get(u)
                if u_sid:
                    emit('update_state', game.state_for(u), room=u_sid)
        else:
            # optional: tell only the acting user
            emit('invalid_play', {"user": user, "card": card, "pile": pile}, room=request.sid)

    def on_draw_request(self, data):
        room = data.get('room')
        game = _games.get(room)
        if not game:
            return

        if game.draw_new_centers():
            for u in game.players:
                u_sid = _user_sids.get(room, {}).get(u)
                if u_sid:
                    emit('update_state', game.state_for(u), room=u_sid)
        else:
            # notify everyone in the room that no draw is possible
            emit('no_draw', {"message": "No more cards to draw."}, room=room)
