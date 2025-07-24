from langchain_core.tools import tool
import logging
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import attributes
from app.models_db import User, Resume
from app.resume import ResumeData
from .get_or_create_resume import get_or_create_resume

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

log = logging.getLogger(__name__)

@tool
async def generate_tailored_resume(
    db: AsyncSession,
    user: User,
    job_title: str,
    company_name: str = "",
    job_description: str = "",
    user_skills: str = ""
) -> str:
    """
    Generates a complete, tailored resume based on a job description and user's profile.
    This tool now fetches the user's data, uses an LLM to generate a structured JSON
    resume, and updates the user's master resume record in the database.
    """
    try:
        # 1. Get User's Base Resume Data
        # This now returns the SQLAlchemy model and the Pydantic model
        db_resume_obj, base_resume_data = await get_or_create_resume(db, user)

        if isinstance(db_resume_obj, str): # Handle potential error string from helper
            return db_resume_obj

        # 2. Create the generation chain with a Pydantic output parser
        parser = PydanticOutputParser(pydantic_object=ResumeData)

        prompt_template = """
        You are an expert career coach and resume writer. Your task is to generate a complete, tailored resume in a structured JSON format.
        Analyze the user's base resume data and the provided job description to create a highly relevant and impactful resume.

        **User's Base Resume Data:**
        {base_resume}

        **Target Job Description:**
        - Job Title: {job_title}
        - Company: {company_name}
        - Description: {job_description}

        **User's Key Skills to Highlight (if provided):**
        {user_skills}

        **Instructions:**
        1.  **Rewrite the Summary:** Create a new, concise professional summary in the `personalInfo` section that directly targets the job description.
        2.  **Tailor Experience:** Rephrase job descriptions under `work_experience` to highlight accomplishments and responsibilities most relevant to the target role. Use strong action verbs and quantify achievements where possible.
        3.  **Prioritize Skills:** In the `skills` section, reorder and highlight the skills that are most relevant to the job description.
        4.  **Maintain Structure:** Keep the user's education, projects, and certifications as they are, but ensure they are in the final JSON.
        5.  **Output Format:** You MUST provide the final output as a valid JSON object matching the provided schema. Do not add any extra text or formatting.

        {format_instructions}
        """

        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["base_resume", "job_title", "company_name", "job_description", "user_skills"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )

        llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro-latest", temperature=0.4)
        chain = prompt | llm | parser

        # 3. Invoke the chain to generate the structured, tailored resume
        tailored_resume_data = await chain.ainvoke({
            "base_resume": json.dumps(base_resume_data.model_dump(), indent=2),
            "job_title": job_title,
            "company_name": company_name,
            "job_description": job_description,
            "user_skills": user_skills,
        })

        # 4. Update the user's single master resume record.
        db_resume_obj.data = tailored_resume_data.model_dump()
        attributes.flag_modified(db_resume_obj, "data")
        await db.commit()
        
        # 5. Return a simple confirmation message with the trigger.
        return (f"I have successfully tailored your resume for the {job_title} role. "
                "You can preview, edit, and download it now. [DOWNLOADABLE_RESUME]")

    except Exception as e:
        log.error(f"Error in generate_tailored_resume tool: {e}", exc_info=True)
        # Check if a transaction is active before trying to roll back
        if db.in_transaction():
            await db.rollback()
        return "An error occurred while tailoring your resume. Please ensure the job description is detailed enough."