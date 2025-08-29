#!/usr/bin/env python3
"""Test script to verify skill/experience field filling with character limits"""

import asyncio
import json
from app.chrome_extension_api import FormField, FormFillerService
from app.models_db import User
from sqlalchemy.ext.asyncio import AsyncSession

async def test_skill_field():
    """Test the skill field with 200 character limit"""
    
    # Create a mock field like the one in the screenshot
    test_field = FormField(
        id="skills_field",
        name="relevant_experience",
        label="Please describe your relevant experience/skills for this particular position",
        placeholder="Answer size should be 200 characters or less.",
        type="textarea",
        value="",
        category="questions.skills"
    )
    
    # Mock resume data
    mock_resume = {
        "personalInfo": {
            "name": "Test User",
            "email": "test@example.com",
            "location": "San Francisco, CA, USA"
        },
        "professionalSummary": "Experienced software engineer with expertise in full-stack development, cloud architecture, and machine learning. Proven track record of delivering scalable solutions.",
        "experience": [
            {
                "jobTitle": "Senior Software Engineer",
                "company": "Tech Corp",
                "description": "Led development of microservices architecture using Python, Docker, and Kubernetes. Implemented ML models for recommendation system. Reduced API latency by 40%.",
                "dates": {"start": "2020-01", "end": "2024-01"}
            }
        ],
        "skills": ["Python", "JavaScript", "React", "Node.js", "Docker", "Kubernetes", "AWS", "Machine Learning", "SQL", "MongoDB"]
    }
    
    # Mock job context
    job_context = "Software Engineer position at a tech company"
    
    # Create mock user
    mock_user = type('User', (), {
        'id': 'test123',
        'name': 'Test User',
        'email': 'test@example.com'
    })()
    
    print("Testing skill field with 200 character limit...")
    print(f"Field label: {test_field.label}")
    print(f"Field placeholder: {test_field.placeholder}")
    print(f"Field category: {test_field.category}")
    
    # Test character limit detection
    import re
    full_text = f"{test_field.label or ''} {test_field.placeholder or ''} {test_field.name or ''}".lower()
    print(f"\nFull text for parsing: {full_text}")
    
    char_limit = None
    if 'character' in full_text or 'char' in full_text:
        numbers = re.findall(r'\d+', full_text)
        print(f"Numbers found: {numbers}")
        if numbers:
            for num in numbers:
                num_int = int(num)
                if 50 <= num_int <= 5000:
                    char_limit = num_int
                    break
    
    print(f"Detected character limit: {char_limit}")
    
    # Test prompt generation
    if char_limit:
        prompt = f"""
This field is asking about skills/experience.
Field: {test_field.label}
Character limit: {char_limit}

User context:
- Role: Senior Software Engineer at Tech Corp
- Skills: Python, JavaScript, React, Node.js, Docker, Kubernetes, AWS, Machine Learning
- Experience: Led microservices development, implemented ML models, reduced API latency by 40%

Generate a response that:
1. Is exactly {char_limit} characters or less
2. Highlights the most relevant skills and experience
3. Is specific and compelling
"""
        print(f"\nGenerated prompt preview:\n{prompt[:500]}...")
        
        # Example response that would be generated
        example_response = "Senior Software Engineer with 4+ years building scalable systems. Expert in Python, React, AWS, and ML. Led microservices architecture reducing latency 40%. Strong Docker/Kubernetes experience."
        print(f"\nExample response ({len(example_response)} chars):")
        print(example_response)
        
        if len(example_response) <= char_limit:
            print("✓ Response fits within character limit")
        else:
            print("✗ Response exceeds character limit")

if __name__ == "__main__":
    asyncio.run(test_skill_field())