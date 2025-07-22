"""
Enhanced Memory and Learning System for Job Hacker Bot - Fixed Async Version
Implements conversation summarization, user behavior learning, and persistent context management
"""

import json
import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from pathlib import Path
import asyncio

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.schema import Document

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError

from app.models_db import ChatMessage, User, UserPreference, UserBehavior
from app.db import async_session_maker

logger = logging.getLogger(__name__)

@dataclass
class ConversationContext:
    """Structured conversation context with metadata"""
    summary: str
    key_topics: List[str]
    user_preferences: Dict[str, Any]
    recent_messages: List[Dict[str, Any]]
    conversation_length: int
    last_updated: datetime

@dataclass
class UserLearningProfile:
    """User learning profile with preferences and behaviors"""
    user_id: str
    preferences: Dict[str, Any]
    interaction_patterns: Dict[str, Any]
    skill_interests: List[str]
    job_search_patterns: Dict[str, Any]
    feedback_history: List[Dict[str, Any]]
    success_metrics: Dict[str, int]

class EnhancedMemoryManager:
    """
    Enhanced memory manager with conversation summarization and user learning.
    This version is refactored to be fully asynchronous and avoid concurrency issues.
    """
    
    def __init__(self, db: AsyncSession, user: User):
        self.db = db
        self.user = user
        self.user_id = user.id
        
        # FIX: Re-enable the LLM and embeddings for advanced memory functions.
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.1)
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        
        # Memory configuration
        self.max_context_messages = 20
        self.summary_trigger_length = 15  # Increased trigger length for summarization
        self.max_summary_length = 500
        
        # In-memory cache for the user's learning profile for the duration of the session.
        self.user_profile_cache = None

    async def get_conversation_context(
        self, 
        page_id: Optional[str] = None,
        include_user_learning: bool = True
    ) -> ConversationContext:
        """
        Retrieves, processes, and summarizes conversation history to provide
        rich context for the agent.
        """
        try:
            # 1. Fetch all messages for the given page from the database
            query = select(ChatMessage).where(
                ChatMessage.user_id == self.user_id,
                ChatMessage.page_id == page_id
            ).order_by(ChatMessage.created_at)
            
            result = await self.db.execute(query)
            messages = result.scalars().all()
            
            # 2. Process the messages to create a conversation context
            context = await self._process_conversation_messages(messages)
            
            # 3. (Optional) Enhance context with user's learned profile
            if include_user_learning:
                user_profile = await self.get_user_learning_profile()
                if user_profile:
                    context.user_preferences.update(user_profile.preferences)
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting conversation context for page {page_id}: {e}")
            return self._create_empty_context()

    async def _process_conversation_messages(
        self, 
        messages: List[ChatMessage]
    ) -> ConversationContext:
        """
        Processes a list of ChatMessage objects to generate a summary and extract
        key topics and recent messages.
        """
        conversation_length = len(messages)
        
        # Format recent messages for the agent's short-term memory
        recent_messages = []
        for msg in messages[-self.max_context_messages:]:
            try:
                content = json.loads(msg.message)
            except (json.JSONDecodeError, TypeError):
                content = str(msg.message)
            
            recent_messages.append({
                "role": "user" if msg.is_user_message else "assistant",
                "content": content,
                "timestamp": msg.created_at.isoformat(),
                "id": msg.id
            })
        
        # Generate a summary if the conversation is long enough
        summary = ""
        key_topics = []
        if conversation_length > self.summary_trigger_length:
            try:
                # Summarize older messages, leaving recent ones for immediate context
                older_messages = messages[:-self.max_context_messages]
                if older_messages:
                    summary = await self._generate_conversation_summary(older_messages)
                    key_topics = await self._extract_key_topics(messages)
            except Exception as e:
                logger.warning(f"Could not generate conversation summary: {e}")
                summary = f"A long conversation with {conversation_length} messages."
        
        return ConversationContext(
            summary=summary,
            key_topics=key_topics,
            user_preferences={},
            recent_messages=recent_messages,
            conversation_length=conversation_length,
            last_updated=datetime.utcnow()
        )

    async def _generate_conversation_summary(self, messages: List[ChatMessage]) -> str:
        """
        Uses an LLM to generate a concise summary of a list of messages.
        """
        if not messages:
            return ""

        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="You are an expert at summarizing conversations. Create a concise summary of the following chat history."),
            HumanMessage(content="\n".join([f"{'User' if msg.is_user_message else 'Assistant'}: {msg.message}" for msg in messages]))
        ])
        chain = prompt | self.llm
        
        summary_result = await chain.ainvoke({})
        return summary_result.content[:self.max_summary_length]

    async def _extract_key_topics(self, messages: List[ChatMessage]) -> List[str]:
        """
        Uses an LLM to extract key topics from a conversation.
        """
        conversation_text = " ".join([msg.message for msg in messages[-10:]])
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="Extract the 5 most important keywords or topics from this conversation. Respond with a comma-separated list."),
            HumanMessage(content=conversation_text)
        ])
        chain = prompt | self.llm
        
        topics_result = await chain.ainvoke({})
        return [topic.strip() for topic in topics_result.content.split(",")]

    async def get_user_learning_profile(self) -> Optional[UserLearningProfile]:
        """
        Builds a profile of the user based on their preferences and past behaviors
        stored in the database.
        """
        if self.user_profile_cache:
            return self.user_profile_cache
        
        try:
            # Fetch preferences and behaviors in parallel
            prefs_task = self.db.execute(select(UserPreference).where(UserPreference.user_id == self.user_id))
            behaviors_task = self.db.execute(
                select(UserBehavior)
                .where(UserBehavior.user_id == self.user_id)
                .order_by(desc(UserBehavior.created_at))
                .limit(100)
            )
            prefs_result, behaviors_result = await asyncio.gather(prefs_task, behaviors_task)
            
            preferences = {p.preference_key: json.loads(p.preference_value) for p in prefs_result.scalars().all()}
            behaviors = behaviors_result.scalars().all()
            
            profile = UserLearningProfile(
                user_id=self.user_id,
                preferences=preferences,
                interaction_patterns=self._analyze_interaction_patterns(behaviors),
                skill_interests=self._extract_skill_interests(behaviors),
                job_search_patterns=self._extract_job_search_patterns(behaviors),
                feedback_history=[],  # Placeholder for future implementation
                success_metrics={}    # Placeholder for future implementation
            )
            
            self.user_profile_cache = profile
            return profile
            
        except Exception as e:
            logger.error(f"Error building user learning profile: {e}")
            return None

    def _analyze_interaction_patterns(self, behaviors: List[UserBehavior]) -> Dict[str, Any]:
        """Analyze interaction patterns safely"""
        
        patterns = {
            "most_common_actions": {},
            "peak_activity_hours": [],
            "preferred_communication_style": "professional",
            "total_actions": len(behaviors)
        }
        
        try:
            # Count action frequencies
            action_counts = {}
            hours = []
            
            for behavior in behaviors:
                try:
                    action = behavior.action_type
                    action_counts[action] = action_counts.get(action, 0) + 1
                    
                    if behavior.created_at:
                        hours.append(behavior.created_at.hour)
                except Exception:
                    continue
            
            # Sort by frequency
            patterns["most_common_actions"] = dict(
                sorted(action_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            )
            
            # Analyze timing patterns
            if hours:
                hour_counts = {}
                for hour in hours:
                    hour_counts[hour] = hour_counts.get(hour, 0) + 1
                
                peak_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)[:2]
                patterns["peak_activity_hours"] = [hour for hour, count in peak_hours]
            
        except Exception as e:
            logger.error(f"Error analyzing interaction patterns: {e}")
        
        return patterns

    def _extract_skill_interests(self, behaviors: List[UserBehavior]) -> List[str]:
        """Extract skill interests from user behaviors."""
        interests = set()
        for behavior in behaviors:
            if behavior.action_type == "skill_search":
                try:
                    context = json.loads(behavior.context)
                    if "skills" in context:
                        interests.update(context["skills"])
                except (json.JSONDecodeError, TypeError):
                    pass
        return list(interests)

    def _extract_job_search_patterns(self, behaviors: List[UserBehavior]) -> Dict[str, Any]:
        """Extract job search patterns from user behaviors."""
        patterns = {}
        for behavior in behaviors:
            if behavior.action_type == "job_search":
                try:
                    context = json.loads(behavior.context)
                    if "keywords" in context:
                        patterns["keywords"] = context["keywords"]
                    if "location" in context:
                        patterns["location"] = context["location"]
                    if "remote" in context:
                        patterns["remote"] = context["remote"]
                except (json.JSONDecodeError, TypeError):
                    pass
        return patterns

    async def save_user_behavior(
        self,
        action_type: str,
        context: Dict[str, Any],
        success: bool = True
    ):
        """
        Saves a user's action and its context to the database for later analysis.
        """
        try:
            behavior = UserBehavior(
                user_id=self.user_id,
                action_type=action_type,
                context=context,
                success=success
            )
            self.db.add(behavior)
            await self.db.commit()
        except Exception as e:
            logger.warning(f"Could not save user behavior: {e}")
            await self.db.rollback()

    async def save_user_preference(
        self,
        preference_key: str,
        preference_value: Any,
    ):
        """
        Saves or updates a user's preference in the database.
        """
        try:
            preference = UserPreference(
                user_id=self.user_id,
                preference_key=preference_key,
                preference_value=json.dumps(preference_value, default=str),
            )
            await self.db.merge(preference)
            await self.db.commit()
        except Exception as e:
            logger.warning(f"Could not save user preference: {e}")
            await self.db.rollback()

    async def get_contextual_system_prompt(self) -> str:
        """Get contextual system prompt with safe async operations"""
        
        try:
            context = await self.get_conversation_context(include_user_learning=False)
            
            base_prompt = (
                "You are Job Hacker Bot, an expert AI assistant specialized in job searching, "
                "career development, and professional advancement. You help users with job applications, "
                "resume building, cover letter writing, interview preparation, and career strategy."
            )
            
            # Add conversation context if available
            if context.summary:
                base_prompt += f"\n\nConversation Summary: {context.summary}"
            
            if context.key_topics:
                topics_str = ", ".join(context.key_topics[:5])
                base_prompt += f"\n\nKey Discussion Topics: {topics_str}"
            
            # Add user preferences if available
            if context.user_preferences:
                prefs = []
                for key, value in context.user_preferences.items():
                    if isinstance(value, (str, int, float)):
                        prefs.append(f"{key}: {value}")
                if prefs:
                    base_prompt += f"\n\nUser Preferences: {'; '.join(prefs[:3])}"
            
            return base_prompt
            
        except Exception as e:
            logger.error(f"Error generating contextual prompt: {e}")
            return (
                "You are Job Hacker Bot, an expert AI assistant specialized in job searching, "
                "career development, and professional advancement."
            )

    def _create_empty_context(self) -> ConversationContext:
        """Creates a default, empty context object."""
        return ConversationContext(
            summary="New conversation started.",
            key_topics=[],
            user_preferences={},
            recent_messages=[],
            conversation_length=0,
            last_updated=datetime.utcnow()
        ) 