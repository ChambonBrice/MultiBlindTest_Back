from MultiBlindTest_Back.Library.bdd_client import execute_sql


class Level:
    @staticmethod
    def get_lives(user_id, level_id):
        payload = execute_sql(
            """
            SELECT l.lives
            FROM Levels l
            JOIN Levels_Etat le ON le.level_id = l.ID
            WHERE le.user_id = ? AND l.ID = ?
            """,
            (user_id, level_id),
        )
        rows = payload.get('rows', [])
        return rows[0]['lives'] if rows else None

    @staticmethod
    def get_tracks(level_id):
        payload = execute_sql('SELECT ID, Name, PATH FROM Music WHERE LevelsID = ?', (level_id,))
        return [{'id': r['ID'], 'name': r['Name'], 'path': r['PATH']} for r in payload.get('rows', [])]

    @staticmethod
    def check_guess(level_id, guess):
        normalized = (guess or '').lower().strip()
        found = execute_sql('SELECT * FROM FoundTracks WHERE session_id = ? AND track_name = ?', (level_id, normalized))
        if found.get('rows'):
            return 'already_found'
        tracks_payload = execute_sql('SELECT Name FROM Music WHERE LevelsID = ?', (level_id,))
        tracks = [row['Name'].lower() for row in tracks_payload.get('rows', [])]
        if normalized in tracks:
            execute_sql('INSERT INTO FoundTracks (session_id, track_name) VALUES (?, ?)', (level_id, normalized))
            return 'correct'
        return 'wrong'

    @staticmethod
    def get_hint(level_id):
        payload = execute_sql('SELECT hint FROM Levels WHERE ID = ?', (level_id,))
        rows = payload.get('rows', [])
        return rows[0]['hint'] if rows else None
