
from functools import wraps
from flask import request, jsonify
from MultiBlindTest_Back.Library.Authentification import Authentification
from MultiBlindTest_Back.Library.token import verify_token


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return jsonify({"error": "Token manquant"}), 401

        try:
            token = auth_header.split(" ")[1]
        except IndexError:
            return jsonify({"error": "Token invalide"}), 401

        payload = verify_token(token, expected_type="access")

        if not payload:
            return jsonify({"error": "Token expiré ou invalide"}), 401

        if Authentification.token_is_blacklisted(token):
            return jsonify({"error": "Token révoqué"}), 401

        request.user_id = payload.get("user_id")
        request.username = payload.get("username")
        return f(*args, **kwargs)

    return decorated
