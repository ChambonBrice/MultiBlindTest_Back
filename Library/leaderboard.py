from flask import Blueprint, jsonify, request
from MultiBlindTest_Back.Library.Authentification import Authentification
leaderboard_bp = Blueprint("leaderboard", __name__)

@leaderboard_bp.route("/leaderboard/global", methods=["GET"])
def global_leaderboard():
    limit = request.args.get("limit", 100, type=int)

    users = Authentification.get_global_leaderboard(limit)

    leaderboard = []
    for rank, user in enumerate(users, start=1):
        leaderboard.append({
            "rank": rank,
            "name": user["name"],
            "points": user["points"],
            "level": user.get("level", 1)
        })

    return jsonify(leaderboard)

@leaderboard_bp.route("/leaderboard/local", methods=["GET"])
def local_leaderboard():
    country = request.args.get("country")
    limit = request.args.get("limit", 100, type=int)

    if not country:
        return jsonify({"error": "country requis"}), 400

    users = Authentification.get_local_leaderboard(country, limit)

    leaderboard = []
    for rank, user in enumerate(users, start=1):
        leaderboard.append({
            "rank": rank,
            "name": user["name"],
            "points": user["points"]
        })

    return jsonify(leaderboard)

@leaderboard_bp.route("/add_points", methods=["POST"])
def add_points():
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON invalide"}), 400

    name = data.get("name")
    points = data.get("points")

    if not name or points is None:
        return jsonify({"error": "Champs 'name' et 'points' requis"}), 400

    success = Authentification.add_points(name, points)

    if not success:
        return jsonify({"error": "Utilisateur non trouvé"}), 404

    return jsonify({"message": f"{points} points ajoutés à {name}"}), 200