from MultiBlindTest_Back.Library.bdd_client import execute_sql, execute_script


def _ensure_result_table():
    execute_script("""
    CREATE TABLE IF NOT EXISTS UserLevelResults (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        UserID TEXT NOT NULL,
        LevelID INTEGER,
        CampaignID INTEGER,
        score INTEGER DEFAULT 0,
        stars INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)


class Victory:
    @staticmethod
    def calcul_score(user_id, nb_music, time_left, lives_remaining, campaign_id, level_id=None):
        _ensure_result_table()
        nb_music = nb_music or 0
        time_left = time_left or 0
        lives_remaining = lives_remaining or 0
        score = (nb_music * 100000) + (time_left * 1000) + (lives_remaining * 50000)
        stars = Victory.etoiles_from_values(score, nb_music, time_left)
        payload = execute_sql(
            'INSERT INTO UserLevelResults (UserID, LevelID, CampaignID, score, stars) VALUES (?, ?, ?, ?, ?)',
            (str(user_id), level_id, campaign_id, score, stars),
        )
        return {'score': score, 'stars': stars, 'victory_id': payload.get('lastrowid')}

    @staticmethod
    def etoiles_from_values(score, nb_music, total_time):
        score = score or 0
        nb_music = nb_music or 0
        total_time = total_time or 0
        score_total = (nb_music * 250000) + (total_time * 1000) + (3 * 50000)
        if score_total <= 0:
            return 0
        if score < score_total / 3:
            return 1
        if score < score_total * 0.75:
            return 2
        return 3

    @staticmethod
    def etoiles(victory_id):
        _ensure_result_table()
        payload = execute_sql('SELECT stars FROM UserLevelResults WHERE ID = ?', (victory_id,))
        rows = payload.get('rows', [])
        return rows[0].get('stars') if rows else 0

    @staticmethod
    def add_xp(user_id, xp):
        execute_sql('UPDATE Profils SET XP = COALESCE(XP, 0) + ? WHERE UserID = ?', (xp, user_id))
