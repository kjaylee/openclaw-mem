"""Tests for openclaw_mem.init_cmd — workspace initialization."""
import os
import tempfile
import shutil
import pytest

from openclaw_mem.init_cmd import init_workspace, CORE_MD_TEMPLATE


@pytest.fixture
def empty_dir():
    """Create a temporary empty directory, clean up after test."""
    d = tempfile.mkdtemp(prefix="ocm_init_test_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


class TestInitWorkspace:
    """Tests for the init_workspace function."""

    def test_creates_memory_directory(self, empty_dir):
        """memory/ directory should be created."""
        init_workspace(root=empty_dir, run_index=False)
        assert os.path.isdir(os.path.join(empty_dir, "memory"))

    def test_creates_core_md(self, empty_dir):
        """memory/core.md should be created with the template content."""
        init_workspace(root=empty_dir, run_index=False)
        core_path = os.path.join(empty_dir, "memory", "core.md")
        assert os.path.isfile(core_path)
        with open(core_path) as f:
            content = f.read()
        assert content == CORE_MD_TEMPLATE

    def test_creates_projects_directory(self, empty_dir):
        """memory/projects/ Brain directory should be created."""
        init_workspace(root=empty_dir, run_index=False)
        assert os.path.isdir(os.path.join(empty_dir, "memory", "projects"))

    def test_creates_observations_md(self, empty_dir):
        """memory/observations.md should be created as an empty file."""
        init_workspace(root=empty_dir, run_index=False)
        obs_path = os.path.join(empty_dir, "memory", "observations.md")
        assert os.path.isfile(obs_path)
        with open(obs_path) as f:
            assert f.read() == ""

    def test_creates_env_file(self, empty_dir):
        """A .env file should be created with OPENCLAW_MEM_ROOT."""
        init_workspace(root=empty_dir, run_index=False)
        env_path = os.path.join(empty_dir, ".env")
        assert os.path.isfile(env_path)
        with open(env_path) as f:
            content = f.read()
        assert "OPENCLAW_MEM_ROOT" in content
        assert empty_dir in content

    def test_skips_existing_files(self, empty_dir):
        """Existing files should NOT be overwritten."""
        # Pre-create core.md with custom content
        mem_dir = os.path.join(empty_dir, "memory")
        os.makedirs(mem_dir)
        core_path = os.path.join(mem_dir, "core.md")
        custom_content = "# My custom core\n"
        with open(core_path, "w") as f:
            f.write(custom_content)

        init_workspace(root=empty_dir, run_index=False)

        with open(core_path) as f:
            assert f.read() == custom_content  # unchanged

    def test_skips_existing_env(self, empty_dir):
        """Existing .env should NOT be overwritten."""
        env_path = os.path.join(empty_dir, ".env")
        original = "EXISTING_VAR=1\n"
        with open(env_path, "w") as f:
            f.write(original)

        init_workspace(root=empty_dir, run_index=False)

        with open(env_path) as f:
            assert f.read() == original

    def test_returns_status_dict(self, empty_dir):
        """init_workspace should return a dict with status for each item."""
        results = init_workspace(root=empty_dir, run_index=False)
        assert isinstance(results, dict)
        assert results["memory/"] == "created"
        assert results["memory/core.md"] == "created"
        assert results["memory/projects/"] == "created"
        assert results["memory/observations.md"] == "created"
        assert results[".env"] == "created"

    def test_second_run_reports_exists(self, empty_dir):
        """Running init twice should report 'exists' for everything."""
        init_workspace(root=empty_dir, run_index=False)
        results = init_workspace(root=empty_dir, run_index=False)
        for key in ("memory/", "memory/core.md", "memory/projects/",
                     "memory/observations.md", ".env"):
            assert results[key] == "exists"

    def test_idempotent(self, empty_dir):
        """Multiple runs should produce the same final structure."""
        init_workspace(root=empty_dir, run_index=False)
        init_workspace(root=empty_dir, run_index=False)
        init_workspace(root=empty_dir, run_index=False)

        assert os.path.isdir(os.path.join(empty_dir, "memory"))
        assert os.path.isdir(os.path.join(empty_dir, "memory", "projects"))
        assert os.path.isfile(os.path.join(empty_dir, "memory", "core.md"))
        assert os.path.isfile(os.path.join(empty_dir, "memory", "observations.md"))
        assert os.path.isfile(os.path.join(empty_dir, ".env"))
