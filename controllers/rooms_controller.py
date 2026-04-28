from flask import Blueprint, request, jsonify
from MultiBlindTest_Back.Flask.auth_utils import token_required
from MultiBlindTest_Back.Library.bdd_client import get_db_session
from MultiBlindTest_Back.services.game_service import GameService
from MultiBlindTest_Back.Library.bdd_client import get_db_session

rooms_bp = Blueprint("rooms", __name__, url_prefix="/rooms")


def get_db():
    return get_db_session()


@rooms_bp.route("", methods=["POST"])
@token_required
def create_room():
    data = request.get_json(silent=True) or {}

    max_players = data.get("max_players", 8)
    total_rounds = data.get("total_rounds", 1)

    try:
        max_players = int(max_players)
        total_rounds = int(total_rounds)
    except (TypeError, ValueError):
        return jsonify({"error": "max_players et total_rounds doivent être des entiers"}), 400

    if max_players <= 0:
        return jsonify({"error": "max_players doit être > 0"}), 400

    if total_rounds <= 0:
        return jsonify({"error": "total_rounds doit être > 0"}), 400

    db = get_db()
    cursor = db.cursor()

    result = GameService.create_room(
        db=cursor,
        user_id=request.user_id,
        max_players=max_players,
        total_rounds=total_rounds
    )

    db.commit()
    return jsonify(result), 201


@rooms_bp.route("/<code>/join", methods=["POST"])
@token_required
def join_room(code):
    db = get_db()
    cursor = db.cursor()

    result, status = GameService.join_room(
        db=cursor,
        code=code,
        user_id=request.user_id
    )

    if status < 400:
        db.commit()

    return jsonify(result), status


@rooms_bp.route("/<code>/ready", methods=["PATCH"])
@token_required
def set_ready(code):
    data = request.get_json(silent=True) or {}

    if "is_ready" not in data:
        return jsonify({"error": "Le champ is_ready est requis"}), 400

    is_ready = bool(data.get("is_ready"))

    db = get_db()
    cursor = db.cursor()

    result, status = GameService.set_ready(
        db=cursor,
        code=code,
        user_id=request.user_id,
        is_ready=is_ready
    )

    if status < 400:
        db.commit()

    return jsonify(result), status


@rooms_bp.route("/<code>", methods=["GET"])
@token_required
def get_room_state(code):
    db = get_db()
    cursor = db.cursor()

    result, status = GameService.get_room_state(
        db=cursor,
        code=code
    )

    return jsonify(result), status