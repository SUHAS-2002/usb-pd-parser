# src/core/base_parser.py

from abc import ABC, abstractmethod
from typing import Any, List, Dict


class BaseParser(ABC):
    """
    Abstract base parser defining the public interface and
    common lifecycle rules.

    Encapsulation rules:
    - parse() is the ONLY public abstract method
    - internal state is private
    - validation logic is encapsulated
    """

    # ---------------------------------------------------------
    # Construction (private state)
    # ---------------------------------------------------------
    def __init__(self, pdf_strategy: Any) -> None:
        self.__strategy = pdf_strategy
        self.__pdf_path: str | None = None

    # ---------------------------------------------------------
    # Public, controlled property
    # ---------------------------------------------------------
    @property
    def pdf_path(self) -> str:
        if self.__pdf_path is None:
            raise ValueError("pdf_path not set")
        return self.__pdf_path

    @pdf_path.setter
    def pdf_path(self, value: str) -> None:
        self.__pdf_path = self.__validate_pdf_path(value)

    # ---------------------------------------------------------
    # Protected access for subclasses
    # ---------------------------------------------------------
    @property
    def _strategy(self) -> Any:
        """
        Protected access to parsing strategy.
        """
        return self.__strategy

    # ---------------------------------------------------------
    # Abstract API
    # ---------------------------------------------------------
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

    # ---------------------------------------------------------
    # Private helpers
    # ---------------------------------------------------------
    def __validate_pdf_path(self, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("pdf_path must be a string")

        if not value.lower().endswith(".pdf"):
            raise ValueError("pdf_path must point to a PDF file")

        return value
