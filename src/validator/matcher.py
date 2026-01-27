from __future__ import annotations

import re
from typing import List, Dict, Any
from difflib import SequenceMatcher

from src.core.base_validator import BaseValidator


class SectionMatcher(BaseValidator):
    """
    Matches TOC entries against extracted content chunks.

    Features:
    - Exact section_id matching
    - Fuzzy title similarity check
    - Page-range consistency check (optional)

    Encapsulation:
    - Public API: validate()
    - Domain API: match()
    - ALL internal state uses name-mangled attributes (__attr)
    - Helpers are protected
    """

    # ---------------------------------------------------------
    # Constructor (TRUE PRIVATE STATE)
    # ---------------------------------------------------------
    def __init__(self, title_threshold: float = 0.85) -> None:
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
        return self.__threshold

    @threshold.setter
    def threshold(self, value: float) -> None:
        self.__threshold = self._validate_threshold(value)

    # ---------------------------------------------------------
    # Read-only statistics
    # ---------------------------------------------------------
    @property
    def matched_count(self) -> int:
        return self.__matched_count

    @property
    def missing_count(self) -> int:
        return self.__missing_count

    @property
    def mismatch_count(self) -> int:
        return self.__mismatch_count

    # ---------------------------------------------------------
    # BaseValidator contract
    # ---------------------------------------------------------
    def validate(
        self,
        toc: List[Dict[str, Any]],
        chunks: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        return self.match(toc, chunks)

    # ---------------------------------------------------------
    # Domain API (SHORT & READABLE)
    # ---------------------------------------------------------
    def match(
        self,
        toc: List[Dict[str, Any]],
        chunks: List[Dict[str, Any]],
    ) -> Dict[str, Any]:

        self._reset_counters()

        chunk_map = self._index_chunks(chunks)
        results = self._init_results()

        for entry in toc:
            self._process_entry(
                entry=entry,
                chunk_map=chunk_map,
                results=results,
            )

        return self._build_report(results, toc)

    # ---------------------------------------------------------
    # Pipeline helpers
    # ---------------------------------------------------------
    def _reset_counters(self) -> None:
        self.__matched_count = 0
        self.__missing_count = 0
        self.__mismatch_count = 0

    @staticmethod
    def _index_chunks(
        chunks: List[Dict[str, Any]],
    ) -> Dict[str, Dict[str, Any]]:
        return {
            c.get("section_id"): c
            for c in chunks
            if c.get("section_id")
        }

    @staticmethod
    def _init_results() -> Dict[str, List[Dict[str, Any]]]:
        return {
            "matched": [],
            "missing": [],
            "title_mismatches": [],
            "page_discrepancies": [],
        }

    def _process_entry(
        self,
        entry: Dict[str, Any],
        chunk_map: Dict[str, Dict[str, Any]],
        results: Dict[str, List[Dict[str, Any]]],
    ) -> None:
        sid = entry.get("section_id")

        if sid not in chunk_map:
            self.__missing_count += 1
            results["missing"].append(entry)
            return

        chunk = chunk_map[sid]
        self.__matched_count += 1
        results["matched"].append(entry)

        self._check_title_similarity(entry, chunk, results)
        self._check_page_range(entry, chunk, results)

    # ---------------------------------------------------------
    # Validation checks
    # ---------------------------------------------------------
    def _check_title_similarity(
        self,
        entry: Dict[str, Any],
        chunk: Dict[str, Any],
        results: Dict[str, List[Dict[str, Any]]],
    ) -> None:
        toc_title = entry.get("title", "")
        chunk_title = chunk.get("title", "")
        sim = self._similarity(toc_title, chunk_title)

        if sim < self.__threshold:
            self.__mismatch_count += 1
            results["title_mismatches"].append(
                {
                    "section_id": entry.get("section_id"),
                    "toc_title": toc_title,
                    "chunk_title": chunk_title,
                    "similarity": sim,
                }
            )

    @staticmethod
    def _check_page_range(
        entry: Dict[str, Any],
        chunk: Dict[str, Any],
        results: Dict[str, List[Dict[str, Any]]],
    ) -> None:
        pr = chunk.get("page_range")
        if not pr:
            return

        start, end = pr
        toc_page = entry.get("page", 0)

        if toc_page < start or toc_page > end:
            results["page_discrepancies"].append(
                {
                    "section_id": entry.get("section_id"),
                    "toc_page": toc_page,
                    "chunk_range": pr,
                }
            )

    # ---------------------------------------------------------
    # Report builder
    # ---------------------------------------------------------
    @staticmethod
    def _build_report(
        results: Dict[str, List[Dict[str, Any]]],
        toc: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        return {
            **results,
            "total_toc": len(toc),
        }

    # ---------------------------------------------------------
    # Validation helpers
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
    # Text normalization & similarity
    # ---------------------------------------------------------
    @staticmethod
    def _normalize(text: str) -> str:
        cleaned = text.lower()
        cleaned = re.sub(r"\s+", " ", cleaned)
        cleaned = re.sub(r"[^\w\s]", "", cleaned)
        return cleaned.strip()

    def _similarity(self, a: str, b: str) -> float:
        return SequenceMatcher(
            None,
            self._normalize(a),
            self._normalize(b),
        ).ratio()

    # ---------------------------------------------------------
    # Polymorphism
    # ---------------------------------------------------------
    def __str__(self) -> str:
        return (
            f"SectionMatcher("
            f"threshold={self.__threshold}, "
            f"matched={self.__matched_count}, "
            f"missing={self.__missing_count})"
        )

    def __repr__(self) -> str:
        return f"SectionMatcher(threshold={self.__threshold})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SectionMatcher):
            return NotImplemented
        return self.__threshold == other.__threshold

    def __hash__(self) -> int:
        return hash((self.__class__, self.__threshold))

    def __bool__(self) -> bool:
        return 0.0 <= self.__threshold <= 1.0

    def __len__(self) -> int:
        return self.__matched_count

    def __enter__(self) -> "SectionMatcher":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        return False
