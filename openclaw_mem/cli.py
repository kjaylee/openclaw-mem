#!/usr/bin/env python3
"""CLI entry point for openclaw-mem.

Usage:
    openclaw-mem search "query" [--index] [--detail ID] [--tag TAG]
    openclaw-mem index [FILE] [--all] [--changed]
    openclaw-mem observe "text" [--tag TAG]
    openclaw-mem archive [--execute] [--reindex]
    openclaw-mem auto-capture [--since 3h] [--dry-run]
"""
import sys


def main():
    """Main CLI dispatcher."""
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    command = sys.argv[1]

    # Remove the subcommand from argv so argparse in each module works
    sys.argv = [f"openclaw-mem {command}"] + sys.argv[2:]

    if command == "search":
        from openclaw_mem.search import main as search_main
        search_main()
    elif command == "index":
        from openclaw_mem.index import main as index_main
        index_main()
    elif command == "observe":
        from openclaw_mem.observe import main as observe_main
        observe_main()
    elif command == "archive":
        from openclaw_mem.archive import main as archive_main
        archive_main()
    elif command in ("auto-capture", "capture"):
        from openclaw_mem.auto_capture import main as capture_main
        capture_main()
    elif command == "version":
        from openclaw_mem import __version__
        print(f"openclaw-mem {__version__}")
    elif command in ("help", "--help", "-h"):
        print_usage()
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        print_usage()
        sys.exit(1)


def print_usage():
    """Print CLI usage information."""
    print("""openclaw-mem — Lightweight RAG memory for AI agents

Commands:
  search        Semantic search over memory (Progressive Disclosure)
  index         Index markdown files into LanceDB
  observe       Record a structured observation
  archive       Archive old memory files (3-Layer: Hot/Warm/Cold)
  auto-capture  Extract observations from session transcripts
  version       Show version

Examples:
  openclaw-mem search "deployment process" --top-k 5
  openclaw-mem search "deployment" --index          # Step 1: summaries
  openclaw-mem search --detail "chunk:0:abc123"     # Step 2: full content
  openclaw-mem index --changed
  openclaw-mem index path/to/file.md
  openclaw-mem observe "Redis cache works well" --tag learning
  openclaw-mem archive --execute
  openclaw-mem auto-capture --since 6h

Environment Variables:
  OPENCLAW_MEM_ROOT             Workspace root directory
  OPENCLAW_MEM_DB_PATH          LanceDB database path
  OPENCLAW_MEM_TABLE            LanceDB table name
  OPENCLAW_MEM_BACKEND          Embedding backend: local (default), openai, ollama
  OPENCLAW_MEM_MODEL            Embedding model name (default: all-MiniLM-L6-v2)
  OPENAI_API_KEY                Required only for openai backend
  OLLAMA_BASE_URL               Ollama server URL (default: http://localhost:11434)
  OPENCLAW_MEM_ARCHIVE_DIR      Archive directory path
  OPENCLAW_MEM_ARCHIVE_DAYS     Days before archiving (default: 30)
  OPENCLAW_MEM_OBSERVATIONS_FILE  Observations file path
  OPENCLAW_MEM_SESSION_DIR      Session transcripts directory
""")


if __name__ == "__main__":
    main()
