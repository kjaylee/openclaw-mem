#!/usr/bin/env python3
"""Record structured observations to observations file and index into LanceDB.

Usage:
    openclaw-mem observe "observation text" --tag learning
    openclaw-mem observe "decision made" --tag decision
"""
import argparse
import logging
import os
import sys
import warnings
warnings.filterwarnings("ignore")

from openclaw_mem.config import OBSERVATIONS_FILE, OBSERVATION_TAGS
from openclaw_mem.sanitizer import get_sanitizer
from datetime import datetime

logger = logging.getLogger(__name__)


def append_observation(text: str, tag: str) -> str:
    """Append an observation to observations file.

    Returns the formatted entry string.
    Injection patterns are detected and filtered before storage.
    """
    sanitizer = get_sanitizer()
    is_safe, matched = sanitizer.check(text)
    if not is_safe:
        logger.warning(
            "Injection pattern detected in observation: %s", matched
        )
        text = sanitizer.sanitize(text)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"- [{timestamp}] **[{tag}]** {text}"

    # Ensure directory exists
    os.makedirs(os.path.dirname(OBSERVATIONS_FILE), exist_ok=True)

    # Create file with header if it doesn't exist
    if not os.path.exists(OBSERVATIONS_FILE):
        with open(OBSERVATIONS_FILE, "w", encoding="utf-8") as f:
            f.write("# Observations\n\n")

    # Append the entry
    with open(OBSERVATIONS_FILE, "a", encoding="utf-8") as f:
        f.write(entry + "\n")

    return entry


def main():
    parser = argparse.ArgumentParser(description="Record a structured observation")
    parser.add_argument("text", help="Observation text to record")
    parser.add_argument("--tag", "-t", type=str, default="insight",
                        choices=OBSERVATION_TAGS,
                        help=f"Tag for the observation ({', '.join(OBSERVATION_TAGS)})")
    parser.add_argument("--quiet", "-q", action="store_true",
                        help="Suppress output")

    args = parser.parse_args()
    verbose = not args.quiet

    # 1. Append to observations file
    entry = append_observation(args.text, args.tag)
    if verbose:
        print(f"Recorded: {entry}")

    # 2. Index into LanceDB immediately
    from openclaw_mem.index import index_observation
    chunk_id = index_observation(args.text, tag=args.tag, verbose=verbose)

    if verbose and chunk_id:
        print(f"Indexed as: {chunk_id}")


if __name__ == "__main__":
    main()
