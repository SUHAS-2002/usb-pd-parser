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

            # Filter false positives at extraction time
            if self._is_false_positive_title(sid, title_clean):
                continue

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
    
    @staticmethod
    def _is_false_positive_title(section_id: str, title: str) -> bool:
        """Enhanced false positive detection at extraction time."""
        import re
        
        # Version with letter suffix (1.0a, 2.0b, etc.)
        if re.match(r'^\d+(\.\d+)*[a-z]$', title, re.IGNORECASE):
            return True
        
        # Very short abbreviations (ms, us, ns, etc.)
        short_abbrevs = {
            'ms', 'us', 'ns', 'ps', 'fs',
            'mv', 'kv', 'ma', 'ua', 'na',
            'db', 'hz', 'khz', 'mhz', 'ghz',
            'kb', 'mb', 'gb', 'tb',
            'mm', 'cm', 'km', 'in', 'ft',
            'kg', 'g', 'mg', 'lb',
        }
        if title.lower() in short_abbrevs:
            return True
        if re.match(r'^[a-z]{1,3}$', title):
            return True
        
        # Just version numbers (1.0, 2.0, 3.1, etc.)
        if re.match(r'^\d+(\.\d+)*$', title):
            if len(title) <= 10 and title.count('.') <= 2:
                return True
        
        # Ellipsis patterns (7…6, 14…12)
        if re.search(r'\d+[…\.]{2,}\d+', title):
            return True
        
        # Voltage patterns (+ 9V, + 15V, - 5V)
        if re.search(r'[\+\-]\s*\d+V', title, re.IGNORECASE):
            return True
        if re.match(r'^[\+\-]?\s*\d+\s*V$', title, re.IGNORECASE):
            return True
        
        # Too short
        if len(title) < 2:
            return True
        
        # Just symbols and numbers
        if len([c for c in title if c.isalnum()]) < 2:
            return True
        
        # Mathematical expressions
        if re.search(r'[\+\-]\s*\d+[\s\+\-]+\d+', title):
            return True
        
        return False

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
    
    
    # --------------------------------------------------------------
    # Polymorphism: Additional special methods
    # --------------------------------------------------------------
    def __str__(self) -> str:
        """Human-readable representation."""
        return f"{self.__class__.__name__}(extracted={self.extracted_count})"
    
    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"{self.__class__.__name__}()"
    
    def __enter__(self) -> "InlineHeadingExtractor":
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Context manager exit."""
        return False