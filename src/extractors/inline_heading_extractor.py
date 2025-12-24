"""
Inline heading extractor (compact OOP, ≤79 chars).

Extracts numeric section headings from document body pages.
These are the authoritative section IDs.
"""

import re
from typing import List, Dict, Any, Optional

from src.core.extractor_base import BaseExtractor


class InlineHeadingExtractor(BaseExtractor):
    """
    Extract numeric section headings from PDF body text.

    Public API:
        - extract(pdf_data)
    """

    # -------------------- Private constants -------------------
    __SECTION_RE = re.compile(
        r"^\s*(\d+(?:\.\d+)*)\s+(.+)$",
        re.MULTILINE,
    )

    # ---------------------------------------------------------
    # Template method implementation
    # ---------------------------------------------------------
    def _extract_impl(self, pdf_data: Dict[str, Any]) -> List[Dict]:
        pages = self._get_pages(pdf_data)
        return self._extract_from_pages(pages)

    # ---------------------------------------------------------
    # Protected helpers
    # ---------------------------------------------------------
    def _get_pages(
        self,
        pdf_data: Dict[str, Any],
    ) -> List[Dict]:
        """
        Safely extract pages from PDF data.
        """
        return pdf_data.get("pages", []) or []

    # ---------------------------------------------------------
    def _extract_from_pages(
        self,
        pages: List[Dict],
    ) -> List[Dict]:
        """
        Extract inline numeric headings from pages.
        """
        out: List[Dict] = []

        for page in pages:
            entry = self._extract_page_headings(page)
            if entry:
                out.extend(entry)

        return out

    # ---------------------------------------------------------
    def _extract_page_headings(
        self,
        page: Dict,
    ) -> List[Dict]:
        """
        Extract headings from a single page.
        """
        page_no = page.get("page")
        text = page.get("text", "")

        if not page_no or not text:
            return []

        headings: List[Dict] = []

        for sid, title in self.__SECTION_RE.findall(text):
            headings.append(
                self._build_heading_entry(
                    sid,
                    title,
                    page_no,
                )
            )

        return headings

    # ---------------------------------------------------------
    def _build_heading_entry(
        self,
        sid: str,
        title: str,
        page: int,
    ) -> Dict:
        """
        Construct a single heading entry.
        """
        clean_title = title.strip()

        return {
            "section_id": sid,
            "title": clean_title,
            "page": page,
            "level": sid.count(".") + 1,
            "parent_id": self._parent_id(sid),
            "full_path": f"{sid} {clean_title}",
        }

    # ---------------------------------------------------------
    def _parent_id(self, sid: str) -> Optional[str]:
        if "." not in sid:
            return None
        return sid.rsplit(".", 1)[0]
