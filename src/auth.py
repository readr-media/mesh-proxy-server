import firebase_admin
import os

class _Authentication():
    def __init__(self):
        self.firebase_app = None
    def verifyTokenByFirebaseAdmin(self):
        firebase_project_id = os.environ.get('FIREBASE_PROJECT_ID', '')
        if self.firebase_app==None:
            print("initialize app by firebase admin")
            firebase_app = firebase_admin.initialize_app({
                "projectId": firebase_project_id
            })

### singleton design patter, you should import Authentication object to use
Authentication = _Authentication()