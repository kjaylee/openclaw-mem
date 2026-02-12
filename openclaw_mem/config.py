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

# --- Embedding configuration ---
# Backend: "local" (sentence-transformers), "openai", "ollama"
EMBEDDING_BACKEND = os.environ.get("OPENCLAW_MEM_BACKEND", "local")

# Model name per backend:
#   local  → sentence-transformers model (default: all-MiniLM-L6-v2)
#   openai → OpenAI model (default: text-embedding-3-small)
#   ollama → Ollama model (default: nomic-embed-text)
_DEFAULT_MODELS = {
    "local": "intfloat/multilingual-e5-small",
    "openai": "text-embedding-3-small",
    "ollama": "nomic-embed-text",
}
EMBEDDING_MODEL = os.environ.get(
    "OPENCLAW_MEM_MODEL",
    _DEFAULT_MODELS.get(EMBEDDING_BACKEND, "intfloat/multilingual-e5-small")
)

# OpenAI settings (only used when EMBEDDING_BACKEND=openai)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "")

# Ollama settings (only used when EMBEDDING_BACKEND=ollama)
OLLAMA_BASE_URL = os.environ.get(
    "OLLAMA_BASE_URL", "http://localhost:11434"
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
OBSERVATION_TAGS = [
    "learning", "decision", "error", "insight",
    "preference", "mistake", "architecture", "next",
]

# --- Brain Routing ---
# Project keyword → Brain file mapping
BRAIN_PROJECT_KEYWORDS: dict[str, str] = {
    "sanguo": "memory/projects/sanguo.md",
    "삼국": "memory/projects/sanguo.md",
    "portrait": "memory/projects/sanguo.md",
    "blog": "memory/projects/eastsea-blog.md",
    "eastsea": "memory/projects/eastsea-blog.md",
    "포스트": "memory/projects/eastsea-blog.md",
    "jekyll": "memory/projects/eastsea-blog.md",
    "game": "memory/projects/game-dev.md",
    "godot": "memory/projects/game-dev.md",
    "게임": "memory/projects/game-dev.md",
}

# Tag → Brain section mapping
BRAIN_TAG_SECTION: dict[str, str] = {
    "decision": "## Architecture Decisions",
    "architecture": "## Architecture Decisions",
    "learning": "## Lessons Learned",
    "error": "## Common Mistakes",
    "mistake": "## Common Mistakes",
    "insight": "## Next Phase",
    "next": "## Next Phase",
    "preference": "## Preferences",
}

# Brain projects directory (relative to WORKSPACE_ROOT)
BRAIN_PROJECTS_DIR = os.path.join(WORKSPACE_ROOT, "memory", "projects")
