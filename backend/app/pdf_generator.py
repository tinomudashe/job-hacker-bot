import logging
import asyncio
from typing import Optional
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
import tempfile
import os

# PDF generation libraries
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    try:
        import pdfkit
        PDFKIT_AVAILABLE = True
        REPORTLAB_AVAILABLE = False
    except ImportError:
        REPORTLAB_AVAILABLE = False
        PDFKIT_AVAILABLE = False

from sqlalchemy import select

from app.db import get_db
from app.models_db import User, GeneratedCoverLetter, Resume
from app.dependencies import get_current_active_user
from app.resume import ResumeData

logger = logging.getLogger(__name__)
router = APIRouter()

class PDFGenerationRequest(BaseModel):
    content_type: str  # "cover_letter" or "resume"
    content_id: Optional[str] = None  # ID of saved cover letter or resume
    content_text: Optional[str] = None  # Direct text content
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    style: str = "modern"  # "modern", "classic", "minimal"

# Professional CSS styles for different themes
STYLES = {
    "modern": """
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            line-height: 1.6;
            color: #1f2937;
            margin: 0;
            padding: 40px;
            background: white;
            font-size: 11pt;
        }
        
        .header {
            border-bottom: 3px solid #3b82f6;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        
        .header h1 {
            margin: 0 0 5px 0;
            font-size: 24pt;
            font-weight: 700;
            color: #1f2937;
        }
        
        .header .subtitle {
            color: #6b7280;
            font-size: 12pt;
            margin: 0;
        }
        
        .content {
            max-width: 700px;
            margin: 0 auto;
        }
        
        .section {
            margin-bottom: 25px;
        }
        
        .section h2 {
            font-size: 14pt;
            font-weight: 600;
            color: #3b82f6;
            margin: 0 0 10px 0;
            padding-bottom: 5px;
            border-bottom: 1px solid #e5e7eb;
        }
        
        .cover-letter-body {
            text-align: justify;
            line-height: 1.7;
        }
        
        .cover-letter-body p {
            margin: 0 0 15px 0;
        }
        
        .experience-item, .education-item {
            margin-bottom: 20px;
            padding-left: 15px;
            border-left: 2px solid #e5e7eb;
        }
        
        .experience-item h3, .education-item h3 {
            font-size: 12pt;
            font-weight: 600;
            margin: 0 0 5px 0;
            color: #1f2937;
        }
        
        .company, .institution {
            font-weight: 500;
            color: #3b82f6;
            margin: 0 0 5px 0;
        }
        
        .dates {
            font-size: 10pt;
            color: #6b7280;
            margin: 0 0 10px 0;
        }
        
        .skills {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }
        
        .skill-tag {
            background: #eff6ff;
            color: #1e40af;
            padding: 4px 12px;
            border-radius: 6px;
            font-size: 10pt;
            font-weight: 500;
        }
        
        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e5e7eb;
            text-align: center;
            color: #6b7280;
            font-size: 9pt;
        }
    """,
    
    "classic": """
        body {
            font-family: 'Times New Roman', serif;
            line-height: 1.6;
            color: #000;
            margin: 0;
            padding: 40px;
            background: white;
            font-size: 12pt;
        }
        
        .header {
            text-align: center;
            border-bottom: 2px solid #000;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        
        .header h1 {
            margin: 0 0 10px 0;
            font-size: 22pt;
            font-weight: bold;
        }
        
        .content {
            max-width: 650px;
            margin: 0 auto;
        }
        
        .section h2 {
            font-size: 14pt;
            font-weight: bold;
            margin: 20px 0 10px 0;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .cover-letter-body {
            text-align: justify;
            line-height: 1.8;
        }
        
        .experience-item, .education-item {
            margin-bottom: 15px;
        }
        
        .experience-item h3, .education-item h3 {
            font-weight: bold;
            margin: 0 0 5px 0;
        }
    """,
    
    "minimal": """
        body {
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            line-height: 1.5;
            color: #333;
            margin: 0;
            padding: 50px;
            background: white;
            font-size: 11pt;
        }
        
        .header h1 {
            margin: 0 0 30px 0;
            font-size: 20pt;
            font-weight: 300;
            color: #333;
        }
        
        .content {
            max-width: 600px;
        }
        
        .section {
            margin-bottom: 30px;
        }
        
        .section h2 {
            font-size: 12pt;
            font-weight: 500;
            margin: 0 0 15px 0;
            color: #333;
        }
        
        .cover-letter-body {
            line-height: 1.7;
        }
        
        .cover-letter-body p {
            margin: 0 0 20px 0;
        }
    """
}

