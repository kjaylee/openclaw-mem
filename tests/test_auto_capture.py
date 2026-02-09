#!/usr/bin/env python3
"""Tests for auto-capture from session transcripts."""
import json
import os
import sys
import tempfile
from datetime import datetime, timezone

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def make_session_entry(text, role="assistant", ts=None):
    """Build a single JSONL entry dict."""
    if ts is None:
        ts = datetime.now(timezone.utc).isoformat()
    return {
        "type": "message",
        "timestamp": ts,
        "message": {
            "role": role,
            "content": [{"type": "text", "text": text}],
        },
    }


def write_session_file(entries):
    """Write entries to a temp .jsonl file, return path."""
    f = tempfile.NamedTemporaryFile(
        mode="w", suffix=".jsonl", delete=False
    )
    for e in entries:
        f.write(json.dumps(e, ensure_ascii=False) + "\n")
    f.close()
    return f.name


# ────────────────────── Pattern Extraction ──────────────────────

class TestPatternExtraction:
    """Test observation pattern extraction from text."""

    def test_decision_colon(self):
        from openclaw_mem.auto_capture import extract_observations_from_text
        text = "이 프로젝트에서 결정: Redis를 캐시 레이어로 사용한다"
        obs = extract_observations_from_text(text)
        assert any(o["tag"] == "decision" for o in obs)

    def test_decision_english(self):
        from openclaw_mem.auto_capture import extract_observations_from_text
        text = "After discussion, Decision: use Rust for the backend implementation"
        obs = extract_observations_from_text(text)
        assert any(o["tag"] == "decision" for o in obs)

    def test_decision_conclusion(self):
        from openclaw_mem.auto_capture import extract_observations_from_text
        text = "여러 옵션 검토 후 결론: Godot 4.6으로 통일하기로"
        obs = extract_observations_from_text(text)
        assert any(o["tag"] == "decision" for o in obs)

    def test_decision_adopt(self):
        from openclaw_mem.auto_capture import extract_observations_from_text
        text = "비교 분석 결과 → 채택 Rust+WASM 방식"
        obs = extract_observations_from_text(text)
        assert any(o["tag"] == "decision" for o in obs)

    def test_decision_keyword(self):
        from openclaw_mem.auto_capture import extract_observations_from_text
        text = "Rust+Godot 전용 스택으로 결정했습니다"
        obs = extract_observations_from_text(text)
        assert any(o["tag"] == "decision" for o in obs)

    def test_learning_colon(self):
        from openclaw_mem.auto_capture import extract_observations_from_text
        text = "배움: Python venv는 재생성이 필요할 수 있다"
        obs = extract_observations_from_text(text)
        assert any(o["tag"] == "learning" for o in obs)

    def test_learning_english(self):
        from openclaw_mem.auto_capture import extract_observations_from_text
        text = "Learned: LanceDB requires numpy<2 for compatibility"
        obs = extract_observations_from_text(text)
        assert any(o["tag"] == "learning" for o in obs)

    def test_learning_discovery(self):
        from openclaw_mem.auto_capture import extract_observations_from_text
        text = "발견: auto_capture.py 패턴 매칭이 한글도 잘 처리함"
        obs = extract_observations_from_text(text)
        assert any(o["tag"] == "learning" for o in obs)

    def test_learning_actually(self):
        from openclaw_mem.auto_capture import extract_observations_from_text
        text = "코드를 보면 알고보니 기존 구현에서 이미 처리하고 있었다"
        obs = extract_observations_from_text(text)
        assert any(o["tag"] == "learning" for o in obs)

    def test_error_korean(self):
        from openclaw_mem.auto_capture import extract_observations_from_text
        text = "빌드 에러: ModuleNotFoundError for pandas 모듈"
        obs = extract_observations_from_text(text)
        assert any(o["tag"] == "error" for o in obs)

    def test_error_english(self):
        from openclaw_mem.auto_capture import extract_observations_from_text
        text = "Build Error: cannot find module 'lancedb' in environment"
        obs = extract_observations_from_text(text)
        assert any(o["tag"] == "error" for o in obs)

    def test_error_fail_keyword(self):
        from openclaw_mem.auto_capture import extract_observations_from_text
        text = "pytest run ERROR: 3 tests failed out of 10 total"
        obs = extract_observations_from_text(text)
        assert any(o["tag"] == "error" for o in obs)

    def test_error_connection_refused(self):
        from openclaw_mem.auto_capture import extract_observations_from_text
        text = "Gateway returned Connection refused on port 8080"
        obs = extract_observations_from_text(text)
        assert any(o["tag"] == "error" for o in obs)

    def test_error_http_code(self):
        from openclaw_mem.auto_capture import extract_observations_from_text
        text = "API 요청에서 401 Unauthorized 에러 발생"
        obs = extract_observations_from_text(text)
        assert any(o["tag"] == "error" for o in obs)

    def test_error_exit_code(self):
        from openclaw_mem.auto_capture import extract_observations_from_text
        text = "Process exited with code 1 after build failure"
        obs = extract_observations_from_text(text)
        assert any(o["tag"] == "error" for o in obs)

    def test_todo_pattern(self):
        from openclaw_mem.auto_capture import extract_observations_from_text
        text = "TODO: 테스트 커버리지 올리기 필요"
        obs = extract_observations_from_text(text)
        assert any(o["tag"] == "insight" for o in obs)

    def test_todo_korean(self):
        from openclaw_mem.auto_capture import extract_observations_from_text
        text = "할일: 크론잡 등록하고 모니터링 추가"
        obs = extract_observations_from_text(text)
        assert any(o["tag"] == "insight" for o in obs)

    def test_completion_deploy(self):
        from openclaw_mem.auto_capture import extract_observations_from_text
        text = "sanguo 게임 배포 완료 — itch.io에 성공적으로 업로드"
        obs = extract_observations_from_text(text)
        assert any(o["tag"] == "learning" for o in obs)

    def test_completion_test_pass(self):
        from openclaw_mem.auto_capture import extract_observations_from_text
        text = "RAG 시스템 테스트 통과 — 13/13 성공"
        obs = extract_observations_from_text(text)
        assert any(o["tag"] == "learning" for o in obs)

    def test_completion_checkmark(self):
        from openclaw_mem.auto_capture import extract_observations_from_text
        text = "auto-capture 구현 ✅ 모든 테스트 성공"
        obs = extract_observations_from_text(text)
        assert any(o["tag"] == "learning" for o in obs)

    def test_tool_success(self):
        from openclaw_mem.auto_capture import extract_observations_from_text
        text = "Process exited with code 0 — build completed successfully"
        obs = extract_observations_from_text(text)
        assert any(o["tag"] == "insight" for o in obs)

    def test_short_text_ignored(self):
        from openclaw_mem.auto_capture import extract_observations_from_text
        text = "에러"
        obs = extract_observations_from_text(text)
        assert len(obs) == 0

    def test_json_line_ignored(self):
        from openclaw_mem.auto_capture import extract_observations_from_text
        text = '{"error": "something failed badly"}'
        obs = extract_observations_from_text(text)
        assert len(obs) == 0

    def test_markdown_line_ignored(self):
        from openclaw_mem.auto_capture import extract_observations_from_text
        text = "- 결정: 이것은 마크다운 리스트"
        obs = extract_observations_from_text(text)
        assert len(obs) == 0

    def test_heartbeat_ignored(self):
        from openclaw_mem.auto_capture import extract_observations_from_text
        text = "HEARTBEAT check 에러 발생 — 재시작됨"
        obs = extract_observations_from_text(text)
        assert len(obs) == 0


