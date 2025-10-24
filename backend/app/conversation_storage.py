#!/usr/bin/env python3
"""
File-based conversation storage organized by user folders
"""

import os
import json
import uuid
import logging
import shutil
from typing import Dict, Any, List, Optional
from datetime import datetime
from filelock import FileLock

logger = logging.getLogger(__name__)

class ConversationStorage:
    """File-based conversation storage organized by user folders"""
    
    def __init__(self, base_dir="backend/conversations"):
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)
        logger.info(f"ConversationStorage initialized at {base_dir}")
    
    def _get_user_dir(self, user_id: str) -> str:
        """Get or create user's conversation directory"""
        user_dir = os.path.join(self.base_dir, user_id)
        os.makedirs(user_dir, exist_ok=True)
        return user_dir
    
    def _get_conversation_file(self, user_id: str, conversation_id: str) -> str:
        """Get path to a conversation file"""
        user_dir = self._get_user_dir(user_id)
        return os.path.join(user_dir, f"{conversation_id}.json")
    
    def create_conversation(self, user_id: str, metadata: Dict[str, Any]) -> str:
        """Create a new conversation for a user"""
        conversation_id = str(uuid.uuid4())
        conversation = {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "last_message_at": datetime.now().isoformat(),
            "metadata": metadata,
            "messages": []
        }
        
        file_path = self._get_conversation_file(user_id, conversation_id)
        with open(file_path, 'w') as f:
            json.dump(conversation, f, indent=2)
        
        logger.info(f"Created conversation {conversation_id} for user {user_id}")
        return conversation_id
    
    def save_message(self, user_id: str, conversation_id: str, message_data: Dict[str, Any]):
        """Append a message to a conversation"""
        file_path = self._get_conversation_file(user_id, conversation_id)
        lock_path = file_path + ".lock"
        
        # Use file locking to prevent concurrent writes
        with FileLock(lock_path, timeout=10):
            try:
                with open(file_path, 'r') as f:
                    conversation = json.load(f)
                
                # Add message ID if not present
                if "message_id" not in message_data:
                    message_data["message_id"] = f"msg_{len(conversation['messages']) + 1}"
                
                conversation["messages"].append(message_data)
                conversation["last_message_at"] = datetime.now().isoformat()
                
                with open(file_path, 'w') as f:
                    json.dump(conversation, f, indent=2)
                
                logger.info(f"Saved message to conversation {conversation_id}")
            except FileNotFoundError:
                logger.error(f"Conversation {conversation_id} not found for user {user_id}")
                raise
    
    def get_conversation(self, user_id: str, conversation_id: str) -> Dict[str, Any]:
        """Load a specific conversation"""
        file_path = self._get_conversation_file(user_id, conversation_id)
        
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Conversation {conversation_id} not found for user {user_id}")
            raise
    
    def list_user_conversations(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """List all conversations for a user (summary only)"""
        user_dir = self._get_user_dir(user_id)
        
        if not os.path.exists(user_dir):
            return []
        
        conversations = []
        files = sorted(
            os.listdir(user_dir),
            key=lambda x: os.path.getmtime(os.path.join(user_dir, x)),
            reverse=True
        )[:limit]
        
        for filename in files:
            if filename.endswith('.json') and not filename.endswith('.lock'):
                file_path = os.path.join(user_dir, filename)
                try:
                    with open(file_path, 'r') as f:
                        conv = json.load(f)
                        # Return summary without full messages
                        conversations.append({
                            "conversation_id": conv["conversation_id"],
                            "created_at": conv["created_at"],
                            "last_message_at": conv["last_message_at"],
                            "message_count": len(conv["messages"]),
                            "preview": conv["messages"][0]["content"][:100] if conv["messages"] else ""
                        })
                except Exception as e:
                    logger.error(f"Error reading conversation {filename}: {e}")
        
        return conversations
    
    def delete_conversation(self, user_id: str, conversation_id: str):
        """Delete a conversation"""
        file_path = self._get_conversation_file(user_id, conversation_id)
        
        try:
            os.remove(file_path)
            logger.info(f"Deleted conversation {conversation_id} for user {user_id}")
        except FileNotFoundError:
            logger.error(f"Conversation {conversation_id} not found for user {user_id}")
            raise
    
    def update_metadata(self, user_id: str, conversation_id: str, metadata: Dict[str, Any]):
        """Update conversation metadata"""
        file_path = self._get_conversation_file(user_id, conversation_id)
        lock_path = file_path + ".lock"
        
        with FileLock(lock_path, timeout=10):
            try:
                with open(file_path, 'r') as f:
                    conversation = json.load(f)
                
                conversation["metadata"].update(metadata)
                conversation["last_message_at"] = datetime.now().isoformat()
                
                with open(file_path, 'w') as f:
                    json.dump(conversation, f, indent=2)
                
                logger.info(f"Updated metadata for conversation {conversation_id}")
            except FileNotFoundError:
                logger.error(f"Conversation {conversation_id} not found for user {user_id}")
                raise
    
    def migrate_user_conversations(self, old_user_id: str, new_user_id: str) -> int:
        """Migrate all conversations from anonymous user to registered user"""
        old_dir = os.path.join(self.base_dir, old_user_id)
        new_dir = self._get_user_dir(new_user_id)
        
        if not os.path.exists(old_dir):
            logger.warning(f"No conversations found for user {old_user_id}")
            return 0
        
        count = 0
        for filename in os.listdir(old_dir):
            if filename.endswith('.json') and not filename.endswith('.lock'):
                src = os.path.join(old_dir, filename)
                dst = os.path.join(new_dir, filename)
                
                # Update user_id in the conversation file
                try:
                    with open(src, 'r') as f:
                        conversation = json.load(f)
                    
                    conversation["user_id"] = new_user_id
                    
                    with open(dst, 'w') as f:
                        json.dump(conversation, f, indent=2)
                    
                    count += 1
                except Exception as e:
                    logger.error(f"Error migrating conversation {filename}: {e}")
        
        logger.info(f"Migrated {count} conversations from {old_user_id} to {new_user_id}")
        return count
