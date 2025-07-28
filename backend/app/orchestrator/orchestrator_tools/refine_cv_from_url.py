import logging
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import attributes
from pydantic import BaseModel, Field
from langchain_core.tools import Tool
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

from app.models_db import Resume, User
from app.url_scraper import scrape_job_url, JobDetails
from app.resume import ResumeData
from .get_or_create_resume import get_or_create_resume

log = logging.getLogger(__name__)

# Step 1: Define the explicit Pydantic input schema.
class RefineCvFromUrlInput(BaseModel):
    job_url: str = Field(description="The URL of the job posting.")

# Step 2: Define the core logic as a plain async function.
async def _refine_cv_from_url(job_url: str, db: AsyncSession, user: User) -> str:
    """The underlying implementation for refining a user's CV based on a job posting URL."""
    try:
        log.info(f"Refining CV from URL: {job_url} for user {user.id}")
        scraped_details = await scrape_job_url(job_url)

        if not isinstance(scraped_details, JobDetails):
            error_msg = scraped_details.get('error', 'Unknown scraping error') if isinstance(scraped_details, dict) else 'Could not parse job details.'
            return f"❌ Sorry, I couldn't extract job details from that URL. Error: {error_msg}"

        job_description = f"{scraped_details.description}\n\nRequirements:\n{scraped_details.requirements}"

        db_resume, base_resume_data = await get_or_create_resume(db, user)
        if isinstance(base_resume_data, str): # Error case
            return base_resume_data

        parser = PydanticOutputParser(pydantic_object=ResumeData)
        prompt = PromptTemplate(
            template="""You are an expert resume writer. Tailor the user's base resume for the target job description.
            Rewrite the summary, rephrase experience to highlight relevant achievements, and prioritize skills.
            Return ONLY a valid JSON object matching the schema.

            USER'S BASE RESUME: {base_resume}
            TARGET JOB: {job_title} at {company_name}
            DESCRIPTION: {job_description}
            
            {format_instructions}""",
            input_variables=["base_resume", "job_title", "company_name", "job_description"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )
        # Use the user-specified Gemini Pro model [[memory:4475666]]
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro-preview-03-25", temperature=0.4)
        chain = prompt | llm | parser

        tailored_resume_data = await chain.ainvoke({
            "base_resume": base_resume_data.model_dump_json(),
            "job_title": scraped_details.title,
            "company_name": scraped_details.company,
            "job_description": job_description,
        })

        db_resume.data = tailored_resume_data.model_dump(exclude_none=True)
        attributes.flag_modified(db_resume, "data")
        await db.commit()

        return (
            f"✅ I have successfully refined your CV for the **{scraped_details.title}** role at **{scraped_details.company}**.\n\n"
            "A download button should now be available on this message to get the updated PDF.\n"
            "[DOWNLOADABLE_RESUME]"
        )

    except Exception as e:
        log.error(f"Error in _refine_cv_from_url for user {user.id}: {e}", exc_info=True)
        await db.rollback()
        return "❌ An error occurred while refining your resume from the URL. The website might be blocking access."

# Step 3: Manually construct the Tool object with the explicit schema.
refine_cv_from_url = Tool(
    name="refine_cv_from_url",
    description="Refines a user's CV for a specific job by extracting details from a job posting URL and tailoring the resume content.",
    func=_refine_cv_from_url,
    args_schema=RefineCvFromUrlInput
)
        