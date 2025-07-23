from langchain_core.tools import tool
import logging
import json
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import attributes
from pydantic import BaseModel, Field

from app.models_db import Resume, User
from app.resume import fix_resume_data_structure
from app.url_scraper import scrape_job_url, JobDetails

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

log = logging.getLogger(__name__)

@tool("refine_cv_from_url", return_direct=False)
async def refine_cv_from_url(job_url: str, db: AsyncSession, user: User) -> str:
    """
    Refines a user's CV for a specific job by extracting details from a job posting URL.
    This tool scrapes the job description, then calls the resume generation logic to
    tailor the user's resume and saves it to the database.

    Args:
        job_url: The URL of the job posting.
    """
    try:
        user_id = user.id
        # Step 1: Scrape job details from the URL
        log.info(f"Attempting to refine CV from URL: {job_url}")
        
        scraped_details = await scrape_job_url(job_url)

        if isinstance(scraped_details, dict) and 'error' in scraped_details:
            return f"Sorry, I couldn't extract job details from that URL. Error: {scraped_details['error']}"

        if not isinstance(scraped_details, JobDetails):
            return "I ran into an issue reading the job posting. The website's structure might be complex."

        job_title = scraped_details.title
        company_name = scraped_details.company
        job_description = f"{scraped_details.description}\n\nRequirements:\n{scraped_details.requirements}"

        # Step 2: Generate the tailored resume using AI
        # Get User's Base Resume Data
        resume_result = await db.execute(
            select(Resume).where(Resume.user_id == user_id)
        )
        base_resume = resume_result.scalars().first()
        
        base_resume_data = {}
        if base_resume and base_resume.data:
            base_resume_data = fix_resume_data_structure(base_resume.data)

        # Define the Pydantic model for the output
        class TailoredResume(BaseModel):
            personalInfo: dict = Field(description="Personal information section, including summary.")
            experience: list = Field(description="List of all work experiences.")
            education: list = Field(description="List of all education entries.")
            skills: list = Field(description="A comprehensive list of skills.")
            projects: list = Field(description="List of projects, if any.")
            certifications: list = Field(description="List of certifications, if any.")

        parser = PydanticOutputParser(pydantic_object=TailoredResume)

        prompt_template = """
        You are an expert career coach. Your task is to generate a complete, tailored resume in JSON format
        based on the user's existing resume data and a target job description.

        **User's Base Resume Data:**
        {base_resume}

        **Target Job Description:**
        - Job Title: {job_title}
        - Company: {company_name}
        - Description: {job_description}

        **Instructions:**
        1. Rewrite the summary in the `personalInfo` section to target the job.
        2. Rephrase `experience` descriptions to highlight relevant accomplishments.
        3. Prioritize the `skills` most relevant to the job.
        4. Keep education, projects, and certifications largely the same.
        5. Return ONLY a valid JSON object matching the schema.

        {format_instructions}
        """
        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["base_resume", "job_title", "company_name", "job_description"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro-preview-03-25", temperature=0.4)
        chain = prompt | llm | parser

        tailored_resume = await chain.ainvoke({
            "base_resume": json.dumps(base_resume_data, indent=2),
            "job_title": job_title,
            "company_name": company_name,
            "job_description": job_description,
        })

        # Step 3: Save the new resume to the database
        db_resume_to_update = await db.get(Resume, base_resume.id) if base_resume else None

        if db_resume_to_update:
            db_resume_to_update.data = tailored_resume.dict()
            attributes.flag_modified(db_resume_to_update, "data")
        else:
            db_resume_to_update = Resume(user_id=user_id, data=tailored_resume.dict())
            db.add(db_resume_to_update)
        
        await db.commit()

        # Step 4: Return a success message
        output_str = (
            f"✅ I have successfully refined your CV for the **{job_title}** role at **{company_name}**.\n\n"
            "I analyzed the job description from the URL and tailored your profile accordingly. "
            "A download button should now be available on this message to get the updated PDF."
            "[DOWNLOADABLE_RESUME]"
        )

        return output_str

    except Exception as e:
        log.error(f"Error in refine_cv_from_url tool: {e}", exc_info=True)
        if db.in_transaction():
            await db.rollback()
        return f"❌ An error occurred while refining your resume from the URL. The website might be blocking access, or the job posting may have expired."
        