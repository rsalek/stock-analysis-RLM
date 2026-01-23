"""Chunk documents into stable chunk identifiers."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, List

from . import config


def _iter_corpus_texts() -> Iterable[tuple[str, str, Dict]]:
    for text_path in config.CORPUS_DIR.glob("*.txt"):
        doc_id = text_path.stem
        meta_path = config.CORPUS_DIR / f"{doc_id}.json"
        metadata = {}
        if meta_path.exists():
            with meta_path.open("r", encoding="utf-8") as file_obj:
                metadata = json.load(file_obj)
        text = text_path.read_text(encoding="utf-8")
        yield doc_id, text, metadata


def chunk_documents(
    chunk_size: int | None = None,
    overlap: int | None = None,
    output_path: Path | None = None,
) -> List[Dict]:
    """Chunk stored documents and persist to the index folder."""
    chunk_size = chunk_size or config.CHUNK_SIZE
    overlap = overlap or config.CHUNK_OVERLAP
    output_path = output_path or config.CHUNKS_PATH

    config.INDEX_DIR.mkdir(parents=True, exist_ok=True)

    chunks: List[Dict] = []
    with output_path.open("w", encoding="utf-8") as file_obj:
        for doc_id, text, metadata in _iter_corpus_texts():
            if not text:
                continue
            start = 0
            chunk_id = 0
            text_length = len(text)
            while start < text_length:
                end = min(start + chunk_size, text_length)
                chunk_text = text[start:end]
                chunk_record = {
                    "doc_id": doc_id,
                    "chunk_id": chunk_id,
                    "start": start,
                    "end": end,
                    "text": chunk_text,
                    "metadata": metadata,
                }
                file_obj.write(json.dumps(chunk_record) + "\n")
                chunks.append(chunk_record)
                chunk_id += 1
                if end == text_length:
                    break
                start = max(0, end - overlap)
    return chunks
