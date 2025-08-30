"""
Professional Summary Enhancer
Automatically refines and improves professional summaries for CVs/resumes
"""

import re
import logging
from typing import Optional, Dict, Any
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

logger = logging.getLogger(__name__)

class SummaryEnhancer:
    """Enhances professional summaries for CVs and resumes"""
    
    def __init__(self):
        self.llm = ChatAnthropic(
            model="claude-3-7-sonnet-20250219",
            temperature=0.2,
            max_tokens=150  # Reduced to force concise summaries
        )
    
    async def enhance_summary(
        self,
        current_summary: str,
        user_data: Dict[str, Any],
        target_role: Optional[str] = None,
        job_description: Optional[str] = None
    ) -> str:
        """
        Enhance a professional summary to be more impactful and tailored
        
        Args:
            current_summary: The existing summary (if any)
            user_data: User's resume data including experience and skills
            target_role: Target job role (optional)
            job_description: Job description to tailor to (optional)
            
        Returns:
            Enhanced professional summary
        """
        
        # Extract key information from user data
        experience_years = self._calculate_experience_years(user_data)
        top_skills = self._extract_top_skills(user_data)
        recent_role = self._get_recent_role(user_data)
        key_achievements = self._extract_achievements(user_data)
        
        # Build context for enhancement
        context = self._build_context(
            current_summary,
            experience_years,
            top_skills,
            recent_role,
            key_achievements,
            target_role
        )
        
        # Create enhancement prompt
        prompt = ChatPromptTemplate.from_template(
            """You are an expert resume writer specializing in creating impactful professional summaries.
            
            CURRENT SUMMARY (if any):
            {current_summary}
            
            USER CONTEXT:
            - Years of Experience: {experience_years}
            - Recent Role: {recent_role}
            - Top Skills: {top_skills}
            - Key Achievements: {key_achievements}
            
            TARGET POSITION (if specified):
            - Role: {target_role}
            - Company: [COMPANY NAME REMOVED FOR UNIVERSAL APPLICABILITY]
            
            INSTRUCTIONS:
            Create a factual 3-4 sentence professional summary based ONLY on provided information:
            
            1. **Opening Statement**: Start with their actual professional identity
               - Example: "[Role] with X+ years of experience in [actual field]"
               - Use only verifiable information from their background
            
            2. **Core Expertise**: List 2-3 areas they have actually worked in
               - Only mention skills/areas from their real experience
               - Use keywords that appear in their work history
            
            3. **Professional Background**: Summarize their actual experience
               - Reference their real education if relevant
               - Mention industries they've actually worked in
               - State capabilities demonstrated in past roles
            
            STRICT REQUIREMENTS:
            - MAXIMUM 80 words - anything longer will be rejected
            - Keep it exactly 2-3 sentences, no more
            - Base EVERYTHING on their actual experience and education
            - Do not invent achievements or capabilities
            - Do not add metrics unless already provided
            - Write in third person without pronouns
            - NEVER mention specific company names in the summary (remove any reference to target company)
            - NEVER include phrases like "seeking the [position] at [company]" or "position at [company]"
            - Keep it universally applicable to any similar role
            - Focus on factual background, not aspirations or job targeting
            - If information is limited, keep the summary shorter rather than inventing details
            
            Generate ONLY the summary text, no additional commentary:"""
        )
        
        chain = prompt | self.llm | StrOutputParser()
        
        try:
            enhanced_summary = await chain.ainvoke({
                "current_summary": current_summary or "No existing summary",
                "experience_years": experience_years,
                "recent_role": recent_role,
                "top_skills": ", ".join(top_skills[:5]),
                "key_achievements": "\n".join(key_achievements[:3]),
                "target_role": target_role or "Not specified",
                "company_name": "NOT_PROVIDED"
            })
            
            # Clean and validate the summary
            enhanced_summary = self._clean_summary(enhanced_summary)
            
            # Aggressively remove any company name references that slipped through
            enhanced_summary = self._remove_company_references(enhanced_summary)
            
            # Ensure it's not too long
            if len(enhanced_summary.split()) > 100:
                enhanced_summary = self._truncate_summary(enhanced_summary, 100)
            
            logger.info(f"Successfully enhanced summary from {len(current_summary)} to {len(enhanced_summary)} chars")
            return enhanced_summary
            
        except Exception as e:
            logger.error(f"Error enhancing summary: {e}")
            # Return improved version of current summary or a default
            return self._create_fallback_summary(
                current_summary, 
                experience_years, 
                recent_role, 
                top_skills
            )
    
    def _calculate_experience_years(self, user_data: Dict[str, Any]) -> str:
        """Calculate years of experience from resume data"""
        if not user_data.get("experience"):
            return "Entry-level"
        
        experience = user_data["experience"]
        if not experience:
            return "Entry-level"
        
        # Simple calculation based on number of positions
        # Could be enhanced with actual date parsing
        num_positions = len(experience)
        
        if num_positions >= 5:
            return "10+"
        elif num_positions >= 3:
            return "5+"
        elif num_positions >= 2:
            return "3+"
        else:
            return "1-3"
    
    def _extract_top_skills(self, user_data: Dict[str, Any]) -> list:
        """Extract top skills from user data"""
        skills = user_data.get("skills", [])
        
        # Prioritize technical and specialized skills
        priority_keywords = [
            'python', 'javascript', 'java', 'react', 'aws', 'docker',
            'kubernetes', 'machine learning', 'data analysis', 'project management',
            'agile', 'sql', 'cloud', 'devops', 'ai', 'leadership'
        ]
        
        prioritized = []
        remaining = []
        
        for skill in skills:
            skill_lower = skill.lower()
            if any(keyword in skill_lower for keyword in priority_keywords):
                prioritized.append(skill)
            else:
                remaining.append(skill)
        
        return prioritized[:5] + remaining[:3]
    
    def _get_recent_role(self, user_data: Dict[str, Any]) -> str:
        """Get the most recent job title"""
        experience = user_data.get("experience", [])
        if experience and len(experience) > 0:
            return experience[0].get("jobTitle", "Professional")
        return "Professional"
    
    def _extract_achievements(self, user_data: Dict[str, Any]) -> list:
        """Extract key achievements from experience"""
        achievements = []
        experience = user_data.get("experience", [])
        
        for job in experience[:2]:  # Look at last 2 jobs
            description = job.get("description", "")
            # Look for achievement patterns
            lines = description.split('\n')
            for line in lines:
                line = line.strip()
                # Look for quantified achievements
                if any(pattern in line.lower() for pattern in [
                    'increased', 'decreased', 'improved', 'reduced',
                    'achieved', 'delivered', 'led', 'managed',
                    '%', 'revenue', 'cost', 'efficiency'
                ]):
                    achievements.append(line[:100])
                
                if len(achievements) >= 5:
                    break
        
        return achievements
    
    def _build_context(
        self,
        current_summary: str,
        experience_years: str,
        top_skills: list,
        recent_role: str,
        key_achievements: list,
        target_role: Optional[str]
    ) -> Dict[str, Any]:
        """Build context for summary enhancement"""
        return {
            "current_summary": current_summary,
            "experience_years": experience_years,
            "top_skills": top_skills,
            "recent_role": recent_role,
            "key_achievements": key_achievements,
            "target_role": target_role
        }
    
    def _clean_summary(self, summary: str) -> str:
        """Clean and format the enhanced summary"""
        # Remove extra whitespace
        summary = ' '.join(summary.split())
        
        # Remove any markdown or special characters
        summary = re.sub(r'[*_#]', '', summary)
        
        # Ensure it ends with a period
        if summary and not summary[-1] in '.!?':
            summary += '.'
        
        return summary.strip()
    
    def _truncate_summary(self, summary: str, max_words: int) -> str:
        """Truncate summary to maximum word count"""
        words = summary.split()
        if len(words) <= max_words:
            return summary
        
        # Find the last complete sentence within limit
        truncated = ' '.join(words[:max_words])
        last_period = truncated.rfind('.')
        
        if last_period > max_words * 0.7:  # If we have at least 70% of target
            return truncated[:last_period + 1]
        
        return truncated + '...'
    
    def _create_fallback_summary(
        self,
        current_summary: str,
        experience_years: str,
        recent_role: str,
        top_skills: list
    ) -> str:
        """Create a fallback summary if enhancement fails"""
        if current_summary and len(current_summary) > 50:
            # Clean up existing summary
            return self._clean_summary(current_summary)
        
        # Create a basic summary
        skills_str = " and ".join(top_skills[:3]) if top_skills else "multiple domains"
        
        return (
            f"Experienced {recent_role} with {experience_years} years of proven expertise in {skills_str}. "
            f"Demonstrated ability to deliver high-quality solutions and drive project success. "
            f"Seeking opportunities to leverage technical skills and contribute to innovative projects."
        )


