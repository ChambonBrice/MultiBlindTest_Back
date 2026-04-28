from flask import Blueprint, jsonify, request

from MultiBlindTest_Back.Flask.auth_utils import token_required
from MultiBlindTest_Back.Library.bdd_client import BDDAPIError
from MultiBlindTest_Back.Library.level_creator import LevelCreatorService

level_creator_bp = Blueprint("level_creator", __name__, url_prefix="/creator")


def json_or_empty():
    return request.get_json(silent=True) or {}


@level_creator_bp.route("/levels", methods=["POST"])
@token_required
def create_creator_level():
    data = json_or_empty()
    title = data.get("title") or data.get("name")
    if not title:
        return jsonify({"error": "title est requis"}), 400

    try:
        level_id = LevelCreatorService.create_level(
            user_id=request.user_id,
            title=title,
            artist_tag=data.get("artist_tag"),
            theme=data.get("theme", "NEON_PINK"),
        )
        return jsonify({"message": "Niveau créé", "level_id": level_id}), 201
    except BDDAPIError as e:
        return jsonify({"error": str(e)}), 502


@level_creator_bp.route("/levels", methods=["GET"])
@token_required
def list_creator_levels():
    try:
        return jsonify(LevelCreatorService.list_user_levels(request.user_id)), 200
    except BDDAPIError as e:
        return jsonify({"error": str(e)}), 502


@level_creator_bp.route("/levels/<int:level_id>", methods=["GET"])
@token_required
def get_creator_level(level_id):
    try:
        level = LevelCreatorService.get_level(level_id)
        if not level.get("level"):
            return jsonify({"error": "Niveau introuvable"}), 404
        if level["level"].get("user_id") != request.user_id:
            return jsonify({"error": "Accès refusé"}), 403
        return jsonify(level), 200
    except BDDAPIError as e:
        return jsonify({"error": str(e)}), 502


@level_creator_bp.route("/levels/<int:level_id>/tracks", methods=["POST"])
@token_required
def add_creator_track(level_id):
    data = json_or_empty()
    media_url = data.get("media_url") or data.get("youtube_url") or data.get("url")
    if not media_url:
        return jsonify({"error": "media_url ou youtube_url est requis"}), 400

    try:
        level = LevelCreatorService.get_level(level_id)
        if not level.get("level"):
            return jsonify({"error": "Niveau introuvable"}), 404
        if level["level"].get("user_id") != request.user_id:
            return jsonify({"error": "Accès refusé"}), 403

        LevelCreatorService.add_track(
            level_id=level_id,
            media_url=media_url,
            start_point=float(data.get("start_point", data.get("start_seconds", 0))),
            duration=float(data.get("duration", data.get("duration_seconds", 10))),
            difficulty=int(data.get("difficulty", 1)),
        )
        return jsonify({"message": "Source YouTube ajoutée", "level_id": level_id}), 201
    except ValueError:
        return jsonify({"error": "start_point, duration et difficulty doivent être numériques"}), 400
    except BDDAPIError as e:
        return jsonify({"error": str(e)}), 502
