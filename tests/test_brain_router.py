#!/usr/bin/env python3
"""Tests for brain_router — project Brain file routing.

Brain 라우터 테스트: 프로젝트 키워드 매칭, 섹션 생성,
중복 방지, 관찰 라우팅 통합 테스트.
"""
import os
import sys
import tempfile
import shutil

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestDetectProject:
    """Test project keyword detection in observation text."""

    def test_sanguo_korean(self):
        from openclaw_mem.brain_router import detect_project
        result = detect_project("삼국지 캐릭터 포트레이트 완성")
        assert result is not None
        assert "sanguo" in result

    def test_sanguo_english(self):
        from openclaw_mem.brain_router import detect_project
        result = detect_project("Sanguo game WebP conversion done")
        assert result is not None
        assert "sanguo" in result

    def test_sanguo_portrait(self):
        from openclaw_mem.brain_router import detect_project
        result = detect_project("Portrait asset pipeline optimized")
        assert result is not None
        assert "sanguo" in result

    def test_blog_keyword(self):
        from openclaw_mem.brain_router import detect_project
        result = detect_project("Blog deployment to GitHub Pages")
        assert result is not None
        assert "eastsea-blog" in result

    def test_blog_eastsea(self):
        from openclaw_mem.brain_router import detect_project
        result = detect_project("eastsea 포스트 업데이트 완료")
        assert result is not None
        assert "eastsea-blog" in result

    def test_blog_jekyll(self):
        from openclaw_mem.brain_router import detect_project
        result = detect_project("Jekyll build failed on missing layout")
        assert result is not None
        assert "eastsea-blog" in result

    def test_game_keyword(self):
        from openclaw_mem.brain_router import detect_project
        result = detect_project("Game export to WebGL2 completed")
        assert result is not None
        assert "game-dev" in result

    def test_game_godot(self):
        from openclaw_mem.brain_router import detect_project
        result = detect_project("Godot 4.6 headless export works")
        assert result is not None
        assert "game-dev" in result

    def test_game_korean(self):
        from openclaw_mem.brain_router import detect_project
        result = detect_project("게임 빌드 파이프라인 구축")
        assert result is not None
        assert "game-dev" in result

    def test_no_match(self):
        from openclaw_mem.brain_router import detect_project
        result = detect_project("Generic observation about Python")
        assert result is None

    def test_case_insensitive(self):
        from openclaw_mem.brain_router import detect_project
        result = detect_project("SANGUO portrait renders are done")
        assert result is not None
        assert "sanguo" in result


class TestGetBrainSection:
    """Test tag to Brain section mapping."""

    def test_decision_section(self):
        from openclaw_mem.brain_router import get_brain_section
        assert get_brain_section("decision") == "## Architecture Decisions"

    def test_architecture_section(self):
        from openclaw_mem.brain_router import get_brain_section
        assert get_brain_section("architecture") == "## Architecture Decisions"

    def test_learning_section(self):
        from openclaw_mem.brain_router import get_brain_section
        assert get_brain_section("learning") == "## Lessons Learned"

    def test_error_section(self):
        from openclaw_mem.brain_router import get_brain_section
        assert get_brain_section("error") == "## Common Mistakes"

    def test_mistake_section(self):
        from openclaw_mem.brain_router import get_brain_section
        assert get_brain_section("mistake") == "## Common Mistakes"

    def test_insight_section(self):
        from openclaw_mem.brain_router import get_brain_section
        assert get_brain_section("insight") == "## Next Phase"

    def test_next_section(self):
        from openclaw_mem.brain_router import get_brain_section
        assert get_brain_section("next") == "## Next Phase"

    def test_preference_section(self):
        from openclaw_mem.brain_router import get_brain_section
        assert get_brain_section("preference") == "## Preferences"

    def test_unknown_tag_fallback(self):
        from openclaw_mem.brain_router import get_brain_section
        assert get_brain_section("unknown_tag") == "## Observations"


