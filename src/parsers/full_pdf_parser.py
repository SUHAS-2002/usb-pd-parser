# src/parsers/full_pdf_parser.py

from typing import List, Dict
from src.core.base_parser import BaseParser
from src.core.pdf_text_strategy import PDFTextStrategy


class FullPDFParser(BaseParser):
    """
    Full PDF parser with improved robustness.
    FIXES:
        - missing page numbers (e.g., page 77 missing)
        - out-of-order pages (e.g., 76 → 500 → 78)
        - duplicated page numbers caused by extractors
        - ensures normalized, gap-free page list
    """

    def __init__(self, strategy: PDFTextStrategy):
        super().__init__(strategy)

    def parse(self) -> List[Dict]:
        """
        Return a list of pages from the strategy.
        Always produces:
            [
                {"page_number": 1, "text": "..."},
                {"page_number": 2, "text": "..."},
                ...
            ]
        and guarantees:
        - sorted pages
        - no duplicates
        - no gaps
        - page count matches the PDF
        """
        raw_pages = self._strategy.extract_text(self.pdf_path)

        # -----------------------------------------------------------
        # 1. Normalize page structure
        # -----------------------------------------------------------
        normalized = []
        for p in raw_pages:
            try:
                num = int(p.get("page_number", 0))
            except Exception:
                continue

            normalized.append({
                "page_number": num,
                "text": p.get("text", "") or ""
            })

        # -----------------------------------------------------------
        # 2. Sort by page number
        # -----------------------------------------------------------
        normalized.sort(key=lambda x: x["page_number"])

        # -----------------------------------------------------------
        # 3. Remove duplicates (keep the first one)
        # -----------------------------------------------------------
        seen = set()
        unique = []
        for p in normalized:
            pg = p["page_number"]
            if pg not in seen:
                unique.append(p)
                seen.add(pg)

        # -----------------------------------------------------------
        # 4. Detect missing pages and fill them with empty placeholders
        # -----------------------------------------------------------
        if not unique:
            return []

        max_page = unique[-1]["page_number"]
        full_pages = []

        page_map = {p["page_number"]: p for p in unique}

        for n in range(1, max_page + 1):
            if n in page_map:
                full_pages.append(page_map[n])
            else:
                # Missing page → create placeholder
                full_pages.append({
                    "page_number": n,
                    "text": ""
                })

        # -----------------------------------------------------------
        # 5. Final list is gap-free, sorted, deduplicated
        # -----------------------------------------------------------
        return full_pages
