import hashlib
from datetime import datetime, timedelta
import copy
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db import get_db
from app.models import User, AskCache
from app.schemas import AskRequest, AskResponse, Answer, AnswerSnippet
from app.routers.auth import get_current_user
from app.services import embedding, indexing, pii
from app.utils import generate_id

router = APIRouter(prefix="/api/ask", tags=["ask"])


def compute_query_hash(query: str, k: int) -> str:
    """Compute hash of query for caching"""
    cache_key = f"{query}:{k}"
    return hashlib.sha256(cache_key.encode('utf-8')).hexdigest()


@router.post("", response_model=AskResponse)
async def ask_question(
    request: AskRequest,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Ask a question and get relevant resume matches with snippets
    
    Args:
        query: Natural language query
        k: Number of top resumes to return
    
    Returns:
        Ranked list of resumes with relevant snippets and scores
    """
    query = request.query
    k = request.k
    
    # Check cache / fetch existing record
    query_hash = compute_query_hash(query, k)
    cache_query = select(AskCache).where(AskCache.query_hash == query_hash)
    cache_result = await db.execute(cache_query)
    cached: AskCache | None = cache_result.scalar_one_or_none()

    TESTING = __import__("os").environ.get("TESTING") == "1"
    # NOTE: Using naive UTC datetimes for consistency with existing schema (TIMESTAMP WITHOUT TIME ZONE)
    now = datetime.utcnow()
    if isinstance(cached, AskCache) and hasattr(cached, "expires_at"):
        is_valid_cache_bool = (not TESTING) and (cached.expires_at > now)
    else:
        is_valid_cache_bool = False
    if is_valid_cache_bool is True:
        # Serve cached response (copy to avoid mutating stored JSON)
        response_data_cached = copy.deepcopy(cached.response_json)  # type: ignore[arg-type]
        if isinstance(response_data_cached, dict):
            response_data_cached["cached"] = True
        return response_data_cached
    
    # Generate query embedding
    query_embedding = embedding.hash_embedding(query)
    
    # Search for similar chunks
    chunks_with_scores = await indexing.search_resume_chunks(
        db, query_embedding, limit=k * 5  # Get more chunks to ensure we have k resumes
    )
    
    # Group by resume
    resume_results = await indexing.group_chunks_by_resume(db, chunks_with_scores, top_k=k)
    
    # Determine user role for PII redaction
    user_role = current_user.role.value if current_user else "user"
    
    # Build response
    answers = []
    for result in resume_results:
        # Redact snippets
        snippets = []
        for snippet in result["snippets"]:
            snippets.append(AnswerSnippet(
                page=snippet["page"],
                text=pii.redact_snippet_text(snippet["text"], user_role),
                start=snippet["start"],
                end=snippet["end"]
            ))
        
        answer = Answer(
            resume_id=result["resume_id"],
            filename=result["filename"],
            score=round(result["score"], 4),
            snippets=snippets
        )
        answers.append(answer)
    
    query_id = f"q_{generate_id()}"
    
    response_data = {
        "query_id": query_id,
        "answers": [
            {
                "resume_id": a.resume_id,
                "filename": a.filename,
                "score": a.score,
                "snippets": [
                    {"page": s.page, "text": s.text, "start": s.start, "end": s.end}
                    for s in a.snippets
                ]
            }
            for a in answers
        ],
        "cached": False
    }
    
    # Upsert / refresh cache entry (expire in 1 hour)
    if isinstance(cached, AskCache):
        # Update existing record
        setattr(cached, "response_json", response_data)  # type: ignore[arg-type]
        setattr(cached, "created_at", now)
        setattr(cached, "expires_at", now + timedelta(hours=1))
    else:
        cache_record = AskCache(
            query_hash=query_hash,
            response_json=response_data,
            created_at=now,
            expires_at=now + timedelta(hours=1)
        )
        db.add(cache_record)
    await db.commit()
    
    return response_data
