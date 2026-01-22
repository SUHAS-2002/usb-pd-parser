# src/core/parser_facade.py

from .parser_factory import ParserFactory
from .adapter.pymupdf_adapter import PyMuPDFAdapter
from ..extractors.toc_extractor import ToCExtractor
from ..extractors.chunk_extractor import ChunkExtractor
from ..extractors.table_extractor import TableExtractor


class ParserFacade:
    """
    Facade that composes the parser, PDF text-extraction strategy,
    and extractor components. Provides a clean `parse_pdf()` API.

    Responsibilities:
    - Select PDF text extraction strategy (PyMuPDF by default)
    - Instantiate parser via ParserFactory
    - Run TOC, chunk, and table extraction
    - Return a structured dictionary of parsed output
    """

    def __init__(self, parser_type: str = "advanced") -> None:
        # Strategy Pattern (Composition) - 100% Encapsulation
        self.__strategy = PyMuPDFAdapter()

        # Factory Pattern → chooses the parser class
        self.__parser = ParserFactory.create(
            parser_type=parser_type,
            pdf_strategy=self.__strategy
        )

        # Extractors (Composition)
        self.__toc_extractor = ToCExtractor()
        self.__chunk_extractor = ChunkExtractor()
        self.__table_extractor = TableExtractor()
    
    # Encapsulation: Properties (read-only)
    @property
    def strategy(self):
        """Get PDF strategy (read-only)."""
        return self.__strategy
    
    @property
    def parser(self):
        """Get parser instance (read-only)."""
        return self.__parser
    
    @property
    def toc_extractor(self):
        """Get TOC extractor (read-only)."""
        return self.__toc_extractor
    
    @property
    def chunk_extractor(self):
        """Get chunk extractor (read-only)."""
        return self.__chunk_extractor
    
    @property
    def table_extractor(self):
        """Get table extractor (read-only)."""
        return self.__table_extractor

    def parse_pdf(self, pdf_path: str) -> dict:
        """
        Run the complete PDF parsing pipeline.

        Parameters
        ----------
        pdf_path : str
            Input PDF file path.

        Returns
        -------
        dict
            {
                "toc": [...],
                "chunks": [...],
                "tables": [...],
                "sections": [...],
            }
        """
        self.__parser.pdf_path = pdf_path
        pdf_data = self.__parser.parse()

        toc = self.__toc_extractor.extract(pdf_data)
        chunks = self.__chunk_extractor.extract(pdf_data)
        tables = self.__table_extractor.extract(pdf_data)

        return {
            "toc": toc,
            "chunks": chunks,
            "tables": tables,
            "sections": pdf_data,
        }
    
    # ---------------------------------------------------------
    # Polymorphism: Special methods
    # ---------------------------------------------------------
    def __str__(self) -> str:
        """Human-readable representation."""
        return f"ParserFacade(parser_type={self.__parser.__class__.__name__})"
    
    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"ParserFacade(parser_type='advanced')"
    
    def __eq__(self, other: object) -> bool:
        """Equality based on parser type."""
        if not isinstance(other, ParserFacade):
            return NotImplemented
        return self.__parser.__class__ == other.__parser.__class__
    
    def __hash__(self) -> int:
        """Hash for use in sets/dicts."""
        return hash((self.__class__, self.__parser.__class__))
    
    def __bool__(self) -> bool:
        """Truthiness: Always True (facade is always valid)."""
        return True
    
    def __len__(self) -> int:
        """Return number of extractors."""
        return 3  # toc, chunk, table extractors
    
    def __enter__(self) -> "ParserFacade":
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Context manager exit."""
        return False
    
    def __call__(self, pdf_path: str) -> dict:
        """Make class callable - delegates to parse_pdf()."""
        return self.parse_pdf(pdf_path)
