from langchain_core.tools import tool
import logging
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import attributes
from app.models_db import User
from app.resume import Experience, Education
from .get_or_create_resume import get_or_create_resume
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

log = logging.getLogger(__name__)

@tool
async def enhance_resume_section(
    db: AsyncSession,
    user: User,
    section: str,
    job_description: str = "",
    current_content: str = ""
) -> str:
    """
    Enhance a specific section of your resume with AI-powered improvements.
    This tool fetches the user's current resume, uses an LLM to improve a specific section,
    and then updates the resume record in the database with the new structured data.
    
    Args:
        section: Section to enhance (summary, experience, skills, education)
        job_description: Target job description for tailoring (optional)
        current_content: Current content of the section to improve (optional, will be fetched if not provided)
    
    Returns:
        A success message indicating the section has been enhanced.
    """
    try:
        # 1. Get the user's current resume data
        db_resume, resume_data = await get_or_create_resume(db, user)

        # Determine the content to be enhanced
        content_to_enhance = current_content
        if not content_to_enhance:
            if section.lower() == 'summary':
                content_to_enhance = resume_data.personalInfo.summary
            elif section.lower() == 'experience':
                content_to_enhance = json.dumps([exp.dict() for exp in resume_data.experience])
            elif section.lower() == 'skills':
                content_to_enhance = ", ".join(resume_data.skills)
            elif section.lower() == 'education':
                    content_to_enhance = json.dumps([edu.dict() for edu in resume_data.education])

        # 2. Use LLM to generate the enhanced content for the specific section
        prompt = ChatPromptTemplate.from_template(
            """You are an expert resume writer. Enhance the specified resume section based on the user's context and the target job description.

USER CONTEXT:
- Current Role: {current_role}
- Current Skills: {current_skills}

SECTION TO ENHANCE: {section}
CURRENT CONTENT:
{content_to_enhance}

TARGET JOB DESCRIPTION (if provided):
{job_description}

INSTRUCTIONS:
- Rewrite the content to be more impactful and results-oriented.
- Use strong action verbs and quantify achievements where possible.
- If it is the 'skills' section, return a comma-separated list of skills.
- If it is 'experience' or 'education', return a JSON array of objects.
- If it is 'summary', return a concise paragraph.
- Return ONLY the enhanced content for the section.

ENHANCED CONTENT:"""
        )
        
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro-preview-03-25", temperature=0.5)
        chain = prompt | llm | StrOutputParser()
        
        enhanced_content = await chain.ainvoke({
            "current_role": resume_data.experience[0].jobTitle if resume_data.experience else "Not specified",
            "current_skills": ", ".join(resume_data.skills),
            "section": section,
            "content_to_enhance": content_to_enhance,
            "job_description": job_description or "Not specified"
        })

        # 3. Update the structured resume data with the enhanced content
        if section.lower() == 'summary':
            resume_data.personalInfo.summary = enhanced_content
        elif section.lower() == 'experience':
            resume_data.experience = [Experience(**exp) for exp in json.loads(enhanced_content)]
        elif section.lower() == 'skills':
            resume_data.skills = [s.strip() for s in enhanced_content.split(',')]
        elif section.lower() == 'education':
            resume_data.education = [Education(**edu) for edu in json.loads(enhanced_content)]

        # 4. Save the updated resume data back to the database
        db_resume.data = resume_data.dict()
        attributes.flag_modified(db_resume, "data")
        await db.commit()

        return f"✅ Your '{section}' section has been successfully enhanced. [DOWNLOADABLE_RESUME]"

    except Exception as e:
        log.error(f"Error enhancing resume section: {e}", exc_info=True)
        if db.in_transaction():
            await db.rollback()
        return f"❌ Sorry, I encountered an error while enhancing your {section} section: {str(e)}."
