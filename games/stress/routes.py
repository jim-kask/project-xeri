from flask import Blueprint, render_template, session, redirect, url_for, jsonify, request
import random, string, re

def slugify(v: str) -> str:
    v = re.sub(r'[^a-z0-9]+', '-', (v or '').strip().lower()).strip('-')
    return v or ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))

stress_bp = Blueprint(
    'stress', __name__,
    template_folder='templates',
    static_folder='static'
)

@stress_bp.route('/')
def stress_home():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('games/stress/game_stress.html',
                           username=session['username'], room='')

@stress_bp.route('/<room>')
def stress_room(room):
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('games/stress/game_stress.html',
                           username=session['username'], room=room)

# === NEW: tables page (uses your shared templates/tables.html)
@stress_bp.route('/tables')
def stress_tables():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template(
        'tables.html',
        username=session['username'],
        room='Game_1',   # label shown on the page
        tables=[]        # (empty for now)
    )

# === NEW: create-table API → returns /game/stress/<room> url
@stress_bp.route('/api/create', methods=['POST'])
def api_create():
    if 'username' not in session:
        return jsonify({"error": "Not authenticated"}), 401

    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()

    base = slugify(name) if name else f"stress-{''.join(random.choices(string.ascii_lowercase + string.digits, k=4))}"
    room = base

    return jsonify({
        "room": room,
        "url": url_for('stress.stress_room', room=room)
    })
