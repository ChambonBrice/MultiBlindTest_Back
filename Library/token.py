
from datetime import datetime, timedelta
import os
import jwt

SECRET_KEY = os.getenv("JWT_USER_SECRET", "change_me_user_secret")
ACCESS_EXPIRES_HOURS = int(os.getenv("JWT_ACCESS_EXPIRES_HOURS", "1"))
REFRESH_EXPIRES_DAYS = int(os.getenv("JWT_REFRESH_EXPIRES_DAYS", "7"))


def _build_token(user_id, username, token_type, expires_delta):
    payload = {
        "user_id": user_id,
        "username": username,
        "type": token_type,
        "exp": datetime.utcnow() + expires_delta,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def generate_access_token(user_id, username):
    return _build_token(user_id, username, "access", timedelta(hours=ACCESS_EXPIRES_HOURS))


def generate_refresh_token(user_id, username):
    return _build_token(user_id, username, "refresh", timedelta(days=REFRESH_EXPIRES_DAYS))


def generate_token(user_id, username):
    return generate_access_token(user_id, username)


def verify_token(token, expected_type=None):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        if expected_type and payload.get("type") != expected_type:
            return None
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
