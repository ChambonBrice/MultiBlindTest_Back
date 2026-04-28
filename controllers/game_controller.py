from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from MultiBlindTest_Back.Flask.auth_utils import token_required
from MultiBlindTest_Back.Library.bdd_client import BDDAPIError, execute_script, execute_sql
from MultiBlindTest_Back.Library.campagne import Campagne
from MultiBlindTest_Back.Library.victory import Victory


game_bp = Blueprint("game", __name__, url_prefix="/levels")


def json_or_empty():
    return request.get_json(silent=True) or {}


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _normalize(value):
    return (value or "").strip().lower()


def _ensure_game_tables():
    execute_script(
        """
        CREATE TABLE IF NOT EXISTS GameSessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            level_id INTEGER NOT NULL,
            campaign_id INTEGER DEFAULT 1,
            status TEXT DEFAULT 'playing',
            lives_remaining INTEGER DEFAULT 3,
            hints_used INTEGER DEFAULT 0,
            time_left INTEGER DEFAULT 0,
            started_at TEXT DEFAULT CURRENT_TIMESTAMP,
            ended_at TEXT
        );

        CREATE TABLE IF NOT EXISTS GameSessionFoundTracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            music_id INTEGER,
            track_name TEXT NOT NULL,
            found_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(session_id, music_id)
        );
        """
    )


def _get_level(level_id):
    payload = execute_sql(
        """
        SELECT
            l.ID,
            l.LevelName,
            l.Difficulty,
            l.hint,
            l.stats,
            60 AS timer,
            3 AS lives,
            COALESCE(COUNT(m.ID), 0) AS nb_music
        FROM Levels l
        LEFT JOIN Music m ON m.LevelsID = l.ID
        WHERE l.ID = ?
        GROUP BY l.ID, l.LevelName, l.Difficulty, l.hint, l.stats
        """,
        (level_id,),
    )
    rows = payload.get("rows", [])
    return rows[0] if rows else None


def _get_level_state(user_id, level_id):
    payload = execute_sql(
        "SELECT etat FROM Levels_Etat WHERE user_id = ? AND level_id = ?",
        (user_id, level_id),
    )
    rows = payload.get("rows", [])
    return rows[0]["etat"] if rows else None


def _get_active_session(user_id, level_id):
    _ensure_game_tables()
    payload = execute_sql(
        """
        SELECT *
        FROM GameSessions
        WHERE user_id = ? AND level_id = ? AND status = 'playing'
        ORDER BY id DESC
        LIMIT 1
        """,
        (user_id, level_id),
    )
    rows = payload.get("rows", [])
    return rows[0] if rows else None


def _get_session(session_id, user_id):
    payload = execute_sql(
        "SELECT * FROM GameSessions WHERE id = ? AND user_id = ?",
        (session_id, user_id),
    )
    rows = payload.get("rows", [])
    return rows[0] if rows else None


def _create_session(user_id, level_id, campaign_id=1):
    _ensure_game_tables()
    level = _get_level(level_id)
    if not level:
        return None

    payload = execute_sql(
        """
        INSERT INTO GameSessions (
            user_id, level_id, campaign_id, status, lives_remaining, hints_used, time_left, started_at
        ) VALUES (?, ?, ?, 'playing', ?, 0, ?, ?)
        """,
        (
            user_id,
            level_id,
            campaign_id,
            level.get("lives") or 3,
            level.get("timer") or 0,
            _now_iso(),
        ),
    )
    return _get_session(payload.get("lastrowid"), user_id)


def _tracks_for_level(level_id):
    payload = execute_sql(
        "SELECT ID, Name, PATH FROM Music WHERE LevelsID = ? ORDER BY ID ASC",
        (level_id,),
    )
    return payload.get("rows", [])


def _found_for_session(session_id):
    payload = execute_sql(
        "SELECT music_id, track_name FROM GameSessionFoundTracks WHERE session_id = ?",
        (session_id,),
    )
    return payload.get("rows", [])


def _format_game_state(session):
    level = _get_level(session["level_id"])
    tracks = _tracks_for_level(session["level_id"])
    found_rows = _found_for_session(session["id"])
    found_ids = {row.get("music_id") for row in found_rows}
    found_names = {_normalize(row.get("track_name")) for row in found_rows}

    visual_tracks = []
    for index, track in enumerate(tracks, start=1):
        is_found = track.get("ID") in found_ids or _normalize(track.get("Name")) in found_names
        visual_tracks.append(
            {
                "id": track.get("ID"),
                "order": index,
                "found": is_found,
                "name": track.get("Name") if is_found else None,
                "path": track.get("PATH") if is_found else None,
            }
        )

    found_count = len([track for track in visual_tracks if track["found"]])
    total = len(visual_tracks)
    return {
        "session_id": session["id"],
        "level_id": session["level_id"],
        "level_name": level.get("LevelName") if level else None,
        "status": session.get("status"),
        "lives_remaining": session.get("lives_remaining"),
        "time_left": session.get("time_left"),
        "hints_used": session.get("hints_used") or 0,
        "total_tracks": total,
        "found_count": found_count,
        "missing_count": max(total - found_count, 0),
        "tracks": visual_tracks,
    }


