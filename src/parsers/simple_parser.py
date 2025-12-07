# src/parsers/simple_parser.py

from typing import List, Dict
from src.core.base_parser import BaseParser
from src.core.pdf_text_strategy import PDFTextStrategy


class SimpleParser(BaseParser):
    """
    Simple parser that performs minimal processing.
    It directly returns text extracted by the chosen PDF strategy.

    Output format:
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
        Extract text without additional analysis.
        Ensures:
        - consistent page_number/text format
        - sorted output
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

        pages.sort(key=lambda p: p["page_number"])
        return pages
