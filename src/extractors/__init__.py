"""
Extractor package initializer.

Provides unified exports for all extractor classes used in the
USB-PD parsing pipeline. This keeps import paths clean and allows
modular extension of extractors.
"""

from .toc_extractor import ToCExtractor
from .chunk_extractor import ChunkExtractor
from .table_extractor import TableExtractor
from .section_builder import SectionContentBuilder
from .high_fidelity_extractor import HighFidelityExtractor

__all__ = [
    "ToCExtractor",
    "ChunkExtractor",
    "TableExtractor",
    "SectionContentBuilder",
    "HighFidelityExtractor",
]
