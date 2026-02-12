#!/usr/bin/env python3
"""Brain router — routes observations to project-specific Brain files.

프로젝트별 Brain 파일에 관찰을 자동 라우팅한다.
키워드 매칭으로 프로젝트를 감지하고, 태그에 따라 적절한 섹션에 기록.

Routes observations to project Brain files based on keyword matching.
Falls back to observations.md for unmatched observations.
"""
import os
import re
from typing import Dict, List, Optional, Tuple

from openclaw_mem.config import (
    BRAIN_PROJECT_KEYWORDS,
    BRAIN_TAG_SECTION,
    BRAIN_PROJECTS_DIR,
    WORKSPACE_ROOT,
)


def detect_project(text: str) -> Optional[str]:
    """Detect project from observation text via keyword matching.

    텍스트에서 프로젝트 키워드를 감지하여 Brain 파일 경로를 반환.
    매칭 안 되면 None 반환.

    Args:
        text: Observation text to analyze.

    Returns:
        Relative path to Brain file (e.g. "memory/projects/sanguo.md"),
        or None if no project keyword matched.
    """
    text_lower = text.lower()
    for keyword, brain_path in BRAIN_PROJECT_KEYWORDS.items():
        if keyword.lower() in text_lower:
            return brain_path
    return None


def get_brain_section(tag: str) -> str:
    """Get the Brain section heading for a given tag.

    태그에 해당하는 Brain 섹션 헤딩을 반환.

    Args:
        tag: Observation tag (e.g. "decision", "learning").

    Returns:
        Section heading string (e.g. "## Architecture Decisions").
    """
    return BRAIN_TAG_SECTION.get(tag, "## Observations")


def _ensure_brain_file(filepath: str) -> None:
    """Create Brain file with default header if it doesn't exist.

    Brain 파일이 없으면 기본 헤더로 생성.

    Args:
        filepath: Absolute path to Brain file.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    if not os.path.exists(filepath):
        # Derive project name from filename
        name = os.path.splitext(os.path.basename(filepath))[0]
        title = name.replace("-", " ").title()
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# {title} Brain\n\n")


def _find_or_create_section(content: str, section: str) -> Tuple[str, int]:
    """Find a section in content; if missing, append it.

    Brain 파일 내용에서 섹션을 찾거나, 없으면 끝에 추가.

    Args:
        content: Full file content.
        section: Section heading (e.g. "## Lessons Learned").

    Returns:
        Tuple of (updated content, insert position after section heading).
    """
    # Find the section heading
    pattern = re.compile(r'^' + re.escape(section) + r'\s*$', re.MULTILINE)
    match = pattern.search(content)

    if match:
        # Section exists — find end of heading line
        insert_pos = match.end()
        # Skip any blank lines right after heading
        while insert_pos < len(content) and content[insert_pos] == '\n':
            insert_pos += 1
            # Keep one blank line after heading
            break
        return content, insert_pos
    else:
        # Section doesn't exist — append it
        if not content.endswith("\n"):
            content += "\n"
        content += f"\n{section}\n\n"
        return content, len(content)


def _content_already_exists(content: str, section: str, entry_text: str) -> bool:
    """Check if an equivalent entry already exists in the section.

    동일 내용이 이미 섹션에 존재하는지 확인 (중복 방지).

    Args:
        content: Full file content.
        section: Section heading.
        entry_text: The core observation text (without timestamp/tag prefix).

    Returns:
        True if duplicate found.
    """
    # Find section boundaries
    pattern = re.compile(r'^' + re.escape(section) + r'\s*$', re.MULTILINE)
    match = pattern.search(content)
    if not match:
        return False

    # Find next section or end of file
    next_section = re.compile(r'^## ', re.MULTILINE)
    next_match = next_section.search(content, match.end())
    section_end = next_match.start() if next_match else len(content)

    section_content = content[match.end():section_end]

    # Normalize for comparison: collapse whitespace, strip
    normalized_entry = re.sub(r'\s+', ' ', entry_text.strip()).lower()

    for line in section_content.split('\n'):
        # Extract text after tag/timestamp markers
        # Pattern: "- [timestamp] **[tag]** actual text"
        clean = re.sub(r'^-\s*\[.*?\]\s*\*\*\[.*?\]\*\*\s*', '', line.strip())
        if not clean:
            # Also handle simpler format: "- actual text"
            clean = re.sub(r'^-\s*', '', line.strip())
        normalized_line = re.sub(r'\s+', ' ', clean.strip()).lower()
        if normalized_line and normalized_entry in normalized_line:
            return True
        if normalized_line and normalized_line in normalized_entry:
            return True

    return False


def route_observation_to_brain(
    text: str,
    tag: str,
    timestamp: str = "",
    dry_run: bool = False,
) -> Optional[str]:
    """Route a single observation to its project Brain file.

    관찰을 프로젝트별 Brain 파일의 적절한 섹션에 기록.
    프로젝트 감지 안 되면 None 반환 (호출자가 기존 방식으로 처리).

    Args:
        text: Observation text.
        tag: Observation tag.
        timestamp: Formatted timestamp string.
        dry_run: If True, don't write to file.

    Returns:
        Brain file path if routed, None if no project matched.
    """
    brain_rel_path = detect_project(text)
    if brain_rel_path is None:
        return None

    brain_abs_path = os.path.join(WORKSPACE_ROOT, brain_rel_path)
    section = get_brain_section(tag)

    if dry_run:
        return brain_rel_path

    # Ensure file exists
    _ensure_brain_file(brain_abs_path)

    # Read current content
    with open(brain_abs_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Check for duplicates
    if _content_already_exists(content, section, text):
        return brain_rel_path  # Already exists, skip

    # Find or create section
    content, insert_pos = _find_or_create_section(content, section)

    # Format entry
    entry = f"- [{timestamp}] **[{tag}]** {text}\n"

    # Insert at position
    new_content = content[:insert_pos] + entry + content[insert_pos:]

    # Write back
    with open(brain_abs_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    return brain_rel_path


def route_observations(
    observations: List[Dict],
    dry_run: bool = False,
    verbose: bool = True,
) -> Tuple[List[Dict], List[Dict]]:
    """Route a list of observations: Brain-routed vs fallback.

    관찰 리스트를 Brain 라우팅된 것과 폴백(observations.md)으로 분류.

    Args:
        observations: List of observation dicts with 'text', 'tag', 'timestamp'.
        dry_run: If True, don't write files.
        verbose: Print routing info.

    Returns:
        Tuple of (brain_routed, fallback) observation lists.
    """
    from datetime import datetime

    brain_routed: List[Dict] = []
    fallback: List[Dict] = []

    for obs in observations:
        tag = obs["tag"]
        text = obs["text"]
        ts = obs.get("timestamp", "")

        # Format timestamp
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            ts_fmt = dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            ts_fmt = datetime.now().strftime("%Y-%m-%d %H:%M")

        result = route_observation_to_brain(
            text, tag, timestamp=ts_fmt, dry_run=dry_run
        )

        if result is not None:
            if verbose:
                print(f"  → Brain [{result}] [{tag}] {text[:60]}")
            brain_routed.append(obs)
        else:
            fallback.append(obs)

    return brain_routed, fallback
