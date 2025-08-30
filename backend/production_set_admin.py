#!/usr/bin/env python3
"""
Production Admin Setup Script
Usage: python production_set_admin.py
This script connects to your production database and sets jnrhapson@gmail.com as admin
"""

import asyncio
import os
from sqlalchemy import select, update, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON
import uuid
from datetime import datetime

# Production database URL - update this with your production database
PRODUCTION_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://your_prod_db_url")

# Create async engine for production
production_engine = create_engine(
    PRODUCTION_DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://"), 
    echo=False
)

# Create async session
async_production_session = async_sessionmaker(
    bind=production_engine.execution_options(compiled_cache={}),
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    external_id = Column(String, unique=True, index=True, nullable=True)
    email = Column(String, unique=False, index=True, nullable=True)
    name = Column(String)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    is_admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

async def set_production_admin():
    """Set jnrhapson@gmail.com as admin in production database"""
    
    admin_email = "jnrhapson@gmail.com"
    
    try:
        async with async_production_session() as db:
            print(f"🔍 Connecting to production database...")
            
            # Check if user exists
            result = await db.execute(
                select(User).where(User.email == admin_email)
            )
            user = result.scalars().first()
            
            if not user:
                print(f"❌ User with email '{admin_email}' not found in production database")
                return False
            
            # Check if already admin
            if getattr(user, 'is_admin', False):
                print(f"✅ User '{admin_email}' is already an admin in production")
                return True
            
            # Set as admin
            await db.execute(
                update(User)
                .where(User.email == admin_email)
                .values(is_admin=True)
            )
            await db.commit()
            
            print(f"✅ SUCCESS: User '{admin_email}' is now an admin in production")
            print(f"   User ID: {user.id}")
            print(f"   Name: {user.name or 'Not set'}")
            print(f"   Admin Access: Premium features unlocked in production")
            return True
            
    except Exception as e:
        print(f"❌ ERROR setting production admin: {e}")
        print(f"   Make sure your DATABASE_URL environment variable is set correctly")
        print(f"   Current DATABASE_URL: {PRODUCTION_DATABASE_URL[:50]}...")
        return False

async def verify_production_admin():
    """Verify admin status in production"""
    try:
        async with async_production_session() as db:
            result = await db.execute(
                select(User).where(User.is_admin == True)
            )
            admins = result.scalars().all()
            
            print(f"\\n📊 Production Admin Users ({len(admins)}):")
            for admin in admins:
                print(f"  - {admin.email} ({admin.name or 'No name'}) - ID: {admin.id}")
                
    except Exception as e:
        print(f"❌ Error verifying production admins: {e}")

async def main():
    print("🚀 Production Admin Setup")
    print("=" * 50)
    print("This script will set jnrhapson@gmail.com as admin in production")
    print()
    
    # Set admin
    success = await set_production_admin()
    
    if success:
        # Verify
        await verify_production_admin()
        print()
        print("✅ Production admin setup complete!")
        print("   The user will now have unlimited access to all features")
        print("   Admin badge will appear after they refresh their browser")
    else:
        print("❌ Production admin setup failed")
        return False
    
    return True

if __name__ == "__main__":
    print("Make sure your DATABASE_URL environment variable points to production")
    print("Example: export DATABASE_URL='postgresql://user:pass@host:5432/dbname'")
    print()
    
    success = asyncio.run(main())
    exit(0 if success else 1)