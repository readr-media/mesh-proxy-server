import firebase_admin
import os

firebase_app = None

def verifyTokenByFirebaseAdmin():
    firebase_project_id = os.environ.get('FIREBASE_PROJECT_ID', '')
    if firebase_app==None:
        print("initialize app by firebase admin")
        firebase_app = firebase_admin.initialize_app({
            "projectId": firebase_project_id
        })
    return True
    