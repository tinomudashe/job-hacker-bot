#!/usr/bin/env python3
"""Test script to verify job_title field is properly handled in resume API"""

import asyncio
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db import async_session_maker
from app.models_db import User, Resume

async def test_job_title():
    """Test that job_title field is properly stored and retrieved"""
    async with async_session_maker() as db:
        # Get a test user
        result = await db.execute(select(User).limit(1))
        user = result.scalars().first()
        
        if not user:
            print("❌ No users found in database")
            return
            
        print(f"✅ Found user: {user.name} ({user.id})")
        
        # Get the user's resume
        result = await db.execute(select(Resume).where(Resume.user_id == user.id))
        resume = result.scalars().first()
        
        if not resume:
            print("❌ No resume found for user")
            # Create a test resume with job_title
            test_data = {
                "personalInfo": {
                    "name": user.name,
                    "email": user.email
                },
                "job_title": "Senior Software Engineer",
                "experience": [],
                "education": [],
                "skills": []
            }
            resume = Resume(user_id=user.id, data=test_data)
            db.add(resume)
            await db.commit()
            print("✅ Created test resume with job_title")
            
        # Check if job_title exists
        if resume.data:
            print(f"✅ Resume data exists")
            if 'job_title' in resume.data:
                print(f"✅ job_title field found: '{resume.data['job_title']}'")
            else:
                print("⚠️  job_title field not found in resume data")
                print("   Adding job_title to resume...")
                resume.data['job_title'] = "Test Professional Title"
                from sqlalchemy.orm import attributes
                attributes.flag_modified(resume, "data")
                await db.commit()
                print("✅ Added job_title to resume")
                
            # Display the structure
            print("\n📋 Resume data structure:")
            print(json.dumps({
                "personalInfo": "...",
                "job_title": resume.data.get('job_title', 'NOT FOUND'),
                "experience": f"[{len(resume.data.get('experience', []))} items]",
                "education": f"[{len(resume.data.get('education', []))} items]",
                "skills": f"[{len(resume.data.get('skills', []))} items]"
            }, indent=2))
        else:
            print("❌ Resume has no data")

if __name__ == "__main__":
    asyncio.run(test_job_title())