class TestBrainFileOperations:
    """Test Brain file creation, section management, and dedup."""

    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.original_root = os.environ.get("OPENCLAW_MEM_ROOT")
        os.environ["OPENCLAW_MEM_ROOT"] = self.tmpdir

        # Reload config to pick up new root
        import importlib
        import openclaw_mem.config
        importlib.reload(openclaw_mem.config)
        import openclaw_mem.brain_router
        importlib.reload(openclaw_mem.brain_router)

    def teardown_method(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)
        if self.original_root is not None:
            os.environ["OPENCLAW_MEM_ROOT"] = self.original_root
        elif "OPENCLAW_MEM_ROOT" in os.environ:
            del os.environ["OPENCLAW_MEM_ROOT"]

    def test_ensure_brain_file_creates(self):
        from openclaw_mem.brain_router import _ensure_brain_file
        filepath = os.path.join(self.tmpdir, "memory", "projects", "test.md")
        _ensure_brain_file(filepath)
        assert os.path.exists(filepath)
        with open(filepath, "r") as f:
            content = f.read()
        assert "# Test Brain" in content

    def test_ensure_brain_file_idempotent(self):
        from openclaw_mem.brain_router import _ensure_brain_file
        filepath = os.path.join(self.tmpdir, "memory", "projects", "test.md")
        _ensure_brain_file(filepath)
        # Write extra content
        with open(filepath, "a") as f:
            f.write("## Custom Section\n")
        _ensure_brain_file(filepath)
        with open(filepath, "r") as f:
            content = f.read()
        assert "## Custom Section" in content  # Not overwritten

    def test_find_or_create_section_existing(self):
        from openclaw_mem.brain_router import _find_or_create_section
        content = "# Brain\n\n## Lessons Learned\n\n- existing entry\n"
        updated, pos = _find_or_create_section(content, "## Lessons Learned")
        assert "## Lessons Learned" in updated
        # Position should be after the section heading
        assert pos > content.index("## Lessons Learned")

    def test_find_or_create_section_new(self):
        from openclaw_mem.brain_router import _find_or_create_section
        content = "# Brain\n\n"
        updated, pos = _find_or_create_section(content, "## Preferences")
        assert "## Preferences" in updated
        assert pos == len(updated)

    def test_content_already_exists_true(self):
        from openclaw_mem.brain_router import _content_already_exists
        content = (
            "# Brain\n\n"
            "## Lessons Learned\n\n"
            "- [2026-02-12 10:00] **[learning]** Redis cache works well\n"
        )
        assert _content_already_exists(
            content, "## Lessons Learned", "Redis cache works well"
        ) is True

    def test_content_already_exists_false(self):
        from openclaw_mem.brain_router import _content_already_exists
        content = (
            "# Brain\n\n"
            "## Lessons Learned\n\n"
            "- [2026-02-12 10:00] **[learning]** Redis cache works well\n"
        )
        assert _content_already_exists(
            content, "## Lessons Learned", "PostgreSQL migration needed"
        ) is False

    def test_content_already_exists_different_section(self):
        from openclaw_mem.brain_router import _content_already_exists
        content = (
            "# Brain\n\n"
            "## Lessons Learned\n\n"
            "- Redis cache works well\n\n"
            "## Architecture Decisions\n\n"
            "- Use Rust for backend\n"
        )
        # Exists in Lessons Learned, not in Architecture
        assert _content_already_exists(
            content, "## Architecture Decisions", "Redis cache works well"
        ) is False

    def test_route_observation_creates_entry(self):
        from openclaw_mem.brain_router import route_observation_to_brain
        result = route_observation_to_brain(
            "Sanguo: WebP 대신 PNG 유지 결정",
            "decision",
            timestamp="2026-02-12 10:00",
        )
        assert result is not None
        assert "sanguo" in result

        # Verify file content
        filepath = os.path.join(self.tmpdir, result)
        with open(filepath, "r") as f:
            content = f.read()
        assert "## Architecture Decisions" in content
        assert "PNG 유지 결정" in content

    def test_route_observation_no_match(self):
        from openclaw_mem.brain_router import route_observation_to_brain
        result = route_observation_to_brain(
            "Generic Python observation",
            "learning",
            timestamp="2026-02-12 10:00",
        )
        assert result is None

    def test_route_observation_dry_run(self):
        from openclaw_mem.brain_router import route_observation_to_brain
        result = route_observation_to_brain(
            "Sanguo portrait rendering optimized",
            "learning",
            timestamp="2026-02-12 10:00",
            dry_run=True,
        )
        assert result is not None
        # File should NOT be created
        filepath = os.path.join(self.tmpdir, result)
        assert not os.path.exists(filepath)

    def test_route_observation_dedup(self):
        from openclaw_mem.brain_router import route_observation_to_brain
        # Route same observation twice
        route_observation_to_brain(
            "Sanguo: PNG format selected for portraits",
            "decision",
            timestamp="2026-02-12 10:00",
        )
        route_observation_to_brain(
            "Sanguo: PNG format selected for portraits",
            "decision",
            timestamp="2026-02-12 11:00",
        )
        # Should only have one entry
        filepath = os.path.join(self.tmpdir, "memory/projects/sanguo.md")
        with open(filepath, "r") as f:
            content = f.read()
        assert content.count("PNG format selected") == 1

    def test_route_observation_multiple_sections(self):
        from openclaw_mem.brain_router import route_observation_to_brain
        route_observation_to_brain(
            "Sanguo: Rust WASM으로 결정",
            "decision",
            timestamp="2026-02-12 10:00",
        )
        route_observation_to_brain(
            "Sanguo: sprite sheet 최적화 배움",
            "learning",
            timestamp="2026-02-12 11:00",
        )
        filepath = os.path.join(self.tmpdir, "memory/projects/sanguo.md")
        with open(filepath, "r") as f:
            content = f.read()
        assert "## Architecture Decisions" in content
        assert "## Lessons Learned" in content
        assert "Rust WASM" in content
        assert "sprite sheet" in content


