import logging
import json
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import attributes
from pydantic import BaseModel, Field
from langchain_core.tools import Tool
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

from app.models_db import User, Resume
from app.resume import ResumeData
from .get_or_create_resume import get_or_create_resume

log = logging.getLogger(__name__)

# Step 1: Define the explicit Pydantic input schema for the tool.
class TailoredResumeInput(BaseModel):
    job_title: str = Field(description="The target job title.")
    company_name: Optional[str] = Field(default="", description="The target company name.")
    job_description: Optional[str] = Field(default="", description="The full job description for the target role.")
    user_skills: Optional[str] = Field(default="", description="Specific skills the user wants to highlight.")

# Step 2: Define the core logic as a plain async function.
async def _generate_tailored_resume(
    db: AsyncSession,
    user: User,
    job_title: str,
    company_name: str = "",
    job_description: str = "",
    user_skills: str = ""
) -> str:
    """
    The underlying implementation for generating a complete, tailored resume.
    """
    try:
        db_resume_obj, base_resume_data = await get_or_create_resume(db, user)

        if isinstance(db_resume_obj, str):
            return db_resume_obj

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

        # As per user instruction, use the correct model name.
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro-preview-03-25", temperature=0.4)
        chain = prompt | llm | parser

        tailored_resume_data = await chain.ainvoke({
            "base_resume": json.dumps(base_resume_data.model_dump(), indent=2),
            "job_title": job_title,
            "company_name": company_name,
            "job_description": job_description,
            "user_skills": user_skills,
        })

        db_resume_obj.data = tailored_resume_data.model_dump()
        attributes.flag_modified(db_resume_obj, "data")
        await db.commit()
        
        return (f"I have successfully tailored your resume for the {job_title} role. "
                "You can preview, edit, and download it now. [DOWNLOADABLE_RESUME]")

    except Exception as e:
        log.error(f"Error in _generate_tailored_resume: {e}", exc_info=True)
        if db.in_transaction():
            await db.rollback()
        return "An error occurred while tailoring your resume. Please ensure the job description is detailed enough."

# Step 3: Manually construct the Tool object with the explicit schema.
generate_tailored_resume = Tool(
    name="generate_tailored_resume",
    description="Generates a complete, tailored resume based on a job description and user's profile.",
    func=_generate_tailored_resume,
    args_schema=TailoredResumeInput
)