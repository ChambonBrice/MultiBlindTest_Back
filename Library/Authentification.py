import base64
import bcrypt
import uuid

from MultiBlindTest_Back.Library.bdd_client import BDDAPIError, execute_sql


token_blacklist = set()


class Authentification:

    @staticmethod
    def get_user_id(name):
        payload = execute_sql(
            "SELECT id FROM Users WHERE name = ? AND archive = 0 LIMIT 1",
            (name,),
        )
        rows = payload.get("rows", [])
        if rows:
            return rows[0]["id"]
        return None

    @staticmethod
    def hash_password(password):
        password_bytes = password.encode("utf-8")
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return base64.b64encode(hashed).decode("utf-8")

    @staticmethod
    def register(name, email, password):
        hashed_password = Authentification.hash_password(password)
        user_uuid = str(uuid.uuid4())

        try:
            payload = execute_sql(
                """
                INSERT INTO Users (uuid, archive, name, nom, email, age, pwd)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (user_uuid, 0, name, name, email, 18, hashed_password),
            )
            user_id = payload.get("lastrowid")
            if not user_id:
                user_id = Authentification.get_user_id(name)

            execute_sql(
                "INSERT INTO Profils (XP, Level, Status, Stats, UserID) VALUES (0, 1, 'New', 0, ?)",
                (user_id,),
            )
            execute_sql("INSERT INTO Rank (UserID, Points) VALUES (?, 0)", (user_id,))
            execute_sql(
                "INSERT INTO Settings (MainVolume, VolumeMusic, VolumeSFX, Language, UserID) VALUES (100, 100, 100, 'FR', ?)",
                (user_id,),
            )
            return True
        except BDDAPIError as e:
            raise e

    @staticmethod
    def login(name, password):
        payload = execute_sql(
            "SELECT pwd FROM Users WHERE name = ? AND archive = 0 LIMIT 1",
            (name,),
        )
        rows = payload.get("rows", [])
        if rows:
            stored_password_base64 = rows[0]["pwd"]
            stored_password_bytes = base64.b64decode(stored_password_base64)
            return bcrypt.checkpw(password.encode("utf-8"), stored_password_bytes)
        return False

    @staticmethod
    def logout(token):
        global token_blacklist
        token_blacklist.add(token)
        return True

    @staticmethod
    def token_is_blacklisted(token):
        global token_blacklist
        return token in token_blacklist

    @staticmethod
    def get_connection():
        raise RuntimeError("Le back ne doit plus ouvrir SQLite directement. Utilise bdd_client.")

    @staticmethod
    def get_global_leaderboard(limit):
        payload = execute_sql(
            """
            SELECT u.name, p.Level, r.Points
            FROM Users u
            JOIN Profils p ON u.id = p.UserID
            JOIN Rank r ON u.id = r.UserID
            ORDER BY r.Points DESC LIMIT ?
            """,
            (limit,),
        )
        return [
            {"name": row["name"], "level": row["Level"], "points": row["Points"]}
            for row in payload.get("rows", [])
        ]

    @staticmethod
    def get_local_leaderboard(country, limit=100):
        payload = execute_sql(
            """
            SELECT u.name, r.Points
            FROM Users u
            JOIN Rank r ON u.id = r.UserID
            WHERE u.country = ?
            ORDER BY r.Points DESC LIMIT ?
            """,
            (country, limit),
        )
        return [{"name": row["name"], "points": row["Points"]} for row in payload.get("rows", [])]

    @staticmethod
    def add_points(name, points):
        user_id = Authentification.get_user_id(name)
        if not user_id:
            return False
        execute_sql("UPDATE Rank SET Points = Points + ? WHERE UserID = ?", (points, user_id))
        return True
