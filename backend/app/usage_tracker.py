#!/usr/bin/env python3
"""
Usage tracking service for anonymous user trial limits
"""

import os
import json
import logging
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class UsageTracker:
    """Track anonymous user interactions and trial limits"""
    
    def __init__(self, base_dir="backend/user_usage"):
        self.base_dir = base_dir
        # Get trial limit from environment variable, default to 10
        self.trial_limit = int(os.getenv("TRIAL_LIMIT", "10"))
        os.makedirs(base_dir, exist_ok=True)
        logger.info(f"UsageTracker initialized with trial_limit={self.trial_limit}")
    
    def _get_usage_file(self, user_id: str) -> str:
        """Get the file path for a user's usage data"""
        return os.path.join(self.base_dir, f"{user_id}.json")
    
    def get_usage(self, user_id: str) -> Dict:
        """Get usage stats for a user"""
        usage_file = self._get_usage_file(user_id)
        
        if not os.path.exists(usage_file):
            return {
                "user_id": user_id,
                "interaction_count": 0,
                "trial_remaining": self.trial_limit,
                "is_registered": False,
                "first_interaction": datetime.now().isoformat(),
                "last_interaction": None
            }
        
        try:
            with open(usage_file, 'r') as f:
                data = json.load(f)
                # Ensure trial_remaining is calculated correctly
                data["trial_remaining"] = max(0, self.trial_limit - data.get("interaction_count", 0))
                return data
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error reading usage file for {user_id}: {e}")
            # Return default usage if file is corrupted
            return {
                "user_id": user_id,
                "interaction_count": 0,
                "trial_remaining": self.trial_limit,
                "is_registered": False,
                "first_interaction": datetime.now().isoformat(),
                "last_interaction": None
            }
    
    def increment_usage(self, user_id: str) -> Dict:
        """Increment interaction count and return updated usage"""
        usage = self.get_usage(user_id)
        usage["interaction_count"] += 1
        usage["trial_remaining"] = max(0, self.trial_limit - usage["interaction_count"])
        usage["last_interaction"] = datetime.now().isoformat()
        
        # Save updated usage
        usage_file = self._get_usage_file(user_id)
        try:
            with open(usage_file, 'w') as f:
                json.dump(usage, f, indent=2)
            logger.info(f"Updated usage for {user_id}: {usage['interaction_count']} interactions, {usage['trial_remaining']} remaining")
        except Exception as e:
            logger.error(f"Error saving usage file for {user_id}: {e}")
        
        return usage
    
    def check_trial_limit(self, user_id: str) -> bool:
        """Check if user has exceeded trial limit"""
        usage = self.get_usage(user_id)
        return usage["interaction_count"] >= self.trial_limit and not usage["is_registered"]
    
    def mark_registered(self, user_id: str, real_user_id: Optional[str] = None):
        """Mark user as registered"""
        usage = self.get_usage(user_id)
        usage["is_registered"] = True
        usage["registered_at"] = datetime.now().isoformat()
        if real_user_id:
            usage["real_user_id"] = real_user_id
        
        usage_file = self._get_usage_file(user_id)
        try:
            with open(usage_file, 'w') as f:
                json.dump(usage, f, indent=2)
            logger.info(f"Marked {user_id} as registered with real_user_id: {real_user_id}")
        except Exception as e:
            logger.error(f"Error marking user as registered: {e}")
    
    def get_trial_warning_threshold(self) -> int:
        """Get the threshold for showing trial warnings (e.g., 3 interactions remaining)"""
        return max(1, self.trial_limit // 3)  # Show warning when 1/3 of trial remains
