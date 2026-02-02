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
        from src.config import CONFIG
        
        processed_pages = set()

        for page in pages:
            page_no = page.get("page")
            if not page_no:
                continue
            
            # Exclude ToC pages (13-18) from inline heading extraction
            if CONFIG.pages.TOC_START <= page_no <= CONFIG.pages.TOC_END:
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
        
        # Filter Figure/Table patterns
        if re.match(r'^(Figure|Table)\s+\d+', title, re.IGNORECASE):
            return True
        
        # Filter section IDs that look like Figure/Table numbers
        if re.match(r'^\d{3,4}$', section_id):
            # Check if title suggests it's a figure/table
            if re.search(r'(Figure|Table|Fig\.|Tbl\.)', title, re.IGNORECASE):
                return True
        
        checks = [
            InlineHeadingExtractor._is_version_with_suffix,
            InlineHeadingExtractor._is_short_abbreviation,
            InlineHeadingExtractor._is_version_number,
            InlineHeadingExtractor._has_ellipsis_pattern,
            InlineHeadingExtractor._has_voltage_pattern,
            InlineHeadingExtractor._is_too_short,
            InlineHeadingExtractor._is_mostly_symbols,
            InlineHeadingExtractor._has_math_expression,
        ]
        
        for check in checks:
            if check(title):
                return True
        
        return False
    
    @staticmethod
    def _is_version_with_suffix(title: str) -> bool:
        """Check if title is version with letter suffix (1.0a, 2.0b)."""
        import re
        return bool(re.match(r'^\d+(\.\d+)*[a-z]$', title, re.IGNORECASE))
    
    @staticmethod
    def _is_short_abbreviation(title: str) -> bool:
        """Check if title is a short abbreviation."""
        import re
        short_abbrevs = {
            'ms', 'us', 'ns', 'ps', 'fs',
            'mv', 'kv', 'ma', 'ua', 'na',
            'db', 'hz', 'khz', 'mhz', 'ghz',
            'kb', 'mb', 'gb', 'tb',
            'mm', 'cm', 'km', 'in', 'ft',
            'kg', 'g', 'mg', 'lb',
        }
        return (
            title.lower() in short_abbrevs
            or bool(re.match(r'^[a-z]{1,3}$', title))
        )
    
    @staticmethod
    def _is_version_number(title: str) -> bool:
        """Check if title is just a version number."""
        import re
        if re.match(r'^\d+(\.\d+)*$', title):
            return len(title) <= 10 and title.count('.') <= 2
        return False
    
    @staticmethod
    def _has_ellipsis_pattern(title: str) -> bool:
        """Check if title has ellipsis pattern."""
        import re
        return bool(re.search(r'\d+[…\.]{2,}\d+', title))
    
    @staticmethod
    def _has_voltage_pattern(title: str) -> bool:
        """Check if title has voltage pattern."""
        import re
        return (
            bool(re.search(r'[\+\-]\s*\d+V', title, re.IGNORECASE))
            or bool(re.match(r'^[\+\-]?\s*\d+\s*V$', title, re.IGNORECASE))
        )
    
    @staticmethod
    def _is_too_short(title: str) -> bool:
        """Check if title is too short."""
        return len(title) < 2
    
    @staticmethod
    def _is_mostly_symbols(title: str) -> bool:
        """Check if title is mostly symbols."""
        alnum_count = len([c for c in title if c.isalnum()])
        return alnum_count < 2
    
    @staticmethod
    def _has_math_expression(title: str) -> bool:
        """Check if title has mathematical expression."""
        import re
        return bool(re.search(r'[\+\-]\s*\d+[\s\+\-]+\d+', title))

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