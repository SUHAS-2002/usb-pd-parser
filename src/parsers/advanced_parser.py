# src/parsers/advanced_parser.py

from typing import List, Dict
from src.core.base_parser import BaseParser
from src.core.pdf_text_strategy import PDFTextStrategy


class AdvancedParser(BaseParser):
    """
    Advanced parser that enhances raw PDF extraction by applying
    additional cleaning, normalization, or structural adjustments.

    Output format matches all parsers:
        [
            {"page_number": int, "text": str},
            ...
        ]
    """

    def __init__(self, strategy: PDFTextStrategy) -> None:
        super().__init__(strategy)

    # ---------------------------------------------------------
    def parse(self) -> List[Dict]:
        """
        Extract text and perform advanced normalization.
        Ensures:
        - page-wise list
        - cleaned text
        - consistent formatting
        """
        raw_pages = self._strategy.extract_text(self.pdf_path)

        pages: List[Dict] = []
        for entry in raw_pages:
            num = entry.get("page_number")
            text = entry.get("text", "") or ""

            if num is None:
                continue

            pages.append(
                {
                    "page_number": int(num),
                    "text": text.strip(),
                }
            )

        # Ensure stable ordering
        pages.sort(key=lambda p: p["page_number"])

        return pages
