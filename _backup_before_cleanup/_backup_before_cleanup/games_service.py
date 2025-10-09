# games_service.py
from flask import Blueprint, jsonify, request
from flask_socketio import SocketIO, join_room, emit
from collections import deque
from flask import request as flask_request  # avoid name clash
import random, string

bp = Blueprint('games_api', __name__, url_prefix='/api')

# --- demo games metadata (can add more later)
GAMES_META = {
    'xeri': {'id': 'xeri', 'name': 'Ξερή', 'icon': '🂡'},
}

# --- in-memory state
TABLES = {}          # { gameId: { tableId: table_dict } }
SID_TO_PLAYER = {}   # { sid: (gameId, tableId, playerId) }

def _id(n=8):
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(n))

# --- REST: games & tables
@bp.get('/games')
def list_games():
    return jsonify(list(GAMES_META.values()))

@bp.get('/games/<game_id>')
def game_info(game_id):
    return jsonify(GAMES_META[game_id])

@bp.get('/games/<game_id>/tables')
def list_tables(game_id):
    out = []
    for t in TABLES.get(game_id, {}).values():
        out.append({'id': t['id'], 'name': t['name'], 'seats': t['seats'], 'players': len(t['players'])})
    return jsonify(out)

@bp.post('/games/<game_id>/tables')
def create_table(game_id):
    data = request.get_json(silent=True) or {}
    name = data.get('name') or f"Table {len(TABLES.get(game_id, {})) + 1}"
    t = {
        'id': _id(), 'name': name, 'seats': 4, 'players': [],
        'started': False, 'turn_idx': 0, 'table': [], 'deck': deque()
    }
    TABLES.setdefault(game_id, {})[t['id']] = t
    return jsonify({'ok': True, 'id': t['id']})

# --- simple deck & rules (placeholder)
SUITS = ['S', 'H', 'D', 'C']
RANKS = list(range(2, 15))

def new_deck():
    deck = [{'r': r, 's': s} for s in SUITS for r in RANKS]
    random.shuffle(deck)
    return deque(deck)

# --- Socket.IO namespace
NS = '/games'
socketio_ref: SocketIO | None = None

def room_key(game_id, table_id): return f"g:{game_id}:t:{table_id}"

def init_socketio(socketio: SocketIO, app):
    """Call this once from app.py: init_games(socketio, app)"""
    global socketio_ref
    socketio_ref = socketio
    app.register_blueprint(bp)

    @socketio.on('join_table', namespace=NS)
    def join_table(data):
        game_id = data.get('gameId'); table_id = data.get('tableId'); name = data.get('name')
        t = TABLES.get(game_id, {}).get(table_id)
        if not t: return
        if not any(p['name'] == name for p in t['players']):
            if len(t['players']) >= t['seats']:
                emit('table_state', {'error': 'Table full'})
                return
            p = {'id': _id(), 'name': name, 'sid': flask_request.sid, 'hand': [], 'ready': False, 'score': 0}
            t['players'].append(p)
            SID_TO_PLAYER[flask_request.sid] = (game_id, table_id, p['id'])
        join_room(room_key(game_id, table_id))
        push_state(game_id, table_id)

    @socketio.on('ready', namespace=NS)
    def ready(_):
        game_id, table_id, pid = who()
        if not pid: return
        t = TABLES[game_id][table_id]
        for pl in t['players']:
            if pl['id'] == pid: pl['ready'] = True
        push_state(game_id, table_id)

    @socketio.on('start', namespace=NS)
    def start(_):
        game_id, table_id, _pid = who()
        if not game_id: return
        t = TABLES[game_id][table_id]
        if len(t['players']) < 2: return
        if not all(pl.get('ready') for pl in t['players']): return
        t['started'] = True; t['turn_idx'] = 0
        t['deck'] = new_deck()
        t['table'] = [t['deck'].popleft() for _ in range(4)]
        for pl in t['players']:
            pl['hand'] = [t['deck'].popleft() for _ in range(6)]
        push_state(game_id, table_id)

    @socketio.on('action', namespace=NS)
    def action(data):
        game_id, table_id, pid = who()
        if not game_id: return
        t = TABLES[game_id][table_id]
        cur = t['players'][t['turn_idx']]
        idx = int(data.get('index', -1))
        if cur['id'] != pid or not t['started']: return
        if idx < 0 or idx >= len(cur['hand']): return
        card = cur['hand'].pop(idx)
        if t['table'] and card['r'] == t['table'][-1]['r']:
            cur['score'] += len(t['table']) + 1
            t['table'] = []
        else:
            t['table'].append(card)
        if all(len(p['hand']) == 0 for p in t['players']):
            if len(t['deck']) >= 6 * len(t['players']):
                for pl in t['players']:
                    pl['hand'] = [t['deck'].popleft() for _ in range(6)]
            else:
                t['started'] = False
                for pl in t['players']: pl['ready'] = False
        if t['started']:
            t['turn_idx'] = (t['turn_idx'] + 1) % len(t['players'])
        push_state(game_id, table_id)

    @socketio.on('disconnect', namespace=NS)
    def disc():
        info = SID_TO_PLAYER.pop(flask_request.sid, None)
        if not info: return
        game_id, table_id, pid = info
        t = TABLES.get(game_id, {}).get(table_id)
        if not t: return
        t['players'] = [pl for pl in t['players'] if pl['id'] != pid]
        push_state(game_id, table_id)

def who():
    info = SID_TO_PLAYER.get(flask_request.sid)
    return info or (None, None, None)

def view_for(t, viewer_sid):
    out_players = []
    for pl in t['players']:
        hand = pl['hand'] if pl['sid'] == viewer_sid else ([{'r': '?', 's': '?'}] * len(pl['hand']))
        out_players.append({'id': pl['id'], 'name': pl['name'], 'ready': pl.get('ready', False), 'hand': hand})
    return {
        'table': {'id': t['id'], 'name': t['name']},
        'players': out_players,
        'table': t['table'],
        'started': t['started'],
        'turn': t['players'][t['turn_idx']]['id'] if t['players'] else None
    }

def push_state(game_id, table_id):
    t = TABLES.get(game_id, {}).get(table_id)
    if not t: return
    for pl in t['players']:
        socketio_ref.emit('table_state', view_for(t, pl['sid']), room=pl['sid'], namespace=NS)
