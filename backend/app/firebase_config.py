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
        print("DEBUG: Initializing Firebase with service account credentials file")
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        print("DEBUG: Firebase initialized successfully with credentials file")
    else:
        # Try environment variables
        project_id = os.getenv('FIREBASE_PROJECT_ID')
        private_key = os.getenv('FIREBASE_PRIVATE_KEY')
        client_email = os.getenv('FIREBASE_CLIENT_EMAIL')
        
        if project_id and private_key and client_email:
            print("DEBUG: Initializing Firebase with environment variables")
            # Create credentials from environment variables
            cred_dict = {
                "type": "service_account",
                "project_id": project_id,
                "private_key_id": os.getenv('FIREBASE_PRIVATE_KEY_ID', ''),
                "private_key": private_key.replace('\\n', '\n'),
                "client_email": client_email,
                "client_id": os.getenv('FIREBASE_CLIENT_ID', ''),
                "auth_uri": os.getenv('FIREBASE_AUTH_URI', 'https://accounts.google.com/o/oauth2/auth'),
                "token_uri": os.getenv('FIREBASE_TOKEN_URI', 'https://oauth2.googleapis.com/token'),
                "auth_provider_x509_cert_url": os.getenv('FIREBASE_AUTH_PROVIDER_X509_CERT_URL', 'https://www.googleapis.com/oauth2/v1/certs'),
                "client_x509_cert_url": os.getenv('FIREBASE_CLIENT_X509_CERT_URL', ''),
                "universe_domain": os.getenv('FIREBASE_UNIVERSE_DOMAIN', 'googleapis.com')
            }
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            print("DEBUG: Firebase initialized successfully with environment variables")
        else:
            print("DEBUG: No credentials file or environment variables found, trying default credentials")
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