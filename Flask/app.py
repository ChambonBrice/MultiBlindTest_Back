import os
import re
import sys
from dotenv import load_dotenv
load_dotenv()
from flask import Flask, jsonify, request
from flask_cors import CORS

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from MultiBlindTest_Back.Flask.auth_utils import token_required
from MultiBlindTest_Back.Library.Authentification import Authentification
from MultiBlindTest_Back.Library.bdd_client import BDDAPIError, get_db_session
from MultiBlindTest_Back.Library.campagne import Campagne
from MultiBlindTest_Back.Library.leaderboard import leaderboard_bp
from MultiBlindTest_Back.Library.level import Level
from MultiBlindTest_Back.Library.level_creator import LevelCreatorService
from MultiBlindTest_Back.Library.motdepasse import motdepassesecu
from MultiBlindTest_Back.Library.settings import SettingsService
from MultiBlindTest_Back.Library.subscription import SubscriptionService
from MultiBlindTest_Back.Library.token import generate_token
from MultiBlindTest_Back.Library.victory import Victory
from MultiBlindTest_Back.controllers.clips_controller import clips_bp
from MultiBlindTest_Back.controllers.rooms_controller import rooms_bp
from MultiBlindTest_Back.controllers.rounds_controller import rounds_bp
from MultiBlindTest_Back.controllers.tracks_controller import tracks_bp

app = Flask(__name__)
CORS(app)

app.register_blueprint(leaderboard_bp)
app.register_blueprint(tracks_bp)
app.register_blueprint(clips_bp)
app.register_blueprint(rooms_bp)
app.register_blueprint(rounds_bp)

print("BDD_API_URL =", os.getenv("BDD_API_URL"))
print("BDD_SERVICE_TOKEN =", os.getenv("BDD_SERVICE_TOKEN"))
print("JWT_USER_SECRET =", os.getenv("JWT_USER_SECRET"))

def get_db():
    return get_db_session()


def email_valide(email):
    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    return re.match(pattern, email)


@app.route("/")
def home():
    return "API Multi Blind Test opérationnelle 🚀"


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "backend"}), 200


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

    try:
        success = Authentification.register(name, email, password)
        if not success:
            return jsonify({"error": "Username ou email déjà utilisé"}), 400

        user_id = Authentification.get_user_id(name)
        db = get_db()
        Campagne.init_user_levels(db.cursor(), user_id)
        db.commit()
        return jsonify({"message": "Inscription réussie"}), 201
    except BDDAPIError as e:
        return jsonify({"error": str(e)}), 502


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

    try:
        if Authentification.login(name, password):
            user_id = Authentification.get_user_id(name)
            token = generate_token(user_id, name)
            if isinstance(token, bytes):
                token = token.decode("utf-8")
            return jsonify({
                "message": "Connexion réussie",
                "token": token,
                "user_id": user_id,
                "username": name,
            }), 200
    except BDDAPIError as e:
        return jsonify({"error": str(e)}), 502

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
    try:
        settings = SettingsService.get_settings(request.user_id)
        return jsonify(settings), 200
    except BDDAPIError as e:
        return jsonify({"error": str(e)}), 502


@app.route("/settings", methods=["PUT", "PATCH", "OPTIONS"])
@token_required
def update_settings():
    if request.method == "OPTIONS":
        return "", 200

    data = request.get_json()
    try:
        settings = SettingsService.update_settings(request.user_id, data)
        return jsonify({"message": "Paramètres mis à jour avec succès", "settings": settings}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except BDDAPIError as e:
        return jsonify({"error": str(e)}), 502


@app.route("/levels", methods=["GET"])
@token_required
def get_levels():
    try:
        db = get_db()
        levels = Campagne.get_levels(db.cursor(), request.user_id)
        return jsonify(levels)
    except BDDAPIError as e:
        return jsonify({"error": str(e)}), 502


@app.route("/play/<int:level_id>", methods=["POST"])
@token_required
def play(level_id):
    data = request.get_json() or {}
    guess = data.get("guess")
    try:
        db = get_db()
        result = Level.check_guess(db.cursor(), level_id, guess)
        db.commit()
        return jsonify({"result": result})
    except BDDAPIError as e:
        return jsonify({"error": str(e)}), 502


@app.route("/end_game", methods=["POST"])
@token_required
def end_game():
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON invalide"}), 400

    required_fields = ["nb_music", "time_left", "lives_remaining", "campaign_id"]
    for field in required_fields:
        if field not in data or data[field] is None:
            return jsonify({"error": f"Champ manquant : {field}"}), 400

    try:
        db = get_db()
        result = Victory.calcul_score(
            db,
            user_id=request.user_id,
            nb_music=data.get("nb_music"),
            time_left=data.get("time_left"),
            lives_remaining=data.get("lives_remaining"),
            campaign_id=data.get("campaign_id"),
        )
        Victory.add_xp(db, request.user_id, 250)
        db.commit()
        return jsonify(result), 200
    except BDDAPIError as e:
        return jsonify({"error": str(e)}), 502


@app.route("/profile", methods=["GET"])
@token_required
def get_profile():
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            """
            SELECT id, uuid, name, nom, email, age
            FROM Users
            WHERE id = ? AND archive = 0
            """,
            (request.user_id,),
        )
        row = cursor.fetchone()
        if not row:
            return jsonify({"error": "Profil introuvable"}), 404
        return jsonify({
            "id": row["id"],
            "uuid": row["uuid"],
            "name": row["name"],
            "nom": row["nom"],
            "email": row["email"],
            "age": row["age"],
        }), 200
    except BDDAPIError as e:
        return jsonify({"error": str(e)}), 502


