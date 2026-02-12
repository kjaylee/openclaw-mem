#!/usr/bin/env python3
"""Tests for extended observation tags (preference, mistake, architecture, next).

확장 태그 테스트: preference, mistake, architecture, next 4개 태그의
패턴 매칭과 config 등록을 검증한다.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestExtendedTagsConfig:
    """Verify new tags are registered in config."""

    def test_all_eight_tags_present(self):
        from openclaw_mem.config import OBSERVATION_TAGS
        expected = {
            "learning", "decision", "error", "insight",
            "preference", "mistake", "architecture", "next",
        }
        assert set(OBSERVATION_TAGS) == expected

    def test_brain_tag_section_mapping(self):
        from openclaw_mem.config import BRAIN_TAG_SECTION
        assert "preference" in BRAIN_TAG_SECTION
        assert "mistake" in BRAIN_TAG_SECTION
        assert "architecture" in BRAIN_TAG_SECTION
        assert "next" in BRAIN_TAG_SECTION


class TestPreferencePatterns:
    """Test preference tag pattern extraction."""

    def test_preference_korean(self):
        from openclaw_mem.auto_capture import extract_observations_from_text
        text = "선호: Tailwind CSS를 모든 프로젝트에 사용한다"
        obs = extract_observations_from_text(text)
        assert any(o["tag"] == "preference" for o in obs)

    def test_preference_english(self):
        from openclaw_mem.auto_capture import extract_observations_from_text
        text = "Prefer: use Rust over C++ for new modules"
        obs = extract_observations_from_text(text)
        assert any(o["tag"] == "preference" for o in obs)

    def test_preference_always_use(self):
        from openclaw_mem.auto_capture import extract_observations_from_text
        text = "우리는 항상 TypeScript를 사용해야 한다는 결론"
        obs = extract_observations_from_text(text)
        assert any(o["tag"] == "preference" for o in obs)


class TestMistakePatterns:
    """Test mistake tag pattern extraction."""

    def test_mistake_korean(self):
        from openclaw_mem.auto_capture import extract_observations_from_text
        text = "실수: update-posts.sh 실행 안 하고 배포해서 포스트가 안 보임"
        obs = extract_observations_from_text(text)
        assert any(o["tag"] == "mistake" for o in obs)

    def test_mistake_english(self):
        from openclaw_mem.auto_capture import extract_observations_from_text
        text = "Mistake: forgot to run migrations before deployment"
        obs = extract_observations_from_text(text)
        assert any(o["tag"] == "mistake" for o in obs)

    def test_mistake_caution(self):
        from openclaw_mem.auto_capture import extract_observations_from_text
        text = "주의: 크론잡 설정 시 타임존 반드시 확인해야 함"
        obs = extract_observations_from_text(text)
        assert any(o["tag"] == "mistake" for o in obs)

    def test_mistake_warning_emoji(self):
        from openclaw_mem.auto_capture import extract_observations_from_text
        text = "배포 전에 ⚠️ 환경변수 확인 필수"
        obs = extract_observations_from_text(text)
        assert any(o["tag"] == "mistake" for o in obs)


class TestArchitecturePatterns:
    """Test architecture tag pattern extraction."""

    def test_architecture_korean(self):
        from openclaw_mem.auto_capture import extract_observations_from_text
        text = "아키텍처: 3-Surface 패턴으로 UI를 분리한다"
        obs = extract_observations_from_text(text)
        assert any(o["tag"] == "architecture" for o in obs)

    def test_architecture_english(self):
        from openclaw_mem.auto_capture import extract_observations_from_text
        text = "Architecture: microservices with event-driven communication"
        obs = extract_observations_from_text(text)
        assert any(o["tag"] == "architecture" for o in obs)

    def test_architecture_design(self):
        from openclaw_mem.auto_capture import extract_observations_from_text
        text = "설계: 데이터 레이어와 UI 레이어를 완전히 분리"
        obs = extract_observations_from_text(text)
        assert any(o["tag"] == "architecture" for o in obs)

    def test_architecture_structure(self):
        from openclaw_mem.auto_capture import extract_observations_from_text
        text = "구조: 모듈별 독립 패키지로 구성하여 의존성 분리"
        obs = extract_observations_from_text(text)
        assert any(o["tag"] == "architecture" for o in obs)


class TestNextPatterns:
    """Test next tag pattern extraction."""

    def test_next_korean(self):
        from openclaw_mem.auto_capture import extract_observations_from_text
        text = "다음: Godot 통합 작업 진행 및 테스트 추가"
        obs = extract_observations_from_text(text)
        assert any(o["tag"] == "next" for o in obs)

    def test_next_english(self):
        from openclaw_mem.auto_capture import extract_observations_from_text
        text = "Next: implement brain-check sanitizer command"
        obs = extract_observations_from_text(text)
        assert any(o["tag"] == "next" for o in obs)
