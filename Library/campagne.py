from MultiBlindTest_Back.Library.bdd_client import execute_sql


class Campagne:
    @staticmethod
    def get_levels(user_id, campagne_id=1):
        payload = execute_sql(
            """
            SELECT l.ID, l.LevelName, l.Difficulty, l.nb_music, le.etat
            FROM CampaignLevels cl
            JOIN Levels l ON l.ID = cl.LevelsID
            JOIN Levels_Etat le ON l.ID = le.level_id
            WHERE cl.CampaignID = ? AND le.user_id = ?
            ORDER BY cl.ID ASC
            """,
            (campagne_id, user_id),
        )
        return [{
            'id': row['ID'],
            'nom': row['LevelName'],
            'difficulty': row['Difficulty'],
            'nb_music': row['nb_music'],
            'etat': row['etat'],
        } for row in payload.get('rows', [])]

    @staticmethod
    def complete_level(user_id, level_id):
        execute_sql(
            "UPDATE Levels_Etat SET etat = 'completed' WHERE user_id = ? AND level_id = ?",
            (user_id, level_id),
        )
        current_payload = execute_sql('SELECT cl.ID FROM CampaignLevels cl WHERE cl.LevelsID = ?', (level_id,))
        current_rows = current_payload.get('rows', [])
        if not current_rows:
            return
        next_id = current_rows[0]['ID'] + 1
        next_payload = execute_sql('SELECT LevelsID FROM CampaignLevels WHERE ID = ?', (next_id,))
        next_rows = next_payload.get('rows', [])
        if next_rows:
            execute_sql(
                "UPDATE Levels_Etat SET etat = 'unlocked' WHERE user_id = ? AND level_id = ?",
                (user_id, next_rows[0]['LevelsID']),
            )

    @staticmethod
    def init_user_levels(user_id, campagne_id=1):
        payload = execute_sql(
            """
            SELECT l.ID
            FROM CampaignLevels cl
            JOIN Levels l ON l.ID = cl.LevelsID
            WHERE cl.CampaignID = ?
            ORDER BY cl.ID ASC
            """,
            (campagne_id,),
        )
        for i, level in enumerate(payload.get('rows', [])):
            etat = 'unlocked' if i == 0 else 'locked'
            execute_sql(
                'INSERT OR IGNORE INTO Levels_Etat (user_id, level_id, etat) VALUES (?, ?, ?)',
                (user_id, level['ID'], etat),
            )

    @staticmethod
    def get_level_detail(user_id, level_id):
        payload = execute_sql(
            """
            SELECT l.ID, l.LevelName, l.Difficulty, l.timer, l.lives, l.hint, le.etat
            FROM Levels l
            JOIN Levels_Etat le ON l.ID = le.level_id
            WHERE l.ID = ? AND le.user_id = ?
            """,
            (level_id, user_id),
        )
        rows = payload.get('rows', [])
        if not rows:
            return None
        row = rows[0]
        tracks_payload = execute_sql('SELECT ID, Name, PATH FROM Music WHERE LevelsID = ?', (level_id,))
        return {
            'id': row['ID'],
            'nom': row['LevelName'],
            'difficulty': row['Difficulty'],
            'etat': row['etat'],
            'timer': row['timer'],
            'lives': row['lives'],
            'hint': row['hint'],
            'tracks': [
                {'id': t['ID'], 'name': t['Name'], 'path': t['PATH']}
                for t in tracks_payload.get('rows', [])
            ],
        }

    @staticmethod
    def get_music(level_id):
        payload = execute_sql('SELECT ID FROM Music WHERE LevelsID = ?', (level_id,))
        return [row['ID'] for row in payload.get('rows', [])]
