import uuid
from datetime import datetime


class Clip:
    @staticmethod
    def create_clip(db, track_id, start_time, duration, file_path, difficulty_level="normal"):
        clip_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()

        db.execute("""
            INSERT INTO Clips (ID, TrackID, StartTime, Duration, FilePath, DifficultyLevel, CreatedAt)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (clip_id, track_id, start_time, duration, file_path, difficulty_level, created_at))

        return clip_id

    @staticmethod
    def get_clip(db, clip_id):
        db.execute("""
            SELECT c.ID, c.TrackID, c.StartTime, c.Duration, c.FilePath, c.DifficultyLevel, c.CreatedAt,
                   t.Title, t.Artist
            FROM Clips c
            JOIN Tracks t ON c.TrackID = t.ID
            WHERE c.ID = ?
        """, (clip_id,))

        row = db.fetchone()

        if not row:
            return None

        return {
            "id": row["ID"],
            "track_id": row["TrackID"],
            "start_time": row["StartTime"],
            "duration": row["Duration"],
            "file_path": row["FilePath"],
            "difficulty_level": row["DifficultyLevel"],
            "created_at": row["CreatedAt"],
            "title": row["Title"],
            "artist": row["Artist"]
        }

    @staticmethod
    def get_clips_by_track(db, track_id):
        db.execute("""
            SELECT ID, TrackID, StartTime, Duration, FilePath, DifficultyLevel, CreatedAt
            FROM Clips
            WHERE TrackID = ?
            ORDER BY StartTime ASC
        """, (track_id,))

        rows = db.fetchall()

        return [{
            "id": row["ID"],
            "track_id": row["TrackID"],
            "start_time": row["StartTime"],
            "duration": row["Duration"],
            "file_path": row["FilePath"],
            "difficulty_level": row["DifficultyLevel"],
            "created_at": row["CreatedAt"]
        } for row in rows]

    @staticmethod
    def get_clips_by_difficulty(db, difficulty_level):
        db.execute("""
            SELECT c.ID, c.TrackID, c.StartTime, c.Duration, c.FilePath, c.DifficultyLevel, c.CreatedAt,
                   t.Title, t.Artist
            FROM Clips c
            JOIN Tracks t ON c.TrackID = t.ID
            WHERE c.DifficultyLevel = ?
            ORDER BY c.CreatedAt DESC
        """, (difficulty_level,))

        rows = db.fetchall()

        return [{
            "id": row["ID"],
            "track_id": row["TrackID"],
            "start_time": row["StartTime"],
            "duration": row["Duration"],
            "file_path": row["FilePath"],
            "difficulty_level": row["DifficultyLevel"],
            "created_at": row["CreatedAt"],
            "title": row["Title"],
            "artist": row["Artist"]
        } for row in rows]

    @staticmethod
    def update_clip(db, clip_id, **kwargs):
        allowed_fields = ["StartTime", "Duration", "FilePath", "DifficultyLevel"]
        updates = []
        values = []

        for key, value in kwargs.items():
            field_map = {
                "start_time": "StartTime",
                "duration": "Duration",
                "file_path": "FilePath",
                "difficulty_level": "DifficultyLevel"
            }
            field_name = field_map.get(key, key)

            if field_name in allowed_fields:
                updates.append(f"{field_name} = ?")
                values.append(value)

        if not updates:
            return

        values.append(clip_id)
        query = f"UPDATE Clips SET {', '.join(updates)} WHERE ID = ?"

        db.execute(query, values)

    @staticmethod
    def delete_clip(db, clip_id):
        db.execute("DELETE FROM Clips WHERE ID = ?", (clip_id,))

    @staticmethod
    def get_random_clip(db, difficulty_level=None):
        if difficulty_level:
            query = """
                SELECT c.ID, c.TrackID, c.StartTime, c.Duration, c.FilePath, c.DifficultyLevel, c.CreatedAt,
                       t.Title, t.Artist
                FROM Clips c
                JOIN Tracks t ON c.TrackID = t.ID
                WHERE c.DifficultyLevel = ?
                ORDER BY RANDOM()
                LIMIT 1
            """
            db.execute(query, (difficulty_level,))
        else:
            query = """
                SELECT c.ID, c.TrackID, c.StartTime, c.Duration, c.FilePath, c.DifficultyLevel, c.CreatedAt,
                       t.Title, t.Artist
                FROM Clips c
                JOIN Tracks t ON c.TrackID = t.ID
                ORDER BY RANDOM()
                LIMIT 1
            """
            db.execute(query)

        row = db.fetchone()

        if not row:
            return None

        return {
            "id": row["ID"],
            "track_id": row["TrackID"],
            "start_time": row["StartTime"],
            "duration": row["Duration"],
            "file_path": row["FilePath"],
            "difficulty_level": row["DifficultyLevel"],
            "created_at": row["CreatedAt"],
            "title": row["Title"],
            "artist": row["Artist"]
        }

    @staticmethod
    def get_all_clips(db, limit=None):
        query = """
            SELECT c.ID, c.TrackID, c.StartTime, c.Duration, c.FilePath, c.DifficultyLevel, c.CreatedAt,
                   t.Title, t.Artist
            FROM Clips c
            JOIN Tracks t ON c.TrackID = t.ID
            ORDER BY c.CreatedAt DESC
        """

        if limit:
            query += f" LIMIT {limit}"

        db.execute(query)
        rows = db.fetchall()

        return [{
            "id": row["ID"],
            "track_id": row["TrackID"],
            "start_time": row["StartTime"],
            "duration": row["Duration"],
            "file_path": row["FilePath"],
            "difficulty_level": row["DifficultyLevel"],
            "created_at": row["CreatedAt"],
            "title": row["Title"],
            "artist": row["Artist"]
        } for row in rows]