def generate_cover_letter_html(content: str, company_name: str = "", job_title: str = "", style: str = "modern", user_name: str = "User") -> str:
    """Generate HTML for cover letter with specified style."""
    
    # Clean and format the content
    paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
    formatted_content = ""
    
    for paragraph in paragraphs:
        if paragraph and not paragraph.startswith('Dear ') and not paragraph.startswith('Sincerely'):
            formatted_content += f"<p>{paragraph}</p>\n"
    
    # Add proper greeting and closing if not present
    if not content.strip().startswith('Dear '):
        greeting = f"Dear {company_name} Hiring Team," if company_name else "Dear Hiring Manager,"
        formatted_content = f"<p>{greeting}</p>\n" + formatted_content
    
    if not content.strip().endswith('Sincerely,'):
        formatted_content += f"<p>Sincerely,<br><br>{user_name}</p>\n"
    
    title = f"Cover Letter - {job_title} at {company_name}" if job_title and company_name else "Cover Letter"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>{title}</title>
        <style>{STYLES[style]}</style>
    </head>
    <body>
        <div class="content">
            <div class="header">
                <h1>{title}</h1>
                <p class="subtitle">Generated on {datetime.now().strftime('%B %d, %Y')}</p>
            </div>
            
            <div class="section">
                <div class="cover-letter-body">
                    {formatted_content}
                </div>
            </div>
            
            <div class="footer">
                <p>Generated by Job Application Assistant</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

def generate_resume_html(resume_data: ResumeData, style: str = "modern") -> str:
    """Generate HTML for resume with specified style."""
    
    personal = resume_data.personalInfo
    
    # Build experience section
    experience_html = ""
    for exp in resume_data.experience:
        experience_html += f"""
        <div class="experience-item">
            <h3>{exp.jobTitle}</h3>
            <div class="company">{exp.company}</div>
            <div class="dates">{exp.dates}</div>
            <p>{exp.description}</p>
        </div>
        """
    
    # Build education section
    education_html = ""
    for edu in resume_data.education:
        education_html += f"""
        <div class="education-item">
            <h3>{edu.degree}</h3>
            <div class="institution">{edu.institution}</div>
            <div class="dates">{edu.dates}</div>
        </div>
        """
    
    # Build skills section
    skills_html = ""
    if resume_data.skills:
        for skill in resume_data.skills:
            skills_html += f'<span class="skill-tag">{skill}</span>'
    
    contact_info = []
    if personal.email:
        contact_info.append(personal.email)
    if personal.phone:
        contact_info.append(personal.phone)
    if personal.location:
        contact_info.append(personal.location)
    if personal.linkedin:
        contact_info.append(personal.linkedin)
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Resume - {personal.name or 'User'}</title>
        <style>{STYLES[style]}</style>
    </head>
    <body>
        <div class="content">
            <div class="header">
                <h1>{personal.name or 'User'}</h1>
                <p class="subtitle">{' | '.join(contact_info)}</p>
            </div>
            
            {f'''
            <div class="section">
                <h2>Professional Summary</h2>
                <p>{personal.summary}</p>
            </div>
            ''' if personal.summary else ''}
            
            {f'''
            <div class="section">
                <h2>Experience</h2>
                {experience_html}
            </div>
            ''' if experience_html else ''}
            
            {f'''
            <div class="section">
                <h2>Education</h2>
                {education_html}
            </div>
            ''' if education_html else ''}
            
            {f'''
            <div class="section">
                <h2>Skills</h2>
                <div class="skills">
                    {skills_html}
                </div>
            </div>
            ''' if skills_html else ''}
            
            <div class="footer">
                <p>Generated on {datetime.now().strftime('%B %d, %Y')}</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

