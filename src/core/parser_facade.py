from .parser_factory import ParserFactory
from .adapter.pdfminer_adapter import PDFMinerAdapter
from .adapter.pymupdf_adapter import PyMuPDFAdapter
from .adapter.pypdf_adapter import PyPDFAdapter

from ..extractors.toc_extractor import ToCExtractor
from ..extractors.chunk_extractor import ChunkExtractor
from ..extractors.table_extractor import TableExtractor

class ParserFacade:
    """
    Facade that composes parsers, extractors, and the text-extraction strategy.
    Provides a simple parse_pdf(pdf_path) API.
    """

    def __init__(self, parser_type: str = "advanced"):
        self._strategy = PyMuPDFAdapter()
        self._parser = ParserFactory.create(parser_type, self._strategy)

        # Composition - concrete extractor instances
        self._toc_extractor = ToCExtractor()
        self._chunk_extractor = ChunkExtractor()
        self._table_extractor = TableExtractor()

    def parse_pdf(self, pdf_path: str) -> dict:
        self._parser.pdf_path = pdf_path
        pdf_data = self._parser.parse()

        toc = self._toc_extractor.extract(pdf_data)
        chunks = self._chunk_extractor.extract(pdf_data)
        tables = self._table_extractor.extract(pdf_data)

        return {
            "toc": toc,
            "chunks": chunks,
            "tables": tables,
            "sections": pdf_data
        }
