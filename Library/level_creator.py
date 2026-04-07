import sqlite3
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
DB_PATH = os.path.join(BASE_DIR, "bdd")
DB_NAME = os.path.join(DB_PATH, "MBT.db")

class LevelCreatorService:
    @staticmethod
    def get_connection():
        os.makedirs(DB_PATH, exist_ok=True)
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def ensure_tables():
        conn = LevelCreatorService.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Levels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                artist_tag TEXT,
                theme TEXT DEFAULT 'NEON_PINK',
                FOREIGN KEY(user_id) REFERENCES Users(id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS LevelTracks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level_id INTEGER NOT NULL,
                media_url TEXT NOT NULL,
                start_point REAL DEFAULT 0.0,
                duration REAL DEFAULT 10.0,
                difficulty INTEGER DEFAULT 1,
                FOREIGN KEY(level_id) REFERENCES Levels(id)
            )
        """)
        conn.commit()
        conn.close()

    @staticmethod
    def create_level(user_id, title, artist_tag, theme):
        LevelCreatorService.ensure_tables()
        conn = LevelCreatorService.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Levels (user_id, title, artist_tag, theme) VALUES (?, ?, ?, ?)",
                       (user_id, title, artist_tag, theme))
        level_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return level_id

    @staticmethod
    def add_track(level_id, media_url, start_point=0.0, duration=10.0, difficulty=1):
        conn = LevelCreatorService.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO LevelTracks (level_id, media_url, start_point, duration, difficulty)
            VALUES (?, ?, ?, ?, ?)""",
            (level_id, media_url, start_point, duration, difficulty)
        )
        conn.commit()
        conn.close()

    @staticmethod
    def get_level(level_id):
        conn = LevelCreatorService.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Levels WHERE id = ?", (level_id,))
        level = cursor.fetchone()
        cursor.execute("SELECT * FROM LevelTracks WHERE level_id = ?", (level_id,))
        tracks = cursor.fetchall()
        conn.close()
        return {"level": dict(level), "tracks": [dict(t) for t in tracks]}

    @staticmethod
    def list_user_levels(user_id):
        conn = LevelCreatorService.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Levels WHERE user_id = ?", (user_id,))
        levels = cursor.fetchall()
        conn.close()
        return [dict(l) for l in levels]