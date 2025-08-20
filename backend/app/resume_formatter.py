"""
Resume Content Formatter
Utilities for formatting resume content to be more concise and readable
"""

import re
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class ResumeFormatter:
    """Helper class for formatting resume content"""
    
    @staticmethod
    def format_bullet_points(text: str, max_points: int = 4, max_length: int = 90) -> List[str]:
        """
        Convert text into concise bullet points
        
        Args:
            text: Raw text to format
            max_points: Maximum number of bullet points to return
            max_length: Maximum length of each bullet point
            
        Returns:
            List of formatted bullet points
        """
        if not text:
            return []
        
        # Remove common filler phrases
        filler_phrases = [
            r'^(Responsible for|Managed to|Helped to|Worked on|Assisted with)\s+',
            r'^(Successfully|Effectively|Efficiently|Actively)\s+',
            r'^(Was involved in|Participated in|Contributed to)\s+',
        ]
        
        # Split text into potential bullet points
        # Try multiple delimiters
        points = re.split(r'[•\-\n]|(?:\. (?=[A-Z]))', text)
        
        formatted_points = []
        for point in points:
            # Clean the point
            point = point.strip()
            if not point or len(point) < 10:  # Skip very short points
                continue
            
            # Remove filler phrases
            for phrase in filler_phrases:
                point = re.sub(phrase, '', point, flags=re.IGNORECASE)
            
            # Ensure it starts with a capital letter
            if point and point[0].islower():
                point = point[0].upper() + point[1:]
            
            # Ensure it ends with proper punctuation
            if point and not point[-1] in '.!?':
                point += '.'
            
            # Truncate if too long
            if len(point) > max_length:
                # Try to find a natural break point
                break_point = point.rfind(' ', 0, max_length)
                if break_point > max_length * 0.7:  # Only break if we're not losing too much
                    point = point[:break_point].rstrip('.,;') + '...'
                else:
                    point = point[:max_length-3] + '...'
            
            formatted_points.append(point)
            
            if len(formatted_points) >= max_points:
                break
        
        return formatted_points
    
    @staticmethod
    def format_job_description(description: str) -> str:
        """
        Format a job description into concise bullet points
        
        Args:
            description: Raw job description text
            
        Returns:
            Formatted description with bullet points
        """
        points = ResumeFormatter.format_bullet_points(description, max_points=4, max_length=90)
        
        if not points:
            return description[:200] + '...' if len(description) > 200 else description
        
        return '\n'.join(f'• {point}' for point in points)
    
    @staticmethod
    def format_skills(skills: List[str], max_skills: int = 12) -> List[str]:
        """
        Format and prioritize skills list
        
        Args:
            skills: List of skills
            max_skills: Maximum number of skills to include
            
        Returns:
            Formatted and prioritized skills list
        """
        if not skills:
            return []
        
        # Remove duplicates while preserving order
        seen = set()
        unique_skills = []
        for skill in skills:
            skill_lower = skill.lower().strip()
            if skill_lower not in seen:
                seen.add(skill_lower)
                unique_skills.append(skill.strip())
        
        # Prioritize technical skills and certifications
        priority_keywords = ['python', 'javascript', 'java', 'react', 'aws', 'docker', 
                           'kubernetes', 'sql', 'agile', 'scrum', 'certified', 'professional']
        
        prioritized = []
        remaining = []
        
        for skill in unique_skills:
            if any(keyword in skill.lower() for keyword in priority_keywords):
                prioritized.append(skill)
            else:
                remaining.append(skill)
        
        # Combine prioritized and remaining, up to max_skills
        final_skills = prioritized[:max_skills]
        if len(final_skills) < max_skills:
            final_skills.extend(remaining[:max_skills - len(final_skills)])
        
        return final_skills
    
    @staticmethod
    def format_project_description(description: str, max_length: int = 120) -> str:
        """
        Format project description to be concise and impactful
        
        Args:
            description: Raw project description
            max_length: Maximum length of description
            
        Returns:
            Formatted project description
        """
        if not description:
            return ""
        
        # Remove unnecessary words
        description = re.sub(r'\b(very|really|quite|just|basically|simply)\b', '', description, flags=re.IGNORECASE)
        description = ' '.join(description.split())  # Clean up extra spaces
        
        # Focus on key achievements and technologies
        if len(description) > max_length:
            # Try to preserve complete sentences
            sentences = description.split('. ')
            result = ""
            for sentence in sentences:
                if len(result) + len(sentence) + 2 <= max_length:
                    result += sentence + ". "
                else:
                    if not result:  # If first sentence is too long
                        result = sentence[:max_length-3] + "..."
                    break
            description = result.rstrip()
        
        return description
    
    @staticmethod
    def format_certification(cert_name: str, org: str, date: Optional[str] = None) -> dict:
        """
        Format certification information
        
        Args:
            cert_name: Name of certification
            org: Issuing organization
            date: Date issued (optional)
            
        Returns:
            Formatted certification dict
        """
        # Shorten common certification names
        cert_abbreviations = {
            'Amazon Web Services': 'AWS',
            'Google Cloud Platform': 'GCP',
            'Microsoft Azure': 'Azure',
            'Project Management Professional': 'PMP',
            'Certified Information Systems Security Professional': 'CISSP',
            'Certified Scrum Master': 'CSM',
        }
        
        for full_name, abbrev in cert_abbreviations.items():
            if full_name in cert_name:
                cert_name = cert_name.replace(full_name, abbrev)
        
        # Format date to be more concise
        if date:
            # Try to extract just year or month/year
            import re
            year_match = re.search(r'\b(20\d{2})\b', date)
            if year_match:
                date = year_match.group(1)
        
        return {
            'name': cert_name,
            'issuing_organization': org,
            'date_issued': date
        }
    
    @staticmethod
    def format_language_proficiency(language: str, proficiency: str) -> dict:
        """
        Format language and proficiency level
        
        Args:
            language: Language name
            proficiency: Proficiency level description
            
        Returns:
            Formatted language dict with standardized proficiency
        """
        # Standardize proficiency levels
        proficiency_map = {
            'native speaker': 'Native',
            'native': 'Native',
            'fluent': 'Fluent',
            'advanced': 'Professional',
            'professional': 'Professional',
            'intermediate': 'Intermediate',
            'conversational': 'Intermediate',
            'basic': 'Basic',
            'beginner': 'Basic',
            'elementary': 'Basic'
        }
        
        # Normalize proficiency
        prof_lower = proficiency.lower().strip()
        for key, value in proficiency_map.items():
            if key in prof_lower:
                proficiency = value
                break
        
        # If not found in map, try to determine from description
        if proficiency not in proficiency_map.values():
            if any(word in prof_lower for word in ['excellent', 'proficient', 'working']):
                proficiency = 'Professional'
            elif any(word in prof_lower for word in ['good', 'moderate']):
                proficiency = 'Intermediate'
            else:
                proficiency = 'Intermediate'  # Default
        
        return {
            'name': language.title(),
            'proficiency': proficiency
        }


