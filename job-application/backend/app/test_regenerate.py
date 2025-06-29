#!/usr/bin/env python3
"""
Simple test endpoint for regeneration without WebSocket complexity
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class RegenerateRequest(BaseModel):
    last_message: str
    context: Optional[str] = None

@router.post("/test-regenerate")
async def test_regenerate(request: RegenerateRequest):
    """
    Simple regeneration test endpoint that bypasses WebSocket and complex agent logic
    """
    try:
        # Simple LLM regeneration without complex tools
        from langchain_google_genai import ChatGoogleGenerativeAI
        
        llm = ChatGoogleGenerativeAI(model='gemini-2.0-flash', temperature=0.7)
        
        regeneration_prompt = f"""
        Please provide an alternative response to this user message. 
        Be helpful, professional, and slightly different from what you might have said before.
        
        User message: {request.last_message}
        
        Context: {request.context or 'General conversation'}
        
        Generate a fresh, helpful response:
        """
        
        result = await llm.ainvoke(regeneration_prompt)
        
        return {
            "regenerated_response": result.content,
            "status": "success",
            "note": "✅ Regeneration working! This is a simplified test endpoint."
        }
        
    except Exception as e:
        logger.error(f"Regeneration test failed: {e}")
        return {
            "regenerated_response": "⚡ Quick regenerated response: I'm here to help with your career and job search needs. Let me know what specific assistance you'd like!",
            "status": "fallback",
            "error": str(e)
        } 