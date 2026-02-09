#!/usr/bin/env python3
"""Index markdown files into LanceDB for RAG search.

Supports:
  - Full reindex (--all)
  - Incremental (--changed, default)
  - Single file indexing
  - Observation records with tags
  - Archive directory indexing (cold layer)
"""
import argparse
import glob
import json
import logging
import os
import sys
import time
import warnings
warnings.filterwarnings("ignore")

from openclaw_mem.config import (
    WORKSPACE_ROOT, LANCE_DB_PATH, TABLE_NAME,
    INDEX_PATTERNS, INDEX_STATE_FILE,
    ARCHIVE_INDEX_PATTERNS
)
from openclaw_mem.chunker import chunk_markdown
from openclaw_mem.embedder import get_embedder
from openclaw_mem.sanitizer import get_sanitizer

logger = logging.getLogger(__name__)


def get_db():
    """Get LanceDB connection."""
    import lancedb
    return lancedb.connect(LANCE_DB_PATH)


def get_files_to_index(patterns=None):
    """Get list of files matching index patterns."""
    if patterns is None:
        patterns = INDEX_PATTERNS + ARCHIVE_INDEX_PATTERNS
    files = []
    for pattern in patterns:
        full_pattern = os.path.join(WORKSPACE_ROOT, pattern)
        matched = glob.glob(full_pattern)
        files.extend(matched)
    return sorted(set(files))


def load_state():
    """Load index state (last indexed times)."""
    if os.path.exists(INDEX_STATE_FILE):
        with open(INDEX_STATE_FILE) as f:
            return json.load(f)
    return {}


