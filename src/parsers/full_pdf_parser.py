from typing import List, Dict

from src.core.base_parser import BaseParser
from src.core.pdf_text_strategy import PDFTextStrategy


class FullPDFParser(BaseParser):
    """
    Full PDF parser with robust page normalization.

    Fixes:
    - Missing page numbers (e.g., page 77 missing)
    - Out-of-order pages (e.g., 76 → 500 → 78)
    - Duplicate pages from extractor bugs
    - Ensures sorted, gap-free, unique page list
    """

    def __init__(self, strategy: PDFTextStrategy) -> None:
        super().__init__(strategy)

    # -----------------------------------------------------------
    # Public API (SHORT & READABLE)
    # -----------------------------------------------------------
    def parse(self) -> List[Dict]:
        """
        Return a normalized list of pages.

        Always produces:
            [
                {"page_number": 1, "text": "..."},
                {"page_number": 2, "text": "..."},
                ...
            ]
        """
        raw_pages = self._extract_raw_pages()
        normalized = self._normalize_pages(raw_pages)
        unique = self._deduplicate_pages(normalized)
        return self._fill_missing_pages(unique)

    # -----------------------------------------------------------
    # Pipeline steps
    # -----------------------------------------------------------
    def _extract_raw_pages(self) -> List[Dict]:
        return self._pdf_strategy.extract_text(self.pdf_path)

    def _normalize_pages(self, raw_pages: List[Dict]) -> List[Dict]:
        normalized: List[Dict] = []

        for page in raw_pages:
            try:
                num = int(page.get("page_number", 0))
            except (ValueError, TypeError):
                # Skip pages with invalid page numbers
                continue

            text = page.get("text") or ""
            normalized.append(
                {"page_number": num, "text": text}
            )

        return sorted(
            normalized,
            key=lambda p: p["page_number"],
        )

    def _deduplicate_pages(
        self,
        pages: List[Dict],
    ) -> List[Dict]:
        seen: set[int] = set()
        unique: List[Dict] = []

        for page in pages:
            num = page["page_number"]
            if num not in seen:
                unique.append(page)
                seen.add(num)

        return unique

    def _fill_missing_pages(
        self,
        pages: List[Dict],
    ) -> List[Dict]:
        if not pages:
            return []

        max_page = pages[-1]["page_number"]
        page_map = {
            p["page_number"]: p
            for p in pages
        }

        full_pages: List[Dict] = []
        for num in range(1, max_page + 1):
            full_pages.append(
                page_map.get(
                    num,
                    {"page_number": num, "text": ""},
                )
            )

        return full_pages
