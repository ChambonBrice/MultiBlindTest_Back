
import os
import re
import sys

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

load_dotenv()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from MultiBlindTest_Back.Flask.auth_utils import token_required
from MultiBlindTest_Back.Library.Authentification import Authentification
from MultiBlindTest_Back.Library.bdd_client import BDDAPIError, execute_sql
from MultiBlindTest_Back.Library.campagne import Campagne
from MultiBlindTest_Back.Library.leaderboard import leaderboard_bp
from MultiBlindTest_Back.Library.level import Level
from MultiBlindTest_Back.Library.level_creator import LevelCreatorService
from MultiBlindTest_Back.Library.mbt_api import MBTApiService
from MultiBlindTest_Back.Library.settings import SettingsService
from MultiBlindTest_Back.Library.subscription import SubscriptionService
from MultiBlindTest_Back.Library.token import generate_access_token, generate_refresh_token, verify_token
from MultiBlindTest_Back.Library.victory import Victory
from MultiBlindTest_Back.controllers.clips_controller import clips_bp
from MultiBlindTest_Back.controllers.rooms_controller import rooms_bp
from MultiBlindTest_Back.controllers.rounds_controller import rounds_bp
from MultiBlindTest_Back.controllers.tracks_controller import tracks_bp

app = Flask(__name__)
CORS(app)

app.register_blueprint(leaderboard_bp)
app.register_blueprint(tracks_bp)
app.register_blueprint(clips_bp)
app.register_blueprint(rooms_bp)
app.register_blueprint(rounds_bp)


def email_valide(email):
    pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
    return re.match(pattern, email) is not None


def json_or_empty():
    return request.get_json(silent=True) or {}


@app.route('/')
def home():
    return 'API Multi Blind Test opérationnelle 🚀'


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'service': 'backend'}), 200


@app.route('/login', methods=['POST'])
def service_login():
    data = json_or_empty()

    if data.get('name') and (data.get('password') or data.get('pwd')):
        return mbt_login()

    if not data:
        return jsonify({'error': 'Données JSON manquantes'}), 400

    user_id = data.get('user_id', 0)
    username = data.get('username') or data.get('service') or 'service'
    access_token = generate_access_token(user_id, username)
    refresh_token = generate_refresh_token(user_id, username)
    return jsonify({'access_token': access_token, 'refresh_token': refresh_token}), 200


@app.route('/refresh', methods=['POST'])
def refresh_token_route():
    data = json_or_empty()
    refresh_token = data.get('refresh_token')
    if not refresh_token:
        return jsonify({'error': 'refresh_token manquant'}), 400
    payload = verify_token(refresh_token, expected_type='refresh')
    if not payload:
        return jsonify({'error': 'refresh_token invalide ou expiré'}), 401
    access_token = generate_access_token(payload['user_id'], payload['username'])
    return jsonify({'access_token': access_token}), 200


@app.route('/register', methods=['POST'])
def register_alias():
    return mbt_register()


@app.route('/mbt/register', methods=['POST'])
def mbt_register():
    data = json_or_empty()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password') or data.get('pwd')
    nom = data.get('nom') or name
    age = int(data.get('age', 18))
    if not name or not email or not password:
        return jsonify({'error': 'Champs requis manquants'}), 400
    if not email_valide(email):
        return jsonify({'error': 'Email invalide'}), 400
    try:
        result = Authentification.register(name=name, email=email, password=password, nom=nom, age=age)
        return jsonify({'message': 'Utilisateur créé avec succès', 'user_id': result.get('user_id'), 'uuid': result.get('uuid')}), 201
    except Exception as e:
        msg = str(e).lower()
        if 'unique' in msg or 'déjà' in msg or 'already' in msg:
            return jsonify({'error': 'Username ou email déjà utilisé'}), 400
        print(e)
        return jsonify({'error': str(e)}), 502

@app.route('/mbt/login', methods=['POST', 'OPTIONS'])
@app.route('/login/user', methods=['POST', 'OPTIONS'])
def mbt_login():
    if request.method == 'OPTIONS':
        return '', 200

    data = json_or_empty()
    name = data.get('name')
    password = data.get('password') or data.get('pwd')

    if not name or not password:
        return jsonify({'error': 'name et password/pwd requis'}), 400

    try:
        remote_payload = Authentification.login(name, password)
        user = remote_payload.get('user', {})

        user_id = user.get('id') or user.get('ID')
        username = user.get('name') or name

        if not user_id:
            return jsonify({'error': 'Identifiants invalides'}), 401

        access_token = generate_access_token(user_id, username)
        refresh_token = generate_refresh_token(user_id, username)

        return jsonify({
            'message': 'Connexion réussie',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'id': user_id,
                'name': username,
                'email': user.get('email')
            },
        }), 200

    except BDDAPIError as e:
        msg = str(e).lower()
        if any(term in msg for term in ['invalid', 'incorrect', 'unauthorized', 'identifiants invalides', '401']):
            return jsonify({'error': 'Identifiants invalides'}), 401
        return jsonify({'error': str(e)}), 502

