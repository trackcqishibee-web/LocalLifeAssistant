#!/usr/bin/env python3
"""
Firebase configuration and initialization
"""

import firebase_admin
from firebase_admin import credentials, firestore
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv('../.env') or load_dotenv('.env') or load_dotenv('/app/.env')

# Initialize Firebase Admin SDK
cred_path = os.getenv('FIREBASE_CREDENTIALS_PATH')
print(f"DEBUG: FIREBASE_CREDENTIALS_PATH = {cred_path}")
print(f"DEBUG: File exists = {os.path.exists(cred_path) if cred_path else False}")

try:
    if cred_path and os.path.exists(cred_path):
        print("DEBUG: Initializing Firebase with service account credentials")
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        print("DEBUG: Firebase initialized successfully with credentials")
    else:
        print("DEBUG: No credentials file found, trying default credentials")
        firebase_admin.initialize_app()
        print("DEBUG: Firebase initialized with default credentials")
    
    # Initialize Firestore
    db = firestore.client()
    print("DEBUG: Firestore client created successfully")
    
except Exception as e:
    print(f"DEBUG: Firebase initialization failed: {e}")
    print(f"DEBUG: Error type: {type(e)}")
    import traceback
    traceback.print_exc()
    db = None