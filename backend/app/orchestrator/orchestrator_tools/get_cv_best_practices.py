import logging
from typing import Optional
from pydantic import BaseModel, Field
from langchain_core.tools import Tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

log = logging.getLogger(__name__)

# Step 1: Define the explicit Pydantic input schema.
class CVBestPracticesInput(BaseModel):
    industry: Optional[str] = Field(default="", description="Target industry (e.g., 'tech', 'finance', 'healthcare').")
    experience_level: Optional[str] = Field(default="mid-level", description="User's experience level.")
    role_type: Optional[str] = Field(default="", description="Type of role (e.g., 'technical', 'management').")

# Step 2: Define the core logic as a plain async function.
async def _get_cv_best_practices(
        industry: str = "",
        experience_level: str = "mid-level",
        role_type: str = ""
    ) -> str:
    """The underlying implementation for getting comprehensive CV best practices."""
    try:
        prompt = ChatPromptTemplate.from_template(
            """You are an expert career coach and CV writer. Provide comprehensive, actionable CV best practices.

            TARGET PROFILE:
            - Industry: {industry}
            - Experience Level: {experience_level}
            - Role Type: {role_type}

            Provide detailed guidance covering all key aspects of a modern, effective CV."""
        )
        
        # Use the user-specified Gemini Pro model [[memory:4475666]]
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro-preview-03-25", temperature=0.7)
        chain = prompt | llm | StrOutputParser()
        
        guidance = await chain.ainvoke({
            "industry": industry or "general",
            "experience_level": experience_level,
            "role_type": role_type or "general professional"
        })
        
        return f"""## 📚 **CV Best Practices Guide**

        🎯 **Tailored for:** {experience_level} {role_type} professionals{f' in {industry}' if industry else ''}

        {guidance}
        """
        
    except Exception as e:
        log.error(f"Error in _get_cv_best_practices: {e}", exc_info=True)
        return f"❌ Sorry, I encountered an error while getting CV best practices: {str(e)}."

# Step 3: Manually construct the Tool object with the explicit schema.
get_cv_best_practices = Tool(
    name="get_cv_best_practices",
    description="Get comprehensive CV best practices, tips, and guidelines tailored to your industry and experience level.",
    func=_get_cv_best_practices,
    args_schema=CVBestPracticesInput
)
