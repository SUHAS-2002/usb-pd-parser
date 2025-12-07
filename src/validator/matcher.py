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

    def __init__(self, title_threshold: float = 0.85) -> None:
        self._threshold = title_threshold

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

    def match(
        self,
        toc: List[Dict[str, Any]],
        chunks: List[Dict[str, Any]]
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

            # -------------- Title Similarity -----------------
            toc_title = entry.get("title", "")
            chunk_title = chunk.get("title", "")
            sim = self._similarity(toc_title, chunk_title)

            if sim < self._threshold:
                title_miss.append(
                    {
                        "section_id": sid,
                        "toc_title": toc_title,
                        "chunk_title": chunk_title,
                        "similarity": sim,
                    }
                )

            # -------------- Page Range Check -----------------
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
