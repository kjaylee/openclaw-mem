#!/usr/bin/env python3
"""Tests for structured observation logging."""
import os
import sys
import tempfile
import time

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestObserve:
    """Test observation recording."""

    def setup_method(self):
        """Set up temp observations file."""
        self.tmpdir = tempfile.mkdtemp()
        self.obs_file = os.path.join(self.tmpdir, "observations.md")
        os.environ["OPENCLAW_MEM_OBSERVATIONS_FILE"] = self.obs_file

        # Reload config then observe to pick up env var
        import importlib
        import openclaw_mem.config
        importlib.reload(openclaw_mem.config)
        import openclaw_mem.observe
        importlib.reload(openclaw_mem.observe)

    def teardown_method(self):
        """Clean up."""
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)
        if "OPENCLAW_MEM_OBSERVATIONS_FILE" in os.environ:
            del os.environ["OPENCLAW_MEM_OBSERVATIONS_FILE"]

    def test_observe_records_to_file(self):
        from openclaw_mem.observe import append_observation

        unique = f"test_obs_{int(time.time())}"
        entry = append_observation(unique, "learning")
        assert "[learning]" in entry

        with open(self.obs_file, "r") as f:
            content = f.read()
        assert unique in content

    def test_observe_with_different_tags(self):
        from openclaw_mem.observe import append_observation

        for tag in ["learning", "decision", "error", "insight"]:
            unique = f"test_{tag}_{int(time.time())}"
            entry = append_observation(unique, tag)
            assert f"[{tag}]" in entry

    def test_observe_creates_file_if_missing(self):
        from openclaw_mem.observe import append_observation

        # File shouldn't exist yet
        assert not os.path.exists(self.obs_file)
        append_observation("first observation", "insight")
        assert os.path.exists(self.obs_file)

        with open(self.obs_file, "r") as f:
            content = f.read()
        assert "# Observations" in content
        assert "first observation" in content
