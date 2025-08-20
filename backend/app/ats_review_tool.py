"""
ATS Resume Review Tool
Analyzes resumes for ATS compatibility and provides improvement suggestions
"""

from typing import Dict, List, Any, Optional
from langchain_core.tools import tool
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
import re
import json
from datetime import datetime


class ATSReviewTool:
    """Tool for reviewing resumes for ATS compatibility"""
    
    def __init__(self):
        self.llm = ChatAnthropic(
            model="claude-3-7-sonnet-20250219",
            temperature=0.3,
            max_tokens=4000
        )
        
    def calculate_ats_score(self, resume_text: str) -> Dict[str, Any]:
        """Calculate ATS score based on various factors"""
        
        score_breakdown = {
            "formatting": 0,
            "keywords": 0,
            "sections": 0,
            "readability": 0,
            "contact_info": 0,
            "skills": 0,
            "experience": 0,
            "achievements": 0
        }
        
        total_score = 0
        max_score = 100
        
        # Check formatting (20 points)
        if not self._has_complex_formatting(resume_text):
            score_breakdown["formatting"] = 20
        else:
            score_breakdown["formatting"] = 10
            
        # Check for standard sections (15 points)
        sections_score = 0
        required_sections = ["experience", "education", "skills"]
        optional_sections = ["summary", "objective", "projects", "certifications"]
        
        for section in required_sections:
            if section.lower() in resume_text.lower():
                sections_score += 5
                
        for section in optional_sections:
            if section.lower() in resume_text.lower():
                sections_score += 2
                
        score_breakdown["sections"] = min(sections_score, 15)
        
        # Check contact information (10 points)
        contact_score = 0
        if re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', resume_text):
            contact_score += 5  # Email found
        if re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', resume_text):
            contact_score += 3  # Phone found
        if re.search(r'linkedin\.com/in/[\w-]+', resume_text, re.IGNORECASE):
            contact_score += 2  # LinkedIn found
            
        score_breakdown["contact_info"] = contact_score
        
        # Check for quantified achievements (15 points)
        achievement_patterns = [
            r'\d+%',  # Percentages
            r'\$[\d,]+',  # Dollar amounts
            r'\d+\+?\s*(years?|months?|weeks?)',  # Time periods
            r'(increased|decreased|improved|reduced|saved|generated).*\d+',
        ]
        
        achievement_count = 0
        for pattern in achievement_patterns:
            matches = re.findall(pattern, resume_text, re.IGNORECASE)
            achievement_count += len(matches)
            
        score_breakdown["achievements"] = min(achievement_count * 2, 15)
        
        # Check readability (10 points)
        if self._check_readability(resume_text):
            score_breakdown["readability"] = 10
        else:
            score_breakdown["readability"] = 5
            
        # Skills section check (15 points)
        skills_mentioned = self._count_technical_skills(resume_text)
        score_breakdown["skills"] = min(skills_mentioned * 3, 15)
        
        # Experience formatting (15 points)
        if self._check_experience_format(resume_text):
            score_breakdown["experience"] = 15
        else:
            score_breakdown["experience"] = 7
            
        # Calculate total score
        total_score = sum(score_breakdown.values())
        
        return {
            "total_score": total_score,
            "max_score": max_score,
            "score_breakdown": score_breakdown,
            "grade": self._get_grade(total_score)
        }
    
    def _has_complex_formatting(self, text: str) -> bool:
        """Check for complex formatting that ATS might struggle with"""
        complex_indicators = [
            "│", "┌", "└", "├", "┤", "─", "━",  # Box drawing characters
            "★", "◆", "●", "▪", "▫", "◊",  # Special bullets
            "🎯", "💼", "📧", "📱", "🔗",  # Emojis
        ]
        
        for indicator in complex_indicators:
            if indicator in text:
                return True
        return False
    
    def _check_readability(self, text: str) -> bool:
        """Check if text is readable and well-structured"""
        lines = text.split('\n')
        
        # Check for reasonable line lengths
        long_lines = sum(1 for line in lines if len(line) > 150)
        
        # Check for proper spacing
        empty_lines = sum(1 for line in lines if line.strip() == '')
        
        return long_lines < 5 and empty_lines > 3
    
    def _count_technical_skills(self, text: str) -> int:
        """Count technical skills mentioned"""
        common_skills = [
            "python", "java", "javascript", "react", "node", "sql", "aws",
            "docker", "kubernetes", "git", "agile", "scrum", "typescript",
            "html", "css", "api", "rest", "graphql", "mongodb", "postgresql",
            "machine learning", "data analysis", "excel", "project management"
        ]
        
        text_lower = text.lower()
        count = 0
        for skill in common_skills:
            if skill in text_lower:
                count += 1
                
        return count
    
    def _check_experience_format(self, text: str) -> bool:
        """Check if experience section is well-formatted"""
        # Look for date patterns
        date_patterns = [
            r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}',
            r'\b\d{1,2}/\d{4}',
            r'\b\d{4}\s*-\s*\d{4}',
            r'\b\d{4}\s*-\s*Present',
        ]
        
        date_count = 0
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            date_count += len(matches)
            
        return date_count >= 2
    
    def _get_grade(self, score: int) -> str:
        """Convert score to grade"""
        if score >= 90:
            return "A+"
        elif score >= 85:
            return "A"
        elif score >= 80:
            return "A-"
        elif score >= 75:
            return "B+"
        elif score >= 70:
            return "B"
        elif score >= 65:
            return "B-"
        elif score >= 60:
            return "C+"
        elif score >= 55:
            return "C"
        elif score >= 50:
            return "C-"
        else:
            return "D"
    
    async def generate_improvements(self, resume_text: str, score_data: Dict[str, Any]) -> List[str]:
        """Generate specific improvement suggestions using AI"""
        
        system_prompt = """You are an expert ATS (Applicant Tracking System) consultant and resume optimization specialist.
        Analyze the resume and provide specific, actionable improvements to increase ATS compatibility and score.
        Focus on:
        1. Keyword optimization
        2. Formatting improvements
        3. Section organization
        4. Quantifiable achievements
        5. Skills presentation
        6. Experience descriptions
        
        Provide 5-8 specific, actionable suggestions."""
        
        human_prompt = f"""Based on this ATS score breakdown:
        
        Total Score: {score_data['total_score']}/{score_data['max_score']} (Grade: {score_data['grade']})
        
        Score Breakdown:
        - Formatting: {score_data['score_breakdown']['formatting']}/20
        - Keywords: {score_data['score_breakdown']['keywords']}/0
        - Sections: {score_data['score_breakdown']['sections']}/15
        - Readability: {score_data['score_breakdown']['readability']}/10
        - Contact Info: {score_data['score_breakdown']['contact_info']}/10
        - Skills: {score_data['score_breakdown']['skills']}/15
        - Experience: {score_data['score_breakdown']['experience']}/15
        - Achievements: {score_data['score_breakdown']['achievements']}/15
        
        Resume Content:
        {resume_text[:3000]}...
        
        Provide specific improvement suggestions to increase the ATS score.
        Format as a JSON list of strings, each being one specific suggestion."""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        
        try:
            # Extract JSON from response
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
                
            suggestions = json.loads(content)
            if isinstance(suggestions, list):
                return suggestions[:8]  # Return max 8 suggestions
        except:
            # Fallback to basic suggestions
            pass
            
        return self._generate_basic_suggestions(score_data)
    
    def _generate_basic_suggestions(self, score_data: Dict[str, Any]) -> List[str]:
        """Generate basic suggestions based on score breakdown"""
        suggestions = []
        breakdown = score_data['score_breakdown']
        
        if breakdown['formatting'] < 15:
            suggestions.append("🔧 Remove special characters, graphics, and complex formatting. Use standard bullets (•) and simple layouts.")
            
        if breakdown['sections'] < 10:
            suggestions.append("📋 Add missing standard sections: Experience, Education, Skills. Consider adding Summary or Objective.")
            
        if breakdown['contact_info'] < 8:
            suggestions.append("📧 Ensure your email, phone number, and LinkedIn URL are clearly visible at the top of your resume.")
            
        if breakdown['achievements'] < 10:
            suggestions.append("📊 Add quantifiable achievements with numbers, percentages, or dollar amounts (e.g., 'Increased sales by 25%').")
            
        if breakdown['skills'] < 10:
            suggestions.append("💻 Expand your skills section with relevant technical skills, tools, and technologies for your target role.")
            
        if breakdown['experience'] < 12:
            suggestions.append("💼 Format experience consistently with company name, job title, dates (Month Year - Month Year), and bullet points.")
            
        if breakdown['readability'] < 8:
            suggestions.append("📖 Improve readability with shorter sentences, consistent formatting, and proper white space between sections.")
            
        suggestions.append("🎯 Tailor your resume keywords to match the specific job description you're applying for.")
        
        return suggestions[:8]


