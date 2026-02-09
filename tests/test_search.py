#!/usr/bin/env python3
"""Tests for search functionality — unit level."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestSearchBasic:
    """Test basic search interface."""

    def test_search_returns_list(self):
        from openclaw_mem.search import search
        results = search("test query", top_k=2)
        assert isinstance(results, list)

    def test_search_respects_top_k(self):
        from openclaw_mem.search import search
        results = search("system", top_k=1)
        assert len(results) <= 1


class TestSearchFiltering:
    """Test search filtering options."""

    def test_search_with_min_score(self):
        from openclaw_mem.search import search
        results = search("test", min_score=0.99, top_k=5)
        for r in results:
            assert r["score"] >= 0.99

    def test_search_result_fields(self):
        from openclaw_mem.search import search
        results = search("memory", top_k=1)
        for r in results:
            assert "id" in r
            assert "source" in r
            assert "content" in r
            assert "score" in r
            assert "metadata" in r


class TestChunker:
    """Test markdown chunking."""

    def test_chunk_small_content(self):
        from openclaw_mem.chunker import chunk_markdown
        content = "# Hello\n\nSmall content here."
        chunks = chunk_markdown(content, "test.md")
        assert len(chunks) >= 1
        assert chunks[0]["content"] == content

    def test_chunk_preserves_metadata(self):
        from openclaw_mem.chunker import chunk_markdown
        content = "# Test\n\nSome content."
        chunks = chunk_markdown(content, "2025-01-15.md")
        assert chunks[0]["metadata"]["filename"] == "2025-01-15.md"
        assert chunks[0]["metadata"]["date"] == "2025-01-15"

    def test_chunk_splits_large_content(self):
        from openclaw_mem.chunker import chunk_markdown
        content = "## Section\n\n" + ("A" * 600)
        chunks = chunk_markdown(content, "test.md", max_size=200)
        assert len(chunks) > 1

    def test_chunk_id_format(self):
        from openclaw_mem.chunker import chunk_markdown
        content = "# Test\n\nContent."
        chunks = chunk_markdown(content, "path/to/file.md")
        assert chunks[0]["id"].startswith("file.md:")
