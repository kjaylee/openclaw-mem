# openclaw-mem

**Lightweight RAG memory system for AI agents** — Progressive Disclosure, Auto-Capture, 3-Layer Archive.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

## Features

- **Progressive Disclosure** — 2-step search: summaries first (`--index`), then full content on demand (`--detail`). Saves tokens for LLM agents.
- **Auto-Capture** — Rule-based extraction of decisions, learnings, errors, and insights from session transcripts. No LLM required.
- **3-Layer Archive** — Hot (active files), Warm (indexed in RAG), Cold (archived but still searchable).
- **Observation Logging** — Structured `[tag]` observations with instant indexing.
- **Pluggable Embeddings** — Local sentence-transformers (default, no API key), OpenAI, or Ollama backends.
- **Multilingual** — Swap in multilingual models for Korean + English support.
- **Zero Config** — Works out of the box with `pip install` and no API keys. Everything is overridable via environment variables.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   openclaw-mem                       │
│                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │  search   │  │  index   │  │  auto-capture    │  │
│  │(2-step)   │  │(incr.)   │  │(rule-based)      │  │
│  └─────┬─────┘  └─────┬────┘  └────────┬─────────┘  │
│        │              │                │             │
│        ▼              ▼                ▼             │
│  ┌─────────────────────────────────────────────┐    │
│  │              LanceDB + Embeddings            │    │
│  │   local (default) │ openai │ ollama          │    │
│  └─────────────────────────────────────────────┘    │
│                                                     │
│  Memory Layers:                                     │
│  ┌────────┐  ┌────────┐  ┌────────┐                │
│  │  HOT   │  │  WARM  │  │  COLD  │                │
│  │(active)│→ │(indexed)│→ │(archive│                │
│  │        │  │  in RAG │  │ in RAG)│                │
│  └────────┘  └────────┘  └────────┘                │
└─────────────────────────────────────────────────────┘
```

## Installation

```bash
# Default: local embeddings (no API key needed)
pip install openclaw-mem

# With OpenAI backend support
pip install openclaw-mem[openai]

# With Ollama backend support
pip install openclaw-mem[ollama]

# Everything
pip install openclaw-mem[all]
```

### From source

```bash
git clone https://github.com/kjaylee/openclaw-mem.git
cd openclaw-mem
pip install -e ".[dev]"
```

## Quick Start

### 1. Index your markdown files

```bash
# Set your workspace root (where memory/ directory lives)
export OPENCLAW_MEM_ROOT=/path/to/workspace

# Index all configured files
openclaw-mem index --all

# Or index only changed files (incremental)
openclaw-mem index --changed

# Or index a specific file
openclaw-mem index path/to/notes.md
```

### 2. Search with Progressive Disclosure

```bash
# Step 1: Get summaries (cheap on tokens)
openclaw-mem search "deployment process" --index

# Output:
# 1. [0.8432] memory/2025-01-15.md
#    id: 2025-01-15.md:3:a1b2c3d4
#    Deployed the new API to production...

# Step 2: Get full content for interesting chunks
openclaw-mem search --detail "2025-01-15.md:3:a1b2c3d4"
```

### 3. Record observations

```bash
openclaw-mem observe "Redis cache reduced latency by 40%" --tag learning
openclaw-mem observe "Switched to Rust for WASM builds" --tag decision
openclaw-mem observe "OOM on 2GB instances with batch size > 100" --tag error
```

### 4. Auto-capture from sessions

```bash
# Scan recent session transcripts for observations
openclaw-mem auto-capture --since 6h

# Dry run — see what would be captured
openclaw-mem auto-capture --dry-run
```

### 5. Archive old files

```bash
# See what would be archived (dry run)
openclaw-mem archive

# Actually archive files older than 30 days
openclaw-mem archive --execute

# Re-index archive for search
openclaw-mem archive --reindex
```

## Configuration

All settings can be overridden via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENCLAW_MEM_ROOT` | Package parent dir | Workspace root directory |
| `OPENCLAW_MEM_DB_PATH` | `$ROOT/lance_db` | LanceDB database path |
| `OPENCLAW_MEM_TABLE` | `openclaw_memory` | LanceDB table name |
| `OPENCLAW_MEM_BACKEND` | `local` | Embedding backend: `local`, `openai`, `ollama` |
| `OPENCLAW_MEM_MODEL` | `intfloat/multilingual-e5-small` | Model name (per backend) |
| `OPENAI_API_KEY` | *(empty)* | Required only for `openai` backend |
| `OPENAI_BASE_URL` | *(empty)* | Custom OpenAI-compatible endpoint |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OPENCLAW_MEM_CHUNK_SIZE` | `500` | Max chunk size (characters) |
| `OPENCLAW_MEM_CHUNK_OVERLAP` | `50` | Chunk overlap (characters) |
| `OPENCLAW_MEM_ARCHIVE_DIR` | `$ROOT/memory/archive` | Archive directory |
| `OPENCLAW_MEM_ARCHIVE_DAYS` | `30` | Days before archiving |
| `OPENCLAW_MEM_OBSERVATIONS_FILE` | `$ROOT/memory/observations.md` | Observations file |
| `OPENCLAW_MEM_SESSION_DIR` | `~/.openclaw/agents/main/sessions` | Session transcripts dir |

### Embedding Backends

```bash
# Default: local sentence-transformers (no API key, ~470MB model download)
export OPENCLAW_MEM_BACKEND=local
export OPENCLAW_MEM_MODEL=intfloat/multilingual-e5-small  # default, Korean+English

# English-only lightweight alternative
export OPENCLAW_MEM_MODEL=all-MiniLM-L6-v2

# OpenAI API
export OPENCLAW_MEM_BACKEND=openai
export OPENCLAW_MEM_MODEL=text-embedding-3-small
export OPENAI_API_KEY=sk-...

# Ollama (local server)
export OPENCLAW_MEM_BACKEND=ollama
export OPENCLAW_MEM_MODEL=nomic-embed-text
```

## Python API

```python
from openclaw_mem.search import search, search_index, get_detail
from openclaw_mem.index import index_single, index_observation
from openclaw_mem.observe import append_observation
from openclaw_mem.auto_capture import extract_observations_from_text
from openclaw_mem.embedder import get_embedder, Embedder

# Search
results = search("deployment", top_k=5)
summaries = search_index("deployment", top_k=10)
detail = get_detail("chunk:0:abc123")

# Index
index_single("path/to/file.md")
index_observation("Important finding", tag="learning")

# Observe
append_observation("Cache works great", tag="learning")

# Extract patterns from text
obs = extract_observations_from_text("결정: Redis를 사용한다")
# [{"tag": "decision", "text": "Redis를 사용한다"}]

# Direct embedding access
embedder = get_embedder()  # uses configured backend
vectors = embedder.embed(["text 1", "text 2"])

# Custom backend
embedder = Embedder(backend="openai", model="text-embedding-3-small")
```

## Observation Tags

| Tag | Description | Example patterns |
|-----|-------------|-----------------|
| `decision` | Decisions made | `결정:`, `Decision:`, `→ 채택` |
| `learning` | Things learned | `배움:`, `Learned:`, `발견:`, `✅` |
| `error` | Errors encountered | `에러:`, `Error:`, `FAIL`, `실패` |
| `insight` | TODOs and insights | `TODO:`, `할일:`, `다음에` |

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=openclaw_mem
```

## License

MIT — see [LICENSE](LICENSE) for details.