# Create the tool function for LangChain
@tool
async def review_resume_ats(resume_text: str) -> str:
    """
    Review a resume for ATS (Applicant Tracking System) compatibility.
    
    This tool:
    1. Analyzes the resume for ATS-friendly formatting
    2. Calculates an ATS score (0-100)
    3. Provides a detailed breakdown of scoring
    4. Offers specific improvement suggestions
    
    Args:
        resume_text: The full text content of the resume to review
        
    Returns:
        A formatted report with ATS score and improvement suggestions
    """
    
    tool = ATSReviewTool()
    
    # Calculate ATS score
    score_data = tool.calculate_ats_score(resume_text)
    
    # Generate improvement suggestions
    suggestions = await tool.generate_improvements(resume_text, score_data)
    
    # Format the response
    response = f"""# 📊 ATS Resume Review Report

## Overall Score: {score_data['total_score']}/{score_data['max_score']} ({score_data['grade']})

### Score Breakdown:
- **Formatting**: {score_data['score_breakdown']['formatting']}/20
- **Standard Sections**: {score_data['score_breakdown']['sections']}/15
- **Contact Information**: {score_data['score_breakdown']['contact_info']}/10
- **Readability**: {score_data['score_breakdown']['readability']}/10
- **Skills Section**: {score_data['score_breakdown']['skills']}/15
- **Experience Format**: {score_data['score_breakdown']['experience']}/15
- **Quantified Achievements**: {score_data['score_breakdown']['achievements']}/15

### 🎯 ATS Optimization Level:
"""
    
    if score_data['total_score'] >= 80:
        response += "✅ **Excellent** - Your resume is highly ATS-compatible!"
    elif score_data['total_score'] >= 70:
        response += "🟢 **Good** - Your resume is ATS-friendly with room for improvement."
    elif score_data['total_score'] >= 60:
        response += "🟡 **Fair** - Your resume needs some optimization for better ATS performance."
    else:
        response += "🔴 **Needs Improvement** - Significant changes recommended for ATS compatibility."
    
    response += "\n\n### 💡 Improvement Suggestions:\n"
    
    for i, suggestion in enumerate(suggestions, 1):
        response += f"\n{i}. {suggestion}"
    
    response += """

### 📝 Quick ATS Tips:
- Use standard section headings (Experience, Education, Skills)
- Include keywords from the job description
- Use standard fonts (Arial, Calibri, Times New Roman)
- Save as .docx or .pdf (text-based, not image)
- Avoid tables, columns, headers/footers
- Use standard bullet points
- Include both acronyms and full terms (e.g., "SQL (Structured Query Language)")

**Note**: For best results, tailor your resume for each specific job application by matching keywords from the job description."""
    
    return response


