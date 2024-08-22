import firebase_admin
from firebase_admin import auth

from src.gql import gql_query, gql_transactions
from src.tool import save_keyfile_from_url
from datetime import datetime, timedelta, timezone

import jwt
import os
import pytz
import src.config as config


def initFirebaseAdmin():
    '''
    Before we use Firebase SDK, we should intialize app.
    Note that firebase_admin itself is singleton, don't need to manage it by yourself.
    '''
    credential_url = os.environ['FIREBASE_CREDENTIALS']
    service_key_path = os.path.join('credential', 'keyfile.json')
    save_keyfile_from_url(credential_url, service_key_path)
    
    cred = firebase_admin.credentials.Certificate(service_key_path)
    firebase_app = firebase_admin.initialize_app(cred)
    print(f"Firebase project_id is {firebase_app.project_id}")

def verifyIdToken(id_token):
    uid, error_message = config.VERIFY_FAILED_ID, ""
    try:
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token.get('uid', config.VERIFY_FAILED_ID)
        print("verifyIdToken uid: ", uid)
    except Exception as e:
        print("verifyIdToken error: ", e)
        error_message = e
    return uid, error_message

def generate_jwt_token(uid):
    '''
    Generate jwt based on transactions that the user has.
    For the convenion of further checking, we use unix timestamp as claim.
    '''
    gql_endpoint = os.environ['MESH_GQL_ENDPOINT']
    jwt_expire_hours = int(os.environ.get('JWT_EXPIRE_HOURS', config.JWT_EXPIRE_HOURS))
    gql_transactions_string = gql_transactions.format(FIREBASE_ID=uid)
    
    response, error_message = gql_query(gql_endpoint, gql_transactions_string)
    jwt_token = None
    if error_message:
        print("generate_jwt_token error: ", error_message)
        return jwt_token
    transactions = response['transactions']
    ### format expireDate to unix timestamp
    for tx in transactions:
        expireDate = tx['expireDate']
        unix_expireDate = int(datetime.strptime(expireDate, '%Y-%m-%dT%H:%M:%S.%fZ').timestamp())
        tx['expireDate'] = unix_expireDate
    claim = {
        "uid": uid,
        "iat": int(datetime.now(tz=timezone.utc).timestamp()), # iat=issued at, claim identifies the time at which the JWT was issued
        "exp": int((datetime.now(tz=timezone.utc) + timedelta(hours=jwt_expire_hours)).timestamp()), # expiration time
        "txs": transactions
    }
    jwt_token = jwt.encode(claim, os.environ['JWT_SECRET'], algorithm='HS256')
    return jwt_token