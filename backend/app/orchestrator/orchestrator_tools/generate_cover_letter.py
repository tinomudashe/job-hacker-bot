from langchain_core.tools import tool, Tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from sqlalchemy.ext.asyncio import AsyncSession
from app.models_db import User, GeneratedCoverLetter
from .get_or_create_resume import get_or_create_resume
from ..CoverLetterDetails import CoverLetterDetails
from ..education_input import PersonalInfo, ResumeData
import json
import uuid
import logging
from pydantic import BaseModel, Field

log = logging.getLogger(__name__)

# Step 1: Define the explicit Pydantic input schema for the tool.
class GenerateCoverLetterInput(BaseModel):
    company_name: str = Field(description="The name of the company to which the user is applying.")
    job_title: str = Field(description="The job title for the position.")
    job_description: str = Field(description="The full job description for the role.")

# Step 2: Define the core logic as a plain async function.
async def _generate_cover_letter(
    db: AsyncSession,
    user: User,
    company_name: str,
    job_title: str,
    job_description: str
) -> str:
    """
    The underlying implementation for generating a structured cover letter.
    """
    try:
        log.info(f"Generating structured cover letter for {job_title} at {company_name}")
        
        db_resume, resume_data = await get_or_create_resume(db, user)
        parser = PydanticOutputParser(pydantic_object=CoverLetterDetails)

        prompt_template = ChatPromptTemplate.from_messages([
            ("system", """You are an expert cover letter writer. Your task is to generate a cover letter in a structured JSON format. You MUST adhere to the JSON schema provided below. Do NOT add any conversational text, introductory sentences, or markdown formatting around the JSON object. Your output must be ONLY the raw JSON object.

{format_instructions}"""),
            ("human", """Please generate a tailored cover letter based on the following details:

**Job Details:**
- Job Title: {job_title}
- Company Name: {company_name}
- Job Description: {job_description}

**Candidate's Information:**
- Name: {name}
- Relevant Skills: {skills}
- Summary of Experience: {summary}

Generate the full cover letter body. It should be professional, concise, and tailored to the job description, highlighting the candidate's relevant skills and experience. Address it to the 'Hiring Team' if a specific name is not available.
"""),
        ])

        # As per user instruction, use the correct model name.
        chain = prompt_template | ChatGoogleGenerativeAI(model="gemini-2.5-pro-preview-03-25", temperature=0.7) | parser
        
        personal_info_dict = resume_data.personalInfo.dict() if resume_data.personalInfo else {}

        structured_response = await chain.ainvoke({
            "format_instructions": parser.get_format_instructions(),
            "job_title": job_title,
            "company_name": company_name,
            "job_description": job_description,
            "name": personal_info_dict.get("name", "User"),
            "skills": ", ".join(resume_data.skills) if resume_data.skills else "Not specified",
            "summary": personal_info_dict.get("summary", "No summary provided.")
        })

        response_dict = structured_response.model_dump()
        response_dict["personal_info"] = personal_info_dict

        new_cover_letter_id = str(uuid.uuid4())
        new_db_entry = GeneratedCoverLetter(
            id=new_cover_letter_id,
            user_id=user.id,
            content=json.dumps(response_dict)
        )
        db.add(new_db_entry)
        await db.commit()
        log.info(f"Successfully saved new cover letter with ID: {new_cover_letter_id}")

        final_output_string = f"[DOWNLOADABLE_COVER_LETTER] {json.dumps(response_dict)}"
        
        log.info(f"Successfully generated structured cover letter string ID {new_cover_letter_id}")
        return final_output_string
    
    except Exception as e:
        log.error(f"Error in generate_cover_letter implementation: {e}", exc_info=True)
        if db.in_transaction():
            await db.rollback()
        return "Sorry, I encountered an error while writing the cover letter. Please try again."

# Step 3: Manually construct the Tool object with the explicit schema.
generate_cover_letter = Tool(
    name="generate_cover_letter",
    description="Generates a structured cover letter based on provided job details (company name, job title, and description).",
    func=_generate_cover_letter,
    args_schema=GenerateCoverLetterInput
)