class TestRouteObservations:
    """Test batch routing of observations."""

    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.original_root = os.environ.get("OPENCLAW_MEM_ROOT")
        os.environ["OPENCLAW_MEM_ROOT"] = self.tmpdir

        import importlib
        import openclaw_mem.config
        importlib.reload(openclaw_mem.config)
        import openclaw_mem.brain_router
        importlib.reload(openclaw_mem.brain_router)

    def teardown_method(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)
        if self.original_root is not None:
            os.environ["OPENCLAW_MEM_ROOT"] = self.original_root
        elif "OPENCLAW_MEM_ROOT" in os.environ:
            del os.environ["OPENCLAW_MEM_ROOT"]

    def test_route_mixed_observations(self):
        from openclaw_mem.brain_router import route_observations
        obs = [
            {"tag": "decision", "text": "Sanguo: use PNG format", "timestamp": ""},
            {"tag": "learning", "text": "Blog Jekyll build requires bundler", "timestamp": ""},
            {"tag": "error", "text": "Generic Python import error found", "timestamp": ""},
        ]
        brain_routed, fallback = route_observations(obs, verbose=False)
        assert len(brain_routed) == 2  # sanguo + blog
        assert len(fallback) == 1      # generic

    def test_route_all_to_brain(self):
        from openclaw_mem.brain_router import route_observations
        obs = [
            {"tag": "decision", "text": "Sanguo portrait rendering", "timestamp": ""},
            {"tag": "learning", "text": "Godot 4.6 export 게임 빌드", "timestamp": ""},
        ]
        brain_routed, fallback = route_observations(obs, verbose=False)
        assert len(brain_routed) == 2
        assert len(fallback) == 0

    def test_route_none_to_brain(self):
        from openclaw_mem.brain_router import route_observations
        obs = [
            {"tag": "insight", "text": "Python venv management tip", "timestamp": ""},
        ]
        brain_routed, fallback = route_observations(obs, verbose=False)
        assert len(brain_routed) == 0
        assert len(fallback) == 1

    def test_route_dry_run_no_files(self):
        from openclaw_mem.brain_router import route_observations
        obs = [
            {"tag": "decision", "text": "Sanguo: use Rust WASM", "timestamp": ""},
        ]
        brain_routed, fallback = route_observations(
            obs, dry_run=True, verbose=False
        )
        assert len(brain_routed) == 1
        # No Brain file should exist
        projects_dir = os.path.join(self.tmpdir, "memory", "projects")
        assert not os.path.exists(projects_dir)
