#!/usr/bin/env python3
"""
Quick Admin Status Checker
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db import async_session_maker
from app.models_db import User
from sqlalchemy import select

AUTHORIZED_ADMINS = ["jnrhapson@gmail.com", "jnrhapson@yahoo.com"]

async def check_admin_status():
    """Check current admin status"""
    
    async with async_session_maker() as db:
        try:
            # Get all admin users
            result = await db.execute(
                select(User).where(User.is_admin == True)
            )
            admin_users = result.scalars().all()
            
            # Get total user count
            total_result = await db.execute(select(User))
            total_users = len(total_result.scalars().all())
            
            print(f"📊 ADMIN STATUS REPORT")
            print(f"=" * 50)
            print(f"Total Users: {total_users}")
            print(f"Admin Users: {len(admin_users)}")
            print()
            
            if len(admin_users) == 0:
                print("✅ No admin users found")
                return
            
            authorized_count = 0
            unauthorized_count = 0
            
            print("Admin Users:")
            for user in admin_users:
                if user.email in AUTHORIZED_ADMINS:
                    print(f"  ✅ {user.email} - AUTHORIZED")
                    authorized_count += 1
                else:
                    print(f"  ❌ {user.email} - UNAUTHORIZED")
                    unauthorized_count += 1
            
            print()
            print(f"Summary:")
            print(f"  ✅ Authorized: {authorized_count}")
            print(f"  ❌ Unauthorized: {unauthorized_count}")
            
            if unauthorized_count > 0:
                print()
                print("🚨 SECURITY ALERT: Unauthorized admin users detected!")
                print("Run: python fix_admin_privileges.py")
            else:
                print()
                print("✅ Admin privileges are correctly configured")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(check_admin_status())