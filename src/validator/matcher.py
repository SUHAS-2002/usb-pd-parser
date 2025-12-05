# src/validator/matcher.py

import re
from typing import List, Dict
from difflib import SequenceMatcher


class SectionMatcher:
    """
    Matches TOC entries to Content Chunks using:
        ✓ Exact section_id mapping
        ✓ Fuzzy title similarity
        ✓ Page range consistency

    Returns a detailed diagnostic report.
    """

    def __init__(self, title_threshold: float = 0.85):
        self.title_threshold = title_threshold

    # ----------------------------------------------------------
    def _normalize(self, s: str) -> str:
        """Normalize strings for comparison."""
        s = s.lower()
        s = re.sub(r"\s+", " ", s)
        s = re.sub(r"[^\w\s]", "", s)
        return s.strip()

    # ----------------------------------------------------------
    def _similarity(self, a: str, b: str) -> float:
        """Fuzzy string similarity."""
        return SequenceMatcher(None, self._normalize(a), self._normalize(b)).ratio()

    # ----------------------------------------------------------
    def match(self, toc: List[Dict], chunks: List[Dict]) -> Dict:
        """
        Validate mapping between TOC entries and extracted content chunks.
        """

        chunk_map = {c["section_id"]: c for c in chunks}

        matched = []
        missing = []
        title_mismatches = []
        page_discrepancies = []

        for entry in toc:
            sid = entry["section_id"]

            # --- Case: Missing Chunk ---
            if sid not in chunk_map:
                missing.append(entry)
                continue

            chunk = chunk_map[sid]

            # --- Fuzzy title validation ---
            sim = self._similarity(entry["title"], chunk["title"])
            if sim < self.title_threshold:
                title_mismatches.append({
                    "section_id": sid,
                    "toc_title": entry["title"],
                    "chunk_title": chunk["title"],
                    "similarity": sim
                })

            # --- Page Range consistency ---
            if entry["page"] < chunk["page_range"][0] or entry["page"] > chunk["page_range"][1]:
                page_discrepancies.append({
                    "section_id": sid,
                    "toc_page": entry["page"],
                    "chunk_range": chunk["page_range"]
                })

            matched.append(entry)

        return {
            "matched": matched,
            "missing": missing,
            "title_mismatches": title_mismatches,
            "page_discrepancies": page_discrepancies,
            "total_toc": len(toc)
        }