def create_cover_letter_pdf(content: str, company_name: str, job_title: str, user_name: str, style: str, filename: str) -> str:
    """Create a cover letter PDF using ReportLab."""
    
    temp_dir = Path(tempfile.gettempdir())
    pdf_path = temp_dir / f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    # Create PDF document
    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter, topMargin=1*inch, bottomMargin=1*inch, 
                           leftMargin=1*inch, rightMargin=1*inch)
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Define custom styles based on theme
    if style == "modern":
        title_style = ParagraphStyle(
            'ModernTitle',
            parent=styles['Title'],
            fontSize=18,
            textColor=colors.HexColor('#3b82f6'),
            spaceAfter=20,
            alignment=TA_CENTER
        )
        body_style = ParagraphStyle(
            'ModernBody',
            parent=styles['Normal'],
            fontSize=11,
            leading=16,
            alignment=TA_JUSTIFY,
            spaceAfter=12
        )
    elif style == "classic":
        title_style = ParagraphStyle(
            'ClassicTitle',
            parent=styles['Title'],
            fontSize=16,
            textColor=colors.black,
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Times-Bold'
        )
        body_style = ParagraphStyle(
            'ClassicBody',
            parent=styles['Normal'],
            fontSize=12,
            leading=18,
            alignment=TA_JUSTIFY,
            spaceAfter=12,
            fontName='Times-Roman'
        )
    else:  # minimal
        title_style = ParagraphStyle(
            'MinimalTitle',
            parent=styles['Title'],
            fontSize=14,
            textColor=colors.black,
            spaceAfter=30,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold'
        )
        body_style = ParagraphStyle(
            'MinimalBody',
            parent=styles['Normal'],
            fontSize=11,
            leading=15,
            alignment=TA_LEFT,
            spaceAfter=15,
            fontName='Helvetica'
        )
    
    # Build content
    story = []
    
    # Title
    title = f"Cover Letter - {job_title} at {company_name}" if job_title and company_name else "Cover Letter"
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Date
    date_style = ParagraphStyle('Date', parent=styles['Normal'], fontSize=10, alignment=TA_RIGHT)
    story.append(Paragraph(datetime.now().strftime('%B %d, %Y'), date_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Content paragraphs
    paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
    
    # Add greeting if not present
    if not content.strip().startswith('Dear '):
        greeting = f"Dear {company_name} Hiring Team," if company_name else "Dear Hiring Manager,"
        story.append(Paragraph(greeting, body_style))
    
    for paragraph in paragraphs:
        if paragraph and not paragraph.startswith('Dear ') and not paragraph.startswith('Sincerely'):
            story.append(Paragraph(paragraph, body_style))
    
    # Add closing if not present
    if not content.strip().endswith('Sincerely,'):
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph("Sincerely,", body_style))
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph(user_name, body_style))
    
    # Build PDF
    doc.build(story)
    return str(pdf_path)

