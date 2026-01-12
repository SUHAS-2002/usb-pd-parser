"""
JSONL file utilities for loading and saving structured data.

This module provides reusable functions for JSONL operations,
eliminating code duplication across the codebase.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Iterator


class JSONLHandler:
    """
    Handles JSONL file operations with proper error handling
    and type safety.

    Follows SRP: Single responsibility for JSONL operations.
    """

    @staticmethod
    def load(path: Path) -> List[Dict[str, Any]]:
        """
        Load a JSONL file into a list of dictionaries.
        """
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        items: List[Dict[str, Any]] = []

        with path.open("r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    items.append(json.loads(line))
                except json.JSONDecodeError as e:
                    raise json.JSONDecodeError(
                        f"Invalid JSON on line {line_num}: {e.msg}",
                        e.doc,
                        e.pos,
                    )

        return items

    @staticmethod
    def save(path: Path, items: List[Dict[str, Any]]) -> None:
        """
        Save a list of dictionaries to a JSONL file.
        """
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", encoding="utf-8") as f:
            for obj in items:
                f.write(json.dumps(obj, ensure_ascii=False) + "\n")

    @staticmethod
    def stream(path: Path) -> Iterator[Dict[str, Any]]:
        """
        Stream JSONL file line by line (memory efficient).
        """
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    yield json.loads(line)


# Backward-compatible helpers
def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    return JSONLHandler.load(path)


def save_jsonl(path: Path, items: List[Dict[str, Any]]) -> None:
    JSONLHandler.save(path, items)
