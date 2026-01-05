# src/core/pdf_text_strategy.py

from abc import ABC, abstractmethod
from typing import Dict, List

from src.core.interfaces import PDFExtractorProtocol


class PDFTextStrategy(ABC, PDFExtractorProtocol):
    """
    Abstract base class for all PDF text extraction strategies.

    Strategy Pattern:
    - Concrete extractors implement `extract_text`
    - Parser interacts via `PDFExtractorProtocol`
    - Strategies are interchangeable and testable
    """

    # ---------------------------------------------------------
    @abstractmethod
    def extract_text(self, pdf_path: str) -> List[Dict]:
        """
        Extract text from the provided PDF file.

        Concrete strategies must implement this method.

        Returns:
            List[Dict] with normalized page text.
        """
        raise NotImplementedError(
            "extract_text() must be implemented by subclasses."
        )

    # ---------------------------------------------------------
    # Protocol compatibility
    # ---------------------------------------------------------
    def extract(self, pdf_path: str) -> List[Dict]:
        """
        Protocol entry point.

        Delegates to the concrete strategy implementation.
        """
        return self.extract_text(pdf_path)

    # ---------------------------------------------------------
    # Strategy metadata
    # ---------------------------------------------------------
    @property
    @abstractmethod
    def strategy_name(self) -> str:
        """Return a human-readable strategy identifier."""
        raise NotImplementedError

    # ---------------------------------------------------------
    # Polymorphism helpers
    # ---------------------------------------------------------
    def __str__(self) -> str:
        return f"{self.__class__.__name__}(strategy={self.strategy_name})"

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}"
            f"(strategy_name={self.strategy_name!r})"
        )
