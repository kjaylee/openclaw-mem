"""Embedding abstraction layer.

Supports multiple backends:
  - local: sentence-transformers (default, no API key needed)
  - openai: OpenAI Embeddings API (requires OPENAI_API_KEY)
  - ollama: Ollama local server (requires running Ollama instance)

Usage:
    from openclaw_mem.embedder import get_embedder

    embedder = get_embedder()
    vectors = embedder.embed(["hello world", "foo bar"])
"""
from __future__ import annotations

import os
from typing import List

from openclaw_mem.config import (
    EMBEDDING_BACKEND, EMBEDDING_MODEL,
    OPENAI_API_KEY, OPENAI_BASE_URL,
    OLLAMA_BASE_URL,
)


class Embedder:
    """Unified embedding interface across backends."""

    def __init__(self, backend: str = EMBEDDING_BACKEND,
                 model: str = EMBEDDING_MODEL):
        self.backend = backend
        self.model_name = model
        self._local_model = None  # lazy-loaded

    # ── public API ──────────────────────────────────────────

    def embed(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of texts, return list of float vectors."""
        if not texts:
            return []
        if self.backend == "local":
            return self._embed_local(texts)
        elif self.backend == "openai":
            return self._embed_openai(texts)
        elif self.backend == "ollama":
            return self._embed_ollama(texts)
        else:
            raise ValueError(
                f"Unknown embedding backend: {self.backend!r}. "
                f"Supported: local, openai, ollama"
            )

    def embed_single(self, text: str) -> List[float]:
        """Embed a single text string."""
        return self.embed([text])[0]

    # ── local (sentence-transformers) ───────────────────────

    def _embed_local(self, texts: List[str]) -> List[List[float]]:
        if self._local_model is None:
            from sentence_transformers import SentenceTransformer
            self._local_model = SentenceTransformer(self.model_name)
        embeddings = self._local_model.encode(texts, show_progress_bar=False)
        return [e.tolist() for e in embeddings]

    # ── openai ──────────────────────────────────────────────

    def _embed_openai(self, texts: List[str]) -> List[List[float]]:
        api_key = OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is required when OPENCLAW_MEM_BACKEND=openai. "
                "Set it via environment variable."
            )
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "openai package is required for the 'openai' backend. "
                "Install it with: pip install openclaw-mem[openai]"
            )

        client_kwargs = {"api_key": api_key}
        base_url = OPENAI_BASE_URL or os.environ.get("OPENAI_BASE_URL", "")
        if base_url:
            client_kwargs["base_url"] = base_url

        client = OpenAI(**client_kwargs)
        response = client.embeddings.create(
            model=self.model_name,
            input=texts,
        )
        # Sort by index to ensure order matches input
        sorted_data = sorted(response.data, key=lambda d: d.index)
        return [d.embedding for d in sorted_data]

    # ── ollama ──────────────────────────────────────────────

    def _embed_ollama(self, texts: List[str]) -> List[List[float]]:
        try:
            import ollama as ollama_lib
        except ImportError:
            raise ImportError(
                "ollama package is required for the 'ollama' backend. "
                "Install it with: pip install openclaw-mem[ollama]"
            )

        base_url = OLLAMA_BASE_URL or os.environ.get(
            "OLLAMA_BASE_URL", "http://localhost:11434"
        )
        client = ollama_lib.Client(host=base_url)

        vectors = []
        for text in texts:
            resp = client.embeddings(model=self.model_name, prompt=text)
            vectors.append(resp["embedding"])
        return vectors


# ── singleton ───────────────────────────────────────────────

_instance: Embedder | None = None


def get_embedder(backend: str | None = None,
                 model: str | None = None) -> Embedder:
    """Get or create the global Embedder instance.

    Call with no args to use config defaults (most common).
    Pass backend/model to override for testing or one-off usage.
    """
    global _instance
    if backend is not None or model is not None:
        # Explicit override → new instance (not cached)
        return Embedder(
            backend=backend or EMBEDDING_BACKEND,
            model=model or EMBEDDING_MODEL,
        )
    if _instance is None:
        _instance = Embedder()
    return _instance


def reset_embedder():
    """Reset the cached singleton (useful for testing)."""
    global _instance
    _instance = None
