#!/usr/bin/env python3
"""Archive old memory files to archive directory (Cold layer).

Files older than ARCHIVE_AFTER_DAYS in memory/ are moved to the archive.
They remain indexed in LanceDB for search.

Usage:
    openclaw-mem archive              # dry-run: show what would be archived
    openclaw-mem archive --execute    # actually move files
    openclaw-mem archive --reindex    # re-index archive directory
"""
import argparse
import glob
import os
import re
import shutil
import sys
import time
import warnings
warnings.filterwarnings("ignore")

from openclaw_mem.config import (
    WORKSPACE_ROOT, ARCHIVE_DIR, ARCHIVE_AFTER_DAYS, OBSERVATIONS_FILE
)
from datetime import datetime, timedelta


# Files that should never be archived (Hot layer)
PROTECTED_FILES = {
    "core.md",
    "observations.md",
    "today.md",
}


def get_memory_files():
    """Get all .md files in memory/ (not archive/)."""
    memory_dir = os.path.join(WORKSPACE_ROOT, "memory")
    files = []
    for f in glob.glob(os.path.join(memory_dir, "*.md")):
        basename = os.path.basename(f)
        # Skip symlinks (like today.md)
        if os.path.islink(f):
            continue
        # Skip protected files
        if basename in PROTECTED_FILES:
            continue
        files.append(f)
    return sorted(files)


def is_old_enough(filepath, days=ARCHIVE_AFTER_DAYS):
    """Check if a file is old enough to archive.

    Uses:
    1. Date in filename (YYYY-MM-DD pattern) if present
    2. File modification time as fallback
    """
    basename = os.path.basename(filepath)
    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', basename)

    if date_match:
        try:
            file_date = datetime.strptime(date_match.group(1), "%Y-%m-%d")
            cutoff = datetime.now() - timedelta(days=days)
            return file_date < cutoff
        except ValueError:
            pass

    # Fallback to mtime
    mtime = os.path.getmtime(filepath)
    cutoff_ts = time.time() - (days * 86400)
    return mtime < cutoff_ts


def find_archivable():
    """Find files that should be archived."""
    files = get_memory_files()
    archivable = []
    for f in files:
        if is_old_enough(f):
            archivable.append(f)
    return archivable


def archive_files(files, verbose=True):
    """Move files to archive directory."""
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    moved = []

    for src in files:
        basename = os.path.basename(src)
        dst = os.path.join(ARCHIVE_DIR, basename)

        # Handle name collision
        if os.path.exists(dst):
            if verbose:
                print(f"  SKIP (exists in archive): {basename}")
            continue

        shutil.move(src, dst)
        moved.append((src, dst))
        if verbose:
            print(f"  Archived: {basename}")

    return moved


def reindex_archive(verbose=True):
    """Re-index archive files to ensure they remain searchable."""
    from openclaw_mem.index import index_single

    archive_files_list = glob.glob(os.path.join(ARCHIVE_DIR, "*.md"))
    if not archive_files_list:
        if verbose:
            print("No archive files to index.")
        return 0

    total = 0
    for f in sorted(archive_files_list):
        count = index_single(f, verbose=verbose)
        total += count

    return total


def main():
    parser = argparse.ArgumentParser(
        description="Archive old memory files (3-Layer memory: Cold layer)")
    parser.add_argument("--execute", action="store_true",
                        help="Actually move files (default is dry-run)")
    parser.add_argument("--reindex", action="store_true",
                        help="Re-index archive directory into LanceDB")
    parser.add_argument("--days", type=int, default=ARCHIVE_AFTER_DAYS,
                        help=f"Archive files older than N days (default: {ARCHIVE_AFTER_DAYS})")
    parser.add_argument("--quiet", "-q", action="store_true",
                        help="Suppress output")

    args = parser.parse_args()
    verbose = not args.quiet

    if args.reindex:
        reindex_archive(verbose)
        return

    archivable = find_archivable()

    if not archivable:
        if verbose:
            print(f"No files older than {args.days} days to archive.")
        return

    if verbose:
        print(f"Found {len(archivable)} files older than {args.days} days:")
        for f in archivable:
            print(f"  {os.path.basename(f)}")

    if args.execute:
        if verbose:
            print(f"\nArchiving to {ARCHIVE_DIR}/...")
        moved = archive_files(archivable, verbose)
        if verbose:
            print(f"\nMoved {len(moved)} files.")
            print("Run 'openclaw-mem archive --reindex' to update search index.")
    else:
        if verbose:
            print(f"\nDry run. Use --execute to actually move files.")


if __name__ == "__main__":
    main()
