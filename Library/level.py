class Level:

    @staticmethod
    def get_lives(db, user_id, level_id):
        db.execute("""
            SELECT l.lives
            FROM Levels l
            JOIN Levels_Etat le ON le.level_id = l.ID
            WHERE le.user_id = ? AND l.ID = ?
        """, (user_id, level_id))

        row = db.fetchone()
        return row["lives"] if row else None

    @staticmethod
    def get_tracks(db, level_id):
        db.execute("""
            SELECT ID, Name, PATH
            FROM Music
            WHERE LevelsID = ?
        """, (level_id,))

        return [
            {"id": row["ID"], "name": row["Name"], "path": row["PATH"]}
            for row in db.fetchall()
        ]

    @staticmethod
    def check_guess(db, level_id, guess):
        db.execute("""
            SELECT *
            FROM FoundTracks
            WHERE session_id = ? AND track_name = ?
        """, (level_id, guess.lower().strip()))

        if db.fetchone():
            return "already_found"

        db.execute("""
            SELECT Name
            FROM Music
            WHERE LevelsID = ?
        """, (level_id,))

        tracks = [row["Name"].lower() for row in db.fetchall()]

        if guess.lower().strip() in tracks:
            db.execute("""
                INSERT INTO FoundTracks (session_id, track_name)
                VALUES (?, ?)
            """, (level_id, guess.lower().strip()))
            return "correct"

        return "wrong"

    @staticmethod
    def get_hint(db, level_id):
        db.execute("""
            SELECT hint
            FROM Levels
            WHERE ID = ?
        """, (level_id,))

        row = db.fetchone()
        return row["hint"] if row else None