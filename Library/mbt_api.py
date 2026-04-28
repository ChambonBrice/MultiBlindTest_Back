
from urllib.parse import urlencode

from MultiBlindTest_Back.Library.bdd_client import get_json, post_json, patch_json, delete_json


class MBTApiService:
    @staticmethod
    def service_login():
        return post_json('/login', {})

    @staticmethod
    def service_refresh(refresh_token):
        return post_json('/refresh', {'refresh_token': refresh_token})

    @staticmethod
    def register_user(payload):
        return post_json('/mbt/register', payload)

    @staticmethod
    def login_user(payload):
        return post_json('/mbt/login', payload)

    @staticmethod
    def get_users():
        return get_json('/mbt/users')

    @staticmethod
    def delete_user(user_id):
        return delete_json(f'/mbt/users/{user_id}')

    @staticmethod
    def get_table():
        return get_json('/mbt/table')

    @staticmethod
    def add_to_table(table, payload):
        return post_json(f'/mbt/add/{table}', payload)

    @staticmethod
    def add_music(payload):
        return post_json('/mbt/add_music', payload)

    @staticmethod
    def get_music(level_id):
        return get_json(f'/mbt/music/{level_id}')

    @staticmethod
    def get_levels(params=None):
        path = '/mbt/levels'
        if params:
            clean = {k: v for k, v in params.items() if v not in (None, '', [])}
            if clean:
                path += '?' + urlencode(clean)
        return get_json(path)

    @staticmethod
    def create_level(payload):
        return post_json('/mbt/levels', payload)

    @staticmethod
    def get_level(public_id):
        return get_json(f'/mbt/levels/{public_id}')

    @staticmethod
    def add_favorite(public_id):
        return patch_json(f'/mbt/levels/{public_id}/favorite', {})

    @staticmethod
    def add_play(public_id):
        return patch_json(f'/mbt/levels/{public_id}/play', {})

    @staticmethod
    def get_leaderboard():
        return get_json('/mbt/leaderboard')
