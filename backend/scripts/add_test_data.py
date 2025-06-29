import asyncio
import os
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from dotenv import load_dotenv
from datetime import datetime, timezone
import uuid

# Add the parent directory to Python path so we can import from app
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from app.db import async_session_maker
from app.models_db import User, Document, Application

async def add_test_data():
    async with async_session_maker() as db:
        # Find our test user
        user_result = await db.execute(select(User).where(User.external_id == 'hmcRCt3f35DJC2NF0iVipwgrub1jlgTS@clients'))
        user = user_result.scalar_one_or_none()
        
        if not user:
            print("Test user not found!")
            return

        # Add a test document
        test_doc = Document(
            id=str(uuid.uuid4()),
            user_id=user.id,
            name="Sample Resume.pdf",
            type="resume",
            content="""
            PROFESSIONAL SUMMARY
            Senior Software Engineer with 6+ years of experience in Python development and cloud technologies.
            Expertise in building scalable microservices and RESTful APIs using FastAPI and AWS.
            
            EXPERIENCE
            Senior Software Engineer | Google
            - Led development of microservices architecture
            - Implemented CI/CD pipelines
            - Reduced API response times by 40%
            
            EDUCATION
            University of Zimbabwe
            Bachelor of Science in Computer Science
            """,
            date_created=datetime.now(timezone.utc)
        )
        db.add(test_doc)

        # Add some test applications
        applications = [
            Application(
                id=str(uuid.uuid4()),
                user_id=user.id,
                job_title="Senior Python Developer",
                company_name="Amazon",
                job_url="https://amazon.jobs/123",
                status="applied",
                notes="Great initial call with the recruiter",
                date_applied=datetime.now(timezone.utc)
            ),
            Application(
                id=str(uuid.uuid4()),
                user_id=user.id,
                job_title="Backend Engineer",
                company_name="Netflix",
                job_url="https://netflix.jobs/456",
                status="interview",
                notes="Technical interview scheduled",
                date_applied=datetime.now(timezone.utc)
            ),
            Application(
                id=str(uuid.uuid4()),
                user_id=user.id,
                job_title="Software Architect",
                company_name="Microsoft",
                job_url="https://microsoft.jobs/789",
                status="rejected",
                notes="Position was filled internally",
                date_applied=datetime.now(timezone.utc)
            )
        ]
        
        for app in applications:
            db.add(app)

        await db.commit()
        print("Test data added successfully!")

if __name__ == "__main__":
    load_dotenv()
    asyncio.run(add_test_data()) 