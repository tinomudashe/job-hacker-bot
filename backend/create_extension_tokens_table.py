"""
Create the extension_tokens table in the database
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

async def create_table():
    engine = create_async_engine(DATABASE_URL)
    
    async with engine.begin() as conn:
        # Create the extension_tokens table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS extension_tokens (
                id VARCHAR PRIMARY KEY,
                user_id VARCHAR NOT NULL,
                name VARCHAR NOT NULL,
                token_hash VARCHAR NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP,
                expires_at TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            );
        """))
        
        # Create index on user_id for faster queries
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_extension_tokens_user_id 
            ON extension_tokens(user_id);
        """))
        
        print("✅ extension_tokens table created successfully!")

if __name__ == "__main__":
    asyncio.run(create_table())