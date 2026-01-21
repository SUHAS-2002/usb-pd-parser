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
        self.__strategy: PDFTextStrategy = strategy
        self.__pdf_path: str | None = None

    # ---------------------------------------------------------
    # Encapsulation: PDF path
    # ---------------------------------------------------------
    @property
    def pdf_path(self) -> str:
        if self.__pdf_path is None:
            raise ValueError("pdf_path not set")
        return self.__pdf_path

    @pdf_path.setter
    def pdf_path(self, value: str) -> None:
        if not isinstance(value, str):
            raise ValueError("pdf_path must be a string")
        if not value.lower().endswith(".pdf"):
            raise ValueError("pdf_path must point to a PDF file")
        self.__pdf_path = value

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
    # Strategy access (protected)
    # ---------------------------------------------------------
    @property
    def _pdf_strategy(self) -> PDFTextStrategy:
        """Return the injected PDF extraction strategy."""
        return self.__strategy

    # ---------------------------------------------------------
    @abstractmethod
    def parse(self) -> List[Dict]:
        """
        Parse the PDF and return structured pages.

        Must be implemented by concrete parsers.
        """
        raise NotImplementedError
