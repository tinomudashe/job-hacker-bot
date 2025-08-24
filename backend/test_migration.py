#!/usr/bin/env python3
"""Test the migration logic"""

import sqlalchemy as sa
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

# Get database URL
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("DATABASE_URL not set")
    exit(1)

# Create engine
engine = create_engine(DATABASE_URL)

# Test the migration logic
with engine.connect() as conn:
    # Check if columns exist
    result = conn.execute(text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'users' 
        AND column_name IN ('onboarding_completed', 'onboarding_completed_at')
    """))
    existing_columns = [row[0] for row in result]
    
    print(f"Existing columns: {existing_columns}")
    
    # Test the UPDATE query - use proper parameter binding
    result = conn.execute(text("""
        SELECT COUNT(*) as count
        FROM users 
        WHERE CAST(preferences AS TEXT) LIKE :pattern1
           OR CAST(preferences AS TEXT) LIKE :pattern2
    """).bindparams(
        pattern1='%"onboarding_completed": true%',
        pattern2='%"onboarding_completed":true%'
    ))
    count = result.fetchone()[0]
    print(f"Users to update: {count}")
    
    print("Migration test passed!")