# Additional tool for comparing resume against job description
@tool
async def compare_resume_to_job(resume_text: str, job_description: str) -> str:
    """
    Compare a resume against a specific job description for ATS optimization.
    
    Args:
        resume_text: The full text content of the resume
        job_description: The job description to compare against
        
    Returns:
        A detailed analysis of keyword matches and recommendations
    """
    
    llm = ChatAnthropic(
        model="claude-3-7-sonnet-20250219",
        temperature=0.3,
        max_tokens=2000
    )
    
    system_prompt = """You are an ATS optimization expert. Analyze the resume against the job description and provide:
    1. Keyword match analysis
    2. Missing critical skills/qualifications
    3. Suggestions for better alignment
    4. Overall match percentage
    
    Format the response in a clear, actionable way."""
    
    human_prompt = f"""Compare this resume to the job description:
    
    RESUME:
    {resume_text[:2000]}
    
    JOB DESCRIPTION:
    {job_description[:2000]}
    
    Provide a detailed ATS optimization analysis."""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_prompt)
    ]
    
    response = await llm.ainvoke(messages)
    
    return f"""# 🎯 Resume-Job Match Analysis

{response.content}

### Next Steps:
1. Update your resume with missing keywords
2. Align your experience descriptions with job requirements
3. Ensure all required skills are prominently featured
4. Rerun the ATS review after making changes"""


# Export the tools
__all__ = ['review_resume_ats', 'compare_resume_to_job']