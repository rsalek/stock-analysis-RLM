"""Trace retrieval events for Phase 0."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional

from . import config


def _trace_path(ticker: str) -> Path:
    return config.RESULTS_BASE_DIR / ticker / config.TRACE_FILENAME


def log_retrieval(
    ticker: str,
    query: str,
    results: List[dict],
    citations: Optional[List[dict]] = None,
) -> None:
    """Log retrieval details to the results folder."""
    trace_path = _trace_path(ticker)
    trace_path.parent.mkdir(parents=True, exist_ok=True)

    payload: dict[str, Any] = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "query": query,
        "results": results,
    }
    if citations is not None:
        payload["citations"] = citations

    existing: List[dict] = []
    if trace_path.exists():
        with trace_path.open("r", encoding="utf-8") as file_obj:
            try:
                existing = json.load(file_obj)
            except json.JSONDecodeError:
                existing = []

    existing.append(payload)
    with trace_path.open("w", encoding="utf-8") as file_obj:
        json.dump(existing, file_obj, indent=2)
