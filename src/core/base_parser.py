# src/core/base_parser.py

from abc import ABC, abstractmethod
from typing import Any, List, Dict


class BaseParser(ABC):
    """
    Abstract base parser defining the public interface and common helpers.
    All concrete PDF parsers (like FullPDFParser) must inherit from this.
    """

    def __init__(self, pdf_strategy: Any):
        self._strategy = pdf_strategy
        self._pdf_path: str | None = None

    @property
    def pdf_path(self) -> str:
        if not self._pdf_path:
            raise ValueError("pdf_path not set")
        return self._pdf_path

    @pdf_path.setter
    def pdf_path(self, value: str):
        if not isinstance(value, str):
            raise ValueError("pdf_path must be a string")
        if not value.lower().endswith(".pdf"):
            raise ValueError("pdf_path must point to a PDF file")
        self._pdf_path = value

    @abstractmethod
    def parse(self) -> List[Dict]:
        """
        Parse the PDF and return structured pages:
        [
            {"page_number": int, "text": str},
            ...
        ]
        """
        raise NotImplementedError
