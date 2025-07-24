from langchain_core.tools import tool
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models_db import Resume, User
from app.resume import ResumeData, fix_resume_data_structure
import logging

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from sqlalchemy.future import select
from app.models_db import User, Resume
from pydantic import BaseModel, Field

log = logging.getLogger(__name__)

class AnalyzeSkillsGapInput(BaseModel):
    """Input for analyzing the skills gap between the user's resume and a job description."""
    job_description: str = Field(description="The full text of the job description to compare against.")

@tool(args_schema=AnalyzeSkillsGapInput)
async def analyze_skills_gap(db: AsyncSession, user: User, job_description: str) -> str:
    """Analyzes the user's skills from their resume against a job description to identify gaps."""
    try:
        # Get user's current skills from profile
        result = await db.execute(select(Resume).where(Resume.user_id == user.id))
        db_resume = result.scalars().first()
        
        user_skills = current_skills
        if not user_skills and db_resume and db_resume.data:
            # Fix missing ID fields in existing data before validation
            fixed_data = fix_resume_data_structure(db_resume.data)
            resume_data = ResumeData(**fixed_data)
            user_skills = ', '.join(resume_data.skills) if resume_data.skills else ""
        
        prompt = ChatPromptTemplate.from_template(
            """You are a career development expert. Analyze the skills gap and provide actionable career development advice.

TARGET ROLE: {target_role}
CURRENT SKILLS: {current_skills}
JOB DESCRIPTION: {job_description}

Provide a comprehensive skills gap analysis:

## 🎯 **Role Requirements Analysis**
- Core technical skills needed
- Soft skills and competencies required
- Experience level expectations
- Industry-specific knowledge needed

## ✅ **Your Strengths**
- Skills you already have that match
- Transferable skills from your background
- Competitive advantages you possess
- Areas where you exceed requirements

## 📈 **Skills to Develop**
### High Priority (Essential)
- Critical missing skills for the role
- Skills that appear in most job postings
- Technical competencies to prioritize

### Medium Priority (Valuable)
- Nice-to-have skills that differentiate candidates
- Emerging technologies in the field
- Cross-functional competencies

### Low Priority (Future Growth)
- Advanced skills for career progression
- Specialized technologies or certifications
- Leadership and management capabilities

## 📚 **Learning Roadmap**
### Immediate (Next 1-3 months)
- Specific courses, certifications, or bootcamps
- Free resources and tutorials
- Practical projects to build skills

### Medium-term (3-6 months)
- More comprehensive training programs
- Professional certifications
- Portfolio development projects

### Long-term (6+ months)
- Advanced certifications or degrees
- Conference attendance and networking
- Thought leadership opportunities

## 💼 **CV Enhancement Strategy**
- How to present existing skills more effectively
- Projects to showcase during skill development
- Keywords to incorporate from target role
- Experience gaps to address

## 🎯 **Action Plan**
Provide specific, time-bound recommendations for skill development."""
        )
        
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-pro-preview-03-25",
            temperature=0.7
        )
        
        chain = prompt | llm | StrOutputParser()
        
        analysis = await chain.ainvoke({
            "target_role": target_role,
            "current_skills": user_skills or "No skills information provided",
            "job_description": job_description or "No specific job description provided"
        })
        
        return f"""## 🔍 **Skills Gap Analysis for {target_role}**

{analysis}

---

**🚀 Next Steps:**
1. **Prioritize Learning**: Focus on high-priority skills first
2. **Update Your CV**: Add new skills as you develop them
3. **Build Projects**: Create portfolio pieces demonstrating new skills
4. **Network Actively**: Connect with professionals in your target role
5. **Track Progress**: Regularly reassess your skill development

**🔗 Helpful Commands:**
- `search jobs for [role]` - Find specific requirements in current job postings
- `enhance my resume section skills` - Optimize your skills presentation
- `create learning plan for [skill]` - Get detailed learning resources"""
        
    except Exception as e:
        log.error(f"Error analyzing skills gap: {e}", exc_info=True)
        return f"❌ Sorry, I encountered an error during skills gap analysis: {str(e)}. Please try again."