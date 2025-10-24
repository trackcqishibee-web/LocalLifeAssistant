#!/usr/bin/env python3
"""
Firebase-based user account management
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
import firebase_admin
from firebase_admin import auth, firestore
from .firebase_config import db

logger = logging.getLogger(__name__)

class UserManager:
    """Firebase-based user account management"""

    def __init__(self):
        self.db = db
        logger.info("Firebase UserManager initialized")

    def register_user(self, email: str, password: str, user_id: str, name: Optional[str] = None) -> Dict[str, Any]:
        """Register a new user with Firebase Auth"""
        try:
            # Create user in Firebase Auth
            user_record = auth.create_user(
                email=email,
                password=password,
                display_name=name,
                uid=user_id
            )

            # Store additional user data in Firestore
            user_data = {
                "user_id": user_id,
                "email": email,
                "name": name,
                "created_at": datetime.now().isoformat(),
                "last_login": datetime.now().isoformat(),
                "auth_uid": user_record.uid
            }

            self.db.collection('users').document(user_id).set(user_data)

            logger.info(f"Registered new user: {email}")
            return user_data

        except auth.EmailAlreadyExistsError:
            raise ValueError("Email already registered")
        except Exception as e:
            logger.error(f"Error registering user: {e}")
            raise

    def login_user(self, email: str, password: str) -> Dict[str, Any]:
        """
        This method is deprecated for Firebase Auth.
        Use verify_token() for authentication instead.
        Firebase Auth should be handled client-side.
        """
        raise NotImplementedError("Use Firebase Auth client-side and verify_token() server-side")

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        try:
            user_record = auth.get_user_by_email(email)
            user_doc = self.db.collection('users').where('auth_uid', '==', user_record.uid).limit(1).get()

            if user_doc:
                return user_doc[0].to_dict()
            return None
        except:
            return None

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by user_id"""
        try:
            user_doc = self.db.collection('users').document(user_id).get()
            if user_doc.exists:
                return user_doc.to_dict()
            return None
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            return None

    def user_exists(self, email: str) -> bool:
        """Check if user exists"""
        return self.get_user_by_email(email) is not None

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify Firebase Auth token"""
        try:
            decoded_token = auth.verify_id_token(token)
            user_id = decoded_token['uid']
            return self.get_user_by_id(user_id)
        except Exception as e:
            logger.error(f"Error verifying token: {e}")
            return None

    def create_custom_token(self, user_id: str) -> str:
        """Create a custom token for client-side authentication"""
        try:
            custom_token = auth.create_custom_token(user_id)
            return custom_token.decode('utf-8')
        except Exception as e:
            logger.error(f"Error creating custom token: {e}")
            raise

    def authenticate_with_token(self, token: str) -> Dict[str, Any]:
        """Authenticate user with Firebase Auth token and update last login"""
        try:
            decoded_token = auth.verify_id_token(token)
            user_id = decoded_token['uid']

            # Get user data
            user_data = self.get_user_by_id(user_id)
            if not user_data:
                # User doesn't exist, create them automatically
                logger.info(f"User {user_id} not found, creating automatically")
                user_data = {
                    "user_id": user_id,
                    "email": decoded_token.get('email', ''),
                    "name": decoded_token.get('name', ''),
                    "created_at": datetime.now().isoformat(),
                    "last_login": datetime.now().isoformat(),
                    "is_registered": True
                }
                self.db.collection('users').document(user_id).set(user_data)
                logger.info(f"User {user_id} created automatically via token authentication")
            else:
                # Update last login for existing user
                user_data["last_login"] = datetime.now().isoformat()
                self.db.collection('users').document(user_id).update({
                    'last_login': user_data["last_login"]
                })

            logger.info(f"User authenticated via token: {user_id}")
            return user_data

        except Exception as e:
            logger.error(f"Error authenticating with token: {e}")
            raise ValueError("Invalid authentication token")
