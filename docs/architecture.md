# Architecture

## Overview

openclaw-mem is a lightweight RAG (Retrieval-Augmented Generation) memory system designed for AI agents. It provides persistent, searchable memory with minimal token overhead.

## Core Concepts

### 3-Layer Memory Model

```
┌─────────────────────────────────────┐
│           HOT Layer                  │
│  Active files loaded into context    │
│  (core.md, today.md, etc.)          │
│  → Always available, not in RAG     │
├─────────────────────────────────────┤
│           WARM Layer                 │
│  Recent memory files                 │
│  → Indexed in LanceDB, searchable   │
│  → Files in memory/*.md             │
├─────────────────────────────────────┤
│           COLD Layer                 │
│  Archived old files                  │
│  → Still in LanceDB index           │
│  → Files in memory/archive/*.md     │
│  → Auto-archived after N days       │
└─────────────────────────────────────┘
```

### Progressive Disclosure Search

Traditional RAG dumps full chunks into context, wasting tokens. Progressive Disclosure uses a 2-step approach:

1. **Index step** (`--index`): Returns only summaries (id + source + first line + score). Agent can scan many results cheaply.
2. **Detail step** (`--detail <id>`): Returns full content for a specific chunk. Agent only retrieves what it actually needs.

This typically saves 60-80% of tokens compared to traditional full-content search.

### Auto-Capture

Instead of requiring explicit observation logging, auto-capture scans session transcripts (JSONL format) and extracts observations using regex patterns:

- **No LLM required** — pure rule-based extraction
- **Bilingual patterns** — Korean and English
- **Deduplication** — MD5 hash-based, prevents duplicate entries
- **Configurable time window** — scan last N hours/days

### Observation System

Structured observations with tags for categorization:

- `learning` — Things learned during sessions
- `decision` — Decisions made (with rationale)
- `error` — Errors encountered (for future avoidance)
- `insight` — TODOs, future plans, general insights

Observations are:
1. Appended to a markdown file (human-readable)
2. Immediately indexed in LanceDB (machine-searchable)

## Data Flow

```
Session Transcripts ──→ auto-capture ──→ observations.md
                                              │
Markdown Files ────→ index (chunker) ──→ LanceDB ←─ search
                                              │
                         archive ──→ memory/archive/
```

## Technology Stack

- **Vector DB**: LanceDB (embedded, zero-config)
- **Embeddings**: sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2)
- **Chunking**: Markdown-aware (headers → paragraphs → character splits)
- **Storage**: Local filesystem + LanceDB files
