import re
from typing import List, Dict, Any
from difflib import SequenceMatcher
import logging

logger = logging.getLogger(__name__)


class SectionMatcher:
    """Matches TOC entries to content chunks with deep analysis."""

    def __init__(self, threshold: float = 0.85):
        self.threshold = threshold

    def _normalize(self, s: str) -> str:
        s = s.lower()
        s = re.sub(r"\s+", " ", s)
        s = re.sub(r"[^\w\s]", "", s)
        return s.strip()

    def _similarity(self, a: str, b: str) -> float:
        return SequenceMatcher(None, self._normalize(a), self._normalize(b)).ratio()

    def _match_titles(self, toc: List[Dict], chunks: List[Dict]) -> Dict:
        toc_map = {e["section_id"]: e for e in toc}
        chunk_map = {c["section_id"]: c for c in chunks}

        matched = []
        missing = []
        extra = []
        title_mismatches = []

        for sid, t in toc_map.items():
            if sid in chunk_map:
                c = chunk_map[sid]
                sim = self._similarity(t["title"], c["start_heading"])
                info = {
                    "section_id": sid,
                    "toc_title": t["title"],
                    "chunk_title": c["start_heading"],
                    "similarity": sim,
                    "page_match": t["page"] == c["start_page"],
                }
                matched.append(info)
                if sim < self.threshold:
                    title_mismatches.append({**info, "issue": "low_similarity"})
            else:
                missing.append({"section_id": sid, "title": t["title"]})

        for sid, c in chunk_map.items():
            if sid not in toc_map:
                extra.append({"section_id": sid, "title": c["start_heading"]})

        return {
            "matched": matched,
            "missing": missing,
            "extra": extra,
            "title_mismatches": title_mismatches,
        }

    def _check_order(self, toc: List[Dict], chunks: List[Dict]) -> List[Dict]:
        order_map = {e["section_id"]: i for i, e in enumerate(toc)}
        issues = []
        prev = -1

        for i, c in enumerate(chunks):
            sid = c["section_id"]
            if sid in order_map:
                curr = order_map[sid]
                if curr < prev:
                    issues.append({
                        "section_id": sid,
                        "expected": curr,
                        "actual": i,
                        "gap": prev - curr,
                    })
                prev = curr
        return issues

    def _check_pages(self, toc: List[Dict], chunks: List[Dict]) -> List[Dict]:
        chunk_map = {c["section_id"]: c for c in chunks}
        issues = []

        for t in toc:
            sid = t["section_id"]
            if sid in chunk_map:
                diff = abs(t["page"] - chunk_map[sid]["start_page"])
                if diff > 2:
                    issues.append({
                        "section_id": sid,
                        "toc_page": t["page"],
                        "chunk_page": chunk_map[sid]["start_page"],
                        "diff": diff,
                    })
        return issues

    def analyze(self, toc: List[Dict], chunks: List[Dict]) -> Dict[str, Any]:
        logger.info("Running section analysis...")
        match_data = self._match_titles(toc, chunks)
        out_of_order = self._check_order(toc, chunks)
        page_issues = self._check_pages(toc, chunks)

        return {
            **match_data,
            "out_of_order": out_of_order,
            "page_discrepancies": page_issues,
            "total_toc": len(toc),
            "total_chunks": len(chunks),
        }