import jwt
import os
from datetime import datetime, timedelta
from src.gql import gql_query, gql_transactions
import src.config as config
import pytz

def generate_jwt_token(uid):
    '''
    Generate jwt based on transactions that the user has.
    For the convenion of further checking, we use unix timestamp as claim.
    '''
    gql_endpoint = os.environ['MESH_GQL_ENDPOINT']
    jwt_expire_hours = int(os.environ.get('JWT_EXPIRE_HOURS', config.JWT_EXPIRE_HOURS))
    gql_transactions_string = gql_transactions.format(FIREBASE_ID=uid)
    
    response, error_message = gql_query(gql_endpoint, gql_transactions_string)
    signature = None
    if error_message:
        print("generate_jwt_token error: ", error_message)
        return signature
    transactions = response['transactions']
    ### format expireDate to unix timestamp
    for tx in transactions:
        expireDate = tx['expireDate']
        unix_expireDate = int(datetime.strptime(expireDate, '%Y-%m-%dT%H:%M:%S.%fZ').timestamp())
        tx['expireDate'] = unix_expireDate
    claim = {
        "uid": uid,
        "iat": int(datetime.now(pytz.timezone('Asia/Taipei')).timestamp()), # iat=issued at, claim identifies the time at which the JWT was issued
        "exp": int((datetime.now(pytz.timezone('Asia/Taipei')) + timedelta(hours=jwt_expire_hours)).timestamp()), # expiration time
        "txs": transactions
    }
    signature = jwt.encode(claim, os.environ['JWT_SECRET'], algorithm='HS256')
    jwt_token = {
        "claim": claim, # claim is the place to put messages
        "signature": signature # signature is the claim after signing by JWT_SECRET
    }
    return jwt_token

def verify_jwt_token(jwt_token):
    '''
    Verify whether sign(claim) equals to signature. If with some error, we'll return error_code, error_msg.
    '''
    ### check existence of claim and signature
    claim = jwt_token.get('claim', None)
    signature = jwt_token.get('signature', None)
    if not claim or not signature:
        # TODO: In this case, we should send logging information because this might be an attack.
        return False
    
    ### check validity of claim
    signed_claim = jwt.encode(claim, os.environ['JWT_SECRET'], algorithm='HS256')
    if signed_claim != signature:
        # TODO: In this case, we should send logging information because this might be an attack.
        return False
    
    ### check ticket expiration
    expireDate = claim.get('exp', 0)
    current_unixtime = int(datetime.now(pytz.timezone('Asia/Taipei')).timestamp())
    if expireDate < current_unixtime:
        return False
    return True
    