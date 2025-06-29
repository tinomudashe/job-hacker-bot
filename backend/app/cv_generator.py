import logging
from typing import List, Optional
from pydantic import BaseModel, EmailStr, HttpUrl
from fastapi import APIRouter, Body, Depends
from fastapi.responses import HTMLResponse
from app.db import get_db
from app.models_db import User, GeneratedCV
from app.dependencies import get_current_active_user
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4
from app.usage import UsageManager

logger = logging.getLogger(__name__)
router = APIRouter()

# --- Pydantic Models for CV Data ---

class PersonalInformation(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    linkedin_url: Optional[HttpUrl] = None
    location: str
    summary: str

class Experience(BaseModel):
    title: str
    company: str
    start_date: str
    end_date: str
    description: str

class Education(BaseModel):
    degree: str
    institution: str
    start_date: str
    end_date: str

class CVData(BaseModel):
    personal_info: PersonalInformation
    experience: List[Experience]
    education: List[Education]
    skills: List[str]


# --- HTML Generation Logic ---

def generate_cv_html(data: CVData) -> str:
    """Generates an HTML representation of the CV."""
    
    # --- Styles ---
    styles = """
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 40px auto;
            padding: 20px;
            border: 1px solid #ddd;
            border-radius: 8px;
            background-color: #fff;
        }
        h1, h2, h3 {
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 5px;
            margin-top: 20px;
        }
        h1 {
            text-align: center;
            border-bottom: none;
            margin-bottom: 0;
        }
        .contact-info {
            text-align: center;
            margin-bottom: 20px;
            color: #555;
        }
        .contact-info a {
            color: #3498db;
            text-decoration: none;
        }
        .contact-info a:hover {
            text-decoration: underline;
        }
        .section {
            margin-bottom: 20px;
        }
        .job, .edu-item {
            margin-bottom: 15px;
        }
        .job-title, .degree {
            font-weight: bold;
            font-size: 1.1em;
        }
        .company, .institution {
            font-style: italic;
            color: #555;
        }
        .dates {
            float: right;
            color: #777;
        }
        .skills-list {
            list-style: none;
            padding: 0;
            display: flex;
            flex-wrap: wrap;
        }
        .skill-item {
            background-color: #3498db;
            color: white;
            padding: 5px 12px;
            margin: 5px;
            border-radius: 5px;
            font-size: 0.9em;
        }
    </style>
    """

    # --- HTML Structure ---
    personal = data.personal_info
    linkedin_link = f'<a href="{personal.linkedin_url}">LinkedIn</a>' if personal.linkedin_url else ""
    
    experience_html = ""
    for job in data.experience:
        experience_html += f"""
        <div class="job">
            <div class="dates">{job.start_date} - {job.end_date}</div>
            <div class="job-title">{job.title}</div>
            <div class="company">{job.company}</div>
            <p>{job.description}</p>
        </div>
        """

    education_html = ""
    for edu in data.education:
        education_html += f"""
        <div class="edu-item">
            <div class="dates">{edu.start_date} - {edu.end_date}</div>
            <div class="degree">{edu.degree}</div>
            <div class="institution">{edu.institution}</div>
        </div>
        """
        
    skills_html = "".join([f'<li class="skill-item">{skill}</li>' for skill in data.skills])

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>CV for {personal.full_name}</title>
        {styles}
    </head>
    <body>
        <h1>{personal.full_name}</h1>
        <div class="contact-info">
            {personal.location} | {personal.email} | {personal.phone} { '| ' + linkedin_link if linkedin_link else ''}
        </div>
        
        <div class="section">
            <h2>Summary</h2>
            <p>{personal.summary}</p>
        </div>
        
        <div class="section">
            <h2>Experience</h2>
            {experience_html}
        </div>
        
        <div class="section">
            <h2>Education</h2>
            {education_html}
        </div>
        
        <div class="section">
            <h2>Skills</h2>
            <ul class="skills-list">{skills_html}</ul>
        </div>
        
    </body>
    </html>
    """
    return html_content

# --- API Endpoint ---

@router.post("/cv/generate", response_class=HTMLResponse)
async def generate_cv(
    cv_data: CVData = Body(
        ...,
        examples={
            "default": {
                "summary": "Example CV data structure.",
                "value": {
                    "personal_info": {
                        "full_name": "Tinomudashe Marecha",
                        "email": "jnrhapson@yahoo.com",
                        "phone": "+1 (123) 456-7890",
                        "linkedin_url": "https://www.linkedin.com/in/myLinkedIn",
                        "location": "New York, NY",
                        "summary": "A concise overview of your professional background..."
                    },
                    "experience": [
                        {
                            "title": "Software Engineer",
                            "company": "Tech Solutions Inc.",
                            "start_date": "Jan 2020",
                            "end_date": "Present",
                            "description": "Developed and maintained web applications..."
                        }
                    ],
                    "education": [
                        {
                            "degree": "Bachelor of Science in Computer Science",
                            "institution": "University of Technology",
                            "start_date": "2016",
                            "end_date": "2020"
                        }
                    ],
                    "skills": ["JavaScript", "Python", "FastAPI", "React"]
                }
            }
        }
    ),
    db: AsyncSession = Depends(get_db),
    db_user: User = Depends(get_current_active_user),
    _ = Depends(UsageManager(feature="cvs"))
):
    """
    Generates a CV in HTML format from the provided data.
    """
    logger.info(f"Generating CV for {cv_data.personal_info.full_name}")
    html_cv = generate_cv_html(cv_data)

    # Save record to database
    new_record = GeneratedCV(
        id=str(uuid4()),
        user_id=db_user.id,
        content_html=html_cv
    )
    db.add(new_record)
    await db.commit()

    return HTMLResponse(content=html_cv) 