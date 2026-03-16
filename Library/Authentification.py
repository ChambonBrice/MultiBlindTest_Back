import sqlite3
import bcrypt
import os
import base64

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
DB_PATH = os.path.join(BASE_DIR, "bdd")
DB_NAME = os.path.join(DB_PATH, "MBT.db")

token_blacklist = set()

class Authentification:

    @staticmethod
    def hash_password(password):
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return base64.b64encode(hashed).decode('utf-8')

    @staticmethod
    def register(name, email, password):

        hashed_password = Authentification.hash_password(password)

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO Users (archive, pseudonyme, nom, email, age, pwd)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (0, name, name, email, 18, hashed_password))

            conn.commit()
            return True

        except sqlite3.IntegrityError:
            return False

        finally:
            conn.close()

    @staticmethod
    def login(name, password):

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("""SELECT pwd FROM Users WHERE pseudonyme = ?
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
        cursor = conn.cursor()

        cursor.execute("""
                       SELECT name, avatar, level, points, title
                       FROM users
                       ORDER BY points DESC LIMIT ?
                       """, (limit,))

        rows = cursor.fetchall()

        users = []
        for row in rows:
            users.append({
                "name": row[0],
                "avatar": row[1],
                "level": row[2],
                "points": row[3],
                "title": row[4]
            })

        conn.close()
        return users

    @staticmethod
    def get_local_leaderboard(country, limit):

        conn = Authentification.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
                       SELECT name, avatar, level, points, title
                       FROM users
                       WHERE country = ?
                       ORDER BY points DESC LIMIT ?
                       """, (country, limit))

        rows = cursor.fetchall()

        users = []
        for row in rows:
            users.append({
                "name": row[0],
                "avatar": row[1],
                "level": row[2],
                "points": row[3],
                "title": row[4]
            })

        conn.close()
        return users

    @staticmethod
    def add_points(name, points):

        conn = sqlite3.connect("DB_NAME")
        cursor = conn.cursor()

        cursor.execute("""
                       UPDATE users
                       SET points = points + ?
                       WHERE pseudonyme = ?
                       """, (points, name))

        conn.commit()
        conn.close()