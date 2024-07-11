import jwt
import os
from datetime import datetime, timedelta
import pytz

def generate_jwt_token(uid):
    message = {
        "uid": uid,
        "iat": datetime.now(pytz.timezone('Asia/Taipei')),
        "exp": datetime.now(pytz.timezone('Asia/Taipei')) + timedelta(hours=3)
    }
    return jwt.encode(message, os.environ['JWT_SECRET'], algorithm='HS256')