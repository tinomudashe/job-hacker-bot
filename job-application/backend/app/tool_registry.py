# 🛠️ Tool Registry - Central Tool Management
# This file helps organize the 25+ tools currently in orchestrator.py

from typing import List
from langchain.tools import Tool

# Import existing specialized modules
from app.job_search import search_jobs
from app.resume_generator import generate_resume
from app.cv_generator import generate_cv
from app.cover_letter_generator import generate_cover_letter
from app.pdf_generator import generate_pdf
from app.documents import get_document_insights, analyze_document
from app.enhanced_memory import get_memory_context

class ToolRegistry:
    """
    Central registry for all agent tools.
    
    USAGE:
    - Move tools FROM orchestrator.py TO appropriate modules
    - Import tools here and register them
    - Orchestrator imports ONLY this registry
    
    BENEFITS:
    - Cleaner orchestrator (only WebSocket + agent setup)
    - Organized tools by category
    - Easier maintenance and testing
    - Better separation of concerns
    """
    
    def __init__(self):
        self.tools = []
        self._register_all_tools()
    
    def _register_all_tools(self):
        """Register all tools from specialized modules"""
        
        # Job Search Tools (move from orchestrator)
        # TODO: Move these from orchestrator.py to app/job_search.py
        # - search_jobs_tool
        # - search_jobs_with_browser
        
        # Resume/CV Tools (move from orchestrator) 
        # TODO: Move these from orchestrator.py to app/resume_tools.py
        # - generate_tailored_resume
        # - enhance_resume_section  
        # - create_resume_from_scratch
        # - refine_cv_for_role
        # - get_cv_best_practices
        # - analyze_skills_gap
        # - get_ats_optimization_tips
        
        # Document Tools (move from orchestrator)
        # TODO: Move these from orchestrator.py to app/document_tools.py
        # - enhanced_document_search
        # - analyze_specific_document
        # - get_document_insights
        # - list_documents
        # - read_document
        
        # Career Tools (move from orchestrator)
        # TODO: Move these from orchestrator.py to app/career_tools.py
        # - get_interview_preparation_guide
        # - get_salary_negotiation_advice
        # - create_career_development_plan
        
        # Cover Letter Tools (move from orchestrator)
        # TODO: Move these from orchestrator.py to app/cover_letter_tools.py
        # - generate_cover_letter_from_url
        # - generate_cover_letter
        
        # PDF/Download Tools (move from orchestrator) 
        # TODO: Move these from orchestrator.py to app/pdf_tools.py
        # - generate_resume_pdf
        # - show_resume_download_options
        
        # Basic Profile Tools (move from orchestrator)
        # TODO: Move these from orchestrator.py to app/profile_tools.py
        # - update_personal_information
        # - add_work_experience
        # - add_education
        # - set_skills
        
        pass  # Tools will be added as we refactor
    
    def get_all_tools(self) -> List[Tool]:
        """Return all registered tools for the agent"""
        return self.tools
    
    def get_tools_by_category(self, category: str) -> List[Tool]:
        """Get tools filtered by category"""
        return [tool for tool in self.tools if getattr(tool, 'category', None) == category]

# 📋 REFACTORING PLAN
"""
PHASE 1: Move Tools to Existing Files
====================================
Move tools from orchestrator.py to your existing specialized files:

✅ YOU ALREADY HAVE THESE FILES:
- app/job_search.py          → Move job search tools here
- app/resume_generator.py    → Move resume generation tools here  
- app/cv_generator.py        → Move CV tools here
- app/cover_letter_generator.py → Move cover letter tools here
- app/pdf_generator.py       → Move PDF tools here
- app/documents.py           → Move document tools here

🆕 CREATE THESE NEW FILES:
- app/career_tools.py        → Interview prep, salary negotiation, career planning
- app/profile_tools.py       → Personal info, experience, education, skills

PHASE 2: Update Orchestrator
===========================
1. Remove all @tool definitions from orchestrator.py
2. Import ToolRegistry
3. Use registry.get_all_tools() in agent setup

PHASE 3: Benefits
================
- Orchestrator goes from 3135 lines → ~500 lines
- Each tool category in dedicated file
- Easier testing and maintenance
- Better Graph RAG integration
- Cleaner separation of concerns
"""

# 🚨 CRITICAL: DON'T BREAK WORKING REGENERATION
"""
When refactoring, preserve these WORKING systems:
- WebSocket message handling in orchestrator.py
- Regeneration logic (both frontend and backend)
- Page/chat switching logic
- Message loading for specific conversations

SAFE REFACTORING APPROACH:
1. Move tools ONE FILE at a time
2. Test regeneration after each move
3. Test chat switching after each move
4. Keep WebSocket logic in orchestrator.py
""" 