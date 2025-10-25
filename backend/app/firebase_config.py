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
if cred_path and os.path.exists(cred_path):
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)
else:
    # For development - initialize without credentials (will use default credentials)
    firebase_admin.initialize_app()

# Initialize Firestore
db = firestore.client()
