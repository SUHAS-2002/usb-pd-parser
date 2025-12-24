"""
Table extractor (compact OOP, ≤79 chars).

Provides a stable interface for future table parsing logic.
"""

from typing import List, Dict, Any, Protocol, runtime_checkable

from src.core.extractor_base import BaseExtractor


# ------------------------------------------------------------
# Public protocol (stable contract)
# ------------------------------------------------------------
@runtime_checkable
class TableExtractorProtocol(Protocol):
    def extract(self, pdf_data: Any) -> List[Dict]:
        ...


# ------------------------------------------------------------
# Concrete implementation
# ------------------------------------------------------------
class TableExtractor(BaseExtractor):
    """
    Placeholder table extractor strategy.

    Encapsulation rules:
    - extract() is inherited and public
    - implementation lives in protected helpers
    """

    # --------------------------------------------------------
    # Template method implementation
    # --------------------------------------------------------
    def _extract_impl(self, pdf_data: Any) -> List[Dict]:
        return self._extract_tables(pdf_data)

    # --------------------------------------------------------
    # Protected extension point
    # --------------------------------------------------------
    def _extract_tables(self, pdf_data: Any) -> List[Dict]:
        """
        Hook for future table extraction logic.
        """
        return []
