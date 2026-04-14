from MultiBlindTest_Back.Library.bdd_client import execute_sql


class LevelCreatorService:
    @staticmethod
    def ensure_tables():
        execute_sql(
            """
            CREATE TABLE IF NOT EXISTS Levels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                artist_tag TEXT,
                theme TEXT DEFAULT 'NEON_PINK',
                FOREIGN KEY(user_id) REFERENCES Users(id)
            )
            """
        )
        execute_sql(
            """
            CREATE TABLE IF NOT EXISTS LevelTracks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level_id INTEGER NOT NULL,
                media_url TEXT NOT NULL,
                start_point REAL DEFAULT 0.0,
                duration REAL DEFAULT 10.0,
                difficulty INTEGER DEFAULT 1,
                FOREIGN KEY(level_id) REFERENCES Levels(id)
            )
            """
        )

    @staticmethod
    def create_level(user_id, title, artist_tag, theme):
        LevelCreatorService.ensure_tables()
        payload = execute_sql(
            "INSERT INTO Levels (user_id, title, artist_tag, theme) VALUES (?, ?, ?, ?)",
            (user_id, title, artist_tag, theme),
        )
        return payload.get("lastrowid")

    @staticmethod
    def add_track(level_id, media_url, start_point=0.0, duration=10.0, difficulty=1):
        execute_sql(
            """
            INSERT INTO LevelTracks (level_id, media_url, start_point, duration, difficulty)
            VALUES (?, ?, ?, ?, ?)
            """,
            (level_id, media_url, start_point, duration, difficulty),
        )

    @staticmethod
    def get_level(level_id):
        payload_level = execute_sql("SELECT * FROM Levels WHERE id = ?", (level_id,))
        payload_tracks = execute_sql("SELECT * FROM LevelTracks WHERE level_id = ?", (level_id,))
        level_rows = payload_level.get("rows", [])
        level = level_rows[0] if level_rows else None
        return {"level": dict(level) if level else None, "tracks": [dict(t) for t in payload_tracks.get("rows", [])]}

    @staticmethod
    def list_user_levels(user_id):
        payload = execute_sql("SELECT * FROM Levels WHERE user_id = ?", (user_id,))
        return [dict(l) for l in payload.get("rows", [])]
