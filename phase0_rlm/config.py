"""Phase 0 configuration values."""
import os
from pathlib import Path

BASE_DRIVE_PATH = os.environ.get(
    "PHASE0_BASE_DRIVE_PATH",
    (Path.home() / "drive" / "My Drive" / "Stock_Analysis").as_posix(),
)

BASE_DIR = Path(__file__).resolve().parent

INPUT_DIR = Path(BASE_DRIVE_PATH) / "Input"
RESULTS_BASE_DIR = Path(BASE_DRIVE_PATH) / "Results"

CORPUS_DIR = BASE_DIR / "corpus"
INDEX_DIR = BASE_DIR / "index"

CHUNK_SIZE = 1200
CHUNK_OVERLAP = 200
DEFAULT_K = 12

CHUNKS_PATH = INDEX_DIR / "chunks.jsonl"
BM25_PATH = INDEX_DIR / "bm25.pkl"

TRACE_FILENAME = "phase0_trace.json"
