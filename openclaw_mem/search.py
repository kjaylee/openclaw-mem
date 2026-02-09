#!/usr/bin/env python3
"""Semantic search over memory using LanceDB RAG.

Supports:
  - Standard search (default, backward compatible)
  - Progressive Disclosure: --index (summaries) then --detail <chunk_id>
  - Tag filtering: --tag <tag> for observation entries
"""
import argparse
import json
import os
import sys
import warnings
warnings.filterwarnings("ignore")

from openclaw_mem.config import (
    LANCE_DB_PATH, TABLE_NAME,
    DEFAULT_TOP_K, DEFAULT_MIN_SCORE
)
from openclaw_mem.embedder import get_embedder


def _get_table():
    """Open the LanceDB table, return None if missing."""
    import lancedb
    db = lancedb.connect(LANCE_DB_PATH)
    if TABLE_NAME not in db.table_names():
        return None
    return db.open_table(TABLE_NAME)


def search(query: str, top_k: int = DEFAULT_TOP_K, source_filter: str = None,
           min_score: float = DEFAULT_MIN_SCORE, tag_filter: str = None) -> list:
    """Search the vector DB. Returns list of result dicts."""
    table = _get_table()
    if table is None:
        return []

    # Encode query
    embedder = get_embedder()
    query_vector = embedder.embed_single(query)

    # Search with cosine metric
    builder = table.search(query_vector).metric("cosine").limit(top_k)

    if source_filter:
        builder = builder.where(f"source LIKE '%{source_filter}%'")

    if tag_filter:
        builder = builder.where(f"tag = '{tag_filter}'")

    results_df = builder.to_pandas()

    output = []
    for _, row in results_df.iterrows():
        distance = row.get("_distance", 0)
        score = round(1.0 - distance, 4)

        if score < min_score:
            continue

        output.append({
            "id": row.get("id", ""),
            "source": row.get("source", ""),
            "content": row.get("text", ""),
            "score": score,
            "metadata": {
                "filename": row.get("filename", ""),
                "chunk_index": int(row.get("chunk_index", 0)),
                "date": row.get("date", ""),
                "tag": row.get("tag", ""),
            }
        })

    return output


def search_index(query: str, top_k: int = DEFAULT_TOP_K,
                 source_filter: str = None, min_score: float = DEFAULT_MIN_SCORE,
                 tag_filter: str = None) -> list:
    """Progressive Disclosure step 1: return summaries (id + source + first line).

    Much cheaper on tokens than full content.
    """
    results = search(query, top_k, source_filter, min_score, tag_filter)
    summaries = []
    for r in results:
        first_line = r["content"].split("\n", 1)[0][:120]
        summaries.append({
            "id": r["id"],
            "source": r["source"],
            "score": r["score"],
            "summary": first_line,
            "tag": r["metadata"].get("tag", ""),
        })
    return summaries


def get_detail(chunk_id: str) -> dict | None:
    """Progressive Disclosure step 2: return full content for a specific chunk id."""
    table = _get_table()
    if table is None:
        return None

    try:
        # Use exact match on the id column
        results = table.search().where(f"id = '{chunk_id}'").limit(1).to_pandas()
        if results.empty:
            return None
        row = results.iloc[0]
        return {
            "id": row.get("id", ""),
            "source": row.get("source", ""),
            "content": row.get("text", ""),
            "metadata": {
                "filename": row.get("filename", ""),
                "chunk_index": int(row.get("chunk_index", 0)),
                "date": row.get("date", ""),
                "tag": row.get("tag", ""),
            }
        }
    except Exception:
        return None


def format_raw(results: list) -> str:
    """Format results as human-readable text."""
    if not results:
        return "No results found."

    lines = []
    for i, r in enumerate(results, 1):
        lines.append(f"--- Result {i} (score: {r['score']}) ---")
        lines.append(f"Source: {r['source']}")
        lines.append(r.get('content', r.get('summary', '')))
        lines.append("")

    return "\n".join(lines)


def format_index_raw(summaries: list) -> str:
    """Format index summaries as human-readable text."""
    if not summaries:
        return "No results found."

    lines = []
    for i, s in enumerate(summaries, 1):
        tag_str = f" [{s['tag']}]" if s.get('tag') else ""
        lines.append(f"{i}. [{s['score']}] {s['source']}{tag_str}")
        lines.append(f"   id: {s['id']}")
        lines.append(f"   {s['summary']}")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Search memory with RAG")
    parser.add_argument("query", nargs="?", help="Search query")
    parser.add_argument("--top-k", "-k", type=int, default=DEFAULT_TOP_K,
                        help=f"Number of results (default: {DEFAULT_TOP_K})")
    parser.add_argument("--source", "-s", type=str, default=None,
                        help="Filter by source (e.g., 'memory')")
    parser.add_argument("--min-score", type=float, default=DEFAULT_MIN_SCORE,
                        help=f"Minimum similarity score (default: {DEFAULT_MIN_SCORE})")
    parser.add_argument("--raw", "-r", action="store_true",
                        help="Human-readable output instead of JSON")

    # Progressive Disclosure
    parser.add_argument("--index", action="store_true",
                        help="Return summaries only (step 1 of progressive disclosure)")
    parser.add_argument("--detail", type=str, default=None,
                        help="Return full content for a specific chunk id (step 2)")

    # Tag filtering
    parser.add_argument("--tag", "-t", type=str, default=None,
                        help="Filter by observation tag (learning|decision|error|insight)")

    args = parser.parse_args()

    # Detail mode: no query needed
    if args.detail:
        result = get_detail(args.detail)
        if result is None:
            print("Chunk not found.", file=sys.stderr)
            sys.exit(1)
        if args.raw:
            print(f"Source: {result['source']}")
            print(f"ID: {result['id']}")
            tag = result['metadata'].get('tag', '')
            if tag:
                print(f"Tag: {tag}")
            print()
            print(result['content'])
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    # Query is required for search/index modes
    if not args.query:
        parser.error("query is required (unless using --detail)")

    if args.index:
        # Progressive Disclosure step 1: summaries
        summaries = search_index(
            query=args.query,
            top_k=args.top_k,
            source_filter=args.source,
            min_score=args.min_score,
            tag_filter=args.tag,
        )
        if args.raw:
            print(format_index_raw(summaries))
        else:
            print(json.dumps(summaries, ensure_ascii=False, indent=2))
    else:
        # Standard full search (backward compatible)
        results = search(
            query=args.query,
            top_k=args.top_k,
            source_filter=args.source,
            min_score=args.min_score,
            tag_filter=args.tag,
        )
        if args.raw:
            print(format_raw(results))
        else:
            print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
