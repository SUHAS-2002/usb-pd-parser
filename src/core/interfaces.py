from typing import Protocol, List, Dict


class PDFExtractorProtocol(Protocol):
    """Protocol for PDF text extraction."""

    def extract(self, pdf_path: str) -> List[Dict]:
        """Extract text from a PDF."""
        ...


class ToCExtractorProtocol(Protocol):
    """Protocol for Table of Contents extraction."""

    def extract(self, pages: List[Dict]) -> List[Dict]:
        """Extract TOC entries from pages."""
        ...


class InlineHeadingExtractorProtocol(Protocol):
    """Protocol for numeric inline heading extraction."""

    def extract(self, pdf_data: Dict) -> List[Dict]:
        """Extract numeric section headings."""
        ...


class SectionBuilderProtocol(Protocol):
    """Protocol for building document sections."""

    def build(
        self,
        toc: List[Dict],
        pages: List[Dict],
        headings: List[Dict],
        doc_title: str,
    ) -> List[Dict]:
        """Build sections from TOC, pages, and headings."""
        ...
