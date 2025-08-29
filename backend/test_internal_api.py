#!/usr/bin/env python3
"""Test resume API internally to verify job_title field"""

import asyncio
import json
from sqlalchemy import select
from app.db import async_session_maker
from app.models_db import User, Resume
from app.internal_api import get_resume_data_internal

async def test_internal_api():
    """Test that internal resume API returns job_title field"""
    async with async_session_maker() as db:
        # Get a test user
        result = await db.execute(select(User).limit(1))
        user = result.scalars().first()
        
        if not user:
            print("❌ No users found")
            return
            
        print(f"✅ Testing with user: {user.name}")
        
        # Call the internal API
        resume_data = await get_resume_data_internal(user, db)
        
        print("✅ Internal API call successful")
        
        # Check for job_title
        if 'job_title' in resume_data:
            print(f"✅ job_title field found: '{resume_data['job_title']}'")
        else:
            print("❌ job_title field NOT found in API response")
            
        # Show structure
        print("\n📋 API Response structure:")
        structure = {
            "personalInfo": "present" if "personalInfo" in resume_data else "missing",
            "job_title": resume_data.get("job_title", "MISSING"),
            "experience": f"{len(resume_data.get('experience', []))} items",
            "education": f"{len(resume_data.get('education', []))} items",
            "skills": f"{len(resume_data.get('skills', []))} items"
        }
        print(json.dumps(structure, indent=2))

if __name__ == "__main__":
    asyncio.run(test_internal_api())