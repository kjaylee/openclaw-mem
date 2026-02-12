#!/usr/bin/env python3
"""Auto-capture observations from session transcripts.

Scans session JSONL files and extracts important observations
using rule-based patterns (no LLM required).

Usage:
    openclaw-mem auto-capture                    # Default: last 3 hours
    openclaw-mem auto-capture --since 6h         # Last 6 hours
    openclaw-mem auto-capture --since 24h        # Last 24 hours
    openclaw-mem auto-capture --dry-run          # Show only, don't write
    openclaw-mem auto-capture --quiet            # No output
"""
import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional

import warnings
warnings.filterwarnings("ignore")

from openclaw_mem.config import OBSERVATIONS_FILE

# --- Paths ---
# Session directory is configurable via environment variable
SESSION_DIR = os.environ.get(
    "OPENCLAW_MEM_SESSION_DIR",
    os.path.expanduser("~/.openclaw/agents/main/sessions")
)
STATE_FILE = os.environ.get(
    "OPENCLAW_MEM_CAPTURE_STATE",
    os.path.join(
        os.environ.get("OPENCLAW_MEM_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        ".openclaw_mem_capture_state.json"
    )
)

# --- Pattern Definitions ---
# Each: (tag, regex)  — group(1) is the captured text.

_RAW_PATTERNS: List[Tuple[str, str]] = [
    # ── Decision ──
    ("decision", r'결정:\s*(.{10,300})'),
    ("decision", r'Decision:\s*(.{10,300})'),
    ("decision", r'결론:\s*(.{10,300})'),
    ("decision", r'판정:\s*(.{10,300})'),
    ("decision", r'(.{5,}→\s*채택.*)'),
    ("decision", r'(.{5,}→\s*비추.*)'),
    ("decision", r'(.{10,}.+(?:으로\s*결정).*)'),
    ("decision", r'(.{10,}.+확정.{5,})'),
    ("decision", r'(.{10,}.+으로\s*간다.*)'),

    # ── Learning ──
    ("learning", r'배움:\s*(.{10,300})'),
    ("learning", r'Learned:\s*(.{10,300})'),
    ("learning", r'교훈:\s*(.{10,300})'),
    ("learning", r'알게됨:\s*(.{10,300})'),
    ("learning", r'발견:\s*(.{10,300})'),
    ("learning", r'(.{5,}알고보니.{10,})'),
    ("learning", r'(.{5,}사실은.{10,})'),

    # ── Completion → learning ──
    ("learning", r'(.+(?:배포|push|deploy)\s*완료.{3,})'),
    ("learning", r'(.+테스트\s*통과.{3,})'),
    ("learning", r'(.{10,}DONE.{3,})'),
    ("learning", r'(.{5,}✅.{3,})'),
    ("learning", r'(.{5,}완료.{5,})'),

    # ── Error ──
    ("error", r'에러:\s*(.{10,300})'),
    ("error", r'(?:^|[^"])Error:\s*(.{10,300})'),
    ("error", r'(.{5,}(?:ERROR|FAIL)[:\s].{5,})'),
    ("error", r'(.{5,}실패.{5,})'),
    ("error", r'(.{5,}오류.{5,})'),
    ("error", r'(.+Connection\s+refused.+)'),
    ("error", r'(.+SIGKILL.+)'),
    ("error", r'(.{5,}(?:timeout|Timeout).{10,})'),
    ("error", r'(.+(?:401|403|404|429|500)\s*'
     r'(?:에러|error|Error|Unauthorized|Forbidden|Not Found).+)'),
    ("error", r'(.*exited\s+with\s+code\s+[1-9]\d*.*)'),

    # ── TODO / Insight ──
    ("insight", r'TODO:?\s+(.{5,300})'),
    ("insight", r'할일:?\s+(.{5,300})'),
    ("insight", r'(.{5,}다음에\s+.{10,})'),
    ("insight", r'(.{5,}나중에\s+.{10,})'),
    ("insight", r'(.*exited\s+with\s+code\s+0.+(?:completed|success|done).*)'),

    # ── Preference (선호) ──
    ("preference", r'선호:\s*(.{10,300})'),
    ("preference", r'Prefer:\s*(.{10,300})'),
    ("preference", r'(.{3,}항상\s+.{3,}사용.*)'),

    # ── Mistake (실수/주의) ──
    ("mistake", r'실수:\s*(.{10,300})'),
    ("mistake", r'Mistake:\s*(.{10,300})'),
    ("mistake", r'주의:\s*(.{10,300})'),
    ("mistake", r'(.{5,}⚠️.{5,})'),

    # ── Architecture (아키텍처/설계) ──
    ("architecture", r'아키텍처:\s*(.{10,300})'),
    ("architecture", r'Architecture:\s*(.{10,300})'),
    ("architecture", r'설계:\s*(.{10,300})'),
    ("architecture", r'구조:\s*(.{10,300})'),

    # ── Next (다음 단계) ──
    ("next", r'다음:\s*(.{10,300})'),
    ("next", r'Next:\s*(.{10,300})'),
]

# Compile patterns
PATTERNS: List[Tuple[str, "re.Pattern"]] = [
    (tag, re.compile(pat)) for tag, pat in _RAW_PATTERNS
]

# Lines to skip (false-positive filters)
_SKIP_LINE_RE = re.compile(
    r'^\s*[\{\[\`\-\*#>]'       # JSON / markdown / blockquote
    r'|"error"\s*:'             # JSON error field
    r'|"timestamp"\s*:'         # JSON timestamp field
    r'|heartbeat'               # heartbeat messages
    r'|session_status'          # session status
    r'|HEARTBEAT',
    re.IGNORECASE,
)

# Roles to process (skip system, tool, etc.)
_ALLOWED_ROLES = {"user", "assistant"}


# ─────────────────────────── helpers ───────────────────────────

def text_hash(text: str) -> str:
    """MD5 hash (first 16 hex chars) for deduplication."""
    return hashlib.md5(text.encode()).hexdigest()[:16]


def _clean_text(text: str) -> str:
    """Trim and collapse whitespace."""
    return re.sub(r'\s+', ' ', text.strip())


# ─────────────────────────── state ───────────────────────────

def load_state() -> Dict:
    """Load state (seen hashes) from JSON file."""
    if not os.path.exists(STATE_FILE):
        return {"seen_hashes": []}
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"seen_hashes": []}


