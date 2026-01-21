"""BM25 indexing over Phase 0 chunks."""
from __future__ import annotations

import json
import math
import pickle
import re
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List

from . import config

TOKEN_PATTERN = re.compile(r"\b\w+\b", re.UNICODE)


def _tokenise(text: str) -> List[str]:
    return [token.lower() for token in TOKEN_PATTERN.findall(text)]


def _load_chunks(chunks_path: Path) -> List[Dict]:
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


def build_bm25_index(
    chunks_path: Path | None = None,
    output_path: Path | None = None,
    k1: float = 1.5,
    b: float = 0.75,
) -> Dict:
    """Build and persist a BM25 index."""
    chunks_path = chunks_path or config.CHUNKS_PATH
    output_path = output_path or config.BM25_PATH

    chunks = _load_chunks(chunks_path)
    if not chunks:
        return {}

    term_freqs: List[Counter] = []
    doc_freq: Counter = Counter()
    doc_len: List[int] = []

    for chunk in chunks:
        tokens = _tokenise(chunk.get("text", ""))
        counts = Counter(tokens)
        term_freqs.append(counts)
        doc_len.append(len(tokens))
        for token in counts.keys():
            doc_freq[token] += 1

    avgdl = sum(doc_len) / len(doc_len) if doc_len else 0.0

    idf: Dict[str, float] = {}
    total_docs = len(chunks)
    for term, freq in doc_freq.items():
        idf[term] = math.log(1 + (total_docs - freq + 0.5) / (freq + 0.5))

    index = {
        "chunks": chunks,
        "term_freqs": term_freqs,
        "doc_freq": dict(doc_freq),
        "idf": idf,
        "doc_len": doc_len,
        "avgdl": avgdl,
        "k1": k1,
        "b": b,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as file_obj:
        pickle.dump(index, file_obj)

    return index


def load_bm25_index(path: Path | None = None) -> Dict:
    path = path or config.BM25_PATH
    if not path.exists():
        return {}
    with path.open("rb") as file_obj:
        return pickle.load(file_obj)
