from MultiBlindTest_Back.Library.bdd_client import execute_sql


class Victory:
    @staticmethod
    def calcul_score(user_id, nb_music, time_left, lives_remaining, campaign_id):
        nb_music = nb_music or 0
        time_left = time_left or 0
        lives_remaining = lives_remaining or 0
        score = (nb_music * 100000) + (time_left * 1000) + (lives_remaining * 50000)
        payload = execute_sql(
            'INSERT INTO Victory (score, CampaignID, UserID) VALUES (?, ?, ?)',
            (score, campaign_id, user_id),
        )
        victory_id = payload.get('lastrowid')
        stars = Victory.etoiles(victory_id)
        return {'score': score, 'stars': stars, 'victory_id': victory_id}

    @staticmethod
    def etoiles(victory_id):
        payload = execute_sql(
            """
            SELECT v.score, l.nb_music, l.timer
            FROM Victory v
            JOIN CampaignLevels cl ON v.CampaignID = cl.CampaignID
            JOIN Levels l ON cl.LevelsID = l.ID
            WHERE v.id = ?
            ORDER BY cl.ID ASC
            LIMIT 1
            """,
            (victory_id,),
        )
        rows = payload.get('rows', [])
        if not rows:
            return 0
        result = rows[0]
        score = result['score']
        nb_music = result.get('nb_music') or 0
        total_time = result.get('timer') or 0
        score_total = (nb_music * 250000) + (total_time * 1000) + (3 * 50000)
        if score_total <= 0:
            stars = 0
        elif score < score_total / 3:
            stars = 1
        elif score < score_total * 0.75:
            stars = 2
        else:
            stars = 3
        execute_sql('UPDATE Victory SET stars = ? WHERE id = ?', (stars, victory_id))
        return stars

    @staticmethod
    def add_xp(user_id, xp):
        execute_sql('UPDATE Profils SET XP = XP + ? WHERE UserID = ?', (xp, user_id))
