from flask_socketio import Namespace, emit, join_room, leave_room
from flask import request
from .engine import StressGame
from .routes import OPEN_ROOMS  # read passwords from routes registry

# room -> state
rooms = {}

def room_state(room_id):
    return rooms.setdefault(room_id, {
        "game": StressGame(room_id),
        "players": {},           # username -> sid
        "sids": {},              # sid -> username
        "ready": set(),          # usernames who pressed ready
        "started": False,
        "password": OPEN_ROOMS.get(room_id, {}).get("password"),
    })

class StressNamespace(Namespace):
    # ----------------- helpers -----------------
    def _broadcast_lobby(self, room_id):
        st = room_state(room_id)
        emit("lobby", {
            "room": room_id,
            "players": list(st["players"].keys()),
            "ready": list(st["ready"]),
            "started": st["started"],
            "locked": bool(st["password"])
        }, room=room_id)

    def _send_state_to_all(self, room_id):
        st = room_state(room_id)
        g = st["game"]
        for user, sid in st["players"].items():
            emit("update_state", g.state_for(user), room=sid)

    def _try_start(self, room_id):
        st = room_state(room_id)
        if st["started"]:
            return
        if len(st["players"]) == 2 and st["ready"] == set(st["players"].keys()):
            # both present AND both ready → start game
            st["started"] = True
            g = st["game"]
            g.start(list(st["players"].keys()))
            emit("start", {"room": room_id}, room=room_id)
            self._send_state_to_all(room_id)

    # ----------------- events -----------------
    def on_join(self, data):
        user = data.get("username")
        room_id = data.get("room")
        supplied_pw = (data.get("password") or "").strip() or None
        if not user or not room_id:
            return

        st = room_state(room_id)
        # password gate
        if st["password"] and st["password"] != supplied_pw:
            emit("join_denied", {"reason": "password_required"})
            return

        # room full?
        if len(st["players"]) >= 2 and user not in st["players"]:
            emit("join_denied", {"reason": "room_full"})
            return

        # join
        join_room(room_id)
        st["players"][user] = request.sid
        st["sids"][request.sid] = user

        # if creator closed the tab earlier, allow rejoin without losing ready
        # otherwise ensure user not pre-marked ready
        st["ready"].discard(user)

        self._broadcast_lobby(room_id)
        if st["started"]:
            self._send_state_to_all(room_id)

    def on_ready(self, data):
        user = data.get("username")
        room_id = data.get("room")
        st = room_state(room_id)
        if user in st["players"]:
            st["ready"].add(user)
            self._broadcast_lobby(room_id)
            self._try_start(room_id)

    def on_cancel_ready(self, data):
        user = data.get("username")
        room_id = data.get("room")
        st = room_state(room_id)
        if st["started"]:
            return
        st["ready"].discard(user)
        self._broadcast_lobby(room_id)

    def on_play_card(self, data):
        room_id = data.get('room')
        user = data.get('username')
        card = data.get('card')
        pile = int(data.get('pile', 0))
        st = room_state(room_id)
        g = st["game"]

        if not st["started"]:
            return
        if g.play_card(user, card, pile):
            self._send_state_to_all(room_id)
        else:
            emit('invalid_play', {"user": user, "card": card, "pile": pile}, room=st["players"].get(user))

    def on_draw_request(self, data):
        room_id = data.get('room')
        st = room_state(room_id)
        g = st["game"]
        if not st["started"]:
            return

        if g.draw_new_centers():
            self._send_state_to_all(room_id)
        else:
            emit('no_draw', {"message": "No more cards to draw."}, room=room_id)

    def on_disconnect(self):
        sid = request.sid
        # remove from whatever room they’re in
        for room_id, st in list(rooms.items()):
            user = st["sids"].pop(sid, None)
            if not user:
                continue
            st["players"].pop(user, None)
            st["ready"].discard(user)
            leave_room(room_id)

            # if game started, mark not started (MVP). You could implement
            # pause/ai/etc later.
            st["started"] = False
            st["game"] = StressGame(room_id)  # reset cleanly
            self._broadcast_lobby(room_id)
            break
