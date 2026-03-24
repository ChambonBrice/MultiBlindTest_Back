class Campagne:

    @staticmethod
    def get_levels(db, user_id):

        campagne_id = 1

        query = """
                SELECT l.ID, l.LevelName, l.Difficulty, l.nb_music, le.etat
                FROM CampaignLevels cl
                JOIN Levels l ON l.ID = cl.LevelID
                JOIN Levels_Etat le ON l.ID = le.level_id
                WHERE cl.CampaignID = ?
                AND le.user_id = ?
                ORDER BY cl.ID ASC 
                """

        db.execute(query, (campagne_id, user_id))
        results = db.fetchall()

        return [{
            "id": row["ID"],
            "nom": row["LevelName"],
            "difficulty": row["Difficulty"],
            "nb_music": row["nb_music"],
            "etat": row["etat"]
        } for row in results]

    @staticmethod
    def complete_level(db, user_id, level_id):

        db.execute("""
                   UPDATE Levels_Etat
                   SET etat = 'completed'
                   WHERE user_id = ?
                     AND level_id = ?
                   """, (user_id, level_id))

        db.execute("""
                   SELECT cl.ID
                   FROM CampaignLevels cl
                   WHERE cl.LevelID = ?
                   """, (level_id,))
        current = db.fetchone()

        if not current:
            return

        next_id = current["ID"] + 1

        db.execute("""
                   SELECT LevelID
                   FROM CampaignLevels
                   WHERE ID = ?
                   """, (next_id,))
        next_level = db.fetchone()

        if next_level:
            db.execute("""
                       UPDATE Levels_Etat
                       SET etat = 'unlocked'
                       WHERE user_id = ?
                         AND level_id = ?
                       """, (user_id, next_level["LevelID"]))

    @staticmethod
    def init_user_levels(db, user_id):

        campagne_id = 1

        db.execute("""
                   SELECT l.ID
                   FROM CampaignLevels cl
                   JOIN Levels l ON l.ID = cl.LevelID
                   WHERE cl.CampaignID = ?
                   ORDER BY cl.LevelID ASC
                   """, (campagne_id,))

        levels = db.fetchall()

        for i, level in enumerate(levels):
            etat = "unlocked" if i == 0 else "locked"

            db.execute("""
                       INSERT
                       OR IGNORE INTO Levels_Etat (user_id, level_id, etat)
                VALUES (?, ?, ?)
                       """, (user_id, level["ID"], etat))

    @staticmethod
    def get_level_detail(db, user_id, level_id):

        db.execute("""
                   SELECT l.ID, l.LevelName, l.Difficulty, l.timer, l.lives, l.hint, le.etat
                   FROM Levels l
                            JOIN Levels_Etat le ON l.ID = le.level_id
                   WHERE l.ID = ?
                     AND le.user_id = ?
                   """, (level_id, user_id))

        row = db.fetchone()

        if not row:
            return None

        db.execute("""
                   SELECT ID, Name, PATH
                   FROM Music
                   WHERE LevelID = ?
                   """, (level_id,))

        tracks = db.fetchall()

        return {
            "id": row["ID"],
            "nom": row["LevelName"],
            "difficulty": row["Difficulty"],
            "etat": row["etat"],
            "timer": row["timer"],
            "lives": row["lives"],
            "hint": row["hint"],
            "tracks": [
                {"id": t["ID"], "name": t["Name"], "path": t["PATH"]}
                for t in tracks
            ]
        }

    @staticmethod
    def get_music(db, level_id):

        db.execute("""
                   SELECT ID FROM Music WHERE LevelID = ?
                   """, (level_id,))

        rows = db.fetchall()

        return [row["ID"] for row in rows]