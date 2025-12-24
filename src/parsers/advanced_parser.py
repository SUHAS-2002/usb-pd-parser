# src/parsers/advanced_parser.py

from typing import List, Dict

from src.core.base_parser import BaseParser
from src.core.pdf_text_strategy import PDFTextStrategy


class AdvancedParser(BaseParser):
    """
    Advanced parser that enhances raw PDF extraction by applying
    additional cleaning, normalization, and structural adjustments.

    Output format (consistent across all parsers):
        [
            {"page_number": int, "text": str},
            ...
        ]
    """

    # ---------------------------------------------------------
    # Construction
    # ---------------------------------------------------------
    def __init__(self, strategy: PDFTextStrategy) -> None:
        super().__init__(strategy)

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------
    def parse(self) -> List[Dict]:
        """
        Extract text using the injected PDF strategy and apply
        advanced normalization rules.

        Guarantees:
        - Page-wise output
        - Cleaned text
        - Stable ordering
        """
        raw_pages = self._extract_raw_pages()
        pages = self._normalize_pages(raw_pages)
        self._sort_pages(pages)

        return pages

    # ---------------------------------------------------------
    # Protected helpers (parser-specific logic)
    # ---------------------------------------------------------
    def _extract_raw_pages(self) -> List[Dict]:
        """
        Delegate raw text extraction to the PDF strategy.
        """
        return self._strategy.extract_text(self.pdf_path)

    # ---------------------------------------------------------
    def _normalize_pages(
        self,
        raw_pages: List[Dict],
    ) -> List[Dict]:
        """
        Normalize raw page entries into a stable structure.
        """
        pages: List[Dict] = []

        for entry in raw_pages:
            page = self._normalize_entry(entry)
            if page:
                pages.append(page)

        return pages

    # ---------------------------------------------------------
    def _normalize_entry(self, entry: Dict) -> Dict | None:
        """
        Normalize a single page entry.
        """
        page_number = entry.get("page_number")
        text = entry.get("text", "") or ""

        if page_number is None:
            return None

        return {
            "page_number": int(page_number),
            "text": text.strip(),
        }

    # ---------------------------------------------------------
    def _sort_pages(self, pages: List[Dict]) -> None:
        """
        Ensure stable ordering by page number.
        """
        pages.sort(key=lambda p: p["page_number"])