# ────────────────────── Deduplication ──────────────────────

class TestDeduplication:
    """Test hash-based deduplication."""

    def test_hash_consistency(self):
        from openclaw_mem.auto_capture import text_hash
        h1 = text_hash("some observation text")
        h2 = text_hash("some observation text")
        assert h1 == h2
        assert len(h1) == 16

    def test_hash_difference(self):
        from openclaw_mem.auto_capture import text_hash
        h1 = text_hash("observation A")
        h2 = text_hash("observation B")
        assert h1 != h2

    def test_deduplicate_removes_dupes(self):
        from openclaw_mem.auto_capture import deduplicate_observations
        obs = [
            {"text": "Duplicate text here", "tag": "learning"},
            {"text": "Duplicate text here", "tag": "learning"},
            {"text": "Unique text over here", "tag": "decision"},
        ]
        seen: set = set()
        result = deduplicate_observations(obs, seen)
        assert len(result) == 2

    def test_deduplicate_respects_seen(self):
        from openclaw_mem.auto_capture import deduplicate_observations, text_hash
        obs = [{"text": "Already seen text", "tag": "error"}]
        seen = {text_hash("Already seen text")}
        result = deduplicate_observations(obs, seen)
        assert len(result) == 0


# ────────────────────── Session File Scanning ──────────────────────

