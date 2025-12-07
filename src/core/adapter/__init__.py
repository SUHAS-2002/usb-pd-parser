"""
Adapter package initializer.

Exports available PDF text extraction strategy implementations.
These strategies follow the Strategy Pattern and all implement
`PDFTextStrategy`, allowing interchangeable text extraction backends.
"""

from .pdfminer_adapter import PDFMinerAdapter
from .pymupdf_adapter import PyMuPDFAdapter
from .pypdf_adapter import PyPDFAdapter

__all__ = [
    "PDFMinerAdapter",
    "PyMuPDFAdapter",
    "PyPDFAdapter",
]
