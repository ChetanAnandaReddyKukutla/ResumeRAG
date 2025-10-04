from typing import List, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from sqlalchemy.sql import and_
import uuid
import time

from app.models import Resume, ResumeChunk
from app.observability.metrics import track_vector_search


async def insert_resume_chunks(
    db: AsyncSession,
    resume_id: str,
    chunks: List[dict]
) -> None:
    """
    Insert resume chunks with embeddings into database
    
    Args:
        db: Database session
        resume_id: ID of the resume
        chunks: List of chunk dicts with page, start_offset, end_offset, text, embedding
    """
    for chunk in chunks:
        chunk_obj = ResumeChunk(
            id=f"chunk_{uuid.uuid4().hex[:16]}",
            resume_id=resume_id,
            page=chunk["page"],
            start_offset=chunk["start_offset"],
            end_offset=chunk["end_offset"],
            text=chunk["text"],
            embedding=chunk["embedding"]
        )
        db.add(chunk_obj)
    
    await db.commit()


async def search_resume_chunks(
    db: AsyncSession,
    query_embedding: List[float],
    limit: int = 20
) -> List[Tuple[ResumeChunk, float]]:
    """
    Search for similar resume chunks using pgvector
    
    Args:
        db: Database session
        query_embedding: Query embedding vector
        limit: Maximum number of results
    
    Returns:
        List of (chunk, distance) tuples
    """
    start_time = time.time()
    
    # Convert embedding to pgvector format
    embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
    
    # Use pgvector's <-> operator for L2 distance
    # Note: Using positional parameters ($1, $2) for asyncpg compatibility
    # Inline embedding vector literal (constructed from floats) to avoid parameter binding
    query_sql = f"""
        SELECT 
            id, resume_id, page, start_offset, end_offset, text,
            embedding <-> '{embedding_str}'::vector AS distance
        FROM resume_chunks
        WHERE embedding IS NOT NULL
        ORDER BY distance ASC
        LIMIT :limit
    """
    query = text(query_sql)
    result = await db.execute(query, {"limit": limit})
    
    rows = result.fetchall()
    
    # Convert to chunk objects with scores
    chunks_with_scores = []
    for row in rows:
        chunk = ResumeChunk(
            id=row[0],
            resume_id=row[1],
            page=row[2],
            start_offset=row[3],
            end_offset=row[4],
            text=row[5],
        )
        distance = row[6]
        # Convert distance to score: score = 1 / (1 + distance)
        score = 1.0 / (1.0 + distance)
        chunks_with_scores.append((chunk, score))
    
    # Track metrics
    duration = time.time() - start_time
    track_vector_search(duration)
    
    return chunks_with_scores


async def group_chunks_by_resume(
    db: AsyncSession,
    chunks_with_scores: List[Tuple[ResumeChunk, float]],
    top_k: int = 5
) -> List[dict]:
    """
    Group chunks by resume and aggregate scores
    
    Args:
        db: Database session
        chunks_with_scores: List of (chunk, score) tuples
        top_k: Number of top resumes to return
    
    Returns:
        List of resume results with aggregated scores and snippets
    """
    # Group by resume_id
    resume_groups = {}
    
    for chunk, score in chunks_with_scores:
        resume_id = chunk.resume_id
        
        if resume_id not in resume_groups:
            resume_groups[resume_id] = {
                "resume_id": resume_id,
                "chunks": [],
                "scores": []
            }
        
        resume_groups[resume_id]["chunks"].append({
            "page": chunk.page,
            "text": chunk.text,
            "start": chunk.start_offset,
            "end": chunk.end_offset
        })
        resume_groups[resume_id]["scores"].append(score)
    
    # Aggregate scores (use max score for each resume)
    resume_results = []
    for resume_id, data in resume_groups.items():
        max_score = max(data["scores"])
        
        # Get resume metadata for tie-breaking
        resume_query = select(Resume).where(Resume.id == resume_id)
        result = await db.execute(resume_query)
        resume = result.scalar_one_or_none()
        
        if resume:
            resume_results.append({
                "resume_id": resume_id,
                "filename": resume.filename,
                "score": max_score,
                "snippets": data["chunks"][:3],  # Top 3 snippets per resume
                "uploaded_at": resume.uploaded_at,
                "resume_db_id": resume.id
            })
    
    # Sort deterministically: (score desc, uploaded_at asc, id asc)
    resume_results.sort(
        key=lambda x: (-x["score"], x["uploaded_at"], x["resume_db_id"])
    )
    
    # Return top k
    return resume_results[:top_k]


async def get_resume_chunks_for_matching(
    db: AsyncSession,
    resume_ids: List[str]
) -> dict:
    """
    Get all chunks for specified resumes for job matching
    
    Args:
        db: Database session
        resume_ids: List of resume IDs
    
    Returns:
        Dict mapping resume_id to list of chunk texts
    """
    query = select(ResumeChunk).where(
        ResumeChunk.resume_id.in_(resume_ids)
    )
    
    result = await db.execute(query)
    chunks = result.scalars().all()
    
    # Group by resume
    resume_chunks = {}
    for chunk in chunks:
        if chunk.resume_id not in resume_chunks:
            resume_chunks[chunk.resume_id] = []
        resume_chunks[chunk.resume_id].append({
            "page": chunk.page,
            "text": chunk.text
        })
    
    return resume_chunks
