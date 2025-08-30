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
    Index,
)
from sqlalchemy.orm import relationship, declarative_base, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.dialects.postgresql import UUID
from typing import List, Optional
from pgvector.sqlalchemy import Vector

# Define the base class for declarative models with AsyncAttrs for proper async support
Base = declarative_base(cls=AsyncAttrs)

def generate_uuid():
    return str(uuid.uuid4())

class Page(Base):
    __tablename__ = "pages"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    last_opened_at = Column(DateTime(timezone=True), nullable=True, index=True)

    user = relationship("User", back_populates="pages")
    chat_messages = relationship("ChatMessage", back_populates="page", cascade="all, delete-orphan")

    # Add composite index for user_id + last_opened_at for efficient page listing
    __table_args__ = (
        Index('ix_pages_user_last_opened', 'user_id', 'last_opened_at'),
        Index('ix_pages_user_created', 'user_id', 'created_at'),
    )

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
    subscribed_to_marketing = Column(Boolean, default=True, nullable=False)
    onboarding_completed = Column(Boolean, default=False, nullable=False)
    onboarding_completed_at = Column(DateTime(timezone=True), nullable=True)
    is_admin = Column(Boolean, default=False, nullable=False)  # Admin flag for premium access
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    applications = relationship("Application", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    chat_messages = relationship("ChatMessage", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    subscription = relationship("Subscription", back_populates="user", uselist=False, cascade="all, delete-orphan", passive_deletes=True)
    generated_cvs = relationship("GeneratedCV", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    generated_cover_letters = relationship("GeneratedCoverLetter", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    resume = relationship("Resume", back_populates="user", uselist=False, cascade="all, delete-orphan", passive_deletes=True)
    tailored_resumes = relationship("TailoredResume", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    pages = relationship("Page", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    user_preferences = relationship("UserPreference", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    user_behaviors = relationship("UserBehavior", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    saved_responses = relationship("SavedApplicationResponse", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)

class Document(Base):
    __tablename__ = "documents"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"))
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
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"))
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
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    page_id = Column(String, ForeignKey("pages.id"), nullable=True, index=True)
    message = Column(Text, nullable=False)
    is_user_message = Column(Boolean, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="chat_messages")
    page = relationship("Page", back_populates="chat_messages")

    # Add composite indexes for efficient message queries
    __table_args__ = (
        Index('ix_chat_messages_user_page_created', 'user_id', 'page_id', 'created_at'),
        Index('ix_chat_messages_page_created', 'page_id', 'created_at'),
        Index('ix_chat_messages_user_created', 'user_id', 'created_at'),
    )

class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    stripe_customer_id = Column(String, unique=True, index=True, nullable=True)
    stripe_subscription_id = Column(String, unique=True, index=True, nullable=True)
    plan = Column(String, default="free", nullable=False)  # e.g., 'free', 'premium'
    status = Column(String, default="active", nullable=False) # e.g., 'active', 'past_due', 'canceled'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="subscription")

class GeneratedCV(Base):
    __tablename__ = 'generated_cvs'
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    content_html = Column(Text, nullable=False)

    user = relationship("User", back_populates="generated_cvs")

class GeneratedCoverLetter(Base):
    __tablename__ = 'generated_cover_letters'
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    content = Column(Text, nullable=False)

    user = relationship("User", back_populates="generated_cover_letters")

class Resume(Base):
    __tablename__ = 'resumes'
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey('users.id', ondelete="CASCADE"), nullable=False, unique=True)
    data = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    user = relationship("User", back_populates="resume")

class TailoredResume(Base):
    __tablename__ = "tailored_resumes"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    base_resume_id = Column(String, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False)
    job_title = Column(String, nullable=True)
    company_name = Column(String, nullable=True)
    job_description = Column(Text, nullable=True)
    tailored_data = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="tailored_resumes")
    base_resume = relationship("Resume")

class UserPreference(Base):
    __tablename__ = 'user_preferences'
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    preference_key = Column(String, nullable=False)
    preference_value = Column(Text, nullable=False)  # JSON string
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

    user = relationship("User", back_populates="user_preferences")

class UserBehavior(Base):
    __tablename__ = 'user_behaviors'
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    action_type = Column(String, nullable=False)  # e.g., 'job_search', 'cover_letter_generation', 'document_upload'
    log_level = Column(String, default="INFO", nullable=False) # INFO, WARNING, ERROR
    context = Column(JSON, nullable=True)  # JSON column with action context
    success = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="user_behaviors")

class SavedApplicationResponse(Base):
    __tablename__ = "saved_application_responses"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    field_category = Column(String, nullable=False, index=True)  # e.g., "personal.firstName", "legal.workAuth"
    field_label = Column(String, nullable=False)  # Human-readable label
    field_value = Column(Text, nullable=False)  # The saved value
    is_default = Column(Boolean, default=False)  # If this should be the default value for this field
    usage_count = Column(Integer, default=0)  # Track how often this is used
    last_used = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    
    user = relationship("User", back_populates="saved_responses")
    
    # Composite index for efficient lookups
    __table_args__ = (
        Index('ix_saved_responses_user_category', 'user_id', 'field_category'),
        Index('ix_saved_responses_user_default', 'user_id', 'is_default'),
    )

class MarketingEmailTemplate(Base):
    __tablename__ = 'marketing_email_templates'
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False, unique=True)
    subject = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now()) 

class LangchainPgCollection(Base):
    __tablename__ = "langchain_pg_collection"
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String)
    cmetadata = Column(JSON)

class LangchainPgEmbedding(Base):
    __tablename__ = "langchain_pg_embedding"
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    collection_id = Column(UUID(as_uuid=True), ForeignKey("langchain_pg_collection.uuid", ondelete="CASCADE"))
    embedding = Column(Vector(768))  # Using 768 dimensions for Google's text-embedding-004
    document = Column(String, nullable=True)
    cmetadata = Column(JSON, nullable=True)
    custom_id = Column(String, nullable=True)

    collection = relationship("LangchainPgCollection", back_populates="embeddings")

LangchainPgCollection.embeddings = relationship(
    "LangchainPgEmbedding",
    back_populates="collection",
    cascade="all, delete-orphan",
    passive_deletes=True,
) 