class QuickSummaryRefiner:
    """Quick summary refinement without LLM calls for faster processing"""
    
    @staticmethod
    def refine_summary(
        summary: str,
        target_role: Optional[str] = None,
        company_name: Optional[str] = None
    ) -> str:
        """
        Quick refinement of summary without LLM
        
        Args:
            summary: Current summary
            target_role: Target role (optional)
            company_name: Target company (optional)
            
        Returns:
            Refined summary
        """
        if not summary:
            return summary
        
        # Remove weak phrases
        weak_phrases = [
            r'\bresponsible for\b',
            r'\bduties included\b',
            r'\btasks included\b',
            r'\bhelped to\b',
            r'\bassisted with\b',
            r'\bworked on\b'
        ]
        
        refined = summary
        for phrase in weak_phrases:
            refined = re.sub(phrase, '', refined, flags=re.IGNORECASE)
        
        # Add target role/company if specified and not already present
        if target_role and target_role.lower() not in refined.lower():
            # Try to insert it naturally
            refined = refined.replace(
                "Seeking opportunities",
                f"Seeking {target_role} opportunities"
            )
            refined = refined.replace(
                "looking for",
                f"looking for {target_role}"
            )
        
        if company_name and company_name.lower() not in refined.lower():
            # Add company mention if there's a seeking statement
            if "seeking" in refined.lower() or "looking" in refined.lower():
                refined = refined.rstrip('.')
                refined += f", particularly interested in contributing to {company_name}."
        
        # Ensure strong opening
        if not any(refined.lower().startswith(word) for word in [
            'experienced', 'accomplished', 'results-driven', 'innovative',
            'strategic', 'dynamic', 'proven', 'senior', 'expert'
        ]):
            # Add a strong opener based on content
            if 'manager' in refined.lower():
                refined = "Accomplished " + refined
            elif 'developer' in refined.lower() or 'engineer' in refined.lower():
                refined = "Innovative " + refined
            elif 'analyst' in refined.lower():
                refined = "Strategic " + refined
            else:
                refined = "Results-driven " + refined
        
        # Clean up
        refined = ' '.join(refined.split())
        
        # Ensure proper ending
        if refined and not refined[-1] in '.!?':
            refined += '.'
        
        return refined


# Singleton instance for reuse
summary_enhancer = SummaryEnhancer()
quick_refiner = QuickSummaryRefiner()