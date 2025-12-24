# src/utils/pdf_utils.py

from pathlib import Path


class PDFUtils:
    """
    PDF helper utilities.

    Encapsulation rules:
    - estimate_page_count() is the ONLY public method
    - implementation details are private
    """

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------
    def estimate_page_count(self, pdf_path: str) -> int:
        path = self.__validate_path(pdf_path)
        return self.__estimate_from_metadata(path)

    # ---------------------------------------------------------
    # Private helpers
    # ---------------------------------------------------------
    def __validate_path(self, pdf_path: str) -> Path:
        path = Path(pdf_path)

        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {path}")

        if path.suffix.lower() != ".pdf":
            raise ValueError("Provided file is not a PDF")

        return path

    # ---------------------------------------------------------
    def __estimate_from_metadata(self, path: Path) -> int:
        """
        Stub implementation.

        Future:
        - use PyMuPDF metadata
        - fallback heuristics
        """
        return 10
