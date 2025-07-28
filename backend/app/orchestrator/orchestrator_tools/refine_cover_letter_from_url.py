import logging
import json
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from langchain_core.tools import Tool

from app.models_db import User, GeneratedCoverLetter
from app.url_scraper import scrape_job_url, JobDetails
from ..CoverLetterDetails import CoverLetterDetails

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

log = logging.getLogger(__name__)

# Step 1: Define the explicit Pydantic input schema.
class RefineCoverLetterFromUrlInput(BaseModel):
    job_url: str = Field(description="The URL of the job posting.")

# Step 2: Define the core logic as a plain async function.
# This function no longer needs the @tool decorator.
async def _refine_cover_letter_from_url(job_url: str, db: AsyncSession, user: User) -> str:
    """
    The underlying implementation for refining a cover letter from a job URL.
    """
    log.info(f"Attempting to generate cover letter from URL: {job_url}")
    try:
        scraped_details = await scrape_job_url(job_url)
        
        if isinstance(scraped_details, dict) and 'error' in scraped_details:
            log.error(f"Failed to scrape job details: {scraped_details['error']}")
            return f"I'm sorry, I couldn't extract details from that URL. The error was: {scraped_details['error']}"

        if not isinstance(scraped_details, JobDetails):
            log.error(f"Scraping returned an unexpected type: {type(scraped_details)}")
            return "I ran into an unexpected issue while reading the job posting."

        # Use the correct, powerful model for this generative task as per user preference.
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro-preview-03-25", temperature=0.3)
        parser = JsonOutputParser(pydantic_object=CoverLetterDetails)
        
        prompt_template = PromptTemplate(
            template="""
            You are a helpful assistant that generates structured cover letters.
            Analyze the user's profile and the provided job details to create a compelling and tailored cover letter.
            User's personal information: {user_info}.
            Job details: {job_details}.
            You must respond using the following JSON format.
            {format_instructions}
            """,
            input_variables=["user_info", "job_details"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )
        
        chain = prompt_template | llm | parser

        user_info_dict = {
            "name": user.name, "email": user.email, "linkedin": user.linkedin,
            "phone": user.phone or "N/A", "website": ""
        }

        job_details_str = f"Job Title: {scraped_details.title}, Company: {scraped_details.company}, Description: {scraped_details.description}"

        response_data = await chain.ainvoke({"user_info": json.dumps(user_info_dict), "job_details": job_details_str})
        
        response_dict = response_data if isinstance(response_data, dict) else response_data.model_dump()
        
        content_json_string = json.dumps(response_dict)

        new_cover_letter = GeneratedCoverLetter(
            id=str(uuid.uuid4()),
            user_id=user.id,
            content=content_json_string,
        )
        db.add(new_cover_letter)
        await db.commit()
        log.info(f"Successfully generated and saved cover letter {new_cover_letter.id}")

        return "I have successfully generated the cover letter from the URL. [DOWNLOADABLE_COVER_LETTER]"

    except Exception as e:
        log.error(f"An unexpected error occurred in _refine_cover_letter_from_url: {e}", exc_info=True)
        if db.in_transaction():
            await db.rollback()
        return f"An unexpected error occurred while generating the cover letter from the URL: {str(e)}"

# Step 3: Manually construct the Tool object with the explicit schema.
refine_cover_letter_from_url = Tool(
    name="refine_cover_letter_from_url",
    description="Refines a cover letter for a specific job by extracting details from a job posting URL.",
    func=_refine_cover_letter_from_url,
    args_schema=RefineCoverLetterFromUrlInput
)
        