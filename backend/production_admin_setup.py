#!/usr/bin/env python3
"""
Production Admin Setup Script for Docker/Cloud Run
This script uses the same database configuration as your main app
"""

import asyncio
import os
import sys

# Use the same imports as your main app
from app.db import async_session_maker
from app.models_db import User
from sqlalchemy import select, update

async def set_production_admin():
    """Set admin users using production database"""
    
    admin_emails = ["jnrhapson@gmail.com", "jnrhapson@yahoo.com"]
    
    try:
        print(f"🚀 Production Admin Setup")
        print(f"=" * 50)
        print(f"Setting up admin users...")
        
        success_count = 0
        
        async with async_session_maker() as db:
            for admin_email in admin_emails:
                print(f"\n📧 Processing {admin_email}...")
                
                # Check if user exists
                result = await db.execute(
                    select(User).where(User.email == admin_email)
                )
                user = result.scalars().first()
                
                if not user:
                    print(f"   ❌ User not found - must sign up first at jobhackerbot.com")
                    continue
                
                # Check if already admin
                if getattr(user, 'is_admin', False):
                    print(f"   ✅ Already an admin")
                    print(f"   Name: {user.name or 'Not set'}")
                    success_count += 1
                    continue
                
                # Set as admin
                await db.execute(
                    update(User)
                    .where(User.email == admin_email)
                    .values(is_admin=True)
                )
                await db.commit()
                
                print(f"   ✅ SUCCESS: Now a production admin!")
                print(f"   Name: {user.name or 'Not set'}")
                print(f"   User ID: {user.id}")
                success_count += 1
            
            print(f"\n🎉 Admin Setup Complete!")
            print(f"   {success_count}/{len(admin_emails)} users set as admin")
            print(f"   Admin users have unlimited premium access")
            
            return success_count > 0
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        print(f"   Database connection failed or user not found")
        return False

if __name__ == "__main__":
    print("This script connects to the same database as your production app")
    print("Make sure the user has signed up at jobhackerbot.com first")
    print()
    
    success = asyncio.run(set_production_admin())
    
    if success:
        print()
        print("🎉 Admin setup complete! The user should:")
        print("   1. Refresh their browser page")
        print("   2. See 'Admin' badge in header instead of 'Trial'") 
        print("   3. Have unlimited access to all features")
    
    sys.exit(0 if success else 1)