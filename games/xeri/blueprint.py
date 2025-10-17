from flask import Blueprint, render_template, request

# NOTE: template_folder uses a relative path back to /templates/xeri
xeri_bp = Blueprint("xeri_bp", __name__, template_folder="../../templates/xeri")

@xeri_bp.route("/")
def lobby():
    # Minimal lobby so we have a landing page
    return render_template("xeri/lobby.html")

@xeri_bp.route("/play")
def play_local():
    # For now we only support vs CPU, later we'll add rooms.
    mode = request.args.get("mode", "cpu")  # cpu | room
    return render_template("xeri/play.html", mode=mode)
