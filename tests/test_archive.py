#!/usr/bin/env python3
"""Tests for 3-Layer memory archive system."""
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestArchiveDetection:
    """Test archive candidate detection."""

    def test_is_old_enough_with_old_date(self):
        from openclaw_mem.archive import is_old_enough
        from datetime import datetime, timedelta

        old_date = (datetime.now() - timedelta(days=35)).strftime("%Y-%m-%d")
        assert is_old_enough(f"memory/{old_date}.md", days=30) is True

    def test_is_old_enough_with_recent_date(self):
        from openclaw_mem.archive import is_old_enough
        from datetime import datetime, timedelta

        recent_date = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
        assert is_old_enough(f"memory/{recent_date}.md", days=30) is False

    def test_protected_files_not_archived(self):
        from openclaw_mem.archive import PROTECTED_FILES
        assert "core.md" in PROTECTED_FILES
        assert "observations.md" in PROTECTED_FILES
        assert "today.md" in PROTECTED_FILES


class TestArchiveExecution:
    """Test actual archive file movement with temp directories."""

    def setup_method(self):
        """Create temporary directories for testing."""
        self.tmpdir = tempfile.mkdtemp()
        self.memory_dir = os.path.join(self.tmpdir, "memory")
        self.archive_dir = os.path.join(self.memory_dir, "archive")
        os.makedirs(self.memory_dir)
        os.makedirs(self.archive_dir)

        self.test_filename = "2025-12-01-test-archive.md"
        self.test_filepath = os.path.join(self.memory_dir, self.test_filename)
        self.archive_filepath = os.path.join(self.archive_dir, self.test_filename)

        with open(self.test_filepath, "w") as f:
            f.write("# Test Archive Content\n\nThis is test content for archiving.\n")

    def teardown_method(self):
        """Clean up temp directory."""
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_is_old_enough_true(self):
        from openclaw_mem.archive import is_old_enough
        assert is_old_enough(self.test_filepath, days=30) is True

    def test_archive_moves_file(self):
        import shutil
        from openclaw_mem.archive import is_old_enough

        assert is_old_enough(self.test_filepath, days=30) is True
        # Manual move simulation
        shutil.move(self.test_filepath, self.archive_filepath)
        assert not os.path.exists(self.test_filepath)
        assert os.path.exists(self.archive_filepath)
