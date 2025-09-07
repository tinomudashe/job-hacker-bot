#!/usr/bin/env python3
"""
Fix Admin Privileges Script
This script removes admin privileges from all users except the authorized admins
"""

import asyncio
import os
import sys
from sqlalchemy import select, update

# Add the app directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db import async_session_maker
from app.models_db import User

# Authorized admin emails - only these should have admin access
AUTHORIZED_ADMIN_EMAILS = [
    "jnrhapson@gmail.com", 
    "jnrhapson@yahoo.com"
]

async def fix_admin_privileges():
    """Remove admin privileges from unauthorized users"""
    
    async with async_session_maker() as db:
        try:
            print("🔍 Checking admin users...")
            
            # Get all users with admin privileges
            result = await db.execute(
                select(User).where(User.is_admin == True)
            )
            admin_users = result.scalars().all()
            
            print(f"Found {len(admin_users)} users with admin privileges:")
            
            unauthorized_admins = []
            authorized_admins = []
            
            for user in admin_users:
                if user.email in AUTHORIZED_ADMIN_EMAILS:
                    authorized_admins.append(user)
                    print(f"  ✅ {user.email} - AUTHORIZED")
                else:
                    unauthorized_admins.append(user)
                    print(f"  ❌ {user.email} - UNAUTHORIZED")
            
            if not unauthorized_admins:
                print("\n✅ No unauthorized admin users found!")
                print(f"Only {len(authorized_admins)} authorized admins exist.")
                return True
            
            print(f"\n⚠️  Found {len(unauthorized_admins)} UNAUTHORIZED admin users!")
            print("These users will have their admin privileges removed:")
            
            for user in unauthorized_admins:
                print(f"  - {user.email} (ID: {user.id}, Name: {user.name or 'No name'})")
            
            # Ask for confirmation
            print(f"\nThis will remove admin privileges from {len(unauthorized_admins)} users.")
            confirm = input("Continue? (yes/no): ").lower()
            
            if confirm != 'yes':
                print("❌ Operation cancelled by user")
                return False
            
            # Remove admin privileges from unauthorized users
            for user in unauthorized_admins:
                await db.execute(
                    update(User)
                    .where(User.id == user.id)
                    .values(is_admin=False)
                )
                print(f"  🔧 Removed admin from: {user.email}")
            
            await db.commit()
            
            print(f"\n✅ SUCCESS!")
            print(f"  - Removed admin privileges from {len(unauthorized_admins)} users")
            print(f"  - {len(authorized_admins)} authorized admins remain")
            
            # Final verification
            print(f"\n📋 Final Admin List:")
            for admin in authorized_admins:
                print(f"  ✅ {admin.email}")
            
            return True
            
        except Exception as e:
            print(f"❌ ERROR: {e}")
            await db.rollback()
            return False

async def list_all_admins():
    """List all current admin users for verification"""
    async with async_session_maker() as db:
        try:
            result = await db.execute(
                select(User).where(User.is_admin == True)
            )
            admins = result.scalars().all()
            
            print(f"\n📊 Current Admin Users ({len(admins)}):")
            if not admins:
                print("  No admin users found")
            else:
                for admin in admins:
                    status = "✅ AUTHORIZED" if admin.email in AUTHORIZED_ADMIN_EMAILS else "❌ UNAUTHORIZED"
                    print(f"  {status} - {admin.email} ({admin.name or 'No name'}) - ID: {admin.id}")
                
        except Exception as e:
            print(f"❌ Error listing admins: {e}")

def print_usage():
    print("Fix Admin Privileges Script")
    print("Usage:")
    print("  python fix_admin_privileges.py              - Fix admin privileges (interactive)")
    print("  python fix_admin_privileges.py --list       - List all current admin users")
    print("  python fix_admin_privileges.py --help       - Show this help")

async def main():
    print("🛠️  Admin Privilege Fixer")
    print("=" * 50)
    print(f"Authorized admin emails: {', '.join(AUTHORIZED_ADMIN_EMAILS)}")
    print()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "--help":
            print_usage()
            return
        elif command == "--list":
            await list_all_admins()
            return
        else:
            print(f"❌ Unknown option: {command}")
            print_usage()
            return
    
    # Default action: list current admins then fix if needed
    await list_all_admins()
    print()
    await fix_admin_privileges()

if __name__ == "__main__":
    asyncio.run(main())