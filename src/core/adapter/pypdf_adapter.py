# src/core/adapter/pypdf_adapter.py

from typing import List, Dict
from PyPDF2 import PdfReader
from src.core.pdf_text_strategy import PDFTextStrategy


class PyPDFAdapter(PDFTextStrategy):
    """
    PDF text extractor using PyPDF2.

    Produces a normalized list:
    [
        {"page_number": int, "text": str}
    ]
    """

    def extract_text(self, pdf_path: str) -> List[Dict]:
        """
        Extract page-wise text using PyPDF2.

        Parameters
        ----------
        pdf_path : str
            Path to PDF file.

        Returns
        -------
        List[Dict]
            List of pages containing extracted text.
        """
        reader = PdfReader(pdf_path)
        pages: List[Dict] = []

        for idx, page in enumerate(reader.pages, start=1):
            raw = page.extract_text() or ""
            text = raw.strip()

            pages.append(
                {
                    "page_number": idx,
                    "text": text,
                }
            )

        return pages