def create_resume_pdf(resume_data: ResumeData, style: str, filename: str) -> str:
    """Create a resume PDF using ReportLab."""
    
    temp_dir = Path(tempfile.gettempdir())
    pdf_path = temp_dir / f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    # Create PDF document
    doc = SimpleDocTemplate(str(pdf_path), pagesize=letter, topMargin=0.75*inch, bottomMargin=0.75*inch,
                           leftMargin=0.75*inch, rightMargin=0.75*inch)
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Define custom styles
    if style == "modern":
        name_style = ParagraphStyle('ModernName', parent=styles['Title'], fontSize=20, 
                                   textColor=colors.HexColor('#3b82f6'), alignment=TA_CENTER, spaceAfter=10)
        contact_style = ParagraphStyle('ModernContact', parent=styles['Normal'], fontSize=10, 
                                      alignment=TA_CENTER, spaceAfter=20)
        section_style = ParagraphStyle('ModernSection', parent=styles['Heading2'], fontSize=14, 
                                      textColor=colors.HexColor('#3b82f6'), spaceAfter=10, spaceBefore=15)
    else:
        name_style = ParagraphStyle('Name', parent=styles['Title'], fontSize=18, alignment=TA_CENTER, spaceAfter=10)
        contact_style = ParagraphStyle('Contact', parent=styles['Normal'], fontSize=10, 
                                      alignment=TA_CENTER, spaceAfter=20)
        section_style = ParagraphStyle('Section', parent=styles['Heading2'], fontSize=12, 
                                      spaceAfter=10, spaceBefore=15)
    
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=10, spaceAfter=8)
    
    # Build content
    story = []
    
    # Name and contact info
    personal = resume_data.personalInfo
    story.append(Paragraph(personal.name or "User", name_style))
    
    contact_info = []
    if personal.email:
        contact_info.append(personal.email)
    if personal.phone:
        contact_info.append(personal.phone)
    if personal.location:
        contact_info.append(personal.location)
    if personal.linkedin:
        contact_info.append(personal.linkedin)
    
    if contact_info:
        story.append(Paragraph(' | '.join(contact_info), contact_style))
    
    # Summary
    if personal.summary:
        story.append(Paragraph("Professional Summary", section_style))
        story.append(Paragraph(personal.summary, body_style))
    
    # Experience
    if resume_data.experience:
        story.append(Paragraph("Experience", section_style))
        for exp in resume_data.experience:
            story.append(Paragraph(f"<b>{exp.jobTitle}</b> - {exp.company}", body_style))
            story.append(Paragraph(f"<i>{exp.dates}</i>", body_style))
            story.append(Paragraph(exp.description, body_style))
            story.append(Spacer(1, 0.1*inch))
    
    # Education
    if resume_data.education:
        story.append(Paragraph("Education", section_style))
        for edu in resume_data.education:
            story.append(Paragraph(f"<b>{edu.degree}</b> - {edu.institution}", body_style))
            story.append(Paragraph(f"<i>{edu.dates}</i>", body_style))
            story.append(Spacer(1, 0.1*inch))
    
    # Skills
    if resume_data.skills:
        story.append(Paragraph("Skills", section_style))
        skills_text = ', '.join(resume_data.skills)
        story.append(Paragraph(skills_text, body_style))
    
    # Build PDF
    doc.build(story)
    return str(pdf_path)

