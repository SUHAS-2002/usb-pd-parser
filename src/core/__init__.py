"""
Core module initializer.

Exports key abstract interfaces and factory components used across
the parsing architecture. Keeps public API clean and consistent.
"""

from .parser_facade import ParserFacade
from .parser_factory import ParserFactory
from .base_parser import BaseParser
from .pdf_text_strategy import PDFTextStrategy
from .extractor_base import BaseExtractor

__all__ = [
    "ParserFacade",
    "ParserFactory",
    "BaseParser",
    "PDFTextStrategy",
    "BaseExtractor",
]
