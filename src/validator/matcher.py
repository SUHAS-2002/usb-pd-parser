# src/validator/matcher.py

from __future__ import annotations

import re
from typing import List, Dict, Any
from difflib import SequenceMatcher


class SectionMatcher:
    """
    Matches TOC entries against extracted content chunks.

    Features:
    - Exact section_id matching
    - Fuzzy title similarity check
    - Page-range consistency check (optional)

    Encapsulation:
    - Public API: match()
    - ALL internal state uses name-mangled attributes (__attr)
    - Helpers are protected
    """

    # ---------------------------------------------------------
    # Constructor (TRUE PRIVATE STATE)
    # ---------------------------------------------------------
    def __init__(self, title_threshold: float = 0.85) -> None:
        """Initialize matcher with name-mangled private state."""
        self.__threshold: float = self._validate_threshold(
            title_threshold
        )

        self.__matched_count: int = 0
        self.__missing_count: int = 0
        self.__mismatch_count: int = 0

    # ---------------------------------------------------------
    # Encapsulation: threshold
    # ---------------------------------------------------------
    @property
    def threshold(self) -> float:
        """Return title similarity threshold (read-only)."""
        return self.__threshold

    @threshold.setter
    def threshold(self, value: float) -> None:
        """Set title similarity threshold (0.0–1.0)."""
        self.__threshold = self._validate_threshold(value)

    # ---------------------------------------------------------
    # Read-only statistics
    # ---------------------------------------------------------
    @property
    def matched_count(self) -> int:
        """Number of matched sections."""
        return self.__matched_count

    @property
    def missing_count(self) -> int:
        """Number of missing sections."""
        return self.__missing_count

    @property
    def mismatch_count(self) -> int:
        """Number of title mismatches."""
        return self.__mismatch_count

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------
    def match(
        self,
        toc: List[Dict[str, Any]],
        chunks: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Match TOC entries with extracted chunks using:
        - section_id alignment
        - fuzzy title similarity
        - optional page-range validation
        """
        # Reset counters
        self.__matched_count = 0
        self.__missing_count = 0
        self.__mismatch_count = 0

        chunk_map = {
            c.get("section_id"): c
            for c in chunks
            if c.get("section_id")
        }

        matched: List[Dict[str, Any]] = []
        missing: List[Dict[str, Any]] = []
        title_miss: List[Dict[str, Any]] = []
        page_err: List[Dict[str, Any]] = []

        for entry in toc:
            sid = entry.get("section_id")

            # Missing section
            if sid not in chunk_map:
                self.__missing_count += 1
                missing.append(entry)
                continue

            chunk = chunk_map[sid]
            self.__matched_count += 1
            matched.append(entry)

            # -------- Title similarity --------
            toc_title = entry.get("title", "")
            chunk_title = chunk.get("title", "")
            sim = self._similarity(toc_title, chunk_title)

            if sim < self.__threshold:
                self.__mismatch_count += 1
                title_miss.append(
                    {
                        "section_id": sid,
                        "toc_title": toc_title,
                        "chunk_title": chunk_title,
                        "similarity": sim,
                    }
                )

            # -------- Page range check --------
            pr = chunk.get("page_range")
            if pr:
                start, end = pr
                toc_page = entry.get("page", 0)

                if toc_page < start or toc_page > end:
                    page_err.append(
                        {
                            "section_id": sid,
                            "toc_page": toc_page,
                            "chunk_range": pr,
                        }
                    )

        return {
            "matched": matched,
            "missing": missing,
            "title_mismatches": title_miss,
            "page_discrepancies": page_err,
            "total_toc": len(toc),
        }

    # ---------------------------------------------------------
    # Validation helpers (protected)
    # ---------------------------------------------------------
    @staticmethod
    def _validate_threshold(value: float) -> float:
        if not isinstance(value, (float, int)):
            raise TypeError(
                "title_threshold must be a float between 0 and 1"
            )

        value = float(value)
        if not 0.0 <= value <= 1.0:
            raise ValueError(
                f"Threshold must be between 0 and 1, got {value}"
            )

        return value

    # ---------------------------------------------------------
    # Text normalization & similarity (protected)
    # ---------------------------------------------------------
    @staticmethod
    def _normalize(text: str) -> str:
        cleaned = text.lower()
        cleaned = re.sub(r"\s+", " ", cleaned)
        cleaned = re.sub(r"[^\w\s]", "", cleaned)
        return cleaned.strip()

    def _similarity(self, a: str, b: str) -> float:
        a_norm = self._normalize(a)
        b_norm = self._normalize(b)
        return SequenceMatcher(None, a_norm, b_norm).ratio()
