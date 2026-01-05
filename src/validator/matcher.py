# src/validator/matcher.py

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
    """

    # ---------------------------------------------------------
    def __init__(self, title_threshold: float = 0.85) -> None:
        self.__threshold: float = self._validate_threshold(
            title_threshold
        )

    # ---------------------------------------------------------
    # Encapsulation: threshold
    # ---------------------------------------------------------
    @property
    def threshold(self) -> float:
        """Return title similarity threshold."""
        return self.__threshold

    @threshold.setter
    def threshold(self, value: float) -> None:
        """Set title similarity threshold (0.0–1.0)."""
        self.__threshold = self._validate_threshold(value)

    # ---------------------------------------------------------
    # Validation helpers
    # ---------------------------------------------------------
    def _validate_threshold(self, value: float) -> float:
        if not isinstance(value, (float, int)):
            raise TypeError(
                "title_threshold must be a float between 0 and 1"
            )
        if not 0.0 <= float(value) <= 1.0:
            raise ValueError(
                f"Threshold must be between 0 and 1, got {value}"
            )
        return float(value)

    # ---------------------------------------------------------
    # Text normalization & similarity
    # ---------------------------------------------------------
    def _normalize(self, text: str) -> str:
        """Lowercase, remove punctuation, collapse whitespace."""
        cleaned = text.lower()
        cleaned = re.sub(r"\s+", " ", cleaned)
        cleaned = re.sub(r"[^\w\s]", "", cleaned)
        return cleaned.strip()

    def _similarity(self, a: str, b: str) -> float:
        """Return normalized similarity between two titles."""
        a_norm = self._normalize(a)
        b_norm = self._normalize(b)
        return SequenceMatcher(None, a_norm, b_norm).ratio()

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
        chunk_map = {c.get("section_id"): c for c in chunks}

        matched: List[Dict[str, Any]] = []
        missing: List[Dict[str, Any]] = []
        title_miss: List[Dict[str, Any]] = []
        page_err: List[Dict[str, Any]] = []

        for entry in toc:
            sid = entry.get("section_id")

            # Missing section
            if sid not in chunk_map:
                missing.append(entry)
                continue

            chunk = chunk_map[sid]

            # -------- Title similarity --------
            toc_title = entry.get("title", "")
            chunk_title = chunk.get("title", "")
            sim = self._similarity(toc_title, chunk_title)

            if sim < self.__threshold:
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

            matched.append(entry)

        return {
            "matched": matched,
            "missing": missing,
            "title_mismatches": title_miss,
            "page_discrepancies": page_err,
            "total_toc": len(toc),
        }
