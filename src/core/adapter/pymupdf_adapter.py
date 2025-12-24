# src/core/adapter/pymupdf_adapter.py

import fitz  # PyMuPDF
from typing import List, Dict
from src.core.pdf_text_strategy import PDFTextStrategy


class PyMuPDFAdapter(PDFTextStrategy):
    """
    High-fidelity text extractor using PyMuPDF.

    Returns:
        [
            {"page_number": int, "text": str}
        ]
    """

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------
    def extract_text(self, pdf_path: str) -> List[Dict]:
        doc = fitz.open(pdf_path)

        try:
            return self.__extract_pages(doc)
        finally:
            doc.close()

    # ---------------------------------------------------------
    # Private helpers
    # ---------------------------------------------------------
    def __extract_pages(self, doc) -> List[Dict]:
        pages: List[Dict] = []

        for idx in range(doc.page_count):
            page = doc.load_page(idx)
            text = self.__extract_page_text(page)

            pages.append(
                {
                    "page_number": idx + 1,
                    "text": text,
                }
            )

        return pages

    # ---------------------------------------------------------
    def __extract_page_text(self, page) -> str:
        blocks = page.get_text("blocks")
        parts: List[str] = []

        for block in blocks:
            block_text = block[4]
            if block_text and block_text.strip():
                parts.append(block_text.strip())

        return "\n".join(parts)
