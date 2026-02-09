"""openclaw-mem — Lightweight RAG memory system for AI agents."""

__version__ = "0.1.0"

from openclaw_mem.embedder import Embedder, get_embedder

__all__ = ["Embedder", "get_embedder", "__version__"]
