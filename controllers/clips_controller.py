from flask import Blueprint, request, jsonify, g
from MultiBlindTest_Back.Library.clips import Clip
from MultiBlindTest_Back.Library.tracks import Track
from MultiBlindTest_Back.Library.audio_service import AudioService
from MultiBlindTest_Back.Flask.auth_utils import token_required

clips_bp = Blueprint("clips", __name__, url_prefix="/clips")


def get_db():
    return g.db


@clips_bp.route("/track/<track_id>", methods=["POST"])
@token_required
def create_clip(track_id):
    data = request.get_json()

    if not data:
        return jsonify({"error": "JSON invalide"}), 400

    start_time = data.get("start_time")
    duration = data.get("duration")
    difficulty_level = data.get("difficulty_level", "normal")

    if start_time is None or duration is None:
        return jsonify({"error": "start_time et duration sont requis"}), 400

    db = get_db()
    cursor = db.cursor()

    track = Track.get_track(cursor, track_id)
    if not track:
        return jsonify({"error": "Track introuvable"}), 404

    try:
        start_time = int(start_time)
        duration = int(duration)

        AudioService.validate_clip_bounds(
            track_duration=track["duration"],
            start_time=start_time,
            duration=duration
        )

        clip_file = AudioService.create_clip(
            source_file=track["file_path"],
            start_time=start_time,
            duration=duration
        )

        clip_id = Clip.create_clip(
            db=cursor,
            track_id=track_id,
            start_time=start_time,
            duration=duration,
            file_path=clip_file,
            difficulty_level=difficulty_level
        )
        db.commit()

        return jsonify({
            "message": "Clip créé avec succès",
            "clip_id": clip_id,
            "track_id": track_id,
            "start_time": start_time,
            "duration": duration,
            "difficulty_level": difficulty_level,
            "file_path": clip_file
        }), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@clips_bp.route("/<clip_id>", methods=["GET"])
@token_required
def get_clip(clip_id):
    db = get_db()
    cursor = db.cursor()

    clip = Clip.get_clip(cursor, clip_id)

    if not clip:
        return jsonify({"error": "Clip introuvable"}), 404

    return jsonify(clip), 200


@clips_bp.route("/track/<track_id>", methods=["GET"])
@token_required
def get_clips_by_track(track_id):
    db = get_db()
    cursor = db.cursor()

    clips = Clip.get_clips_by_track(cursor, track_id)
    return jsonify(clips), 200


@clips_bp.route("/difficulty/<difficulty_level>", methods=["GET"])
@token_required
def get_clips_by_difficulty(difficulty_level):
    db = get_db()
    cursor = db.cursor()

    clips = Clip.get_clips_by_difficulty(cursor, difficulty_level)
    return jsonify(clips), 200


@clips_bp.route("/<clip_id>", methods=["PATCH"])
@token_required
def update_clip(clip_id):
    data = request.get_json()

    if not data:
        return jsonify({"error": "JSON invalide"}), 400

    db = get_db()
    cursor = db.cursor()

    clip = Clip.get_clip(cursor, clip_id)
    if not clip:
        return jsonify({"error": "Clip introuvable"}), 404

    updates = {}
    if "start_time" in data:
        updates["start_time"] = int(data["start_time"])
    if "duration" in data:
        updates["duration"] = int(data["duration"])
    if "difficulty_level" in data:
        updates["difficulty_level"] = data["difficulty_level"]
    if "file_path" in data:
        updates["file_path"] = data["file_path"]

    if not updates:
        return jsonify({"error": "Aucune donnée à mettre à jour"}), 400

    Clip.update_clip(cursor, clip_id, **updates)
    db.commit()

    return jsonify({"message": "Clip mis à jour"}), 200


@clips_bp.route("/<clip_id>", methods=["DELETE"])
@token_required
def delete_clip(clip_id):
    db = get_db()
    cursor = db.cursor()

    clip = Clip.get_clip(cursor, clip_id)
    if not clip:
        return jsonify({"error": "Clip introuvable"}), 404

    Clip.delete_clip(cursor, clip_id)
    db.commit()

    return jsonify({"message": "Clip supprimé"}), 200