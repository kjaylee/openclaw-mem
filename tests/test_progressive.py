#!/usr/bin/env python3
"""Tests for Progressive Disclosure (2-step search) — unit level."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestSearchIndex:
    """Test search_index returns summaries without full content."""

    def test_search_index_returns_list(self):
        from openclaw_mem.search import search_index
        # This may return empty if no DB, but should not error
        results = search_index("test query", top_k=3)
        assert isinstance(results, list)

    def test_search_index_summary_fields(self):
        from openclaw_mem.search import search_index
        results = search_index("memory", top_k=1)
        for s in results:
            assert "id" in s
            assert "source" in s
            assert "score" in s
            assert "summary" in s
            assert "content" not in s

    def test_search_index_summary_length(self):
        from openclaw_mem.search import search_index
        results = search_index("system", top_k=3)
        for s in results:
            assert len(s["summary"]) <= 120


class TestGetDetail:
    """Test get_detail retrieves full content."""

    def test_detail_nonexistent_returns_none(self):
        from openclaw_mem.search import get_detail
        result = get_detail("nonexistent:0:abc12345")
        assert result is None


class TestFormatting:
    """Test output formatting functions."""

    def test_format_raw_empty(self):
        from openclaw_mem.search import format_raw
        assert format_raw([]) == "No results found."

    def test_format_raw_with_results(self):
        from openclaw_mem.search import format_raw
        results = [{
            "score": 0.95,
            "source": "test.md",
            "content": "Test content here",
        }]
        output = format_raw(results)
        assert "Result 1" in output
        assert "0.95" in output
        assert "Test content here" in output

    def test_format_index_raw_empty(self):
        from openclaw_mem.search import format_index_raw
        assert format_index_raw([]) == "No results found."

    def test_format_index_raw_with_results(self):
        from openclaw_mem.search import format_index_raw
        summaries = [{
            "score": 0.9,
            "source": "test.md",
            "id": "test:0:abc",
            "summary": "First line of chunk",
            "tag": "learning",
        }]
        output = format_index_raw(summaries)
        assert "test.md" in output
        assert "[learning]" in output
        assert "id: test:0:abc" in output
