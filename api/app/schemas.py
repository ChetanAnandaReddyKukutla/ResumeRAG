from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr


# Health & Meta
class HealthResponse(BaseModel):
    status: str
    time: str


class MetaResponse(BaseModel):
    name: str
    version: str
    api_root: str
    endpoints: List[str]
    features: Dict[str, bool]


# User schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: str
    email: str
    role: str


# Resume schemas
class ResumeUploadResponse(BaseModel):
    id: str
    filename: str
    status: str
    uploaded_at: str


class ResumeSnippet(BaseModel):
    page: int
    text: str
    start: int
    end: int


class ResumeListItem(BaseModel):
    id: str
    name: Optional[str] = None
    snippet: Optional[str] = None
    score: Optional[float] = None
    uploaded_at: str


class ResumeListResponse(BaseModel):
    items: List[ResumeListItem]
    next_offset: Optional[int] = None


class ResumeDetailResponse(BaseModel):
    id: str
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    parsed_text_snippets: List[ResumeSnippet]
    uploaded_at: str
    status: str


# Ask schemas
class AskRequest(BaseModel):
    query: str
    k: int = Field(default=5, ge=1, le=100)


class AnswerSnippet(BaseModel):
    page: int
    text: str
    start: int
    end: int


class Answer(BaseModel):
    resume_id: str
    filename: str
    score: float
    snippets: List[AnswerSnippet]


class AskResponse(BaseModel):
    query_id: str
    answers: List[Answer]
    cached: bool


# Job schemas
class JobCreate(BaseModel):
    title: str
    description: str


class JobResponse(BaseModel):
    id: str
    title: str
    description: str
    parsed_requirements: Optional[List[str]] = None
    created_at: str


class JobMatchRequest(BaseModel):
    top_n: int = Field(default=10, ge=1, le=100)


class JobMatchEvidence(BaseModel):
    page: int
    text: str
    matched_keyword: str
    line_number: Optional[int] = None


class JobMatch(BaseModel):
    resume_id: str
    filename: str
    score: float
    evidence: List[JobMatchEvidence]
    missing_requirements: List[str]


class JobMatchResponse(BaseModel):
    job_id: str
    matches: List[JobMatch]


# Error schemas
class ErrorDetail(BaseModel):
    code: str
    message: str
    field: Optional[str] = None


class ErrorResponse(BaseModel):
    error: ErrorDetail
