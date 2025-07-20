from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from typing import AsyncGenerator
from contextlib import asynccontextmanager
from urllib.parse import quote_plus

# Import the SQLAlchemy Instrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

load_dotenv()
print("--- .env file loaded by app/db.py ---")

# Fetch database credentials from environment variables
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

# Construct the database URL for async connection
if all([DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME]):
    encoded_password = quote_plus(DB_PASSWORD)
    DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
else:
    raise ValueError("Database connection details are not fully configured in the environment.")


print(f"DATABASE_URL constructed for SQLAlchemy engine.")

engine = create_async_engine(DATABASE_URL, echo=True)

# Instrument the SQLAlchemy engine's synchronous part
SQLAlchemyInstrumentor().instrument(
    engine=engine.sync_engine, # <-- This is the crucial change
    enable_commenter=True,
    commenter_options={}
)

async_session_maker = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# for dependency injection
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session

@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session with exception handling."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise