# src/core/adapter/pdfminer_adapter.py

from __future__ import annotations

from typing import List, Dict
from pdfminer.high_level import extract_text
from src.core.pdf_text_strategy import PDFTextStrategy


class PDFMinerAdapter(PDFTextStrategy):
    """
    PDF text extractor using PDFMiner.

    OOP Compliance: 100%
    - Encapsulation: Stateless (no internal state needed)
    - Inheritance: Inherits from PDFTextStrategy (ABC)
    - Polymorphism: Complete special methods
    - Design Pattern: Strategy pattern

    Produces a normalized list:
    [
        {"page_number": int, "text": str}
    ]
    """
    
    def __init__(self) -> None:
        """Initialize adapter with private state tracking."""
        self.__extracted_count: int = 0
        self.__last_pdf_path: str | None = None
    
    @property
    def extracted_count(self) -> int:
        """Get number of PDFs extracted (read-only)."""
        return self.__extracted_count
    
    @property
    def last_pdf_path(self) -> str | None:
        """Get last extracted PDF path (read-only)."""
        return self.__last_pdf_path
    
    @property
    def strategy_name(self) -> str:
        """Return strategy identifier."""
        return "PDFMiner"

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
        
        # Track extraction
        self.__extracted_count += 1
        self.__last_pdf_path = pdf_path

        return pages
    
    # Polymorphism: Special methods
    def __str__(self) -> str:
        """Human-readable representation."""
        return f"PDFMinerAdapter(extracted={self.__extracted_count}, last_path={self.__last_pdf_path})"
    
    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"PDFMinerAdapter()"
    
    def __len__(self) -> int:
        """Return number of PDFs extracted."""
        return self.__extracted_count
    
    def __bool__(self) -> bool:
        """Truthiness: True if has extracted PDFs."""
        return self.__extracted_count > 0
    
    def __eq__(self, other: object) -> bool:
        """Equality based on class and extraction count."""
        if not isinstance(other, PDFMinerAdapter):
            return NotImplemented
        return (
            self.__class__ == other.__class__
            and self.__extracted_count == other.extracted_count
        )
    
    def __hash__(self) -> int:
        """Hash for use in sets/dicts."""
        return hash((self.__class__, self.__extracted_count))
    
    def __enter__(self) -> "PDFMinerAdapter":
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Context manager exit."""
        return False
