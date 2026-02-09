#!/usr/bin/env python3
"""Tests for embedding abstraction layer."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestEmbedderFactory:
    """Test get_embedder factory."""

    def test_get_embedder_returns_instance(self):
        from openclaw_mem.embedder import get_embedder, reset_embedder, Embedder
        reset_embedder()
        e = get_embedder()
        assert isinstance(e, Embedder)

    def test_get_embedder_singleton(self):
        from openclaw_mem.embedder import get_embedder, reset_embedder
        reset_embedder()
        e1 = get_embedder()
        e2 = get_embedder()
        assert e1 is e2

    def test_get_embedder_override_not_cached(self):
        from openclaw_mem.embedder import get_embedder, reset_embedder
        reset_embedder()
        e_default = get_embedder()
        e_custom = get_embedder(backend="local", model="test-model")
        assert e_custom is not e_default
        assert e_custom.model_name == "test-model"

    def test_reset_embedder(self):
        from openclaw_mem.embedder import get_embedder, reset_embedder
        e1 = get_embedder()
        reset_embedder()
        e2 = get_embedder()
        assert e1 is not e2


class TestEmbedderLocal:
    """Test local backend (sentence-transformers)."""

    def test_default_backend_is_local(self):
        from openclaw_mem.embedder import Embedder
        e = Embedder()
        assert e.backend == "local"

    def test_embed_empty_list(self):
        from openclaw_mem.embedder import Embedder
        e = Embedder(backend="local", model="intfloat/multilingual-e5-small")
        result = e.embed([])
        assert result == []

    def test_embed_returns_vectors(self):
        from openclaw_mem.embedder import Embedder
        e = Embedder(backend="local", model="intfloat/multilingual-e5-small")
        vectors = e.embed(["hello world"])
        assert len(vectors) == 1
        assert isinstance(vectors[0], list)
        assert len(vectors[0]) > 0
        assert all(isinstance(v, float) for v in vectors[0])

    def test_embed_multiple_texts(self):
        from openclaw_mem.embedder import Embedder
        e = Embedder(backend="local", model="intfloat/multilingual-e5-small")
        vectors = e.embed(["hello", "world", "test"])
        assert len(vectors) == 3
        # All should have same dimension
        dims = {len(v) for v in vectors}
        assert len(dims) == 1

    def test_embed_single(self):
        from openclaw_mem.embedder import Embedder
        e = Embedder(backend="local", model="intfloat/multilingual-e5-small")
        vector = e.embed_single("hello world")
        assert isinstance(vector, list)
        assert len(vector) > 0

    def test_embed_consistent(self):
        from openclaw_mem.embedder import Embedder
        e = Embedder(backend="local", model="intfloat/multilingual-e5-small")
        v1 = e.embed_single("test text")
        v2 = e.embed_single("test text")
        assert v1 == v2

    def test_embed_different_texts_different_vectors(self):
        from openclaw_mem.embedder import Embedder
        e = Embedder(backend="local", model="intfloat/multilingual-e5-small")
        v1 = e.embed_single("cats are great")
        v2 = e.embed_single("quantum physics theory")
        assert v1 != v2


class TestEmbedderInvalidBackend:
    """Test error handling for invalid backend."""

    def test_unknown_backend_raises(self):
        from openclaw_mem.embedder import Embedder
        e = Embedder(backend="nonexistent", model="x")
        with pytest.raises(ValueError, match="Unknown embedding backend"):
            e.embed(["test"])


class TestEmbedderOpenAI:
    """Test OpenAI backend error handling (no actual API calls)."""

    def test_openai_without_key_raises(self):
        from openclaw_mem.embedder import Embedder
        old_key = os.environ.pop("OPENAI_API_KEY", None)
        try:
            e = Embedder(backend="openai", model="text-embedding-3-small")
            with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
                e.embed(["test"])
        finally:
            if old_key is not None:
                os.environ["OPENAI_API_KEY"] = old_key


class TestEmbedderOllama:
    """Test Ollama backend error handling (no actual server)."""

    def test_ollama_without_package_or_server(self):
        from openclaw_mem.embedder import Embedder
        e = Embedder(backend="ollama", model="nomic-embed-text")
        # Will either ImportError (no package) or ConnectionError (no server)
        with pytest.raises((ImportError, Exception)):
            e.embed(["test"])
