import random
import string


class Room:
    @staticmethod
    def generate_code(length=6):
        chars = string.ascii_uppercase + string.digits
        return "".join(random.choices(chars, k=length))

    @staticmethod
    def create_room(db, host_user_id, max_players=8, total_rounds=1):
        code = Room.generate_code()

        # évite collision de code
        while True:
            db.execute("SELECT id FROM GameRooms WHERE code = ?", (code,))
            if not db.fetchone():
                break
            code = Room.generate_code()

        db.execute("""
            INSERT INTO GameRooms (
                code, host_user_id, status, max_players, current_round, total_rounds
            )
            VALUES (?, ?, 'waiting', ?, 0, ?)
        """, (code, host_user_id, max_players, total_rounds))

        room_id = db.lastrowid

        db.execute("""
            INSERT INTO RoomPlayers (
                room_id, user_id, is_host, is_ready, connection_status, total_score
            )
            VALUES (?, ?, 1, 0, 'connected', 0)
        """, (room_id, host_user_id))

        return {
            "id": room_id,
            "code": code,
            "host_user_id": host_user_id,
            "status": "waiting",
            "max_players": max_players,
            "current_round": 0,
            "total_rounds": total_rounds
        }

    @staticmethod
    def get_room_by_code(db, code):
        db.execute("""
            SELECT *
            FROM GameRooms
            WHERE code = ?
        """, (code,))
        return db.fetchone()

    @staticmethod
    def get_room_by_id(db, room_id):
        db.execute("""
            SELECT *
            FROM GameRooms
            WHERE id = ?
        """, (room_id,))
        return db.fetchone()

    @staticmethod
    def add_player(db, room_id, user_id):
        db.execute("""
            INSERT INTO RoomPlayers (
                room_id, user_id, is_host, is_ready, connection_status, total_score
            )
            VALUES (?, ?, 0, 0, 'connected', 0)
        """, (room_id, user_id))

    @staticmethod
    def is_player_in_room(db, room_id, user_id):
        db.execute("""
            SELECT 1
            FROM RoomPlayers
            WHERE room_id = ? AND user_id = ? AND left_at IS NULL
        """, (room_id, user_id))
        return db.fetchone() is not None

    @staticmethod
    def get_room_players(db, room_id):
        db.execute("""
            SELECT
                rp.id,
                rp.room_id,
                rp.user_id,
                rp.is_host,
                rp.is_ready,
                rp.joined_at,
                rp.left_at,
                rp.connection_status,
                rp.total_score,
                u.name
            FROM RoomPlayers rp
            JOIN Users u ON u.id = rp.user_id
            WHERE rp.room_id = ? AND rp.left_at IS NULL
            ORDER BY rp.joined_at ASC
        """, (room_id,))
        return db.fetchall()

    @staticmethod
    def count_players(db, room_id):
        db.execute("""
            SELECT COUNT(*) AS total
            FROM RoomPlayers
            WHERE room_id = ? AND left_at IS NULL
        """, (room_id,))
        row = db.fetchone()
        return row["total"]

    @staticmethod
    def set_ready(db, room_id, user_id, is_ready):
        db.execute("""
            UPDATE RoomPlayers
            SET is_ready = ?
            WHERE room_id = ? AND user_id = ? AND left_at IS NULL
        """, (1 if is_ready else 0, room_id, user_id))

    @staticmethod
    def is_host(db, room_id, user_id):
        db.execute("""
            SELECT 1
            FROM RoomPlayers
            WHERE room_id = ? AND user_id = ? AND is_host = 1 AND left_at IS NULL
        """, (room_id, user_id))
        return db.fetchone() is not None

    @staticmethod
    def all_non_host_players_ready(db, room_id):
        db.execute("""
            SELECT COUNT(*) AS not_ready_count
            FROM RoomPlayers
            WHERE room_id = ?
              AND left_at IS NULL
              AND is_host = 0
              AND is_ready = 0
        """, (room_id,))
        row = db.fetchone()
        return row["not_ready_count"] == 0

    @staticmethod
    def update_room_status(db, room_id, status):
        db.execute("""
            UPDATE GameRooms
            SET status = ?
            WHERE id = ?
        """, (status, room_id))

    @staticmethod
    def increment_current_round(db, room_id):
        db.execute("""
            UPDATE GameRooms
            SET current_round = current_round + 1
            WHERE id = ?
        """, (room_id,))

    @staticmethod
    def update_started_at(db, room_id):
        db.execute("""
            UPDATE GameRooms
            SET started_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (room_id,))

    @staticmethod
    def update_finished_at(db, room_id):
        db.execute("""
            UPDATE GameRooms
            SET finished_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (room_id,))

    @staticmethod
    def add_score(db, room_id, user_id, score_delta):
        db.execute("""
            UPDATE RoomPlayers
            SET total_score = total_score + ?
            WHERE room_id = ? AND user_id = ?
        """, (score_delta, room_id, user_id))