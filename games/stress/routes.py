from flask import Blueprint, render_template, session, redirect, url_for

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
