import os
import hashlib
import zipfile
import tempfile
from typing import List, Tuple, Optional
from io import BytesIO
from pathlib import Path

from docx import Document
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LAParams


class ParseResult:
    def __init__(self, text: str, chunks: List[Tuple[int, int, int, str]], parsing_hash: str, metadata: dict):
        self.text = text
        self.chunks = chunks  # List of (page, start_offset, end_offset, text)
        self.parsing_hash = parsing_hash
        self.metadata = metadata


def normalize_text(text: str) -> str:
    """Normalize text by removing weird whitespace and unifying newlines"""
    # Replace multiple spaces with single space
    text = ' '.join(text.split())
    # Unify newlines
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    # Remove multiple consecutive newlines
    lines = [line for line in text.split('\n')]
    return '\n'.join(lines)


def compute_parsing_hash(text: str) -> str:
    """Compute SHA256 hash of normalized text"""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def extract_pdf_text(file_path: str) -> ParseResult:
    """Extract text from PDF with page numbers and character offsets"""
    chunks = []
    full_text = ""
    current_offset = 0
    
    laparams = LAParams()
    
    for page_num, page_layout in enumerate(extract_pages(file_path, laparams=laparams), start=1):
        page_text = ""
        
        for element in page_layout:
            if isinstance(element, LTTextContainer):
                page_text += element.get_text()
        
        if page_text.strip():
            normalized_page_text = normalize_text(page_text)
            start_offset = current_offset
            end_offset = current_offset + len(normalized_page_text)
            
            chunks.append((page_num, start_offset, end_offset, normalized_page_text))
            full_text += normalized_page_text + "\n"
            current_offset = end_offset + 1  # +1 for newline
    
    normalized_full_text = normalize_text(full_text)
    parsing_hash = compute_parsing_hash(normalized_full_text)
    
    # Extract basic metadata
    metadata = {
        "total_pages": len(chunks),
        "name": None,
        "email": None,
        "phone": None
    }
    
    # Simple metadata extraction (first page, first few lines)
    if chunks:
        first_page_text = chunks[0][3]
        lines = first_page_text.split('\n')[:5]
        
        # Try to extract name (usually first non-empty line)
        for line in lines:
            if line.strip() and len(line.strip()) > 2:
                metadata["name"] = line.strip()
                break
        
        # Try to extract email
        import re
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        for line in lines:
            email_match = re.search(email_pattern, line)
            if email_match:
                metadata["email"] = email_match.group(0)
                break
        
        # Try to extract phone
        phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        for line in lines:
            phone_match = re.search(phone_pattern, line)
            if phone_match:
                metadata["phone"] = phone_match.group(0)
                break
    
    return ParseResult(normalized_full_text, chunks, parsing_hash, metadata)


def extract_docx_text(file_path: str) -> ParseResult:
    """Extract text from DOCX with page=1 fallback"""
    doc = Document(file_path)
    chunks = []
    full_text = ""
    current_offset = 0
    
    # DOCX doesn't have clear page boundaries, so we treat each paragraph as a chunk
    # with page=1 as fallback
    for para in doc.paragraphs:
        text = para.text
        if text.strip():
            normalized_text = normalize_text(text)
            start_offset = current_offset
            end_offset = current_offset + len(normalized_text)
            
            chunks.append((1, start_offset, end_offset, normalized_text))
            full_text += normalized_text + "\n"
            current_offset = end_offset + 1
    
    normalized_full_text = normalize_text(full_text)
    parsing_hash = compute_parsing_hash(normalized_full_text)
    
    # Extract basic metadata
    metadata = {
        "total_pages": 1,
        "name": None,
        "email": None,
        "phone": None
    }
    
    # Simple metadata extraction from first paragraph
    if chunks:
        first_text = chunks[0][3]
        lines = first_text.split('\n')[:5]
        
        for line in lines:
            if line.strip() and len(line.strip()) > 2:
                metadata["name"] = line.strip()
                break
        
        import re
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        for chunk_text in [c[3] for c in chunks[:5]]:
            email_match = re.search(email_pattern, chunk_text)
            if email_match:
                metadata["email"] = email_match.group(0)
                break
        
        phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        for chunk_text in [c[3] for c in chunks[:5]]:
            phone_match = re.search(phone_pattern, chunk_text)
            if phone_match:
                metadata["phone"] = phone_match.group(0)
                break
    
    return ParseResult(normalized_full_text, chunks, parsing_hash, metadata)


def extract_txt_text(file_path: str) -> ParseResult:
    """Extract text from TXT file"""
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        text = f.read()
    
    normalized_text = normalize_text(text)
    parsing_hash = compute_parsing_hash(normalized_text)
    
    # Create a single chunk with page=1
    chunks = [(1, 0, len(normalized_text), normalized_text)]
    
    # Extract basic metadata
    metadata = {
        "total_pages": 1,
        "name": None,
        "email": None,
        "phone": None
    }
    
    lines = normalized_text.split('\n')[:5]
    for line in lines:
        if line.strip() and len(line.strip()) > 2:
            metadata["name"] = line.strip()
            break
    
    import re
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    email_match = re.search(email_pattern, normalized_text)
    if email_match:
        metadata["email"] = email_match.group(0)
    
    phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
    phone_match = re.search(phone_pattern, normalized_text)
    if phone_match:
        metadata["phone"] = phone_match.group(0)
    
    return ParseResult(normalized_text, chunks, parsing_hash, metadata)


def parse_resume(file_path: str, filename: str) -> ParseResult:
    """Parse resume based on file extension"""
    ext = Path(filename).suffix.lower()
    
    if ext == '.pdf':
        return extract_pdf_text(file_path)
    elif ext == '.docx':
        return extract_docx_text(file_path)
    elif ext == '.txt':
        return extract_txt_text(file_path)
    else:
        raise ValueError(f"Unsupported file format: {ext}")


def extract_zip(zip_path: str, extract_dir: str) -> List[str]:
    """Extract ZIP file and return list of extracted file paths"""
    extracted_files = []
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        for file_info in zip_ref.filelist:
            if not file_info.is_dir():
                # Check if file has supported extension
                ext = Path(file_info.filename).suffix.lower()
                if ext in ['.pdf', '.docx', '.txt']:
                    zip_ref.extract(file_info, extract_dir)
                    extracted_files.append(os.path.join(extract_dir, file_info.filename))
    
    return extracted_files


def compute_file_hash(file_path: str) -> str:
    """Compute SHA256 hash of file contents"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()
