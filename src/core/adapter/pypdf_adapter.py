# src/core/adapter/pypdf_adapter.py

from typing import List, Dict
from pathlib import Path
from PyPDF2 import PdfReader

from src.core.pdf_text_strategy import PDFTextStrategy


class PyPDFAdapter(PDFTextStrategy):
    """
    PDF text extractor using PyPDF2.
    """

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------
    def extract_text(self, pdf_path: str) -> List[Dict]:
        path = self.__validate_path(pdf_path)
        reader = PdfReader(path)
        return self.__extract_pages(reader)

    # ---------------------------------------------------------
    # Private helpers
    # ---------------------------------------------------------
    def __validate_path(self, pdf_path: str) -> Path:
        path = Path(pdf_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {path}")
        return path

    def __extract_pages(self, reader: PdfReader) -> List[Dict]:
        pages: List[Dict] = []

        for idx, page in enumerate(reader.pages, start=1):
            raw = page.extract_text() or ""
            pages.append(
                {
                    "page_number": idx,
                    "text": raw.strip(),
                }
            )

        return pages
