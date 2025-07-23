from langchain_core.tools import tool
import logging
import json
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.models_db import User, GeneratedCoverLetter
from app.url_scraper import scrape_job_url, JobDetails
from ..orchestrator_models.CoverLetterDetails import CoverLetterDetails
from app.db import get_db_session

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

log = logging.getLogger(__name__)

@tool("refine_cover_letter_from_url", return_direct=False)
async def refine_cover_letter_from_url(job_url: str, db: AsyncSession, user: User) -> str:
    """
    Refines a user's cover letter for a specific job by extracting details from a job posting URL.
    
    Args:
        job_url (str): The URL of the job posting.
    
    Returns:
        str: A confirmation message with a trigger to download the cover letter.
    """
    log.info(f"Attempting to generate cover letter from URL: {job_url}")
    try:
        user_id = user.id
        if not user_id:
            return "Authentication failed. Could not identify user."

        # Step 1: Scrape the job description from the URL
        scraped_details = await scrape_job_url(job_url)
        
        if isinstance(scraped_details, dict) and 'error' in scraped_details:
            log.error(f"Failed to scrape job details: {scraped_details['error']}")
            return f"I'm sorry, I couldn't extract details from that URL. The error was: {scraped_details['error']}"

        if not isinstance(scraped_details, JobDetails):
            log.error(f"Scraping returned an unexpected type: {type(scraped_details)}")
            return "I ran into an unexpected issue while reading the job posting. The website's structure might be too complex."

        # Step 2: Use the generated details to create and save the cover letter
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro-preview-03-25", temperature=0.3)
        parser = JsonOutputParser(pydantic_object=CoverLetterDetails)
        
        prompt_template = PromptTemplate(
            template="""
            You are a helpful assistant that generates structured cover letters based on user information and a job description.
            Analyze the user's profile and the provided job details to create a compelling and tailored cover letter.
            The user's personal information is: {user_info}.
            The job details are: {job_details}.
            You must respond using the following JSON format.
            {format_instructions}
            """,
            input_variables=["user_info", "job_details"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )
        
        chain = prompt_template | llm | parser

        user_info_dict = {
            "name": user.name,
            "email": user.email,
            "linkedin": user.linkedin,
            "phone": user.phone or "Not provided",
            "website": ""
        }

        job_details_str = f"Job Title: {scraped_details.title}, Company: {scraped_details.company}, Description: {scraped_details.description}, Requirements: {scraped_details.requirements}"

        response_data = await chain.ainvoke({"user_info": json.dumps(user_info_dict), "job_details": job_details_str})
        
        if isinstance(response_data, BaseModel):
            response_dict = response_data.model_dump()
        else:
            response_dict = response_data
        
        content_json_string = json.dumps(response_dict)

        new_cover_letter = GeneratedCoverLetter(
            id=str(uuid.uuid4()),
            user_id=user.id,
            content=content_json_string,
        )
        db.add(new_cover_letter)
        await db.commit()
        log.info(f"Successfully generated and saved cover letter {new_cover_letter.id} for user {user.id}")

        # Step 3: Return the trigger to the user
        return "I have successfully generated the cover letter based on the URL. You can view and download it now. [DOWNLOADABLE_COVER_LETTER]"

    except Exception as e:
        log.error(f"An unexpected error occurred in refine_cover_letter_from_url: {e}", exc_info=True)
        if db.in_transaction():
            await db.rollback()
        return f"An unexpected error occurred while generating the cover letter from the URL: {str(e)}"
        