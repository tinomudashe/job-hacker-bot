from langchain_core.tools import tool
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models_db import User, Resume
from app.resume import ResumeData, fix_resume_data_structure
from ._try_browser_extraction import _try_browser_extraction
from ._try_basic_extraction import _try_basic_extraction

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

log = logging.getLogger(__name__)


@tool
async def get_interview_preparation_guide(
    db: AsyncSession,
    user: User,
    job_title: str = "",
    company_name: str = "",
    interview_type: str = "general",
    job_url: str = ""
) -> str:
    """Get comprehensive interview preparation guidance based on your CV and target role.
    
    Args:
        job_title: Position you're interviewing for (optional if job_url provided)
        company_name: Target company (optional if job_url provided)
        interview_type: Type of interview (behavioral, technical, panel, phone, video)
        job_url: URL of the job posting to analyze (optional, will extract job details)
    
    Returns:
        Personalized interview preparation guide with questions and strategies
    """
    try:
        # Extract job details from URL if provided
        extracted_job_title = job_title
        extracted_company_name = company_name
        job_description = ""
        
        if job_url:
            log.info(f"Extracting job details from URL: {job_url}")
            try:
                # Simplified logic: Always try browser extraction first, then fall back.
                success, extracted_data = await _try_browser_extraction(job_url)
                if not success or not extracted_data:
                    log.warning("Browser extraction failed, falling back to basic extraction.")
                    success, extracted_data = await _try_basic_extraction(job_url)

                if success and extracted_data:
                    extracted_job_title = extracted_data.get("job_title", job_title)
                    extracted_company_name = extracted_data.get("company_name", company_name)
                    job_description = extracted_data.get("job_description", "")
                    log.info(f"Successfully extracted job details: {extracted_job_title} at {extracted_company_name}")

            except Exception as e:
                log.warning(f"URL extraction failed: {e}, using provided job details")
        
        # Use extracted details or fallback to provided ones
        final_job_title = extracted_job_title or job_title
        final_company_name = extracted_company_name or company_name
        
        if not final_job_title:
            return "❌ Please provide either a job title or a job URL to generate interview preparation guide."
        
        # Get user's CV data for personalized prep
        result = await db.execute(select(Resume).where(Resume.user_id == user.id))
        db_resume = result.scalars().first()
        
        user_context_parts = [f"User: {user.first_name} {user.last_name}"]
        if db_resume and db_resume.data:
            fixed_data = fix_resume_data_structure(db_resume.data)
            resume_data = ResumeData(**fixed_data)
            
            # Build a comprehensive user context
            if resume_data.personalInfo and resume_data.personalInfo.summary:
                user_context_parts.append(f"\n## Professional Summary\n{resume_data.personalInfo.summary}")

            if resume_data.experience:
                user_context_parts.append("\n## Work Experience")
                for exp in resume_data.experience:
                    exp_str = f"- **{exp.jobTitle}** at **{exp.company}** ({exp.dates})\n  {exp.description}"
                    user_context_parts.append(exp_str)

            if resume_data.education:
                user_context_parts.append("\n## Education")
                for edu in resume_data.education:
                    edu_str = f"- **{edu.degree}** from **{edu.institution}** ({edu.dates})"
                    user_context_parts.append(edu_str)

            if resume_data.skills:
                user_context_parts.append(f"\n## Skills\n{', '.join(resume_data.skills)}")

            if resume_data.projects:
                user_context_parts.append("\n## Projects")
                for proj in resume_data.projects:
                    proj_str = f"- **{proj.name}**: {proj.description}"
                    user_context_parts.append(proj_str)
        
        user_context = "\n".join(user_context_parts)
        
        prompt = ChatPromptTemplate.from_template(
            """You are an expert interview coach. Create a comprehensive, personalized interview preparation guide.

USER CONTEXT: {user_context}
TARGET ROLE: {job_title}
COMPANY: {company_name}
INTERVIEW TYPE: {interview_type}
JOB DESCRIPTION: {job_description}

Create a detailed interview preparation guide:

## 🎯 **Role-Specific Preparation**
### Key Competencies to Highlight
- Core skills most relevant to this role
- How to connect your background to role requirements
- Unique value propositions to emphasize
- Potential concerns to address proactively

### Industry Context
- Current trends and challenges in the industry
- Company-specific research points
- Market positioning and competitive landscape
- Recent news or developments to mention

## 💬 **Expected Interview Questions**
### Behavioral Questions (STAR Method)
- 5-7 likely behavioral questions for this role
- Frameworks for structuring responses
- How to use your CV experiences effectively
- Stories to prepare from your background

### Technical/Role-Specific Questions
- Technical skills assessments to expect
- Problem-solving scenarios relevant to the role
- Industry knowledge questions
- Portfolio or work sample discussions

### Situational Questions
- Hypothetical scenarios for this position
- Leadership and teamwork examples
- Conflict resolution situations
- Decision-making frameworks

## 🤝 **Company Research Strategy**
### Essential Research Areas
- Company mission, values, and culture
- Recent achievements and challenges
- Leadership team and organizational structure
- Products, services, and market position

### Research Sources
- Official company resources
- Industry publications and news
- Employee insights (LinkedIn, Glassdoor)
- Social media and recent announcements

## ❓ **Questions to Ask Them**
### Role and Responsibilities
- Thoughtful questions about the position
- Team dynamics and collaboration
- Success metrics and expectations
- Growth opportunities and career path

### Company and Culture
- Strategic questions about company direction
- Culture and work environment inquiries
- Professional development opportunities
- Industry challenges and opportunities

## 🎭 **Interview Performance Tips**
### Communication Strategies
- How to present your CV experiences compellingly
- Confidence-building techniques
- Body language and presentation tips
- Virtual interview best practices (if applicable)

### Common Pitfalls to Avoid
- Red flags that hurt candidates
- How to handle difficult questions
- Salary and compensation discussions
- Follow-up and next steps etiquette

## 📋 **Preparation Checklist**
### Before the Interview
- Documents and materials to prepare
- Questions and answers to practice
- Research tasks to complete
- Logistics and setup considerations

### Day of Interview
- Final preparation steps
- What to bring/have ready
- Timing and arrival guidelines
- Backup plans for technical issues

Provide specific, actionable advice tailored to this role and the user's background."""
        )
        
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-pro-preview-03-25",
            temperature=0.3
        )
        
        chain = prompt | llm | StrOutputParser()
        
        guide = await chain.ainvoke({
            "user_context": user_context,
            "job_title": final_job_title,
            "company_name": final_company_name or "the target company",
            "interview_type": interview_type,
            "job_description": job_description or "No specific job description provided"
        })
        
        # Generate structured Q&A pairs for flashcards
        qa_prompt = ChatPromptTemplate.from_template(
            """Generate 10 realistic interview questions and answers for this role, including CV-specific questions.

USER CONTEXT: {user_context}
TARGET ROLE: {job_title}
COMPANY: {company_name}
INTERVIEW TYPE: {interview_type}
JOB DESCRIPTION: {job_description}

**CRITICAL: Analyze the user's CV/background and the job description to create questions that reference their SPECIFIC experience:**

Generate exactly 10 interview questions with sample answers. Return as JSON array:
[
    {{
    "question": "Tell me about yourself.",
    "answer": "Brief sample answer that the candidate could reference or build upon"
    }},
    ...
]

Include this mix:
- 2 CV-specific questions (reference their actual experience, career transitions, specific technologies/companies)
- 2 behavioral questions (STAR method opportunities)
- 3 technical/role-specific questions
- 2 situational questions
- 1 company/culture fit question

**CV-SPECIFIC QUESTION EXAMPLES (adapt to their actual background):**
- "I see you were doing freelance work while working full-time at [Company]. How did you manage both responsibilities?"
- "You used [Technology] at [Company]. Can you walk me through how you implemented it?"
- "I notice you transitioned from [Previous Role] to [Current Role]. What motivated this change?"
- "You worked at [Company] for [Duration]. What was your biggest achievement there?"
- "I see you have experience with [Specific Skill/Technology]. How did you learn it and apply it?"
- "You've worked in both [Industry A] and [Industry B]. How do those experiences complement each other?"

**IMPORTANT RULES:**
1. Reference ACTUAL companies, technologies, roles from their background
2. Ask about career transitions, overlapping roles, technology choices
3. Question specific timeframes, gaps, or interesting patterns in their CV
4. Make questions sound like a real interviewer who studied their resume
5. Include follow-up style questions that dig deeper into their experience

"""
        )
        
        qa_chain = qa_prompt | llm | StrOutputParser()
        
        qa_json_str = await qa_chain.ainvoke({
            "user_context": user_context,
            "job_title": final_job_title,
            "company_name": final_company_name or "the target company",
            "interview_type": interview_type,
            "job_description": job_description or "No specific job description provided"
        })

        # Format the final response
        final_response = (
            f"Of course! Here is your interview preparation guide for the "
            f"**{final_job_title}** position at **{final_company_name}**.\n\n"
            f"[INTERVIEW_FLASHCARDS_AVAILABLE]\n"
            f"<!--FLASHCARD_DATA:{qa_json_str}-->\n\n"
            f"{guide}"
        )
        
        return final_response

    except Exception as e:
        log.error(f"Error generating interview guide: {e}", exc_info=True)
        return "❌ I'm sorry, but I encountered an error while trying to generate the interview preparation guide. Please try again."
