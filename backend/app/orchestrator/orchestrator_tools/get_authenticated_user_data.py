from langchain_core.tools import tool
import logging
import json
from sqlalchemy.ext.asyncio import AsyncSession
from app.models_db import User
from app.internal_api import make_internal_api_call

log = logging.getLogger(__name__)

@tool
async def get_authenticated_user_data(
    endpoint: str,
    user: User,
    db: AsyncSession
) -> str:
    """
    Access protected user endpoints using the authenticated WebSocket user.
    
    Args:
        endpoint: The API endpoint to access (e.g., '/api/users/me', '/api/resume', '/api/users/me/documents')
    
    Returns:
        JSON data from the protected endpoint
    """
    if endpoint is None:
        endpoint = "/api/users/me"

    try:
        # Use the internal API to access protected endpoints with the authenticated user
        data = await make_internal_api_call(endpoint, user, db)
        
        # Format the response nicely for the user
        if endpoint == "/api/users/me":
            return f"""✅ **User Profile Data Retrieved**

**👤 Profile Information:**
- **Name**: {data.get('name', 'Not provided')}
- **Email**: {data.get('email', 'Not provided')}
- **Phone**: {data.get('phone', 'Not provided')}
- **Location**: {data.get('address', 'Not provided')}
- **LinkedIn**: {data.get('linkedin', 'Not provided')}
- **Skills**: {data.get('skills', 'Not provided')}
- **Profile Headline**: {data.get('profile_headline', 'Not provided')}

**🔧 Account Details:**
- **User ID**: {data.get('id')}
- **Status**: {'Active' if data.get('active') else 'Inactive'}
- **External ID**: {data.get('external_id', 'Not provided')}

<!-- raw_data={json.dumps(data)} -->"""
            
        elif endpoint == "/api/resume":
            personal_info = data.get('personalInfo', {})
            experience_count = len(data.get('experience', []))
            education_count = len(data.get('education', []))
            skills_count = len(data.get('skills', []))
            
            return f"""✅ **Resume Data Retrieved**

**📋 Resume Summary:**
- **Name**: {personal_info.get('name', 'Not provided')}
- **Email**: {personal_info.get('email', 'Not provided')}
- **Phone**: {personal_info.get('phone', 'Not provided')}
- **Location**: {personal_info.get('location', 'Not provided')}
- **Summary**: {personal_info.get('summary', 'Not provided')}

**📊 Resume Sections:**
- **Work Experience**: {experience_count} entries
- **Education**: {education_count} entries  
- **Skills**: {skills_count} skills listed
- **Projects**: {len(data.get('projects', []))} projects
- **Certifications**: {len(data.get('certifications', []))} certifications

<!-- raw_data={json.dumps(data)} -->"""
            
        elif endpoint == "/api/users/me/documents":
            doc_count = len(data)
            doc_types = list(set(doc.get('type', 'unknown') for doc in data))
            
            return f"""✅ **Documents Retrieved**

**📄 Document Summary:**
- **Total Documents**: {doc_count}
- **Document Types**: {', '.join(doc_types) if doc_types else 'None'}

**📋 Recent Documents:**
{chr(10).join([f"• {doc.get('name', 'Unnamed')} ({doc.get('type', 'unknown')}) - {doc.get('date_created', 'No date')[:10]}" for doc in data[:5]])}

<!-- raw_data={json.dumps(data)} -->"""
            
        else:
            return f"""✅ **Data Retrieved from {endpoint}**

{json.dumps(data, indent=2)}

<!-- raw_data={json.dumps(data)} -->"""
            
    except Exception as e:
        log.error(f"Error accessing {endpoint}: {e}", exc_info=True)
        return f"❌ **Error accessing {endpoint}**: {str(e)}"
