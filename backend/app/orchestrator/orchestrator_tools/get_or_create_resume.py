from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import attributes
import re

from app.models_db import Resume, User
from app.resume import ResumeData, PersonalInfo, fix_resume_data_structure

async def get_or_create_resume(session: AsyncSession, user: User):
    """
    Helper to get or create a resume for the current user using a specific session.
    This ensures transactional integrity within tools.
    """
    user_id = user.id

    result = await session.execute(select(Resume).where(Resume.user_id == user_id))
    db_resume = result.scalar_one_or_none()

    if db_resume and db_resume.data:
        data_from_db = db_resume.data.copy()
        data_from_db.setdefault('personalInfo', {})
        data_from_db.setdefault('experience', [])
        data_from_db.setdefault('education', [])
        data_from_db.setdefault('skills', [])
        data_from_db.setdefault('projects', [])
        data_from_db.setdefault('certifications', [])
        data_from_db.setdefault('languages', [])
        data_from_db.setdefault('interests', [])

        fixed_data = fix_resume_data_structure(data_from_db)

        for section_key in ['experience', 'education']:
            if section_key in fixed_data and isinstance(fixed_data[section_key], list):
                for item in fixed_data[section_key]:
                    if isinstance(item, dict) and 'dates' in item and isinstance(item['dates'], str):
                        date_match = re.match(r'^\s*(.*?)\s*–\s*(.*)\s*$', item['dates'])
                        if date_match:
                            start, end = date_match.groups()
                            item['dates'] = {'start': start.strip(), 'end': end.strip()}
                        else:
                            item['dates'] = {'start': item['dates'].strip(), 'end': None}

        db_resume.data = fixed_data
        attributes.flag_modified(db_resume, "data")
        await session.commit()
        await session.refresh(db_resume)

        return db_resume, ResumeData(**fixed_data)
    
    default_personal_info = PersonalInfo(
        name=f"{user.first_name or ''} {user.last_name or ''}".strip() or "User",
        email=user.email if user.email else None,
        phone=user.phone or "",
        linkedin=user.linkedin if hasattr(user, 'linkedin') else None,
        location=user.address or "",
        summary=""
    )
    
    new_resume_data = ResumeData(
        personalInfo=default_personal_info, 
        experience=[], 
        education=[], 
        skills=[],
        projects=[],
        certifications=[],
        languages=[],
        interests=[]
    )
    new_db_resume = Resume(user_id=user_id, data=new_resume_data.dict())
    session.add(new_db_resume)
    await session.commit()
    await session.refresh(new_db_resume)
    return new_db_resume, new_resume_data