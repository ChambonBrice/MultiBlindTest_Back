import jwt
import datetime

SECRET_KEY = "token_secret"

def generate_token(user_id, name):

    payload = {
        "user_id": user_id,
        "username": name,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2)
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

    return token

def verify_token(token):

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload

    except jwt.ExpiredSignatureError:
        return None

    except jwt.InvalidTokenError:
        return None