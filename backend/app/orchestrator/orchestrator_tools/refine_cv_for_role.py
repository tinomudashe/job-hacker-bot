from langchain_core.tools import tool
import logging
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import attributes
from app.models_db import User, Resume
from app.resume import ResumeData
from .get_or_create_resume import get_or_create_resume
import asyncio

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

log = logging.getLogger(__name__)

@tool
async def refine_cv_for_role(
    db: AsyncSession,
    user: User,
    resume_modification_lock: asyncio.Lock,
    target_role: str = "AI Engineering",
    job_description: str = "",
    company_name: str = ""
) -> str:
    """⭐ PRIMARY CV REFINEMENT TOOL ⭐"""
    async with resume_modification_lock:
        try:
            log.info(f"CV refinement requested for role: {target_role}")
            
            # 1. Get the user's current resume data.
            db_resume, base_resume_data = await get_or_create_resume(db, user)
            
            # 2. Create the generation chain to output structured JSON.
            parser = PydanticOutputParser(pydantic_object=ResumeData)
            
            prompt = PromptTemplate(
                template="""You are an expert career coach and resume writer. Your task is to refine a user's resume and return it as a structured JSON object.
                
                USER'S CURRENT RESUME DATA:
                {context}

                TARGET ROLE: {target_role}
                COMPANY: {company_name}
                JOB DESCRIPTION: {job_description}

                **CRITICAL, NON-NEGOTIABLE DIRECTIVE:**
                - **You MUST ONLY use the information provided in the 'USER'S CURRENT RESUME DATA' section.**
                - **You are STRICTLY FORBIDDEN from inventing, creating, or hallucinating any new information.**
                - Your ONLY task is to REFORMAT, REPHRASE, and TAILOR the *existing* information to better match the target role.
                - If a section is empty in the user's data, it should remain empty.
                - Return ONLY a valid JSON object matching the provided schema. Do not add any extra text or formatting.

                {format_instructions}
                """,
                input_variables=["context", "target_role", "company_name", "job_description"],
                partial_variables={"format_instructions": parser.get_format_instructions()},
            )
            
            # FIX: Use the user-specified Gemini Pro model.
            llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro-preview-03-25", temperature=0.3)
            chain = prompt | llm | parser
            
            # 3. Invoke the chain to generate the refined structured resume.
            refined_resume_data = await chain.ainvoke({
                "context": base_resume_data.json(),
                "target_role": target_role,
                "company_name": company_name or "target companies",
                "job_description": job_description or f"General {target_role} position requirements",
            })
            
            # 4. FIX: Update the user's single master resume record with the new structured data.
            db_resume.data = refined_resume_data.dict()
            attributes.flag_modified(db_resume, "data")
            await db.commit()
            
            # 5. Return a simple confirmation message with the trigger.
            return (f"I've successfully refined your CV for the **{target_role}** role. "
                    "A download button will appear on this message. [DOWNLOADABLE_RESUME]")
            
        except Exception as e:
            log.error(f"Error in CV refinement: {e}", exc_info=True)
            if db.in_transaction():
                await db.rollback()
            return f"❌ Sorry, an error occurred while refining your CV. Please try again."