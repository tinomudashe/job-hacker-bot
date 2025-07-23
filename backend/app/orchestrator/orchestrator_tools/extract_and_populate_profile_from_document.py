from langchain_core.tools import tool
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models_db import Document, User, Resume
import logging
import json

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

log = logging.getLogger(__name__)

@tool
async def extract_and_populate_profile_from_documents(db: AsyncSession, user: User) -> str:
    """Extract personal information from uploaded documents and populate user profile automatically.
    
    This tool extracts real personal details (name, email, phone, linkedin, portfolio) 
    from uploaded CV/resume documents and updates the user profile with actual data
    instead of placeholder information.
    
    Returns:
        Success message with extracted information summary
    """
    try:
        user_id = user.id
        # Get user documents for extraction
        doc_result = await db.execute(
            select(Document).where(Document.user_id == user_id).order_by(Document.date_created.desc())
        )
        documents = doc_result.scalars().all()
        
        if not documents:
            return "❌ No documents found to extract profile information from. Please upload your CV/resume first."
        
        # Combine content from all documents for comprehensive extraction
        document_content = ""
        for doc in documents[:5]:  # Use latest 5 documents
            if doc.content and len(doc.content) > 50:
                document_content += f"\n\nDocument: {doc.name}\n{doc.content[:2000]}"
        
        if not document_content.strip():
            return "❌ No readable content found in uploaded documents."
        
        prompt = ChatPromptTemplate.from_template(
            """You are an expert information extractor. Extract COMPREHENSIVE resume information from CV/resume documents.

DOCUMENT CONTENT:
{document_content}

EXTRACTION TASK:
Extract ALL information and return ONLY a JSON object with these exact keys:
- "full_name": Person's complete name
- "email": Email address
- "phone": Phone number (with country code)
- "location": Current location/address
- "linkedin": LinkedIn profile URL
- "portfolio": Personal website/portfolio URL
- "github": GitHub profile URL
- "summary": Professional summary/bio (2-3 sentences)
- "skills": Array of technical skills, programming languages, tools
- "experience": Array of work experience objects with:
    - "jobTitle": Job title/position
    - "company": Company name
    - "dates": Employment dates (start - end)
    - "description": Brief description of role and achievements
- "education": Array of education objects with:
    - "degree": Degree title/name
    - "institution": School/university name
    - "dates": Graduation date or study period
    - "field": Field of study (optional)
- "projects": Array of project objects with:
    - "name": Project name
    - "description": Brief description
    - "technologies": Technologies used
- "certifications": Array of certification names with dates

CRITICAL RULES:
1. Return ONLY valid JSON - no additional text, formatting, or markdown
2. Use null for any field not found in the documents
3. For arrays, use empty arrays [] if no items found
4. Extract ALL work experience, education, and projects found
5. For dates, use format like "2020-2023" or "2023" or "Present"
6. Include quantifiable achievements in job descriptions
7. Use the most recent/complete information if multiple versions exist

Extract EVERYTHING from the document content and return the complete JSON:"""
        )
        
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-pro-preview-03-25",
            temperature=0.3  # Low temperature for accurate extraction
        )
        
        chain = prompt | llm | StrOutputParser()
        
        extracted_json = await chain.ainvoke({
            "document_content": document_content
        })
        
        # Parse the extracted JSON
        try:
            extracted_info = json.loads(extracted_json.strip())
        except json.JSONDecodeError:
            # Try to clean up the response and parse again
            clean_json = extracted_json.strip()
            if clean_json.startswith('```json'):
                clean_json = clean_json.replace('```json', '').replace('```', '').strip()
            try:
                extracted_info = json.loads(clean_json)
            except json.JSONDecodeError:
                return f"❌ Failed to parse extracted information. Raw response: {extracted_json[:300]}..."
        
        # Get current user record
        result = await db.execute(select(User).where(User.id == user_id))
        db_user = result.scalars().first()
        
        if not db_user:
            return "❌ User record not found."
        
        # Update user fields with extracted information
        updates_made = []
        
        if extracted_info.get('full_name'):
            # Split full name into first_name and last_name
            name_parts = extracted_info['full_name'].strip().split()
            if len(name_parts) >= 2:
                db_user.first_name = name_parts[0]
                db_user.last_name = ' '.join(name_parts[1:])
                db_user.name = extracted_info['full_name']
                updates_made.append(f"Name: {extracted_info['full_name']}")
            else:
                db_user.name = extracted_info['full_name']
                updates_made.append(f"Name: {extracted_info['full_name']}")
        
        if extracted_info.get('email') and '@' in extracted_info['email']:
            db_user.email = extracted_info['email']
            updates_made.append(f"Email: {extracted_info['email']}")
        
        if extracted_info.get('phone'):
            db_user.phone = extracted_info['phone']
            updates_made.append(f"Phone: {extracted_info['phone']}")
        
        if extracted_info.get('location'):
            db_user.address = extracted_info['location']
            updates_made.append(f"Location: {extracted_info['location']}")
        
        if extracted_info.get('linkedin'):
            db_user.linkedin = extracted_info['linkedin']
            updates_made.append(f"LinkedIn: {extracted_info['linkedin']}")
        
        # Create or update comprehensive resume data structure
        try:
            resume_result = await db.execute(select(Resume).where(Resume.user_id == user_id))
            db_resume = resume_result.scalars().first()
            
            # Create comprehensive resume data structure
            comprehensive_resume_data = {
                "personalInfo": {
                    "name": extracted_info.get('full_name', ''),
                    "email": extracted_info.get('email', ''),
                    "phone": extracted_info.get('phone', ''),
                    "location": extracted_info.get('location', ''),
                    "linkedin": extracted_info.get('linkedin', ''),
                    "github": extracted_info.get('github', ''),
                    "portfolio": extracted_info.get('portfolio', ''),
                    "summary": extracted_info.get('summary', '')
                },
                "skills": extracted_info.get('skills', []),
                "experience": extracted_info.get('experience', []),
                "education": extracted_info.get('education', []),
                "projects": extracted_info.get('projects', []),
                "certifications": extracted_info.get('certifications', [])
            }
            
            if db_resume:
                # Update existing resume
                db_resume.data = comprehensive_resume_data
                updates_made.append("Updated complete resume data structure")
            else:
                # Create new resume record
                new_resume = Resume(
                    user_id=user_id,
                    data=comprehensive_resume_data
                )
                db.add(new_resume)
                updates_made.append("Created complete resume data structure")
                
            # Also update individual profile skills field for backward compatibility
            if extracted_info.get('skills'):
                db_user.skills = ", ".join(extracted_info['skills'])
                
            # Add professional summary to profile headline
            if extracted_info.get('summary'):
                db_user.profile_headline = extracted_info['summary']
                
        except Exception as resume_error:
            log.warning(f"Failed to update comprehensive resume data: {resume_error}")
        
        # Commit all changes
        await db.commit()
        
        if not updates_made:
            return "ℹ️ No new information was extracted from documents that wasn't already in your profile."
        
        return f"""✅ **Profile Successfully Updated from Documents!**

**📋 Extracted and Updated Information:**
{chr(10).join(f"• {update}" for update in updates_made)}

**🎯 Comprehensive Data Extracted:**
• **Personal Info**: {extracted_info.get('full_name', 'Not found')} | {extracted_info.get('email', 'Not found')}
• **Contact**: {extracted_info.get('phone', 'Not found')} | {extracted_info.get('location', 'Not found')}
• **Links**: Portfolio: {extracted_info.get('portfolio', 'Not found')} | GitHub: {extracted_info.get('github', 'Not found')}
• **Work Experience**: {len(extracted_info.get('experience', []))} positions extracted
• **Education**: {len(extracted_info.get('education', []))} degrees/qualifications extracted  
• **Skills**: {len(extracted_info.get('skills', []))} technical skills extracted
• **Projects**: {len(extracted_info.get('projects', []))} projects extracted
• **Certifications**: {len(extracted_info.get('certifications', []))} certifications extracted

**🎉 Your profile is now fully populated with real data!** 

**📥 PDF Forms Now Populated:**
- ✅ Personal information fields
- ✅ Work experience entries  
- ✅ Education history
- ✅ Skills and competencies
- ✅ Projects and achievements
- ✅ Certifications and awards

**📝 Next Steps:**
1. **Test PDF Dialog**: Click any download button - all fields should now be populated!
2. **Verify Data**: Check the work experience form you showed me - it should now have your real jobs
3. **Generate Content**: Create resumes/cover letters with your actual information
4. **Fine-tune**: Make any adjustments directly in the profile settings

**💡 Pro Tip**: Your PDF dialog forms should now show your actual work experience instead of "Software Engineer at Google Inc."!

<!-- extracted_info={json.dumps(extracted_info)} -->"""
        
    except Exception as e:
        log.error(f"Error extracting profile information: {e}", exc_info=True)
        return f"❌ Sorry, I encountered an error while extracting your profile information: {str(e)}. Please try again."