def save_state(state):
    """Save index state."""
    with open(INDEX_STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def build_records(filepath, tag=""):
    """Build records from a file for LanceDB insertion.

    Args:
        filepath: Path to the markdown file.
        tag: Optional tag string (used for observations).
    """
    rel_path = os.path.relpath(filepath, WORKSPACE_ROOT)

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    if not content.strip():
        return []

    chunks = chunk_markdown(content, rel_path)
    if not chunks:
        return []

    # Warn on injection patterns in existing file chunks (non-blocking)
    sanitizer = get_sanitizer()
    for chunk in chunks:
        is_safe, matched = sanitizer.check(chunk["content"])
        if not is_safe:
            logger.warning(
                "Injection pattern in %s chunk %s: %s",
                rel_path, chunk["metadata"]["chunk_index"], matched,
            )

    embedder = get_embedder()
    texts = [c["content"] for c in chunks]
    embeddings = embedder.embed(texts)

    records = []
    for i, chunk in enumerate(chunks):
        records.append({
            "id": chunk["id"],
            "text": chunk["content"],
            "source": chunk["metadata"]["source"],
            "filename": chunk["metadata"]["filename"],
            "chunk_index": chunk["metadata"]["chunk_index"],
            "date": chunk["metadata"].get("date", ""),
            "tag": tag,
            "vector": embeddings[i],
        })

    return records


def build_observation_records(text, tag=""):
    """Build a single record from an observation text."""
    import hashlib
    from datetime import datetime

    content_hash = hashlib.md5(text.encode()).hexdigest()[:8]
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    chunk_id = f"obs:{timestamp}:{content_hash}"

    embedder = get_embedder()
    embedding = embedder.embed_single(text)

    return [{
        "id": chunk_id,
        "text": text,
        "source": "memory/observations.md",
        "filename": "observations.md",
        "chunk_index": 0,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "tag": tag,
        "vector": embedding,
    }]


def _ensure_table_schema(db, records):
    """Ensure table exists; create if needed, add records to existing."""
    existing_tables = db.table_names()

    if TABLE_NAME in existing_tables:
        table = db.open_table(TABLE_NAME)
        if records:
            table.add(records)
        return table
    else:
        if records:
            return db.create_table(TABLE_NAME, records)
        return None


def index_all(verbose=True):
    """Index all configured files."""
    files = get_files_to_index()
    if verbose:
        print(f"Found {len(files)} files to index")

    all_records = []
    state = load_state()

    for filepath in files:
        rel_path = os.path.relpath(filepath, WORKSPACE_ROOT)
        records = build_records(filepath)
        all_records.extend(records)
        state[rel_path] = time.time()
        if verbose:
            print(f"  {rel_path}: {len(records)} chunks")

    if not all_records:
        if verbose:
            print("No records to index.")
        return 0

    # Create/overwrite the table
    db = get_db()
    try:
        db.drop_table(TABLE_NAME)
    except Exception:
        pass

    db.create_table(TABLE_NAME, all_records)

    save_state(state)

    if verbose:
        print(f"\nDone. Total chunks in DB: {len(all_records)}")

    return len(all_records)


def index_changed(verbose=True):
    """Index only files that changed since last indexing."""
    files = get_files_to_index()
    state = load_state()

    changed = []
    for filepath in files:
        rel_path = os.path.relpath(filepath, WORKSPACE_ROOT)
        mtime = os.path.getmtime(filepath)
        last_indexed = state.get(rel_path, 0)
        if mtime > last_indexed:
            changed.append(filepath)

    if not changed:
        if verbose:
            print("No files changed since last indexing.")
        return 0

    if verbose:
        print(f"Found {len(changed)} changed files")

    # Build records for changed files
    new_records = []
    changed_filenames = set()
    for filepath in changed:
        rel_path = os.path.relpath(filepath, WORKSPACE_ROOT)
        records = build_records(filepath)
        new_records.extend(records)
        changed_filenames.add(os.path.basename(filepath))
        state[rel_path] = time.time()
        if verbose:
            print(f"  {rel_path}: {len(records)} chunks")

    db = get_db()

    # Check if table exists
    existing_tables = db.table_names()

    if TABLE_NAME in existing_tables:
        table = db.open_table(TABLE_NAME)
        # Delete old records for changed files, add new ones
        for fn in changed_filenames:
            try:
                table.delete(f'filename = "{fn}"')
            except Exception:
                pass
        if new_records:
            table.add(new_records)
        total = table.count_rows()
    else:
        if new_records:
            table = db.create_table(TABLE_NAME, new_records)
            total = len(new_records)
        else:
            total = 0

    save_state(state)

    if verbose:
        print(f"\nDone. Total chunks in DB: {total}")

    return len(new_records)


def index_single(filepath, verbose=True, tag=""):
    """Index a single specified file."""
    if not os.path.isabs(filepath):
        filepath = os.path.join(WORKSPACE_ROOT, filepath)

    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    records = build_records(filepath, tag=tag)
    if not records:
        if verbose:
            print("No content to index.")
        return 0

    rel_path = os.path.relpath(filepath, WORKSPACE_ROOT)
    filename = os.path.basename(filepath)

    db = get_db()
    existing_tables = db.table_names()

    if TABLE_NAME in existing_tables:
        table = db.open_table(TABLE_NAME)
        try:
            table.delete(f'filename = "{filename}"')
        except Exception:
            pass
        table.add(records)
        total = table.count_rows()
    else:
        table = db.create_table(TABLE_NAME, records)
        total = len(records)

    state = load_state()
    state[rel_path] = time.time()
    save_state(state)

    if verbose:
        print(f"Indexed {rel_path}: {len(records)} chunks")
        print(f"Total chunks in DB: {total}")

    return len(records)


def index_observation(text, tag="", verbose=True):
    """Index a single observation record into LanceDB.

    Returns the created chunk id.
    """
    records = build_observation_records(text, tag)
    if not records:
        return None

    db = get_db()
    _ensure_table_schema(db, records)

    if verbose:
        print(f"Indexed observation: {records[0]['id']}")

    return records[0]["id"]


def main():
    parser = argparse.ArgumentParser(description="Index files into RAG vector DB")
    parser.add_argument("file", nargs="?", help="Single file to index")
    parser.add_argument("--all", action="store_true", help="Index all configured files")
    parser.add_argument("--changed", action="store_true", help="Index only changed files")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress output")

    args = parser.parse_args()
    verbose = not args.quiet

    if args.file:
        index_single(args.file, verbose)
    elif args.changed:
        index_changed(verbose)
    elif args.all:
        index_all(verbose)
    else:
        index_changed(verbose)


if __name__ == "__main__":
    main()