# Example usage and testing
if __name__ == "__main__":
    formatter = ResumeFormatter()
    
    # Test bullet point formatting
    test_description = """
    Responsible for managing a team of 10 developers to deliver high-quality software solutions.
    Successfully implemented new CI/CD pipeline that reduced deployment time by 50%.
    Worked on improving code quality through code reviews and establishing best practices.
    Helped to mentor junior developers and conducted technical interviews.
    """
    
    points = formatter.format_bullet_points(test_description)
    print("Formatted bullet points:")
    for point in points:
        print(f"  • {point}")
    
    # Test skills formatting
    test_skills = ["Python", "JavaScript", "React", "Node.js", "AWS", "Docker", "Git", 
                   "Agile", "SQL", "MongoDB", "REST APIs", "GraphQL", "TypeScript", 
                   "Kubernetes", "CI/CD", "Testing"]
    
    formatted_skills = formatter.format_skills(test_skills, max_skills=10)
    print(f"\nFormatted skills: {formatted_skills}")
    
    # Test project description
    test_project = "Developed a very comprehensive web application using React and Node.js that basically helps users manage their tasks and projects. The application includes features like real-time collaboration, task assignments, deadline tracking, and reporting capabilities."
    
    formatted_project = formatter.format_project_description(test_project)
    print(f"\nFormatted project: {formatted_project}")