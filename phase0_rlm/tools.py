"""Utility tools for Phase 0 retrieval."""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Dict, List, Optional

from . import bm25_index, config, trace


def _load_chunks(chunks_path: Path | None = None) -> List[Dict]:
    chunks_path = chunks_path or config.CHUNKS_PATH
    chunks: List[Dict] = []
    if not chunks_path.exists():
        return chunks
    with chunks_path.open("r", encoding="utf-8") as file_obj:
        for line in file_obj:
            line = line.strip()
            if not line:
                continue
            chunks.append(json.loads(line))
    return chunks


def list_docs() -> List[Dict]:
    """List document metadata stored in the corpus."""
    docs: List[Dict] = []
    if not config.CORPUS_DIR.exists():
        return docs
    for meta_path in config.CORPUS_DIR.glob("*.json"):
        with meta_path.open("r", encoding="utf-8") as file_obj:
            docs.append(json.load(file_obj))
    return docs


def open_chunk(doc_id: str, chunk_id: int) -> Optional[Dict]:
    """Open a chunk by identifier."""
    for chunk in _load_chunks():
        if chunk.get("doc_id") == doc_id and chunk.get("chunk_id") == chunk_id:
            return chunk
    return None


def _filter_chunks(chunks: List[Dict], filters: Optional[Dict]) -> List[Dict]:
    if not filters:
        return chunks
    filtered: List[Dict] = []
    for chunk in chunks:
        metadata = chunk.get("metadata", {})
        if all(metadata.get(key) == value for key, value in filters.items()):
            filtered.append(chunk)
    return filtered


def _score_query(query: str, index: Dict) -> List[float]:
    tokens = bm25_index.TOKEN_PATTERN.findall(query.lower())
    if not tokens:
        return [0.0 for _ in index.get("chunks", [])]

    idf = index.get("idf", {})
    term_freqs = index.get("term_freqs", [])
    doc_len = index.get("doc_len", [])
    avgdl = index.get("avgdl", 0.0)
    k1 = index.get("k1", 1.5)
    b = index.get("b", 0.75)

    scores: List[float] = []
    for idx, freqs in enumerate(term_freqs):
        score = 0.0
        length = doc_len[idx] if idx < len(doc_len) else 0
        for token in tokens:
            if token not in freqs:
                continue
            term_idf = idf.get(token, 0.0)
            freq = freqs[token]
            denom = freq + k1 * (1 - b + b * (length / (avgdl or 1.0)))
            score += term_idf * (freq * (k1 + 1)) / (denom or 1.0)
        scores.append(score)
    return scores


def search(query: str, k: int | None = None, filters: Optional[Dict] = None, ticker: str | None = None) -> List[Dict]:
    """Search chunks using BM25 and return top passages."""
    k = k or config.DEFAULT_K
    index = bm25_index.load_bm25_index()
    if not index:
        return []

    chunks = index.get("chunks", [])
    scores = _score_query(query, index)

    scored_chunks = [
        {**chunk, "score": score}
        for chunk, score in zip(chunks, scores)
        if score > 0
    ]

    filtered = _filter_chunks(scored_chunks, filters)
    filtered.sort(key=lambda item: item.get("score", 0.0), reverse=True)
    results = filtered[:k]

    if ticker:
        trace.log_retrieval(
            ticker=ticker,
            query=query,
            results=[
                {
                    "doc_id": item.get("doc_id"),
                    "chunk_id": item.get("chunk_id"),
                    "score": item.get("score"),
                }
                for item in results
            ],
        )

    return results


def cite(passages: List[Dict], ticker: str | None = None) -> str:
    """Format citations for a set of passages."""
    citations: List[Dict] = []
    lines: List[str] = []
    for passage in passages:
        doc_id = passage.get("doc_id")
        chunk_id = passage.get("chunk_id")
        metadata = passage.get("metadata", {})
        source = metadata.get("file_name") or metadata.get("source_path", "unknown")
        location = f"{doc_id}:{chunk_id}"
        span = f"chars {passage.get('start')}–{passage.get('end')}"
        lines.append(f"- [{location}] {source} ({span})")
        citations.append(
            {
                "doc_id": doc_id,
                "chunk_id": chunk_id,
                "source": source,
                "start": passage.get("start"),
                "end": passage.get("end"),
            }
        )

    if ticker:
        trace.log_retrieval(
            ticker=ticker,
            query="citation",
            results=[],
            citations=citations,
        )

    return "\n".join(lines)
