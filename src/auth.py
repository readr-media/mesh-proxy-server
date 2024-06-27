import firebase_admin
from firebase_admin import auth
import os
from src.tool import save_keyfile_from_url
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
        print("verifyIdToken decoded_token: ", decoded_token)
        uid = decoded_token.get('uid', config.VERIFY_FAILED_ID)
    except Exception as e:
        error_message = e
    print(f"verifyIdToken uid: {uid}, error_message: {error_message}")
    return {
        "uid": uid,
        "verify_msg": error_message
    }