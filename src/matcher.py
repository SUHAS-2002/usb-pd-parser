import re
from typing import List, Dict, Any
from difflib import SequenceMatcher
import logging

logger = logging.getLogger(__name__)


class SectionMatcher:
    """Matches TOC entries to content chunks with deep analysis."""

    def __init__(self, threshold: float = 0.85):
        self.threshold = threshold

    def _normalize(self, text: str) -> str:
        """Normalize text for similarity checks."""
        text = text.lower()
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"[^\w\s]", "", text)
        return text.strip()

    def _similarity(self, a: str, b: str) -> float:
        """Compute similarity ratio between two strings."""
        return SequenceMatcher(None, self._normalize(a),
                               self._normalize(b)).ratio()

    def _match_titles(self, toc: List[Dict], chunks: List[Dict]) -> Dict:
        """Match TOC titles to chunk headings."""
        toc_map = {e["section_id"]: e for e in toc}
        chunk_map = {c["section_id"]: c for c in chunks}

        matched = []
        missing = []
        extra = []
        title_mismatches = []

        for sid, toc_entry in toc_map.items():
            if sid in chunk_map:
                chunk = chunk_map[sid]
                sim = self._similarity(toc_entry["title"],
                                       chunk["start_heading"])
                matched.append({
                    "section_id": sid,
                    "toc_title": toc_entry["title"],
                    "chunk_title": chunk["start_heading"],
                    "similarity": sim,
                    "page_match": toc_entry["page"] == chunk["start_page"]
                })
                if sim < self.threshold:
                    title_mismatches.append({
                        "section_id": sid,
                        "toc_title": toc_entry["title"],
                        "chunk_title": chunk["start_heading"],
                        "similarity": sim,
                        "issue": "low_similarity"
                    })
            else:
                missing.append({"section_id": sid,
                                "title": toc_entry["title"]})

        for sid, chunk in chunk_map.items():
            if sid not in toc_map:
                extra.append({"section_id": sid,
                              "title": chunk["start_heading"]})

        return {
            "matched": matched,
            "missing": missing,
            "extra": extra,
            "title_mismatches": title_mismatches
        }

    def _check_order(self, toc: List[Dict], chunks: List[Dict]) -> List[Dict]:
        """Check if chunks appear in the correct TOC order."""
        order_map = {e["section_id"]: i for i, e in enumerate(toc)}
        issues = []
        prev_index = -1

        for i, chunk in enumerate(chunks):
            sid = chunk["section_id"]
            if sid in order_map:
                curr_index = order_map[sid]
                if curr_index < prev_index:
                    issues.append({
                        "section_id": sid,
                        "expected": curr_index,
                        "actual": i,
                        "gap": prev_index - curr_index
                    })
                prev_index = curr_index
        return issues

    def _check_pages(self, toc: List[Dict], chunks: List[Dict]) -> List[Dict]:
        """Check for page number discrepancies."""
        chunk_map = {c["section_id"]: c for c in chunks}
        issues = []

        for toc_entry in toc:
            sid = toc_entry["section_id"]
            if sid in chunk_map:
                chunk_page = chunk_map[sid]["start_page"]
                diff = abs(toc_entry["page"] - chunk_page)
                if diff > 2:
                    issues.append({
                        "section_id": sid,
                        "toc_page": toc_entry["page"],
                        "chunk_page": chunk_page,
                        "diff": diff
                    })
        return issues

    def analyze(self, toc: List[Dict], chunks: List[Dict]) -> Dict[str, Any]:
        """Run full analysis of TOC vs content chunks."""
        logger.info("Running section analysis...")

        match_data = self._match_titles(toc, chunks)
        out_of_order = self._check_order(toc, chunks)
        page_issues = self._check_pages(toc, chunks)

        return {
            **match_data,
            "out_of_order": out_of_order,
            "page_discrepancies": page_issues,
            "total_toc": len(toc),
            "total_chunks": len(chunks)
        }
