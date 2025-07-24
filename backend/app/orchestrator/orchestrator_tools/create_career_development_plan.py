import logging
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.tools import tool
from sqlalchemy import select
from app.models_db import Resume, User
from app.resume import ResumeData, fix_resume_data_structure

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

log = logging.getLogger(__name__)

class CreateCareerDevelopmentPlanInput(BaseModel):
    """Input for creating a career development plan."""
    current_role: str = Field(description="The user's current job role or title.")
    target_role: str = Field(description="The desired future job role or title.")
    timeframe_years: int = Field(5, description="The timeframe in years for the career plan, e.g., 5.")

@tool(args_schema=CreateCareerDevelopmentPlanInput)
async def create_career_development_plan(
    db: AsyncSession,
    user: User,
    current_role: str,
    target_role: str,
    timeframe_years: int = 5,
) -> str:
    """Create a comprehensive career development plan with specific steps and milestones.
    
    Args:
        current_role: Your current position/role
        target_role: Where you want to be in your career
        timeframe_years: Timeframe for achieving your goal in years
    
    Returns:
        Detailed career development roadmap with actionable steps
    """
    try:
        # Get user context from resume
        result = await db.execute(select(Resume).where(Resume.user_id == user.id))
        db_resume = result.scalars().first()
        
        user_context = f"User: {user.first_name} {user.last_name}"
        if db_resume and db_resume.data:
            # Fix missing ID fields in existing data before validation
            fixed_data = fix_resume_data_structure(db_resume.data)
            resume_data = ResumeData(**fixed_data)
            user_context += f"\nCurrent Background: {resume_data.personalInfo.summary or 'No summary available'}"
            user_context += f"\nSkills: {', '.join(resume_data.skills[:8]) if resume_data.skills else 'No skills listed'}"
            if resume_data.experience:
                user_context += f"\nCurrent Role: {resume_data.experience[0].jobTitle} at {resume_data.experience[0].company}"
        
        prompt = ChatPromptTemplate.from_template(
            """You are a senior career strategist and executive coach. Create a comprehensive, actionable career development plan.

USER CONTEXT: {user_context}
CURRENT ROLE: {current_role}
TARGET ROLE: {target_role}
TIMELINE: {timeline}

Create a detailed career development roadmap:

## 🎯 **Career Vision & Goals**
### Target Role Analysis
- Detailed breakdown of target role requirements
- Skills, experience, and qualifications needed
- Typical career progression path to this role
- Market demand and growth outlook

### Gap Analysis
- Current state vs. target state assessment
- Critical skills and experience gaps
- Knowledge areas requiring development
- Network and relationship gaps

## 🗓️ **Timeline & Milestones**
### Phase 1: Foundation Building (Months 1-{timeline_first_third})
- Immediate skill development priorities
- Quick wins and early achievements
- Network building initiatives
- Performance optimization in current role

### Phase 2: Growth & Expansion (Months {timeline_middle})
- Advanced skill acquisition
- Leadership development activities
- Strategic project involvement
- External visibility building

### Phase 3: Positioning & Transition (Final phase)
- Final preparation for target role
- Strategic job search activities
- Interview and positioning preparation
- Offer negotiation and transition planning

## 📚 **Learning & Development Strategy**
### Technical Skills Development
- Specific courses, certifications, and training
- Online learning platforms and resources
- Hands-on projects and applications
- Skill assessment and validation methods

### Soft Skills Enhancement
- Leadership and management capabilities
- Communication and presentation skills
- Strategic thinking and business acumen
- Industry knowledge and market awareness

### Formal Education & Certifications
- Professional certifications to pursue
- Advanced degree considerations
- Industry-specific credentials
- Cost-benefit analysis of educational investments

## 🤝 **Networking & Relationship Building**
### Professional Network Expansion
- Industry conferences and events to attend
- Professional associations to join
- LinkedIn strategy and online presence
- Informational interview targets

### Mentorship & Sponsorship
- Identifying potential mentors
- Building sponsor relationships
- Peer learning groups and communities
- Reverse mentoring opportunities

### Internal Relationship Building
- Stakeholder mapping in current organization
- Cross-functional collaboration opportunities
- Visibility projects and high-impact initiatives
- Leadership team exposure strategies

## 💼 **Experience & Exposure Plan**
### Current Role Optimization
- Ways to enhance current role impact
- Additional responsibilities to seek
- Performance metrics to improve
- Success stories to develop

### Strategic Project Involvement
- High-visibility projects to pursue
- Cross-functional team leadership
- Innovation and change initiatives
- Customer or client-facing opportunities

### External Experience Building
- Volunteer leadership roles
- Industry speaking opportunities
- Writing and thought leadership
- Board or committee service

## 📊 **Progress Tracking & Measurement**
### Key Performance Indicators
- Specific metrics to track progress
- Milestone achievement criteria
- Skills assessment benchmarks
- Network growth measurements

### Regular Review Process
- Monthly progress check-ins
- Quarterly goal adjustments
- Annual plan reviews and updates
- Feedback collection and integration

### Course Correction Strategies
- How to adapt plan based on market changes
- Pivoting strategies if goals change
- Accelerating progress when opportunities arise
- Managing setbacks and delays

## 🚀 **Action Plan & Next Steps**
### Immediate Actions (Next 30 days)
- Specific tasks to start immediately
- Resources to gather and review
- Conversations to initiate
- Systems to put in place

### Short-term Priorities (Next 90 days)
- Major initiatives to launch
- Skills development to begin
- Relationships to build
- Opportunities to pursue

Provide specific, time-bound, measurable actions that create a clear path to the target role."""
        )
        
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-pro-preview-03-25",
            temperature=0.7
        )
        
        chain = prompt | llm | StrOutputParser()
        
        # Calculate timeline phases for the prompt
        timeline_months = timeframe_years * 12
        first_third = timeline_months // 3
        middle = f"{first_third + 1}-{timeline_months * 2 // 3}"
        
        plan = await chain.ainvoke({
            "user_context": user_context,
            "current_role": current_role or "current position",
            "target_role": target_role or "target career goal",
            "timeline": f"{timeframe_years} years",
            "timeline_first_third": first_third,
            "timeline_middle": middle
        })
        
        return f"""## 🚀 **Career Development Plan**

**Journey:** {current_role or 'Current Role'} → {target_role or 'Target Role'} | **Timeline:** {timeframe_years} years

{plan}

---

**📋 Implementation Checklist:**
- ✅ Schedule monthly career development review meetings
- ✅ Create learning and development budget
- ✅ Identify and reach out to potential mentors
- ✅ Set up skill assessment baseline measurements
- ✅ Begin networking activities and relationship building
- ✅ Start first priority learning initiative

**⚡ Success Factors:**
- **Consistency**: Regular, dedicated effort toward goals
- **Flexibility**: Adapt plan based on opportunities and market changes
- **Accountability**: Regular progress reviews and adjustments
- **Network**: Strong professional relationships for guidance and opportunities
- **Measurement**: Clear metrics to track progress and success

**🔄 Review Schedule:**
- **Weekly**: Progress on immediate actions and priorities
- **Monthly**: Overall plan progress and milestone achievement
- **Quarterly**: Goals adjustment and strategy refinement
- **Annually**: Comprehensive plan review and major updates

**🔗 Supporting Tools:**
- `analyze my skills gap` - Regular skills assessment
- `get interview preparation guide` - Practice for target role
- `enhance my resume section` - Update CV as you grow"""
        
    except Exception as e:
        log.error(f"Error creating career development plan: {e}", exc_info=True)
        return f"❌ Sorry, I encountered an error while creating your career plan: {str(e)}. Please try again."