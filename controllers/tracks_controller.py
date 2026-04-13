from flask import Blueprint, request, jsonify, g
from MultiBlindTest_Back.Library.tracks import Track
from MultiBlindTest_Back.services.audio_service import AudioService
from MultiBlindTest_Back.Flask.auth_utils import token_required

tracks_bp = Blueprint("tracks", __name__, url_prefix="/tracks")


def get_db():
    return g.db


@tracks_bp.route("", methods=["POST"])
@token_required
def create_track():
    data = request.get_json()

    if not data:
        return jsonify({"error": "JSON invalide"}), 400

    title = data.get("title")
    artist = data.get("artist")
    youtube_url = data.get("youtube_url")
    level_id = data.get("level_id")

    if not title or not artist or not youtube_url:
        return jsonify({"error": "title, artist et youtube_url sont requis"}), 400

    db = get_db()
    cursor = db.cursor()

    try:
        file_path, duration = AudioService.download_audio_from_youtube(youtube_url)

        track_id = Track.create_track(
            db=cursor,
            title=title,
            artist=artist,
            youtube_url=youtube_url,
            duration=duration,
            file_path=file_path,
            level_id=level_id
        )
        db.commit()

        return jsonify({
            "message": "Track créée avec succès",
            "track_id": track_id,
            "title": title,
            "artist": artist,
            "duration": duration,
            "file_path": file_path
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@tracks_bp.route("", methods=["GET"])
@token_required
def get_all_tracks():
    db = get_db()
    cursor = db.cursor()

    limit = request.args.get("limit", type=int)
    tracks = Track.get_all_tracks(cursor, limit=limit)

    return jsonify(tracks), 200


@tracks_bp.route("/search", methods=["GET"])
@token_required
def search_tracks():
    query_text = request.args.get("q")

    if not query_text:
        return jsonify({"error": "Paramètre q requis"}), 400

    db = get_db()
    cursor = db.cursor()

    results = Track.search_tracks(cursor, query_text)
    return jsonify(results), 200


@tracks_bp.route("/<track_id>", methods=["GET"])
@token_required
def get_track(track_id):
    db = get_db()
    cursor = db.cursor()

    track = Track.get_track(cursor, track_id)

    if not track:
        return jsonify({"error": "Track introuvable"}), 404

    return jsonify(track), 200


@tracks_bp.route("/<track_id>", methods=["PATCH"])
@token_required
def update_track(track_id):
    data = request.get_json()

    if not data:
        return jsonify({"error": "JSON invalide"}), 400

    db = get_db()
    cursor = db.cursor()

    track = Track.get_track(cursor, track_id)
    if not track:
        return jsonify({"error": "Track introuvable"}), 404

    updates = {}
    for field in ["title", "artist", "youtube_url", "duration", "file_path"]:
        if field in data:
            updates[field] = data[field]

    if not updates:
        return jsonify({"error": "Aucune donnée à mettre à jour"}), 400

    Track.update_track(cursor, track_id, **updates)
    db.commit()

    return jsonify({"message": "Track mise à jour"}), 200


@tracks_bp.route("/<track_id>", methods=["DELETE"])
@token_required
def delete_track(track_id):
    db = get_db()
    cursor = db.cursor()

    track = Track.get_track(cursor, track_id)
    if not track:
        return jsonify({"error": "Track introuvable"}), 404

    Track.delete_track(cursor, track_id)
    db.commit()

    return jsonify({"message": "Track supprimée"}), 200