from flask import Blueprint, render_template, session, redirect, url_for, jsonify, request
import random, string, re

def slugify(v: str) -> str:
    v = re.sub(r'[^a-z0-9]+', '-', (v or '').strip().lower()).strip('-')
    return v or ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))

stress_bp = Blueprint(
    "stress", __name__,
    template_folder="templates",
    static_folder="static"
)

# ── Landing: send users to the tables page
@stress_bp.route("/")
def home():
    return redirect(url_for("stress.tables"))

# ── Tables page (uses shared templates/tables.html)
@stress_bp.route("/tables")
def tables():
    if "username" not in session:
        return redirect(url_for("login"))
    return render_template(
        "tables.html",
        username=session["username"],
        room="Stress",     # label shown on the page
        tables=[]          # (placeholder for now)
    )

# ── Room page → render the shared game.html that contains #gx-root
@stress_bp.route("/<room>")
def room(room):
    if "username" not in session:
        return redirect(url_for("login"))
    return render_template("game.html", username=session["username"], room=room)

# ── Create-table API → returns /game/stress/<room>
@stress_bp.route("/api/create", methods=["POST"])
def api_create():
    if "username" not in session:
        return jsonify({"error": "Not authenticated"}), 401

    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    base = slugify(name) if name else f"stress-{''.join(random.choices(string.ascii_lowercase + string.digits, k=4))}"
    room = base

    return jsonify({
        "room": room,
        "url": url_for("stress.room", room=room)
    })
