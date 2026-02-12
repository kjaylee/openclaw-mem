#!/usr/bin/env python3
"""Initialize an openclaw-mem workspace in the current directory.

Creates the standard memory directory structure, a .env file,
and runs the first index pass.
"""
import os
import subprocess
import sys


# ANSI colors
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"

CORE_MD_TEMPLATE = """\
# Core Memory

## Key Decisions

## Lessons Learned
"""


def _created(path: str) -> None:
    print(f"  {GREEN}✅ Created{RESET}  {path}")


def _exists(path: str) -> None:
    print(f"  {YELLOW}⏭️  Exists{RESET}  {path}")


def _ensure_dir(dirpath: str) -> bool:
    """Create directory if missing. Returns True if created."""
    if os.path.isdir(dirpath):
        _exists(dirpath)
        return False
    os.makedirs(dirpath, exist_ok=True)
    _created(dirpath)
    return True


def _ensure_file(filepath: str, content: str = "") -> bool:
    """Create file if missing. Returns True if created."""
    if os.path.exists(filepath):
        _exists(filepath)
        return False
    # Ensure parent directory exists
    parent = os.path.dirname(filepath)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    _created(filepath)
    return True


def init_workspace(root: str | None = None, run_index: bool = True) -> dict:
    """Initialize the workspace at the given root (default: cwd).

    Returns a dict summarising what was created/skipped.
    """
    root = root or os.getcwd()
    results: dict[str, str] = {}

    print(f"\n{CYAN}🧠 Initializing openclaw-mem workspace in {root}{RESET}\n")

    # 1. memory/ directory
    memory_dir = os.path.join(root, "memory")
    if _ensure_dir(memory_dir):
        results["memory/"] = "created"
    else:
        results["memory/"] = "exists"

    # 2. memory/core.md
    core_md = os.path.join(memory_dir, "core.md")
    if _ensure_file(core_md, CORE_MD_TEMPLATE):
        results["memory/core.md"] = "created"
    else:
        results["memory/core.md"] = "exists"

    # 3. memory/projects/ (Brain directory)
    projects_dir = os.path.join(memory_dir, "projects")
    if _ensure_dir(projects_dir):
        results["memory/projects/"] = "created"
    else:
        results["memory/projects/"] = "exists"

    # 4. memory/observations.md
    obs_md = os.path.join(memory_dir, "observations.md")
    if _ensure_file(obs_md, ""):
        results["memory/observations.md"] = "created"
    else:
        results["memory/observations.md"] = "exists"

    # 5. .env file with OPENCLAW_MEM_ROOT
    env_file = os.path.join(root, ".env")
    env_line = f'OPENCLAW_MEM_ROOT="{root}"\n'
    if _ensure_file(env_file, env_line):
        results[".env"] = "created"
    else:
        results[".env"] = "exists"

    # 6. First indexing pass
    if run_index:
        print(f"\n  {CYAN}📦 Indexing...{RESET}")
        try:
            subprocess.run(
                [sys.executable, "-m", "openclaw_mem.cli", "index", "--all", "-q"],
                cwd=root,
                env={**os.environ, "OPENCLAW_MEM_ROOT": root},
                check=False,
                capture_output=True,
            )
            results["index"] = "done"
            print(f"  {GREEN}✅ Indexing complete{RESET}")
        except Exception as exc:
            results["index"] = f"error: {exc}"
            print(f"  {YELLOW}⚠️  Indexing skipped ({exc}){RESET}")

    print(f"\n{GREEN}✅ Workspace ready!{RESET}\n")
    return results


def main() -> None:
    """CLI entry-point."""
    init_workspace()


if __name__ == "__main__":
    main()
