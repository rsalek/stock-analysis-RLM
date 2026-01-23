"""Document ingestion and normalisation for Phase 0."""
from __future__ import annotations

import hashlib
import json
import os
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable, List

from . import config

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".html", ".htm"}


class _HTMLStripper(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._chunks: List[str] = []

    def handle_data(self, data: str) -> None:
        if data:
            self._chunks.append(data)

    def get_text(self) -> str:
        return " ".join(self._chunks)


def _normalise_text(text: str) -> str:
    """Normalise whitespace for downstream chunking."""
    return " ".join(text.split())


def _read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _read_html_file(path: Path) -> str:
    parser = _HTMLStripper()
    parser.feed(path.read_text(encoding="utf-8", errors="ignore"))
    return parser.get_text()


def _read_pdf_file(path: Path) -> str:
    try:
        import PyPDF2
    except ImportError as exc:
        raise RuntimeError("PyPDF2 is required to read PDF files.") from exc

    text_parts: List[str] = []
    with path.open("rb") as file_obj:
        reader = PyPDF2.PdfReader(file_obj)
        for page in reader.pages:
            extracted = page.extract_text() or ""
            text_parts.append(extracted)
    return "\n".join(text_parts)


def _generate_doc_id(path: Path) -> str:
    hasher = hashlib.sha1()
    hasher.update(str(path).encode("utf-8"))
    return hasher.hexdigest()


def _collect_paths(paths: Iterable[str | Path]) -> List[Path]:
    collected: List[Path] = []
    for input_path in paths:
        path = Path(input_path)
        if path.is_dir():
            for child in path.iterdir():
                if child.suffix.lower() in SUPPORTED_EXTENSIONS:
                    collected.append(child)
        elif path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            collected.append(path)
    return collected


def ingest_drive_paths(paths: Iterable[str | Path]) -> List[dict]:
    """Ingest documents from local or Drive-backed paths."""
    config.CORPUS_DIR.mkdir(parents=True, exist_ok=True)

    docs: List[dict] = []
    for path in _collect_paths(paths):
        suffix = path.suffix.lower()
        if suffix in {".txt", ".md"}:
            raw_text = _read_text_file(path)
        elif suffix in {".html", ".htm"}:
            raw_text = _read_html_file(path)
        elif suffix == ".pdf":
            raw_text = _read_pdf_file(path)
        else:
            continue

        text = _normalise_text(raw_text)
        if not text:
            continue

        doc_id = _generate_doc_id(path)
        metadata = {
            "doc_id": doc_id,
            "source_path": str(path),
            "file_name": path.name,
            "file_type": suffix,
            "size_bytes": path.stat().st_size,
            "modified_time": path.stat().st_mtime,
        }

        text_path = config.CORPUS_DIR / f"{doc_id}.txt"
        meta_path = config.CORPUS_DIR / f"{doc_id}.json"
        text_path.write_text(text, encoding="utf-8")
        meta_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

        docs.append(metadata)

    return docs


def list_corpus_documents() -> List[dict]:
    """List stored corpus metadata records."""
    records: List[dict] = []
    if not config.CORPUS_DIR.exists():
        return records

    for meta_file in config.CORPUS_DIR.glob("*.json"):
        with meta_file.open("r", encoding="utf-8") as file_obj:
            records.append(json.load(file_obj))
    return records
