import jwt
import os
from datetime import datetime, timedelta
from src.gql import gql_query, gql_transactions
import src.config as config
import pytz

def generate_jwt_token(uid):
    gql_endpoint = os.environ['MESH_GQL_ENDPOINT']
    jwt_expire_hours = int(os.environ.get('JWT_EXPIRE_HOURS', config.JWT_EXPIRE_HOURS))
    gql_transactions_string = gql_transactions.format(FIREBASE_ID=uid)
    
    response, error_message = gql_query(gql_endpoint, gql_transactions_string)
    jwt_token = None
    if error_message:
        print("generate_jwt_token error: ", error_message)
        return jwt_token
    transactions = response['transactions']
    message = {
        "uid": uid,
        "iat": datetime.now(pytz.timezone('Asia/Taipei')),
        "exp": datetime.now(pytz.timezone('Asia/Taipei')) + timedelta(hours=jwt_expire_hours),
        "txs": transactions
    }
    jwt_token = jwt.encode(message, os.environ['JWT_SECRET'], algorithm='HS256')
    return jwt_token

def decoded_jwt_token(jwt_token):
    return jwt.decode(jwt_token, os.environ['JWT_SECRET'], algorithms=['HS256'])