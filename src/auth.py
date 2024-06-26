import firebase_admin
from firebase_admin import auth

def initFirebaseAdmin():
    '''
    Before we use Firebase SDK, we should intialize app.
    Note that firebase_admin itself is singleton, don't need to manage it by yourself.
    '''
    firebase_app = firebase_admin.initialize_app()
    print(f"Firebase project_id is {firebase_app.project_id}")

def verifyIdToken(id_token):
    decoded_token = auth.verify_id_token(id_token)
    uid = decoded_token.get('uid', None)
    print("verifyIdToken decoded uid: ", uid)
    return uid