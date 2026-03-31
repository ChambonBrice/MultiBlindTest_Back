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
from MultiBlindTest_Back.controllers.tracks_controller import tracks_bp
from MultiBlindTest_Back.controllers.clips_controller import clips_bp
from MultiBlindTest_Back.Flask.auth_utils import token_required
from MultiBlindTest_Back.Library.subscription import SubscriptionService
from MultiBlindTest_Back.controllers.rooms_controller import rooms_bp
from MultiBlindTest_Back.controllers.rounds_controller import rounds_bp
from bdd.MBT import MBT

app = Flask(__name__)
CORS(app)

app.register_blueprint(leaderboard_bp)
app.register_blueprint(tracks_bp)
app.register_blueprint(clips_bp)
app.register_blueprint(rooms_bp)
app.register_blueprint(rounds_bp)

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

def init_database():
    mbt_db = MBT()
    mbt_db.creer_table()

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

    if not data:
        return jsonify({"error": "JSON invalide"}), 400

    required_fields = ["nb_music", "time_left", "lives_remaining", "campaign_id"]
    for field in required_fields:
        if field not in data or data[field] is None:
            return jsonify({"error": f"Champ manquant : {field}"}), 400

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
    db.commit()

    return jsonify(result), 200

@app.route("/profile", methods=["GET"])
@token_required
def get_profile():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT id, uuid, name, nom, email, age
        FROM Users
        WHERE id = ? AND archive = 0
    """, (request.user_id,))

    row = cursor.fetchone()

    if not row:
        return jsonify({"error": "Profil introuvable"}), 404

    return jsonify({
        "id": row["id"],
        "uuid": row["uuid"],
        "name": row["name"],
        "nom": row["nom"],
        "email": row["email"],
        "age": row["age"]
    }), 200

@app.route("/profile", methods=["PATCH"])
@token_required
def update_profile():
    data = request.get_json()

    if not data:
        return jsonify({"error": "JSON invalide"}), 400

    db = get_db()
    cursor = db.cursor()

    allowed_fields = {
        "name": "name",
        "nom": "nom",
        "email": "email",
        "age": "age"
    }

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
        cursor.execute(
            f"UPDATE Users SET {', '.join(updates)} WHERE id = ? AND archive = 0",
            values
        )
        db.commit()

        return jsonify({"message": "Profil mis à jour avec succès"}), 200

    except sqlite3.IntegrityError:
        return jsonify({"error": "Nom ou email déjà utilisé"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/settings", methods=["GET"])
@token_required
def get_settings():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT MainVolume, VolumeMusic, VolumeSFX, Language
        FROM Settings
        WHERE UserID = ?
    """, (request.user_id,))

    row = cursor.fetchone()

    if not row:
        return jsonify({"error": "Settings introuvables"}), 404

    return jsonify({
        "main_volume": row["MainVolume"],
        "volume_music": row["VolumeMusic"],
        "volume_sfx": row["VolumeSFX"],
        "language": row["Language"]
    }), 200

@app.route("/settings", methods=["PATCH"])
@token_required
def update_settings():
    data = request.get_json()

    if not data:
        return jsonify({"error": "JSON invalide"}), 400

    db = get_db()
    cursor = db.cursor()

    allowed_fields = {
        "main_volume": "MainVolume",
        "volume_music": "VolumeMusic",
        "volume_sfx": "VolumeSFX",
        "language": "Language"
    }

    updates = []
    values = []

    for key, db_field in allowed_fields.items():
        if key in data:
            updates.append(f"{db_field} = ?")
            values.append(data[key])

    if not updates:
        return jsonify({"error": "Aucune donnée autorisée à mettre à jour"}), 400

    try:
        values.append(request.user_id)
        cursor.execute(
            f"UPDATE Settings SET {', '.join(updates)} WHERE UserID = ?",
            values
        )
        db.commit()

        return jsonify({"message": "Settings mises à jour avec succès"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/subscription", methods=["GET"])
@token_required
def get_subscription():
    subscription = SubscriptionService.get_user_subscription(request.user_id)

    if not subscription:
        return jsonify({
            "has_subscription": False,
            "plan": "free",
            "status": "none"
        }), 200

    is_active = SubscriptionService.has_active_subscription(request.user_id)

    return jsonify({
        "has_subscription": is_active,
        "plan": subscription["plan"],
        "status": subscription["status"],
        "start_date": subscription["start_date"],
        "end_date": subscription["end_date"],
        "auto_renew": bool(subscription["auto_renew"]),
        "provider": subscription["provider"]
    }), 200

if __name__ == "__main__":
    init_database()
    app.run(host="0.0.0.0", port=5000, debug=True)