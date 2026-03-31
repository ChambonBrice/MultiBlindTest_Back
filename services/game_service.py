import random
from MultiBlindTest_Back.Library.room import Room
from MultiBlindTest_Back.Library.round import Round
from MultiBlindTest_Back.Library.player_state import PlayerState


class GameService:
    @staticmethod
    def create_room(db, user_id, max_players=8, total_rounds=1):
        room = Room.create_room(
            db=db,
            host_user_id=user_id,
            max_players=max_players,
            total_rounds=total_rounds
        )
        return room

    @staticmethod
    def join_room(db, code, user_id):
        room = Room.get_room_by_code(db, code)
        if not room:
            return {"error": "Room introuvable"}, 404

        if room["status"] != "waiting":
            return {"error": "La room n'accepte plus de joueurs"}, 400

        if Room.is_player_in_room(db, room["id"], user_id):
            return {"message": "Déjà présent dans la room", "code": room["code"]}, 200

        current_players = Room.count_players(db, room["id"])
        if current_players >= room["max_players"]:
            return {"error": "Room pleine"}, 400

        Room.add_player(db, room["id"], user_id)

        return {
            "message": "Room rejointe",
            "room_id": room["id"],
            "code": room["code"]
        }, 200

    @staticmethod
    def set_ready(db, code, user_id, is_ready):
        room = Room.get_room_by_code(db, code)
        if not room:
            return {"error": "Room introuvable"}, 404

        if not Room.is_player_in_room(db, room["id"], user_id):
            return {"error": "Joueur non présent dans la room"}, 403

        Room.set_ready(db, room["id"], user_id, is_ready)

        return {
            "message": "État ready mis à jour",
            "is_ready": bool(is_ready)
        }, 200

    @staticmethod
    def get_room_state(db, code):
        room = Room.get_room_by_code(db, code)
        if not room:
            return {"error": "Room introuvable"}, 404

        players = Room.get_room_players(db, room["id"])

        return {
            "id": room["id"],
            "code": room["code"],
            "status": room["status"],
            "host_user_id": room["host_user_id"],
            "max_players": room["max_players"],
            "current_round": room["current_round"],
            "total_rounds": room["total_rounds"],
            "players": [
                {
                    "user_id": p["user_id"],
                    "name": p["name"],
                    "is_host": bool(p["is_host"]),
                    "is_ready": bool(p["is_ready"]),
                    "connection_status": p["connection_status"],
                    "total_score": p["total_score"]
                }
                for p in players
            ]
        }, 200

    @staticmethod
    def start_round(db, code, user_id, track_count=3, duration_seconds=30):
        room = Room.get_room_by_code(db, code)
        if not room:
            return {"error": "Room introuvable"}, 404

        if not Room.is_host(db, room["id"], user_id):
            return {"error": "Seul l'hôte peut lancer la manche"}, 403

        if room["status"] not in ("waiting", "starting", "in_progress"):
            return {"error": "Statut de room invalide"}, 400

        player_count = Room.count_players(db, room["id"])
        if player_count < 1:
            return {"error": "Aucun joueur dans la room"}, 400

        if room["current_round"] >= room["total_rounds"]:
            return {"error": "Toutes les manches ont déjà été jouées"}, 400

        if player_count > 1 and not Room.all_non_host_players_ready(db, room["id"]):
            return {"error": "Tous les joueurs ne sont pas prêts"}, 400

        Room.update_room_status(db, room["id"], "starting")
        Room.increment_current_round(db, room["id"])
        Room.update_started_at(db, room["id"])

        updated_room = Room.get_room_by_id(db, room["id"])
        round_number = updated_room["current_round"]

        created_round = Round.create_round(
            db=db,
            room_id=room["id"],
            round_number=round_number,
            duration_seconds=duration_seconds,
            start_delay_seconds=3
        )

        round_id = created_round["id"]

        db.execute("""
            SELECT
                c.ID AS clip_id,
                c.TrackID AS track_id,
                t.Title AS title
            FROM Clips c
            JOIN Tracks t ON t.ID = c.TrackID
            ORDER BY RANDOM()
            LIMIT ?
        """, (track_count,))
        selected_clips = db.fetchall()

        if len(selected_clips) < track_count:
            return {"error": "Pas assez de clips disponibles"}, 400

        for index, clip in enumerate(selected_clips, start=1):
            Round.add_round_track(
                db=db,
                round_id=round_id,
                track_id=clip["track_id"],
                clip_id=clip["clip_id"],
                answer_text=clip["title"].strip().lower(),
                display_order=index
            )

        players = Room.get_room_players(db, room["id"])
        for player in players:
            PlayerState.create_player_round_state(
                db=db,
                round_id=round_id,
                user_id=player["user_id"]
            )

        Room.update_room_status(db, room["id"], "in_progress")

        round_tracks = Round.get_round_tracks(db, round_id)

        return {
            "message": "Manche créée",
            "room_id": room["id"],
            "round_id": round_id,
            "round_number": round_number,
            "status": "active",
            "start_at": created_round["start_at"],
            "end_at": created_round["end_at"],
            "duration_seconds": duration_seconds,
            "tracks": [
                {
                    "round_track_id": t["id"],
                    "track_id": t["track_id"],
                    "clip_id": t["clip_id"],
                    "title": t["Title"],
                    "artist": t["Artist"],
                    "file_path": t["FilePath"],
                    "start_time": t["StartTime"],
                    "duration": t["Duration"],
                    "display_order": t["display_order"]
                }
                for t in round_tracks
            ]
        }, 201