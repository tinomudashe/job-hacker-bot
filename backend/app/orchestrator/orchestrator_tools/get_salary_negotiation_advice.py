import logging
from typing import Optional
from pydantic import BaseModel, Field
from langchain_core.tools import Tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

log = logging.getLogger(__name__)

# Step 1: Define the explicit Pydantic input schema.
class SalaryNegotiationInput(BaseModel):
    job_title: str = Field(description="The position you are negotiating for.")
    experience_level: Optional[str] = Field(default="mid-level", description="Your experience level.")
    location: Optional[str] = Field(default="", description="Job location for market rate context.")
    industry: Optional[str] = Field(default="", description="Industry for sector-specific advice.")

# Step 2: Define the core logic as a plain async function.
async def _get_salary_negotiation_advice(
        job_title: str,
        experience_level: str = "mid-level", 
        location: str = "",
        industry: str = ""
    ) -> str:
    """The underlying implementation for getting salary negotiation strategies."""
    try:
        prompt = ChatPromptTemplate.from_template(
            """You are a compensation and career negotiation expert. Provide comprehensive salary negotiation guidance.

            NEGOTIATION CONTEXT:
            - Job Title: {job_title}
            - Experience Level: {experience_level}
            - Location: {location}
            - Industry: {industry}

            Provide a detailed guide covering market research, negotiation strategy, and common scenarios."""
        )
        
        # Use the user-specified Gemini Pro model [[memory:4475666]]
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro-preview-03-25", temperature=0.7)
        chain = prompt | llm | StrOutputParser()
        
        advice = await chain.ainvoke({
            "job_title": job_title,
            "experience_level": experience_level,
            "location": location or "general market",
            "industry": industry or "general"
        })
        
        return f"## 💰 **Salary Negotiation Strategy Guide for {job_title}**\n\n{advice}"
        
    except Exception as e:
        log.error(f"Error in _get_salary_negotiation_advice: {e}", exc_info=True)
        return f"❌ Sorry, I encountered an error while getting negotiation advice: {str(e)}."

# Step 3: Manually construct the Tool object with the explicit schema.
get_salary_negotiation_advice = Tool(
    name="get_salary_negotiation_advice",
    description="Get comprehensive salary negotiation strategies and market data insights.",
    func=_get_salary_negotiation_advice,
    args_schema=SalaryNegotiationInput
)
