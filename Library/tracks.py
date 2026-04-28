import uuid
from datetime import datetime


class Track:
    @staticmethod
    def create_track(db, title, artist, youtube_url, duration, file_path, level_id=None):
        track_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()

        db.execute("""
            INSERT INTO Tracks (ID, Title, Artist, YouTubeURL, Duration, FilePath, LevelID, CreatedAt)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (track_id, title, artist, youtube_url, duration, file_path, level_id, created_at))

        return track_id

    @staticmethod
    def get_track(db, track_id):
        db.execute("""
            SELECT ID, Title, Artist, YouTubeURL, Duration, FilePath, LevelID, CreatedAt
            FROM Tracks
            WHERE ID = ?
        """, (track_id,))

        row = db.fetchone()

        if not row:
            return None

        return {
            "id": row["ID"],
            "title": row["Title"],
            "artist": row["Artist"],
            "youtube_url": row["YouTubeURL"],
            "duration": row["Duration"],
            "file_path": row["FilePath"],
            "level_id": row["LevelID"],
            "created_at": row["CreatedAt"]
        }

    @staticmethod
    def get_tracks_by_level(db, level_id):
        db.execute("""
            SELECT ID, Title, Artist, YouTubeURL, Duration, FilePath, LevelID, CreatedAt
            FROM Tracks
            WHERE LevelID = ?
            ORDER BY CreatedAt ASC
        """, (level_id,))

        rows = db.fetchall()

        return [{
            "id": row["ID"],
            "title": row["Title"],
            "artist": row["Artist"],
            "youtube_url": row["YouTubeURL"],
            "duration": row["Duration"],
            "file_path": row["FilePath"],
            "level_id": row["LevelID"],
            "created_at": row["CreatedAt"]
        } for row in rows]

    @staticmethod
    def update_track(db, track_id, **kwargs):
        allowed_fields = ["Title", "Artist", "Duration", "FilePath", "YouTubeURL"]
        updates = []
        values = []

        for key, value in kwargs.items():
            if key in allowed_fields or key.capitalize() in allowed_fields:
                field_name = key if key in allowed_fields else key.capitalize()
                updates.append(f"{field_name} = ?")
                values.append(value)

        if not updates:
            return

        values.append(track_id)
        query = f"UPDATE Tracks SET {', '.join(updates)} WHERE ID = ?"

        db.execute(query, values)

    @staticmethod
    def delete_track(db, track_id):
        db.execute("DELETE FROM Clips WHERE TrackID = ?", (track_id,))

        db.execute("DELETE FROM Tracks WHERE ID = ?", (track_id,))

    @staticmethod
    def get_all_tracks(db, limit=None):
        query = "SELECT ID, Title, Artist, YouTubeURL, Duration, FilePath, LevelID, CreatedAt FROM Tracks"

        if limit:
            query += f" LIMIT {limit}"

        db.execute(query)
        rows = db.fetchall()

        return [{
            "id": row["ID"],
            "title": row["Title"],
            "artist": row["Artist"],
            "youtube_url": row["YouTubeURL"],
            "duration": row["Duration"],
            "file_path": row["FilePath"],
            "level_id": row["LevelID"],
            "created_at": row["CreatedAt"]
        } for row in rows]

    @staticmethod
    def search_tracks(db, query_text):
        search_pattern = f"%{query_text}%"

        db.execute("""
            SELECT ID, Title, Artist, YouTubeURL, Duration, FilePath, LevelID, CreatedAt
            FROM Tracks
            WHERE Title LIKE ? OR Artist LIKE ?
            ORDER BY Title ASC
        """, (search_pattern, search_pattern))

        rows = db.fetchall()

        return [{
            "id": row["ID"],
            "title": row["Title"],
            "artist": row["Artist"],
            "youtube_url": row["YouTubeURL"],
            "duration": row["Duration"],
            "file_path": row["FilePath"],
            "level_id": row["LevelID"],
            "created_at": row["CreatedAt"]
        } for row in rows]