@app.route('/logout', methods=['POST'])
@token_required
def logout():
    auth_header = request.headers.get('Authorization')
    token = auth_header.split(' ')[1]
    Authentification.logout(token)
    return jsonify({'message': 'Déconnexion réussie'}), 200


@app.route('/mbt/table', methods=['GET'])
@token_required
def mbt_table():
    try:
        return jsonify(MBTApiService.get_table()), 200
    except BDDAPIError as e:
        return jsonify({'error': str(e)}), 502


@app.route('/mbt/users', methods=['GET'])
@token_required
def mbt_users():
    try:
        return jsonify(MBTApiService.get_users()), 200
    except BDDAPIError as e:
        return jsonify({'error': str(e)}), 502


@app.route('/mbt/users/<int:user_id>', methods=['DELETE'])
@token_required
def mbt_delete_user(user_id):
    try:
        return jsonify(MBTApiService.delete_user(user_id)), 200
    except BDDAPIError as e:
        return jsonify({'error': str(e)}), 502


@app.route('/mbt/add/<table>', methods=['POST'])
@token_required
def mbt_add_to_table(table):
    try:
        return jsonify(MBTApiService.add_to_table(table, json_or_empty())), 201
    except BDDAPIError as e:
        return jsonify({'error': str(e)}), 502


@app.route('/mbt/add_music', methods=['POST'])
@token_required
def mbt_add_music():
    try:
        return jsonify(MBTApiService.add_music(json_or_empty())), 201
    except BDDAPIError as e:
        return jsonify({'error': str(e)}), 502


@app.route('/mbt/music/<int:level_id>', methods=['GET'])
@token_required
def mbt_music(level_id):
    try:
        return jsonify(MBTApiService.get_music(level_id)), 200
    except BDDAPIError as e:
        return jsonify({'error': str(e)}), 502


@app.route('/mbt/levels', methods=['GET'])
@token_required
def mbt_get_levels():
    try:
        params = {
            'sort': request.args.get('sort'),
            'category': request.args.get('category'),
            'search': request.args.get('search'),
        }
        return jsonify(MBTApiService.get_levels(params)), 200
    except BDDAPIError as e:
        return jsonify({'error': str(e)}), 502


@app.route('/mbt/levels', methods=['POST'])
@token_required
def mbt_create_level():
    data = json_or_empty()
    required = ['public_id', 'title', 'creator_tag', 'difficulty_index', 'difficulty_label', 'rating', 'category', 'theme', 'tracks']
    missing = [field for field in required if field not in data]
    if missing:
        return jsonify({'error': f"Champs manquants : {', '.join(missing)}"}), 400
    data['creator_user_id'] = request.user_id
    try:
        return jsonify(MBTApiService.create_level(data)), 201
    except BDDAPIError as e:
        return jsonify({'error': str(e)}), 502


@app.route('/mbt/levels/<public_id>', methods=['GET'])
@token_required
def mbt_get_level(public_id):
    try:
        return jsonify(MBTApiService.get_level(public_id)), 200
    except BDDAPIError as e:
        return jsonify({'error': str(e)}), 502


@app.route('/mbt/levels/<public_id>/favorite', methods=['PATCH'])
@token_required
def mbt_favorite_level(public_id):
    try:
        return jsonify(MBTApiService.add_favorite(public_id)), 200
    except BDDAPIError as e:
        return jsonify({'error': str(e)}), 502


@app.route('/mbt/levels/<public_id>/play', methods=['PATCH'])
@token_required
def mbt_play_level(public_id):
    try:
        return jsonify(MBTApiService.add_play(public_id)), 200
    except BDDAPIError as e:
        return jsonify({'error': str(e)}), 502


@app.route('/mbt/leaderboard', methods=['GET'])
@token_required
def mbt_leaderboard():
    try:
        return jsonify(MBTApiService.get_leaderboard()), 200
    except BDDAPIError as e:
        return jsonify({'error': str(e)}), 502


# Alias compatibilité anciennes routes du back
@app.route('/settings', methods=['GET'])
@token_required
def get_settings():
    try:
        return jsonify(SettingsService.get_settings(request.user_id)), 200
    except BDDAPIError as e:
        return jsonify({'error': str(e)}), 502


