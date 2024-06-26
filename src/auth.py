import firebase_admin
import os

class _Authentication():
    def __init__(self):
        self.firebase_app = None
    def verifyTokenByFirebaseAdmin(self):
        if self.firebase_app==None:
            print("initialize app by firebase admin")
            self.firebase_app = firebase_admin.initialize_app()

### singleton design patter, you should import Authentication object to use
Authentication = _Authentication()