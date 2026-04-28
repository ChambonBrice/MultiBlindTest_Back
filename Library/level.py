from MultiBlindTest_Back.Library.bdd_client import execute_sql


class Level:
    @staticmethod
    def get_lives(user_id, level_id):
        return 3

    @staticmethod
    def get_tracks(level_id):
        payload = execute_sql('SELECT ID, Name, PATH FROM Music WHERE LevelsID = ? ORDER BY ID ASC', (level_id,))
        return [{'id': r.get('ID'), 'name': r.get('Name'), 'path': r.get('PATH')} for r in payload.get('rows', [])]

    @staticmethod
    def check_guess(level_id, guess):
        normalized = (guess or '').lower().strip()
        found = execute_sql('SELECT * FROM FoundTracks WHERE session_id = ? AND LOWER(track_name) = ?', (level_id, normalized))
        if found.get('rows'):
            return 'already_found'
        tracks_payload = execute_sql('SELECT Name FROM Music WHERE LevelsID = ?', (level_id,))
        tracks = [(row.get('Name') or '').lower().strip() for row in tracks_payload.get('rows', [])]
        if normalized in tracks:
            execute_sql('INSERT INTO FoundTracks (session_id, track_name) VALUES (?, ?)', (level_id, normalized))
            return 'correct'
        return 'wrong'

    @staticmethod
    def get_hint(level_id):
        payload = execute_sql('SELECT hint FROM Levels WHERE ID = ?', (level_id,))
        rows = payload.get('rows', [])
        return rows[0].get('hint') if rows else None
