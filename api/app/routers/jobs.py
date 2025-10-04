import re
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db import get_db
from app.models import Job, User, Resume, ResumeStatus
from app.schemas import (
    JobCreate,
    JobResponse,
    JobMatchRequest,
    JobMatchResponse,
    JobMatch,
    JobMatchEvidence
)
from app.routers.auth import get_current_user
from app.services.idempotency import check_idempotency_key, store_idempotency_key
from app.services import indexing
from app.utils import generate_id
from app.observability.metrics import track_job_match

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


def parse_job_requirements(description: str) -> List[str]:
    """
    Parse job requirements from description
    
    Simple keyword extraction for MVP:
    - Split on commas, newlines, "and"
    - Common tech keywords
    """
    # Common tech keywords to extract
    tech_keywords = [
        'react', 'vue', 'angular', 'node', 'nodejs', 'python', 'java', 'javascript',
        'typescript', 'go', 'rust', 'c++', 'c#', 'ruby', 'php', 'swift', 'kotlin',
        'django', 'flask', 'express', 'fastapi', 'spring', 'rails',
        'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch',
        'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'terraform',
        'git', 'ci/cd', 'agile', 'scrum', 'rest', 'graphql', 'api',
        'frontend', 'backend', 'fullstack', 'devops', 'machine learning', 'ai'
    ]
    
    requirements = []
    text_lower = description.lower()
    
    # Split on common delimiters first
    parts = re.split(r'[,;\n]|\sand\s', description)
    for part in parts:
        part = part.strip()
        if part and len(part) > 2 and len(part) < 30:
            # Check if it looks like a skill/requirement
            if any(char.isalnum() for char in part):
                requirements.append(part)
    
    # Only add tech keywords that weren't already captured from splitting
    for keyword in tech_keywords:
        if keyword in text_lower:
            # Check if we don't already have a similar requirement
            keyword_title = keyword.title()
            if not any(req.lower() == keyword for req in requirements):
                requirements.append(keyword_title)
    
    # Remove duplicates while preserving order (case-insensitive)
    seen = set()
    unique_requirements = []
    for req in requirements:
        req_lower = req.lower()
        if req_lower not in seen:
            seen.add(req_lower)
            unique_requirements.append(req)
    
    return unique_requirements[:20]  # Limit to 20 requirements


@router.post("", response_model=JobResponse, status_code=201)
async def create_job(
    job_data: JobCreate,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new job posting"""
    user_id = current_user.id if current_user else None
    
    # Prepare request data for idempotency
    request_data = {
        "title": job_data.title,
        "description": job_data.description
    }
    
    # Check idempotency
    try:
        existing_response = await check_idempotency_key(db, idempotency_key, user_id, request_data)
        if existing_response:
            return existing_response
    except ValueError as e:
        raise HTTPException(
            status_code=409,
            detail={"error": {"code": "CONFLICT", "message": str(e)}}
        )
    
    # Parse requirements
    parsed_requirements = parse_job_requirements(job_data.description)
    
    # Create job
    job = Job(
        id=f"job_{generate_id()}",
        owner_id=current_user.id if current_user else None,
        title=job_data.title,
        description=job_data.description,
        parsed_requirements=parsed_requirements,
        created_at=datetime.utcnow()
    )
    
    db.add(job)
    await db.commit()
    
    # Prepare response
    response_data = {
        "id": job.id,
        "title": job.title,
        "description": job.description,
        "parsed_requirements": job.parsed_requirements,
        "created_at": job.created_at.isoformat() + "Z"
    }
    
    # Store idempotency key
    await store_idempotency_key(db, idempotency_key, user_id, request_data, response_data)
    
    return response_data


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get job details"""
    query = select(Job).where(Job.id == job_id)
    result = await db.execute(query)
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "Job not found"}}
        )
    
    return {
        "id": job.id,
        "title": job.title,
        "description": job.description,
        "parsed_requirements": job.parsed_requirements,
        "created_at": job.created_at.isoformat() + "Z"
    }


