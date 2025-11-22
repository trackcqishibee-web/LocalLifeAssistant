#!/usr/bin/env python3
"""
Firebase-based conversation storage
"""

import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from firebase_admin import firestore
from .firebase_config import db

logger = logging.getLogger(__name__)

class ConversationStorage:
    """Firebase-based conversation storage"""

    def __init__(self):
        self.db = db
        logger.info("Firebase ConversationStorage initialized")

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

        self.db.collection('users').document(user_id).collection('conversations').document(conversation_id).set(conversation)

        logger.info(f"Created conversation {conversation_id} for user {user_id}")
        return conversation_id

    def save_message(self, user_id: str, conversation_id: str, message_data: Dict[str, Any]):
        """Append a message to a conversation"""
        try:
            conv_ref = self.db.collection('users').document(user_id).collection('conversations').document(conversation_id)

            # Add message ID if not present
            if "message_id" not in message_data:
                # Get current conversation to count messages
                conv_doc = conv_ref.get()
                if conv_doc.exists:
                    current_messages = conv_doc.to_dict().get('messages', [])
                    message_data["message_id"] = f"msg_{len(current_messages) + 1}"
                else:
                    message_data["message_id"] = "msg_1"

            # Add message to array
            conv_ref.update({
                'messages': firestore.ArrayUnion([message_data]),
                'last_message_at': datetime.now().isoformat()
            })

            logger.info(f"Saved message to conversation {conversation_id}")

        except Exception as e:
            logger.error(f"Error saving message: {e}")
            raise

    def get_conversation(self, user_id: str, conversation_id: str) -> Dict[str, Any]:
        """Load a specific conversation"""
        try:
            conv_doc = self.db.collection('users').document(user_id).collection('conversations').document(conversation_id).get()

            if conv_doc.exists:
                return conv_doc.to_dict()
            else:
                raise FileNotFoundError(f"Conversation {conversation_id} not found")

        except Exception as e:
            logger.error(f"Error getting conversation: {e}")
            raise

    def list_user_conversations(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """List all conversations for a user (summary only)"""
        try:
            conversations = []
            conv_ref = self.db.collection('users').document(user_id).collection('conversations')
            
            # Check if the user document exists first
            user_doc = self.db.collection('users').document(user_id).get()
            if not user_doc.exists:
                # User doesn't exist yet, return empty list
                logger.info(f"User {user_id} does not exist in Firestore, returning empty conversations list")
                return []
            
            # Query conversations for this user
            conv_docs = conv_ref.order_by('last_message_at', direction=firestore.Query.DESCENDING) \
                .limit(limit).get()

            for doc in conv_docs:
                conv = doc.to_dict()
                if not conv:
                    continue
                messages = conv.get('messages', [])

                # Create summary
                conversations.append({
                    "conversation_id": conv.get("conversation_id", doc.id),
                    "created_at": conv.get("created_at", ""),
                    "last_message_at": conv.get("last_message_at", ""),
                    "message_count": len(messages),
                    "preview": messages[0]["content"][:100] if messages else ""
                })

            return conversations

        except Exception as e:
            logger.error(f"Error listing conversations for user {user_id}: {e}", exc_info=True)
            # Return empty list instead of raising - this handles new users gracefully
            return []

    def delete_conversation(self, user_id: str, conversation_id: str):
        """Delete a conversation"""
        try:
            self.db.collection('users').document(user_id).collection('conversations').document(conversation_id).delete()
            logger.info(f"Deleted conversation {conversation_id} for user {user_id}")
        except Exception as e:
            logger.error(f"Error deleting conversation: {e}")
            raise

    def update_metadata(self, user_id: str, conversation_id: str, metadata: Dict[str, Any]):
        """Update conversation metadata"""
        try:
            conv_ref = self.db.collection('users').document(user_id).collection('conversations').document(conversation_id)

            conv_ref.update({
                'metadata': metadata,
                'last_message_at': datetime.now().isoformat()
            })

            logger.info(f"Updated metadata for conversation {conversation_id}")

        except Exception as e:
            logger.error(f"Error updating metadata: {e}")
            raise

    def migrate_user_conversations(self, old_user_id: str, new_user_id: str) -> int:
        """Migrate all conversations from anonymous user to registered user"""
        try:
            count = 0
            conv_docs = self.db.collection('users').document(old_user_id).collection('conversations').get()

            for doc in conv_docs:
                conv_data = doc.to_dict()
                conv_data['user_id'] = new_user_id

                # Create in new user's collection
                new_conv_ref = self.db.collection('users').document(new_user_id).collection('conversations').document(doc.id)
                new_conv_ref.set(conv_data)

                # Delete from old collection
                doc.reference.delete()
                count += 1

            logger.info(f"Migrated {count} conversations from {old_user_id} to {new_user_id}")
            return count

        except Exception as e:
            logger.error(f"Error migrating conversations: {e}")
            return 0
