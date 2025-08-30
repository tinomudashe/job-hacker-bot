#!/usr/bin/env python3
"""
Admin User Setup Script
Usage: python set_admin.py email@domain.com
"""

import asyncio
import sys
import os
from sqlalchemy import select, update

# Add the app directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db import async_session_maker
from app.models_db import User

async def set_user_admin(email: str):
    """Set a user as admin by email"""
    async with async_session_maker() as db:
        try:
            # Find user by email
            result = await db.execute(
                select(User).where(User.email == email)
            )
            user = result.scalars().first()
            
            if not user:
                print(f"❌ User with email '{email}' not found")
                return False
            
            # Check if already admin
            if getattr(user, 'is_admin', False):
                print(f"✅ User '{email}' is already an admin")
                return True
            
            # Set as admin
            await db.execute(
                update(User)
                .where(User.email == email)
                .values(is_admin=True)
            )
            await db.commit()
            
            print(f"✅ User '{email}' (ID: {user.id}) is now an admin")
            print(f"   Name: {user.name or 'Not set'}")
            print(f"   Admin Access: Premium features unlocked")
            return True
            
        except Exception as e:
            print(f"❌ Error setting admin: {e}")
            await db.rollback()
            return False

async def list_admins():
    """List all admin users"""
    async with async_session_maker() as db:
        try:
            result = await db.execute(
                select(User).where(User.is_admin == True)
            )
            admins = result.scalars().all()
            
            if not admins:
                print("No admin users found")
                return
                
            print(f"Admin Users ({len(admins)}):")
            for admin in admins:
                print(f"  - {admin.email} ({admin.name or 'No name'}) - ID: {admin.id}")
                
        except Exception as e:
            print(f"❌ Error listing admins: {e}")

async def remove_admin(email: str):
    """Remove admin status from a user"""
    async with async_session_maker() as db:
        try:
            # Find user by email
            result = await db.execute(
                select(User).where(User.email == email)
            )
            user = result.scalars().first()
            
            if not user:
                print(f"❌ User with email '{email}' not found")
                return False
            
            if not getattr(user, 'is_admin', False):
                print(f"✅ User '{email}' is not an admin")
                return True
            
            # Remove admin status
            await db.execute(
                update(User)
                .where(User.email == email)
                .values(is_admin=False)
            )
            await db.commit()
            
            print(f"✅ Removed admin status from '{email}'")
            return True
            
        except Exception as e:
            print(f"❌ Error removing admin: {e}")
            await db.rollback()
            return False

def print_usage():
    print("Admin Management Script")
    print("Usage:")
    print("  python set_admin.py <email>              - Set user as admin")
    print("  python set_admin.py --list               - List all admins")
    print("  python set_admin.py --remove <email>     - Remove admin status")
    print("  python set_admin.py --help               - Show this help")

async def main():
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "--help":
        print_usage()
    elif command == "--list":
        await list_admins()
    elif command == "--remove":
        if len(sys.argv) < 3:
            print("❌ Email required for --remove")
            print_usage()
            sys.exit(1)
        email = sys.argv[2]
        success = await remove_admin(email)
        sys.exit(0 if success else 1)
    elif command.startswith("--"):
        print(f"❌ Unknown option: {command}")
        print_usage()
        sys.exit(1)
    else:
        # Treat as email address
        email = command
        if "@" not in email:
            print("❌ Invalid email format")
            sys.exit(1)
        
        success = await set_user_admin(email)
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())