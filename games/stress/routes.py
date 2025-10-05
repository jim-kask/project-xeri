from flask import Blueprint, render_template, session, redirect, url_for, jsonify, request
import random, string, re

stress_bp = Blueprint(
    "stress", __name__,
    template_folder="templates",
    static_folder="static"
)

# ---------- simple in-memory room registry (MVP) ----------
# room_id -> {"password": str|None}
OPEN_ROOMS = {}

def _slugify(v: str) -> str:
    v = re.sub(r'[^a-z0-9]+', '-', (v or '').strip().lower()).strip('-')
    return v or ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))

# ---------- pages ----------

@stress_bp.route("/")
def home():
    if "username" not in session:
        return redirect(url_for("login"))
    # use shared tables template; client will fetch /api/list to show rooms
    return render_template(
        "tables.html",
        username=session["username"],
        room="Stress",
        tables=[]   # populated by JS via /game/stress/api/list
    )

@stress_bp.route("/<room>")
def room(room):
    if "username" not in session:
        return redirect(url_for("login"))
    # IMPORTANT: render the actual Stress board template you already have
    return render_template(
        "games/stress/game_stress.html",
        username=session["username"],
        room=room
    )

# ---------- APIs ----------

@stress_bp.route("/api/create", methods=["POST"])
def api_create():
    if "username" not in session:
        return jsonify({"error": "Not authenticated"}), 401

    data = request.get_json(silent=True) or {}
    base = (data.get("name") or "").strip()
    password = (data.get("password") or "").strip() or None

    room_id = _slugify(base) if base else f"stress-{''.join(random.choices(string.ascii_lowercase + string.digits, k=6))}"
    OPEN_ROOMS[room_id] = {"password": password}

    return jsonify({"room": room_id, "url": url_for("stress.room", room=room_id)})

@stress_bp.route("/api/list")
def api_list():
    # return rooms + locked flag
    items = [{"id": rid, "locked": bool(meta.get("password"))} for rid, meta in OPEN_ROOMS.items()]
    # optional: sort newest first
    items.sort(key=lambda x: x["id"], reverse=True)
    return jsonify({"rooms": items})

@stress_bp.route("/api/exists/<room_id>")
def api_exists(room_id):
    meta = OPEN_ROOMS.get(room_id)
    if not meta:
        return jsonify({"exists": False})
    return jsonify({"exists": True, "locked": bool(meta.get("password"))})
