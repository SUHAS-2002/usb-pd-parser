# src/core/base_parser.py

from abc import ABC, abstractmethod
from typing import Any, List, Dict

from src.core.pdf_text_strategy import PDFTextStrategy


class BaseParser(ABC):
    """
    Abstract base parser defining the public interface
    for all concrete PDF parsers.

    Encapsulation:
    - ALL internal state uses name-mangled attributes (__attr)
    - Public API remains stable
    - Strategy access is protected
    """

    # ---------------------------------------------------------
    # Constructor (TRUE PRIVATE STATE)
    # ---------------------------------------------------------
    def __init__(self, strategy: PDFTextStrategy) -> None:
        """Initialize parser with name-mangled private state."""
        self.__strategy: PDFTextStrategy = strategy
        self.__pdf_path: str | None = None

    # ---------------------------------------------------------
    # Encapsulation: PDF path
    # ---------------------------------------------------------
    @property
    def pdf_path(self) -> str:
        """Get PDF path (read-only after set)."""
        if self.__pdf_path is None:
            raise ValueError("pdf_path not set")
        return self.__pdf_path

    @pdf_path.setter
    def pdf_path(self, value: str) -> None:
        """Set PDF path with validation."""
        if not isinstance(value, str):
            raise ValueError("pdf_path must be a string")
        if not value.lower().endswith(".pdf"):
            raise ValueError("pdf_path must point to a PDF file")
        self.__pdf_path = value

    # ---------------------------------------------------------
    # Strategy access (protected property)
    # ---------------------------------------------------------
    @property
    def _pdf_strategy(self) -> PDFTextStrategy:
        """Return the injected PDF extraction strategy (protected)."""
        return self.__strategy

    # ---------------------------------------------------------
    # Factory entry point
    # ---------------------------------------------------------
    def run(self) -> List[Dict]:
        """
        Standard execution entry point for Factory usage.

        Delegates to parse() implemented by subclasses.
        """
        return self.parse()

    # ---------------------------------------------------------
    # Abstract method
    # ---------------------------------------------------------
    @abstractmethod
    def parse(self) -> List[Dict]:
        """
        Parse the PDF and return structured pages.

        Must be implemented by concrete parsers.
        """
        raise NotImplementedError
    
    # ---------------------------------------------------------
    # Polymorphism: Special methods
    # ---------------------------------------------------------
    def __str__(self) -> str:
        """Human-readable representation."""
        pdf_name = Path(self.__pdf_path).name if self.__pdf_path else "None"
        return f"{self.__class__.__name__}(pdf={pdf_name})"
    
    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"{self.__class__.__name__}(strategy={self.__strategy!r})"
    
    def __eq__(self, other: object) -> bool:
        """Equality based on class and PDF path."""
        if not isinstance(other, BaseParser):
            return NotImplemented
        return (
            self.__class__ == other.__class__
            and self.__pdf_path == other.__pdf_path
        )
    
    def __hash__(self) -> int:
        """Hash for use in sets/dicts."""
        return hash((self.__class__, self.__pdf_path))
    
    def __bool__(self) -> bool:
        """Truthiness: True if PDF path is set."""
        return self.__pdf_path is not None
