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

    def extract_text(self, pdf_path: str) -> List[Dict]:
        """
        Extract text from a PDF file.

        Parameters
        ----------
        pdf_path : str
            Path to PDF file.

        Returns
        -------
        List[Dict]
            List of pages containing extracted text.
        """
        with open(pdf_path, "rb") as file_obj:
            full_text = extract_text(file_obj)

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
