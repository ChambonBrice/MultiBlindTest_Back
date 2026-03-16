from flask import Blueprint, jsonify, request
from back.Library.Authentification import Authentification

leaderboard_bp = Blueprint("leaderboard", __name__)

players = []

@leaderboard_bp.route("/leaderboard/global", methods=["GET"])
def global_leaderboard():

    sorted_players = sorted(players, key=lambda x: x["points"], reverse=True)

    leaderboard = []

    for rank, player in enumerate(sorted_players, start=1):
        leaderboard.append({
            "rank": rank,
            "name": player["name"],
            "points": player["points"],
        })

    return jsonify(leaderboard)


@leaderboard_bp.route("/leaderboard/local", methods=["GET"])
def local_leaderboard():

    country = request.args.get("country")
    limit = request.args.get("limit", 100)

    if not country:
        return jsonify({"error": "country requis"}), 400

    users = Authentification.get_local_leaderboard(country, limit)
    leaderboard = []
    for rank, user in enumerate(users, start=1):
        leaderboard.append({
            "rank": rank,
            "name": user["name"],
            "points": user["points"],
        })

    return jsonify(leaderboard)

@leaderboard_bp.route("/add_points", methods=["POST"])
def add_points():

    data = request.get_json()

    name = data.get("name")
    points = data.get("points")

    player_found = False

    for player in players:
        if player["name"] == name:
            player["points"] += points
            player_found = True

    if not player_found:
        players.append({
            "name": name,
            "avatar": "default.png",
            "level": 1,
            "points": points,
            "title": "Débutant"
        })

    return jsonify({"message": "Points ajoutés"})