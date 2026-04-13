<<<<<<< HEAD
=======
import requests

>>>>>>> 5c60396f91d151ce1565d8305ec5e09e4ee4ab23
class Victory:

    @staticmethod
    def calcul_score(db, user_id, nb_music, time_left, lives_remaining, campaign_id):
<<<<<<< HEAD
        cursor = db.cursor()

        nb_music = nb_music or 0
        time_left = time_left or 0
        lives_remaining = lives_remaining or 0

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
=======

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

>>>>>>> 5c60396f91d151ce1565d8305ec5e09e4ee4ab23
        stars = Victory.etoiles(db, victory_id)

        return {
            "score": score,
            "stars": stars,
            "victory_id": victory_id
        }

    @staticmethod
    def etoiles(db, victory_id):
<<<<<<< HEAD
        cursor = db.cursor()

        cursor.execute("""
            SELECT v.score, l.nb_music, l.timer
            FROM Victory v
            JOIN CampaignLevels cl ON v.CampaignID = cl.CampaignID
            JOIN Levels l ON cl.LevelsID = l.ID
            WHERE v.id = ?
            ORDER BY cl.ID ASC
            LIMIT 1
=======

        cursor = db.cursor()

        cursor.execute("""
        SELECT v.score, l.nb_music
        FROM Victory v
        JOIN CampaignLevels cl ON v.CampaignID = cl.CampaignID
        JOIN Levels l ON cl.id = l.id
        WHERE v.id = ?
>>>>>>> 5c60396f91d151ce1565d8305ec5e09e4ee4ab23
        """, (victory_id,))

        result = cursor.fetchone()

        if not result:
            return 0

        score = result["score"]
<<<<<<< HEAD
        nb_music = result["nb_music"] or 0
        total_time = result["timer"] or 0

        score_total = (nb_music * 250000) + (total_time * 1000) + (3 * 50000)

        if score_total <= 0:
            stars = 0
        elif score < score_total / 3:
=======
        nb_music = result["nb_music"]
        total_time = result["time"]

        score_total = (nb_music * 250000) + (total_time * 1000) + (3 * 50000)

        if score < score_total / 3:
>>>>>>> 5c60396f91d151ce1565d8305ec5e09e4ee4ab23
            stars = 1
        elif score < score_total * 0.75:
            stars = 2
        else:
            stars = 3

        cursor.execute("""
<<<<<<< HEAD
            UPDATE Victory
            SET stars = ?
            WHERE id = ?
        """, (stars, victory_id))
=======
                       UPDATE Victory
                       SET stars = ?
                       WHERE id = ?
                       """, (stars, victory_id))

        db.commit()
>>>>>>> 5c60396f91d151ce1565d8305ec5e09e4ee4ab23

        return stars

    @staticmethod
    def add_xp(db, user_id, xp):
<<<<<<< HEAD
        cursor = db.cursor()
        cursor.execute("""
            UPDATE Profils
            SET XP = XP + ?
            WHERE UserID = ?
        """, (xp, user_id))
=======

        cursor = db.cursor()
        cursor.execute("""
                       UPDATE Profils
                       SET XP = XP + 250
                       WHERE UserID = ?
                       """, (xp, user_id,))
        db.commit()
>>>>>>> 5c60396f91d151ce1565d8305ec5e09e4ee4ab23
