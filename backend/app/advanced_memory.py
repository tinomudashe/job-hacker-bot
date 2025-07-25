"""
Advanced Memory System for Job Hacker Bot
Based on LangChain's Long-Term Memory Agent pattern
"""

import json
import logging
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass
from typing_extensions import TypedDict

from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.tools import tool
from langchain_core.runnables import RunnableConfig

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.models_db import User, UserBehavior, UserPreference

logger = logging.getLogger(__name__)

class KnowledgeTriple(TypedDict):
    """Structured knowledge representation"""
    subject: str
    predicate: str
    object_: str

@dataclass
class MemoryContext:
    """Enhanced memory context with semantic search"""
    user_id: str
    relevant_memories: List[str]
    knowledge_graph: List[Dict[str, str]]
    user_preferences: Dict[str, Any]
    context_summary: str

class AdvancedMemoryManager:
    """Advanced memory manager using vector store and knowledge graphs"""
    
    def __init__(self, user: User):
        self.user = user
        self.user_id = user.id
        
        # Initialize embeddings and vector store
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        self.memory_store = FAISS.from_texts(
            ["Initial memory store"], 
            self.embeddings,
            metadatas=[{"user_id": self.user_id, "type": "system"}]
        )
        
        logger.info(f"Advanced memory manager initialized for user {self.user_id}")
    
    async def save_memories(self, memories: List[KnowledgeTriple]) -> str:
        """Save structured memories to vector store"""
        try:
            documents = []
            for memory in memories:
                # Create searchable text from triple
                memory_text = f"{memory['subject']} {memory['predicate']} {memory['object_']}"
                
                document = Document(
                    page_content=memory_text,
                    metadata={
                        "user_id": self.user_id,
                        "subject": memory["subject"],
                        "predicate": memory["predicate"],
                        "object_": memory["object_"],
                        "timestamp": datetime.utcnow().isoformat(),
                        "memory_id": str(uuid.uuid4())
                    }
                )
                documents.append(document)
            
            # Add to vector store
            self.memory_store.add_documents(documents)
            
            logger.info(f"Saved {len(memories)} memories for user {self.user_id}")
            return f"Successfully saved {len(memories)} memories"
            
        except Exception as e:
            logger.error(f"Error saving memories: {e}")
            return f"Error saving memories: {str(e)}"
    
    async def search_memories(self, query: str, k: int = 5) -> List[str]:
        """Search for relevant memories using semantic similarity"""
        try:
            # --- BUG FIX ---
            # The `filter` parameter for in-memory FAISS is not reliably supported.
            # The robust solution is to fetch all results and then filter them manually.

            # 1. Get all similarity search results from the vector store first.
            all_results = self.memory_store.similarity_search(query, k=k)

            # 2. Manually filter the results to ensure they belong to the current user.
            # This is safer and avoids the internal bug in the FAISS filter implementation.
            results = [
                doc for doc in all_results 
                if isinstance(doc, Document) and doc.metadata.get("user_id") == self.user_id
            ]
            
            memories = []
            for result in results:
                # Format memory for readability
                metadata = result.metadata
                if all(key in metadata for key in ["subject", "predicate", "object_"]):
                    memory_text = f"{metadata['subject']} {metadata['predicate']} {metadata['object_']}"
                else:
                    memory_text = result.page_content
                memories.append(memory_text)
            
            logger.info(f"Found {len(memories)} relevant memories for query: {query}")
            return memories
            
        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            return []
    
    async def extract_knowledge_from_conversation(self, user_message: str, ai_response: str) -> List[KnowledgeTriple]:
        """Extract structured knowledge from conversation"""
        try:
            # Simple knowledge extraction (could be enhanced with LLM)
            knowledge = []
            
            # Extract user preferences
            user_name = self.user.first_name or "User"
            
            # Job-related preferences
            if any(term in user_message.lower() for term in ["remote", "work from home"]):
                knowledge.append({
                    "subject": user_name,
                    "predicate": "prefers",
                    "object_": "remote work"
                })
            
            if any(term in user_message.lower() for term in ["python", "javascript", "react", "node"]):
                for term in ["python", "javascript", "react", "node"]:
                    if term in user_message.lower():
                        knowledge.append({
                            "subject": user_name,
                            "predicate": "has skill in",
                            "object_": term
                        })
            
            # Location preferences
            if any(city in user_message.lower() for city in ["warsaw", "krakow", "gdansk", "london", "berlin"]):
                for city in ["warsaw", "krakow", "gdansk", "london", "berlin"]:
                    if city in user_message.lower():
                        knowledge.append({
                            "subject": user_name,
                            "predicate": "interested in location",
                            "object_": city.title()
                        })
            
            # Experience level
            if any(term in user_message.lower() for term in ["senior", "junior", "mid-level", "entry-level"]):
                for term in ["senior", "junior", "mid-level", "entry-level"]:
                    if term in user_message.lower():
                        knowledge.append({
                            "subject": user_name,
                            "predicate": "has experience level",
                            "object_": term
                        })
            
            # Industry preferences
            if any(term in user_message.lower() for term in ["fintech", "healthcare", "ai", "machine learning"]):
                for term in ["fintech", "healthcare", "ai", "machine learning"]:
                    if term in user_message.lower():
                        knowledge.append({
                            "subject": user_name,
                            "predicate": "interested in industry",
                            "object_": term
                        })
            
            return knowledge
            
        except Exception as e:
            logger.error(f"Error extracting knowledge: {e}")
            return []
    
    async def load_relevant_context(self, current_message: str) -> MemoryContext:
        """Load relevant memories for current conversation context"""
        try:
            # Search for relevant memories
            relevant_memories = await self.search_memories(current_message, k=5)
            
            # Get knowledge graph entries
            knowledge_graph = []
            try:
                all_memories = self.memory_store.similarity_search(
                    "",
                    k=20,
                    filter=lambda doc: doc.metadata.get("user_id") == self.user_id
                )
                
                for memory in all_memories:
                    metadata = memory.metadata
                    if all(key in metadata for key in ["subject", "predicate", "object_"]):
                        knowledge_graph.append({
                            "subject": metadata["subject"],
                            "predicate": metadata["predicate"],
                            "object_": metadata["object_"]
                        })
            except Exception:
                pass
            
            # Create context summary
            context_summary = self._create_context_summary(relevant_memories, knowledge_graph)
            
            return MemoryContext(
                user_id=self.user_id,
                relevant_memories=relevant_memories,
                knowledge_graph=knowledge_graph,
                user_preferences={},
                context_summary=context_summary
            )
            
        except Exception as e:
            logger.error(f"Error loading context: {e}")
            return self._create_empty_context()
    
    def _create_context_summary(self, memories: List[str], knowledge: List[Dict[str, str]]) -> str:
        """Create intelligent context summary"""
        if not memories and not knowledge:
            return "New user with no memory history."
        
        summary_parts = []
        
        if memories:
            summary_parts.append(f"Relevant memories: {len(memories)} items")
        
        if knowledge:
            # Analyze knowledge patterns
            subjects = set()
            predicates = set()
            objects = set()
            
            for item in knowledge:
                subjects.add(item.get("subject", ""))
                predicates.add(item.get("predicate", ""))
                objects.add(item.get("object_", ""))
            
            if predicates:
                summary_parts.append(f"Known relationships: {', '.join(list(predicates)[:3])}")
        
        return "; ".join(summary_parts)
    
    def _create_empty_context(self) -> MemoryContext:
        """Create empty context as fallback"""
        return MemoryContext(
            user_id=self.user_id,
            relevant_memories=[],
            knowledge_graph=[],
            user_preferences={},
            context_summary="New conversation started."
        )
    
    async def get_enhanced_system_prompt(self, current_message: str) -> str:
        """Get enhanced system prompt with memory context"""
        try:
            context = await self.load_relevant_context(current_message)
            
            base_prompt = (
                "You are Job Hacker Bot, an expert AI assistant specialized in job searching, "
                "career development, and professional advancement. You help users with job applications, "
                "resume building, cover letter writing, interview preparation, and career strategy."
            )
            
            # Add memory context
            if context.relevant_memories:
                memories_text = "\n".join([f"- {memory}" for memory in context.relevant_memories[:5]])
                base_prompt += f"\n\nRelevant memories about the user:\n{memories_text}"
            
            # Add knowledge graph context
            if context.knowledge_graph:
                knowledge_text = []
                for item in context.knowledge_graph[:5]:
                    knowledge_text.append(f"- {item['subject']} {item['predicate']} {item['object_']}")
                base_prompt += f"\n\nKnown facts about the user:\n" + "\n".join(knowledge_text)
            
            # Add context summary
            if context.context_summary:
                base_prompt += f"\n\nContext Summary: {context.context_summary}"
            
            return base_prompt
            
        except Exception as e:
            logger.error(f"Error generating enhanced prompt: {e}")
            return (
                "You are Job Hacker Bot, an expert AI assistant specialized in job searching, "
                "career development, and professional advancement."
            )

def create_memory_tools(memory_manager: AdvancedMemoryManager):
    """Create memory management tools for the agent"""
    
    @tool
    async def save_user_memory(memories: List[KnowledgeTriple]) -> str:
        """Save important facts about the user for future conversations.
        
        Use this tool to remember:
        - User preferences (remote work, location, salary expectations)
        - Skills and experience (programming languages, years of experience)
        - Career goals (target roles, industries, companies)
        - Personal information (education, certifications, achievements)
        
        Args:
            memories: List of knowledge triples (subject, predicate, object)
        """
        return await memory_manager.save_memories(memories)
    
    @tool
    async def recall_user_information(query: str) -> List[str]:
        """Search for relevant information about the user from previous conversations.
        
        Use this tool to:
        - Find user's skills and experience
        - Recall their job preferences
        - Look up their career goals
        - Access their background information
        
        Args:
            query: What you want to remember about the user
        """
        return await memory_manager.search_memories(query)
    
    return [save_user_memory, recall_user_information] 