class TestSessionScanning:
    """Test JSONL session file scanning."""

    def test_scan_extracts_decision(self):
        from openclaw_mem.auto_capture import scan_session_file
        path = write_session_file([
            make_session_entry("프로젝트 결정: Rust WASM 빌드로 통일한다"),
        ])
        try:
            obs = scan_session_file(path)
            assert len(obs) > 0
            assert any(o["tag"] == "decision" for o in obs)
        finally:
            os.unlink(path)

    def test_scan_skips_non_message(self):
        from openclaw_mem.auto_capture import scan_session_file
        f = tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False
        )
        f.write(json.dumps({"type": "session", "id": "abc"}) + "\n")
        f.close()
        try:
            obs = scan_session_file(f.name)
            assert len(obs) == 0
        finally:
            os.unlink(f.name)

    def test_scan_skips_system_role(self):
        from openclaw_mem.auto_capture import scan_session_file
        path = write_session_file([
            make_session_entry("결정: skip this", role="system"),
        ])
        try:
            obs = scan_session_file(path)
            assert len(obs) == 0
        finally:
            os.unlink(path)

    def test_scan_per_session_dedup(self):
        """Same pattern repeated in session → only first kept."""
        from openclaw_mem.auto_capture import scan_session_file
        path = write_session_file([
            make_session_entry("프로젝트 결정: Rust WASM으로 통일"),
            make_session_entry("다시 한번 결정: Rust WASM으로 통일"),
        ])
        try:
            obs = scan_session_file(path)
            decision_obs = [o for o in obs if o["tag"] == "decision"]
            assert len(decision_obs) == 1
        finally:
            os.unlink(path)

    def test_scan_preserves_timestamp(self):
        from openclaw_mem.auto_capture import scan_session_file
        ts = "2026-02-09T10:00:00Z"
        path = write_session_file([
            make_session_entry("프로젝트 결정: TypeScript 제거", ts=ts),
        ])
        try:
            obs = scan_session_file(path)
            assert len(obs) > 0
            assert obs[0]["timestamp"] == ts
        finally:
            os.unlink(path)


# ────────────────────── State Persistence ──────────────────────

class TestState:
    """Test state load/save."""

    def test_load_missing_state(self):
        from openclaw_mem.auto_capture import load_state
        import tempfile
        # Use a non-existent path
        original = os.environ.get("OPENCLAW_MEM_CAPTURE_STATE")
        try:
            os.environ["OPENCLAW_MEM_CAPTURE_STATE"] = os.path.join(
                tempfile.gettempdir(), "nonexistent_state.json"
            )
            # Re-import to pick up new env
            import importlib
            import openclaw_mem.auto_capture as ac
            importlib.reload(ac)
            state = ac.load_state()
            assert "seen_hashes" in state
            assert isinstance(state["seen_hashes"], list)
        finally:
            if original is not None:
                os.environ["OPENCLAW_MEM_CAPTURE_STATE"] = original
            elif "OPENCLAW_MEM_CAPTURE_STATE" in os.environ:
                del os.environ["OPENCLAW_MEM_CAPTURE_STATE"]

    def test_save_and_load_roundtrip(self):
        import tempfile
        from openclaw_mem.auto_capture import save_state, load_state
        state_file = os.path.join(tempfile.gettempdir(), "test_state.json")
        original_sf = os.environ.get("OPENCLAW_MEM_CAPTURE_STATE")
        try:
            os.environ["OPENCLAW_MEM_CAPTURE_STATE"] = state_file
            import importlib
            import openclaw_mem.auto_capture as ac
            importlib.reload(ac)
            test_state = {"seen_hashes": ["abc123", "def456"]}
            ac.save_state(test_state)
            loaded = ac.load_state()
            assert loaded["seen_hashes"] == ["abc123", "def456"]
        finally:
            if original_sf is not None:
                os.environ["OPENCLAW_MEM_CAPTURE_STATE"] = original_sf
            elif "OPENCLAW_MEM_CAPTURE_STATE" in os.environ:
                del os.environ["OPENCLAW_MEM_CAPTURE_STATE"]
            if os.path.exists(state_file):
                os.remove(state_file)
