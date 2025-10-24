#!/usr/bin/env python3
"""
File-based user account management
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from filelock import FileLock

logger = logging.getLogger(__name__)

class UserManager:
    """File-based user account management"""
    
    def __init__(self, base_dir="backend/users"):
        self.base_dir = base_dir
        self.users_file = os.path.join(base_dir, "users.json")
        os.makedirs(base_dir, exist_ok=True)
        
        # Initialize users file if it doesn't exist
        if not os.path.exists(self.users_file):
            with open(self.users_file, 'w') as f:
                json.dump({}, f)
        
        logger.info(f"UserManager initialized at {base_dir}")
    
    def _load_users(self) -> Dict[str, Any]:
        """Load all users from file"""
        lock_path = self.users_file + ".lock"
        with FileLock(lock_path, timeout=10):
            with open(self.users_file, 'r') as f:
                return json.load(f)
    
    def _save_users(self, users: Dict[str, Any]):
        """Save users to file"""
        lock_path = self.users_file + ".lock"
        with FileLock(lock_path, timeout=10):
            with open(self.users_file, 'w') as f:
                json.dump(users, f, indent=2)
    
    def register_user(self, email: str, password: str, user_id: str, name: Optional[str] = None) -> Dict[str, Any]:
        """Register a new user"""
        users = self._load_users()
        
        # Check if email already exists
        if email in users:
            raise ValueError("Email already registered")
        
        # Store user (in production, hash password with bcrypt!)
        user_data = {
            "user_id": user_id,
            "email": email,
            "password": password,  # TODO: Hash this with bcrypt!
            "name": name,
            "created_at": datetime.now().isoformat(),
            "last_login": datetime.now().isoformat()
        }
        
        users[email] = user_data
        self._save_users(users)
        
        logger.info(f"Registered new user: {email}")
        return user_data
    
    def login_user(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate user login"""
        users = self._load_users()
        
        # Find user by email
        if email not in users:
            raise ValueError("Invalid email or password")
        
        user = users[email]
        
        # Verify password (in production, use bcrypt!)
        if user["password"] != password:
            raise ValueError("Invalid email or password")
        
        # Update last login
        user["last_login"] = datetime.now().isoformat()
        users[email] = user
        self._save_users(users)
        
        logger.info(f"User logged in: {email}")
        return user
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        users = self._load_users()
        return users.get(email)
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by user_id"""
        users = self._load_users()
        for email, user in users.items():
            if user["user_id"] == user_id:
                return user
        return None
    
    def user_exists(self, email: str) -> bool:
        """Check if user exists"""
        users = self._load_users()
        return email in users