def save_state(state: Dict):
    """Persist state to JSON file."""
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


# ─────────────────────────── extraction ───────────────────────────

def extract_observations_from_text(text: str) -> List[Dict[str, str]]:
    """Extract observations from a text block.

    Returns list of dicts: {tag, text}
    """
    observations: List[Dict[str, str]] = []
    seen_in_block: Set[str] = set()  # per-block dedup (tag + first 30 chars)

    # Process line by line
    for line in text.split('\n'):
        line = line.strip()
        if not line or len(line) < 10:
            continue
        # Skip false-positive lines
        if _SKIP_LINE_RE.search(line):
            continue

        for tag, pattern in PATTERNS:
            m = pattern.search(line)
            if not m:
                continue

            captured = _clean_text(m.group(1))

            # Minimum length: avoid 1-word matches
            if len(captured) < 8:
                continue
            # Cap length
            if len(captured) > 300:
                captured = captured[:297] + "..."

            # Per-block dedup key
            dedup_key = f"{tag}:{captured[:30]}"
            if dedup_key in seen_in_block:
                continue
            seen_in_block.add(dedup_key)

            observations.append({"tag": tag, "text": captured})
            break  # one match per line is enough

    return observations


# ─────────────────────────── session scanning ───────────────────────────

def get_recent_sessions(since_hours: int = 3) -> List[str]:
    """Return session files modified within the last *since_hours*."""
    if not os.path.isdir(SESSION_DIR):
        return []

    cutoff_ts = (datetime.now(timezone.utc) - timedelta(hours=since_hours)).timestamp()
    sessions = [
        str(f) for f in Path(SESSION_DIR).glob("*.jsonl")
        if f.stat().st_mtime > cutoff_ts
    ]
    return sorted(sessions, key=lambda p: os.path.getmtime(p), reverse=True)


def scan_session_file(filepath: str) -> List[Dict]:
    """Scan one JSONL session file and return observations."""
    observations: List[Dict] = []
    session_seen: Set[str] = set()  # same session, same pattern → first only

    try:
        with open(filepath, "r") as f:
            for line_raw in f:
                line_raw = line_raw.strip()
                if not line_raw:
                    continue
                try:
                    entry = json.loads(line_raw)
                except json.JSONDecodeError:
                    continue

                if entry.get("type") != "message":
                    continue

                msg = entry.get("message", {})
                role = msg.get("role", "")
                if role not in _ALLOWED_ROLES:
                    continue

                # Collect text content
                content_items = msg.get("content", [])
                full_text = ""
                for item in content_items:
                    if isinstance(item, dict) and "text" in item:
                        full_text += item["text"] + "\n"
                    elif isinstance(item, str):
                        full_text += item + "\n"

                if not full_text.strip():
                    continue

                extracted = extract_observations_from_text(full_text)
                for obs in extracted:
                    # Per-session dedup
                    sess_key = f"{obs['tag']}:{obs['text'][:40]}"
                    if sess_key in session_seen:
                        continue
                    session_seen.add(sess_key)

                    obs["source_file"] = os.path.basename(filepath)
                    obs["timestamp"] = entry.get("timestamp", "")
                    observations.append(obs)

    except Exception as e:
        print(f"Error scanning {filepath}: {e}", file=sys.stderr)

    return observations


