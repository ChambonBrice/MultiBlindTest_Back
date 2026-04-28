from datetime import datetime, timezone
from MultiBlindTest_Back.Library.round import Round
from MultiBlindTest_Back.Library.player_state import PlayerState
from MultiBlindTest_Back.Library.room import Room


class RoundService:
    @staticmethod
    def normalize_answer(answer):
        return answer.strip().lower()

    @staticmethod
    def _parse_iso_datetime(value):
        if not value:
            return None
        try:
            dt = datetime.fromisoformat(value)
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except ValueError:
            return None

    @staticmethod
    def _compute_time_left_ms(end_at_str):
        end_at = RoundService._parse_iso_datetime(end_at_str)
        if not end_at:
            return 0
        now = datetime.now(timezone.utc)
        diff_ms = int((end_at - now).total_seconds() * 1000)
        return max(0, diff_ms)

    @staticmethod
    def _compute_points(time_left_ms):
        base_points = 100
        speed_bonus = time_left_ms // 1000
        return base_points + speed_bonus

    @staticmethod
    def get_round_state(db, round_id, user_id):
        round_row = Round.get_round_by_id(db, round_id)
        if not round_row:
            return {"error": "Manche introuvable"}, 404

        state = PlayerState.get_player_round_state(db, round_id, user_id)
        if not state:
            return {"error": "État joueur introuvable pour cette manche"}, 404

        tracks = Round.get_round_tracks(db, round_id)
        found_tracks = PlayerState.get_found_tracks(db, round_id, user_id)
        found_track_ids = {row["round_track_id"] for row in found_tracks}

        leaderboard = PlayerState.get_round_leaderboard(db, round_id)

        return {
            "round_id": round_row["id"],
            "room_id": round_row["room_id"],
            "round_number": round_row["round_number"],
            "status": round_row["status"],
            "start_at": round_row["start_at"],
            "end_at": round_row["end_at"],
            "duration_seconds": round_row["duration_seconds"],
            "player_state": {
                "found_count": state["found_count"],
                "time_left_ms": state["time_left_ms"],
                "round_score": state["round_score"],
                "status": state["status"],
                "completed_at": state["completed_at"]
            },
            "tracks": [
                {
                    "round_track_id": t["id"],
                    "clip_id": t["clip_id"],
                    "track_id": t["track_id"],
                    "title": t["Title"],
                    "artist": t["Artist"],
                    "file_path": t["FilePath"],
                    "display_order": t["display_order"],
                    "found_by_me": t["id"] in found_track_ids
                }
                for t in tracks
            ],
            "leaderboard": [
                {
                    "user_id": row["user_id"],
                    "name": row["name"],
                    "found_count": row["found_count"],
                    "round_score": row["round_score"],
                    "time_left_ms": row["time_left_ms"],
                    "status": row["status"]
                }
                for row in leaderboard
            ]
        }, 200

    @staticmethod
    def submit_answer(db, round_id, user_id, answer):
        if not answer:
            return {"error": "Réponse manquante"}, 400

        round_row = Round.get_round_by_id(db, round_id)
        if not round_row:
            return {"error": "Manche introuvable"}, 404

        if round_row["status"] != "active":
            return {"error": "La manche n'est plus active"}, 400

        player_state = PlayerState.get_player_round_state(db, round_id, user_id)
        if not player_state:
            return {"error": "Joueur non inscrit à cette manche"}, 403

        if player_state["status"] != "playing":
            return {"error": "Le joueur a déjà terminé cette manche"}, 400

        time_left_ms = RoundService._compute_time_left_ms(round_row["end_at"])
        if time_left_ms <= 0:
            PlayerState.timeout_player_round(db, round_id, user_id)
            return {"error": "Temps écoulé"}, 400

        normalized_answer = RoundService.normalize_answer(answer)
        matched_track = Round.find_round_track_by_answer(db, round_id, normalized_answer)

        if not matched_track:
            return {
                "result": "wrong",
                "message": "Réponse incorrecte"
            }, 200

        already_found = PlayerState.has_player_found_track(
            db=db,
            round_id=round_id,
            user_id=user_id,
            round_track_id=matched_track["id"]
        )

        if already_found:
            return {
                "result": "already_found",
                "message": "Déjà trouvée"
            }, 200

        points = RoundService._compute_points(time_left_ms)

        PlayerState.mark_track_found(
            db=db,
            round_id=round_id,
            user_id=user_id,
            round_track_id=matched_track["id"],
            points_awarded=points
        )

        total_tracks = Round.count_round_tracks(db, round_id)
        updated_state = PlayerState.get_player_round_state(db, round_id, user_id)

        finished = updated_state["found_count"] >= total_tracks
        if finished:
            bonus_completion = max(0, time_left_ms // 100)
            db.execute("""
                UPDATE PlayerRoundState
                SET round_score = round_score + ?
                WHERE round_id = ? AND user_id = ?
            """, (bonus_completion, round_id, user_id))

            PlayerState.finish_player_round(db, round_id, user_id, time_left_ms)
            Room.add_score(db, round_row["room_id"], user_id, points + bonus_completion)
        else:
            Room.add_score(db, round_row["room_id"], user_id, points)

        if PlayerState.are_all_players_done(db, round_id):
            Round.end_round(db, round_id)

            current_room = Room.get_room_by_id(db, round_row["room_id"])
            if current_room["current_round"] >= current_room["total_rounds"]:
                Room.update_room_status(db, current_room["id"], "finished")
                Room.update_finished_at(db, current_room["id"])
            else:
                Room.update_room_status(db, current_room["id"], "waiting")

        final_state = PlayerState.get_player_round_state(db, round_id, user_id)
        leaderboard = PlayerState.get_round_leaderboard(db, round_id)

        return {
            "result": "correct",
            "message": "Bonne réponse",
            "round_track_id": matched_track["id"],
            "points_awarded": points,
            "player_state": {
                "found_count": final_state["found_count"],
                "round_score": final_state["round_score"],
                "status": final_state["status"],
                "time_left_ms": final_state["time_left_ms"]
            },
            "leaderboard": [
                {
                    "user_id": row["user_id"],
                    "name": row["name"],
                    "found_count": row["found_count"],
                    "round_score": row["round_score"],
                    "status": row["status"]
                }
                for row in leaderboard
            ]
        }, 200

    @staticmethod
    def get_round_leaderboard(db, round_id):
        round_row = Round.get_round_by_id(db, round_id)
        if not round_row:
            return {"error": "Manche introuvable"}, 404

        leaderboard = PlayerState.get_round_leaderboard(db, round_id)

        return {
            "round_id": round_id,
            "leaderboard": [
                {
                    "rank": index + 1,
                    "user_id": row["user_id"],
                    "name": row["name"],
                    "found_count": row["found_count"],
                    "round_score": row["round_score"],
                    "time_left_ms": row["time_left_ms"],
                    "status": row["status"]
                }
                for index, row in enumerate(leaderboard)
            ]
        }, 200