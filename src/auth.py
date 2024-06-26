import firebase_admin
import os

firebase_app = None

def verifyTokenByFirebaseAdmin():
    firebase_project_id = os.environ.get('FIREBASE_PROJECT_ID', '')
    if firebaseapp==None:
        print("initialize app by firebase admin")
        firebaseapp = firebase_admin.initialize_app({
            "projectId": firebase_project_id
        })
    return True
    