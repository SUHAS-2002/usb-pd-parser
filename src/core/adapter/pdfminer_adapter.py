# src/core/adapter/pdfminer_adapter.py

from typing import List, Dict
from pdfminer.high_level import extract_text

from src.core.pdf_text_strategy import PDFTextStrategy


class PDFMinerAdapter(PDFTextStrategy):
    """
    PDF text extractor using PDFMiner.

    Produces a normalized list:
    [
        {"page_number": int, "text": str}
    ]
    """

    # ---------------------------------------------------------
    # Public API (Strategy interface)
    # ---------------------------------------------------------
    def extract_text(self, pdf_path: str) -> List[Dict]:
        full_text = self.__extract_raw_text(pdf_path)
        return self.__split_into_pages(full_text)

    # ---------------------------------------------------------
    # Private helpers
    # ---------------------------------------------------------
    def __extract_raw_text(self, pdf_path: str) -> str:
        with open(pdf_path, "rb") as file_obj:
            return extract_text(file_obj)

    # ---------------------------------------------------------
    def __split_into_pages(self, full_text: str) -> List[Dict]:
        raw_pages = full_text.split("\f")
        pages: List[Dict] = []

        for idx, content in enumerate(raw_pages, start=1):
            text = content.strip() if content else ""
            pages.append(
                {
                    "page_number": idx,
                    "text": text,
                }
            )

        return pages
