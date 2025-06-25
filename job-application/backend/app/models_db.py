import uuid
from sqlalchemy import (
    create_engine,
    Column,
    String,
    Text,
    ForeignKey,
    DateTime,
    Boolean,
    Integer,
    func,
    Table,
    JSON,
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

# Define the base class for declarative models
Base = declarative_base()

def generate_uuid():
    return str(uuid.uuid4())

class Page(Base):
    __tablename__ = "pages"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="pages")
    chat_messages = relationship("ChatMessage", back_populates="page", cascade="all, delete-orphan")

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    external_id = Column(String, unique=True, index=True, nullable=True)
    email = Column(String, unique=False, index=True, nullable=True)
    name = Column(String)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    address = Column(String, nullable=True)
    linkedin = Column(String, nullable=True)
    preferred_language = Column(String, nullable=True)
    date_of_birth = Column(String, nullable=True)
    profile_headline = Column(String, nullable=True)
    skills = Column(Text, nullable=True)  # JSON or comma-separated
    profile_picture_url = Column(String, nullable=True)
    picture = Column(String, nullable=True)
    active = Column(Boolean, default=True)
    hashed_password = Column(String, nullable=True)
    preferences = Column(Text)
    faiss_index_path = Column(String, nullable=True)

    applications = relationship("Application", back_populates="user", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="user", cascade="all, delete-orphan")
    subscription = relationship("Subscription", back_populates="user", uselist=False, cascade="all, delete-orphan")
    generated_cvs = relationship("GeneratedCV", back_populates="user", cascade="all, delete-orphan")
    generated_cover_letters = relationship("GeneratedCoverLetter", back_populates="user", cascade="all, delete-orphan")
    resume = relationship("Resume", back_populates="user", uselist=False, cascade="all, delete-orphan")
    pages = relationship("Page", back_populates="user", cascade="all, delete-orphan")

class Document(Base):
    __tablename__ = "documents"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    type = Column(String)
    name = Column(String)
    content = Column(Text, nullable=True)
    vector_store_path = Column(String, nullable=True)
    date_created = Column(DateTime(timezone=True), server_default=func.now())
    date_updated = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    user = relationship("User", back_populates="documents")

class Application(Base):
    __tablename__ = "applications"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    job_title = Column(String)
    company_name = Column(String)
    job_url = Column(String)
    status = Column(String, default="draft")
    notes = Column(Text)
    date_applied = Column(DateTime(timezone=True))
    success = Column(Boolean, default=True)

    user = relationship("User", back_populates="applications")

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    type = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    date = Column(DateTime(timezone=True), server_default=func.now())
    read = Column(Boolean, default=False)

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    page_id = Column(String, ForeignKey("pages.id"), nullable=True)
    message = Column(Text, nullable=False)
    is_user_message = Column(Boolean, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="chat_messages")
    page = relationship("Page", back_populates="chat_messages")

class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    stripe_customer_id = Column(String, unique=True, index=True, nullable=True)
    stripe_subscription_id = Column(String, unique=True, index=True, nullable=True)
    plan = Column(String, default="free", nullable=False)  # e.g., 'free', 'premium'
    status = Column(String, default="active", nullable=False) # e.g., 'active', 'past_due', 'canceled'
    
    user = relationship("User", back_populates="subscription")

class GeneratedCV(Base):
    __tablename__ = 'generated_cvs'
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    content_html = Column(Text, nullable=False)

    user = relationship("User", back_populates="generated_cvs")

class GeneratedCoverLetter(Base):
    __tablename__ = 'generated_cover_letters'
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    content = Column(Text, nullable=False)

    user = relationship("User", back_populates="generated_cover_letters")

class Resume(Base):
    __tablename__ = 'resumes'
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey('users.id'), nullable=False, unique=True)
    data = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    user = relationship("User", back_populates="resume") 