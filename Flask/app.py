import os
import sys
import sqlite3
import re
from flask import Flask, request, jsonify, g
from flask_cors import CORS

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
DB_PATH = os.path.join(BASE_DIR, "bdd")
DB_NAME = os.path.join(DB_PATH, "MBT.db")

from MultiBlindTest_Back.Library.Authentification import Authentification
from MultiBlindTest_Back.Library.motdepasse import motdepassesecu
from MultiBlindTest_Back.Library.token import generate_token
from MultiBlindTest_Back.Library.leaderboard import leaderboard_bp
from MultiBlindTest_Back.Library.campagne import Campagne
from MultiBlindTest_Back.Library.level import Level
from MultiBlindTest_Back.Library.victory import Victory
from MultiBlindTest_Back.Library.settings import SettingsService
from MultiBlindTest_Back.controllers.tracks_controller import tracks_bp
from MultiBlindTest_Back.controllers.clips_controller import clips_bp
from MultiBlindTest_Back.Library.level_creator import LevelCreatorService
from MultiBlindTest_Back.Flask.auth_utils import token_required

app = Flask(__name__)
CORS(app)

app.register_blueprint(leaderboard_bp)
app.register_blueprint(tracks_bp)
app.register_blueprint(clips_bp)

def get_db():
    if "db" not in g:
        os.makedirs(os.path.dirname(DB_NAME), exist_ok=True)
        g.db = sqlite3.connect(DB_NAME)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop("db", None)
    if db is not None:
        db.close()

@app.before_request
def attach_db():
    get_db()

def email_valide(email):
    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    return re.match(pattern, email)

@app.route("/")
def home():
    return "API Multi Blind Test opérationnelle 🚀"

@app.route("/register", methods=["POST", "OPTIONS"])
def register():
    if request.method == "OPTIONS":
        return "", 200

    data = request.get_json()

    if not data:
        return jsonify({"error": "JSON invalide"}), 400

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not name or not email or not password:
        return jsonify({"error": "Champs manquants"}), 400

    if not email_valide(email):
        return jsonify({"error": "Email invalide"}), 400

    try:
        motdepassesecu(password)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    success = Authentification.register(name, email, password)

    if not success:
        return jsonify({"error": "Username ou email déjà utilisé"}), 400

    user_id = Authentification.get_user_id(name)

    db = get_db()
    Campagne.init_user_levels(db.cursor(), user_id)
    db.commit()

    return jsonify({"message": "Inscription réussie"}), 201


@app.route("/login", methods=["POST", "OPTIONS"])
def login():
    if request.method == "OPTIONS":
        return "", 200

    data = request.get_json()

    if not data:
        return jsonify({"error": "JSON invalide"}), 400

    name = data.get("name")
    password = data.get("password")

    if not name or not password:
        return jsonify({"error": "Champs manquants"}), 400

    if Authentification.login(name, password):
        user_id = Authentification.get_user_id(name)
        token = generate_token(user_id, name)

        if isinstance(token, bytes):
            token = token.decode("utf-8")

        return jsonify({
            "message": "Connexion réussie",
            "token": token,
            "user_id": user_id,
            "username": name
        }), 200

    return jsonify({"error": "Identifiants invalides"}), 401


@app.route("/logout", methods=["POST"])
@token_required
def logout():
    auth_header = request.headers.get("Authorization")
    token = auth_header.split(" ")[1]

    Authentification.logout(token)
    return jsonify({"message": "Déconnexion réussie"}), 200




@app.route("/settings", methods=["GET"])
@token_required
def get_settings():
    settings = SettingsService.get_settings(request.user_id)
    return jsonify(settings), 200


@app.route("/settings", methods=["PUT", "OPTIONS"])
@token_required
def update_settings():
    if request.method == "OPTIONS":
        return "", 200

    data = request.get_json()

    try:
        settings = SettingsService.update_settings(request.user_id, data)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    return jsonify({
        "message": "Paramètres mis à jour avec succès",
        "settings": settings
    }), 200


@app.route("/levels", methods=["GET"])
@token_required
def get_levels():
    db = get_db()
    levels = Campagne.get_levels(db.cursor(), request.user_id)
    return jsonify(levels)


@app.route("/play/<int:level_id>", methods=["POST"])
@token_required
def play(level_id):
    data = request.get_json()
    guess = data.get("guess")

    db = get_db()
    result = Level.check_guess(db.cursor(), level_id, guess)
    db.commit()

    return jsonify({"result": result})


@app.route("/end_game", methods=["POST"])
@token_required
def end_game():
    data = request.get_json()

    db = get_db()

    result = Victory.calcul_score(
        db,
        user_id=request.user_id,
        nb_music=data.get("nb_music"),
        time_left=data.get("time_left"),
        lives_remaining=data.get("lives_remaining"),
        campaign_id=data.get("campaign_id")
    )

    Victory.add_xp(db, request.user_id, 250)
    return jsonify(result)

@app.route("/levels/create", methods=["POST"])
@token_required
def create_level():
    data = request.get_json()
    title = data.get("title")
    artist_tag = data.get("artist_tag", "")
    theme = data.get("theme", "NEON_PINK")
    if not title:
        return jsonify({"error": "Le titre est requis"}), 400

    level_id = LevelCreatorService.create_level(request.user_id, title, artist_tag, theme)
    return jsonify({"message": "Level créé", "level_id": level_id}), 201

@app.route("/levels/<int:level_id>/tracks", methods=["POST"])
@token_required
def add_track(level_id):
    data = request.get_json()
    media_url = data.get("media_url")
    start_point = data.get("start_point", 0.0)
    duration = data.get("duration", 10.0)
    difficulty = data.get("difficulty", 1)
    if not media_url:
        return jsonify({"error": "URL du média requise"}), 400
    LevelCreatorService.add_track(level_id, media_url, start_point, duration, difficulty)
    return jsonify({"message": "Track ajouté"}), 201

@app.route("/levels/mine", methods=["GET"])
@token_required
def list_my_levels():
    levels = LevelCreatorService.list_user_levels(request.user_id)
    return jsonify(levels)

@app.route("/levels/<int:level_id>", methods=["GET"])
@token_required
def get_level(level_id):
    level = LevelCreatorService.get_level(level_id)
    return jsonify(level)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)