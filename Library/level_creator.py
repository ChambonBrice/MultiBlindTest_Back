from MultiBlindTest_Back.Library.bdd_client import execute_sql, execute_script


class LevelCreatorService:
    @staticmethod
    def ensure_tables():
        execute_script("""
        CREATE TABLE IF NOT EXISTS LevelsCustom (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            artist_tag TEXT,
            theme TEXT DEFAULT 'NEON_PINK',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES Users(id)
        );
        CREATE TABLE IF NOT EXISTS LevelTracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level_id INTEGER NOT NULL,
            media_url TEXT NOT NULL,
            start_point REAL DEFAULT 0.0,
            duration REAL DEFAULT 10.0,
            difficulty INTEGER DEFAULT 1,
            FOREIGN KEY(level_id) REFERENCES LevelsCustom(id)
        );
        """)

    @staticmethod
    def create_level(user_id, title, artist_tag, theme):
        LevelCreatorService.ensure_tables()
        payload = execute_sql(
            'INSERT INTO LevelsCustom (user_id, title, artist_tag, theme) VALUES (?, ?, ?, ?)',
            (user_id, title, artist_tag, theme),
        )
        return payload.get('lastrowid')

    @staticmethod
    def add_track(level_id, media_url, start_point=0.0, duration=10.0, difficulty=1):
        execute_sql(
            'INSERT INTO LevelTracks (level_id, media_url, start_point, duration, difficulty) VALUES (?, ?, ?, ?, ?)',
            (level_id, media_url, start_point, duration, difficulty),
        )

    @staticmethod
    def get_level(level_id):
        level_payload = execute_sql('SELECT * FROM LevelsCustom WHERE id = ?', (level_id,))
        tracks_payload = execute_sql('SELECT * FROM LevelTracks WHERE level_id = ?', (level_id,))
        levels = level_payload.get('rows', [])
        return {'level': levels[0] if levels else None, 'tracks': tracks_payload.get('rows', [])}

    @staticmethod
    def list_user_levels(user_id):
        payload = execute_sql('SELECT * FROM LevelsCustom WHERE user_id = ? ORDER BY id DESC', (user_id,))
        return payload.get('rows', [])
