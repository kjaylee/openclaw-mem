# Quick Start Guide

## Installation

```bash
pip install openclaw-mem
```

## Setup

1. Create a workspace directory with a `memory/` folder:

```bash
mkdir -p ~/my-agent/memory
export OPENCLAW_MEM_ROOT=~/my-agent
```

2. Create some memory files:

```bash
echo "# 2025-01-15\n\nDeployed new API. Used Redis for caching." > ~/my-agent/memory/2025-01-15.md
echo "# 2025-01-16\n\nFixed timeout bug in worker process." > ~/my-agent/memory/2025-01-16.md
```

3. Index your files:

```bash
openclaw-mem index --all
```

## Basic Usage

### Search

```bash
# Full search
openclaw-mem search "deployment"

# Progressive disclosure (token-efficient)
openclaw-mem search "deployment" --index        # Step 1: summaries
openclaw-mem search --detail "CHUNK_ID"         # Step 2: full content

# Filter by source
openclaw-mem search "bug" --source memory

# Human-readable output
openclaw-mem search "deployment" --raw
```

### Record Observations

```bash
openclaw-mem observe "Redis reduces p99 latency by 40ms" --tag learning
openclaw-mem observe "Use connection pooling for DB" --tag decision
```

### Archive Management

```bash
# Preview what would be archived
openclaw-mem archive

# Execute archive (moves files older than 30 days)
openclaw-mem archive --execute

# Files remain searchable after archiving
openclaw-mem search "old topic" --top-k 3
```

## Integration with AI Agents

### In an agent's tool definition:

```python
from openclaw_mem.search import search_index, get_detail

# Step 1: Agent gets summaries
summaries = search_index("relevant topic", top_k=10)
# → [{id, source, score, summary}, ...]

# Step 2: Agent picks interesting results
for s in summaries:
    if s["score"] > 0.7:
        detail = get_detail(s["id"])
        # Use detail["content"] in context
```

### Auto-capture from sessions:

```python
from openclaw_mem.auto_capture import extract_observations_from_text

text = "결정: Rust+WASM으로 빌드 파이프라인 통일"
obs = extract_observations_from_text(text)
# [{"tag": "decision", "text": "Rust+WASM으로 빌드 파이프라인 통일"}]
```

## Next Steps

- Read [Architecture](architecture.md) for system design details
- Configure environment variables for your setup (see README)
- Set up cron for periodic `openclaw-mem auto-capture` and `openclaw-mem archive`
