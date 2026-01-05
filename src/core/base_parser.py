# src/core/base_parser.py

from abc import ABC, abstractmethod
from typing import Any, List, Dict

from src.core.pdf_text_strategy import PDFTextStrategy


class BaseParser(ABC):
    """
    Abstract base parser defining the public interface
    for all concrete PDF parsers.

    This class is Factory-compatible and Strategy-aware.
    """

    # ---------------------------------------------------------
    def __init__(self, strategy: PDFTextStrategy) -> None:
        self._strategy: PDFTextStrategy = strategy
        self._pdf_path: str | None = None

    # ---------------------------------------------------------
    # Encapsulation: PDF path
    # ---------------------------------------------------------
    @property
    def pdf_path(self) -> str:
        if self._pdf_path is None:
            raise ValueError("pdf_path not set")
        return self._pdf_path

    @pdf_path.setter
    def pdf_path(self, value: str) -> None:
        if not isinstance(value, str):
            raise ValueError("pdf_path must be a string")
        if not value.lower().endswith(".pdf"):
            raise ValueError("pdf_path must point to a PDF file")
        self._pdf_path = value

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
        return self._strategy

    # ---------------------------------------------------------
    @abstractmethod
    def parse(self) -> List[Dict]:
        """
        Parse the PDF and return structured pages.

        Must be implemented by concrete parsers.
        """
        raise NotImplementedError
