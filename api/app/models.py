from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, JSON, BigInteger, Enum as SQLEnum, Boolean, LargeBinary
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
import enum

from app.db import Base


class UserRole(str, enum.Enum):
    USER = "user"
    RECRUITER = "recruiter"
    ADMIN = "admin"


class ResumeStatus(str, enum.Enum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ResumeVisibility(str, enum.Enum):
    PRIVATE = "private"
    TEAM = "team"
    PUBLIC = "public"


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Account security fields
    failed_login_count = Column(Integer, default=0, nullable=False)
    last_failed_login = Column(DateTime, nullable=True)
    locked_until = Column(DateTime, nullable=True, index=True)

    resumes = relationship("Resume", back_populates="owner", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="owner", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(String, primary_key=True)
    owner_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    filename = Column(String, nullable=False)
    status = Column(SQLEnum(ResumeStatus), default=ResumeStatus.PROCESSING, nullable=False)
    visibility = Column(SQLEnum(ResumeVisibility), default=ResumeVisibility.PRIVATE, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    size_bytes = Column(BigInteger, nullable=True)
    file_hash = Column(String, nullable=True, index=True)
    parsing_hash = Column(String, nullable=True)
    parsed_metadata = Column(JSON, nullable=True)  # name, email, phone, etc.
    file_path = Column(String, nullable=True)

    owner = relationship("User", back_populates="resumes")
    chunks = relationship("ResumeChunk", back_populates="resume", cascade="all, delete-orphan")


class ResumeChunk(Base):
    __tablename__ = "resume_chunks"

    id = Column(String, primary_key=True)
    resume_id = Column(String, ForeignKey("resumes.id"), nullable=False, index=True)
    page = Column(Integer, nullable=False)
    start_offset = Column(Integer, nullable=False)
    end_offset = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    embedding = Column(Vector(1536), nullable=True)  # pgvector column

    resume = relationship("Resume", back_populates="chunks")


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True)
    owner_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    parsed_requirements = Column(JSON, nullable=True)  # list of required skills/keywords
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    owner = relationship("User", back_populates="jobs")


class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"

    key = Column(String, primary_key=True)
    user_id = Column(String, nullable=True, index=True)
    request_hash = Column(String, nullable=False)
    response_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)


class AskCache(Base):
    __tablename__ = "ask_cache"

    query_hash = Column(String, primary_key=True)
    response_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String, nullable=False, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    revoked = Column(Boolean, default=False, nullable=False, index=True)
    
    user = relationship("User", back_populates="refresh_tokens")


class PIIStore(Base):
    __tablename__ = "pii_store"

    id = Column(String, primary_key=True)
    resume_id = Column(String, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    field_name = Column(String, nullable=False)  # 'email', 'phone', etc.
    encrypted_value = Column(LargeBinary, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class PIIAccessLog(Base):
    __tablename__ = "pii_access_log"

    id = Column(String, primary_key=True)
    actor_user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    resume_id = Column(String, ForeignKey("resumes.id"), nullable=False, index=True)
    action = Column(String, nullable=False)  # VIEW_PII, EXPORT_PII, etc.
    reason = Column(Text, nullable=True)
    request_id = Column(String, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
