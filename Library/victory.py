import requests

class Victory:

    @staticmethod
    def calcul_score(db, user_id, nb_music, time_left, lives_remaining, campaign_id):

        cursor = db.cursor()

        score = (
                nb_music * 100000 +
                time_left * 1000 +
                lives_remaining * 50000
        )

        cursor.execute("""
                       INSERT INTO Victory (score, CampaignID, UserID)
                       VALUES (?, ?, ?)
                       """, (score, campaign_id, user_id))

        victory_id = cursor.lastrowid

        db.commit()

        stars = Victory.etoiles(db, victory_id)

        return {
            "score": score,
            "stars": stars,
            "victory_id": victory_id
        }

    @staticmethod
    def etoiles(db, victory_id):

        cursor = db.cursor()

        cursor.execute("""
        SELECT v.score, l.nb_music
        FROM Victory v
        JOIN CampaignLevels cl ON v.CampaignID = cl.CampaignID
        JOIN Levels l ON cl.id = l.id
        WHERE v.id = ?
        """, (victory_id,))

        result = cursor.fetchone()

        if not result:
            return 0

        score = result["score"]
        nb_music = result["nb_music"]
        total_time = result["time"]

        score_total = (nb_music * 250000) + (total_time * 1000) + (3 * 50000)

        if score < score_total / 3:
            stars = 1
        elif score < score_total * 0.75:
            stars = 2
        else:
            stars = 3

        cursor.execute("""
                       UPDATE Victory
                       SET stars = ?
                       WHERE id = ?
                       """, (stars, victory_id))

        db.commit()

        return stars

    @staticmethod
    def add_xp(db, user_id, xp):

        cursor = db.cursor()
        cursor.execute("""
                       UPDATE Profils
                       SET XP = XP + 250
                       WHERE UserID = ?
                       """, (xp, user_id,))
        db.commit()
