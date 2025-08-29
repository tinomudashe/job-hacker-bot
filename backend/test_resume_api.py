#!/usr/bin/env python3
"""Test that the resume API endpoint returns job_title field"""

import requests
import json

# You'll need a valid auth token - get this from browser developer tools
# when logged into the app
AUTH_TOKEN = "YOUR_AUTH_TOKEN_HERE"

def test_resume_endpoint():
    """Test that /api/resume returns job_title field"""
    
    # This is a placeholder - you need to provide a real token
    print("⚠️  Note: This test requires a valid auth token from the browser")
    print("   To get a token:")
    print("   1. Open the app in browser")
    print("   2. Log in")
    print("   3. Open Developer Tools (F12)")
    print("   4. Go to Network tab")
    print("   5. Look for any API call")
    print("   6. Copy the Authorization header value (after 'Bearer')")
    print()
    
    if AUTH_TOKEN == "YOUR_AUTH_TOKEN_HERE":
        print("❌ Please update AUTH_TOKEN in this script first")
        return
        
    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}"
    }
    
    try:
        # Get resume data
        response = requests.get("http://localhost:8000/api/resume", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Resume API call successful")
            
            # Check for job_title field
            if 'job_title' in data:
                print(f"✅ job_title field found: '{data['job_title']}'")
            else:
                print("❌ job_title field NOT found in response")
                
            # Show structure
            print("\n📋 Response structure:")
            structure = {
                "personalInfo": "present" if "personalInfo" in data else "missing",
                "job_title": data.get("job_title", "MISSING"),
                "experience": f"{len(data.get('experience', []))} items" if "experience" in data else "missing",
                "education": f"{len(data.get('education', []))} items" if "education" in data else "missing",
                "skills": f"{len(data.get('skills', []))} items" if "skills" in data else "missing"
            }
            print(json.dumps(structure, indent=2))
            
        else:
            print(f"❌ API call failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error calling API: {e}")

if __name__ == "__main__":
    test_resume_endpoint()