# ─────────────────────────── dedup & record ───────────────────────────

def deduplicate_observations(
    observations: List[Dict], seen_hashes: Set[str]
) -> List[Dict]:
    """Remove observations whose text hash is already in *seen_hashes*."""
    new_obs: List[Dict] = []
    for obs in observations:
        h = text_hash(obs["text"])
        if h not in seen_hashes:
            new_obs.append(obs)
            seen_hashes.add(h)
    return new_obs


def record_observations(
    observations: List[Dict],
    dry_run: bool = False,
    verbose: bool = True,
) -> int:
    """Append observations to observations file and index into RAG."""
    if not observations:
        return 0

    # Lazy import to avoid heavy deps in tests
    from openclaw_mem.index import index_observation

    # Ensure file exists
    os.makedirs(os.path.dirname(OBSERVATIONS_FILE), exist_ok=True)
    if not os.path.exists(OBSERVATIONS_FILE):
        with open(OBSERVATIONS_FILE, "w") as f:
            f.write("# Observations\n\n")

    recorded = 0
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

        entry_line = f"- [{ts_fmt}] **[{tag}]** {text}"

        if not dry_run:
            with open(OBSERVATIONS_FILE, "a") as f:
                f.write(entry_line + "\n")
            try:
                index_observation(text, tag=tag, verbose=False)
            except Exception:
                pass  # don't fail on index errors

        if verbose:
            print(f"  [{tag}] {text[:80]}")

        recorded += 1

    return recorded


# ─────────────────────────── main ───────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Auto-capture observations from session transcripts")
    parser.add_argument("--since", type=str, default="3h",
                        help="Time window (e.g., 3h, 24h, 7d)")
    parser.add_argument("--file", type=str, default=None,
                        help="Scan a specific session file")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be recorded without writing")
    parser.add_argument("--route-to-brain", action="store_true",
                        help="Route observations to project Brain files")
    parser.add_argument("--quiet", "-q", action="store_true",
                        help="Suppress output")

    args = parser.parse_args()
    verbose = not args.quiet

    # Parse time window
    since_hours = 3
    if args.since.endswith("h"):
        since_hours = int(args.since[:-1])
    elif args.since.endswith("d"):
        since_hours = int(args.since[:-1]) * 24

    # Collect session files
    if args.file:
        session_files = [args.file]
    else:
        session_files = get_recent_sessions(since_hours)

    if verbose:
        print(f"Scanning {len(session_files)} session file(s) "
              f"(last {args.since})...")

    # Load state
    state = load_state()
    seen_hashes: Set[str] = set(state.get("seen_hashes", []))

    # Scan
    all_obs: List[Dict] = []
    for fp in session_files:
        all_obs.extend(scan_session_file(fp))

    # Deduplicate against history
    new_obs = deduplicate_observations(all_obs, seen_hashes)

    if verbose:
        print(f"Found {len(all_obs)} total, {len(new_obs)} new")

    if not new_obs:
        if verbose:
            print("No new observations to record.")
        return

    if verbose and args.dry_run:
        print("(dry run) Would record:")
    elif verbose:
        print("Recording:")

    # Route to Brain files if requested
    if args.route_to_brain:
        from openclaw_mem.brain_router import route_observations
        brain_routed, fallback = route_observations(
            new_obs, dry_run=args.dry_run, verbose=verbose
        )
        # Record only unrouted observations to observations.md
        recorded_fallback = record_observations(
            fallback, dry_run=args.dry_run, verbose=verbose
        )
        recorded = len(brain_routed) + recorded_fallback
        if verbose:
            print(f"  Brain: {len(brain_routed)}, "
                  f"Observations: {recorded_fallback}")
    else:
        recorded = record_observations(new_obs, dry_run=args.dry_run,
                                       verbose=verbose)

    # Persist state (unless dry-run)
    if not args.dry_run:
        state["seen_hashes"] = sorted(seen_hashes)
        save_state(state)
        if verbose:
            print(f"Recorded {recorded} observation(s).")


if __name__ == "__main__":
    main()
