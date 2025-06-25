from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()
print("--- .env file loaded by app/db.py ---")
print(f"DATABASE_URL from os.getenv: {os.getenv('DATABASE_URL')}")

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(DATABASE_URL, echo=True)

async_session_maker = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# for dependency injection
async def get_db():
    async with async_session_maker() as session:
        yield session 

def get_session():
    return async_session_maker() 