@app.route("/profile", methods=["PATCH"])
@token_required
def update_profile():
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON invalide"}), 400

    db = get_db()
    cursor = db.cursor()
    allowed_fields = {"name": "name", "nom": "nom", "email": "email", "age": "age"}
    updates = []
    values = []

    for key, db_field in allowed_fields.items():
        if key in data:
            if key == "email" and not email_valide(data["email"]):
                return jsonify({"error": "Email invalide"}), 400
            updates.append(f"{db_field} = ?")
            values.append(data[key])

    if not updates:
        return jsonify({"error": "Aucune donnée autorisée à mettre à jour"}), 400

    try:
        values.append(request.user_id)
        cursor.execute(f"UPDATE Users SET {', '.join(updates)} WHERE id = ? AND archive = 0", values)
        db.commit()
        return jsonify({"message": "Profil mis à jour avec succès"}), 200
    except BDDAPIError as e:
        msg = str(e).lower()
        if "unique" in msg or "déjà" in msg:
            return jsonify({"error": "Nom ou email déjà utilisé"}), 400
        return jsonify({"error": str(e)}), 502


@app.route("/subscription", methods=["GET"])
@token_required
def get_subscription():
    try:
        subscription = SubscriptionService.get_user_subscription(request.user_id)
        if not subscription:
            return jsonify({"has_subscription": False, "plan": "free", "status": "none"}), 200

        is_active = SubscriptionService.has_active_subscription(request.user_id)
        return jsonify({
            "has_subscription": is_active,
            "plan": subscription["plan"],
            "status": subscription["status"],
            "start_date": subscription["start_date"],
            "end_date": subscription["end_date"],
            "auto_renew": bool(subscription["auto_renew"]),
            "provider": subscription["provider"],
        }), 200
    except BDDAPIError as e:
        return jsonify({"error": str(e)}), 502


@app.route("/levels/create", methods=["POST"])
@token_required
def create_level():
    data = request.get_json() or {}
    title = data.get("title")
    artist_tag = data.get("artist_tag", "")
    theme = data.get("theme", "NEON_PINK")
    if not title:
        return jsonify({"error": "Le titre est requis"}), 400
    try:
        level_id = LevelCreatorService.create_level(request.user_id, title, artist_tag, theme)
        return jsonify({"message": "Level créé", "level_id": level_id}), 201
    except BDDAPIError as e:
        return jsonify({"error": str(e)}), 502


@app.route("/levels/<int:level_id>/tracks", methods=["POST"])
@token_required
def add_track(level_id):
    data = request.get_json() or {}
    media_url = data.get("media_url")
    start_point = data.get("start_point", 0.0)
    duration = data.get("duration", 10.0)
    difficulty = data.get("difficulty", 1)

    if not media_url:
        return jsonify({"error": "URL du média requise"}), 400

    try:
        LevelCreatorService.add_track(level_id, media_url, start_point, duration, difficulty)
        return jsonify({"message": "Track ajouté"}), 201
    except BDDAPIError as e:
        return jsonify({"error": str(e)}), 502


@app.route("/levels/mine", methods=["GET"])
@token_required
def list_my_levels():
    try:
        levels = LevelCreatorService.list_user_levels(request.user_id)
        return jsonify(levels)
    except BDDAPIError as e:
        return jsonify({"error": str(e)}), 502


@app.route("/levels/<int:level_id>", methods=["GET"])
@token_required
def get_user_level(level_id):
    try:
        level = LevelCreatorService.get_level(level_id)
        return jsonify(level)
    except BDDAPIError as e:
        return jsonify({"error": str(e)}), 502


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
