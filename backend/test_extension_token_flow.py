#!/usr/bin/env python3
"""
Test script to verify the extension token flow
"""

import asyncio
import aiohttp
import json

async def test_token_flow():
    """Test the complete token flow"""
    
    # Replace with your actual token
    token = input("Enter your extension token (starts with jhb_): ").strip()
    
    if not token.startswith("jhb_"):
        print("❌ Invalid token format. Token should start with 'jhb_'")
        return
    
    base_url = "http://localhost:8000"
    
    # Test 1: Verify token
    print("\n1. Testing token verification...")
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{base_url}/api/extension-tokens/verify",
            headers={"Authorization": f"Bearer {token}"}
        ) as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ Token verified: {data}")
            else:
                print(f"❌ Token verification failed: {response.status}")
                error_text = await response.text()
                print(f"   Error: {error_text}")
                return
    
    # Test 2: Get extension status
    print("\n2. Testing extension status...")
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{base_url}/api/chrome-extension/status",
            headers={"Authorization": f"Bearer {token}"}
        ) as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ Status retrieved:")
                print(f"   - Extension Enabled: {data.get('extensionEnabled')}")
                print(f"   - Has Resume: {data.get('hasResume')}")
                print(f"   - Profile Complete: {data.get('profileComplete')}")
            else:
                print(f"❌ Status check failed: {response.status}")
                error_text = await response.text()
                print(f"   Error: {error_text}")
    
    # Test 3: Test autofill with mock data
    print("\n3. Testing autofill endpoint...")
    mock_form_data = {
        "formStructure": {
            "fields": [
                {
                    "id": "firstName",
                    "name": "firstName",
                    "type": "text",
                    "category": "personal.firstName",
                    "label": "First Name",
                    "required": True
                },
                {
                    "id": "email",
                    "name": "email",
                    "type": "email",
                    "category": "personal.email",
                    "label": "Email",
                    "required": True
                }
            ],
            "metadata": {},
            "jobContext": {
                "title": "Software Engineer",
                "company": "Test Company"
            }
        },
        "includeConfidence": True
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{base_url}/api/chrome-extension/autofill",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json=mock_form_data
        ) as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ Autofill successful:")
                print(f"   - Field Values: {data.get('fieldValues')}")
                print(f"   - Missing Info: {data.get('missingInfo')}")
            else:
                print(f"❌ Autofill failed: {response.status}")
                error_text = await response.text()
                print(f"   Error: {error_text}")
    
    print("\n✨ All tests completed!")

if __name__ == "__main__":
    print("Extension Token Flow Test")
    print("=" * 50)
    asyncio.run(test_token_flow())