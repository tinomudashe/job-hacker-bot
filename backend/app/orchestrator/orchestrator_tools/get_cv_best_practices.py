from langchain_core.tools import tool
import logging
log = logging.getLogger(__name__)

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

@tool
async def get_cv_best_practices(
        industry: str = "",
        experience_level: str = "mid-level",
        role_type: str = ""
    ) -> str:
    """Get comprehensive CV best practices, tips, and guidelines tailored to your industry and experience level.
    
    Args:
        industry: Target industry (e.g., "tech", "finance", "healthcare", "marketing")
        experience_level: Your experience level (entry-level, mid-level, senior, executive)
        role_type: Type of role (e.g., "technical", "management", "sales", "creative")
    
    Returns:
        Detailed CV best practices and actionable tips
    """
    try:
        prompt = ChatPromptTemplate.from_template(
            """You are an expert career coach and CV writer. Provide comprehensive, actionable CV best practices.

TARGET PROFILE:
- Industry: {industry}
- Experience Level: {experience_level}
- Role Type: {role_type}

Provide detailed guidance covering:

## 📋 **CV Structure & Format**
- Optimal CV length and layout
- Section ordering and priorities
- Font, spacing, and visual guidelines
- ATS-friendly formatting tips

## 🎯 **Content Best Practices**
- How to write compelling professional summaries
- Quantifying achievements with metrics
- Using strong action verbs effectively
- Tailoring content for specific roles

## 🔍 **Industry-Specific Tips**
- Key skills and keywords for this industry
- Common requirements and expectations
- Portfolio/work samples considerations
- Certification and education priorities

## ⚠️ **Common Mistakes to Avoid**
- Red flags that hurt your chances
- Outdated practices to eliminate
- Length and content balance issues
- Contact information best practices

## 🚀 **Advanced Strategies**
- ATS optimization techniques
- Personal branding integration
- LinkedIn profile alignment
- Cover letter coordination

## 📊 **Success Metrics**
- How to track CV performance
- When and how to update your CV
- Multiple version strategies

Provide specific, actionable advice that someone can implement immediately."""
        )
        
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-pro-preview-03-25",
            temperature=0.7
        )
        
        chain = prompt | llm | StrOutputParser()
        
        guidance = await chain.ainvoke({
            "industry": industry or "general",
            "experience_level": experience_level,
            "role_type": role_type or "general professional"
        })
        
        return f"""## 📚 **CV Best Practices Guide**

🎯 **Tailored for:** {experience_level} {role_type} professionals{f' in {industry}' if industry else ''}

{guidance}

---

**💡 Quick Action Items:**
1. **Review Your Current CV**: Use these guidelines to audit your existing CV
2. **Implement Top 3 Changes**: Start with the most impactful improvements
3. **Test ATS Compatibility**: Use online ATS checkers to validate formatting
4. **Get Feedback**: Have colleagues or mentors review using these criteria

**🔗 Related Commands:**
- `enhance my resume section [section_name]` - Improve specific sections
- `create resume from scratch` - Start fresh with best practices
- `analyze my skills gap` - Identify areas for improvement"""
        
    except Exception as e:
        log.error(f"Error getting CV best practices: {e}", exc_info=True)
        return f"❌ Sorry, I encountered an error while getting CV best practices: {str(e)}. Please try again."
