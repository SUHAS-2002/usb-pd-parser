"""
Inline heading extractor (compact OOP, ≤79 chars).

Extracts numeric section headings from document body pages.
These are the authoritative section IDs.
"""

from __future__ import annotations

import re
import logging
from typing import List, Dict, Any

from src.core.extractor_base import BaseExtractor

# ------------------------------------------------------------------
# Module-level logger (encapsulation-friendly)
# ------------------------------------------------------------------
_logger = logging.getLogger(__name__)


class InlineHeadingExtractor(BaseExtractor):
    """
    Extract numeric section headings from PDF body text.

    Encapsulation:
    - Regex patterns are TRUE PRIVATE class constants (__CONSTANT)
    - Access via protected classmethod
    - All helpers are protected
    """

    # --------------------------------------------------------------
    # TRUE PRIVATE class constant (PHASE 2)
    # --------------------------------------------------------------
    __SECTION_PATTERN = re.compile(
        r"^\s*(\d+(?:\.\d+)*)\s+(.+)$",
        re.MULTILINE,
    )

    # --------------------------------------------------------------
    # Controlled access to class constant
    # --------------------------------------------------------------
    @classmethod
    def _get_section_pattern(cls) -> re.Pattern:
        """Get section heading regex pattern (protected)."""
        return cls.__SECTION_PATTERN

    # --------------------------------------------------------------
    # Public API
    # --------------------------------------------------------------
    def extract(self, pdf_data: Dict[str, Any]) -> List[Dict]:
        pages = pdf_data.get("pages", [])
        results: List[Dict] = []

        processed_pages = self._extract_from_pages(pages, results)

        _logger.info(
            "Processed %d pages for inline heading extraction",
            processed_pages,
        )

        return results

    # --------------------------------------------------------------
    # Extraction helpers (protected)
    # --------------------------------------------------------------
    def _extract_from_pages(
        self,
        pages: List[Dict[str, Any]],
        results: List[Dict],
    ) -> int:
        processed_pages = set()

        for page in pages:
            page_no = page.get("page")
            if not page_no:
                continue

            text = page.get("text") or ""
            self._extract_from_text(
                text=text,
                page_no=page_no,
                results=results,
            )
            processed_pages.add(page_no)

        return len(processed_pages)

    def _extract_from_text(
        self,
        text: str,
        page_no: int,
        results: List[Dict],
    ) -> None:
        for sid, title in self._get_section_pattern().findall(text):
            title_clean = title.strip()

            results.append(
                {
                    "section_id": sid,
                    "title": title_clean,
                    "page": page_no,
                    "level": self._compute_level(sid),
                    "parent_id": self._compute_parent(sid),
                    "full_path": f"{sid} {title_clean}",
                }
            )

    # --------------------------------------------------------------
    # Section helpers (protected)
    # --------------------------------------------------------------
    @staticmethod
    def _compute_level(section_id: str) -> int:
        return section_id.count(".") + 1

    @staticmethod
    def _compute_parent(section_id: str) -> str | None:
        if "." in section_id:
            return section_id.rsplit(".", 1)[0]
        return None
