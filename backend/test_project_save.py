#!/usr/bin/env python3
"""
Test project saving functionality
"""
import asyncio
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models_db import Resume, User
from app.db import async_session_maker
from sqlalchemy import select, update
import uuid

async def test_project_saving():
    """Test if projects are saved correctly"""
    async with async_session_maker() as db:
        try:
            # Get a user to test with
            result = await db.execute(select(User).limit(1))
            user = result.scalars().first()
            
            if not user:
                print("No users found in database")
                return
            
            print(f"Testing with user: {user.id}")
            
            # Get or create resume
            result = await db.execute(select(Resume).where(Resume.user_id == user.id))
            resume = result.scalars().first()
            
            if not resume:
                # Create new resume
                resume = Resume(user_id=user.id, data={})
                db.add(resume)
                await db.flush()
                print("Created new resume")
            
            # Test project data structure that frontend sends
            test_projects = [
                {
                    "title": "Test Project 1",  # Using 'title' as frontend now sends
                    "description": "This is a test project description with bullet points:\n• Feature 1\n• Feature 2\n• Feature 3",
                    "technologies": ["React", "TypeScript", "Node.js"],
                    "url": "https://github.com/test/project1"
                },
                {
                    "title": "Test Project 2",
                    "description": "Another test project",
                    "technologies": ["Python", "FastAPI"],
                    "url": ""
                }
            ]
            
            # Update resume with test projects
            current_data = resume.data or {}
            current_data["projects"] = test_projects
            
            print(f"Before save - projects: {current_data.get('projects', [])}")
            
            # Apply the same fix_resume_data_structure that the API uses
            from app.resume import fix_resume_data_structure
            fixed_data = fix_resume_data_structure(current_data)
            
            print(f"After fix_resume_data_structure - projects: {fixed_data.get('projects', [])}")
            
            resume.data = fixed_data
            await db.commit()
            
            print("✅ Successfully saved projects:")
            for i, proj in enumerate(test_projects):
                print(f"  {i+1}. {proj['title']}")
            
            # Verify save by reading back from database
            result = await db.execute(select(Resume).where(Resume.user_id == user.id))
            verified_resume = result.scalars().first()
            saved_projects = verified_resume.data.get("projects", []) if verified_resume else []
            
            print(f"\n✅ Verified: {len(saved_projects)} projects saved in database")
            for i, proj in enumerate(saved_projects):
                print(f"  {i+1}. Title: {proj.get('title', 'MISSING')}")
                print(f"      Description: {proj.get('description', 'MISSING')[:50]}...")
                print(f"      Technologies: {proj.get('technologies', [])}")
                print(f"      URL: {proj.get('url', 'MISSING')}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error testing project save: {e}")
            await db.rollback()
            return False

if __name__ == "__main__":
    success = asyncio.run(test_project_saving())
    sys.exit(0 if success else 1)