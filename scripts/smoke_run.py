"""Smoke run for Phase 0 and Phase 1."""
from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

from phase0_rlm import bm25_index, chunking, document_store


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    base_path = repo_root / "smoke_data"
    input_dir = base_path / "Input" / "SMOKE"
    input_dir.mkdir(parents=True, exist_ok=True)

    sample_text = input_dir / "sample.txt"
    sample_text.write_text(
        "Smoke test content for Phase 0 retrieval and Phase 1 prompts.",
        encoding="utf-8",
    )

    os.environ["BASE_DRIVE_PATH"] = base_path.as_posix()
    os.environ["PHASE0_BASE_DRIVE_PATH"] = base_path.as_posix()
    os.environ["PHASE1_SMOKE"] = "1"
    os.environ["PHASE1_TICKER"] = "SMOKE"

    document_store.ingest_drive_paths([input_dir])
    chunking.chunk_documents()
    bm25_index.build_bm25_index()

    phase1_script = repo_root / "phase1" / "Simple Stock Analysis phase1"

    if importlib.util.find_spec("google.colab") is None:
        print("⚠️ google.colab is unavailable. Skipping Phase 1 smoke run.")
        return 0

    subprocess.run([sys.executable, phase1_script.as_posix()], check=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
