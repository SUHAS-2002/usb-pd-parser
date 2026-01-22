# src/parsers/full_pdf_parser.py

from typing import List, Dict
from src.core.base_parser import BaseParser
from src.core.pdf_text_strategy import PDFTextStrategy


class FullPDFParser(BaseParser):
    """
    Full PDF parser with robust page normalization.

    Fixes:
    - Missing page numbers (e.g., page 77 missing).
    - Out-of-order pages (e.g., 76 → 500 → 78).
    - Duplicate pages from extractor bugs.
    - Ensures sorted, gap-free, unique page list.
    """

    def __init__(self, strategy: PDFTextStrategy) -> None:
        super().__init__(strategy)

    def parse(self) -> List[Dict]:
        """
        Return a normalized list of pages.

        Always produces:
            [
                {"page_number": 1, "text": "..."},
                {"page_number": 2, "text": "..."},
                ...
            ]

        Guarantees:
        - Sorted pages
        - No duplicates
        - No missing gaps
        """
        raw_pages = self._pdf_strategy.extract_text(self.pdf_path)

        # -----------------------------------------------------------
        # 1. Normalize page structure
        # -----------------------------------------------------------
        normalized: List[Dict] = []
        for page in raw_pages:
            try:
                num = int(page.get("page_number", 0))
            except Exception:
                continue

            txt = page.get("text") or ""
            normalized.append(
                {"page_number": num, "text": txt}
            )

        # -----------------------------------------------------------
        # 2. Sort pages
        # -----------------------------------------------------------
        normalized.sort(key=lambda p: p["page_number"])

        # -----------------------------------------------------------
        # 3. Remove duplicate pages
        # -----------------------------------------------------------
        seen: set = set()
        unique: List[Dict] = []

        for page in normalized:
            num = page["page_number"]
            if num not in seen:
                unique.append(page)
                seen.add(num)

        if not unique:
            return []

        # -----------------------------------------------------------
        # 4. Fill missing pages with blank placeholders
        # -----------------------------------------------------------
        max_page = unique[-1]["page_number"]
        page_map = {p["page_number"]: p for p in unique}

        full_pages: List[Dict] = []
        for num in range(1, max_page + 1):
            if num in page_map:
                full_pages.append(page_map[num])
            else:
                full_pages.append(
                    {"page_number": num, "text": ""}
                )

        return full_pages
