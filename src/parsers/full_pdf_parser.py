# src/parsers/full_pdf_parser.py

from typing import List, Dict
from src.core.base_parser import BaseParser
from src.core.pdf_text_strategy import PDFTextStrategy


class FullPDFParser(BaseParser):
    """
    Full PDF parser with robust page normalization.

    Fixes:
    - Missing page numbers
    - Out-of-order pages
    - Duplicate pages
    - Ensures sorted, gap-free page list
    """

    def __init__(self, strategy: PDFTextStrategy) -> None:
        super().__init__(strategy)

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------
    def parse(self) -> List[Dict]:
        raw_pages = self._strategy.extract_text(self.pdf_path)

        normalized = self.__normalize(raw_pages)
        unique = self.__deduplicate(normalized)

        if not unique:
            return []

        return self.__fill_gaps(unique)

    # ---------------------------------------------------------
    # Private helpers
    # ---------------------------------------------------------
    def __normalize(
        self,
        raw_pages: List[Dict],
    ) -> List[Dict]:
        pages: List[Dict] = []

        for page in raw_pages:
            try:
                num = int(page.get("page_number", 0))
            except Exception:
                continue

            text = page.get("text") or ""
            pages.append(
                {"page_number": num, "text": text}
            )

        pages.sort(key=lambda p: p["page_number"])
        return pages

    # ---------------------------------------------------------
    def __deduplicate(
        self,
        pages: List[Dict],
    ) -> List[Dict]:
        seen = set()
        unique: List[Dict] = []

        for page in pages:
            num = page["page_number"]
            if num not in seen:
                unique.append(page)
                seen.add(num)

        return unique

    # ---------------------------------------------------------
    def __fill_gaps(
        self,
        pages: List[Dict],
    ) -> List[Dict]:
        max_page = pages[-1]["page_number"]
        page_map = {
            p["page_number"]: p for p in pages
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
