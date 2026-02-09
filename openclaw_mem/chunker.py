"""Markdown chunking for RAG indexing."""
import hashlib
import re
from typing import List, Dict


def chunk_markdown(content: str, source: str, max_size: int = 500, overlap: int = 50) -> List[Dict]:
    """Split markdown content into chunks with metadata.

    Strategy:
    1. Split by ## or ### headers first
    2. If section > max_size, split by paragraphs
    3. If paragraph > max_size, split by character limit with overlap
    """
    chunks = []

    # Split by headers (## or ###)
    sections = re.split(r'(?=^#{2,3}\s)', content, flags=re.MULTILINE)

    chunk_index = 0
    for section in sections:
        section = section.strip()
        if not section:
            continue

        if len(section) <= max_size:
            chunks.append(_make_chunk(section, source, chunk_index))
            chunk_index += 1
        else:
            # Split by paragraphs
            paragraphs = re.split(r'\n\n+', section)
            buffer = ""

            for para in paragraphs:
                para = para.strip()
                if not para:
                    continue

                if len(buffer) + len(para) + 2 <= max_size:
                    buffer = f"{buffer}\n\n{para}" if buffer else para
                else:
                    if buffer:
                        chunks.append(_make_chunk(buffer, source, chunk_index))
                        chunk_index += 1
                        # Keep overlap from end of buffer
                        if overlap > 0 and len(buffer) > overlap:
                            buffer = buffer[-overlap:] + "\n\n" + para
                        else:
                            buffer = para
                    else:
                        # Single paragraph too large, force split
                        sub_chunks = _force_split(para, max_size, overlap)
                        for sc in sub_chunks:
                            chunks.append(_make_chunk(sc, source, chunk_index))
                            chunk_index += 1
                        buffer = ""

            if buffer:
                chunks.append(_make_chunk(buffer, source, chunk_index))
                chunk_index += 1

    return chunks


def _force_split(text: str, max_size: int, overlap: int) -> List[str]:
    """Force split text by character limit."""
    parts = []
    start = 0
    while start < len(text):
        end = start + max_size
        parts.append(text[start:end])
        start = end - overlap if overlap > 0 else end
    return parts


def _make_chunk(content: str, source: str, chunk_index: int) -> Dict:
    """Create a chunk dict with metadata."""
    content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
    filename = source.split("/")[-1] if "/" in source else source

    # Extract date from memory filenames (YYYY-MM-DD.md)
    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
    date = date_match.group(1) if date_match else None

    return {
        "id": f"{filename}:{chunk_index}:{content_hash}",
        "content": content,
        "metadata": {
            "source": source,
            "filename": filename,
            "chunk_index": chunk_index,
            "date": date or "",
        }
    }
