from flask import Blueprint, jsonify, request

from MultiBlindTest_Back.Flask.auth_utils import token_required
from MultiBlindTest_Back.Library.bdd_client import BDDAPIError, execute_sql, execute_script
from MultiBlindTest_Back.Library.campagne import Campagne

campaign_bp = Blueprint("campaign", __name__, url_prefix="/campaign")


def _ensure_result_table():
    execute_script("""
    CREATE TABLE IF NOT EXISTS UserLevelResults (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        UserID TEXT NOT NULL,
        LevelID INTEGER,
        CampaignID INTEGER,
        score INTEGER DEFAULT 0,
        stars INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)


def _best_stars_for_level(user_id, level_id):
    _ensure_result_table()
    payload = execute_sql(
        """
        SELECT COALESCE(MAX(stars), 0) AS stars, COALESCE(MAX(score), 0) AS best_score
        FROM UserLevelResults
        WHERE UserID = ? AND LevelID = ?
        """,
        (str(user_id), level_id),
    )
    rows = payload.get("rows", [])
    if not rows:
        return {"stars": 0, "best_score": 0}
    return {
        "stars": rows[0].get("stars") or 0,
        "best_score": rows[0].get("best_score") or 0,
    }


def _enrich_level(user_id, level):
    progress = _best_stars_for_level(user_id, level["id"])
    return {**level, **progress}


@campaign_bp.route("/levels", methods=["GET"])
@token_required
def get_campaign_levels():
    campaign_id = request.args.get("campaign_id", 1, type=int)
    try:
        Campagne.init_user_levels(request.user_id, campaign_id)
        levels = Campagne.get_levels(request.user_id, campaign_id)
        return jsonify([_enrich_level(request.user_id, level) for level in levels]), 200
    except BDDAPIError as e:
        return jsonify({"error": str(e)}), 502


@campaign_bp.route("/levels/<int:level_id>", methods=["GET"])
@token_required
def get_campaign_level_detail(level_id):
    """Détail d'un niveau de campagne, verrouillage inclus."""
    campaign_id = request.args.get("campaign_id", 1, type=int)
    try:
        Campagne.init_user_levels(request.user_id, campaign_id)
        detail = Campagne.get_level_detail(request.user_id, level_id)
        if not detail:
            return jsonify({"error": "Niveau introuvable pour cet utilisateur"}), 404
        return jsonify(_enrich_level(request.user_id, detail)), 200
    except BDDAPIError as e:
        return jsonify({"error": str(e)}), 502


@campaign_bp.route("/levels/<int:level_id>/complete", methods=["POST"])
@token_required
def complete_campaign_level(level_id):
    """Marque un niveau comme terminé et débloque le niveau suivant."""
    try:
        detail = Campagne.get_level_detail(request.user_id, level_id)
        if not detail:
            return jsonify({"error": "Niveau introuvable pour cet utilisateur"}), 404
        if detail.get("etat") == "locked":
            return jsonify({"error": "Ce niveau est verrouillé"}), 403

        Campagne.complete_level(request.user_id, level_id)
        return jsonify({"message": "Niveau complété", "level_id": level_id}), 200
    except BDDAPIError as e:
        return jsonify({"error": str(e)}), 502
