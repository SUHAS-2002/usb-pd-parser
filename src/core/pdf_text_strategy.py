# src/core/pdf_text_strategy.py

from abc import ABC, abstractmethod
from typing import Dict, List

from src.core.interfaces import PDFExtractorProtocol


class PDFTextStrategy(ABC, PDFExtractorProtocol):
    """
    Abstract base class for all PDF text extraction strategies.

    Strategy Pattern:
    - Concrete extractors implement extract_text()
    - Parser interacts via PDFExtractorProtocol
    - Strategies are interchangeable and testable

    Encapsulation:
    - No internal state (stateless strategy)
    - Public API strictly defined by abstract methods
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
    # Polymorphism: Complete special methods
    # ---------------------------------------------------------
    def __str__(self) -> str:
        return f"{self.__class__.__name__}(strategy={self.strategy_name})"

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}"
            f"(strategy_name={self.strategy_name!r})"
        )
    
    def __eq__(self, other: object) -> bool:
        """Equality based on class and strategy name."""
        if not isinstance(other, PDFTextStrategy):
            return NotImplemented
        return (
            self.__class__ == other.__class__
            and self.strategy_name == other.strategy_name
        )
    
    def __hash__(self) -> int:
        """Hash for use in sets/dicts."""
        return hash((self.__class__, self.strategy_name))
    
    def __bool__(self) -> bool:
        """Truthiness: Always True (strategy is always valid)."""
        return True
    
    def __len__(self) -> int:
        """Return strategy identifier length."""
        return len(self.strategy_name)
    
    def __call__(self, pdf_path: str) -> List[Dict]:
        """Make class callable - delegates to extract_text()."""
        return self.extract_text(pdf_path)
    
    def __enter__(self) -> "PDFTextStrategy":
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Context manager exit."""
        return False
