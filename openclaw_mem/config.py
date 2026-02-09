"""RAG system configuration.

All paths are derived from environment variables or sensible defaults.
Set OPENCLAW_MEM_ROOT to override the workspace root directory.
"""
import os

# Base paths — configurable via environment
WORKSPACE_ROOT = os.environ.get(
    "OPENCLAW_MEM_ROOT",
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
LANCE_DB_PATH = os.environ.get(
    "OPENCLAW_MEM_DB_PATH",
    os.path.join(WORKSPACE_ROOT, "lance_db")
)

# Table name
TABLE_NAME = os.environ.get("OPENCLAW_MEM_TABLE", "openclaw_memory")

# Embedding model (multilingual, supports Korean + English)
EMBEDDING_MODEL = os.environ.get(
    "OPENCLAW_MEM_EMBEDDING_MODEL",
    "paraphrase-multilingual-MiniLM-L12-v2"
)

# Chunking settings
MAX_CHUNK_SIZE = int(os.environ.get("OPENCLAW_MEM_CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.environ.get("OPENCLAW_MEM_CHUNK_OVERLAP", "50"))

# Files to index (relative to WORKSPACE_ROOT)
INDEX_PATTERNS = [
    "memory/*.md",
]

# State file for change detection
INDEX_STATE_FILE = os.path.join(WORKSPACE_ROOT, ".openclaw_mem_index_state.json")

# Search defaults
DEFAULT_TOP_K = 5
DEFAULT_MIN_SCORE = 0.0

# --- 3-Layer Memory: Archive settings ---
ARCHIVE_DIR = os.environ.get(
    "OPENCLAW_MEM_ARCHIVE_DIR",
    os.path.join(WORKSPACE_ROOT, "memory", "archive")
)
ARCHIVE_AFTER_DAYS = int(os.environ.get("OPENCLAW_MEM_ARCHIVE_DAYS", "30"))

# Archive also indexes these patterns (cold layer stays in RAG)
ARCHIVE_INDEX_PATTERNS = [
    "memory/archive/*.md",
]

# --- Observations ---
OBSERVATIONS_FILE = os.environ.get(
    "OPENCLAW_MEM_OBSERVATIONS_FILE",
    os.path.join(WORKSPACE_ROOT, "memory", "observations.md")
)
OBSERVATION_TAGS = ["learning", "decision", "error", "insight"]
