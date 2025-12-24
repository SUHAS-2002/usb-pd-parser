# src/core/extractor_base.py

from abc import ABC, abstractmethod
from typing import List, Dict


class BaseExtractor(ABC):
    """
    Abstract base class for all PDF extraction strategies.

    Encapsulation rules:
    - extract() is the ONLY public entry point
    - subclasses may override protected helpers
    - no internal state is exposed directly
    """

    # ------------------------------------------------------------
    # Public API (stable)
    # ------------------------------------------------------------
    def extract(self, pdf_path: str) -> List[Dict]:
        """
        Public extraction entry point.

        This method enforces a consistent extraction lifecycle
        across all extractors.
        """
        self._validate_input(pdf_path)
        return self._extract_impl(pdf_path)

    # ------------------------------------------------------------
    # Protected template methods (for subclasses)
    # ------------------------------------------------------------
    @abstractmethod
    def _extract_impl(self, pdf_path: str) -> List[Dict]:
        """
        Concrete extraction logic.

        Must be implemented by subclasses.
        """
        raise NotImplementedError

    # ------------------------------------------------------------
    # Protected helpers
    # ------------------------------------------------------------
    def _validate_input(self, pdf_path: str) -> None:
        """
        Validate extractor input.

        Subclasses may override if stricter validation is required.
        """
        if not isinstance(pdf_path, str):
            raise TypeError("pdf_path must be a string")

        if not pdf_path.lower().endswith(".pdf"):
            raise ValueError("pdf_path must point to a PDF file")