@router.post("/{job_id}/match", response_model=JobMatchResponse)
async def match_job(
    job_id: str,
    match_request: JobMatchRequest,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Match job requirements with resumes
    
    Returns top N matching resumes with evidence and missing requirements
    """
    # Get job
    job_query = select(Job).where(Job.id == job_id)
    job_result = await db.execute(job_query)
    job = job_result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "Job not found"}}
        )
    
    # Get all completed resumes
    resumes_query = select(Resume).where(Resume.status == ResumeStatus.COMPLETED)
    resumes_result = await db.execute(resumes_query)
    resumes = resumes_result.scalars().all()
    
    if not resumes:
        return {
            "job_id": job_id,
            "matches": []
        }
    
    # Get chunks for all resumes
    resume_ids = [r.id for r in resumes]
    resume_chunks = await indexing.get_resume_chunks_for_matching(db, resume_ids)
    
    # Match each resume
    matches = []
    job_requirements = job.parsed_requirements or []
    job_requirements_lower = [req.lower() for req in job_requirements]
    
    for resume in resumes:
        chunks = resume_chunks.get(resume.id, [])
        
        if not chunks:
            continue
        
        # Concatenate all chunk text
        full_text = " ".join([chunk["text"] for chunk in chunks])
        full_text_lower = full_text.lower()
        
        # Count matching requirements
        matched_requirements = []
        missing_requirements = []
        evidence = []
        evidence_seen = set()  # Track unique paragraphs to avoid duplicates
        
        for req, req_lower in zip(job_requirements, job_requirements_lower):
            if req_lower in full_text_lower:
                matched_requirements.append(req)
                
                # Find evidence snippet with matched keyword and line number
                for chunk in chunks:
                    chunk_text = chunk["text"]
                    chunk_text_lower = chunk_text.lower()
                    
                    if req_lower in chunk_text_lower:
                        # Find the position of the matched keyword
                        match_pos = chunk_text_lower.find(req_lower)
                        
                        # Calculate line number (lines are separated by \n)
                        lines_before_match = chunk_text[:match_pos].count('\n')
                        line_number = lines_before_match + 1
                        
                        # Extract the full paragraph containing the match
                        # Find paragraph boundaries (double newline or start/end of text)
                        text_before = chunk_text[:match_pos]
                        text_after = chunk_text[match_pos:]
                        
                        # Find start of paragraph (last double newline before match, or start of text)
                        para_start = text_before.rfind('\n\n')
                        if para_start == -1:
                            para_start = 0
                        else:
                            para_start += 2  # Skip the double newline
                        
                        # Find end of paragraph (next double newline after match, or end of text)
                        para_end_in_after = text_after.find('\n\n')
                        if para_end_in_after == -1:
                            para_end = len(chunk_text)
                        else:
                            para_end = match_pos + para_end_in_after
                        
                        # Extract the paragraph
                        paragraph = chunk_text[para_start:para_end].strip()
                        
                        # Limit to reasonable length (max 500 chars)
                        if len(paragraph) > 500:
                            # If too long, extract context around match
                            start = max(0, match_pos - 200)
                            end = min(len(chunk_text), match_pos + len(req_lower) + 300)
                            paragraph = chunk_text[start:end].strip()
                            if start > 0:
                                paragraph = "..." + paragraph
                            if end < len(chunk_text):
                                paragraph = paragraph + "..."
                        
                        # Create a hash of the paragraph to detect duplicates
                        para_hash = hash(paragraph[:100])  # Hash first 100 chars for uniqueness
                        
                        # Only add if we haven't seen this paragraph before
                        if para_hash not in evidence_seen:
                            evidence_seen.add(para_hash)
                            
                            # Collect all matched keywords in this paragraph
                            matched_in_para = [req]
                            for other_req in matched_requirements:
                                if other_req != req and other_req.lower() in paragraph.lower():
                                    if other_req not in matched_in_para:
                                        matched_in_para.append(other_req)
                            
                            # Join multiple keywords
                            keyword_display = ", ".join(matched_in_para)
                            
                            evidence.append(JobMatchEvidence(
                                page=chunk["page"],
                                text=paragraph,
                                matched_keyword=keyword_display,
                                line_number=line_number
                            ))
                        break
            else:
                missing_requirements.append(req)
        
        # Calculate match score
        if job_requirements:
            score = len(matched_requirements) / len(job_requirements)
        else:
            score = 0.0
        
        # Only include resumes with some matches
        if score > 0:
            matches.append({
                "resume_id": resume.id,
                "filename": resume.filename,
                "score": score,
                "evidence": evidence[:3],  # Top 3 evidence snippets
                "missing_requirements": missing_requirements,
                "uploaded_at": resume.uploaded_at,
                "resume_db_id": resume.id
            })
    
    # Sort deterministically: (score desc, uploaded_at asc, id asc)
    matches.sort(
        key=lambda x: (-x["score"], x["uploaded_at"], x["resume_db_id"])
    )
    
    # Return top N
    top_matches = matches[:match_request.top_n]
    
    # Build response
    response_matches = []
    for match in top_matches:
        response_matches.append(JobMatch(
            resume_id=match["resume_id"],
            filename=match["filename"],
            score=round(match["score"], 4),
            evidence=match["evidence"],
            missing_requirements=match["missing_requirements"]
        ))
    
    # Track job match metric
    track_job_match()
    
    return {
        "job_id": job_id,
        "matches": response_matches
    }
