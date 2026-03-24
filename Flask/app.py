import os
import sys
from flask import Flask, request, jsonify
from flask_cors import CORS
from MultiBlindTest_Back.Library.Authentification import Authentification
from MultiBlindTest_Back.Library.motdepasse import motdepassesecu
from MultiBlindTest_Back.Library.token import generate_token, verify_token
from functools import wraps
from MultiBlindTest_Back.Library.leaderboard import leaderboard_bp
import re
from MultiBlindTest_Back.Library.campagne import Campagne
import sqlite3
from flask import g
from MultiBlindTest_Back.Library.level import Level
from MultiBlindTest_Back.Library.victory import Victory

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
DB_PATH = os.path.join(BASE_DIR, "bdd")
DB_NAME = os.path.join(DB_PATH, "MBT.db")
app = Flask(__name__)
CORS(app)

app.register_blueprint(leaderboard_bp)

@app.route("/")
def home():
    return "API Projet SLAM opérationnelle"

def email_valide(email):
    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    return re.match(pattern, email)

@app.route("/register", methods=['POST', 'OPTIONS'])
def register():
    if request.method == "OPTIONS":
        return "", 200

    data = request.get_json()
    print("Data reçue:", data)

    if not data:
        return jsonify({"error": "JSON invalide"}), 400

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not name or not email or not password:
        return jsonify({"error": "Champs manquants"}), 400

    if not email_valide(email):
        return jsonify({"error": "Email invalide (ex: test@hotmail.fr)"}), 400

    try:
        if not motdepassesecu(password):
          return jsonify({"error": "Mot de passe invalide"}), 400
    except BaseException as ex:
            return jsonify({"error": str(ex)}), 400

    success = Authentification.register(name, email, password)
    print("Utilisateur ajouté:", name)

    if not success:
        return jsonify({"error": "Username ou email déjà utilisé"}), 400

    user_id = Authentification.get_user_id(name)

    db = get_db()
    Campagne.init_user_levels(db.cursor(), user_id)
    db.commit()

    return jsonify({"message": "Inscription réussie"}), 201


@app.route("/login", methods=['POST', 'OPTIONS'])
def login():

    if request.method == "OPTIONS":
        return "", 200

    data = request.get_json()
    print("LOGIN DATE:", data)

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
    else:
        return jsonify({"error": "Identifiants invalides"}), 401

def token_required(f):

    @wraps(f)
    def decorated(*args, **kwargs):

        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return jsonify({"error": "Token manquant"}), 401

        try:
            token = auth_header.split(" ")[1]
        except IndexError:
            return jsonify({"error": "Token invalide"}), 401

        payload = verify_token(token)

        if not payload:
            return jsonify({"error": "Token expiré ou invalide"}), 401

        if Authentification.token_is_blacklisted(token):
            return jsonify({"error": "Token révoqué"}), 401

        request.user_id = payload.get("user_id")

        return f(*args, **kwargs)

    return decorated

@app.route("/profile")
@token_required
def profile():

    return jsonify({
            "message": "Route protégée accessible"
    })

@app.route("/logout", methods=["POST"])
@token_required
def logout():

    auth_header = request.headers.get("Authorization")
    token = auth_header.split(" ")[1]

    Authentification.logout(token)

    return jsonify({"message": "Déconnexion réussie"}), 200

@app.route("/add_points", methods=["POST"])
def add_points():

    data = request.get_json()

    name = data.get("name")
    points = data.get("points")

    Authentification.add_points(name, points)

    return jsonify({"message": "Points ajoutés"})

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

@app.route("/levels", methods=["GET"])
@token_required
def get_levels():
    user_id = request.user_id
    db = get_db()
    levels = Campagne.get_levels(db.cursor(), user_id)
    if not levels:
        return jsonify({"error": "Niveau introuvable"}), 404
    return jsonify(levels)

@app.route("/complete_level/<int:level_id>/", methods=["POST"])
@token_required
def complete_level(level_id):
    user_id = request.user_id
    db = get_db()
    Campagne.complete_level(db.cursor(), user_id, level_id,)
    db.commit()
    return jsonify({"message": "niveau complété"})

@app.route("/init_levels", methods=["POST"])
@token_required
def init_levels():
    user_id = request.user_id
    db = get_db()

    Campagne.init_user_levels(db.cursor(), user_id)
    db.commit()

    return jsonify({"message": "Levels initialisés"})

@app.route("/level/<int:level_id>", methods=["GET"])
@token_required
def level_detail(level_id):

    user_id = request.user_id
    db = get_db()

    level = Campagne.get_level_detail(db.cursor(), user_id, level_id)

    if not level:
        return jsonify({"error": "Niveau introuvable"}), 404

    return jsonify(level)

@app.route("/play/<int:level_id>", methods=["POST"])
@token_required
def play(level_id):

    data = request.get_json()
    guess = data.get("guess")

    user_id = request.user_id
    db = get_db()
    cursor = db.cursor()

    result = Level.check_guess(cursor, level_id, guess)
    db.commit()

    return jsonify({"result": result})

@app.route("/end_game", methods=["POST"])
@token_required
def end_game():

    data = request.get_json()

    nb_music = data.get("nb_music")
    time_left = data.get("time_left")
    lives_remaining = data.get("lives_remaining")
    campaign_id = data.get("campaign_id")

    user_id = request.user_id

    db = get_db()

    result = Victory.calcul_score(
        db,
        user_id=user_id,
        nb_music=nb_music,
        time_left=time_left,
        lives_remaining=lives_remaining,
        campaign_id=campaign_id
    )

    xp_reward = {
        1: 100,
        2: 250,
        3: 500
    }

    Victory.add_xp(db, user_id, xp_reward[result["stars"]])

    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

