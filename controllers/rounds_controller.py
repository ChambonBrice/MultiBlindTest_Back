from flask import Blueprint, request, jsonify
from MultiBlindTest_Back.Flask.auth_utils import token_required
from MultiBlindTest_Back.Library.bdd_client import get_db_session
from MultiBlindTest_Back.services.game_service import GameService
from MultiBlindTest_Back.Library.bdd_client import get_db_session
from MultiBlindTest_Back.services.round_service import RoundService

rounds_bp = Blueprint("rounds", __name__, url_prefix="/rounds")


def get_db():
    return get_db_session()


@rounds_bp.route("/room/<code>/start", methods=["POST"])
@token_required
def start_round(code):
    data = request.get_json(silent=True) or {}

    track_count = data.get("track_count", 3)
    duration_seconds = data.get("duration_seconds", 30)

    try:
        track_count = int(track_count)
        duration_seconds = int(duration_seconds)
    except (TypeError, ValueError):
        return jsonify({"error": "track_count et duration_seconds doivent être des entiers"}), 400

    if track_count <= 0:
        return jsonify({"error": "track_count doit être > 0"}), 400

    if duration_seconds <= 0:
        return jsonify({"error": "duration_seconds doit être > 0"}), 400

    db = get_db()
    cursor = db.cursor()

    result, status = GameService.start_round(
        db=cursor,
        code=code,
        user_id=request.user_id,
        track_count=track_count,
        duration_seconds=duration_seconds
    )

    if status < 400:
        db.commit()

    return jsonify(result), status


@rounds_bp.route("/<int:round_id>/answer", methods=["POST"])
@token_required
def submit_answer(round_id):
    data = request.get_json(silent=True) or {}
    answer = data.get("answer")

    db = get_db()
    cursor = db.cursor()

    result, status = RoundService.submit_answer(
        db=cursor,
        round_id=round_id,
        user_id=request.user_id,
        answer=answer
    )

    if status < 400:
        db.commit()

    return jsonify(result), status


@rounds_bp.route("/<int:round_id>/state", methods=["GET"])
@token_required
def get_round_state(round_id):
    db = get_db()
    cursor = db.cursor()

    result, status = RoundService.get_round_state(
        db=cursor,
        round_id=round_id,
        user_id=request.user_id
    )

    return jsonify(result), status


@rounds_bp.route("/<int:round_id>/leaderboard", methods=["GET"])
@token_required
def get_round_leaderboard(round_id):
    db = get_db()
    cursor = db.cursor()

    result, status = RoundService.get_round_leaderboard(
        db=cursor,
        round_id=round_id
    )

    return jsonify(result), status