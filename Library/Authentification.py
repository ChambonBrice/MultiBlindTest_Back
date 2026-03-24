import sqlite3
import bcrypt
import os
import base64
import uuid

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
DB_PATH = os.path.join(BASE_DIR, "bdd")
DB_NAME = os.path.join(DB_PATH, "MBT.db")

token_blacklist = set()

class Authentification:

    @staticmethod
    def get_user_id(name):
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT id FROM Users WHERE name = ?", (name,))
        user = cur.fetchone()
        conn.close()
        if user:
            return user["id"]
        return None

    @staticmethod
    def hash_password(password):
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return base64.b64encode(hashed).decode('utf-8')

    @staticmethod
    def register(name, email, password):

        hashed_password = Authentification.hash_password(password)
        user_uuid = str(uuid.uuid4())

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                           INSERT INTO Users (uuid, archive, name, nom, email, age, pwd)
                           VALUES (?, ?, ?, ?, ?, ?, ?)
                           """, (user_uuid, 0, name, name, email, 18, hashed_password))

            user_id = cursor.lastrowid

            # 🔥 Ajout automatique des tables liées
            cursor.execute("INSERT INTO Profils (XP, Level, Status, Stats, UserID) VALUES (0,1,'New',0,?)", (user_id,))
            cursor.execute("INSERT INTO Rank (UserID, Points) VALUES (?, 0)", (user_id,))
            cursor.execute("INSERT INTO Settings (MainVolume, VolumeMusic, VolumeSFX, Language, UserID) VALUES (100,100,100,'FR',?)",(user_id,))

            conn.commit()
            return True

        except sqlite3.IntegrityError as e:
            print(e)
            return False

        finally:
            conn.close()

    @staticmethod
    def login(name, password):

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("""SELECT pwd FROM Users WHERE name = ?
            """,(name,))
        result = cursor.fetchone()

        conn.close()

        if result:
            stored_password_base64 = result[0]
            stored_password_bytes = base64.b64decode(stored_password_base64)
            if bcrypt.checkpw(password.encode('utf-8'), stored_password_bytes):
                return True

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
        return sqlite3.connect(DB_NAME)

    @staticmethod
    def get_global_leaderboard(limit):
        conn = Authentification.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
                       SELECT u.name, p.Level, r.Points
                       FROM Users u
                                JOIN Profils p ON u.id = p.UserID
                                JOIN Rank r ON u.id = r.UserID
                       ORDER BY r.Points DESC LIMIT ?
                       """, (limit,))

        rows = cursor.fetchall()
        conn.close()

        users = []
        for row in rows:
            users.append({
                "name": row["name"],
                "level": row["Level"],
                "points": row["Points"]
            })

        return users

    @staticmethod
    def get_local_leaderboard(country, limit=100):
        conn = Authentification.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
                       SELECT u.name, r.Points
                       FROM Users u
                                JOIN Rank r ON u.id = r.UserID
                       WHERE u.country = ?
                       ORDER BY r.Points DESC LIMIT ?
                       """, (country, limit))

        rows = cursor.fetchall()
        conn.close()
        return [{"name": row["name"], "points": row["Points"]} for row in rows]

    @staticmethod
    def add_points(name, points):
        conn = Authentification.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM Users WHERE name = ?", (name,))
        user = cursor.fetchone()
        if not user:
            conn.close()
            return False

        cursor.execute("UPDATE Rank SET Points = Points + ? WHERE UserID = ?", (points, user[0]))
        conn.commit()
        conn.close()
        return True