import logging
from typing import Optional
from pydantic import BaseModel, Field
from langchain_core.tools import Tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

log = logging.getLogger(__name__)

# Step 1: Define the explicit Pydantic input schema.
class ATSOptimizationInput(BaseModel):
    file_format: Optional[str] = Field(default="PDF", description="CV file format (e.g., 'PDF', 'DOCX').")
    industry: Optional[str] = Field(default="", description="Target industry for specific ATS considerations.")

# Step 2: Define the core logic as a plain async function.
async def _get_ats_optimization_tips(
        file_format: str = "PDF",
        industry: str = ""
    ) -> str:
    """The underlying implementation for getting ATS optimization tips."""
    try:
        prompt = ChatPromptTemplate.from_template(
            """You are an ATS optimization expert. Provide comprehensive, technical guidance for passing modern ATS systems.

            TARGET CONTEXT:
            - File Format: {file_format}
            - Industry: {industry}

            Provide detailed ATS optimization guidance covering file format, keywords, structure, and testing."""
        )
        
        # Use the user-specified Gemini Pro model [[memory:4475666]]
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro-preview-03-25", temperature=0.6)
        chain = prompt | llm | StrOutputParser()
        
        tips = await chain.ainvoke({
            "file_format": file_format,
            "industry": industry or "general"
        })
        
        return f"## 🤖 **ATS Optimization Guide**\n\n📁 **Format:** {file_format} | 🏢 **Industry:** {industry or 'General'}\n\n{tips}"
        
    except Exception as e:
        log.error(f"Error in _get_ats_optimization_tips: {e}", exc_info=True)
        return f"❌ Sorry, I encountered an error while getting ATS tips: {str(e)}."

# Step 3: Manually construct the Tool object with the explicit schema.
get_ats_optimization_tips = Tool(
    name="get_ats_optimization_tips",
    description="Get specific tips for optimizing your CV to pass Applicant Tracking Systems (ATS).",
    func=_get_ats_optimization_tips,
    args_schema=ATSOptimizationInput
)