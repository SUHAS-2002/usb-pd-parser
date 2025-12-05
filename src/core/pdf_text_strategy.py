# src/core/pdf_text_strategy.py
from abc import ABC, abstractmethod
from typing import Any, Dict, List


class PDFTextStrategy(ABC):
    """
    Abstract base class for all PDF text extraction strategies.

    The strategy pattern allows multiple interchangeable extractors such as:
        - PyMuPDF-based text extractor
        - PDFMiner-based extractor
        - OCR-based extractor
        - Hybrid extractor for noisy documents

    Each concrete implementation MUST return a normalized structure:
        List[Dict] where each item is:
            {
                "page_number": int,
                "text": str
            }
    """

    @abstractmethod
    def extract_text(self, pdf_path: str) -> List[Dict]:
        """
        Extract text from the given PDF file.

        Parameters
        ----------
        pdf_path : str
            Input PDF file path.

        Returns
        -------
        List[Dict]
            A list of pages in normalized format.

        Example:
        [
            {"page_number": 1, "text": "..."},
            {"page_number": 2, "text": "..."},
            ...
        ]
        """
        raise NotImplementedError("extract_text() must be implemented by subclasses.")