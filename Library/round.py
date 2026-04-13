from datetime import datetime, timedelta


class Round:
    @staticmethod
    def create_round(db, room_id, round_number, duration_seconds, start_delay_seconds=3):
        start_at = datetime.utcnow() + timedelta(seconds=start_delay_seconds)
        end_at = start_at + timedelta(seconds=duration_seconds)

        db.execute("""
            INSERT INTO GameRounds (
                room_id, round_number, status, start_at, end_at, duration_seconds
            )
            VALUES (?, ?, 'active', ?, ?, ?)
        """, (
            room_id,
            round_number,
            start_at.isoformat(),
            end_at.isoformat(),
            duration_seconds
        ))

        return {
            "id": db.lastrowid,
            "room_id": room_id,
            "round_number": round_number,
            "status": "active",
            "start_at": start_at.isoformat(),
            "end_at": end_at.isoformat(),
            "duration_seconds": duration_seconds
        }

    @staticmethod
    def get_round_by_id(db, round_id):
        db.execute("""
            SELECT *
            FROM GameRounds
            WHERE id = ?
        """, (round_id,))
        return db.fetchone()

    @staticmethod
    def get_current_room_round(db, room_id):
        db.execute("""
            SELECT *
            FROM GameRounds
            WHERE room_id = ?
            ORDER BY round_number DESC, id DESC
            LIMIT 1
        """, (room_id,))
        return db.fetchone()

    @staticmethod
    def add_round_track(db, round_id, track_id, clip_id, answer_text, display_order):
        db.execute("""
            INSERT INTO RoundTracks (
                round_id, track_id, clip_id, answer_text, display_order
            )
            VALUES (?, ?, ?, ?, ?)
        """, (round_id, track_id, clip_id, answer_text, display_order))

    @staticmethod
    def get_round_tracks(db, round_id):
        db.execute("""
            SELECT
                rt.id,
                rt.round_id,
                rt.track_id,
                rt.clip_id,
                rt.answer_text,
                rt.display_order,
                t.Title,
                t.Artist,
                c.FilePath,
                c.StartTime,
                c.Duration
            FROM RoundTracks rt
            JOIN Tracks t ON t.ID = rt.track_id
            JOIN Clips c ON c.ID = rt.clip_id
            WHERE rt.round_id = ?
            ORDER BY rt.display_order ASC
        """, (round_id,))
        return db.fetchall()

    @staticmethod
    def find_round_track_by_answer(db, round_id, normalized_answer):
        db.execute("""
            SELECT *
            FROM RoundTracks
            WHERE round_id = ? AND lower(trim(answer_text)) = ?
            LIMIT 1
        """, (round_id, normalized_answer))
        return db.fetchone()

    @staticmethod
    def end_round(db, round_id):
        db.execute("""
            UPDATE GameRounds
            SET status = 'ended'
            WHERE id = ?
        """, (round_id,))

    @staticmethod
    def count_round_tracks(db, round_id):
        db.execute("""
            SELECT COUNT(*) AS total
            FROM RoundTracks
            WHERE round_id = ?
        """, (round_id,))
        row = db.fetchone()
        return row["total"]