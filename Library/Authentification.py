
import base64
import bcrypt

from MultiBlindTest_Back.Library.bdd_client import BDDAPIError, get_json, post_json


token_blacklist = set()


class Authentification:
    @staticmethod
    def get_user_id(name=None, email=None):
        users = get_json('/mbt/users')
        if not isinstance(users, list):
            return None
        for user in users:
            if name and user.get('name') == name:
                return user.get('id') or user.get('ID')
            if email and user.get('email') == email:
                return user.get('id') or user.get('ID')
        return None

    @staticmethod
    def hash_password(password):
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return base64.b64encode(hashed).decode('utf-8')

    @staticmethod
    def register(name, email, password, nom=None, age=18):
        hashed_password = Authentification.hash_password(password)
        payload = post_json('/mbt/register', {
            'name': name,
            'nom': nom or name,
            'email': email,
            'age': age,
            'pwd': hashed_password,
        })
        user_id = Authentification.get_user_id(name=name, email=email)
        return {
            'success': True,
            'user_id': user_id,
            'uuid': payload.get('uuid')
        }

    @staticmethod
    def login(name, password):
        return post_json('/mbt/login', {
            'name': name,
            'password': password,
        })

    @staticmethod
    def logout(token):
        token_blacklist.add(token)
        return True

    @staticmethod
    def token_is_blacklisted(token):
        return token in token_blacklist

    @staticmethod
    def get_connection():
        raise RuntimeError('Le back ne doit plus ouvrir SQLite directement. Utilise bdd_client.')

    @staticmethod
    def get_global_leaderboard(limit):
        rows = get_json('/mbt/leaderboard')
        rows = rows if isinstance(rows, list) else []
        out = []
        for row in rows[:limit]:
            out.append({
                'name': row.get('name'),
                'level': 1,
                'points': row.get('points', 0),
            })
        return out

    @staticmethod
    def get_local_leaderboard(country, limit=100):
        return []

    @staticmethod
    def add_points(name, points):
        user_id = Authentification.get_user_id(name=name)
        if not user_id:
            return False
        post_json('/mbt/add/Rank', {'Userid': user_id, 'Points': int(points)})
        return True
