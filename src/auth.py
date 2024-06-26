import firebase_admin
from firebase_admin import auth
import os
from src.tool import save_keyfile_from_url

def initFirebaseAdmin():
    '''
    Before we use Firebase SDK, we should intialize app.
    Note that firebase_admin itself is singleton, don't need to manage it by yourself.
    '''
    credential_url = os.environ['GOOGLE_APPLICATION_CREDENTIALS']
    service_key_path = os.path.join('credential', 'keyfile.json')
    save_keyfile_from_url(credential_url, service_key_path)
    
    cred = firebase_admin.credentials.Certificate(service_key_path)
    firebase_app = firebase_admin.initialize_app(cred)
    print(f"Firebase project_id is {firebase_app.project_id}")

def verifyIdToken(id_token):
    verify_result, error_message = False, None
    try:
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token.get('uid', None)
        print("verifyIdToken decoded uid: ", uid)
        verify_result = True
    except Exception as e:
        print("verifyIdToken error: ", e)
        error_message = e
    return {
        "verify_result": verify_result,
        "error_message": error_message
    }