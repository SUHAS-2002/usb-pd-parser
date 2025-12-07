# src/core/pdf_text_strategy.py

from abc import ABC, abstractmethod
from typing import Dict, List


class PDFTextStrategy(ABC):
    """
    Abstract base class for all PDF text extraction strategies.

    The strategy pattern allows interchangeable extractors such as:

    - PyMuPDF-based extractor
    - PDFMiner-based extractor
    - OCR-based extractor
    - Hybrid extractors for complex layouts

    Each implementation must return a normalized structure:

        List[Dict] where each dict contains:
            {
                "page_number": int,
                "text": str
            }
    """

    @abstractmethod
    def extract_text(self, pdf_path: str) -> List[Dict]:
        """
        Extract text from the provided PDF file.

        Parameters
        ----------
        pdf_path : str
            Path to the input PDF file.

        Returns
        -------
        List[Dict]
            List of pages in normalized format.

        Example:
            [
                {"page_number": 1, "text": "..."},
                {"page_number": 2, "text": "..."}
            ]
        """
        raise NotImplementedError(
            "extract_text() must be implemented by subclasses."
        )
