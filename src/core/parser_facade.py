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
        # Strategy Pattern (Composition)
        self._strategy = PyMuPDFAdapter()

        # Factory Pattern → chooses the parser class
        self._parser = ParserFactory.create(
            parser_type=parser_type,
            pdf_strategy=self._strategy
        )

        # Extractors (Composition)
        self._toc_extractor = ToCExtractor()
        self._chunk_extractor = ChunkExtractor()
        self._table_extractor = TableExtractor()

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
        self._parser.pdf_path = pdf_path
        pdf_data = self._parser.parse()

        toc = self._toc_extractor.extract(pdf_data)
        chunks = self._chunk_extractor.extract(pdf_data)
        tables = self._table_extractor.extract(pdf_data)

        return {
            "toc": toc,
            "chunks": chunks,
            "tables": tables,
            "sections": pdf_data,
        }
