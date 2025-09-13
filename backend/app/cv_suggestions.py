import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from app.db import get_db
from app.dependencies import get_current_active_user
from app.models_db import User
from app.resume import ResumeData

logger = logging.getLogger(__name__)
router = APIRouter()

class CVSuggestion(BaseModel):
    id: str
    section: str  # "summary", "skills", "experience", "education"
    type: str  # "add", "enhance", "reorder", "highlight"
    title: str
    description: str
    target_text: str  # The text to highlight/underline
    suggested_text: str  # The improved text
    priority: str  # "high", "medium", "low"
    reasoning: str
    color: str  # "red", "blue", "green", "purple" for Grammarly-style colors

class CVSuggestionsRequest(BaseModel):
    job_title: str
    job_description: Optional[str] = ""
    target_keywords: Optional[List[str]] = []

class CVSuggestionsResponse(BaseModel):
    suggestions: List[CVSuggestion]
    total_suggestions: int
    high_priority_count: int

@router.post("/analyze-suggestions", response_model=CVSuggestionsResponse)
async def analyze_cv_suggestions(
    request: CVSuggestionsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Generate Grammarly-style suggestions for CV improvement based on job requirements."""
    
    try:
        # Get user's current resume data
        from sqlalchemy import select
        from app.models_db import Resume
        
        result = await db.execute(
            select(Resume).where(Resume.user_id == current_user.id)
        )
        resume_record = result.scalars().first()
        
        if not resume_record:
            raise HTTPException(status_code=404, detail="No resume found")
        
        resume_data = ResumeData(**resume_record.data)
        
        # Create AI prompt for generating suggestions
        suggestions_prompt = ChatPromptTemplate.from_template("""
You are an expert career coach analyzing a CV for improvement suggestions. Generate specific, actionable suggestions in Grammarly style.

CURRENT CV DATA:
{resume_data}

TARGET JOB:
Title: {job_title}
Description: {job_description}

If no specific job is provided, give general CV improvement suggestions for a stronger, more professional resume.

Analyze the CV and provide suggestions using this JSON schema:
{{
  "suggestions": [
    {{
      "id": "unique_id",
      "section": "summary|skills|experience|education|projects|certifications",
      "type": "add|enhance|reorder|highlight",
      "title": "Brief suggestion title",
      "description": "Detailed explanation",
      "target_text": "Exact text to highlight/underline",
      "suggested_text": "Improved version of the text",
      "priority": "high|medium|low",
      "reasoning": "Why this suggestion matters",
      "color": "red|blue|green|purple"
    }}
  ]
}}

COLOR CODING RULES:
- RED: Missing critical keywords/skills from job description
- BLUE: Clarity and structure improvements
- GREEN: Enhancement opportunities (add metrics, details, achievements)
- PURPLE: Section reordering and formatting suggestions

CRITICAL RULES - NEVER SUGGEST FAKE DATA:
1. NEVER suggest adding specific numbers, percentages, or metrics that aren't already in the CV
2. NEVER suggest fabricated achievements or false claims
3. Focus on wording improvements, keyword additions, and structure changes
4. Only suggest reordering existing content or improving existing descriptions

FOCUS ON EACH SECTION:
1. **Summary**: Missing keywords, weak descriptions, better positioning of experience
2. **Skills**: Reordering by relevance, adding missing job-related technologies
3. **Experience**: Stronger action verbs, clearer descriptions, better structure
4. **Education**: Relevant coursework, degree emphasis, academic achievements
5. **Projects**: Technology highlighting, better project descriptions
6. **Certifications**: Relevance to role, proper formatting

Provide 3-8 specific, factual suggestions across ALL sections that improve presentation without adding false information.
""")

        llm = ChatAnthropic(model="claude-3-7-sonnet-20250219", temperature=0.3)
        parser = JsonOutputParser()
        
        chain = suggestions_prompt | llm | parser
        
        # Generate suggestions
        response = await chain.ainvoke({
            "resume_data": resume_data.dict(),  # Use dict() instead of json()
            "job_title": request.job_title,
            "job_description": request.job_description or ""
        })
        
        # Parse and validate suggestions
        suggestions = []
        sections_found = {}
        
        for suggestion_data in response.get("suggestions", []):
            try:
                suggestion = CVSuggestion(**suggestion_data)
                suggestions.append(suggestion)
                
                # Track sections for debugging
                section = suggestion.section
                sections_found[section] = sections_found.get(section, 0) + 1
                
            except Exception as e:
                logger.warning(f"Invalid suggestion format: {e}")
                continue
        
        # Debug logging
        logger.info(f"Generated suggestions by section: {sections_found}")
        logger.info(f"Total suggestions: {len(suggestions)}")
        
        # Count priority levels
        high_priority_count = len([s for s in suggestions if s.priority == "high"])
        
        logger.info(f"Generated {len(suggestions)} CV suggestions for user {current_user.id}")
        
        return CVSuggestionsResponse(
            suggestions=suggestions,
            total_suggestions=len(suggestions),
            high_priority_count=high_priority_count
        )
        
    except Exception as e:
        logger.error(f"Error generating CV suggestions: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate suggestions")

@router.post("/apply-suggestion")
async def apply_cv_suggestion(
    suggestion_id: str,
    new_text: str,
    section: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Apply a specific suggestion to the user's CV."""
    
    try:
        from sqlalchemy import select
        from app.models_db import Resume
        
        # Get current resume
        result = await db.execute(
            select(Resume).where(Resume.user_id == current_user.id)
        )
        resume_record = result.scalars().first()
        
        if not resume_record:
            raise HTTPException(status_code=404, detail="No resume found")
        
        # Update the specific section with new text
        resume_data = resume_record.data.copy()
        
        # Apply the suggestion based on section
        if section == "summary" and "personalInfo" in resume_data:
            resume_data["personalInfo"]["summary"] = new_text
        elif section == "skills":
            # For skills, new_text should be a list
            try:
                import json
                skills_list = json.loads(new_text) if isinstance(new_text, str) else new_text
                resume_data["skills"] = skills_list
            except:
                resume_data["skills"] = new_text.split(", ") if isinstance(new_text, str) else []
        # Add more section handling as needed
        
        # Save updated resume
        resume_record.data = resume_data
        await db.commit()
        
        logger.info(f"Applied suggestion {suggestion_id} to {section} for user {current_user.id}")
        
        return {"success": True, "message": "Suggestion applied successfully"}
        
    except Exception as e:
        logger.error(f"Error applying CV suggestion: {e}")
        raise HTTPException(status_code=500, detail="Failed to apply suggestion")