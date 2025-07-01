"""
Simple Memory System for Job Hacker Bot
A functional memory system that actually works without greenlet issues
"""

import json
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from sqlalchemy.exc import SQLAlchemyError

from app.models_db import ChatMessage, User, UserPreference, UserBehavior

logger = logging.getLogger(__name__)

@dataclass
class MemoryContext:
    """Simple memory context"""
    user_id: str
    conversation_history: List[Dict[str, Any]]
    user_preferences: Dict[str, Any]
    recent_behaviors: List[Dict[str, Any]]
    context_summary: str

class SimpleMemoryManager:
    """Simple, functional memory manager"""
    
    def __init__(self, db: AsyncSession, user: User):
        self.db = db
        self.user = user
        self.user_id = user.id
        logger.info(f"Simple memory manager initialized for user {self.user_id}")
    
    async def get_conversation_context(self, page_id: Optional[str] = None, limit: int = 10) -> MemoryContext:
        """Get conversation context with recent messages and user data"""
        try:
            # Get recent messages
            query = select(ChatMessage).where(ChatMessage.user_id == self.user_id)
            if page_id:
                query = query.where(ChatMessage.page_id == page_id)
            query = query.order_by(desc(ChatMessage.created_at)).limit(limit)
            
            result = await self.db.execute(query)
            messages = result.scalars().all()
            
            # Format messages
            conversation_history = []
            for msg in reversed(messages):  # Reverse to get chronological order
                try:
                    content = json.loads(msg.message) if isinstance(msg.message, str) else msg.message
                except (json.JSONDecodeError, TypeError):
                    content = str(msg.message)
                
                conversation_history.append({
                    "role": "user" if msg.is_user_message else "assistant",
                    "content": content,
                    "timestamp": msg.created_at.isoformat() if msg.created_at else datetime.utcnow().isoformat(),
                    "id": msg.id
                })
            
            # Get user preferences
            user_preferences = await self.get_user_preferences()
            
            # Get recent behaviors
            recent_behaviors = await self.get_recent_behaviors(limit=5)
            
            # Create simple context summary
            context_summary = self._create_context_summary(conversation_history, recent_behaviors)
            
            return MemoryContext(
                user_id=self.user_id,
                conversation_history=conversation_history,
                user_preferences=user_preferences,
                recent_behaviors=recent_behaviors,
                context_summary=context_summary
            )
            
        except Exception as e:
            logger.error(f"Error getting conversation context: {e}")
            return self._create_empty_context()
    
    async def get_user_preferences(self) -> Dict[str, Any]:
        """Get user preferences from database"""
        try:
            result = await self.db.execute(
                select(UserPreference).where(UserPreference.user_id == self.user_id)
            )
            preferences = result.scalars().all()
            
            prefs = {}
            for pref in preferences:
                try:
                    prefs[pref.preference_key] = json.loads(pref.preference_value)
                except (json.JSONDecodeError, TypeError):
                    prefs[pref.preference_key] = pref.preference_value
            
            return prefs
            
        except Exception as e:
            logger.error(f"Error getting user preferences: {e}")
            return {}
    
    async def get_recent_behaviors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent user behaviors"""
        try:
            result = await self.db.execute(
                select(UserBehavior)
                .where(UserBehavior.user_id == self.user_id)
                .order_by(desc(UserBehavior.created_at))
                .limit(limit)
            )
            behaviors = result.scalars().all()
            
            behavior_list = []
            for behavior in behaviors:
                behavior_list.append({
                    "action_type": behavior.action_type,
                    "context": behavior.context if isinstance(behavior.context, dict) else {},
                    "success": behavior.success,
                    "timestamp": behavior.created_at.isoformat() if behavior.created_at else datetime.utcnow().isoformat()
                })
            
            return behavior_list
            
        except Exception as e:
            logger.error(f"Error getting recent behaviors: {e}")
            return []
    
    async def save_user_behavior(self, action_type: str, context: Dict[str, Any], success: bool = True) -> bool:
        """Save user behavior to database"""
        try:
            behavior = UserBehavior(
                user_id=self.user_id,
                action_type=action_type,
                context=context,
                success=success,
                created_at=datetime.utcnow()
            )
            
            self.db.add(behavior)
            await self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error saving user behavior: {e}")
            try:
                await self.db.rollback()
            except:
                pass
            return False
    
    async def save_user_preference(self, key: str, value: Any) -> bool:
        """Save user preference to database"""
        try:
            # Check if preference exists
            result = await self.db.execute(
                select(UserPreference).where(
                    UserPreference.user_id == self.user_id,
                    UserPreference.preference_key == key
                )
            )
            existing = result.scalars().first()
            
            if existing:
                existing.preference_value = json.dumps(value) if not isinstance(value, str) else value
                existing.updated_at = datetime.utcnow()
            else:
                preference = UserPreference(
                    user_id=self.user_id,
                    preference_key=key,
                    preference_value=json.dumps(value) if not isinstance(value, str) else value,
                    updated_at=datetime.utcnow()
                )
                self.db.add(preference)
            
            await self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error saving user preference: {e}")
            try:
                await self.db.rollback()
            except:
                pass
            return False
    
    def _create_context_summary(self, conversation: List[Dict[str, Any]], behaviors: List[Dict[str, Any]]) -> str:
        """Create a simple context summary"""
        if not conversation and not behaviors:
            return "New user with no conversation history."
        
        msg_count = len(conversation)
        behavior_count = len(behaviors)
        
        summary = f"User has {msg_count} recent messages"
        
        if behaviors:
            action_types = [b.get("action_type", "unknown") for b in behaviors[:3]]
            summary += f" and recent actions: {', '.join(action_types)}"
        
        return summary
    
    def _create_empty_context(self) -> MemoryContext:
        """Create empty context as fallback"""
        return MemoryContext(
            user_id=self.user_id,
            conversation_history=[],
            user_preferences={},
            recent_behaviors=[],
            context_summary="New conversation started."
        )
    
    async def get_contextual_system_prompt(self) -> str:
        """Get enhanced system prompt with user context"""
        try:
            context = await self.get_conversation_context()
            
            base_prompt = (
                "You are Job Hacker Bot, an expert AI assistant specialized in job searching, "
                "career development, and professional advancement. You help users with job applications, "
                "resume building, cover letter writing, interview preparation, and career strategy."
            )
            
            # Add user context
            if context.context_summary:
                base_prompt += f"\n\nUser Context: {context.context_summary}"
            
            # Add preferences
            if context.user_preferences:
                prefs = []
                for key, value in context.user_preferences.items():
                    if isinstance(value, (str, int, float, bool)):
                        prefs.append(f"{key}: {value}")
                if prefs:
                    base_prompt += f"\n\nUser Preferences: {'; '.join(prefs[:3])}"
            
            # Add recent patterns
            if context.recent_behaviors:
                recent_actions = [b.get("action_type", "unknown") for b in context.recent_behaviors[:3]]
                if recent_actions:
                    base_prompt += f"\n\nRecent User Actions: {', '.join(recent_actions)}"
            
            return base_prompt
            
        except Exception as e:
            logger.error(f"Error generating contextual prompt: {e}")
            return (
                "You are Job Hacker Bot, an expert AI assistant specialized in job searching, "
                "career development, and professional advancement."
            ) 