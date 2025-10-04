import os
import uuid
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, UploadFile, File, Form, Header, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from pathlib import Path

from app.db import get_db
from app.models import Resume, ResumeStatus, ResumeVisibility, User
from app.schemas import (
    ResumeUploadResponse,
    ResumeListResponse,
    ResumeListItem,
    ResumeDetailResponse,
    ResumeSnippet,
    ErrorResponse
)
from app.routers.auth import get_current_user
from app.services import parsing, embedding, indexing, pii
from app.services.idempotency import check_idempotency_key, store_idempotency_key
from app.services.upload_security import validate_file_upload, sanitize_filename
from app.services.auditing import log_pii_access, has_pii_access_permission
from app.utils import get_upload_dir, generate_id
from app.observability.metrics import track_resume_upload, track_resume_parse_error

router = APIRouter(prefix="/api/resumes", tags=["resumes"])


@router.post("", response_model=ResumeUploadResponse, status_code=201)
async def upload_resume(
    file: UploadFile = File(...),
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    owner_id: Optional[str] = Form(None),
    visibility: str = Form("private"),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload and parse a resume"""
    # Validate and scan file for security
    content, file_hash = await validate_file_upload(file)
    
    # Sanitize filename
    safe_filename = sanitize_filename(file.filename or "resume.txt")
    
    # Determine user_id for idempotency check
    user_id = current_user.id if current_user else owner_id
    
    # Prepare request data for idempotency
    request_data = {
        "filename": safe_filename,
        "owner_id": owner_id,
        "visibility": visibility,
        "file_hash": file_hash  # Include hash in idempotency check
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
    
    # Get file extension
    file_ext = Path(safe_filename).suffix.lower()
    
    # Save uploaded file
    upload_dir = get_upload_dir()
    file_id = generate_id("resume_")
    file_path = os.path.join(upload_dir, f"{file_id}{file_ext}")
    
    # Save file content
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Check for duplicate by file_hash
    duplicate_query = select(Resume).where(Resume.file_hash == file_hash)
    duplicate_result = await db.execute(duplicate_query)
    duplicate_resume = duplicate_result.scalar_one_or_none()
    
    if duplicate_resume:
        # Return existing resume
        response_data = {
            "id": duplicate_resume.id,
            "filename": duplicate_resume.filename,
            "status": duplicate_resume.status.value,
            "uploaded_at": duplicate_resume.uploaded_at.isoformat() + "Z"
        }
        
        # Store idempotency key
        await store_idempotency_key(db, idempotency_key, user_id, request_data, response_data)
        
        return response_data
    
    # Create resume record
    resume = Resume(
        id=file_id,
        owner_id=owner_id or (current_user.id if current_user else None),
        filename=file.filename,
        status=ResumeStatus.PROCESSING,
        visibility=ResumeVisibility(visibility),
        uploaded_at=datetime.utcnow(),
        size_bytes=len(content),
        file_hash=file_hash,
        file_path=file_path
    )
    
    db.add(resume)
    await db.commit()
    
    # Parse resume (synchronous for MVP)
    try:
        if file_ext == '.zip':
            # Handle ZIP files
            import tempfile
            import shutil
            temp_dir = tempfile.mkdtemp()
            
            try:
                extracted_files = parsing.extract_zip(file_path, temp_dir)
                
                # Process first file found (for MVP)
                if extracted_files:
                    parse_result = parsing.parse_resume(extracted_files[0], os.path.basename(extracted_files[0]))
                else:
                    raise ValueError("No valid files found in ZIP")
            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)
        else:
            parse_result = parsing.parse_resume(file_path, file.filename)
        
        # Update resume with parsed metadata
        resume.parsing_hash = parse_result.parsing_hash
        resume.parsed_metadata = parse_result.metadata
        resume.status = ResumeStatus.COMPLETED
        
        # Create and store chunks with embeddings
        chunks = embedding.chunk_resume_by_pages(parse_result)
        await indexing.insert_resume_chunks(db, resume.id, chunks)
        
        await db.commit()
        
        # Track successful upload
        track_resume_upload('success')
        
    except Exception as e:
        print(f"Parse error: {e}")
        resume.status = ResumeStatus.FAILED
        track_resume_parse_error()
        track_resume_upload('failed_processing')
        await db.commit()
    
    # Prepare response
    response_data = {
        "id": resume.id,
        "filename": resume.filename,
        "status": resume.status.value,
        "uploaded_at": resume.uploaded_at.isoformat() + "Z"
    }
    
    # Store idempotency key
    await store_idempotency_key(db, idempotency_key, user_id, request_data, response_data)
    
    return response_data


@router.get("", response_model=ResumeListResponse)
async def list_resumes(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    q: Optional[str] = Query(None),
    owner_id: Optional[str] = Query(None),
    visibility: Optional[str] = Query(None),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List resumes with pagination and optional search"""
    # Build query
    query = select(Resume).where(Resume.status == ResumeStatus.COMPLETED)
    
    # Filter by owner_id
    if owner_id:
        query = query.where(Resume.owner_id == owner_id)
    
    # Filter by visibility
    if visibility:
        query = query.where(Resume.visibility == ResumeVisibility(visibility))
    
    # Apply offset and limit
    query = query.offset(offset).limit(limit + 1)  # Get one extra to check if there are more
    
    # Order deterministically
    query = query.order_by(Resume.uploaded_at.desc(), Resume.id.asc())
    
    result = await db.execute(query)
    resumes = result.scalars().all()
    
    # Check if there are more results
    has_more = len(resumes) > limit
    if has_more:
        resumes = resumes[:limit]
    
    # Build response items
    items = []
    for resume in resumes:
        item = ResumeListItem(
            id=resume.id,
            name=resume.parsed_metadata.get("name") if resume.parsed_metadata else None,
            snippet=None,  # TODO: Add snippet from first chunk
            score=None,
            uploaded_at=resume.uploaded_at.isoformat() + "Z"
        )
        items.append(item)
    
    # Calculate next_offset
    next_offset = offset + limit if has_more else None
    
    return {
        "items": items,
        "next_offset": next_offset
    }


@router.get("/{resume_id}", response_model=ResumeDetailResponse)
async def get_resume(
    resume_id: str,
    include_pii: bool = Query(False),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get resume details with parsed snippets"""
    # Get resume
    query = select(Resume).where(Resume.id == resume_id)
    result = await db.execute(query)
    resume = result.scalar_one_or_none()
    
    if not resume:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "Resume not found"}}
        )
    
    # Check PII access permission
    user_role = "user"  # default for non-authenticated
    if current_user:
        user_role = current_user.role.value
        
        # If requesting PII and user is not owner, check permission and log access
        if include_pii:
            # Check permission
            if not await has_pii_access_permission(current_user, resume.owner_id):
                raise HTTPException(
                    status_code=403,
                    detail={"error": {"code": "FORBIDDEN", "message": "Not authorized to view PII for this resume"}}
                )
            
            # Log PII access
            await log_pii_access(
                db=db,
                actor_user_id=str(current_user.id),
                resume_id=resume_id,
                action="VIEW_PII",
                reason="Resume detail view with include_pii=true",
                request_id=None  # TODO: Add request_id tracking middleware
            )
    
    # Get chunks
    from app.models import ResumeChunk
    chunks_query = select(ResumeChunk).where(ResumeChunk.resume_id == resume_id).order_by(
        ResumeChunk.page, ResumeChunk.start_offset
    )
    chunks_result = await db.execute(chunks_query)
    chunks = chunks_result.scalars().all()
    
    # Determine redaction based on include_pii flag and permissions
    should_redact = not include_pii
    
    # Redact metadata
    metadata = resume.parsed_metadata or {}
    if should_redact:
        redacted_metadata = pii.redact_metadata(metadata, user_role)
    else:
        redacted_metadata = metadata
    
    # Build snippets
    snippets = []
    for chunk in chunks:
        if should_redact:
            snippet_text = pii.redact_snippet_text(chunk.text, user_role)
        else:
            snippet_text = chunk.text
            
        snippet = ResumeSnippet(
            page=chunk.page,
            text=snippet_text,
            start=chunk.start_offset,
            end=chunk.end_offset
        )
        snippets.append(snippet)
    
    return {
        "id": resume.id,
        "name": redacted_metadata.get("name"),
        "email": redacted_metadata.get("email"),
        "phone": redacted_metadata.get("phone"),
        "parsed_text_snippets": snippets,
        "uploaded_at": resume.uploaded_at.isoformat() + "Z",
        "status": resume.status.value
    }


@router.get("/{resume_id}/download")
async def download_resume(
    resume_id: str,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Download the original resume file"""
    # Get resume
    query = select(Resume).where(Resume.id == resume_id)
    result = await db.execute(query)
    resume = result.scalar_one_or_none()
    
    if not resume:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "Resume not found"}}
        )
    
    # Check if file exists
    if not resume.file_path or not os.path.exists(resume.file_path):
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "FILE_NOT_FOUND", "message": "Resume file not found on server"}}
        )
    
    # Return the file
    return FileResponse(
        path=resume.file_path,
        filename=resume.filename,
        media_type="application/octet-stream"
    )

