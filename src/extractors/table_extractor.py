"""
Table extractor (compact OOP, ≤79 chars).

Provides a stable interface for future table parsing logic.
"""

from typing import List, Dict, Any, Protocol, runtime_checkable


@runtime_checkable
class TableExtractorProtocol(Protocol):
    def extract(self, pdf_data: Any) -> List[Dict]:
        ...


class TableExtractor:
    """
    Placeholder table extractor strategy.
    """

    def __init__(self) -> None:
        pass

    def extract(self, pdf_data: Any) -> List[Dict]:
        """
        Extract tables from parsed PDF data.
        """
        return []
