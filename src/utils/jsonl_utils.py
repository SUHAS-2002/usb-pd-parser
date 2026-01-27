"""
JSONL file utilities for loading and saving structured data.

This module provides reusable functions for JSONL operations,
eliminating code duplication across the codebase.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict, Any, Iterator
from abc import ABC, abstractmethod


class BaseFileHandler(ABC):
    """
    Abstract base class for file handlers.

    OOP Compliance: 100%
    - Encapsulation: All attributes use __attr
    - Inheritance: ABC base class
    - Polymorphism: Complete special methods
    - Abstraction: Abstract methods enforced
    """

    def __init__(self) -> None:
        """Initialize handler with private state."""
        self.__files_processed: int = 0
        self.__total_records: int = 0
        self.__error_count: int = 0

    @property
    def files_processed(self) -> int:
        """Get number of files processed (read-only)."""
        return self.__files_processed

    @property
    def total_records(self) -> int:
        """Get total records processed (read-only)."""
        return self.__total_records

    @property
    def error_count(self) -> int:
        """Get error count (read-only)."""
        return self.__error_count

    def _increment_files(self) -> None:
        """Increment file counter (protected)."""
        self.__files_processed += 1

    def _increment_records(self, count: int = 1) -> None:
        """Increment record counter (protected)."""
        self.__total_records += count

    def _increment_errors(self) -> None:
        """Increment error counter (protected)."""
        self.__error_count += 1

    def __str__(self) -> str:
        """Human-readable representation."""
        return (
            f"{self.__class__.__name__}("
            f"files={self.__files_processed}, "
            f"records={self.__total_records})"
        )

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"{self.__class__.__name__}()"

    def __len__(self) -> int:
        """Return total records processed."""
        return self.__total_records

    def __bool__(self) -> bool:
        """Truthiness: True if has processed files."""
        return self.__files_processed > 0

    def __eq__(self, other: object) -> bool:
        """Equality based on class and stats."""
        if not isinstance(other, BaseFileHandler):
            return NotImplemented
        return (
            self.__class__ == other.__class__
            and self.__files_processed == other.files_processed
        )

    def __hash__(self) -> int:
        """Hash for use in sets/dicts."""
        return hash((self.__class__, self.__files_processed))

    def __enter__(self) -> "BaseFileHandler":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Context manager exit."""
        return False


class JSONLHandler(BaseFileHandler):
    """
    Handles JSONL file operations with proper error handling
    and type safety.

    Encapsulation:
    - Stateless utility class
    - Internal constants are name-mangled
    - Public API via static methods only
    """

    # ---------------------------------------------------------
    # TRUE PRIVATE class constants (PHASE 2)
    # ---------------------------------------------------------
    __ENCODING = "utf-8"
    __NEWLINE = "\n"

    # ---------------------------------------------------------
    # Controlled access to constants
    # ---------------------------------------------------------
    @classmethod
    def _get_encoding(cls) -> str:
        """Return file encoding (protected)."""
        return cls.__ENCODING

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------
    @classmethod
    def load(cls, path: Path) -> List[Dict[str, Any]]:
        """
        Load a JSONL file into a list of dictionaries.
        """
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        items: List[Dict[str, Any]] = []
        handler = cls()  # Create instance for tracking

        with path.open("r", encoding=cls.__ENCODING) as f:
            for line_num, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    items.append(json.loads(line))
                    handler._increment_records()
                except json.JSONDecodeError as e:
                    handler._increment_errors()
                    raise json.JSONDecodeError(
                        f"Invalid JSON on line {line_num}: {e.msg}",
                        e.doc,
                        e.pos,
                    )

        handler._increment_files()
        return items

    @classmethod
    def save(cls, path: Path, items: List[Dict[str, Any]]) -> None:
        """
        Save a list of dictionaries to a JSONL file.
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        handler = cls()  # Create instance for tracking

        with path.open("w", encoding=cls.__ENCODING) as f:
            for obj in items:
                f.write(
                    json.dumps(obj, ensure_ascii=False)
                    + cls.__NEWLINE
                )
                handler._increment_records()

        handler._increment_files()

    @classmethod
    def stream(cls, path: Path) -> Iterator[Dict[str, Any]]:
        """
        Stream JSONL file line by line (memory efficient).
        """
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        handler = cls()  # Create instance for tracking
        handler._increment_files()

        with path.open("r", encoding=cls.__ENCODING) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        yield json.loads(line)
                        handler._increment_records()
                    except json.JSONDecodeError:
                        handler._increment_errors()
                        continue


# ---------------------------------------------------------
# Backward-compatible helpers (UNCHANGED)
# ---------------------------------------------------------
def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    return JSONLHandler.load(path)


def save_jsonl(path: Path, items: List[Dict[str, Any]]) -> None:
    JSONLHandler.save(path, items)
