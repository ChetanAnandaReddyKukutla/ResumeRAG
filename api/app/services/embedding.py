import os
import hashlib
import time
from typing import List, Optional, Tuple
import numpy as np

from app.observability.metrics import track_embedding_generation


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 200) -> List[str]:
    """
    Chunk text into overlapping segments
    
    Args:
        text: Text to chunk
        chunk_size: Size of each chunk in characters
        overlap: Overlap between chunks in characters
    
    Returns:
        List of text chunks
    """
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunk = text[start:end]
        
        if chunk.strip():  # Only add non-empty chunks
            chunks.append(chunk)
        
        if end >= text_length:
            break
            
        start += (chunk_size - overlap)
    
    return chunks


def hash_embedding(text: str, dim: int = 1536) -> List[float]:
    """
    Generate deterministic embedding from text using SHA256 hash
    
    This creates a reproducible embedding that:
    1. Hashes the text with SHA256
    2. Converts hex pairs into integers
    3. Maps to floats in [-1, 1]
    4. Pads or truncates to desired dimension
    5. Normalizes to unit length
    
    Args:
        text: Text to embed
        dim: Dimension of output vector (default 1536 for OpenAI compatibility)
    
    Returns:
        List of floats representing the embedding vector
    """
    start_time = time.time()
    
    # Compute SHA256 hash
    h = hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    # Convert hex string to list of integers
    # Each pair of hex characters becomes one int (0-255)
    hex_ints = []
    for i in range(0, len(h), 2):
        hex_ints.append(int(h[i:i+2], 16))
    
    # Map integers to floats in range [-1, 1]
    # 0-255 -> -1 to 1
    floats = [(x / 127.5) - 1.0 for x in hex_ints]
    
    # Pad or truncate to desired dimension
    if len(floats) < dim:
        # Pad by repeating the sequence
        repeats = (dim // len(floats)) + 1
        floats = (floats * repeats)[:dim]
    else:
        floats = floats[:dim]
    
    # Convert to numpy array for normalization
    vector = np.array(floats, dtype=np.float32)
    
    # Normalize to unit length
    norm = np.linalg.norm(vector)
    if norm > 0:
        vector = vector / norm
    
    # Track metrics
    duration = time.time() - start_time
    track_embedding_generation('hash-sha256', duration)
    
    return vector.tolist()


async def get_embedding(text: str, use_openai: bool = False) -> List[float]:
    """
    Get embedding for text, using OpenAI if available, otherwise fallback to hash
    
    Args:
        text: Text to embed
        use_openai: Whether to use OpenAI API (requires OPENAI_API_KEY)
    
    Returns:
        Embedding vector as list of floats
    """
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if use_openai and openai_key:
        try:
            import openai
            openai.api_key = openai_key
            
            response = await openai.Embedding.acreate(
                input=text,
                model="text-embedding-ada-002"
            )
            return response['data'][0]['embedding']
        except Exception as e:
            print(f"OpenAI embedding failed, falling back to hash: {e}")
            return hash_embedding(text)
    else:
        # Use deterministic hash embedding
        return hash_embedding(text)


def create_chunks_with_embeddings(parse_result, page_chunk_map: List[Tuple[int, str]]) -> List[dict]:
    """
    Create chunks with embeddings from parse result
    
    Args:
        parse_result: ParseResult from parsing service
        page_chunk_map: List of (page_number, chunk_text) tuples
    
    Returns:
        List of chunk dictionaries with page, offsets, text, and embedding
    """
    chunks_with_embeddings = []
    
    for page_num, chunk_text in page_chunk_map:
        # Generate embedding
        embedding = hash_embedding(chunk_text)
        
        # Find the chunk in original parse result to get offsets
        # For simplicity, we'll calculate offsets based on position in text
        start_offset = 0
        end_offset = len(chunk_text)
        
        chunks_with_embeddings.append({
            "page": page_num,
            "start_offset": start_offset,
            "end_offset": end_offset,
            "text": chunk_text,
            "embedding": embedding
        })
    
    return chunks_with_embeddings


def chunk_resume_by_pages(parse_result) -> List[dict]:
    """
    Chunk resume text while preserving page information
    
    Args:
        parse_result: ParseResult from parsing service
    
    Returns:
        List of dicts with page, start_offset, end_offset, text, embedding
    """
    all_chunks = []
    
    # Group chunks by page from parse result
    page_texts = {}
    for page, start, end, text in parse_result.chunks:
        if page not in page_texts:
            page_texts[page] = []
        page_texts[page].append((start, end, text))
    
    # Chunk each page's text
    for page_num in sorted(page_texts.keys()):
        page_chunks = page_texts[page_num]
        
        # Concatenate all text from this page
        page_text = " ".join([text for _, _, text in page_chunks])
        
        # Chunk the page text
        text_chunks = chunk_text(page_text, chunk_size=800, overlap=200)
        
        # Create chunk objects with embeddings
        current_offset = page_chunks[0][0] if page_chunks else 0
        
        for chunk_str in text_chunks:
            embedding = hash_embedding(chunk_str)

            all_chunks.append({
                "page": page_num,
                "start_offset": current_offset,
                "end_offset": current_offset + len(chunk_str),
                "text": chunk_str,
                "embedding": embedding
            })

            current_offset += len(chunk_str)
    
    return all_chunks
