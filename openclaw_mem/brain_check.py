#!/usr/bin/env python3
"""Brain integrity checker — scans Brain files for injection patterns.

memory/projects/*.md 파일을 스캔하여 injection 패턴을 감지하고
PASS/WARN 결과를 출력한다. --fix 옵션으로 자동 제거 가능.

Scans project Brain files for prompt injection patterns using
the existing MemorySanitizer. Reports PASS/WARN per file.
"""
import argparse
import glob
import os
import sys
from typing import Dict, List, Tuple

from openclaw_mem.config import BRAIN_PROJECTS_DIR
from openclaw_mem.sanitizer import get_sanitizer


def scan_brain_file(filepath: str) -> List[Dict]:
    """Scan a single Brain file for injection patterns.

    Brain 파일 한 개를 스캔하여 발견된 injection 패턴 목록 반환.

    Args:
        filepath: Absolute path to the Brain markdown file.

    Returns:
        List of dicts: {line_num, line_text, matched_patterns}
    """
    sanitizer = get_sanitizer()
    findings: List[Dict] = []

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.rstrip("\n")
                if not line.strip():
                    continue
                is_safe, matched = sanitizer.check(line)
                if not is_safe:
                    findings.append({
                        "line_num": line_num,
                        "line_text": line.strip(),
                        "matched_patterns": matched,
                    })
    except (IOError, OSError) as e:
        print(f"Error reading {filepath}: {e}", file=sys.stderr)

    return findings


def scan_all_brains(
    projects_dir: str = "",
) -> Dict[str, List[Dict]]:
    """Scan all Brain files in the projects directory.

    memory/projects/*.md 전체를 스캔하여 파일별 결과 반환.

    Args:
        projects_dir: Path to projects directory. Defaults to config.

    Returns:
        Dict mapping filepath → list of findings.
    """
    if not projects_dir:
        projects_dir = BRAIN_PROJECTS_DIR

    results: Dict[str, List[Dict]] = {}

    if not os.path.isdir(projects_dir):
        return results

    for filepath in sorted(glob.glob(os.path.join(projects_dir, "*.md"))):
        findings = scan_brain_file(filepath)
        results[filepath] = findings

    return results


def fix_brain_file(filepath: str) -> Tuple[int, int]:
    """Remove injection patterns from a Brain file.

    감지된 injection 패턴을 [FILTERED]로 대체.

    Args:
        filepath: Absolute path to the Brain file.

    Returns:
        Tuple of (lines_fixed, total_patterns_removed).
    """
    sanitizer = get_sanitizer()
    lines_fixed = 0
    patterns_removed = 0

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        new_lines = []
        for line in lines:
            is_safe, matched = sanitizer.check(line)
            if not is_safe:
                line = sanitizer.sanitize(line)
                lines_fixed += 1
                patterns_removed += len(matched)
            new_lines.append(line)

        with open(filepath, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

    except (IOError, OSError) as e:
        print(f"Error fixing {filepath}: {e}", file=sys.stderr)

    return lines_fixed, patterns_removed


def print_report(
    results: Dict[str, List[Dict]],
    verbose: bool = True,
) -> Tuple[int, int]:
    """Print PASS/WARN report for all scanned files.

    결과를 PASS/WARN 형식으로 출력.

    Args:
        results: Dict from scan_all_brains.
        verbose: Show detailed findings.

    Returns:
        Tuple of (pass_count, warn_count).
    """
    pass_count = 0
    warn_count = 0

    if not results:
        if verbose:
            print("No Brain files found to check.")
        return 0, 0

    for filepath, findings in results.items():
        basename = os.path.basename(filepath)
        if findings:
            warn_count += 1
            print(f"WARN  {basename} ({len(findings)} issue(s))")
            if verbose:
                for f in findings:
                    print(f"  L{f['line_num']}: {f['line_text'][:80]}")
                    for pat in f["matched_patterns"]:
                        print(f"    → pattern: {pat}")
        else:
            pass_count += 1
            print(f"PASS  {basename}")

    print(f"\n{pass_count} passed, {warn_count} warned")
    return pass_count, warn_count


def main():
    """CLI entry point for brain-check.

    Brain 파일 무결성 검사 CLI.
    """
    parser = argparse.ArgumentParser(
        description="Check Brain files for injection patterns")
    parser.add_argument("--fix", action="store_true",
                        help="Auto-remove detected injection patterns")
    parser.add_argument("--dir", type=str, default="",
                        help="Projects directory to scan (default: config)")
    parser.add_argument("--quiet", "-q", action="store_true",
                        help="Minimal output")

    args = parser.parse_args()
    verbose = not args.quiet

    projects_dir = args.dir or BRAIN_PROJECTS_DIR

    if verbose:
        print(f"Scanning Brain files in: {projects_dir}\n")

    results = scan_all_brains(projects_dir)

    if args.fix:
        total_fixed = 0
        total_patterns = 0
        for filepath, findings in results.items():
            if findings:
                fixed, patterns = fix_brain_file(filepath)
                total_fixed += fixed
                total_patterns += patterns
                if verbose:
                    basename = os.path.basename(filepath)
                    print(f"FIXED {basename}: {fixed} line(s), "
                          f"{patterns} pattern(s) removed")

        # Re-scan after fix
        if total_fixed > 0:
            if verbose:
                print(f"\nFixed {total_fixed} line(s), "
                      f"{total_patterns} pattern(s) total.\n"
                      f"Re-scanning...\n")
            results = scan_all_brains(projects_dir)

    pass_count, warn_count = print_report(results, verbose=verbose)

    # Exit code: 1 if warnings remain
    if warn_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