@game_bp.route("/<int:level_id>/start", methods=["POST"])
@token_required
def start_level(level_id):
    data = json_or_empty()
    campaign_id = data.get("campaign_id", 1)
    try:
        Campagne.init_user_levels(request.user_id, campaign_id)
        state = _get_level_state(request.user_id, level_id)
        if state == "locked":
            return jsonify({"error": "Ce niveau est verrouillé"}), 403
        if state is None:
            return jsonify({"error": "Niveau introuvable dans la campagne"}), 404

        session = _get_active_session(request.user_id, level_id) or _create_session(request.user_id, level_id, campaign_id)
        if not session:
            return jsonify({"error": "Niveau introuvable"}), 404
        return jsonify(_format_game_state(session)), 201
    except BDDAPIError as e:
        return jsonify({"error": str(e)}), 502


@game_bp.route("/<int:level_id>/game-state", methods=["GET"])
@token_required
def get_game_state(level_id):
    try:
        session = _get_active_session(request.user_id, level_id)
        if not session:
            return jsonify({"error": "Aucune partie active. Lance la route start avant."}), 404
        return jsonify(_format_game_state(session)), 200
    except BDDAPIError as e:
        return jsonify({"error": str(e)}), 502


@game_bp.route("/<int:level_id>/answer", methods=["POST"])
@token_required
def answer_level(level_id):
    data = json_or_empty()
    guess = _normalize(data.get("guess") or data.get("answer"))
    time_left = data.get("time_left")

    if not guess:
        return jsonify({"error": "Réponse manquante"}), 400

    try:
        session = _get_active_session(request.user_id, level_id)
        if not session:
            return jsonify({"error": "Aucune partie active. Lance la route start avant."}), 404

        already_found = _found_for_session(session["id"])
        if guess in {_normalize(row.get("track_name")) for row in already_found}:
            state = _format_game_state(session)
            return jsonify({"result": "already_found", "state": state}), 200

        tracks = _tracks_for_level(level_id)
        matching_track = next((track for track in tracks if _normalize(track.get("Name")) == guess), None)

        if matching_track:
            execute_sql(
                "INSERT OR IGNORE INTO GameSessionFoundTracks (session_id, music_id, track_name, found_at) VALUES (?, ?, ?, ?)",
                (session["id"], matching_track.get("ID"), matching_track.get("Name"), _now_iso()),
            )
            if time_left is not None:
                execute_sql("UPDATE GameSessions SET time_left = ? WHERE id = ?", (time_left, session["id"]))
            session = _get_session(session["id"], request.user_id)
            state = _format_game_state(session)
            return jsonify({"result": "correct", "track": matching_track.get("Name"), "state": state}), 200

        new_lives = max((session.get("lives_remaining") or 0) - 1, 0)
        execute_sql(
            "UPDATE GameSessions SET lives_remaining = ?, time_left = COALESCE(?, time_left) WHERE id = ?",
            (new_lives, time_left, session["id"]),
        )
        session = _get_session(session["id"], request.user_id)
        state = _format_game_state(session)
        return jsonify({"result": "wrong", "state": state, "game_over": new_lives <= 0}), 200
    except BDDAPIError as e:
        return jsonify({"error": str(e)}), 502


@game_bp.route("/<int:level_id>/hint", methods=["POST"])
@token_required
def get_level_hint(level_id):
    try:
        session = _get_active_session(request.user_id, level_id)
        if not session:
            return jsonify({"error": "Aucune partie active. Lance la route start avant."}), 404

        level = _get_level(level_id)
        execute_sql("UPDATE GameSessions SET hints_used = COALESCE(hints_used, 0) + 1 WHERE id = ?", (session["id"],))
        session = _get_session(session["id"], request.user_id)
        return jsonify({"hint": level.get("hint") if level else None, "state": _format_game_state(session)}), 200
    except BDDAPIError as e:
        return jsonify({"error": str(e)}), 502


@game_bp.route("/<int:level_id>/end-game", methods=["POST"])
@token_required
def end_level_game(level_id):
    data = json_or_empty()
    try:
        session = _get_active_session(request.user_id, level_id)
        if not session:
            return jsonify({"error": "Aucune partie active à terminer"}), 404

        time_left = data.get("time_left", session.get("time_left") or 0)
        campaign_id = data.get("campaign_id", session.get("campaign_id") or 1)
        state = _format_game_state(session)

        result = Victory.calcul_score(
            user_id=request.user_id,
            nb_music=state["found_count"],
            time_left=time_left,
            lives_remaining=session.get("lives_remaining") or 0,
            campaign_id=campaign_id,
            level_id=level_id,
        )
        Victory.add_xp(request.user_id, 250)

        completed = state["total_tracks"] > 0 and state["found_count"] == state["total_tracks"]
        if completed:
            Campagne.complete_level(request.user_id, level_id)

        execute_sql(
            "UPDATE GameSessions SET status = 'finished', time_left = ?, ended_at = ? WHERE id = ?",
            (time_left, _now_iso(), session["id"]),
        )

        return jsonify({
            "message": "Partie terminée",
            "completed": completed,
            "result": result,
            "state": state,
        }), 200
    except BDDAPIError as e:
        return jsonify({"error": str(e)}), 502