@app.route('/settings', methods=['PUT', 'PATCH', 'OPTIONS'])
@token_required
def update_settings():
    if request.method == 'OPTIONS':
        return '', 200
    try:
        settings = SettingsService.update_settings(request.user_id, json_or_empty())
        return jsonify({'message': 'Paramètres mis à jour avec succès', 'settings': settings}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except BDDAPIError as e:
        return jsonify({'error': str(e)}), 502


@app.route('/levels', methods=['GET'])
@token_required
def get_levels_alias():
    return mbt_get_levels()


@app.route('/play/<int:level_id>', methods=['POST'])
@token_required
def play(level_id):
    data = json_or_empty()
    guess = data.get('guess')
    try:
        result = Level.check_guess(level_id, guess)
        return jsonify({'result': result}), 200
    except BDDAPIError as e:
        return jsonify({'error': str(e)}), 502


@app.route('/end_game', methods=['POST'])
@token_required
def end_game():
    data = json_or_empty()
    for field in ['nb_music', 'time_left', 'lives_remaining', 'campaign_id']:
        if field not in data or data[field] is None:
            return jsonify({'error': f'Champ manquant : {field}'}), 400
    try:
        result = Victory.calcul_score(
            user_id=request.user_id,
            nb_music=data.get('nb_music'),
            time_left=data.get('time_left'),
            lives_remaining=data.get('lives_remaining'),
            campaign_id=data.get('campaign_id'),
        )
        Victory.add_xp(request.user_id, 250)
        return jsonify(result), 200
    except BDDAPIError as e:
        return jsonify({'error': str(e)}), 502


@app.route('/profile', methods=['GET'])
@token_required
def get_profile():
    try:
        payload = execute_sql('SELECT id, uuid, name, nom, email, age FROM Users WHERE id = ? AND archive = 0', (request.user_id,))
        rows = payload.get('rows', [])
        if not rows:
            return jsonify({'error': 'Profil introuvable'}), 404
        return jsonify(rows[0]), 200
    except BDDAPIError as e:
        return jsonify({'error': str(e)}), 502


@app.route('/profile', methods=['PATCH'])
@token_required
def update_profile():
    data = json_or_empty()
    allowed_fields = {'name': 'name', 'nom': 'nom', 'email': 'email', 'age': 'age'}
    updates, values = [], []
    for key, db_field in allowed_fields.items():
        if key in data:
            if key == 'email' and not email_valide(data['email']):
                return jsonify({'error': 'Email invalide'}), 400
            updates.append(f'{db_field} = ?')
            values.append(data[key])
    if not updates:
        return jsonify({'error': 'Aucune donnée autorisée à mettre à jour'}), 400
    try:
        values.append(request.user_id)
        execute_sql(f"UPDATE Users SET {', '.join(updates)} WHERE id = ? AND archive = 0", tuple(values))
        return jsonify({'message': 'Profil mis à jour avec succès'}), 200
    except BDDAPIError as e:
        msg = str(e).lower()
        if 'unique' in msg or 'déjà' in msg:
            return jsonify({'error': 'Nom ou email déjà utilisé'}), 400
        return jsonify({'error': str(e)}), 502


@app.route('/subscription', methods=['GET'])
@token_required
def get_subscription():
    try:
        subscription = SubscriptionService.get_user_subscription(request.user_id)
        if not subscription:
            return jsonify({'has_subscription': False, 'plan': 'free', 'status': 'none'}), 200
        is_active = SubscriptionService.has_active_subscription(request.user_id)
        return jsonify({
            'has_subscription': is_active,
            'plan': subscription['plan'],
            'status': subscription['status'],
            'start_date': subscription['start_date'],
            'end_date': subscription['end_date'],
            'auto_renew': bool(subscription['auto_renew']),
            'provider': subscription['provider'],
        }), 200
    except BDDAPIError as e:
        return jsonify({'error': str(e)}), 502


@app.route('/levels/create', methods=['POST'])
@token_required
def create_level_alias():
    return mbt_create_level()


@app.route('/levels/<int:level_id>/tracks', methods=['POST'])
@token_required
def add_track(level_id):
    data = json_or_empty()
    payload = {
        'level_id': level_id,
        'name': data.get('name', f'Track {data.get("track_order", 1)}'),
        'path': data.get('media_url') or data.get('path'),
        'track_order': data.get('track_order', 1),
        'source_type': data.get('source_type', 'YOUTUBE'),
        'video_id': data.get('video_id'),
        'start_seconds': data.get('start_point', data.get('start_seconds', 0)),
        'duration_seconds': data.get('duration', data.get('duration_seconds', 15)),
    }
    if not payload['path']:
        return jsonify({'error': 'URL du média requise'}), 400
    try:
        MBTApiService.add_music(payload)
        return jsonify({'message': 'Track ajoutée'}), 201
    except BDDAPIError as e:
        return jsonify({'error': str(e)}), 502


@app.route('/levels/mine', methods=['GET'])
@token_required
def list_my_levels():
    try:
        rows = MBTApiService.get_levels({})
        mine = [row for row in rows if row.get('creator_user_id') == request.user_id or row.get('creator_tag') == getattr(request, 'username', None)]
        return jsonify(mine), 200
    except BDDAPIError as e:
        return jsonify({'error': str(e)}), 502


@app.route('/levels/<level_or_public_id>', methods=['GET'])
@token_required
def get_user_level(level_or_public_id):
    try:
        return jsonify(MBTApiService.get_level(level_or_public_id)), 200
    except BDDAPIError as e:
        return jsonify({'error': str(e)}), 502


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