@router.post("/pdf/generate")
async def generate_pdf(
    request: PDFGenerationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Generate a styled PDF for cover letter or resume."""
    
    try:
        if not REPORTLAB_AVAILABLE:
            raise HTTPException(
                status_code=500, 
                detail="PDF generation not available. Please install reportlab."
            )
        
        filename = "document"
        pdf_path = ""
        
        if request.content_type == "cover_letter":
            # Get cover letter content
            if request.content_id:
                # Fetch from database
                result = await db.execute(
                    select(GeneratedCoverLetter).where(
                        GeneratedCoverLetter.id == request.content_id,
                        GeneratedCoverLetter.user_id == current_user.id
                    )
                )
                cover_letter = result.scalars().first()
                if not cover_letter:
                    raise HTTPException(status_code=404, detail="Cover letter not found")
                content = cover_letter.content
            elif request.content_text:
                content = request.content_text
            else:
                raise HTTPException(status_code=400, detail="Either content_id or content_text required")
            
            user_name = f"{current_user.first_name or ''} {current_user.last_name or ''}".strip() or "User"
            filename = f"cover_letter_{request.company_name or 'document'}".replace(" ", "_")
            
            # Generate PDF using ReportLab
            pdf_path = create_cover_letter_pdf(
                content=content,
                company_name=request.company_name or "",
                job_title=request.job_title or "",
                user_name=user_name,
                style=request.style,
                filename=filename
            )
            
        elif request.content_type == "resume":
            # Get resume data
            result = await db.execute(
                select(Resume).where(Resume.user_id == current_user.id)
            )
            resume = result.scalars().first()
            
            if not resume:
                raise HTTPException(status_code=404, detail="Resume not found")
            
            resume_data = ResumeData(**resume.data)
            filename = f"resume_{current_user.first_name or 'user'}".replace(" ", "_")
            
            # Generate PDF using ReportLab
            pdf_path = create_resume_pdf(resume_data, request.style, filename)
            
        else:
            raise HTTPException(status_code=400, detail="Invalid content_type. Must be 'cover_letter' or 'resume'")
        
        # Return file response
        return FileResponse(
            path=pdf_path,
            filename=f"{filename}.pdf",
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}.pdf"}
        )
        
    except Exception as e:
        logger.error(f"Error in PDF generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pdf/generate")
async def generate_pdf_get(
    content_type: str,
    style: str = "modern",
    content_id: Optional[str] = None,
    company_name: Optional[str] = None,
    job_title: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Generate a styled PDF for cover letter or resume using GET request (for direct links)."""
    
    try:
        if not REPORTLAB_AVAILABLE:
            raise HTTPException(
                status_code=500, 
                detail="PDF generation not available. Please install reportlab."
            )
        
        filename = "document"
        pdf_path = ""
        
        if content_type == "cover_letter":
            # Get cover letter content
            if content_id:
                # Fetch from database
                result = await db.execute(
                    select(GeneratedCoverLetter).where(
                        GeneratedCoverLetter.id == content_id,
                        GeneratedCoverLetter.user_id == current_user.id
                    )
                )
                cover_letter = result.scalars().first()
                if not cover_letter:
                    raise HTTPException(status_code=404, detail="Cover letter not found")
                content = cover_letter.content
            else:
                raise HTTPException(status_code=400, detail="content_id required for cover letter")
            
            user_name = f"{current_user.first_name or ''} {current_user.last_name or ''}".strip() or "User"
            filename = f"cover_letter_{company_name or 'document'}".replace(" ", "_")
            
            # Generate PDF using ReportLab
            pdf_path = create_cover_letter_pdf(
                content=content,
                company_name=company_name or "",
                job_title=job_title or "",
                user_name=user_name,
                style=style,
                filename=filename
            )
            
        elif content_type == "resume":
            # Get resume data
            result = await db.execute(
                select(Resume).where(Resume.user_id == current_user.id)
            )
            resume = result.scalars().first()
            
            if not resume:
                raise HTTPException(status_code=404, detail="Resume not found")
            
            resume_data = ResumeData(**resume.data)
            filename = f"resume_{current_user.first_name or 'user'}".replace(" ", "_")
            
            # Generate PDF using ReportLab
            pdf_path = create_resume_pdf(resume_data, style, filename)
            
        else:
            raise HTTPException(status_code=400, detail="Invalid content_type. Must be 'cover_letter' or 'resume'")
        
        # Return file response
        return FileResponse(
            path=pdf_path,
            filename=f"{filename}.pdf",
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}.pdf"}
        )
        
    except Exception as e:
        logger.error(f"Error in PDF generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pdf/preview/{content_type}")
async def preview_html(
    content_type: str,
    content_id: Optional[str] = None,
    style: str = "modern",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Preview HTML version before PDF generation."""
    
    try:
        if content_type == "cover_letter" and content_id:
            from sqlalchemy import select
            result = await db.execute(
                select(GeneratedCoverLetter).where(
                    GeneratedCoverLetter.id == content_id,
                    GeneratedCoverLetter.user_id == current_user.id
                )
            )
            cover_letter = result.scalars().first()
            if not cover_letter:
                raise HTTPException(status_code=404, detail="Cover letter not found")
            
            user_name = f"{current_user.first_name or ''} {current_user.last_name or ''}".strip() or "User"
            html_content = generate_cover_letter_html(
                content=cover_letter.content,
                style=style,
                user_name=user_name
            )
            
        elif content_type == "resume":
            from sqlalchemy import select
            result = await db.execute(
                select(Resume).where(Resume.user_id == current_user.id)
            )
            resume = result.scalars().first()
            
            if not resume:
                raise HTTPException(status_code=404, detail="Resume not found")
            
            resume_data = ResumeData(**resume.data)
            html_content = generate_resume_html(resume_data, style)
            
        else:
            raise HTTPException(status_code=400, detail="Invalid content_type")
        
        return Response(content=html_content, media_type="text/html")
        
    except Exception as e:
        logger.error(f"Error in HTML preview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Alias endpoint for backward compatibility
@router.post("/pdf/download")
async def download_pdf(
    request: PDFGenerationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Download a styled PDF for cover letter or resume. (Alias for /pdf/generate)"""
    return await generate_pdf(request, db, current_user) 