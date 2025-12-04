# src/parsers/full_pdf_parser.py
from typing import List, Dict
from ..core.base_parser import BaseParser
from ..core.pdf_text_strategy import PDFTextStrategy

class FullPDFParser(BaseParser):
    """
    Full PDF parser: uses a PDFTextStrategy to return the raw pages list.
    The extractors will build the ToC & chunks from this list.
    """

    def __init__(self, strategy: PDFTextStrategy):
        super().__init__(strategy)

    def parse(self) -> List[Dict]:
        """
        Return a list of pages from the strategy.
        Each page is {"page_number": int, "text": str}
        """
        pages = self._strategy.extract_text(self.pdf_path)
        # Ensure format is consistent
        normalized = []
        for p in pages:
            normalized.append({
                "page_number": int(p.get("page_number", 0)),
                "text": p.get("text", "") or ""
            })
        return normalized
